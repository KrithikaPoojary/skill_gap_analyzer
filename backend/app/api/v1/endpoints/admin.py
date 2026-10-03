"""Admin REST API endpoints — superuser-only operations."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response, status


from app.api.deps import CurrentSuperuser, DbSession
from app.repositories.user_repo import user_repository
from app.services import notification_service
from app.services.platform_stats_service import platform_stats_service

router = APIRouter(prefix="/admin", tags=["Admin"])



@router.get("/users", summary="List all registered users", response_model=dict)
def list_users(
    _: CurrentSuperuser,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """Return paginated list of all user accounts."""
    users = user_repository.get_multi(db, skip=skip, limit=limit)
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "login_count": getattr(u, "login_count", 0),
                "last_login_at": u.last_login_at.isoformat() if getattr(u, "last_login_at", None) else None,
            }
            for u in users
        ],
    }


@router.get("/users/export", summary="Export registered users as JSON or CSV")
def export_users(
    _: CurrentSuperuser,
    db: DbSession,
    format: str = Query("json", pattern="^(json|csv)$", description="Export format: json or csv"),
) -> Any:
    """Export all user accounts with activity and status metrics."""
    import csv
    import io

    users = user_repository.get_multi(db, skip=0, limit=10000)
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "email", "full_name", "is_active", "is_superuser", "login_count", "last_login_at", "created_at"])
        for u in users:
            writer.writerow([
                u.id,
                u.email,
                u.full_name or "",
                u.is_active,
                u.is_superuser,
                getattr(u, "login_count", 0),
                u.last_login_at.isoformat() if getattr(u, "last_login_at", None) else "",
                u.created_at.isoformat() if getattr(u, "created_at", None) else "",
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="users_export.csv"'},
        )
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "login_count": getattr(u, "login_count", 0),
                "last_login_at": u.last_login_at.isoformat() if getattr(u, "last_login_at", None) else None,
                "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
            }
            for u in users
        ],
    }


@router.get("/users/{user_id}", summary="Get a single user by ID", response_model=dict)

def get_user(user_id: int, _: CurrentSuperuser, db: DbSession) -> Any:
    """Fetch full user record by primary key."""
    user = user_repository.get(db, entity_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }


@router.patch("/users/{user_id}/deactivate", summary="Deactivate a user account", response_model=dict)
def deactivate_user(user_id: int, _: CurrentSuperuser, db: DbSession) -> Any:
    """Set is_active=False for the specified user."""
    user = user_repository.get(db, entity_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return {"id": user.id, "is_active": user.is_active}


@router.patch("/users/{user_id}/activate", summary="Reactivate a user account", response_model=dict)
def activate_user(user_id: int, _: CurrentSuperuser, db: DbSession) -> Any:
    """Set is_active=True for the specified user."""
    user = user_repository.get(db, entity_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return {"id": user.id, "is_active": user.is_active}


@router.get("/users/search", summary="Search users by email fragment", response_model=dict)
def search_users(
    _: CurrentSuperuser,
    db: DbSession,
    q: str = Query(..., min_length=2, description="Email search term"),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """Return users whose email contains the search term."""
    users = user_repository.search_by_email(db, query=q, limit=limit)
    return {
        "total": len(users),
        "users": [
            {"id": u.id, "email": u.email, "is_active": u.is_active}
            for u in users
        ],
    }


@router.post("/notifications/broadcast", summary="Broadcast a notification to all active users", response_model=dict)
def broadcast_notification(
    _: CurrentSuperuser,
    db: DbSession,
    title: str = Query(..., description="Notification title"),
    message: str = Query(..., description="Notification body"),
    category: str = Query("announcement", description="Notification category"),
) -> Any:
    """Create a notification record for every active user."""
    users = user_repository.get_multi(db, skip=0, limit=10000)
    active_users = [u for u in users if u.is_active]
    for user in active_users:
        notification_service.create_notification(
            db,
            user_id=user.id,
            title=title,
            message=message,
            category=category,
        )
    return {"sent_to": len(active_users), "title": title}


@router.delete("/users/{user_id}", summary="Permanently delete a user account", response_model=dict)
def delete_user(user_id: int, _: CurrentSuperuser, db: DbSession) -> Any:
    """Hard-delete a user account and all cascade data."""
    user = user_repository.get(db, entity_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    email = user.email
    db.delete(user)
    db.commit()
    return {"deleted": True, "email": email}


@router.patch("/users/{user_id}/promote", summary="Grant superuser role to a user", response_model=dict)
def promote_user(user_id: int, _: CurrentSuperuser, db: DbSession) -> Any:
    """Elevate a regular account to superuser privileges."""
    user = user_repository.get(db, entity_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_superuser = True
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "is_superuser": user.is_superuser}


@router.get("/stats/overview", summary="Platform-wide aggregated metrics overview", response_model=dict)
def get_platform_overview(_: CurrentSuperuser, db: DbSession) -> Any:
    """Return platform-wide operational statistics for monitoring dashboards."""
    return platform_stats_service.get_overview(db)

