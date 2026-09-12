"""Global HTTP exception handlers for the FastAPI application.

These handlers intercept exceptions raised anywhere in the request lifecycle
and transform them into the standardised ``ErrorResponse`` envelope defined
in ``app.core.exceptions``.

Registered handlers:
- ``404 Not Found``          — unknown routes or missing resources
- ``405 Method Not Allowed`` — wrong HTTP verb for a valid route
- ``422 Unprocessable Entity``— Pydantic request-body validation failures
- ``500 Internal Server Error``— any unhandled exception
"""

import logging
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    ErrorDetail,
    ErrorResponse,
    internal_server_error,
    not_found_error,
    validation_error,
)

logger = logging.getLogger(__name__)


# ── Individual handler functions ──────────────────────────────────────────────

async def http_404_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle 404 Not Found — unknown URL path or missing resource.

    Args:
        request: The incoming HTTP request.
        exc:     The Starlette HTTPException that was raised.

    Returns:
        JSONResponse: Standardised 404 error envelope.
    """
    logger.warning("404 Not Found: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=404,
        content=not_found_error("The requested endpoint or resource").model_dump(),
    )


async def http_405_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle 405 Method Not Allowed.

    Args:
        request: The incoming HTTP request.
        exc:     The Starlette HTTPException that was raised.

    Returns:
        JSONResponse: Standardised 405 error envelope.
    """
    logger.warning("405 Method Not Allowed: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=405,
        content=ErrorResponse(
            error=ErrorDetail(
                code="METHOD_NOT_ALLOWED",
                message=f"HTTP method '{request.method}' is not allowed for this endpoint.",
            )
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle any Starlette HTTPException not covered by specific handlers.

    Falls through from 404/405 handlers for other 4xx/5xx status codes.

    Args:
        request: The incoming HTTP request.
        exc:     The Starlette HTTPException that was raised.

    Returns:
        JSONResponse: Standardised error envelope matching the exception status.
    """
    logger.warning(
        "HTTP %s: %s %s — %s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
            )
        ).model_dump(),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle 422 Unprocessable Entity — Pydantic request validation failures.

    Extracts the validation error list and embeds it in the standard
    ``ErrorResponse.error.detail`` field so clients can map errors to fields.

    Args:
        request: The incoming HTTP request.
        exc:     The FastAPI RequestValidationError.

    Returns:
        JSONResponse: Standardised 422 error envelope with field-level detail.
    """
    errors: list[Any] = exc.errors()
    safe_errors: list[Any] = []
    for err in errors:
        if isinstance(err, dict):
            clean_err = {}
            for k, v in err.items():
                if k == "ctx" and isinstance(v, dict):
                    clean_err[k] = {
                        ck: str(cv) if isinstance(cv, Exception) else cv
                        for ck, cv in v.items()
                    }
                else:
                    clean_err[k] = v
            safe_errors.append(clean_err)
        else:
            safe_errors.append(err)

    logger.warning(
        "422 Validation Error: %s %s — %d error(s)",
        request.method,
        request.url.path,
        len(safe_errors),
    )
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(validation_error(detail=safe_errors).model_dump()),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exception as 500 Internal Server Error.

    Logs the full traceback for debugging while returning a safe generic
    message to the client (no internal details leaked in production).

    Args:
        request: The incoming HTTP request.
        exc:     The unhandled Python exception.

    Returns:
        JSONResponse: Standardised 500 error envelope.
    """
    logger.exception(
        "500 Unhandled Exception: %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content=internal_server_error().model_dump(),
    )


# ── Registration helper ───────────────────────────────────────────────────────

def register_exception_handlers(app: Any) -> None:
    """Attach all global exception handlers to the FastAPI application.

    Called once inside ``create_application()`` in ``app/main.py``.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(404, http_404_handler)
    app.add_exception_handler(405, http_405_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
