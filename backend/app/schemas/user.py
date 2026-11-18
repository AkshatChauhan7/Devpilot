"""User schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""
    github_id: int
    username: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None


class UserRead(UserBase):
    """Schema for reading a user."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class UserWithToken(UserRead):
    """User with access token."""
    access_token: str
    token_type: str = "bearer"