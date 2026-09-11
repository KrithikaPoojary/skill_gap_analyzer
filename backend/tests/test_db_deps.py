"""Unit tests for database session FastAPI dependency injection."""

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.api.deps import DbSession, get_db
from app.db.session import SessionLocal


class TestDatabaseDependency:
    """Test suite for get_db dependency provider and FastAPI integration."""

    def test_get_db_generator_lifecycle(self) -> None:
        db_gen = get_db()
        session = next(db_gen)
        assert isinstance(session, Session)
        # Advance generator to simulate request completion
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected generator completion

    def test_endpoint_dependency_injection(self) -> None:
        test_app = FastAPI()

        @test_app.get("/test-db-inject")
        def route_with_db(db: DbSession):
            return {"active": db.is_active}

        with TestClient(test_app) as client:
            response = client.get("/test-db-inject")
            assert response.status_code == 200
            assert response.json() == {"active": True}

    def test_dependency_override_in_testing(self) -> None:
        test_app = FastAPI()

        @test_app.get("/test-override")
        def route_override(db: Session = Depends(get_db)):
            return {"overridden": True}

        # Override get_db with dummy
        def fake_get_db():
            yield "mock_session"

        test_app.dependency_overrides[get_db] = fake_get_db

        with TestClient(test_app) as client:
            response = client.get("/test-override")
            assert response.status_code == 200
            assert response.json() == {"overridden": True}
