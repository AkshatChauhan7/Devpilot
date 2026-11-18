"""Task schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task types."""
    REPOSITORY_ANALYSIS = "repository_analysis"
    BUG_DETECTION = "bug_detection"
    CODE_GENERATION = "code_generation"
    CODE_MODIFICATION = "code_modification"
    TEST_GENERATION = "test_generation"
    TEST_EXECUTION = "test_execution"
    PR_CREATION = "pr_creation"
    DEPENDENCY_UPDATE = "dependency_update"
    SECURITY_SCAN = "security_scan"


class TaskBase(BaseModel):
    """Base task schema."""
    type: TaskType
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    user_id: int
    repository_id: Optional[int] = None
    parent_task_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    status: Optional[TaskStatus] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    total_steps: Optional[int] = Field(None, ge=1)
    celery_task_id: Optional[str] = None


class TaskRead(TaskBase):
    """Schema for reading a task."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    status: TaskStatus
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: int
    current_step: Optional[str] = None
    total_steps: int
    user_id: int
    repository_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TaskList(BaseModel):
    """Paginated task list."""
    items: List[TaskRead]
    total: int
    page: int
    page_size: int
    total_pages: int