"""Execution tasks."""
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.execution import Execution, ExecutionStatus
from app.services.execution import ExecutionService

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=1, default_retry_delay=30)
def run_execution_task(self, execution_id: int):
    """Run code execution in isolated container."""
    import asyncio

    async def _run():
        async with get_db_context() as db:
            result = await db.execute(select(Execution).where(Execution.id == execution_id))
            execution = result.scalar_one_or_none()
            if not execution:
                logger.error("Execution not found", execution_id=execution_id)
                return

            execution.status = ExecutionStatus.RUNNING
            execution.started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            await db.commit()

            try:
                service = ExecutionService()
                await service._run_execution(execution_id)

            except Exception as e:
                logger.exception("Execution failed", execution_id=execution_id, error=str(e))
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                await db.commit()
                raise

    asyncio.run(_run())


@shared_task(bind=True, max_retries=0)
def cleanup_execution_task(self, execution_id: int):
    """Clean up execution resources."""
    import asyncio

    async def _cleanup():
        async with get_db_context() as db:
            result = await db.execute(select(Execution).where(Execution.id == execution_id))
            execution = result.scalar_one_or_none()
            if not execution or not execution.container_id:
                return

            service = ExecutionService()
            await service._cleanup_container(execution.container_id)

    asyncio.run(_cleanup())