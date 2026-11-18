"""Common response schemas."""
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseModel):
    """Error response."""
    model_config = ConfigDict(from_attributes=True)

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    code: Optional[str] = None


class SuccessResponse(BaseModel, Generic[T]):
    """Success response."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    database: str
    redis: str