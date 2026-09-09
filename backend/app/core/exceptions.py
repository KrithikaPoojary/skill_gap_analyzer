"""Centralised HTTP exception definitions and standardised error schema.

Every API error in this application returns a consistent JSON envelope:

    {
        "success": false,
        "error": {
            "code":    "NOT_FOUND",
            "message": "The requested resource was not found.",
            "detail":  null          # optional extra context
        }
    }

This makes client-side error handling predictable regardless of which
endpoint raised the error.
"""

from typing import Any

from pydantic import BaseModel


# ── Error payload models ──────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Inner error object carried inside every error response."""

    code: str
    """Machine-readable error code, e.g. 'NOT_FOUND', 'VALIDATION_ERROR'."""

    message: str
    """Human-readable description suitable for display in a UI."""

    detail: Any = None
    """Optional extra context (validation field errors, stack hint, etc.)."""


class ErrorResponse(BaseModel):
    """Top-level error response envelope returned for all HTTP error statuses."""

    success: bool = False
    error: ErrorDetail


# ── Canonical error factories ─────────────────────────────────────────────────

def not_found_error(resource: str = "Resource") -> ErrorResponse:
    """Build a standardised 404 Not Found error response.

    Args:
        resource: Human-friendly name of the missing resource.

    Returns:
        ErrorResponse: Serialisable error envelope.
    """
    return ErrorResponse(
        error=ErrorDetail(
            code="NOT_FOUND",
            message=f"{resource} was not found.",
        )
    )


def validation_error(detail: Any = None) -> ErrorResponse:
    """Build a standardised 422 Unprocessable Entity error response.

    Args:
        detail: Pydantic validation error list or custom message.

    Returns:
        ErrorResponse: Serialisable error envelope.
    """
    return ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed. Check the 'detail' field for specifics.",
            detail=detail,
        )
    )


def internal_server_error(detail: Any = None) -> ErrorResponse:
    """Build a standardised 500 Internal Server Error response.

    Args:
        detail: Optional debug hint (only exposed in development environments).

    Returns:
        ErrorResponse: Serialisable error envelope.
    """
    return ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            detail=detail,
        )
    )


def bad_request_error(message: str, detail: Any = None) -> ErrorResponse:
    """Build a standardised 400 Bad Request error response.

    Args:
        message: Reason the request was rejected.
        detail:  Optional supplementary information.

    Returns:
        ErrorResponse: Serialisable error envelope.
    """
    return ErrorResponse(
        error=ErrorDetail(
            code="BAD_REQUEST",
            message=message,
            detail=detail,
        )
    )
