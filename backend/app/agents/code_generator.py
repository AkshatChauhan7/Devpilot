"""Code generator agent."""
from typing import Dict, Any, List

from app.agents.base import BaseAgent, AgentContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class CodeGeneratorAgent(BaseAgent):
    """Agent for generating code from specifications."""

    def __init__(self):
        super().__init__("code_generator", "Generates code implementations from requirements and specifications")

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Generate code based on specification."""
        logger.info("Starting code generation", repository_id=context.repository_id)

        spec = context.metadata.get("spec", {})
        if not spec:
            return {"files": [], "error": "No specification provided"}

        # Get repository context
        repo_context = await self._get_repository_context(context)

        # Generate implementation plan
        plan = await self._create_implementation_plan(spec, repo_context)

        # Generate files
        files = []
        for file_spec in plan.get("files", []):
            file_content = await self._generate_file(file_spec, repo_context, spec)
            if file_content:
                files.append({
                    "path": file_spec["path"],
                    "content": file_content,
                    "description": file_spec.get("description", ""),
                    "type": file_spec.get("type", "implementation"),
                })

        return {
            "files": files,
            "plan": plan,
            "total_files": len(files),
        }

    async def _get_repository_context(self, context: AgentContext) -> Dict[str, Any]:
        """Get repository context for code generation."""
        from app.services.repository import RepositoryService
        from app.core.database import get_db_context
        from app.models.repository import Repository
        from sqlalchemy import select

        repo_service = RepositoryService()

        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == context.repository_id))
            repository = result.scalar_one_or_none()

        if not repository:
            return {}

        # Get file tree and key files
        tree = await repo_service.get_file_tree(repository)
        key_files = {}

        for item in tree:
            if item["type"] == "blob" and self._is_key_file(item["path"]):
                content = await repo_service.get_file_content(repository, item["path"])
                if content:
                    key_files[item["path"]] = content[:2000]  # Limit size

        return {
            "repository": {
                "name": repository.name,
                "full_name": repository.full_name,
                "language": repository.language,
                "default_branch": repository.default_branch,
            },
            "structure": {
                "files": [f["path"] for f in tree if f["type"] == "blob"],
                "directories": [f["path"] for f in tree if f["type"] == "tree"],
            },
            "key_files": key_files,
        }

    def _is_key_file(self, file_path: str) -> bool:
        """Check if file is important for understanding codebase."""
        key_patterns = [
            "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml",
            "requirements.txt", "setup.py", "tsconfig.json", "webpack.config.js",
            "main.", "app.", "index.", "server.", "handler.", "config.",
            "models.", "schemas.", "types.", "interfaces.",
        ]
        return any(pattern in file_path for pattern in key_patterns)

    async def _create_implementation_plan(self, spec: Dict[str, Any], repo_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation plan using LLM."""
        prompt = f"""
        Create an implementation plan for this specification:

        Specification: {spec}

        Repository Context:
        - Language: {repo_context.get('repository', {}).get('language', 'Unknown')}
        - Key files: {list(repo_context.get('key_files', {}).keys())[:20]}
        - Structure: {len(repo_context.get('structure', {}).get('files', []))} files

        Return a JSON object with:
        {{
            "overview": "High-level approach",
            "files": [
                {{
                    "path": "relative/path/to/file.ext",
                    "type": "implementation|test|config|documentation",
                    "description": "What this file does",
                    "dependencies": ["other/files/that/might/be/needed"],
                    "key_components": ["ClassName", "function_name", "interface"]
                }}
            ],
            "estimated_complexity": "low|medium|high",
            "testing_strategy": "How to test this implementation"
        }}
        """

        try:
            response = await self.think(
                prompt,
                system_prompt="You are a senior software architect creating implementation plans. Return only valid JSON.",
                temperature=0.2,
            )
            import json
            return json.loads(response)
        except Exception as e:
            logger.warning("Failed to create implementation plan", error=str(e))
            return {"overview": "Failed to create plan", "files": []}

    async def _generate_file(self, file_spec: Dict[str, Any], repo_context: Dict[str, Any], spec: Dict[str, Any]) -> str:
        """Generate a single file."""
        prompt = f"""
        Generate the complete implementation for this file:

        File: {file_spec['path']}
        Type: {file_spec['type']}
        Description: {file_spec['description']}
        Key Components: {file_spec.get('key_components', [])}
        Dependencies: {file_spec.get('dependencies', [])}

        Specification: {spec}

        Repository Context:
        - Language: {repo_context.get('repository', {}).get('language', 'Unknown')}
        - Existing patterns: {self._get_patterns_for_file(file_spec['path'], repo_context)}

        Return ONLY the file content, no markdown formatting, no explanations.
        Use the existing code style and patterns from the repository.
        Include proper imports, type hints, error handling, and documentation.
        """

        try:
            content = await self.think(
                prompt,
                system_prompt="You are a senior software engineer writing production-quality code. Return only the code.",
                temperature=0.1,
            )
            return content.strip()
        except Exception as e:
            logger.warning("Failed to generate file", file=file_spec['path'], error=str(e))
            return ""

    def _get_patterns_for_file(self, file_path: str, repo_context: Dict[str, Any]) -> str:
        """Extract relevant patterns from repository for a file type."""
        key_files = repo_context.get("key_files", {})
        patterns = []

        # Find similar files
        for path, content in key_files.items():
            if self._similar_file_type(file_path, path):
                patterns.append(f"=== {path} ===\n{content[:1000]}")
                if len(patterns) >= 3:
                    break

        return "\n\n".join(patterns) if patterns else "No similar files found"

    def _similar_file_type(self, file1: str, file2: str) -> bool:
        """Check if two files are similar type."""
        ext1 = file1.split(".")[-1] if "." in file1 else ""
        ext2 = file2.split(".")[-1] if "." in file2 else ""
        return ext1 == ext2

    async def _perform_action(self, action: str, **kwargs) -> Any:
        """Perform specific code generation actions."""
        if action == "generate_file":
            return await self._generate_file(kwargs.get("file_spec"), kwargs.get("repo_context"), kwargs.get("spec"))
        elif action == "create_plan":
            return await self._create_implementation_plan(kwargs.get("spec"), kwargs.get("repo_context"))
        else:
            raise ValueError(f"Unknown action: {action}")