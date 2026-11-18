"""Bug detector agent."""
from typing import Dict, Any, List

from app.agents.base import BaseAgent, AgentContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class BugDetectorAgent(BaseAgent):
    """Agent for detecting bugs and code issues."""

    def __init__(self):
        super().__init__("bug_detector", "Detects bugs, security vulnerabilities, and code quality issues")

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Detect bugs in the repository."""
        logger.info("Starting bug detection", repository_id=context.repository_id)

        # Get repository files
        files = await self._get_repository_files(context)
        if not files:
            return {"bugs": [], "error": "No files to analyze"}

        # Analyze files for bugs
        bugs = []
        for file_path, content in files.items():
            if self._should_analyze(file_path):
                file_bugs = await self._analyze_file(file_path, content, context)
                bugs.extend(file_bugs)

        # Deduplicate and prioritize
        bugs = self._deduplicate_bugs(bugs)
        bugs = self._prioritize_bugs(bugs)

        return {
            "bugs": bugs,
            "total_found": len(bugs),
            "by_severity": self._count_by_severity(bugs),
            "by_type": self._count_by_type(bugs),
        }

    async def _get_repository_files(self, context: AgentContext) -> Dict[str, str]:
        """Get repository files for analysis."""
        from app.services.repository import RepositoryService
        from app.core.database import get_db_context
        from app.models.repository import Repository
        from sqlalchemy import select

        repo_service = RepositoryService()

        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == context.repository_id))
            repository = result.scalar_one_or_none()

        if not repository or not repository.installation_id:
            return {}

        # Get file tree
        tree = await repo_service.get_file_tree(repository)
        files = {}

        # Filter to source files only
        for item in tree:
            if item["type"] == "blob" and self._should_analyze(item["path"]):
                content = await repo_service.get_file_content(repository, item["path"])
                if content:
                    files[item["path"]] = content

        return files

    def _should_analyze(self, file_path: str) -> bool:
        """Check if file should be analyzed."""
        # Skip test files, config files, vendor directories
        skip_patterns = [
            "node_modules/", "vendor/", "__pycache__/", ".git/",
            "dist/", "build/", ".next/", "target/",
            ".min.js", ".min.css", ".map",
            "test_", "_test.", "spec.", ".test.",
            "migrations/", "fixtures/",
        ]

        for pattern in skip_patterns:
            if pattern in file_path:
                return False

        # Only analyze source files
        source_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
            ".rs", ".cpp", ".c", ".h", ".cs", ".rb", ".php",
            ".swift", ".kt", ".scala", ".r", ".m", ".mm",
        }

        return any(file_path.endswith(ext) for ext in source_extensions)

    async def _analyze_file(self, file_path: str, content: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Analyze a single file for bugs."""
        bugs = []

        # Run static analysis patterns
        bugs.extend(self._check_common_patterns(file_path, content))
        bugs.extend(self._check_security_patterns(file_path, content))
        bugs.extend(self._check_performance_patterns(file_path, content))

        # Use LLM for deeper analysis on important files
        if self._is_important_file(file_path, content):
            llm_bugs = await self._llm_analyze(file_path, content)
            bugs.extend(llm_bugs)

        return bugs

    def _check_common_patterns(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Check for common bug patterns."""
        bugs = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # TODO/FIXME comments
            if "TODO" in line or "FIXME" in line or "HACK" in line:
                bugs.append({
                    "id": f"todo_{file_path}_{i}",
                    "type": "technical_debt",
                    "severity": "low",
                    "title": "TODO/FIXME comment found",
                    "description": line.strip(),
                    "file": file_path,
                    "line": i,
                    "column": line.find("TODO") if "TODO" in line else line.find("FIXME"),
                })

            # Hardcoded secrets (basic check)
            if any(keyword in line.lower() for keyword in ["password", "secret", "api_key", "token", "private_key"]):
                if "=" in line and not line.strip().startswith("#"):
                    bugs.append({
                        "id": f"secret_{file_path}_{i}",
                        "type": "security",
                        "severity": "high",
                        "title": "Potential hardcoded secret",
                        "description": "Possible hardcoded credential detected",
                        "file": file_path,
                        "line": i,
                    })

            # SQL injection risk
            if "execute(" in line and "%" in line and ("SELECT" in line.upper() or "INSERT" in line.upper()):
                bugs.append({
                    "id": f"sql_injection_{file_path}_{i}",
                    "type": "security",
                    "severity": "high",
                    "title": "Potential SQL injection",
                    "description": "String formatting in SQL query detected",
                    "file": file_path,
                    "line": i,
                })

            # Empty except blocks
            if "except:" in line and i + 1 < len(lines) and "pass" in lines[i]:
                bugs.append({
                    "id": f"empty_except_{file_path}_{i}",
                    "type": "error_handling",
                    "severity": "medium",
                    "title": "Empty except block",
                    "description": "Bare except clause with pass swallows all exceptions",
                    "file": file_path,
                    "line": i,
                })

        return bugs

    def _check_security_patterns(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Check for security vulnerabilities."""
        bugs = []
        lines = content.split("\n")

        # Path traversal
        for i, line in enumerate(lines, 1):
            if "open(" in line and ("../" in line or "..\\" in line):
                bugs.append({
                    "id": f"path_traversal_{file_path}_{i}",
                    "type": "security",
                    "severity": "high",
                    "title": "Potential path traversal",
                    "description": "File path uses relative traversal",
                    "file": file_path,
                    "line": i,
                })

            # Command injection
            if any(func in line for func in ["subprocess.run(", "subprocess.Popen(", "os.system(", "eval(", "exec("]):
                if "%" in line or "+" in line or ".format(" in line or "f\"" in line:
                    bugs.append({
                        "id": f"cmd_injection_{file_path}_{i}",
                        "type": "security",
                        "severity": "critical",
                        "title": "Potential command injection",
                        "description": "User input in command execution",
                        "file": file_path,
                        "line": i,
                    })

        return bugs

    def _check_performance_patterns(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Check for performance issues."""
        bugs = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # N+1 query patterns (basic)
            if "for " in line and "query(" in line:
                bugs.append({
                    "id": f"n_plus_one_{file_path}_{i}",
                    "type": "performance",
                    "severity": "medium",
                    "title": "Potential N+1 query",
                    "description": "Database query inside loop detected",
                    "file": file_path,
                    "line": i,
                })

        return bugs

    def _is_important_file(self, file_path: str, content: str) -> bool:
        """Check if file is important enough for LLM analysis."""
        important_patterns = [
            "main.", "app.", "server.", "handler.", "controller.",
            "service.", "repository.", "model.", "entity.",
            "auth.", "security.", "payment.", "billing.",
        ]
        return any(pattern in file_path for pattern in important_patterns) and len(content) > 500

    async def _llm_analyze(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Use LLM to analyze file for bugs."""
        prompt = f"""
        Analyze this code file for bugs, security issues, and code quality problems:

        File: {file_path}
        Content:
        ```
        {content[:3000]}
        ```

        Return a JSON array of issues found, each with:
        - type: bug/security/performance/style
        - severity: critical/high/medium/low
        - title: brief title
        - description: detailed description
        - line: approximate line number
        - suggestion: fix suggestion

        Focus on:
        1. Logic errors and edge cases
        2. Security vulnerabilities
        3. Performance issues
        4. Error handling problems
        5. Concurrency issues
        """

        try:
            response = await self.think(
                prompt,
                system_prompt="You are a senior security engineer and code reviewer. Return only valid JSON array.",
                temperature=0.1,
            )

            import json
            bugs = json.loads(response)
            for bug in bugs:
                bug["id"] = f"llm_{file_path}_{bug.get('line', 0)}"
                bug["file"] = file_path
            return bugs
        except Exception as e:
            logger.warning("LLM analysis failed", file=file_path, error=str(e))
            return []

    def _deduplicate_bugs(self, bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate bugs."""
        seen = set()
        unique = []
        for bug in bugs:
            key = (bug.get("file"), bug.get("line"), bug.get("type"), bug.get("title"))
            if key not in seen:
                seen.add(key)
                unique.append(bug)
        return unique

    def _prioritize_bugs(self, bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort bugs by severity."""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(bugs, key=lambda b: severity_order.get(b.get("severity", "low"), 4))

    def _count_by_severity(self, bugs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count bugs by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for bug in bugs:
            sev = bug.get("severity", "low")
            if sev in counts:
                counts[sev] += 1
        return counts

    def _count_by_type(self, bugs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count bugs by type."""
        counts = {}
        for bug in bugs:
            typ = bug.get("type", "unknown")
            counts[typ] = counts.get(typ, 0) + 1
        return counts

    async def _perform_action(self, action: str, **kwargs) -> Any:
        """Perform specific bug detection actions."""
        if action == "analyze_file":
            return await self._analyze_file(kwargs.get("file_path"), kwargs.get("content"), kwargs.get("context"))
        elif action == "get_bug_details":
            return {"details": "Bug details would be fetched here"}
        else:
            raise ValueError(f"Unknown action: {action}")