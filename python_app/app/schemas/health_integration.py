"""
Pydantic schemas for health app integration API endpoints.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.models.health_integration import (
    HealthPlatform, DataType, SyncStatus, PermissionLevel, SyncFrequency,
    HealthMetric, HealthIntegration, SyncSession, HealthDataMapping,
    HealthDataConflict, HealthInsight, HealthGoalIntegration
)


# Base response models
class BaseHealthResponse(BaseModel):
    """Base response model for health integration endpoints."""
    success: bool = Field(default=True, description="Whether request was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthIntegrationBase(BaseModel):
    """Base schema for health integrations."""
    platform: HealthPlatform = Field(..., description="Health platform")
    enabled_data_types: List[DataType] = Field(default_factory=list, description="Enabled data types")
    sync_frequency: SyncFrequency = Field(default=SyncFrequency.HOURLY, description="Sync frequency")
    auto_sync_enabled: bool = Field(default=True, description="Whether automatic sync is enabled")
    sync_historical_data: bool = Field(default=False, description="Whether to sync historical data")
    historical_data_days: int = Field(default=30, ge=0, le=365, description="Days of historical data to sync")
    platform_settings: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific settings")


class HealthIntegrationCreate(HealthIntegrationBase):
    """Schema for creating health integrations."""
    pass


class HealthIntegrationUpdate(BaseModel):
    """Schema for updating health integrations."""
    enabled_data_types: Optional[List[DataType]] = None
    sync_frequency: Optional[SyncFrequency] = None
    auto_sync_enabled: Optional[bool] = None
    sync_historical_data: Optional[bool] = None
    historical_data_days: Optional[int] = Field(None, ge=0, le=365)
    platform_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class HealthIntegrationResponse(HealthIntegrationBase):
    """Schema for health integration responses."""
    id: str = Field(..., description="Unique integration identifier")
    user_id: int = Field(..., description="User who owns this integration")
    is_connected: bool = Field(..., description="Whether integration is currently connected")
    permissions: Dict[DataType, PermissionLevel] = Field(default_factory=dict, description="Data type permissions")
    last_sync_at: Optional[datetime] = Field(None, description="When last sync occurred")
    last_successful_sync_at: Optional[datetime] = Field(None, description="When last successful sync occurred")
    next_sync_at: Optional[datetime] = Field(None, description="When next sync is scheduled")
    consecutive_failures: int = Field(default=0, description="Number of consecutive sync failures")
    last_error: Optional[str] = Field(None, description="Last sync error message")
    last_error_at: Optional[datetime] = Field(None, description="When last error occurred")
    created_at: datetime = Field(..., description="When integration was created")
    updated_at: datetime = Field(..., description="When integration was last updated")
    is_active: bool = Field(..., description="Whether integration is active")


class HealthMetricBase(BaseModel):
    """Base schema for health metrics."""
    data_type: DataType = Field(..., description="Type of health data")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(..., description="When the metric was recorded")
    source_platform: HealthPlatform = Field(..., description="Platform that provided the data")
    source_device: Optional[str] = Field(None, description="Device that recorded the data")
    source_app: Optional[str] = Field(None, description="App that recorded the data")
    confidence_score: float = Field(default=1.0, ge=0, le=1, description="Confidence in data accuracy")
    external_id: Optional[str] = Field(None, description="ID from external platform")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw data from platform")


class HealthMetricCreate(HealthMetricBase):
    """Schema for creating health metrics."""
    pass


class HealthMetricUpdate(BaseModel):
    """Schema for updating health metrics."""
    value: Optional[float] = None
    unit: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    is_validated: Optional[bool] = None
    validation_notes: Optional[str] = None


class HealthMetricResponse(HealthMetricBase):
    """Schema for health metric responses."""
    id: str = Field(..., description="Unique metric identifier")
    is_validated: bool = Field(..., description="Whether data has been validated")
    validation_notes: Optional[str] = Field(None, description="Notes about data validation")
    created_at: datetime = Field(..., description="When record was created")
    updated_at: datetime = Field(..., description="When record was last updated")


class SyncSessionBase(BaseModel):
    """Base schema for sync sessions."""
    sync_type: str = Field(..., description="Type of sync (full, incremental, manual)")
    data_types: List[DataType] = Field(default_factory=list, description="Data types being synced")
    sync_from_date: Optional[datetime] = Field(None, description="Start date for data sync")
    sync_to_date: Optional[datetime] = Field(None, description="End date for data sync")


class SyncRequest(SyncSessionBase):
    """Schema for sync requests."""
    force_full_sync: bool = Field(default=False, description="Whether to force a full sync")


class SyncSessionResponse(SyncSessionBase):
    """Schema for sync session responses."""
    id: str = Field(..., description="Unique session identifier")
    integration_id: str = Field(..., description="Integration that initiated this sync")
    user_id: int = Field(..., description="User whose data is being synced")
    platform: HealthPlatform = Field(..., description="Platform being synced")
    status: SyncStatus = Field(..., description="Current sync status")
    started_at: datetime = Field(..., description="When sync started")
    completed_at: Optional[datetime] = Field(None, description="When sync completed")
    duration_seconds: Optional[float] = Field(None, description="Sync duration in seconds")
    records_processed: int = Field(default=0, description="Number of records processed")
    records_imported: int = Field(default=0, description="Number of records successfully imported")
    records_updated: int = Field(default=0, description="Number of records updated")
    records_skipped: int = Field(default=0, description="Number of records skipped")
    records_failed: int = Field(default=0, description="Number of records that failed to import")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during sync")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during sync")
    summary: Optional[str] = Field(None, description="Summary of sync results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional sync metadata")


class HealthMetricQuery(BaseModel):
    """Schema for querying health metrics."""
    data_types: Optional[List[DataType]] = Field(None, description="Filter by data types")
    platforms: Optional[List[HealthPlatform]] = Field(None, description="Filter by platforms")
    start_date: Optional[datetime] = Field(None, description="Start date for metrics")
    end_date: Optional[datetime] = Field(None, description="End date for metrics")
    min_confidence: Optional[float] = Field(None, ge=0, le=1, description="Minimum confidence score")
    validated_only: bool = Field(default=False, description="Return only validated metrics")
    include_raw_data: bool = Field(default=False, description="Include raw platform data")

    @field_validator('end_date')
    @classmethod
    def end_date_after_start_date(cls, v, info):
        if v and info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


class HealthDataConflictBase(BaseModel):
    """Base schema for health data conflicts."""
    data_type: DataType = Field(..., description="Type of conflicting data")
    timestamp: datetime = Field(..., description="Timestamp of conflicting data")
    values: List[Dict[str, Any]] = Field(..., description="List of conflicting values with their sources")


class HealthDataConflictResponse(HealthDataConflictBase):
    """Schema for health data conflict responses."""
    id: str = Field(..., description="Unique conflict identifier")
    user_id: int = Field(..., description="User whose data has conflicts")
    resolution_strategy: Optional[str] = Field(None, description="Strategy used to resolve conflict")
    resolved_value: Optional[float] = Field(None, description="Final resolved value")
    resolved_at: Optional[datetime] = Field(None, description="When conflict was resolved")
    resolved_by: Optional[str] = Field(None, description="How conflict was resolved")
    created_at: datetime = Field(..., description="When conflict was detected")
    is_resolved: bool = Field(..., description="Whether conflict has been resolved")


class ConflictResolution(BaseModel):
    """Schema for resolving data conflicts."""
    resolution_strategy: str = Field(..., description="Strategy to use for resolution")
    selected_value_index: Optional[int] = Field(None, description="Index of selected value if manual resolution")
    custom_value: Optional[float] = Field(None, description="Custom value if manual resolution")

    @field_validator('selected_value_index')
    @classmethod
    def validate_selected_value_index(cls, v, info):
        if info.data.get('resolution_strategy') == 'manual_select' and v is None:
            raise ValueError('selected_value_index is required for manual_select strategy')
        return v

    @field_validator('custom_value')
    @classmethod
    def validate_custom_value(cls, v, info):
        if info.data.get('resolution_strategy') == 'custom_value' and v is None:
            raise ValueError('custom_value is required for custom_value strategy')
        return v


class HealthInsightBase(BaseModel):
    """Base schema for health insights."""
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    insight_type: str = Field(..., description="Type of insight")
    data_types_used: List[DataType] = Field(default_factory=list, description="Data types used to generate insight")
    platforms_used: List[HealthPlatform] = Field(default_factory=list, description="Platforms that provided data")
    date_range_start: date = Field(..., description="Start date of data used")
    date_range_end: date = Field(..., description="End date of data used")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in insight accuracy")
    actionable_recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Data supporting the insight")


class HealthInsightResponse(HealthInsightBase):
    """Schema for health insight responses."""
    id: str = Field(..., description="Unique insight identifier")
    user_id: int = Field(..., description="User for whom insight was generated")
    viewed_at: Optional[datetime] = Field(None, description="When user viewed the insight")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating of insight usefulness")
    user_feedback: Optional[str] = Field(None, description="User feedback on insight")
    generated_at: datetime = Field(..., description="When insight was generated")
    expires_at: Optional[datetime] = Field(None, description="When insight expires")
    is_active: bool = Field(..., description="Whether insight is active")


class HealthInsightFeedback(BaseModel):
    """Schema for health insight feedback."""
    user_rating: int = Field(..., ge=1, le=5, description="User rating of insight usefulness")
    user_feedback: Optional[str] = Field(None, description="User feedback on insight")
    is_helpful: bool = Field(..., description="Whether user found insight helpful")


class HealthGoalIntegrationBase(BaseModel):
    """Base schema for health goal integrations."""
    health_goal_id: str = Field(..., description="Health goal being integrated")
    data_source: HealthPlatform = Field(..., description="Platform providing data for goal tracking")
    data_type: DataType = Field(..., description="Type of data used for goal tracking")
    auto_update_progress: bool = Field(default=True, description="Whether to automatically update goal progress")
    aggregation_method: str = Field(default="sum", description="How to aggregate data")
    measurement_frequency: str = Field(default="daily", description="How often to measure progress")
    sync_enabled: bool = Field(default=True, description="Whether sync is enabled")


class HealthGoalIntegrationCreate(HealthGoalIntegrationBase):
    """Schema for creating health goal integrations."""
    pass


class HealthGoalIntegrationUpdate(BaseModel):
    """Schema for updating health goal integrations."""
    auto_update_progress: Optional[bool] = None
    aggregation_method: Optional[str] = None
    measurement_frequency: Optional[str] = None
    sync_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class HealthGoalIntegrationResponse(HealthGoalIntegrationBase):
    """Schema for health goal integration responses."""
    id: str = Field(..., description="Unique integration identifier")
    user_id: int = Field(..., description="User who owns this integration")
    last_sync_at: Optional[datetime] = Field(None, description="When goal progress was last synced")
    created_at: datetime = Field(..., description="When integration was created")
    updated_at: datetime = Field(..., description="When integration was last updated")
    is_active: bool = Field(..., description="Whether integration is active")


class HealthDataMappingBase(BaseModel):
    """Base schema for health data mappings."""
    platform: HealthPlatform = Field(..., description="Source platform")
    platform_data_type: str = Field(..., description="Platform-specific data type identifier")
    internal_data_type: DataType = Field(..., description="Our internal data type")
    value_field: str = Field(..., description="Field name for the value in platform data")
    unit_field: Optional[str] = Field(None, description="Field name for the unit in platform data")
    timestamp_field: str = Field(..., description="Field name for the timestamp in platform data")
    value_multiplier: float = Field(default=1.0, description="Multiplier to apply to values")
    value_offset: float = Field(default=0.0, description="Offset to add to values")
    unit_conversion: Optional[Dict[str, str]] = Field(None, description="Unit conversion mapping")
    min_value: Optional[float] = Field(None, description="Minimum valid value")
    max_value: Optional[float] = Field(None, description="Maximum valid value")
    required_fields: List[str] = Field(default_factory=list, description="Required fields in platform data")


class HealthDataMappingCreate(HealthDataMappingBase):
    """Schema for creating health data mappings."""
    pass


class HealthDataMappingUpdate(BaseModel):
    """Schema for updating health data mappings."""
    value_field: Optional[str] = None
    unit_field: Optional[str] = None
    timestamp_field: Optional[str] = None
    value_multiplier: Optional[float] = None
    value_offset: Optional[float] = None
    unit_conversion: Optional[Dict[str, str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    required_fields: Optional[List[str]] = None
    is_active: Optional[bool] = None


class HealthDataMappingResponse(HealthDataMappingBase):
    """Schema for health data mapping responses."""
    id: str = Field(..., description="Unique mapping identifier")
    created_at: datetime = Field(..., description="When mapping was created")
    updated_at: datetime = Field(..., description="When mapping was last updated")
    is_active: bool = Field(..., description="Whether mapping is active")


class HealthAnalytics(BaseModel):
    """Schema for health analytics responses."""
    user_id: int = Field(..., description="User identifier")
    period_start: date = Field(..., description="Analytics period start")
    period_end: date = Field(..., description="Analytics period end")
    
    # Data summary
    total_metrics: int = Field(..., description="Total health metrics in period")
    data_types_tracked: List[DataType] = Field(..., description="Data types tracked in period")
    platforms_used: List[HealthPlatform] = Field(..., description="Platforms used in period")
    
    # Sync statistics
    total_syncs: int = Field(..., description="Total sync sessions in period")
    successful_syncs: int = Field(..., description="Successful sync sessions")
    failed_syncs: int = Field(..., description="Failed sync sessions")
    sync_success_rate: float = Field(..., ge=0, le=1, description="Sync success rate")
    
    # Data quality
    validated_metrics: int = Field(..., description="Number of validated metrics")
    validation_rate: float = Field(..., ge=0, le=1, description="Data validation rate")
    conflicts_detected: int = Field(..., description="Number of data conflicts detected")
    conflicts_resolved: int = Field(..., description="Number of conflicts resolved")
    
    # Insights
    insights_generated: int = Field(..., description="Number of insights generated")
    insights_viewed: int = Field(..., description="Number of insights viewed")
    average_insight_rating: Optional[float] = Field(None, ge=1, le=5, description="Average insight rating")
    
    # Trends
    data_trends: Dict[str, Any] = Field(default_factory=dict, description="Data trends and patterns")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When analytics were generated")


class PlatformAuthRequest(BaseModel):
    """Schema for platform authentication requests."""
    platform: HealthPlatform = Field(..., description="Platform to authenticate with")
    auth_code: Optional[str] = Field(None, description="Authorization code from platform")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI used for OAuth")
    state: Optional[str] = Field(None, description="State parameter for OAuth")


class PlatformAuthResponse(BaseModel):
    """Schema for platform authentication responses."""
    platform: HealthPlatform = Field(..., description="Platform")
    auth_url: Optional[str] = Field(None, description="URL for user authentication")
    is_connected: bool = Field(..., description="Whether platform is now connected")
    permissions_granted: List[DataType] = Field(default_factory=list, description="Data types user granted access to")
    expires_at: Optional[datetime] = Field(None, description="When authentication expires")


class BulkHealthMetricCreate(BaseModel):
    """Schema for bulk creating health metrics."""
    metrics: List[HealthMetricCreate] = Field(..., min_items=1, max_items=1000, description="Metrics to create")
    skip_validation: bool = Field(default=False, description="Whether to skip validation")
    resolve_conflicts: bool = Field(default=True, description="Whether to automatically resolve conflicts")


class BulkHealthMetricResponse(BaseModel):
    """Schema for bulk health metric creation responses."""
    created_metrics: List[HealthMetricResponse] = Field(default_factory=list, description="Successfully created metrics")
    failed_metrics: List[Dict[str, Any]] = Field(default_factory=list, description="Failed metric creations with errors")
    conflicts_detected: List[HealthDataConflictResponse] = Field(default_factory=list, description="Conflicts detected")
    total_created: int = Field(..., ge=0, description="Total metrics created")
    total_failed: int = Field(..., ge=0, description="Total metrics failed")
    total_conflicts: int = Field(..., ge=0, description="Total conflicts detected")


class HealthDashboardResponse(BaseModel):
    """Schema for health dashboard responses."""
    user_id: int = Field(..., description="User identifier")
    integrations: List[HealthIntegrationResponse] = Field(default_factory=list, description="User's health integrations")
    recent_metrics: List[HealthMetricResponse] = Field(default_factory=list, description="Recent health metrics")
    active_conflicts: List[HealthDataConflictResponse] = Field(default_factory=list, description="Unresolved conflicts")
    recent_insights: List[HealthInsightResponse] = Field(default_factory=list, description="Recent health insights")
    sync_status: Dict[str, Any] = Field(default_factory=dict, description="Current sync status")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of health data")
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When dashboard was generated")


# Filter and search schemas
class HealthIntegrationFilter(BaseModel):
    """Schema for filtering health integrations."""
    platforms: Optional[List[HealthPlatform]] = None
    is_connected: Optional[bool] = None
    is_active: Optional[bool] = None
    has_errors: Optional[bool] = None
    data_types: Optional[List[DataType]] = None


class SyncSessionFilter(BaseModel):
    """Schema for filtering sync sessions."""
    platforms: Optional[List[HealthPlatform]] = None
    status: Optional[List[SyncStatus]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    integration_ids: Optional[List[str]] = None


class HealthInsightFilter(BaseModel):
    """Schema for filtering health insights."""
    insight_types: Optional[List[str]] = None
    data_types: Optional[List[DataType]] = None
    platforms: Optional[List[HealthPlatform]] = None
    min_confidence: Optional[float] = Field(None, ge=0, le=1)
    viewed_only: Optional[bool] = None
    active_only: Optional[bool] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None 