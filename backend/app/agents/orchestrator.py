"""Agent orchestrator for multi-agent workflows."""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.repository import Repository
from app.models.task import Task
from app.agents.base import AgentRegistry, AgentContext, agent_registry
from app.agents.bug_detector import BugDetectorAgent
from app.agents.code_generator import CodeGeneratorAgent
from app.agents.code_modifier import CodeModifierAgent
from app.agents.test_generator import TestGeneratorAgent
from app.agents.repository_analyzer import RepositoryAnalyzerAgent
from app.services.repository import RepositoryService
from app.services.github import GitHubService

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrates multi-agent workflows for development tasks."""

    def __init__(self):
        self.registry = agent_registry
        self._initialize_agents()
        self.github = GitHubService()
        self.repo_service = RepositoryService()

    def _initialize_agents(self):
        """Initialize and register all agents."""
        if not self.registry.get("repository_analyzer"):
            self.registry.register(RepositoryAnalyzerAgent())
        if not self.registry.get("bug_detector"):
            self.registry.register(BugDetectorAgent())
        if not self.registry.get("code_generator"):
            self.registry.register(CodeGeneratorAgent())
        if not self.registry.register("code_modifier"):
            self.registry.register(CodeModifierAgent())
        if not self.registry.get("test_generator"):
            self.registry.register(TestGeneratorAgent())

    async def run_task(self, task: Task) -> Dict[str, Any]:
        """Run a task using appropriate agents."""
        # Create context
        context = await self._create_context(task)

        # Route to appropriate agent based on task type
        if task.type.value == "repository_analysis":
            return await self._run_repository_analysis(context)
        elif task.type.value == "bug_detection":
            return await self._run_bug_detection(context)
        elif task.type.value == "code_generation":
            return await self._run_code_generation(context)
        elif task.type.value == "code_modification":
            return await self._run_code_modification(context)
        elif task.type.value == "test_generation":
            return await self._run_test_generation(context)
        else:
            raise ValueError(f"Unknown task type: {task.type}")

    async def _create_context(self, task: Task) -> AgentContext:
        """Create agent context from task."""
        # Get repository
        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == task.repository_id))
            repository = result.scalar_one_or_none()

        if not repository:
            raise ValueError(f"Repository {task.repository_id} not found")

        # Get GitHub token if installation exists
        github_token = None
        if repository.installation_id:
            async with get_db_context() as db:
                from app.models.installation import Installation
                result = await db.execute(select(Installation).where(Installation.id == repository.installation_id))
                installation = result.scalar_one_or_none()
                if installation:
                    github_token = await self.github.get_installation_token(installation.github_id)

        return AgentContext(
            repository_id=task.repository_id,
            task_id=task.id,
            user_id=task.user_id,
            github_token=github_token,
            metadata=task.input_data or {},
        )

    async def _run_repository_analysis(self, context: AgentContext) -> Dict[str, Any]:
        """Run repository analysis using analyzer agent."""
        analyzer = self.registry.get("repository_analyzer")
        if not analyzer:
            raise ValueError("Repository analyzer not available")

        result = await analyzer.execute(context)
        return result

    async def _run_bug_detection(self, context: AgentContext) -> Dict[str, Any]:
        """Run bug detection using detector agent."""
        detector = self.registry.get("bug_detector")
        if not detector:
            raise ValueError("Bug detector not available")

        result = await detector.execute(context)
        return result

    async def _run_code_generation(self, context: AgentContext) -> Dict[str, Any]:
        """Run code generation using generator agent."""
        generator = self.registry.get("code_generator")
        if not generator:
            raise ValueError("Code generator not available")

        result = await generator.execute(context)
        return result

    async def _run_code_modification(self, context: AgentContext) -> Dict[str, Any]:
        """Run code modification using modifier agent."""
        modifier = self.registry.get("code_modifier")
        if not modifier:
            raise ValueError("Code modifier not available")

        result = await modifier.execute(context)
        return result

    async def _run_test_generation(self, context: AgentContext) -> Dict[str, Any]:
        """Run test generation using test generator agent."""
        generator = self.registry.get("test_generator")
        if not generator:
            raise ValueError("Test generator not available")

        result = await generator.execute(context)
        return result

    async def detect_bugs(self, repository_id: int) -> List[Dict[str, Any]]:
        """Detect bugs in repository."""
        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == repository_id))
            repository = result.scalar_one_or_none()

        if not repository:
            return []

        context = AgentContext(
            repository_id=repository_id,
            task_id=0,
            user_id=repository.owner_id,
        )

        detector = self.registry.get("bug_detector")
        if detector:
            result = await detector.execute(context)
            return result.get("bugs", [])

        return []

    async def generate_code(self, repository_id: int, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on specification."""
        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == repository_id))
            repository = result.scalar_one_or_none()

        if not repository:
            return {"files": []}

        context = AgentContext(
            repository_id=repository_id,
            task_id=0,
            user_id=repository.owner_id,
            metadata=spec,
        )

        generator = self.registry.get("code_generator")
        if generator:
            return await generator.execute(context)

        return {"files": []}

    async def generate_tests(self, repository_id: int, target_files: List[str]) -> Dict[str, Any]:
        """Generate tests for target files."""
        async with get_db_context() as db:
            result = await db.execute(select(Repository).where(Repository.id == repository_id))
            repository = result.scalar_one_or_none()

        if not repository:
            return {"files": []}

        context = AgentContext(
            repository_id=repository_id,
            task_id=0,
            user_id=repository.owner_id,
            metadata={"target_files": target_files},
        )

        generator = self.registry.get("test_generator")
        if generator:
            return await generator.execute(context)

        return {"files": []}