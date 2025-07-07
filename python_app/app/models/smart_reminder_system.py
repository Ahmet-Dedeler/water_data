from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
from enum import Enum
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from app.models.common import TimestampMixin, UUIDMixin

Base = declarative_base()

# Enums for smart reminder system
class ReminderType(str, Enum):
    HYDRATION = "hydration"
    MEAL = "meal"
    EXERCISE = "exercise"
    MEDICATION = "medication"
    SLEEP = "sleep"
    BREAK = "break"
    CUSTOM = "custom"

class ReminderPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class ReminderFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
    SMART = "smart"

class ReminderStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class DeliveryMethod(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    VOICE = "voice"
    WEBHOOK = "webhook"

class AdaptationStrategy(str, Enum):
    FIXED = "fixed"
    LEARNING = "learning"
    CONTEXTUAL = "contextual"
    PREDICTIVE = "predictive"
    HYBRID = "hybrid"

class ContextFactor(str, Enum):
    WEATHER = "weather"
    ACTIVITY = "activity"
    LOCATION = "location"
    CALENDAR = "calendar"
    HEART_RATE = "heart_rate"
    SLEEP = "sleep"
    STRESS = "stress"
    MOOD = "mood"

class MLModelType(str, Enum):
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"
    REINFORCEMENT = "reinforcement"

class PersonalizationLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

# Core smart reminder models
class SmartReminder(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "smart_reminders"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic reminder information
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reminder_type = Column(SQLEnum(ReminderType), nullable=False)
    priority = Column(SQLEnum(ReminderPriority), default=ReminderPriority.NORMAL)
    status = Column(SQLEnum(ReminderStatus), default=ReminderStatus.ACTIVE)
    
    # Scheduling information
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    frequency = Column(SQLEnum(ReminderFrequency), default=ReminderFrequency.DAILY)
    interval_minutes = Column(Integer, default=60)
    
    # Time-based settings
    preferred_times = Column(JSON)  # List of preferred times
    time_windows = Column(JSON)  # Acceptable time windows
    blackout_periods = Column(JSON)  # Times to avoid
    
    # Delivery settings
    delivery_methods = Column(JSON)  # List of delivery methods
    delivery_preferences = Column(JSON)  # Method-specific preferences
    
    # Smart features
    adaptation_strategy = Column(SQLEnum(AdaptationStrategy), default=AdaptationStrategy.LEARNING)
    personalization_level = Column(SQLEnum(PersonalizationLevel), default=PersonalizationLevel.INTERMEDIATE)
    context_factors = Column(JSON)  # List of context factors to consider
    
    # ML and AI settings
    ml_model_id = Column(String(36))
    learning_enabled = Column(Boolean, default=True)
    prediction_enabled = Column(Boolean, default=True)
    
    # Performance metrics
    success_rate = Column(Float, default=0.0)
    response_rate = Column(Float, default=0.0)
    effectiveness_score = Column(Float, default=0.0)
    
    # Customization
    custom_message_templates = Column(JSON)
    custom_sounds = Column(JSON)
    custom_actions = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="smart_reminders")
    instances = relationship("ReminderInstance", back_populates="reminder")
    interactions = relationship("ReminderInteraction", back_populates="reminder")
    analytics = relationship("ReminderAnalytics", back_populates="reminder")

class ReminderInstance(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "reminder_instances"
    
    reminder_id = Column(String(36), ForeignKey("smart_reminders.id"), nullable=False, index=True)
    
    # Instance details
    scheduled_time = Column(DateTime, nullable=False)
    actual_delivery_time = Column(DateTime)
    expiry_time = Column(DateTime)
    
    # Delivery information
    delivery_method = Column(SQLEnum(DeliveryMethod), nullable=False)
    delivery_status = Column(String(50), default="pending")
    delivery_attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Content
    message_content = Column(Text, nullable=False)
    subject = Column(String(200))
    custom_data = Column(JSON)
    
    # Context at delivery time
    context_data = Column(JSON)  # Weather, activity, location, etc.
    user_state = Column(JSON)  # Sleep, stress, mood, etc.
    
    # Response tracking
    was_delivered = Column(Boolean, default=False)
    was_seen = Column(Boolean, default=False)
    was_acknowledged = Column(Boolean, default=False)
    was_acted_upon = Column(Boolean, default=False)
    
    # Timing metrics
    delivery_delay = Column(Integer, default=0)  # seconds
    response_time = Column(Integer)  # seconds from delivery to response
    
    # Relationships
    reminder = relationship("SmartReminder", back_populates="instances")
    interactions = relationship("ReminderInteraction", back_populates="instance")

class ReminderInteraction(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "reminder_interactions"
    
    reminder_id = Column(String(36), ForeignKey("smart_reminders.id"), nullable=False, index=True)
    instance_id = Column(String(36), ForeignKey("reminder_instances.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # viewed, dismissed, snoozed, completed
    interaction_time = Column(DateTime, nullable=False)
    
    # Response data
    response_value = Column(String(500))  # User's response/action
    response_data = Column(JSON)  # Additional response data
    
    # Context
    device_info = Column(JSON)
    location_data = Column(JSON)
    app_state = Column(JSON)
    
    # Feedback
    user_feedback = Column(Text)
    satisfaction_rating = Column(Integer)  # 1-5 scale
    
    # Relationships
    reminder = relationship("SmartReminder", back_populates="interactions")
    instance = relationship("ReminderInstance", back_populates="interactions")
    user = relationship("User")

class ReminderTemplate(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "reminder_templates"
    
    # Template identification
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(50))
    
    # Template content
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Personalization variables
    variables = Column(JSON)  # List of variables that can be personalized
    personalization_rules = Column(JSON)  # Rules for personalization
    
    # Delivery settings
    default_delivery_methods = Column(JSON)
    delivery_preferences = Column(JSON)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    user_rating = Column(Float, default=0.0)
    
    # Template settings
    is_system_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User")

class ReminderRule(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "reminder_rules"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Rule identification
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Rule conditions
    conditions = Column(JSON, nullable=False)  # Complex condition logic
    context_requirements = Column(JSON)  # Required context factors
    
    # Rule actions
    actions = Column(JSON, nullable=False)  # Actions to take when conditions are met
    
    # Rule settings
    priority = Column(Integer, default=50)  # Higher number = higher priority
    cooldown_minutes = Column(Integer, default=0)  # Minimum time between rule executions
    max_executions_per_day = Column(Integer)
    
    # Performance tracking
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    last_execution = Column(DateTime)
    
    # Relationships
    user = relationship("User")

class ReminderAnalytics(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "reminder_analytics"
    
    reminder_id = Column(String(36), ForeignKey("smart_reminders.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Time period
    date = Column(DateTime, nullable=False)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly
    
    # Delivery metrics
    total_scheduled = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    
    # Response metrics
    total_viewed = Column(Integer, default=0)
    total_acknowledged = Column(Integer, default=0)
    total_acted_upon = Column(Integer, default=0)
    total_dismissed = Column(Integer, default=0)
    total_snoozed = Column(Integer, default=0)
    
    # Timing metrics
    average_response_time = Column(Float, default=0.0)
    average_delivery_delay = Column(Float, default=0.0)
    
    # Effectiveness metrics
    success_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    satisfaction_score = Column(Float, default=0.0)
    
    # Context insights
    best_delivery_times = Column(JSON)
    worst_delivery_times = Column(JSON)
    context_correlations = Column(JSON)
    
    # Relationships
    reminder = relationship("SmartReminder", back_populates="analytics")
    user = relationship("User")

class MLModel(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "ml_models"
    
    # Model identification
    name = Column(String(100), nullable=False)
    description = Column(Text)
    model_type = Column(SQLEnum(MLModelType), nullable=False)
    version = Column(String(20), default="1.0")
    
    # Model configuration
    algorithm = Column(String(50), nullable=False)
    hyperparameters = Column(JSON)
    feature_columns = Column(JSON)
    target_column = Column(String(100))
    
    # Training information
    training_data_size = Column(Integer, default=0)
    training_start_date = Column(DateTime)
    training_end_date = Column(DateTime)
    last_training_date = Column(DateTime)
    
    # Performance metrics
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    
    # Model status
    is_active = Column(Boolean, default=False)
    is_production_ready = Column(Boolean, default=False)
    
    # Model artifacts
    model_file_path = Column(String(500))
    model_metadata = Column(JSON)
    
    # Usage statistics
    prediction_count = Column(Integer, default=0)
    last_prediction_date = Column(DateTime)

class UserBehaviorPattern(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "user_behavior_patterns"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Pattern identification
    pattern_type = Column(String(50), nullable=False)  # hydration, activity, sleep, etc.
    pattern_name = Column(String(100))
    confidence_score = Column(Float, default=0.0)
    
    # Pattern data
    pattern_data = Column(JSON, nullable=False)
    statistical_summary = Column(JSON)
    
    # Time-based patterns
    hourly_patterns = Column(JSON)
    daily_patterns = Column(JSON)
    weekly_patterns = Column(JSON)
    monthly_patterns = Column(JSON)
    
    # Context patterns
    weather_correlations = Column(JSON)
    activity_correlations = Column(JSON)
    location_correlations = Column(JSON)
    
    # Pattern validity
    discovery_date = Column(DateTime, nullable=False)
    last_validation_date = Column(DateTime)
    validation_score = Column(Float, default=0.0)
    
    # Usage in reminders
    used_in_reminders = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    effectiveness_score = Column(Float, default=0.0)
    
    # Relationships
    user = relationship("User")

class ContextData(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "context_data"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Context timestamp
    context_time = Column(DateTime, nullable=False)
    
    # Weather data
    weather_temperature = Column(Float)
    weather_humidity = Column(Float)
    weather_condition = Column(String(50))
    weather_feels_like = Column(Float)
    
    # Activity data
    activity_type = Column(String(50))
    activity_intensity = Column(String(20))
    heart_rate = Column(Integer)
    steps_count = Column(Integer)
    calories_burned = Column(Float)
    
    # Location data
    location_type = Column(String(50))  # home, work, gym, outdoor, etc.
    location_coordinates = Column(JSON)
    location_name = Column(String(100))
    
    # Calendar data
    calendar_events = Column(JSON)
    is_busy = Column(Boolean, default=False)
    next_event_time = Column(DateTime)
    
    # Physiological data
    sleep_quality = Column(Float)
    stress_level = Column(Float)
    mood_score = Column(Float)
    energy_level = Column(Float)
    
    # Device data
    device_type = Column(String(50))
    battery_level = Column(Float)
    connectivity_status = Column(String(20))
    
    # Relationships
    user = relationship("User")

class ReminderOptimization(Base, TimestampMixin, UUIDMixin):
    __tablename__ = "reminder_optimizations"
    
    reminder_id = Column(String(36), ForeignKey("smart_reminders.id"), nullable=False, index=True)
    
    # Optimization details
    optimization_type = Column(String(50), nullable=False)  # timing, content, delivery, frequency
    optimization_date = Column(DateTime, nullable=False)
    
    # Before optimization
    before_metrics = Column(JSON)
    before_settings = Column(JSON)
    
    # After optimization
    after_metrics = Column(JSON)
    after_settings = Column(JSON)
    
    # Optimization results
    improvement_percentage = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    
    # Optimization method
    method_used = Column(String(50))  # ml_model, rule_based, user_feedback, a_b_test
    algorithm_details = Column(JSON)
    
    # Validation
    is_validated = Column(Boolean, default=False)
    validation_period_days = Column(Integer, default=7)
    validation_results = Column(JSON)
    
    # Relationships
    reminder = relationship("SmartReminder")

# Pydantic models for API
class SmartReminderCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    reminder_type: ReminderType
    priority: ReminderPriority = ReminderPriority.NORMAL
    start_date: datetime
    end_date: Optional[datetime] = None
    frequency: ReminderFrequency = ReminderFrequency.DAILY
    interval_minutes: int = Field(60, ge=1, le=1440)
    preferred_times: Optional[List[str]] = None
    time_windows: Optional[Dict[str, Any]] = None
    blackout_periods: Optional[List[Dict[str, Any]]] = None
    delivery_methods: List[DeliveryMethod] = [DeliveryMethod.PUSH]
    delivery_preferences: Optional[Dict[str, Any]] = None
    adaptation_strategy: AdaptationStrategy = AdaptationStrategy.LEARNING
    personalization_level: PersonalizationLevel = PersonalizationLevel.INTERMEDIATE
    context_factors: Optional[List[ContextFactor]] = None
    learning_enabled: bool = True
    prediction_enabled: bool = True
    custom_message_templates: Optional[Dict[str, str]] = None

class SmartReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[ReminderPriority] = None
    status: Optional[ReminderStatus] = None
    end_date: Optional[datetime] = None
    frequency: Optional[ReminderFrequency] = None
    interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    preferred_times: Optional[List[str]] = None
    time_windows: Optional[Dict[str, Any]] = None
    blackout_periods: Optional[List[Dict[str, Any]]] = None
    delivery_methods: Optional[List[DeliveryMethod]] = None
    delivery_preferences: Optional[Dict[str, Any]] = None
    adaptation_strategy: Optional[AdaptationStrategy] = None
    personalization_level: Optional[PersonalizationLevel] = None
    context_factors: Optional[List[ContextFactor]] = None
    learning_enabled: Optional[bool] = None
    prediction_enabled: Optional[bool] = None

class ReminderInteractionCreate(BaseModel):
    interaction_type: str = Field(..., max_length=50)
    response_value: Optional[str] = Field(None, max_length=500)
    response_data: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None
    location_data: Optional[Dict[str, Any]] = None
    app_state: Optional[Dict[str, Any]] = None
    user_feedback: Optional[str] = Field(None, max_length=1000)
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)

class ReminderTemplateCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    title_template: str = Field(..., max_length=200)
    message_template: str = Field(..., max_length=2000)
    variables: Optional[List[str]] = None
    personalization_rules: Optional[Dict[str, Any]] = None
    default_delivery_methods: Optional[List[DeliveryMethod]] = None
    delivery_preferences: Optional[Dict[str, Any]] = None
    is_public: bool = False

class ReminderRuleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    conditions: Dict[str, Any] = Field(...)
    context_requirements: Optional[Dict[str, Any]] = None
    actions: Dict[str, Any] = Field(...)
    priority: int = Field(50, ge=1, le=100)
    cooldown_minutes: int = Field(0, ge=0)
    max_executions_per_day: Optional[int] = Field(None, ge=1)

class ContextDataCreate(BaseModel):
    weather_temperature: Optional[float] = None
    weather_humidity: Optional[float] = None
    weather_condition: Optional[str] = None
    activity_type: Optional[str] = None
    activity_intensity: Optional[str] = None
    heart_rate: Optional[int] = Field(None, ge=30, le=220)
    steps_count: Optional[int] = Field(None, ge=0)
    location_type: Optional[str] = None
    location_coordinates: Optional[Dict[str, float]] = None
    is_busy: Optional[bool] = None
    sleep_quality: Optional[float] = Field(None, ge=0.0, le=10.0)
    stress_level: Optional[float] = Field(None, ge=0.0, le=10.0)
    mood_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    energy_level: Optional[float] = Field(None, ge=0.0, le=10.0)

class SmartReminderResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    reminder_type: ReminderType
    priority: ReminderPriority
    status: ReminderStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    frequency: ReminderFrequency
    interval_minutes: int
    adaptation_strategy: AdaptationStrategy
    personalization_level: PersonalizationLevel
    success_rate: float
    response_rate: float
    effectiveness_score: float
    learning_enabled: bool
    prediction_enabled: bool
    created_at: datetime
    updated_at: datetime

class ReminderInstanceResponse(BaseModel):
    id: str
    reminder_id: str
    scheduled_time: datetime
    actual_delivery_time: Optional[datetime] = None
    delivery_method: DeliveryMethod
    delivery_status: str
    message_content: str
    was_delivered: bool
    was_seen: bool
    was_acknowledged: bool
    was_acted_upon: bool
    response_time: Optional[int] = None
    created_at: datetime

class ReminderAnalyticsResponse(BaseModel):
    reminder_id: str
    date: datetime
    period_type: str
    total_scheduled: int
    total_delivered: int
    total_viewed: int
    total_acknowledged: int
    total_acted_upon: int
    success_rate: float
    engagement_rate: float
    satisfaction_score: float
    average_response_time: float
    best_delivery_times: Optional[List[str]] = None
    context_correlations: Optional[Dict[str, Any]] = None 