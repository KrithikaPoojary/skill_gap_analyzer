"""Shared pytest fixtures and test configuration.

Any fixture defined here is automatically available to all tests in the
``tests/`` directory without explicit import.

Fixtures added today:
- ``client`` — a synchronous Starlette TestClient backed by the FastAPI app.
"""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provide a reusable Starlette TestClient for the FastAPI application.

    ``TestClient`` is the correct synchronous test transport for ASGI apps.
    Using ``scope="module"`` means the app lifecycle is shared across all
    tests in a module, improving performance without sacrificing isolation.

    Yields:
        starlette.testclient.TestClient: A synchronous test client connected
        to the ASGI app.
    """
    with TestClient(app=app, base_url="http://testserver") as c:
        yield c
