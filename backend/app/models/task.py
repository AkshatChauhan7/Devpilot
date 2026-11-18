"""Task model for tracking async operations."""
import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
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


class Task(Base):
    """Task model for tracking asynchronous operations."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    current_step: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_steps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    repository_id: Mapped[Optional[int]] = mapped_column(ForeignKey("repositories.id"), nullable=True, index=True)
    parent_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks", lazy="selectin")
    repository: Mapped[Optional["Repository"]] = relationship("Repository", back_populates="tasks", lazy="selectin")
    parent_task: Mapped[Optional["Task"]] = relationship("Task", remote_side=[id], backref="subtasks", lazy="selectin")
    executions: Mapped[List["Execution"]] = relationship("Execution", back_populates="task", lazy="selectin")
    pull_requests: Mapped[List["PullRequest"]] = relationship("PullRequest", back_populates="task", lazy="selectin")

    __table_args__ = (
        Index("ix_task_user_status", "user_id", "status"),
        Index("ix_task_repo_status", "repository_id", "status"),
        Index("ix_task_type_status", "type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, task_id={self.task_id}, type={self.type}, status={self.status})>"