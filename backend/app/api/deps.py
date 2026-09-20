"""FastAPI route dependencies.

Provides reusable dependency providers for database sessions, authentication,
and common query parameters.
"""

from collections.abc import Generator
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Provide an isolated database session per request.

    Ensures transactions are closed cleanly after request processing.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Type alias for cleaner endpoint signatures
DbSession = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------- #
# Authentication & User Context Dependencies
# ---------------------------------------------------------------------- #
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repo import user_repository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False,
)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    """Validate bearer JWT token and return authenticated User entity."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(token)
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise ValueError("Token missing subject claim.")
        user_id = int(user_id_raw)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = user_repository.get(db, entity_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with token not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure that the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    return current_user


def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Ensure that the authenticated user possesses administrator privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges.",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
