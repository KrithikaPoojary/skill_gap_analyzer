"""Generic pagination parameters and response schemas."""

import math
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard query parameters for pagination."""

    page: int = Field(1, ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")

    @property
    def offset(self) -> int:
        """Calculate SQL OFFSET value."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Calculate SQL LIMIT value."""
        return self.page_size


class PaginationMeta(BaseModel):
    """Metadata describing pagination state and navigation capabilities."""

    total_items: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, *, total_items: int, page: int, page_size: int) -> "PaginationMeta":
        """Compute pagination metadata from counts."""
        total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0
        return cls(
            total_items=total_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard generic wrapper for paginated entity collections."""

    items: list[T]
    pagination: PaginationMeta
