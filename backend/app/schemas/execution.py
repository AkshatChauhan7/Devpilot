"""Execution schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionBase(BaseModel):
    """Base execution schema."""
    command: str
    working_directory: str = Field(default="/workspace", max_length=500)
    image: str = Field(..., max_length=500)
    environment: Optional[Dict[str, str]] = None
    timeout: int = Field(default=300, ge=1, le=3600)
    cpu_limit: Optional[float] = Field(None, gt=0, le=16)
    memory_limit: Optional[str] = Field(None, pattern=r"^\d+[gmk]?$")


class ExecutionCreate(ExecutionBase):
    """Schema for creating an execution."""
    task_id: Optional[int] = None
    repository_id: Optional[int] = None


class ExecutionRead(ExecutionBase):
    """Schema for reading an execution."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: str
    status: ExecutionStatus
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    task_id: Optional[int] = None
    repository_id: Optional[int] = None
    container_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime