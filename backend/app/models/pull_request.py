"""Pull Request model."""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PRStatus(str, enum.Enum):
    """Pull Request status."""
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    FAILED = "failed"


class PullRequest(Base):
    """Pull Request model for tracking PRs created by DevPilot."""

    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_pr_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, index=True, nullable=True)
    github_pr_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    head_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    status: Mapped[PRStatus] = mapped_column(Enum(PRStatus), default=PRStatus.DRAFT, nullable=False, index=True)
    is_draft: Mapped[bool] = mapped_column(default=True, nullable=False)
    mergeable: Mapped[Optional[bool]] = mapped_column(nullable=True)
    merge_commit_sha: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    head_sha: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    base_sha: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    changes_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    files_changed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    additions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deletions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False, index=True)
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
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="pull_requests", lazy="selectin")
    repository: Mapped["Repository"] = relationship("Repository", back_populates="pull_requests", lazy="selectin")

    __table_args__ = (
        Index("ix_pull_request_repo_status", "repository_id", "status"),
        Index("ix_pull_request_task", "task_id"),
    )

    def __repr__(self) -> str:
        return f"<PullRequest(id={self.id}, github_pr_number={self.github_pr_number}, status={self.status})>"