"""Agent orchestration tasks."""
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.task import Task, TaskStatus, TaskType
from app.models.repository import Repository
from app.agents.orchestrator import AgentOrchestrator

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_agent_task(self, task_id: int):
    """Run an agent task."""
    import asyncio

    async def _run():
        async with get_db_context() as db:
            # Get task
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if not task:
                logger.error("Task not found", task_id=task_id)
                return

            task.status = TaskStatus.RUNNING
            task.progress = 0
            await db.commit()

            try:
                orchestrator = AgentOrchestrator()
                result = await orchestrator.run_task(task)

                task.output_data = result
                task.progress = 100
                task.status = TaskStatus.COMPLETED
                await db.commit()

            except Exception as e:
                logger.exception("Agent task failed", task_id=task_id, error=str(e))
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                await db.commit()
                raise

    asyncio.run(_run())


@shared_task(bind=True, max_retries=1, default_retry_delay=30)
def run_bug_detection_task(self, repository_id: int, user_id: int):
    """Run bug detection on repository."""
    import asyncio

    async def _run():
        async with get_db_context() as db:
            # Create parent task
            parent_task = Task(
                task_id=f"bug_detection_{repository_id}",
                type=TaskType.BUG_DETECTION,
                title=f"Bug detection for repository {repository_id}",
                status=TaskStatus.RUNNING,
                user_id=user_id,
                repository_id=repository_id,
                progress=0,
                total_steps=3,
            )
            db.add(parent_task)
            await db.commit()
            await db.refresh(parent_task)

            try:
                # Step 1: Analyze repository structure
                parent_task.progress = 20
                parent_task.current_step = "Analyzing repository structure"
                await db.commit()

                # Step 2: Run agent-based bug detection
                parent_task.progress = 50
                parent_task.current_step = "Running bug detection agents"
                await db.commit()

                orchestrator = AgentOrchestrator()
                bugs = await orchestrator.detect_bugs(repository_id)

                # Step 3: Create subtasks for each bug
                parent_task.progress = 80
                parent_task.current_step = "Creating fix tasks"
                await db.commit()

                for bug in bugs:
                    subtask = Task(
                        task_id=f"bug_fix_{bug['id']}",
                        type=TaskType.CODE_MODIFICATION,
                        title=f"Fix: {bug['title']}",
                        description=bug.get("description", ""),
                        input_data=bug,
                        user_id=user_id,
                        repository_id=repository_id,
                        parent_task_id=parent_task.id,
                        status=TaskStatus.PENDING,
                    )
                    db.add(subtask)

                parent_task.progress = 100
                parent_task.current_step = f"Found {len(bugs)} potential issues"
                parent_task.status = TaskStatus.COMPLETED
                parent_task.output_data = {"bugs_found": len(bugs), "bugs": bugs}
                await db.commit()

            except Exception as e:
                logger.exception("Bug detection failed", repository_id=repository_id, error=str(e))
                parent_task.status = TaskStatus.FAILED
                parent_task.error_message = str(e)
                await db.commit()
                raise

    asyncio.run(_run())


@shared_task(bind=True, max_retries=1, default_retry_delay=30)
def run_code_generation_task(self, repository_id: int, user_id: int, spec: dict):
    """Run code generation based on specification."""
    import asyncio

    async def _run():
        async with get_db_context() as db:
            parent_task = Task(
                task_id=f"code_gen_{repository_id}",
                type=TaskType.CODE_GENERATION,
                title=f"Code generation for repository {repository_id}",
                status=TaskStatus.RUNNING,
                user_id=user_id,
                repository_id=repository_id,
                input_data=spec,
                progress=0,
                total_steps=3,
            )
            db.add(parent_task)
            await db.commit()
            await db.refresh(parent_task)

            try:
                parent_task.progress = 30
                parent_task.current_step = "Analyzing requirements"
                await db.commit()

                orchestrator = AgentOrchestrator()
                generated = await orchestrator.generate_code(repository_id, spec)

                parent_task.progress = 70
                parent_task.current_step = "Creating implementation tasks"
                await db.commit()

                for file_change in generated.get("files", []):
                    subtask = Task(
                        task_id=f"code_gen_file_{file_change['path']}",
                        type=TaskType.CODE_MODIFICATION,
                        title=f"Create/Update: {file_change['path']}",
                        description=file_change.get("description", ""),
                        input_data=file_change,
                        user_id=user_id,
                        repository_id=repository_id,
                        parent_task_id=parent_task.id,
                        status=TaskStatus.PENDING,
                    )
                    db.add(subtask)

                parent_task.progress = 100
                parent_task.current_step = f"Generated {len(generated.get('files', []))} files"
                parent_task.status = TaskStatus.COMPLETED
                parent_task.output_data = generated
                await db.commit()

            except Exception as e:
                logger.exception("Code generation failed", repository_id=repository_id, error=str(e))
                parent_task.status = TaskStatus.FAILED
                parent_task.error_message = str(e)
                await db.commit()
                raise

    asyncio.run(_run())


@shared_task(bind=True, max_retries=1, default_retry_delay=30)
def run_test_generation_task(self, repository_id: int, user_id: int, target_files: list[str]):
    """Generate tests for specified files."""
    import asyncio

    async def _run():
        async with get_db_context() as db:
            parent_task = Task(
                task_id=f"test_gen_{repository_id}",
                type=TaskType.TEST_GENERATION,
                title=f"Test generation for repository {repository_id}",
                status=TaskStatus.RUNNING,
                user_id=user_id,
                repository_id=repository_id,
                input_data={"target_files": target_files},
                progress=0,
                total_steps=3,
            )
            db.add(parent_task)
            await db.commit()
            await db.refresh(parent_task)

            try:
                orchestrator = AgentOrchestrator()
                tests = await orchestrator.generate_tests(repository_id, target_files)

                for test_file in tests.get("files", []):
                    subtask = Task(
                        task_id=f"test_gen_file_{test_file['path']}",
                        type=TaskType.CODE_MODIFICATION,
                        title=f"Create test: {test_file['path']}",
                        description=test_file.get("description", ""),
                        input_data=test_file,
                        user_id=user_id,
                        repository_id=repository_id,
                        parent_task_id=parent_task.id,
                        status=TaskStatus.PENDING,
                    )
                    db.add(subtask)

                parent_task.progress = 100
                parent_task.current_step = f"Generated {len(tests.get('files', []))} test files"
                parent_task.status = TaskStatus.COMPLETED
                parent_task.output_data = tests
                await db.commit()

            except Exception as e:
                logger.exception("Test generation failed", repository_id=repository_id, error=str(e))
                parent_task.status = TaskStatus.FAILED
                parent_task.error_message = str(e)
                await db.commit()
                raise

    asyncio.run(_run())