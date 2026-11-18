"""Code modifier agent."""
from typing import Dict, Any, List

from app.agents.base import BaseAgent, AgentContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class CodeModifierAgent(BaseAgent):
    """Agent for modifying existing code."""

    def __init__(self):
        super().__init__("code_modifier", "Modifies existing code to fix bugs, add features, or refactor")

    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Modify code based on task input."""
        logger.info("Starting code modification", repository_id=context.repository_id)

        input_data = context.metadata
        if not input_data:
            return {"files": [], "error": "No modification specification provided"}

        # Get the file to modify
        file_path = input_data.get("file_path") or input_data.get("path")
        if not file_path:
            return {"files": [], "error": "No file path specified"}

        # Get current file content
        current_content = await self._get_file_content(context, file_path)
        if not current_content:
            return {"files": [], "error": f"File not found: {file_path}"}

        # Determine modification type
        mod_type = input_data.get("type", "fix")
        instruction = input_data.get("instruction") or input_data.get("description", "")

        # Generate modified content
        modified_content = await self._modify_file(
            file_path=file_path,
            current_content=current_content,
            instruction=instruction,
            mod_type=mod_type,
            context=input_data,
        )

        if not modified_content:
            return {"files": [], "error": "Failed to generate modification"}

        return {
            "files": [{
                "path": file_path,
                "content": modified_content,
                "description": instruction,
                "type": mod_type,
                "original_content": current_content,
            }],
            "total_files": 1,
        }

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

    async def _modify_file(
        self,
        file_path: str,
        current_content: str,
        instruction: str,
        mod_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Modify a file based on instruction."""
        prompt = f"""
        Modify this file according to the instruction:

        File: {file_path}
        Type: {mod_type}
        Instruction: {instruction}

        Current Content:
        ```
        {current_content}
        ```

        Context: {context}

        Return ONLY the complete modified file content.
        Preserve existing code style, imports, and structure.
        Make minimal, focused changes.
        Include proper error handling and type hints.
        """

        try:
            content = await self.think(
                prompt,
                system_prompt="You are a senior software engineer making precise code modifications. Return only the modified code.",
                temperature=0.1,
            )
            return content.strip()
        except Exception as e:
            logger.warning("Failed to modify file", file=file_path, error=str(e))
            return ""

    async def apply_fix(self, context: AgentContext, bug: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a fix for a detected bug."""
        file_path = bug.get("file")
        if not file_path:
            return {"success": False, "error": "No file specified in bug"}

        current_content = await self._get_file_content(context, file_path)
        if not current_content:
            return {"success": False, "error": f"File not found: {file_path}"}

        # Generate fix
        fix_prompt = f"""
        Fix this bug in the code:

        Bug: {bug.get('title')}
        Description: {bug.get('description')}
        Severity: {bug.get('severity')}
        Type: {bug.get('type')}
        File: {file_path}
        Line: {bug.get('line')}
        Suggestion: {bug.get('suggestion', 'No suggestion provided')}

        Current Content:
        ```
        {current_content}
        ```

        Return ONLY the complete fixed file content.
        Make minimal changes to fix the specific issue.
        """

        try:
            fixed_content = await self.think(
                fix_prompt,
                system_prompt="You are a senior software engineer fixing bugs. Return only the fixed code.",
                temperature=0.1,
            )

            return {
                "success": True,
                "file": {
                    "path": file_path,
                    "content": fixed_content.strip(),
                    "description": f"Fix: {bug.get('title')}",
                    "type": "bug_fix",
                    "original_content": current_content,
                },
            }
        except Exception as e:
            logger.warning("Failed to apply fix", file=file_path, error=str(e))
            return {"success": False, "error": str(e)}

    async def refactor(self, context: AgentContext, file_path: str, refactor_type: str) -> Dict[str, Any]:
        """Refactor code."""
        current_content = await self._get_file_content(context, file_path)
        if not current_content:
            return {"success": False, "error": f"File not found: {file_path}"}

        refactor_prompts = {
            "extract_method": "Extract a reusable method from duplicated code",
            "simplify_conditionals": "Simplify complex conditional logic",
            "remove_dead_code": "Remove unused code and imports",
            "improve_naming": "Improve variable and function names for clarity",
            "add_type_hints": "Add missing type hints",
            "optimize_performance": "Optimize for better performance",
        }

        instruction = refactor_prompts.get(refactor_type, "Refactor for better code quality")

        modified_content = await self._modify_file(
            file_path=file_path,
            current_content=current_content,
            instruction=instruction,
            mod_type=f"refactor_{refactor_type}",
            context={},
        )

        if not modified_content:
            return {"success": False, "error": "Failed to refactor"}

        return {
            "success": True,
            "file": {
                "path": file_path,
                "content": modified_content,
                "description": f"Refactor: {instruction}",
                "type": f"refactor_{refactor_type}",
                "original_content": current_content,
            },
        }

    async def _perform_action(self, action: str, **kwargs) -> Any:
        """Perform specific code modification actions."""
        if action == "apply_fix":
            return await self.apply_fix(kwargs.get("context"), kwargs.get("bug"))
        elif action == "refactor":
            return await self.refactor(kwargs.get("context"), kwargs.get("file_path"), kwargs.get("refactor_type"))
        elif action == "modify_file":
            return await self._modify_file(
                kwargs.get("file_path"),
                kwargs.get("current_content"),
                kwargs.get("instruction"),
                kwargs.get("mod_type"),
                kwargs.get("context"),
            )
        else:
            raise ValueError(f"Unknown action: {action}")