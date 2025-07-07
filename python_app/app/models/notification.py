from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Type of notification."""
    RECALL_ALERT = "recall_alert"
    NEW_PRODUCT = "new_product"
    HEALTH_WARNING = "health_warning"
    GOAL_MILESTONE = "goal_milestone"
    GOAL_REMINDER = "goal_reminder"
    REVIEW_RESPONSE = "review_response"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    NEW_RECOMMENDATION = "new_recommendation"


class NotificationChannel(str, Enum):
    """Channel through which the notification is sent."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class NotificationStatus(str, Enum):
    """Status of a notification."""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"


class NotificationPriority(str, Enum):
    """Priority of the notification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Notification(BaseModel):
    """Notification model."""
    id: str = Field(..., description="Unique identifier for the notification")
    user_id: int = Field(..., description="User to be notified")
    
    title: str = Field(..., max_length=150, description="Title of the notification")
    message: str = Field(..., max_length=1000, description="Main content of the notification")
    
    notification_type: NotificationType = Field(..., description="Type of notification")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="Priority level")
    
    status: NotificationStatus = Field(default=NotificationStatus.UNREAD, description="Current status")
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP], description="Channels to send through")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the notification was created")
    read_at: Optional[datetime] = Field(None, description="When the notification was read")
    
    # Contextual data
    related_entity_id: Optional[str] = Field(None, description="ID of the related entity (e.g., product, review, goal)")
    related_entity_type: Optional[str] = Field(None, description="Type of the related entity")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Additional data for the notification")
    
    # Actionable notifications
    action_url: Optional[str] = Field(None, description="URL for the user to take action")
    action_text: Optional[str] = Field(None, description="Text for the action button")


class NotificationCreate(BaseModel):
    """Model for creating a notification."""
    user_id: int
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    action_url: Optional[str] = None
    action_text: Optional[str] = None


class NotificationUpdate(BaseModel):
    """Model for updating a notification's status."""
    status: Optional[NotificationStatus] = None
    

class UserNotificationSettings(BaseModel):
    """User-specific notification settings."""
    user_id: int = Field(..., description="User ID")
    
    # Global switch
    master_enabled: bool = Field(default=True, description="Enable or disable all notifications")
    
    # Channel settings
    email_enabled: bool = Field(default=True, description="Enable email notifications")
    push_enabled: bool = Field(default=False, description="Enable push notifications")
    sms_enabled: bool = Field(default=False, description="Enable SMS notifications")
    
    # Type-specific settings
    recall_alerts_enabled: bool = Field(default=True)
    new_product_alerts_enabled: bool = Field(default=True)
    health_warnings_enabled: bool = Field(default=True)
    goal_milestones_enabled: bool = Field(default=True)
    goal_reminders_enabled: bool = Field(default=True)
    review_responses_enabled: bool = Field(default=True)
    system_announcements_enabled: bool = Field(default=True)
    new_recommendations_enabled: bool = Field(default=True)
    
    # Quiet hours
    quiet_hours_enabled: bool = Field(default=False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(None, description="Start time for quiet hours (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="End time for quiet hours (HH:MM)")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class NotificationSettingsUpdate(BaseModel):
    """Model for updating user notification settings."""
    master_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    recall_alerts_enabled: Optional[bool] = None
    new_product_alerts_enabled: Optional[bool] = None
    health_warnings_enabled: Optional[bool] = None
    goal_milestones_enabled: Optional[bool] = None
    goal_reminders_enabled: Optional[bool] = None
    review_responses_enabled: Optional[bool] = None
    system_announcements_enabled: Optional[bool] = None
    new_recommendations_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationListResponse(BaseModel):
    """Response for listing notifications."""
    notifications: List[Notification]
    total: int
    unread_count: int

class NotificationSendRequest(BaseModel):
    """Request to send a notification to a user or group."""
    user_ids: List[int]
    notification: NotificationCreate
    send_immediately: bool = True
    scheduled_at: Optional[datetime] = None 