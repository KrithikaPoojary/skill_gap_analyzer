"""Generic API response envelope schema.

Every successful API response in this application is wrapped in an
``APIResponse[T]`` envelope:

    {
        "success": true,
        "data": { ... },        # the actual payload, type-safe via Generic[T]
        "message": "OK"         # optional human-readable status note
    }

This symmetry with the ``ErrorResponse`` envelope means clients always
deal with the same outer shape — they check ``success`` first and then
read either ``data`` or ``error``.

Usage example in an endpoint:
    from app.schemas.response import ok
    return ok({"job_id": 42, "title": "Data Analyst"})
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

# Generic type variable representing the payload shape
T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard success response wrapper returned by all successful endpoints.

    Attributes:
        success: Always ``True`` for successful responses.
        data:    The endpoint-specific response payload.
        message: Optional human-readable status message.
    """

    success: bool = True
    data: Optional[T] = None
    message: str = "OK"


def ok(data: Any, message: str = "OK") -> APIResponse:
    """Shorthand factory for building a successful ``APIResponse``.

    Args:
        data:    The response payload to embed.
        message: Optional status note (default: 'OK').

    Returns:
        APIResponse: A populated success envelope ready for serialisation.

    Example::

        return ok({"user_id": 1, "name": "Alice"}, message="Profile retrieved")
    """
    return APIResponse(success=True, data=data, message=message)
