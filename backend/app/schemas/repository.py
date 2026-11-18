"""Repository schemas."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class RepositoryBase(BaseModel):
    """Base repository schema."""
    github_id: int
    name: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    html_url: HttpUrl
    clone_url: HttpUrl
    ssh_url: HttpUrl
    default_branch: str = Field(default="main", max_length=255)
    language: Optional[str] = Field(None, max_length=100)
    stars: int = Field(default=0, ge=0)
    forks: int = Field(default=0, ge=0)
    is_private: bool = False
    is_fork: bool = False
    is_archived: bool = False


class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository."""
    owner_id: int
    installation_id: Optional[int] = None


class RepositoryUpdate(BaseModel):
    """Schema for updating a repository."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    full_name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    default_branch: Optional[str] = Field(None, max_length=255)
    language: Optional[str] = Field(None, max_length=100)
    stars: Optional[int] = Field(None, ge=0)
    forks: Optional[int] = Field(None, ge=0)
    is_private: Optional[bool] = None
    is_archived: Optional[bool] = None
    analysis_status: Optional[str] = None
    analysis_error: Optional[str] = None


class RepositoryRead(RepositoryBase):
    """Schema for reading a repository."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    installation_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_analyzed_at: Optional[datetime] = None
    analysis_status: str
    analysis_error: Optional[str] = None


class RepositoryList(BaseModel):
    """Paginated repository list."""
    items: List[RepositoryRead]
    total: int
    page: int
    page_size: int
    total_pages: int