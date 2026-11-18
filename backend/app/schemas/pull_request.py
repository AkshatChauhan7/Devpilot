"""Pull Request schemas."""
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class PRStatus(str, Enum):
    """Pull Request status."""
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    FAILED = "failed"


class PullRequestBase(BaseModel):
    """Base pull request schema."""
    title: str = Field(..., min_length=1, max_length=500)
    body: Optional[str] = None
    head_branch: str = Field(..., min_length=1, max_length=255)
    base_branch: str = Field(default="main", min_length=1, max_length=255)
    is_draft: bool = True
    review_required: bool = True


class PullRequestCreate(PullRequestBase):
    """Schema for creating a pull request."""
    task_id: Optional[int] = None
    repository_id: int


class PullRequestUpdate(BaseModel):
    """Schema for updating a pull request."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = None
    status: Optional[PRStatus] = None
    is_draft: Optional[bool] = None
    mergeable: Optional[bool] = None
    approved_by: Optional[str] = None


class PullRequestRead(PullRequestBase):
    """Schema for reading a pull request."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    github_pr_id: Optional[int] = None
    github_pr_number: Optional[int] = None
    status: PRStatus
    mergeable: Optional[bool] = None
    merge_commit_sha: Optional[str] = None
    head_sha: Optional[str] = None
    base_sha: Optional[str] = None
    changes_summary: Optional[str] = None
    files_changed: Optional[int] = None
    additions: Optional[int] = None
    deletions: Optional[int] = None
    approved_by: Optional[str] = None
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    task_id: Optional[int] = None
    repository_id: int
    created_at: datetime
    updated_at: datetime