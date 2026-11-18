"""Repository analysis service."""
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.repository import Repository
from app.services.github import GitHubService

logger = get_logger(__name__)


class RepositoryService:
    """Service for repository analysis and code intelligence."""

    def __init__(self):
        self.github = GitHubService()

    async def analyze_repository(self, repository_id: int):
        """Analyze a repository for code intelligence."""
        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == repository_id))
            repository = result.scalar_one_or_none()
            if not repository:
                logger.error("Repository not found", repository_id=repository_id)
                return

            repository.analysis_status = "running"
            await db.commit()

            try:
                # Clone repository
                repo_path = await self._clone_repository(repository)
                if not repo_path:
                    repository.analysis_status = "failed"
                    repository.analysis_error = "Failed to clone repository"
                    await db.commit()
                    return

                # Run analysis
                analysis_result = await self._run_analysis(repo_path, repository)

                # Update repository with analysis results
                repository.analysis_status = "completed"
                repository.last_analyzed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                # Store analysis results in repository metadata or separate table
                await db.commit()

                logger.info("Repository analysis completed", repository_id=repository_id)

            except Exception as e:
                logger.exception("Repository analysis failed", repository_id=repository_id, error=str(e))
                repository.analysis_status = "failed"
                repository.analysis_error = str(e)
                await db.commit()

    async def _clone_repository(self, repository: Repository) -> Optional[str]:
        """Clone repository to temporary directory."""
        if not repository.installation_id:
            logger.error("Repository has no installation", repository_id=repository.id)
            return None

        async with get_db_context() as db:
            result = await db.execute(
                select(Installation).where(Installation.id == repository.installation_id)
            )
            installation = result.scalar_one_or_none()
            if not installation:
                return None

            token = await self.github.get_installation_token(installation.github_id)
            if not token:
                return None

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"devpilot_{repository.id}_")
        repo_path = Path(temp_dir) / repository.name

        try:
            # Clone using GitHub token
            clone_url = repository.clone_url.replace("https://", f"https://x-access-token:{token}@")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.error("Git clone failed", stderr=result.stderr)
                return None

            return str(repo_path)
        except Exception as e:
            logger.exception("Clone failed", error=str(e))
            return None

    async def _run_analysis(self, repo_path: str, repository: Repository) -> Dict[str, Any]:
        """Run code analysis on repository."""
        results = {
            "languages": {},
            "files": [],
            "dependencies": {},
            "structure": {},
            "issues": [],
        }

        # Detect languages
        results["languages"] = await self._detect_languages(repo_path)

        # Analyze structure
        results["structure"] = await self._analyze_structure(repo_path)

        # Find dependency files
        results["dependencies"] = await self._find_dependencies(repo_path)

        # Run static analysis if tools available
        results["issues"] = await self._run_static_analysis(repo_path, results["languages"])

        return results

    async def _detect_languages(self, repo_path: str) -> Dict[str, int]:
        """Detect programming languages in repository."""
        languages = {}
        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".r": "R",
            ".m": "Objective-C",
            ".mm": "Objective-C++",
            ".sh": "Shell",
            ".sql": "SQL",
        }

        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and node_modules
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "__pycache__"]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in extensions:
                    lang = extensions[ext]
                    languages[lang] = languages.get(lang, 0) + 1

        return languages

    async def _analyze_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository structure."""
        structure = {
            "directories": [],
            "files": [],
            "entry_points": [],
            "config_files": [],
            "test_directories": [],
        }

        config_files = {
            "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
            "requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "poetry.lock",
            "Cargo.toml", "Cargo.lock",
            "go.mod", "go.sum",
            "pom.xml", "build.gradle", "build.gradle.kts",
            "composer.json", "composer.lock",
            "Gemfile", "Gemfile.lock",
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".github", ".gitlab-ci.yml", ".circleci",
            "README.md", "README.rst", "README.txt",
            "LICENSE", "LICENSE.md", "LICENSE.txt",
            ".gitignore", ".dockerignore",
        }

        test_dirs = {"test", "tests", "spec", "specs", "__tests__", "testing"}

        for root, dirs, files in os.walk(repo_path):
            rel_root = os.path.relpath(root, repo_path)
            if rel_root == ".":
                rel_root = ""

            # Track directories
            for d in dirs:
                if not d.startswith("."):
                    structure["directories"].append(os.path.join(rel_root, d))

            # Track files
            for f in files:
                if not f.startswith("."):
                    filepath = os.path.join(rel_root, f)
                    structure["files"].append(filepath)

                    # Check for config files
                    if f in config_files:
                        structure["config_files"].append(filepath)

                    # Check for entry points
                    if f in {"main.py", "index.js", "index.ts", "main.go", "main.rs", "Main.java", "Program.cs"}:
                        structure["entry_points"].append(filepath)

            # Check for test directories
            for d in dirs:
                if d.lower() in test_dirs:
                    structure["test_directories"].append(os.path.join(rel_root, d))

        return structure

    async def _find_dependencies(self, repo_path: str) -> Dict[str, Any]:
        """Find and parse dependency files."""
        dependencies = {}

        # Python
        for dep_file in ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "poetry.lock"]:
            path = Path(repo_path) / dep_file
            if path.exists():
                dependencies["python"] = {"file": dep_file, "path": str(path)}
                break

        # Node.js
        for dep_file in ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
            path = Path(repo_path) / dep_file
            if path.exists():
                dependencies["nodejs"] = {"file": dep_file, "path": str(path)}
                break

        # Rust
        path = Path(repo_path) / "Cargo.toml"
        if path.exists():
            dependencies["rust"] = {"file": "Cargo.toml", "path": str(path)}

        # Go
        path = Path(repo_path) / "go.mod"
        if path.exists():
            dependencies["go"] = {"file": "go.mod", "path": str(path)}

        # Java
        for dep_file in ["pom.xml", "build.gradle", "build.gradle.kts"]:
            path = Path(repo_path) / dep_file
            if path.exists():
                dependencies["java"] = {"file": dep_file, "path": str(path)}
                break

        return dependencies

    async def _run_static_analysis(self, repo_path: str, languages: Dict[str, int]) -> List[Dict[str, Any]]:
        """Run static analysis tools."""
        issues = []

        # Python - run ruff if available
        if "Python" in languages:
            issues.extend(await self._run_ruff(repo_path))

        # JavaScript/TypeScript - run eslint if available
        if "JavaScript" in languages or "TypeScript" in languages:
            issues.extend(await self._run_eslint(repo_path))

        return issues

    async def _run_ruff(self, repo_path: str) -> List[Dict[str, Any]]:
        """Run Ruff linter on Python code."""
        issues = []
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", repo_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.stdout:
                import json
                ruff_issues = json.loads(result.stdout)
                for issue in ruff_issues:
                    issues.append({
                        "tool": "ruff",
                        "file": issue.get("filename", ""),
                        "line": issue.get("location", {}).get("row", 0),
                        "column": issue.get("location", {}).get("column", 0),
                        "code": issue.get("code", ""),
                        "message": issue.get("message", ""),
                        "severity": "warning",
                    })
        except FileNotFoundError:
            pass  # Ruff not installed
        except Exception as e:
            logger.warning("Ruff analysis failed", error=str(e))

        return issues

    async def _run_eslint(self, repo_path: str) -> List[Dict[str, Any]]:
        """Run ESLint on JavaScript/TypeScript code."""
        issues = []
        try:
            result = subprocess.run(
                ["eslint", "--format=json", repo_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.stdout:
                import json
                eslint_results = json.loads(result.stdout)
                for result in eslint_results:
                    for message in result.get("messages", []):
                        issues.append({
                            "tool": "eslint",
                            "file": result.get("filePath", ""),
                            "line": message.get("line", 0),
                            "column": message.get("column", 0),
                            "code": message.get("ruleId", ""),
                            "message": message.get("message", ""),
                            "severity": "error" if message.get("severity") == 2 else "warning",
                        })
        except FileNotFoundError:
            pass  # ESLint not installed
        except Exception as e:
            logger.warning("ESLint analysis failed", error=str(e))

        return issues

    async def get_file_content(self, repository: Repository, file_path: str, ref: str = None) -> Optional[str]:
        """Get file content from repository."""
        if not repository.installation_id:
            return None

        async with get_db_context() as db:
            result = await db.execute(
                select(Installation).where(Installation.id == repository.installation_id)
            )
            installation = result.scalar_one_or_none()
            if not installation:
                return None

            token = await self.github.get_installation_token(installation.github_id)
            if not token:
                return None

        owner, repo = repository.full_name.split("/")
        content = await self.github.get_contents(token, owner, repo, file_path, ref)
        if content and isinstance(content, dict) and content.get("content"):
            import base64
            return base64.b64decode(content["content"]).decode("utf-8")
        return None

    async def get_file_tree(self, repository: Repository, ref: str = None) -> List[Dict[str, Any]]:
        """Get repository file tree."""
        if not repository.installation_id:
            return []

        async with get_db_context() as db:
            result = await db.execute(
                select(Installation).where(Installation.id == repository.installation_id)
            )
            installation = result.scalar_one_or_none()
            if not installation:
                return []

            token = await self.github.get_installation_token(installation.github_id)
            if not token:
                return []

        owner, repo = repository.full_name.split("/")
        # Use GitHub Trees API for recursive tree
        response = await self.github.client.get(
            f"{self.github.BASE_URL}/repos/{owner}/{repo}/git/trees/{ref or repository.default_branch}?recursive=1",
            headers=self.github._get_headers(token),
        )
        if response.status_code == 200:
            return response.json().get("tree", [])
        return []


# Import here to avoid circular import
from app.models.installation import Installation