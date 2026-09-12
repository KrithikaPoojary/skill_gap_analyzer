"""Unit tests for pagination and job filter parameter schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.enums import EmploymentType, ExperienceLevel
from app.schemas.job_filter import JobFilterParams
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)


class TestPaginationSchemas:
    """Test suite for pagination parameters and response structures."""

    def test_pagination_params_defaults(self) -> None:
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0
        assert params.limit == 20

    def test_pagination_params_custom(self) -> None:
        params = PaginationParams(page=3, page_size=25)
        assert params.page == 3
        assert params.page_size == 25
        assert params.offset == 50
        assert params.limit == 25

    def test_pagination_params_bounds_validation(self) -> None:
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

        with pytest.raises(ValidationError):
            PaginationParams(page_size=150)

    def test_pagination_meta_computation(self) -> None:
        meta = PaginationMeta.create(total_items=95, page=1, page_size=20)
        assert meta.total_items == 95
        assert meta.page == 1
        assert meta.page_size == 20
        assert meta.total_pages == 5
        assert meta.has_next is True
        assert meta.has_prev is False

        # Last page
        last_meta = PaginationMeta.create(total_items=95, page=5, page_size=20)
        assert last_meta.has_next is False
        assert last_meta.has_prev is True

    def test_paginated_response_serialization(self) -> None:
        meta = PaginationMeta.create(total_items=2, page=1, page_size=10)
        resp = PaginatedResponse[str](items=["item1", "item2"], pagination=meta)
        assert len(resp.items) == 2
        assert resp.pagination.total_items == 2


class TestJobFilterParams:
    """Test suite for JobFilterParams search query validation."""

    def test_filter_params_defaults(self) -> None:
        filters = JobFilterParams()
        assert filters.is_active is True
        assert filters.query is None
        assert filters.is_remote is None

    def test_filter_params_custom(self) -> None:
        filters = JobFilterParams(
            query="python fastapi",
            is_remote=True,
            employment_type=EmploymentType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            min_salary=100000.0,
            skill_ids=[1, 2, 3],
        )
        assert filters.query == "python fastapi"
        assert filters.is_remote is True
        assert filters.employment_type == EmploymentType.FULL_TIME
        assert filters.skill_ids == [1, 2, 3]
