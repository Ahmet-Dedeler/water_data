"""
Models for health app integration with Apple Health and Google Fit.
"""

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4


class HealthPlatform(str, Enum):
    """Supported health platforms."""
    APPLE_HEALTH = "apple_health"
    GOOGLE_FIT = "google_fit"
    SAMSUNG_HEALTH = "samsung_health"
    FITBIT = "fitbit"
    GARMIN = "garmin"
    POLAR = "polar"


class DataType(str, Enum):
    """Types of health data that can be synced."""
    WATER_INTAKE = "water_intake"
    STEPS = "steps"
    HEART_RATE = "heart_rate"
    WEIGHT = "weight"
    BODY_FAT = "body_fat"
    SLEEP = "sleep"
    EXERCISE = "exercise"
    BLOOD_PRESSURE = "blood_pressure"
    BLOOD_GLUCOSE = "blood_glucose"
    CALORIES_BURNED = "calories_burned"
    ACTIVE_ENERGY = "active_energy"
    DISTANCE = "distance"
    FLIGHTS_CLIMBED = "flights_climbed"
    BODY_TEMPERATURE = "body_temperature"
    RESPIRATORY_RATE = "respiratory_rate"


class SyncStatus(str, Enum):
    """Status of data synchronization."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class PermissionLevel(str, Enum):
    """Permission levels for health data access."""
    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    READ_WRITE = "read_write"
    NONE = "none"


class SyncFrequency(str, Enum):
    """Frequency of automatic data synchronization."""
    REAL_TIME = "real_time"
    EVERY_5_MINUTES = "every_5_minutes"
    EVERY_15_MINUTES = "every_15_minutes"
    EVERY_30_MINUTES = "every_30_minutes"
    HOURLY = "hourly"
    EVERY_6_HOURS = "every_6_hours"
    DAILY = "daily"
    MANUAL_ONLY = "manual_only"


class HealthMetric(BaseModel):
    """Individual health metric data point."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique metric identifier")
    data_type: DataType = Field(..., description="Type of health data")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(..., description="When the metric was recorded")
    source_platform: HealthPlatform = Field(..., description="Platform that provided the data")
    source_device: Optional[str] = Field(None, description="Device that recorded the data")
    source_app: Optional[str] = Field(None, description="App that recorded the data")
    
    # Data quality and validation
    confidence_score: float = Field(default=1.0, ge=0, le=1, description="Confidence in data accuracy")
    is_validated: bool = Field(default=False, description="Whether data has been validated")
    validation_notes: Optional[str] = Field(None, description="Notes about data validation")
    
    # Metadata
    external_id: Optional[str] = Field(None, description="ID from external platform")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw data from platform")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When record was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When record was last updated")


class HealthIntegration(BaseModel):
    """Health platform integration configuration."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique integration identifier")
    user_id: int = Field(..., description="User who owns this integration")
    platform: HealthPlatform = Field(..., description="Health platform")
    
    # Authentication and connection
    is_connected: bool = Field(default=False, description="Whether integration is currently connected")
    access_token: Optional[str] = Field(None, description="Platform access token")
    refresh_token: Optional[str] = Field(None, description="Platform refresh token")
    token_expires_at: Optional[datetime] = Field(None, description="When access token expires")
    
    # Permissions and data types
    enabled_data_types: List[DataType] = Field(default_factory=list, description="Data types user has enabled")
    permissions: Dict[DataType, PermissionLevel] = Field(default_factory=dict, description="Permission level for each data type")
    
    # Sync configuration
    sync_frequency: SyncFrequency = Field(default=SyncFrequency.HOURLY, description="How often to sync data")
    auto_sync_enabled: bool = Field(default=True, description="Whether automatic sync is enabled")
    sync_historical_data: bool = Field(default=False, description="Whether to sync historical data on first connection")
    historical_data_days: int = Field(default=30, ge=0, le=365, description="How many days of historical data to sync")
    
    # Last sync information
    last_sync_at: Optional[datetime] = Field(None, description="When last sync occurred")
    last_successful_sync_at: Optional[datetime] = Field(None, description="When last successful sync occurred")
    next_sync_at: Optional[datetime] = Field(None, description="When next sync is scheduled")
    
    # Error handling
    consecutive_failures: int = Field(default=0, description="Number of consecutive sync failures")
    last_error: Optional[str] = Field(None, description="Last sync error message")
    last_error_at: Optional[datetime] = Field(None, description="When last error occurred")
    
    # Platform-specific settings
    platform_settings: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific configuration")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When integration was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When integration was last updated")
    is_active: bool = Field(default=True, description="Whether integration is active")


class SyncSession(BaseModel):
    """Data synchronization session."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique session identifier")
    integration_id: str = Field(..., description="Integration that initiated this sync")
    user_id: int = Field(..., description="User whose data is being synced")
    platform: HealthPlatform = Field(..., description="Platform being synced")
    
    # Session details
    status: SyncStatus = Field(default=SyncStatus.PENDING, description="Current sync status")
    data_types: List[DataType] = Field(default_factory=list, description="Data types being synced")
    sync_type: str = Field(..., description="Type of sync (full, incremental, manual)")
    
    # Time tracking
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When sync started")
    completed_at: Optional[datetime] = Field(None, description="When sync completed")
    duration_seconds: Optional[float] = Field(None, description="Sync duration in seconds")
    
    # Data processing
    records_processed: int = Field(default=0, description="Number of records processed")
    records_imported: int = Field(default=0, description="Number of records successfully imported")
    records_updated: int = Field(default=0, description="Number of records updated")
    records_skipped: int = Field(default=0, description="Number of records skipped")
    records_failed: int = Field(default=0, description="Number of records that failed to import")
    
    # Date range
    sync_from_date: Optional[datetime] = Field(None, description="Start date for data sync")
    sync_to_date: Optional[datetime] = Field(None, description="End date for data sync")
    
    # Error handling
    errors: List[str] = Field(default_factory=list, description="Errors encountered during sync")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during sync")
    
    # Results
    summary: Optional[str] = Field(None, description="Summary of sync results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional sync metadata")


class HealthDataMapping(BaseModel):
    """Mapping between platform-specific data and our internal format."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique mapping identifier")
    platform: HealthPlatform = Field(..., description="Source platform")
    platform_data_type: str = Field(..., description="Platform-specific data type identifier")
    internal_data_type: DataType = Field(..., description="Our internal data type")
    
    # Mapping configuration
    value_field: str = Field(..., description="Field name for the value in platform data")
    unit_field: Optional[str] = Field(None, description="Field name for the unit in platform data")
    timestamp_field: str = Field(..., description="Field name for the timestamp in platform data")
    
    # Value transformation
    value_multiplier: float = Field(default=1.0, description="Multiplier to apply to values")
    value_offset: float = Field(default=0.0, description="Offset to add to values")
    unit_conversion: Optional[Dict[str, str]] = Field(None, description="Unit conversion mapping")
    
    # Validation rules
    min_value: Optional[float] = Field(None, description="Minimum valid value")
    max_value: Optional[float] = Field(None, description="Maximum valid value")
    required_fields: List[str] = Field(default_factory=list, description="Required fields in platform data")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When mapping was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When mapping was last updated")
    is_active: bool = Field(default=True, description="Whether mapping is active")


class HealthDataConflict(BaseModel):
    """Conflict between different data sources."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique conflict identifier")
    user_id: int = Field(..., description="User whose data has conflicts")
    data_type: DataType = Field(..., description="Type of conflicting data")
    timestamp: datetime = Field(..., description="Timestamp of conflicting data")
    
    # Conflicting values
    values: List[Dict[str, Any]] = Field(..., description="List of conflicting values with their sources")
    
    # Resolution
    resolution_strategy: Optional[str] = Field(None, description="Strategy used to resolve conflict")
    resolved_value: Optional[float] = Field(None, description="Final resolved value")
    resolved_at: Optional[datetime] = Field(None, description="When conflict was resolved")
    resolved_by: Optional[str] = Field(None, description="How conflict was resolved (auto/manual)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When conflict was detected")
    is_resolved: bool = Field(default=False, description="Whether conflict has been resolved")


class HealthInsight(BaseModel):
    """AI-generated insights from health data."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique insight identifier")
    user_id: int = Field(..., description="User for whom insight was generated")
    
    # Insight content
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    insight_type: str = Field(..., description="Type of insight (correlation, trend, anomaly, etc.)")
    
    # Data sources
    data_types_used: List[DataType] = Field(default_factory=list, description="Data types used to generate insight")
    platforms_used: List[HealthPlatform] = Field(default_factory=list, description="Platforms that provided data")
    date_range_start: date = Field(..., description="Start date of data used")
    date_range_end: date = Field(..., description="End date of data used")
    
    # Insight details
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in insight accuracy")
    actionable_recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Data supporting the insight")
    
    # User interaction
    viewed_at: Optional[datetime] = Field(None, description="When user viewed the insight")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating of insight usefulness")
    user_feedback: Optional[str] = Field(None, description="User feedback on insight")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When insight was generated")
    expires_at: Optional[datetime] = Field(None, description="When insight expires")
    is_active: bool = Field(default=True, description="Whether insight is active")


class HealthGoalIntegration(BaseModel):
    """Integration between health goals and external health data."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique integration identifier")
    user_id: int = Field(..., description="User who owns this integration")
    health_goal_id: str = Field(..., description="Health goal being integrated")
    
    # Data source configuration
    data_source: HealthPlatform = Field(..., description="Platform providing data for goal tracking")
    data_type: DataType = Field(..., description="Type of data used for goal tracking")
    
    # Progress calculation
    auto_update_progress: bool = Field(default=True, description="Whether to automatically update goal progress")
    aggregation_method: str = Field(default="sum", description="How to aggregate data (sum, average, max, etc.)")
    measurement_frequency: str = Field(default="daily", description="How often to measure progress")
    
    # Sync settings
    last_sync_at: Optional[datetime] = Field(None, description="When goal progress was last synced")
    sync_enabled: bool = Field(default=True, description="Whether sync is enabled")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When integration was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When integration was last updated")
    is_active: bool = Field(default=True, description="Whether integration is active")


# Request/Response models
class HealthIntegrationCreate(BaseModel):
    """Request model for creating health integrations."""
    platform: HealthPlatform
    enabled_data_types: List[DataType] = Field(default_factory=list)
    sync_frequency: SyncFrequency = Field(default=SyncFrequency.HOURLY)
    auto_sync_enabled: bool = Field(default=True)
    sync_historical_data: bool = Field(default=False)
    historical_data_days: int = Field(default=30, ge=0, le=365)
    platform_settings: Dict[str, Any] = Field(default_factory=dict)


class HealthIntegrationUpdate(BaseModel):
    """Request model for updating health integrations."""
    enabled_data_types: Optional[List[DataType]] = None
    sync_frequency: Optional[SyncFrequency] = None
    auto_sync_enabled: Optional[bool] = None
    sync_historical_data: Optional[bool] = None
    historical_data_days: Optional[int] = Field(None, ge=0, le=365)
    platform_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SyncRequest(BaseModel):
    """Request model for manual data sync."""
    data_types: Optional[List[DataType]] = Field(None, description="Specific data types to sync")
    sync_from_date: Optional[datetime] = Field(None, description="Start date for sync")
    sync_to_date: Optional[datetime] = Field(None, description="End date for sync")
    force_full_sync: bool = Field(default=False, description="Whether to force a full sync")


class HealthMetricCreate(BaseModel):
    """Request model for creating health metrics."""
    data_type: DataType
    value: float
    unit: str
    timestamp: datetime
    source_platform: HealthPlatform
    source_device: Optional[str] = None
    source_app: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0, le=1)
    external_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class HealthMetricQuery(BaseModel):
    """Query parameters for health metrics."""
    data_types: Optional[List[DataType]] = None
    platforms: Optional[List[HealthPlatform]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_confidence: Optional[float] = Field(None, ge=0, le=1)
    validated_only: bool = Field(default=False)


class ConflictResolution(BaseModel):
    """Request model for resolving data conflicts."""
    resolution_strategy: str = Field(..., description="Strategy to use for resolution")
    selected_value_index: Optional[int] = Field(None, description="Index of selected value if manual resolution")
    custom_value: Optional[float] = Field(None, description="Custom value if manual resolution")


class HealthInsightFeedback(BaseModel):
    """Feedback on health insights."""
    user_rating: int = Field(..., ge=1, le=5, description="User rating of insight usefulness")
    user_feedback: Optional[str] = Field(None, description="User feedback on insight")
    is_helpful: bool = Field(..., description="Whether user found insight helpful") 