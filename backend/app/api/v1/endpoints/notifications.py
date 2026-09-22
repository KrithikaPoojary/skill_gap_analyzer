"""Notification REST API endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", summary="List notifications for the current user", response_model=list[dict])
def list_my_notifications(
    current_user: CurrentUser,
    db: DbSession,
    unread_only: bool = Query(False, description="Filter to unread only"),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    items = notification_service.list_notifications(
        db, user_id=current_user.id, unread_only=unread_only, limit=limit
    )
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "category": n.category,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in items
    ]


@router.patch("/{notification_id}/read", summary="Mark a notification as read", response_model=dict)
def mark_notification_read(
    notification_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> Any:
    notif = notification_service.mark_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"id": notif.id, "is_read": notif.is_read}


@router.patch("/read-all", summary="Mark all notifications as read", response_model=dict)
def mark_all_notifications_read(current_user: CurrentUser, db: DbSession) -> Any:
    count = notification_service.mark_all_read(db, user_id=current_user.id)
    return {"marked_read": count}


@router.delete("/{notification_id}", summary="Delete a notification", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    deleted = notification_service.delete_notification(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
