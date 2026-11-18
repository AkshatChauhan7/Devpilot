"""GitHub App Installation model."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Installation(Base):
    """GitHub App Installation model."""

    __tablename__ = "installations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    account_login: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)  # User or Organization
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    account_avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_html_url: Mapped[str] = mapped_column(String(500), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    permissions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    events: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    repository_selection: Mapped[str] = mapped_column(String(50), nullable=False)  # all or selected
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="installations", lazy="selectin")
    repositories: Mapped[List["Repository"]] = relationship(
        "Repository", back_populates="installation", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("github_id", name="uq_installation_github_id"),
    )

    def __repr__(self) -> str:
        return f"<Installation(id={self.id}, github_id={self.github_id}, account={self.account_login})>"