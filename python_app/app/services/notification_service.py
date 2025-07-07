"""
Service for handling notifications.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification, NotificationCreate, NotificationStatus, UserNotificationSettings,
    NotificationSettingsUpdate, NotificationChannel, NotificationType, NotificationSettings
)
from app.services.user_service import user_service
from app.services.data_service import data_service
from app.utils.time_utils import get_current_time
from app.services.base_service import BaseService
from app.models.user import User
from app.schemas.notification import NotificationUpdate

logger = logging.getLogger(__name__)


class NotificationService(BaseService[Notification, NotificationCreate, NotificationUpdate]):
    """Service for managing notifications and user settings."""

    def __init__(self):
        self.notifications_file = Path(__file__).parent.parent / "data" / "notifications.json"
        self.settings_file = Path(__file__).parent.parent / "data" / "notification_settings.json"
        self._ensure_data_files()
        self._notifications_cache = None
        self._settings_cache = None

    def _ensure_data_files(self):
        """Ensure data files for notifications exist."""
        data_dir = self.notifications_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [self.notifications_file, self.settings_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)

    async def _load_notifications(self) -> List[Dict]:
        """Load notifications from file."""
        if self._notifications_cache is None:
            with open(self.notifications_file, 'r') as f:
                self._notifications_cache = json.load(f)
        return self._notifications_cache

    async def _save_notifications(self, notifications: List[Dict]):
        """Save notifications to file."""
        with open(self.notifications_file, 'w') as f:
            json.dump(notifications, f, indent=2, default=str)
        self._notifications_cache = notifications

    async def _load_settings(self) -> List[Dict]:
        """Load notification settings from file."""
        if self._settings_cache is None:
            with open(self.settings_file, 'r') as f:
                self._settings_cache = json.load(f)
        return self._settings_cache

    async def _save_settings(self, settings: List[Dict]):
        """Save notification settings to file."""
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2, default=str)
        self._settings_cache = settings

    async def send_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create and 'send' a notification."""
        notifications = await self._load_notifications()
        
        notification = Notification(
            id=str(uuid.uuid4()),
            **notification_data.model_dump()
        )
        
        user_settings = await self.get_user_notification_settings(notification.user_id)
        
        # Check if notifications are enabled for this user and type
        if not self._should_send(notification, user_settings):
            logger.info(f"Notification {notification.id} for user {notification.user_id} suppressed by user settings.")
            # Still save it as unread, but don't "send" it via external channels
            notification.status = NotificationStatus.UNREAD 
        
        notifications.append(notification.model_dump())
        await self._save_notifications(notifications)
        
        logger.info(f"Sent notification {notification.id} of type {notification.notification_type} to user {notification.user_id}")
        
        # In a real app, this is where you'd integrate with email/push/SMS services
        # For now, we just save it to our JSON "database"
        
        return notification
        
    def _should_send(self, notification: Notification, settings: UserNotificationSettings) -> bool:
        """Check if a notification should be sent based on user settings."""
        if not settings.master_enabled:
            return False
            
        type_setting_map = {
            NotificationType.RECALL_ALERT: settings.recall_alerts_enabled,
            NotificationType.NEW_PRODUCT: settings.new_product_alerts_enabled,
            NotificationType.HEALTH_WARNING: settings.health_warnings_enabled,
            NotificationType.GOAL_MILESTONE: settings.goal_milestones_enabled,
            NotificationType.GOAL_REMINDER: settings.goal_reminders_enabled,
            NotificationType.REVIEW_RESPONSE: settings.review_responses_enabled,
            NotificationType.SYSTEM_ANNOUNCEMENT: settings.system_announcements_enabled,
            NotificationType.NEW_RECOMMENDATION: settings.new_recommendations_enabled
        }
        
        if not type_setting_map.get(notification.notification_type, True):
            return False
        
        # Quiet hours check (simplified)
        if settings.quiet_hours_enabled and settings.quiet_hours_start and settings.quiet_hours_end:
            now = datetime.now().time()
            start_time = datetime.strptime(settings.quiet_hours_start, '%H:%M').time()
            end_time = datetime.strptime(settings.quiet_hours_end, '%H:%M').time()
            if start_time <= now <= end_time:
                return False # Don't send during quiet hours
        
        return True

    async def get_user_notifications(
        self,
        user_id: int,
        status: Optional[NotificationStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> (List[Notification], int):
        """Get notifications for a user."""
        notifications = await self._load_notifications()
        user_notifications = [n for n in notifications if n['user_id'] == user_id]
        
        if status:
            user_notifications = [n for n in user_notifications if n['status'] == status]
            
        user_notifications.sort(key=lambda n: n['created_at'], reverse=True)
        
        total = len(user_notifications)
        paginated_notifications = [Notification(**n) for n in user_notifications[offset : offset + limit]]
        
        return paginated_notifications, total

    async def mark_as_read(self, notification_id: str, user_id: int) -> Optional[Notification]:
        """Mark a notification as read."""
        notifications = await self._load_notifications()
        
        for n in notifications:
            if n['id'] == notification_id and n['user_id'] == user_id:
                n['status'] = NotificationStatus.READ
                n['read_at'] = datetime.utcnow()
                await self._save_notifications(notifications)
                return Notification(**n)
        return None

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all of a user's unread notifications as read."""
        notifications = await self._load_notifications()
        count = 0
        for n in notifications:
            if n['user_id'] == user_id and n['status'] == NotificationStatus.UNREAD:
                n['status'] = NotificationStatus.READ
                n['read_at'] = datetime.utcnow()
                count += 1
        
        if count > 0:
            await self._save_notifications(notifications)
        
        return count

    async def get_unread_count(self, user_id: int) -> int:
        """Get the count of unread notifications for a user."""
        notifications = await self._load_notifications()
        return len([n for n in notifications if n['user_id'] == user_id and n['status'] == NotificationStatus.UNREAD])

    async def get_user_notification_settings(self, user_id: int) -> UserNotificationSettings:
        """Get notification settings for a user, creating them if they don't exist."""
        settings_list = await self._load_settings()
        
        setting_dict = next((s for s in settings_list if s['user_id'] == user_id), None)
        
        if setting_dict:
            return UserNotificationSettings(**setting_dict)
        
        # Create default settings for the user
        new_settings = UserNotificationSettings(user_id=user_id)
        settings_list.append(new_settings.model_dump())
        await self._save_settings(settings_list)
        return new_settings

    async def update_user_notification_settings(
        self,
        user_id: int,
        update_data: NotificationSettingsUpdate
    ) -> UserNotificationSettings:
        """Update notification settings for a user."""
        settings_list = await self._load_settings()
        setting_index = next((i for i, s in enumerate(settings_list) if s['user_id'] == user_id), None)

        if setting_index is None:
            # Should not happen if get_user_notification_settings is used, but handle defensively
            current_settings = UserNotificationSettings(user_id=user_id)
            settings_list.append(current_settings.model_dump())
            setting_index = len(settings_list) - 1
        else:
            current_settings = UserNotificationSettings(**settings_list[setting_index])

        update_dict = update_data.model_dump(exclude_unset=True)
        updated_settings = current_settings.model_copy(update=update_dict)
        updated_settings.last_updated = datetime.utcnow()
        
        settings_list[setting_index] = updated_settings.model_dump()
        await self._save_settings(settings_list)
        
        return updated_settings

    async def check_hydration_progress_and_notify(self, user_id: int):
        """
        Check user's hydration progress for the day and log a reminder if they are behind schedule.
        This is a conceptual implementation for a feature that would be run by a periodic background task.
        """
        profile = await user_service.get_user_profile(user_id)
        if not profile or not profile.notifications_enabled:
            return

        now = get_current_time()
        
        # We only send reminders between 9am and 9pm
        if not (9 <= now.hour <= 21):
            return

        # Get today's logs
        all_logs = await data_service.read_data("user_water_logs.json")
        today_logs = [
            log for log in all_logs
            if log.get("user_id") == user_id and datetime.fromisoformat(log["date"]).date() == now.date()
        ]
        
        volume_today_ml = sum(log.get("volume", 0) for log in today_logs) * 1000 # Convert L to mL
        
        # Calculate expected progress
        percent_of_day_passed = (now.hour * 3600 + now.minute * 60 + now.second) / (24 * 3600)
        expected_volume_ml = profile.daily_goal_ml * percent_of_day_passed

        # Send a reminder if user is significantly behind (e.g., less than 70% of expected progress)
        if volume_today_ml < (expected_volume_ml * 0.7):
            # In a real app, this would trigger a push notification. For now, we log it.
            logger.info(
                f"Reminder for User {user_id}: You're a bit behind on your hydration goal for today! "
                f"Current: {volume_today_ml:.0f}ml, Expected: {expected_volume_ml:.0f}ml."
            )
            # Conceptually, we could also create a Notification object here.
            await self.create_notification(
                user_id,
                "hydration_reminder",
                f"Just a friendly reminder to drink some water! You're currently at {volume_today_ml:.0f}ml for the day."
            )

    def get_notifications_by_user(self, db: Session, *, user_id: int, limit: int = 20) -> List[Notification]:
        return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.timestamp.desc()).limit(limit).all()

    def create_notification(self, db: Session, *, user_id: int, message: str):
        # First, check user's settings to see if they want this type of notification
        # This is a placeholder for more complex logic
        settings = self.get_or_create_settings(db, user_id=user_id)
        if not settings.enabled:
            return None

        notification = Notification(user_id=user_id, message=message)
        db.add(notification)
        db.commit()
        db.refresh(notification)
        logger.info(f"Notification created for user {user_id}: {message}")
        # Here you would also trigger a push notification if the user has a device registered
        # push_notification_service.send_push(user_id, message)
        return notification

    def mark_all_as_read(self, db: Session, *, user_id: int) -> int:
        num_updated = db.query(Notification).filter_by(user_id=user_id, read=False).update({"read": True})
        db.commit()
        logger.info(f"Marked {num_updated} notifications as read for user {user_id}")
        return num_updated

    # --- Specific Notification Creators ---
    
    def create_friend_request_notification(self, db: Session, *, user_id: int, requester_id: int):
        requester = db.query(User).get(requester_id)
        message = f"You have a new friend request from {requester.full_name or requester.email}."
        return self.create_notification(db, user_id=user_id, message=message)

    def create_achievement_notification(self, db: Session, *, user_id: int, achievement_name: str):
        message = f"Congratulations! You've earned the '{achievement_name}' achievement!"
        return self.create_notification(db, user_id=user_id, message=message)

    def create_comment_notification(self, db: Session, *, user_id: int, commenter_id: int, achievement_name: str):
        commenter = db.query(User).get(commenter_id)
        message = f"{commenter.full_name or commenter.email} commented on your '{achievement_name}' achievement."
        return self.create_notification(db, user_id=user_id, message=message)

    # --- Notification Settings ---

    def get_or_create_settings(self, db: Session, *, user_id: int) -> NotificationSettings:
        settings = db.query(NotificationSettings).filter_by(user_id=user_id).first()
        if not settings:
            settings = NotificationSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    def update_settings(self, db: Session, *, user_id: int, settings_in: NotificationSettingsUpdate) -> NotificationSettings:
        settings = self.get_or_create_settings(db, user_id=user_id)
        update_data = settings_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings


notification_service = NotificationService() 