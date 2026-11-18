"""Task endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskType
from app.schemas.task import TaskRead, TaskCreate, TaskUpdate, TaskList, TaskStatus as TaskStatusEnum, TaskType as TaskTypeEnum
from app.schemas.common import PaginatedResponse
from app.tasks.base import celery_app

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TaskRead])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: TaskStatusEnum | None = Query(None),
    type: TaskTypeEnum | None = Query(None),
    repository_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks for the current user."""
    query = select(Task).where(Task.user_id == current_user.id)

    if status:
        query = query.where(Task.status == status)

    if type:
        query = query.where(Task.type == type)

    if repository_id:
        query = query.where(Task.repository_id == repository_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Task.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .options(selectinload(Task.repository), selectinload(Task.subtasks))
    )
    tasks = result.scalars().all()

    return PaginatedResponse.create(
        items=[TaskRead.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(
    task_create: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task."""
    # Verify repository access if provided
    if task_create.repository_id:
        from app.models.repository import Repository
        result = await db.execute(
            select(Repository).where(
                Repository.id == task_create.repository_id,
                Repository.owner_id == current_user.id,
            )
        )
        repository = result.scalar_one_or_none()
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")

    # Create task
    import uuid
    task = Task(
        task_id=str(uuid.uuid4())[:8],
        type=task_create.type,
        title=task_create.title,
        description=task_create.description,
        input_data=task_create.input_data,
        user_id=current_user.id,
        repository_id=task_create.repository_id,
        parent_task_id=task_create.parent_task_id,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Queue task for execution
    background_tasks.add_task(queue_task, task.id)

    return TaskRead.model_validate(task)


async def queue_task(task_id: int):
    """Queue task for Celery execution."""
    # This would be implemented with actual Celery tasks
    pass


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task by ID."""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id, Task.user_id == current_user.id)
        .options(selectinload(Task.repository), selectinload(Task.subtasks), selectinload(Task.executions))
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return TaskRead.model_validate(task)


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a running task."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")

    task.status = TaskStatus.CANCELLED

    # Cancel Celery task if running
    if task.celery_task_id:
        celery_app.control.revoke(task.celery_task_id, terminate=True)

    await db.commit()

    return {"message": "Task cancelled successfully"}


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task execution logs."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # In production, fetch logs from execution service or Celery
    return {
        "task_id": task.id,
        "logs": "Task logs would be fetched from execution service",
    }