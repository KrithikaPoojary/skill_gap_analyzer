"""Notification service — create, list, and mark notifications."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    category: str = "general",
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def list_notifications(
    db: Session,
    *,
    user_id: int,
    unread_only: bool = False,
    category: str | None = None,
    limit: int = 50,
) -> list[Notification]:
    q = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    if category:
        q = q.filter(Notification.category == category)
    return q.order_by(Notification.created_at.desc()).limit(limit).all()


def get_notification_stats(db: Session, *, user_id: int) -> dict:
    """Return count of total, unread, read, and category breakdown for a user."""
    from sqlalchemy import func
    rows = (
        db.query(Notification.category, Notification.is_read, func.count(Notification.id))
        .filter(Notification.user_id == user_id)
        .group_by(Notification.category, Notification.is_read)
        .all()
    )
    total = sum(r[2] for r in rows)
    unread = sum(r[2] for r in rows if not r[1])
    read = total - unread
    by_category: dict[str, dict[str, int]] = {}
    for cat, is_read, cnt in rows:
        if cat not in by_category:
            by_category[cat] = {"total": 0, "unread": 0, "read": 0}
        by_category[cat]["total"] += cnt
        if is_read:
            by_category[cat]["read"] += cnt
        else:
            by_category[cat]["unread"] += cnt
    return {
        "total": total,
        "unread": unread,
        "read": read,
        "by_category": by_category,
    }



def mark_read(db: Session, *, notification_id: int, user_id: int) -> Notification | None:
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_read(db: Session, *, user_id: int) -> int:
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return count


def delete_notification(db: Session, *, notification_id: int, user_id: int) -> bool:
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if notif:
        db.delete(notif)
        db.commit()
        return True
    return False


def clear_read_notifications(db: Session, *, user_id: int) -> int:
    """Delete all read notifications for a given user."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(True))
        .delete()
    )
    db.commit()
    return count


def clear_all_notifications(db: Session, *, user_id: int) -> int:
    """Delete all notifications for a given user."""
    count = db.query(Notification).filter(Notification.user_id == user_id).delete()
    db.commit()
    return count


def get_unread_count(db: Session, *, user_id: int) -> int:
    """Return count of unread notifications for a user."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count()
    )


