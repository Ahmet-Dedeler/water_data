from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from enum import Enum
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.models.common import TimestampMixin, UUIDMixin

Base = declarative_base()

# Enums for notification system
class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    VOICE = "voice"
    DESKTOP = "desktop"
    BROWSER = "browser"

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    BOUNCED = "bounced"
    SPAM = "spam"

class NotificationCategory(str, Enum):
    HYDRATION_REMINDER = "hydration_reminder"
    GOAL_ACHIEVEMENT = "goal_achievement"
    SOCIAL_ACTIVITY = "social_activity"
    HEALTH_ALERT = "health_alert"
    SYSTEM_UPDATE = "system_update"
    MARKETING = "marketing"
    SECURITY = "security"
    MAINTENANCE = "maintenance"
    FRIEND_REQUEST = "friend_request"
    CHALLENGE_INVITE = "challenge_invite"
    MILESTONE = "milestone"
    WEATHER_ALERT = "weather_alert"
    COACHING_TIP = "coaching_tip"
    REPORT_READY = "report_ready"
    BACKUP_COMPLETE = "backup_complete"

class TemplateType(str, Enum):
    BASIC = "basic"
    RICH = "rich"
    INTERACTIVE = "interactive"
    CAROUSEL = "carousel"
    VIDEO = "video"
    AUDIO = "audio"
    FORM = "form"
    SURVEY = "survey"
    GAME = "game"
    AR = "ar"

class DeliveryMethod(str, Enum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    BATCH = "batch"
    TRIGGERED = "triggered"
    SMART = "smart"
    QUEUE = "queue"
    PRIORITY = "priority"

class PersonalizationLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"
    ADVANCED = "advanced"
    AI_POWERED = "ai_powered"
    HYPER_PERSONALIZED = "hyper_personalized"

# Core notification models
class NotificationTemplate(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_templates"
    
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    category = Column(SQLEnum(NotificationCategory), nullable=False)
    template_type = Column(SQLEnum(TemplateType), default=TemplateType.BASIC)
    
    # Template content for different channels
    email_subject = Column(String(200))
    email_body = Column(Text)
    email_html = Column(Text)
    sms_content = Column(Text)
    push_title = Column(String(100))
    push_body = Column(Text)
    in_app_title = Column(String(100))
    in_app_content = Column(Text)
    
    # Advanced template features
    variables = Column(JSON)  # Template variables and their types
    personalization_rules = Column(JSON)  # Rules for personalization
    localization = Column(JSON)  # Multi-language support
    media_assets = Column(JSON)  # Images, videos, audio files
    interactive_elements = Column(JSON)  # Buttons, forms, etc.
    
    # Template settings
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    version = Column(String(20), default="1.0.0")
    author_id = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    notifications = relationship("Notification", back_populates="template")
    campaigns = relationship("NotificationCampaign", back_populates="template")

class NotificationChannel(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_channels"
    
    name = Column(String(100), nullable=False)
    channel_type = Column(SQLEnum(NotificationChannel), nullable=False)
    description = Column(Text)
    
    # Channel configuration
    config = Column(JSON)  # Channel-specific settings
    credentials = Column(JSON)  # API keys, tokens, etc. (encrypted)
    rate_limits = Column(JSON)  # Rate limiting settings
    retry_policy = Column(JSON)  # Retry configuration
    
    # Channel status
    is_active = Column(Boolean, default=True)
    is_healthy = Column(Boolean, default=True)
    last_health_check = Column(DateTime)
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, default=100.0)
    
    # Relationships
    notifications = relationship("Notification", back_populates="channel")
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="channel")

class NotificationRule(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_rules"
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Rule conditions
    trigger_events = Column(JSON)  # Events that trigger this rule
    conditions = Column(JSON)  # Conditions to evaluate
    filters = Column(JSON)  # User/data filters
    
    # Rule actions
    template_id = Column(String(36), ForeignKey("notification_templates.id"))
    channels = Column(JSON)  # Preferred channels
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Scheduling
    schedule_type = Column(SQLEnum(DeliveryMethod), default=DeliveryMethod.IMMEDIATE)
    schedule_config = Column(JSON)  # Scheduling configuration
    timezone_aware = Column(Boolean, default=True)
    
    # Rule settings
    is_active = Column(Boolean, default=True)
    max_frequency = Column(JSON)  # Frequency limits
    personalization_level = Column(SQLEnum(PersonalizationLevel), default=PersonalizationLevel.BASIC)
    
    # Relationships
    template = relationship("NotificationTemplate")
    notifications = relationship("Notification", back_populates="rule")

class Notification(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notifications"
    
    # Basic notification info
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    template_id = Column(String(36), ForeignKey("notification_templates.id"))
    rule_id = Column(String(36), ForeignKey("notification_rules.id"))
    channel_id = Column(String(36), ForeignKey("notification_channels.id"))
    
    # Notification content
    title = Column(String(200))
    content = Column(Text)
    rich_content = Column(JSON)  # Rich media content
    variables = Column(JSON)  # Template variables filled
    
    # Notification metadata
    category = Column(SQLEnum(NotificationCategory), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Scheduling and delivery
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Tracking and analytics
    delivery_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    error_message = Column(Text)
    tracking_id = Column(String(100), unique=True)
    
    # Personalization
    personalization_data = Column(JSON)
    ab_test_variant = Column(String(50))
    
    # Relationships
    user = relationship("User")
    template = relationship("NotificationTemplate", back_populates="notifications")
    rule = relationship("NotificationRule", back_populates="notifications")
    channel = relationship("NotificationChannel", back_populates="notifications")
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="notification")
    interactions = relationship("NotificationInteraction", back_populates="notification")

class NotificationDeliveryLog(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_delivery_logs"
    
    notification_id = Column(String(36), ForeignKey("notifications.id"), nullable=False)
    channel_id = Column(String(36), ForeignKey("notification_channels.id"))
    
    # Delivery details
    attempt_number = Column(Integer, nullable=False)
    status = Column(SQLEnum(NotificationStatus), nullable=False)
    delivery_time = Column(DateTime)
    response_time = Column(Float)  # in milliseconds
    
    # Technical details
    provider_response = Column(JSON)
    error_code = Column(String(50))
    error_message = Column(Text)
    retry_after = Column(DateTime)
    
    # Tracking
    external_id = Column(String(200))  # Provider's tracking ID
    delivery_receipt = Column(JSON)
    
    # Relationships
    notification = relationship("Notification", back_populates="delivery_logs")
    channel = relationship("NotificationChannel", back_populates="delivery_logs")

class NotificationInteraction(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_interactions"
    
    notification_id = Column(String(36), ForeignKey("notifications.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # click, read, dismiss, etc.
    interaction_data = Column(JSON)  # Additional interaction data
    interaction_time = Column(DateTime, default=datetime.utcnow)
    
    # Context
    device_info = Column(JSON)
    location_data = Column(JSON)
    session_id = Column(String(100))
    
    # Relationships
    notification = relationship("Notification", back_populates="interactions")
    user = relationship("User")

class NotificationCampaign(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_campaigns"
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    template_id = Column(String(36), ForeignKey("notification_templates.id"))
    
    # Campaign settings
    target_audience = Column(JSON)  # Audience criteria
    channels = Column(JSON)  # Delivery channels
    schedule = Column(JSON)  # Campaign schedule
    
    # Campaign status
    status = Column(String(20), default="draft")  # draft, active, paused, completed
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Campaign metrics
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    
    # A/B testing
    ab_test_config = Column(JSON)
    variants = Column(JSON)
    
    # Relationships
    template = relationship("NotificationTemplate", back_populates="campaigns")

class NotificationPreference(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_preferences"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Category preferences
    hydration_reminders = Column(Boolean, default=True)
    goal_achievements = Column(Boolean, default=True)
    social_activities = Column(Boolean, default=True)
    health_alerts = Column(Boolean, default=True)
    system_updates = Column(Boolean, default=True)
    marketing = Column(Boolean, default=False)
    
    # Advanced preferences
    quiet_hours = Column(JSON)  # Time ranges to avoid notifications
    frequency_limits = Column(JSON)  # Max notifications per channel/category
    personalization_level = Column(SQLEnum(PersonalizationLevel), default=PersonalizationLevel.BASIC)
    
    # Smart preferences
    smart_timing = Column(Boolean, default=True)
    predictive_filtering = Column(Boolean, default=True)
    context_awareness = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User")

class NotificationQueue(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_queue"
    
    notification_id = Column(String(36), ForeignKey("notifications.id"), nullable=False)
    
    # Queue management
    queue_name = Column(String(100), nullable=False)
    priority_score = Column(Integer, default=0)
    scheduled_for = Column(DateTime)
    
    # Processing status
    status = Column(String(20), default="queued")  # queued, processing, completed, failed
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_attempt = Column(DateTime)
    
    # Queue metadata
    processor_id = Column(String(100))
    processing_started = Column(DateTime)
    processing_completed = Column(DateTime)
    error_details = Column(JSON)
    
    # Relationships
    notification = relationship("Notification")

class NotificationAnalytics(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "notification_analytics"
    
    # Time period
    date = Column(DateTime, nullable=False, index=True)
    hour = Column(Integer)
    
    # Dimensions
    channel = Column(String(50))
    category = Column(String(50))
    template_id = Column(String(36))
    user_segment = Column(String(50))
    
    # Metrics
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # Performance metrics
    avg_delivery_time = Column(Float)
    avg_response_time = Column(Float)
    delivery_rate = Column(Float)
    open_rate = Column(Float)
    click_rate = Column(Float)
    
    # Engagement metrics
    engagement_score = Column(Float)
    conversion_rate = Column(Float)
    unsubscribe_rate = Column(Float)
    spam_rate = Column(Float)

# Pydantic models for API
class NotificationTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: NotificationCategory
    template_type: TemplateType = TemplateType.BASIC
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    email_html: Optional[str] = None
    sms_content: Optional[str] = None
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    in_app_title: Optional[str] = None
    in_app_content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    personalization_rules: Optional[Dict[str, Any]] = None
    localization: Optional[Dict[str, Any]] = None
    media_assets: Optional[Dict[str, Any]] = None
    interactive_elements: Optional[Dict[str, Any]] = None

class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    email_html: Optional[str] = None
    sms_content: Optional[str] = None
    push_title: Optional[str] = None
    push_body: Optional[str] = None
    in_app_title: Optional[str] = None
    in_app_content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    personalization_rules: Optional[Dict[str, Any]] = None
    localization: Optional[Dict[str, Any]] = None
    media_assets: Optional[Dict[str, Any]] = None
    interactive_elements: Optional[Dict[str, Any]] = None

class NotificationRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    trigger_events: List[str]
    conditions: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    template_id: str
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    schedule_type: DeliveryMethod = DeliveryMethod.IMMEDIATE
    schedule_config: Optional[Dict[str, Any]] = None
    timezone_aware: bool = True
    max_frequency: Optional[Dict[str, Any]] = None
    personalization_level: PersonalizationLevel = PersonalizationLevel.BASIC

class NotificationCreate(BaseModel):
    user_id: str
    template_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    rich_content: Optional[Dict[str, Any]] = None
    category: NotificationCategory
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    variables: Optional[Dict[str, Any]] = None
    personalization_data: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    category: NotificationCategory
    priority: NotificationPriority
    status: NotificationStatus
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    tracking_id: Optional[str] = None

class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    hydration_reminders: Optional[bool] = None
    goal_achievements: Optional[bool] = None
    social_activities: Optional[bool] = None
    health_alerts: Optional[bool] = None
    system_updates: Optional[bool] = None
    marketing: Optional[bool] = None
    quiet_hours: Optional[Dict[str, Any]] = None
    frequency_limits: Optional[Dict[str, Any]] = None
    personalization_level: Optional[PersonalizationLevel] = None
    smart_timing: Optional[bool] = None
    predictive_filtering: Optional[bool] = None
    context_awareness: Optional[bool] = None

class NotificationCampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    template_id: str
    target_audience: Dict[str, Any]
    channels: List[NotificationChannel]
    schedule: Dict[str, Any]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ab_test_config: Optional[Dict[str, Any]] = None
    variants: Optional[List[Dict[str, Any]]] = None

class NotificationAnalyticsResponse(BaseModel):
    date: datetime
    channel: Optional[str] = None
    category: Optional[str] = None
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    failed_count: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    engagement_score: float 