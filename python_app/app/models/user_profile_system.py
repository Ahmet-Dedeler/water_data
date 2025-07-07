from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from enum import Enum
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr
from app.models.common import TimestampMixin, UUIDMixin

Base = declarative_base()

# Enums for user profile system
class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"
    CUSTOM = "custom"

class ThemePreference(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"

class LanguageCode(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    JA = "ja"
    KO = "ko"
    ZH = "zh"
    RU = "ru"
    AR = "ar"
    HI = "hi"

class UnitSystem(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"
    MIXED = "mixed"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"

class HealthGoalType(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_GAIN = "muscle_gain"
    ENDURANCE = "endurance"
    GENERAL_HEALTH = "general_health"
    HYDRATION_FOCUS = "hydration_focus"
    RECOVERY = "recovery"

class NotificationFrequency(str, Enum):
    NEVER = "never"
    MINIMAL = "minimal"
    NORMAL = "normal"
    FREQUENT = "frequent"
    MAXIMUM = "maximum"

class DataSharingLevel(str, Enum):
    NONE = "none"
    ANONYMOUS = "anonymous"
    AGGREGATED = "aggregated"
    IDENTIFIED = "identified"

class PrivacyLevel(str, Enum):
    MINIMAL = "minimal"
    BALANCED = "balanced"
    STRICT = "strict"
    PARANOID = "paranoid"

# Core user profile models
class UserProfile(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_profiles"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Basic profile information
    display_name = Column(String(100))
    bio = Column(Text)
    location = Column(String(200))
    website = Column(String(500))
    birth_date = Column(DateTime)
    gender = Column(String(20))
    
    # Profile customization
    avatar_url = Column(String(500))
    cover_image_url = Column(String(500))
    profile_color = Column(String(7))  # Hex color code
    profile_theme = Column(String(50))
    
    # Visibility settings
    profile_visibility = Column(SQLEnum(ProfileVisibility), default=ProfileVisibility.FRIENDS)
    show_real_name = Column(Boolean, default=False)
    show_location = Column(Boolean, default=False)
    show_stats = Column(Boolean, default=True)
    show_achievements = Column(Boolean, default=True)
    show_activity = Column(Boolean, default=True)
    
    # Health and fitness information
    height = Column(Float)  # in cm
    weight = Column(Float)  # in kg
    activity_level = Column(SQLEnum(ActivityLevel), default=ActivityLevel.MODERATELY_ACTIVE)
    health_goals = Column(JSON)  # List of health goals
    medical_conditions = Column(JSON)  # List of medical conditions
    medications = Column(JSON)  # List of medications
    allergies = Column(JSON)  # List of allergies
    
    # Hydration-specific settings
    wake_up_time = Column(String(5))  # HH:MM format
    sleep_time = Column(String(5))  # HH:MM format
    work_schedule = Column(JSON)  # Work hours and days
    timezone = Column(String(50))
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    verification_type = Column(String(50))  # email, phone, id, etc.
    
    # Profile completion
    profile_completion_percentage = Column(Float, default=0.0)
    last_profile_update = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    preferences = relationship("UserPreferences", back_populates="profile", uselist=False)
    privacy_settings = relationship("UserPrivacySettings", back_populates="profile", uselist=False)
    customizations = relationship("UserCustomizations", back_populates="profile", uselist=False)
    achievements = relationship("UserAchievement", back_populates="profile")
    social_connections = relationship("UserSocialConnection", back_populates="profile")

class UserPreferences(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_preferences"
    
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    
    # Localization preferences
    language = Column(SQLEnum(LanguageCode), default=LanguageCode.EN)
    country = Column(String(2))  # ISO country code
    timezone = Column(String(50))
    date_format = Column(String(20), default="YYYY-MM-DD")
    time_format = Column(String(20), default="24h")
    
    # Unit preferences
    unit_system = Column(SQLEnum(UnitSystem), default=UnitSystem.METRIC)
    temperature_unit = Column(String(1), default="C")  # C or F
    distance_unit = Column(String(10), default="km")
    weight_unit = Column(String(10), default="kg")
    volume_unit = Column(String(10), default="ml")
    
    # App behavior preferences
    theme = Column(SQLEnum(ThemePreference), default=ThemePreference.AUTO)
    auto_sync = Column(Boolean, default=True)
    offline_mode = Column(Boolean, default=False)
    battery_saver = Column(Boolean, default=False)
    
    # Notification preferences
    notification_frequency = Column(SQLEnum(NotificationFrequency), default=NotificationFrequency.NORMAL)
    quiet_hours_start = Column(String(5))  # HH:MM
    quiet_hours_end = Column(String(5))  # HH:MM
    weekend_notifications = Column(Boolean, default=True)
    
    # Hydration preferences
    default_container_size = Column(Integer, default=500)  # ml
    reminder_interval = Column(Integer, default=60)  # minutes
    smart_reminders = Column(Boolean, default=True)
    weather_adjustments = Column(Boolean, default=True)
    activity_adjustments = Column(Boolean, default=True)
    
    # Social preferences
    allow_friend_requests = Column(Boolean, default=True)
    show_online_status = Column(Boolean, default=True)
    allow_challenges = Column(Boolean, default=True)
    share_achievements = Column(Boolean, default=True)
    
    # Data and analytics preferences
    data_sharing_level = Column(SQLEnum(DataSharingLevel), default=DataSharingLevel.AGGREGATED)
    analytics_tracking = Column(Boolean, default=True)
    personalized_insights = Column(Boolean, default=True)
    
    # Accessibility preferences
    high_contrast = Column(Boolean, default=False)
    large_text = Column(Boolean, default=False)
    screen_reader_support = Column(Boolean, default=False)
    reduced_motion = Column(Boolean, default=False)
    
    # Advanced preferences
    experimental_features = Column(Boolean, default=False)
    beta_testing = Column(Boolean, default=False)
    developer_mode = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="preferences")

class UserPrivacySettings(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_privacy_settings"
    
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    
    # Overall privacy level
    privacy_level = Column(SQLEnum(PrivacyLevel), default=PrivacyLevel.BALANCED)
    
    # Data collection settings
    allow_analytics = Column(Boolean, default=True)
    allow_crash_reporting = Column(Boolean, default=True)
    allow_performance_monitoring = Column(Boolean, default=True)
    allow_usage_statistics = Column(Boolean, default=True)
    
    # Profile visibility
    profile_searchable = Column(Boolean, default=True)
    show_in_leaderboards = Column(Boolean, default=True)
    allow_profile_indexing = Column(Boolean, default=False)
    
    # Data sharing
    share_anonymous_data = Column(Boolean, default=True)
    share_aggregated_data = Column(Boolean, default=True)
    allow_research_participation = Column(Boolean, default=False)
    
    # Communication settings
    allow_marketing_emails = Column(Boolean, default=False)
    allow_product_updates = Column(Boolean, default=True)
    allow_survey_invitations = Column(Boolean, default=False)
    
    # Third-party integrations
    allow_health_app_sync = Column(Boolean, default=False)
    allow_fitness_tracker_sync = Column(Boolean, default=False)
    allow_social_media_sharing = Column(Boolean, default=False)
    
    # Location and tracking
    allow_location_tracking = Column(Boolean, default=False)
    allow_precise_location = Column(Boolean, default=False)
    location_history_retention = Column(Integer, default=30)  # days
    
    # Data retention
    data_retention_period = Column(Integer, default=365)  # days
    auto_delete_old_data = Column(Boolean, default=False)
    
    # Security settings
    two_factor_enabled = Column(Boolean, default=False)
    login_notifications = Column(Boolean, default=True)
    suspicious_activity_alerts = Column(Boolean, default=True)
    
    # GDPR and compliance
    gdpr_consent = Column(Boolean, default=False)
    gdpr_consent_date = Column(DateTime)
    ccpa_opt_out = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="privacy_settings")

class UserCustomizations(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_customizations"
    
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    
    # Theme customizations
    primary_color = Column(String(7))  # Hex color
    secondary_color = Column(String(7))  # Hex color
    accent_color = Column(String(7))  # Hex color
    background_color = Column(String(7))  # Hex color
    text_color = Column(String(7))  # Hex color
    
    # Layout customizations
    dashboard_layout = Column(JSON)  # Dashboard widget configuration
    widget_preferences = Column(JSON)  # Enabled/disabled widgets
    chart_preferences = Column(JSON)  # Chart types and settings
    
    # Custom goals and targets
    custom_hydration_goals = Column(JSON)  # Custom goal definitions
    milestone_celebrations = Column(JSON)  # Custom celebration settings
    
    # Personalized content
    favorite_drink_types = Column(JSON)  # Preferred drink categories
    custom_drink_recipes = Column(JSON)  # User-created drink recipes
    custom_reminders = Column(JSON)  # Personalized reminder messages
    
    # Gamification customizations
    achievement_preferences = Column(JSON)  # Preferred achievement types
    challenge_preferences = Column(JSON)  # Challenge difficulty and types
    reward_preferences = Column(JSON)  # Preferred reward types
    
    # Interface customizations
    quick_actions = Column(JSON)  # Customized quick action buttons
    shortcuts = Column(JSON)  # Keyboard shortcuts
    gesture_controls = Column(JSON)  # Touch gesture preferences
    
    # Notification customizations
    custom_notification_sounds = Column(JSON)  # Custom sound preferences
    notification_templates = Column(JSON)  # Personalized message templates
    
    # Advanced customizations
    api_integrations = Column(JSON)  # Third-party API configurations
    custom_scripts = Column(JSON)  # User automation scripts
    
    # Relationships
    profile = relationship("UserProfile", back_populates="customizations")

class UserAchievement(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_achievements"
    
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    achievement_id = Column(String(36), nullable=False)
    
    # Achievement details
    achievement_name = Column(String(100), nullable=False)
    achievement_description = Column(Text)
    achievement_category = Column(String(50))
    achievement_type = Column(String(50))
    
    # Progress tracking
    current_progress = Column(Float, default=0.0)
    target_value = Column(Float)
    completion_percentage = Column(Float, default=0.0)
    
    # Status
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime)
    is_hidden = Column(Boolean, default=False)
    
    # Rewards
    points_earned = Column(Integer, default=0)
    badges_earned = Column(JSON)
    rewards_claimed = Column(JSON)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="achievements")

class UserSocialConnection(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_social_connections"
    
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    
    # Connection details
    platform = Column(String(50), nullable=False)  # facebook, twitter, instagram, etc.
    platform_user_id = Column(String(100))
    platform_username = Column(String(100))
    
    # Connection settings
    is_connected = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    allow_sharing = Column(Boolean, default=True)
    auto_post = Column(Boolean, default=False)
    
    # Sync settings
    sync_achievements = Column(Boolean, default=True)
    sync_milestones = Column(Boolean, default=True)
    sync_challenges = Column(Boolean, default=False)
    
    # Connection metadata
    connection_date = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime)
    sync_frequency = Column(String(20), default="daily")
    
    # Relationships
    profile = relationship("UserProfile", back_populates="social_connections")

class UserHealthProfile(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_health_profiles"
    
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    
    # Basic health metrics
    resting_heart_rate = Column(Integer)
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)
    body_fat_percentage = Column(Float)
    muscle_mass = Column(Float)
    bone_density = Column(Float)
    
    # Fitness metrics
    vo2_max = Column(Float)
    daily_steps_goal = Column(Integer, default=10000)
    weekly_exercise_goal = Column(Integer, default=150)  # minutes
    
    # Hydration-specific health data
    sweat_rate = Column(Float)  # ml per hour during exercise
    electrolyte_needs = Column(JSON)  # Personalized electrolyte requirements
    hydration_efficiency = Column(Float)  # How well body retains water
    
    # Medical information
    chronic_conditions = Column(JSON)
    current_medications = Column(JSON)
    supplement_intake = Column(JSON)
    dietary_restrictions = Column(JSON)
    
    # Health goals
    primary_health_goal = Column(SQLEnum(HealthGoalType))
    target_weight = Column(Float)
    target_body_fat = Column(Float)
    target_fitness_level = Column(String(50))
    
    # Health tracking preferences
    track_symptoms = Column(Boolean, default=False)
    track_mood = Column(Boolean, default=False)
    track_energy_levels = Column(Boolean, default=False)
    track_sleep_quality = Column(Boolean, default=False)
    
    # Integration settings
    health_app_connected = Column(Boolean, default=False)
    fitness_tracker_connected = Column(Boolean, default=False)
    smart_scale_connected = Column(Boolean, default=False)
    
    # Data sharing for health
    share_with_healthcare_provider = Column(Boolean, default=False)
    participate_in_health_research = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile")

class UserActivityProfile(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_activity_profiles"
    
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    
    # Activity patterns
    typical_wake_time = Column(String(5))  # HH:MM
    typical_sleep_time = Column(String(5))  # HH:MM
    work_schedule = Column(JSON)  # Work days and hours
    exercise_schedule = Column(JSON)  # Regular exercise times
    
    # Activity preferences
    preferred_activities = Column(JSON)  # List of preferred activities
    activity_intensity_preference = Column(String(20))
    indoor_outdoor_preference = Column(String(20))
    
    # Hydration patterns
    morning_hydration_routine = Column(JSON)
    workout_hydration_strategy = Column(JSON)
    evening_hydration_routine = Column(JSON)
    
    # Environmental factors
    typical_environment = Column(String(50))  # office, outdoor, home, etc.
    climate_zone = Column(String(50))
    seasonal_adjustments = Column(JSON)
    
    # Tracking preferences
    auto_detect_activities = Column(Boolean, default=True)
    manual_activity_logging = Column(Boolean, default=False)
    gps_tracking = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile")

# Pydantic models for API
class UserProfileCreate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=500)
    birth_date: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=20)
    height: Optional[float] = Field(None, ge=0, le=300)  # cm
    weight: Optional[float] = Field(None, ge=0, le=1000)  # kg
    activity_level: Optional[ActivityLevel] = None
    timezone: Optional[str] = Field(None, max_length=50)
    wake_up_time: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    sleep_time: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=500)
    birth_date: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=20)
    height: Optional[float] = Field(None, ge=0, le=300)
    weight: Optional[float] = Field(None, ge=0, le=1000)
    activity_level: Optional[ActivityLevel] = None
    profile_visibility: Optional[ProfileVisibility] = None
    show_real_name: Optional[bool] = None
    show_location: Optional[bool] = None
    show_stats: Optional[bool] = None
    show_achievements: Optional[bool] = None
    show_activity: Optional[bool] = None
    timezone: Optional[str] = Field(None, max_length=50)
    wake_up_time: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    sleep_time: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

class UserPreferencesUpdate(BaseModel):
    language: Optional[LanguageCode] = None
    timezone: Optional[str] = Field(None, max_length=50)
    unit_system: Optional[UnitSystem] = None
    theme: Optional[ThemePreference] = None
    notification_frequency: Optional[NotificationFrequency] = None
    quiet_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    default_container_size: Optional[int] = Field(None, ge=50, le=5000)
    reminder_interval: Optional[int] = Field(None, ge=5, le=480)
    smart_reminders: Optional[bool] = None
    weather_adjustments: Optional[bool] = None
    activity_adjustments: Optional[bool] = None
    allow_friend_requests: Optional[bool] = None
    show_online_status: Optional[bool] = None
    data_sharing_level: Optional[DataSharingLevel] = None
    analytics_tracking: Optional[bool] = None
    personalized_insights: Optional[bool] = None

class UserPrivacySettingsUpdate(BaseModel):
    privacy_level: Optional[PrivacyLevel] = None
    allow_analytics: Optional[bool] = None
    allow_crash_reporting: Optional[bool] = None
    profile_searchable: Optional[bool] = None
    show_in_leaderboards: Optional[bool] = None
    share_anonymous_data: Optional[bool] = None
    allow_marketing_emails: Optional[bool] = None
    allow_product_updates: Optional[bool] = None
    allow_location_tracking: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    login_notifications: Optional[bool] = None
    data_retention_period: Optional[int] = Field(None, ge=30, le=3650)
    auto_delete_old_data: Optional[bool] = None

class UserCustomizationsUpdate(BaseModel):
    primary_color: Optional[str] = Field(None, regex=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    secondary_color: Optional[str] = Field(None, regex=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    accent_color: Optional[str] = Field(None, regex=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    dashboard_layout: Optional[Dict[str, Any]] = None
    widget_preferences: Optional[Dict[str, Any]] = None
    custom_hydration_goals: Optional[Dict[str, Any]] = None
    favorite_drink_types: Optional[List[str]] = None
    quick_actions: Optional[List[str]] = None

class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    birth_date: Optional[datetime] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_visibility: ProfileVisibility
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    timezone: Optional[str] = None
    is_verified: bool
    profile_completion_percentage: float
    created_at: datetime
    updated_at: datetime

class UserPreferencesResponse(BaseModel):
    language: LanguageCode
    timezone: Optional[str] = None
    unit_system: UnitSystem
    theme: ThemePreference
    notification_frequency: NotificationFrequency
    default_container_size: int
    reminder_interval: int
    smart_reminders: bool
    weather_adjustments: bool
    activity_adjustments: bool
    data_sharing_level: DataSharingLevel
    analytics_tracking: bool
    updated_at: datetime

class UserPrivacySettingsResponse(BaseModel):
    privacy_level: PrivacyLevel
    allow_analytics: bool
    profile_searchable: bool
    show_in_leaderboards: bool
    share_anonymous_data: bool
    allow_marketing_emails: bool
    allow_location_tracking: bool
    two_factor_enabled: bool
    data_retention_period: int
    updated_at: datetime

class UserHealthProfileResponse(BaseModel):
    resting_heart_rate: Optional[int] = None
    daily_steps_goal: int
    primary_health_goal: Optional[HealthGoalType] = None
    target_weight: Optional[float] = None
    health_app_connected: bool
    fitness_tracker_connected: bool
    updated_at: datetime 