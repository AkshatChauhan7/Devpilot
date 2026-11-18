"""Test generator agent."""
from typing import Dict, Any, List

from app.agents.base import BaseAgent, AgentContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class TestGeneratorAgent(BaseAgent):
    """Agent for generating tests."""

    def __init__(self):
        super().__init__("test_generator", "Generates unit, integration, and end-to-end tests")

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Generate tests for target files."""
        logger.info("Starting test generation", repository_id=context.repository_id)

        target_files = context.metadata.get("target_files", [])
        if not target_files:
            return {"files": [], "error": "No target files specified"}

        # Get repository context
        repo_context = await self._get_repository_context(context)

        files = []
        for file_path in target_files:
            # Get source file content
            source_content = await self._get_file_content(context, file_path)
            if not source_content:
                continue

            # Check if test already exists
            test_path = self._get_test_path(file_path, repo_context)
            existing_test = await self._get_file_content(context, test_path) if test_path else None

            # Generate test
            test_content = await self._generate_test(
                file_path=file_path,
                source_content=source_content,
                existing_test=existing_test,
                repo_context=repo_context,
            )

            if test_content:
                files.append({
                    "path": test_path or self._suggest_test_path(file_path, repo_context),
                    "content": test_content,
                    "description": f"Tests for {file_path}",
                    "type": "test",
                    "source_file": file_path,
                })

        return {
            "files": files,
            "total_files": len(files),
        }

    async def _get_repository_context(self, context: AgentContext) -> Dict[str, Any]:
        """Get repository context for test generation."""
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

        # Get test framework info
        tree = await repo_service.get_file_tree(repository)
        test_frameworks = self._detect_test_frameworks(tree)

        return {
            "repository": {
                "name": repository.name,
                "language": repository.language,
            },
            "test_frameworks": test_frameworks,
            "structure": {
                "files": [f["path"] for f in tree if f["type"] == "blob"],
            },
        }

    def _detect_test_frameworks(self, tree: List[Dict[str, Any]]) -> List[str]:
        """Detect test frameworks from repository structure."""
        frameworks = []
        files = [f["path"] for f in tree if f["type"] == "blob"]

        # Python
        if any(f in files for f in ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"]):
            if any("pytest" in f for f in files):
                frameworks.append("pytest")
            frameworks.append("unittest")

        # JavaScript/TypeScript
        if any(f in files for f in ["package.json", "jest.config.js", "vitest.config.ts"]):
            frameworks.append("jest")
            frameworks.append("vitest")

        # Go
        if any(f.endswith("_test.go") for f in files):
            frameworks.append("go test")

        # Rust
        if any("tests/" in f for f in files):
            frameworks.append("cargo test")

        return frameworks

    def _get_test_path(self, source_path: str, repo_context: Dict[str, Any]) -> str:
        """Determine test file path for a source file."""
        language = repo_context.get("repository", {}).get("language", "").lower()
        structure = repo_context.get("structure", {}).get("files", [])

        # Python
        if language == "python" or source_path.endswith(".py"):
            # Check for tests/ directory
            if any(f.startswith("tests/") for f in structure):
                return source_path.replace("src/", "tests/").replace(".py", "_test.py")
            elif any(f.startswith("test/") for f in structure):
                return source_path.replace("src/", "test/").replace(".py", "_test.py")
            else:
                return source_path.replace(".py", "_test.py")

        # JavaScript/TypeScript
        if language in ["javascript", "typescript"] or source_path.endswith((".js", ".ts", ".jsx", ".tsx")):
            if any(f.startswith("__tests__/") for f in structure):
                return source_path.replace("src/", "__tests__/").replace(".ts", ".test.ts").replace(".js", ".test.js")
            elif any(f.startswith("tests/") for f in structure):
                return source_path.replace("src/", "tests/").replace(".ts", ".test.ts").replace(".js", ".test.js")
            else:
                return source_path.replace(".ts", ".test.ts").replace(".js", ".test.js")

        # Go
        if language == "go" or source_path.endswith(".go"):
            return source_path.replace(".go", "_test.go")

        # Rust
        if language == "rust" or source_path.endswith(".rs"):
            return source_path.replace("src/", "tests/").replace(".rs", "_test.rs")

        # Java
        if language == "java" or source_path.endswith(".java"):
            return source_path.replace("src/main/", "src/test/").replace(".java", "Test.java")

        return source_path + ".test"

    def _suggest_test_path(self, source_path: str, repo_context: Dict[str, Any]) -> str:
        """Suggest test path when none exists."""
        return self._get_test_path(source_path, repo_context)

    async def _get_file_content(self, context: AgentContext, file_path: str) -> str:
        """Get file content from repository."""
        from app.services.repository import RepositoryService
        from app.core.database import get_db_context
        from app.models.repository import Repository
        from sqlalchemy import select

        repo_service = RepositoryService()

        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == context.repository_id))
            repository = result.scalar_one_or_none()

        if not repository:
            return ""

        return await repo_service.get_file_content(repository, file_path) or ""

    async def _generate_test(
        self,
        file_path: str,
        source_content: str,
        existing_test: str,
        repo_context: Dict[str, Any],
    ) -> str:
        """Generate test for a source file."""
        frameworks = repo_context.get("test_frameworks", [])
        language = repo_context.get("repository", {}).get("language", "").lower()

        # Determine test framework
        framework = self._select_framework(language, frameworks)

        prompt = f"""
        Generate comprehensive tests for this source file:

        Source File: {file_path}
        Language: {language}
        Test Framework: {framework}
        Existing Test: {existing_test[:1000] if existing_test else 'None'}

        Source Code:
        ```
        {source_content[:3000]}
        ```

        Generate tests that cover:
        1. Happy path cases
        2. Edge cases
        3. Error conditions
        4. Boundary values
        5. Mock external dependencies

        Return ONLY the test file content.
        Use {framework} conventions and best practices.
        Include proper imports, fixtures, and test organization.
        """

        try:
            content = await self.think(
                prompt,
                system_prompt=f"You are a senior software engineer writing {framework} tests. Return only the test code.",
                temperature=0.1,
            )
            return content.strip()
        except Exception as e:
            logger.warning("Failed to generate test", file=file_path, error=str(e))
            return ""

    def _select_framework(self, language: str, frameworks: List[str]) -> str:
        """Select appropriate test framework."""
        if "pytest" in frameworks:
            return "pytest"
        if "jest" in frameworks:
            return "jest"
        if "vitest" in frameworks:
            return "vitest"
        if "go test" in frameworks:
            return "go test"
        if "cargo test" in frameworks:
            return "cargo test"

        # Defaults by language
        defaults = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "go": "go test",
            "rust": "cargo test",
            "java": "junit",
        }
        return defaults.get(language, "pytest")

    async def _perform_action(self, action: str, **kwargs) -> Any:
        """Perform specific test generation actions."""
        if action == "generate_test":
            return await self._generate_test(
                kwargs.get("file_path"),
                kwargs.get("source_content"),
                kwargs.get("existing_test"),
                kwargs.get("repo_context"),
            )
        elif action == "get_test_path":
            return self._get_test_path(kwargs.get("file_path"), kwargs.get("repo_context"))
        else:
            raise ValueError(f"Unknown action: {action}")