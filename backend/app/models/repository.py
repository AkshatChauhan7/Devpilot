"""Repository model."""
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Repository(Base):
    """Repository model for tracking GitHub repositories."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_url: Mapped[str] = mapped_column(String(500), nullable=False)
    clone_url: Mapped[str] = mapped_column(String(500), nullable=False)
    ssh_url: Mapped[str] = mapped_column(String(500), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    installation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("installations.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    analysis_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="repositories", lazy="selectin")
    installation: Mapped[Optional["Installation"]] = relationship(
        "Installation", back_populates="repositories", lazy="selectin"
    )
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="repository", lazy="selectin")
    executions: Mapped[List["Execution"]] = relationship("Execution", back_populates="repository", lazy="selectin")
    pull_requests: Mapped[List["PullRequest"]] = relationship("PullRequest", back_populates="repository", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("github_id", name="uq_repository_github_id"),
        Index("ix_repository_owner_full_name", "owner_id", "full_name"),
    )

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, github_id={self.github_id}, full_name={self.full_name})>"