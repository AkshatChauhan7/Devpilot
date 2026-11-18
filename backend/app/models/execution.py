"""Execution model for code execution in isolated environments."""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExecutionStatus(str, enum.Enum):
    """Execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class Execution(Base):
    """Execution model for tracking code execution in isolated containers."""

    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    execution_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False, index=True)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    working_directory: Mapped[str] = mapped_column(String(500), default="/workspace", nullable=False)
    image: Mapped[str] = mapped_column(String(500), nullable=False)  # Docker image to use
    environment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Environment variables
    timeout: Mapped[int] = mapped_column(Integer, default=300, nullable=False)  # Seconds
    cpu_limit: Mapped[Optional[float]] = mapped_column(nullable=True)  # CPU cores
    memory_limit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "2g"
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    repository_id: Mapped[Optional[int]] = mapped_column(ForeignKey("repositories.id"), nullable=True, index=True)
    container_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
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
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="executions", lazy="selectin")
    repository: Mapped[Optional["Repository"]] = relationship("Repository", back_populates="executions", lazy="selectin")

    __table_args__ = (
        Index("ix_execution_task_status", "task_id", "status"),
        Index("ix_execution_repo_status", "repository_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Execution(id={self.id}, execution_id={self.execution_id}, status={self.status})>"