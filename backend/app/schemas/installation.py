"""Installation schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict


class InstallationBase(BaseModel):
    """Base installation schema."""
    github_id: int
    account_login: str = Field(..., min_length=1, max_length=255)
    account_type: str = Field(..., max_length=50)
    account_id: int
    account_avatar_url: Optional[str] = None
    account_html_url: str
    target_type: str = Field(..., max_length=50)
    permissions: Dict[str, Any]
    events: List[str]
    repository_selection: str = Field(..., max_length=50)


class InstallationCreate(InstallationBase):
    """Schema for creating an installation."""
    user_id: Optional[int] = None


class InstallationRead(InstallationBase):
    """Schema for reading an installation."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    suspended_at: Optional[datetime] = None