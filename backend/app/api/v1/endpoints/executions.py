"""Execution endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.execution import Execution, ExecutionStatus
from app.schemas.execution import ExecutionRead, ExecutionCreate, ExecutionStatus as ExecutionStatusEnum
from app.schemas.common import PaginatedResponse
from app.services.execution import ExecutionService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ExecutionRead])
async def list_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ExecutionStatusEnum | None = Query(None),
    task_id: int | None = Query(None),
    repository_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List executions for the current user."""
    # Join with task to filter by user
    query = select(Execution).join(Execution.task).where(Task.user_id == current_user.id)

    if status:
        query = query.where(Execution.status == status)

    if task_id:
        query = query.where(Execution.task_id == task_id)

    if repository_id:
        query = query.where(Execution.repository_id == repository_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Execution.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(selectinload(Execution.task), selectinload(Execution.repository))
    )
    executions = result.scalars().all()

    return PaginatedResponse.create(
        items=[ExecutionRead.model_validate(e) for e in executions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ExecutionRead, status_code=201)
async def create_execution(
    execution_create: ExecutionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create and start a new execution."""
    # Verify task access if provided
    if execution_create.task_id:
        from app.models.task import Task
        result = await db.execute(
            select(Task).where(Task.id == execution_create.task_id, Task.user_id == current_user.id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

    # Verify repository access if provided
    if execution_create.repository_id:
        from app.models.repository import Repository
        result = await db.execute(
            select(Repository).where(
                Repository.id == execution_create.repository_id,
                Repository.owner_id == current_user.id,
            )
        )
        repository = result.scalar_one_or_none()
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")

    # Create execution
    import uuid
    execution = Execution(
        execution_id=str(uuid.uuid4())[:8],
        command=execution_create.command,
        working_directory=execution_create.working_directory,
        image=execution_create.image,
        environment=execution_create.environment,
        timeout=execution_create.timeout,
        cpu_limit=execution_create.cpu_limit,
        memory_limit=execution_create.memory_limit,
        task_id=execution_create.task_id,
        repository_id=execution_create.repository_id,
        status=ExecutionStatus.PENDING,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Queue execution
    execution_service = ExecutionService()
    await execution_service.queue_execution(execution.id)

    return ExecutionRead.model_validate(execution)


@router.get("/{execution_id}", response_model=ExecutionRead)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution by ID."""
    result = await db.execute(
        select(Execution)
        .join(Execution.task)
        .where(Execution.id == execution_id, Task.user_id == current_user.id)
        .options(selectinload(Execution.task), selectinload(Execution.repository))
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionRead.model_validate(execution)


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a running execution."""
    result = await db.execute(
        select(Execution)
        .join(Execution.task)
        .where(Execution.id == execution_id, Task.user_id == current_user.id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.QUEUED, ExecutionStatus.PREPARING, ExecutionStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Execution cannot be cancelled")

    execution_service = ExecutionService()
    await execution_service.cancel_execution(execution.id)

    execution.status = ExecutionStatus.CANCELLED
    await db.commit()

    return {"message": "Execution cancelled successfully"}


@router.get("/{execution_id}/logs")
async def get_execution_logs(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution logs."""
    result = await db.execute(
        select(Execution)
        .join(Execution.task)
        .where(Execution.id == execution_id, Task.user_id == current_user.id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution_service = ExecutionService()
    logs = await execution_service.get_logs(execution.id)

    return {
        "execution_id": execution.id,
        "stdout": execution.stdout,
        "stderr": execution.stderr,
        "logs": logs,
    }