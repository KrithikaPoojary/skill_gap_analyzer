"""Tests for the APIResponse envelope schema.

Verifies:
- ok() factory produces a valid APIResponse.
- success field is True for ok() responses.
- data field carries the payload correctly.
- message field defaults to 'OK' and can be overridden.
- ErrorResponse has success=False and contains an error field.
- ErrorResponse error factories produce expected codes.
"""

import pytest

from app.core.exceptions import (
    bad_request_error,
    internal_server_error,
    not_found_error,
    validation_error,
)
from app.schemas.response import APIResponse, ok


class TestAPIResponseEnvelope:
    """Unit tests for the APIResponse success envelope."""

    def test_ok_returns_api_response_instance(self) -> None:
        """ok() must return an APIResponse instance."""
        result = ok(data={"key": "value"})
        assert isinstance(result, APIResponse)

    def test_ok_success_is_true(self) -> None:
        """ok() result must have success=True."""
        assert ok(data={}).success is True

    def test_ok_carries_data_payload(self) -> None:
        """ok() must embed the given data in the data field."""
        payload = {"job_id": 42, "title": "Data Analyst"}
        result = ok(data=payload)
        assert result.data == payload

    def test_ok_default_message_is_ok(self) -> None:
        """ok() default message must be 'OK'."""
        assert ok(data=None).message == "OK"

    def test_ok_custom_message(self) -> None:
        """ok() must accept a custom message string."""
        result = ok(data={}, message="Profile retrieved successfully")
        assert result.message == "Profile retrieved successfully"

    def test_ok_serialises_to_dict(self) -> None:
        """model_dump() on ok() result must produce a JSON-serialisable dict."""
        result = ok(data={"x": 1})
        dumped = result.model_dump()
        assert dumped["success"] is True
        assert dumped["data"] == {"x": 1}


class TestErrorFactories:
    """Unit tests for the ErrorResponse factory functions."""

    def test_not_found_error_has_correct_code(self) -> None:
        """not_found_error() must produce code='NOT_FOUND'."""
        err = not_found_error()
        assert err.error.code == "NOT_FOUND"

    def test_validation_error_has_correct_code(self) -> None:
        """validation_error() must produce code='VALIDATION_ERROR'."""
        err = validation_error()
        assert err.error.code == "VALIDATION_ERROR"

    def test_internal_server_error_has_correct_code(self) -> None:
        """internal_server_error() must produce code='INTERNAL_SERVER_ERROR'."""
        err = internal_server_error()
        assert err.error.code == "INTERNAL_SERVER_ERROR"

    def test_bad_request_error_has_correct_code(self) -> None:
        """bad_request_error() must produce code='BAD_REQUEST'."""
        err = bad_request_error(message="Invalid input")
        assert err.error.code == "BAD_REQUEST"

    def test_error_response_success_is_false(self) -> None:
        """All error factory results must have success=False."""
        for err in [not_found_error(), validation_error(), internal_server_error()]:
            assert err.success is False

    def test_validation_error_carries_detail(self) -> None:
        """validation_error() must embed the supplied detail."""
        detail = [{"loc": ["body", "name"], "msg": "field required"}]
        err = validation_error(detail=detail)
        assert err.error.detail == detail
