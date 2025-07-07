from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import logging

from app.api.dependencies import get_db
from app.core.websockets import manager
from app.models.notification import (
    Notification, NotificationUpdate, UserNotificationSettings, 
    NotificationSettingsUpdate, NotificationListResponse, NotificationStatus
)
from app.services.notification_service import notification_service
from app.core.auth import get_current_user, get_current_active_user
from app.models.user import User
from app.models.common import BaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            # We are just receiving messages to keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="Get user notifications",
    description="Retrieves a list of the most recent notifications for the currently authenticated user.",
)
def get_notifications(
    db: Session = Depends(get_db),
    status: Optional[NotificationStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user)
):
    """Get notifications for the authenticated user."""
    try:
        notifications, total = notification_service.get_user_notifications(
            db, current_user.id, status, limit, offset
        )
        unread_count = notification_service.get_unread_count(db, current_user.id)
        
        return NotificationListResponse(
            notifications=notifications,
            total=total,
            unread_count=unread_count
        )
    except Exception as e:
        logger.error(f"Error getting notifications for user {current_user.id}: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to get notifications")


@router.post("/mark-read/{notification_id}", response_model=BaseResponse)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark a specific notification as read."""
    try:
        notification = notification_service.mark_as_read(db, notification_id, current_user.id)
        if not notification:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
        return BaseResponse(message="Notification marked as read.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to mark notification as read")


@router.post(
    "/mark-all-read",
    response_model=BaseResponse,
    summary="Mark notifications as read",
    description="Marks all unread notifications for the current user as read.",
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all unread notifications as read for the user."""
    try:
        count = notification_service.mark_all_as_read(db, current_user.id)
        return BaseResponse(
            message=f"{count} notifications marked as read."
        )
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {current_user.id}: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to mark all notifications as read")


@router.get(
    "/settings",
    response_model=UserNotificationSettings,
    summary="Get notification settings",
    description="Retrieves the current notification settings for the authenticated user.",
)
def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the current user's notification settings."""
    try:
        settings = notification_service.get_user_notification_settings(db, current_user.id)
        return settings
    except Exception as e:
        logger.error(f"Error getting settings for user {current_user.id}: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to get notification settings")


@router.put(
    "/settings",
    response_model=UserNotificationSettings,
    summary="Update notification settings",
    description="Updates the notification settings for the currently authenticated user.",
)
def update_notification_settings(
    update_data: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update the current user's notification settings."""
    try:
        settings = notification_service.update_user_notification_settings(db, current_user.id, update_data)
        return settings
    except Exception as e:
        logger.error(f"Error updating settings for user {current_user.id}: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update notification settings")


@router.get("/unread-count", response_model=BaseResponse)
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the count of unread notifications for the user."""
    try:
        count = notification_service.get_unread_count(db, current_user.id)
        return BaseResponse(
            data={"unread_count": count}
        )
    except Exception as e:
        logger.error(f"Error getting unread count for user {current_user.id}: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to get unread count")


@router.post("/trigger-hydration-check", response_model=BaseResponse[dict])
def trigger_hydration_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually triggers a hydration progress check for the current user.
    NOTE: In a production environment, this logic would be handled by a scheduled background task.
    """
    try:
        user_id = current_user.id
        notification_service.check_hydration_progress_and_notify(db, user_id)
        return BaseResponse(
            data={"status": "check_triggered"},
            message="Hydration progress check has been triggered."
        )
    except Exception as e:
        # This endpoint should not fail loudly for the user
        return BaseResponse(
            data={"status": "check_failed"},
            message="Could not trigger hydration progress check."
        ) 