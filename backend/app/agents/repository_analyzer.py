"""Repository analyzer agent."""
from typing import Dict, Any, List
import json

from app.agents.base import BaseAgent, AgentContext
from app.core.logging import get_logger
from app.services.repository import RepositoryService

logger = get_logger(__name__)


class RepositoryAnalyzerAgent(BaseAgent):
    """Agent for analyzing repository structure and code."""

    def __init__(self):
        super().__init__("repository_analyzer", "Analyzes repository structure, dependencies, and code patterns")
        self.repo_service = RepositoryService()

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze repository and return structured information."""
        logger.info("Starting repository analysis", repository_id=context.repository_id)

        # Get repository info
        async with get_db_context() as db:
            from app.models.repository import Repository
            from sqlalchemy import select
            result = await db.execute(select(Repository).where(Repository.id == context.repository_id))
            repository = result.scalar_one_or_none()

        if not repository:
            return {"error": "Repository not found"}

        # Clone and analyze
        repo_path = await self.repo_service._clone_repository(repository)
        if not repo_path:
            return {"error": "Failed to clone repository"}

        try:
            analysis = await self.repo_service._run_analysis(repo_path, repository)

            # Use LLM to summarize findings
            summary = await self._summarize_analysis(analysis, repository)

            return {
                "repository_id": context.repository_id,
                "analysis": analysis,
                "summary": summary,
                "files_analyzed": len(analysis.get("structure", {}).get("files", [])),
                "languages": analysis.get("languages", {}),
                "dependencies": analysis.get("dependencies", {}),
                "issues_found": len(analysis.get("issues", [])),
            }
        finally:
            # Cleanup
            import shutil
            if repo_path:
                shutil.rmtree(repo_path, ignore_errors=True)

    async def _summarize_analysis(self, analysis: Dict[str, Any], repository) -> str:
        """Use LLM to create a summary of the analysis."""
        prompt = f"""
        Analyze this repository and provide a concise summary:

        Repository: {repository.full_name}
        Description: {repository.description or 'N/A'}
        Languages: {analysis.get('languages', {})}
        Dependencies: {list(analysis.get('dependencies', {}).keys())}
        Structure: {len(analysis.get('structure', {}).get('files', []))} files, {len(analysis.get('structure', {}).get('directories', []))} directories
        Entry points: {analysis.get('structure', {}).get('entry_points', [])}
        Config files: {analysis.get('structure', {}).get('config_files', [])}
        Issues found: {len(analysis.get('issues', []))}

        Provide a 2-3 paragraph summary covering:
        1. What type of project this is
        2. Key technologies and architecture patterns
        3. Notable findings or concerns
        """

        return await self.think(prompt, system_prompt="You are a senior software architect analyzing codebases.")

    async def _perform_action(self, action: str, **kwargs) -> Any:
        """Perform specific analysis actions."""
        if action == "get_file_tree":
            return await self.repo_service.get_file_tree(
                kwargs.get("repository"), kwargs.get("ref")
            )
        elif action == "get_file_content":
            return await self.repo_service.get_file_content(
                kwargs.get("repository"), kwargs.get("file_path"), kwargs.get("ref")
            )
        elif action == "analyze_dependencies":
            return await self.repo_service._find_dependencies(kwargs.get("repo_path"))
        else:
            raise ValueError(f"Unknown action: {action}")