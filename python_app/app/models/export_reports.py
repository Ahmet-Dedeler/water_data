from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import uuid


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    XML = "xml"
    HTML = "html"
    PARQUET = "parquet"
    AVRO = "avro"
    YAML = "yaml"


class ReportType(str, Enum):
    """Types of reports that can be generated."""
    COMPREHENSIVE = "comprehensive"
    HYDRATION_SUMMARY = "hydration_summary"
    GOAL_PROGRESS = "goal_progress"
    SOCIAL_ACTIVITY = "social_activity"
    HEALTH_INSIGHTS = "health_insights"
    ANALYTICS_DASHBOARD = "analytics_dashboard"
    GDPR_EXPORT = "gdpr_export"
    MEDICAL_REPORT = "medical_report"
    CUSTOM = "custom"
    COMPLIANCE_REPORT = "compliance_report"
    PERFORMANCE_REPORT = "performance_report"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


class ExportStatus(str, Enum):
    """Export processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    QUEUED = "queued"
    PAUSED = "paused"
    RETRYING = "retrying"


class DataCategory(str, Enum):
    """Categories of user data for export."""
    PROFILE = "profile"
    WATER_LOGS = "water_logs"
    HEALTH_GOALS = "health_goals"
    ACHIEVEMENTS = "achievements"
    SOCIAL_DATA = "social_data"
    MESSAGES = "messages"
    ANALYTICS = "analytics"
    PREFERENCES = "preferences"
    DEVICE_DATA = "device_data"
    LOCATION_DATA = "location_data"
    BIOMETRIC_DATA = "biometric_data"
    ACTIVITY_DATA = "activity_data"
    NUTRITION_DATA = "nutrition_data"
    SLEEP_DATA = "sleep_data"
    WORKOUT_DATA = "workout_data"


class ReportSection(str, Enum):
    """Standard report sections."""
    EXECUTIVE_SUMMARY = "executive_summary"
    USER_PROFILE = "user_profile"
    HYDRATION_OVERVIEW = "hydration_overview"
    GOAL_ANALYSIS = "goal_analysis"
    TREND_ANALYSIS = "trend_analysis"
    SOCIAL_SUMMARY = "social_summary"
    HEALTH_INSIGHTS = "health_insights"
    RECOMMENDATIONS = "recommendations"
    RAW_DATA = "raw_data"
    APPENDIX = "appendix"
    METHODOLOGY = "methodology"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    PREDICTIVE_INSIGHTS = "predictive_insights"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_STATUS = "compliance_status"


class PrivacyLevel(str, Enum):
    """Privacy levels for data export."""
    PUBLIC = "public"
    FRIENDS_ONLY = "friends_only"
    PRIVATE = "private"
    ANONYMIZED = "anonymized"
    PSEUDONYMIZED = "pseudonymized"
    ENCRYPTED = "encrypted"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"


class IntegrationType(str, Enum):
    """Third-party integration types."""
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    SFTP = "sftp"
    FTP = "ftp"
    WEBHOOK = "webhook"
    API = "api"


class CompressionType(str, Enum):
    """File compression types."""
    NONE = "none"
    ZIP = "zip"
    GZIP = "gzip"
    TAR = "tar"
    BZIP2 = "bzip2"
    XZ = "xz"


class EncryptionType(str, Enum):
    """Encryption algorithms."""
    NONE = "none"
    AES256 = "aes256"
    RSA = "rsa"
    PGP = "pgp"
    CHACHA20 = "chacha20"


# Core Export Models

class ExportRequest(BaseModel):
    """Request for data export."""
    export_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    export_format: ExportFormat
    data_categories: List[DataCategory]
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    include_raw_data: bool = True
    include_analytics: bool = True
    include_visualizations: bool = False
    privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE
    password_protect: bool = False
    password: Optional[str] = None
    compression: CompressionType = CompressionType.ZIP
    encryption: EncryptionType = EncryptionType.NONE
    encryption_key: Optional[str] = None
    email_when_ready: bool = True
    retention_days: int = 7
    notes: Optional[str] = None
    tags: List[str] = []
    priority: int = Field(default=5, ge=1, le=10)
    max_file_size_mb: Optional[int] = None
    split_large_files: bool = False
    include_metadata: bool = True
    custom_fields: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExportResponse(BaseModel):
    """Response for export request."""
    export_id: str
    user_id: int
    status: ExportStatus
    export_format: ExportFormat
    file_size_bytes: Optional[int] = None
    file_count: int = 1
    download_url: Optional[str] = None
    download_urls: List[str] = []
    expires_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    progress_percentage: float = 0.0
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    processing_time_seconds: Optional[float] = None
    queue_position: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ReportRequest(BaseModel):
    """Request for report generation."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    report_type: ReportType
    report_format: ExportFormat = ExportFormat.PDF
    title: Optional[str] = None
    description: Optional[str] = None
    sections: List[ReportSection] = []
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    include_charts: bool = True
    include_insights: bool = True
    include_recommendations: bool = True
    include_comparisons: bool = False
    include_predictions: bool = False
    custom_branding: bool = False
    logo_url: Optional[str] = None
    color_scheme: Optional[Dict[str, str]] = None
    font_preferences: Optional[Dict[str, str]] = None
    language: str = "en"
    timezone: str = "UTC"
    template_id: Optional[str] = None
    filters: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}
    recipients: List[str] = []
    delivery_schedule: Optional[str] = None
    tags: List[str] = []
    priority: int = Field(default=5, ge=1, le=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReportResponse(BaseModel):
    """Response for report generation."""
    report_id: str
    user_id: int
    status: ExportStatus
    report_type: ReportType
    report_format: ExportFormat
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    page_count: Optional[int] = None
    chart_count: Optional[int] = None
    insight_count: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    quality_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Advanced Template Models

class ReportTemplate(BaseModel):
    """Report template configuration."""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    report_type: ReportType
    sections: List[ReportSection]
    default_format: ExportFormat = ExportFormat.PDF
    styling: Dict[str, Any] = {}
    layout_config: Dict[str, Any] = {}
    chart_config: Dict[str, Any] = {}
    is_public: bool = False
    is_featured: bool = False
    category: str = "general"
    tags: List[str] = []
    version: str = "1.0.0"
    created_by: int
    usage_count: int = 0
    rating: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class TemplateComponent(BaseModel):
    """Template component definition."""
    component_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    type: str  # header, footer, chart, table, text, image
    name: str
    config: Dict[str, Any]
    position: Dict[str, Any]  # x, y, width, height
    order: int = 0
    is_required: bool = False
    conditions: List[Dict[str, Any]] = []


class TemplateVariable(BaseModel):
    """Template variable definition."""
    variable_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    name: str
    type: str  # string, number, date, boolean, list
    default_value: Any = None
    description: Optional[str] = None
    validation_rules: List[Dict[str, Any]] = []
    is_required: bool = False


# Workflow Models

class ExportWorkflow(BaseModel):
    """Export workflow definition."""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    trigger_type: str  # manual, scheduled, event
    trigger_config: Dict[str, Any] = {}
    steps: List[Dict[str, Any]] = []
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: int
    is_active: bool = True
    execution_count: int = 0
    last_execution: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class WorkflowExecution(BaseModel):
    """Workflow execution instance."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    user_id: int
    status: WorkflowStatus
    trigger_data: Dict[str, Any] = {}
    step_results: List[Dict[str, Any]] = []
    current_step: int = 0
    total_steps: int = 0
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class WorkflowStep(BaseModel):
    """Individual workflow step."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    name: str
    type: str  # export, report, notification, integration
    config: Dict[str, Any]
    order: int
    conditions: List[Dict[str, Any]] = []
    retry_config: Dict[str, Any] = {}
    timeout_seconds: int = 300


# Notification Models

class NotificationTemplate(BaseModel):
    """Notification template."""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    channel: NotificationChannel
    subject_template: str
    body_template: str
    variables: List[str] = []
    is_active: bool = True
    created_by: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationRule(BaseModel):
    """Notification rule configuration."""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    trigger_events: List[str]
    conditions: List[Dict[str, Any]] = []
    template_id: str
    recipients: List[str] = []
    is_active: bool = True
    created_by: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationDelivery(BaseModel):
    """Notification delivery record."""
    delivery_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    template_id: str
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    status: str  # sent, failed, pending
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None


# Integration Models

class ThirdPartyIntegration(BaseModel):
    """Third-party service integration for exports."""
    integration_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    service_type: IntegrationType
    service_name: str
    service_config: Dict[str, Any]
    credentials: Dict[str, Any] = {}
    is_active: bool = True
    auto_sync: bool = False
    sync_frequency: Optional[str] = None
    last_sync: Optional[datetime] = None
    sync_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class IntegrationSync(BaseModel):
    """Integration synchronization record."""
    sync_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    integration_id: str
    export_id: Optional[str] = None
    report_id: Optional[str] = None
    sync_type: str  # upload, download, bidirectional
    status: str  # success, failed, partial
    files_synced: int = 0
    bytes_synced: int = 0
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration."""
    webhook_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    name: str
    url: str
    events: List[str] = []
    headers: Dict[str, str] = {}
    secret_key: Optional[str] = None
    is_active: bool = True
    retry_attempts: int = 3
    timeout_seconds: int = 30
    last_triggered: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Advanced Analytics Models

class ExportAnalytics(BaseModel):
    """Export system analytics."""
    analytics_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period_start: datetime
    period_end: datetime
    total_exports: int
    successful_exports: int
    failed_exports: int
    cancelled_exports: int
    average_processing_time: float
    median_processing_time: float
    total_data_exported_gb: float
    unique_users: int
    popular_formats: Dict[str, int]
    popular_categories: Dict[str, int]
    peak_hours: List[int]
    geographic_distribution: Dict[str, int] = {}
    device_types: Dict[str, int] = {}
    user_satisfaction: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class UserExportProfile(BaseModel):
    """User export behavior profile."""
    user_id: int
    total_exports: int
    successful_exports: int
    failed_exports: int
    preferred_format: ExportFormat
    preferred_categories: List[DataCategory]
    average_file_size_mb: float
    export_frequency_days: float
    last_export_date: Optional[date] = None
    most_active_hour: int
    most_active_day: str
    satisfaction_score: float = 0.0
    profile_updated: datetime = Field(default_factory=datetime.utcnow)


class ExportPerformanceMetrics(BaseModel):
    """Export system performance metrics."""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    queue_size: int
    processing_capacity: int
    average_queue_time: float
    system_load: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_throughput_mbps: float
    error_rate_percent: float
    uptime_percent: float


# Data Structure Models

class ExportData(BaseModel):
    """Container for exported data."""
    export_id: str
    user_id: int
    export_timestamp: datetime
    data_categories: List[DataCategory]
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    privacy_level: PrivacyLevel
    total_records: int
    file_format: ExportFormat
    schema_version: str = "1.0.0"
    checksum: Optional[str] = None
    digital_signature: Optional[str] = None


class UserDataExport(BaseModel):
    """Complete user data export structure."""
    user_profile: Dict[str, Any]
    water_logs: List[Dict[str, Any]] = []
    health_goals: List[Dict[str, Any]] = []
    achievements: List[Dict[str, Any]] = []
    social_connections: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
    analytics_data: Dict[str, Any] = {}
    preferences: Dict[str, Any] = {}
    device_information: List[Dict[str, Any]] = []
    biometric_data: List[Dict[str, Any]] = []
    activity_data: List[Dict[str, Any]] = []
    nutrition_data: List[Dict[str, Any]] = []
    export_metadata: Dict[str, Any]
    data_lineage: List[Dict[str, Any]] = []
    data_quality_metrics: Dict[str, Any] = {}


class ReportData(BaseModel):
    """Container for report data."""
    report_id: str
    user_id: int
    report_type: ReportType
    generated_at: datetime
    sections: Dict[str, Any]
    charts: List[Dict[str, Any]] = []
    insights: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    summary_statistics: Dict[str, float] = {}
    comparative_data: Dict[str, Any] = {}
    predictive_data: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    quality_metrics: Dict[str, Any] = {}
    data_sources: List[str] = []


# GDPR and Privacy Models

class GDPRRequest(BaseModel):
    """GDPR data request."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    request_type: str  # access, rectification, erasure, portability, restriction, objection
    data_categories: List[DataCategory] = []
    reason: Optional[str] = None
    legal_basis: Optional[str] = None
    verification_method: str
    verification_data: Dict[str, Any] = {}
    status: str = "pending"
    priority: str = "normal"  # low, normal, high, urgent
    deadline: Optional[datetime] = None
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    compliance_officer: Optional[int] = None
    notes: List[str] = []
    attachments: List[str] = []


class DataPortabilityExport(BaseModel):
    """GDPR Article 20 data portability export."""
    export_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    gdpr_request_id: str
    requested_at: datetime
    completed_at: Optional[datetime] = None
    data_format: ExportFormat = ExportFormat.JSON
    structured_data: Dict[str, Any]
    machine_readable: bool = True
    includes_metadata: bool = True
    verification_hash: str
    digital_signature: Optional[str] = None
    recipient_system: Optional[str] = None
    transfer_method: Optional[str] = None


class PrivacySettings(BaseModel):
    """User privacy settings for exports."""
    user_id: int
    allow_data_export: bool = True
    default_privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE
    require_password_protection: bool = False
    require_encryption: bool = False
    max_retention_days: int = 30
    email_notifications: bool = True
    include_analytics_in_export: bool = True
    include_social_data: bool = True
    include_biometric_data: bool = False
    anonymize_sensitive_data: bool = False
    allow_third_party_sharing: bool = False
    data_processing_consent: Dict[str, bool] = {}
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConsentRecord(BaseModel):
    """Data processing consent record."""
    consent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    consent_type: str
    purpose: str
    legal_basis: str
    granted: bool
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source: str  # web, app, api
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    evidence: Dict[str, Any] = {}


# Quota and Usage Models

class ExportQuota(BaseModel):
    """User export quota and limits."""
    user_id: int
    daily_export_limit: int = 5
    monthly_export_limit: int = 50
    yearly_export_limit: int = 500
    max_file_size_mb: int = 100
    max_concurrent_exports: int = 3
    daily_exports_used: int = 0
    monthly_exports_used: int = 0
    yearly_exports_used: int = 0
    concurrent_exports: int = 0
    quota_reset_date: date
    premium_user: bool = False
    enterprise_user: bool = False
    custom_limits: Dict[str, int] = {}


class DataUsageStatistics(BaseModel):
    """Statistics about data usage and exports."""
    user_id: int
    total_exports_created: int
    total_data_exported_mb: float
    most_used_format: ExportFormat
    average_export_size_mb: float
    largest_export_size_mb: float
    fastest_export_time_seconds: float
    slowest_export_time_seconds: float
    last_export_date: Optional[date] = None
    export_frequency_days: float = 0.0
    gdpr_requests_count: int = 0
    data_retention_compliance: bool = True
    carbon_footprint_kg: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Audit and Monitoring Models

class ExportAuditLog(BaseModel):
    """Audit log for export operations."""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int
    action: str  # request, download, delete, expire, share
    export_id: Optional[str] = None
    report_id: Optional[str] = None
    resource_type: str = "export"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = {}
    risk_score: float = 0.0
    compliance_flags: List[str] = []


class SecurityEvent(BaseModel):
    """Security event for export system."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[int] = None
    event_type: str  # suspicious_activity, policy_violation, breach_attempt
    severity: str  # low, medium, high, critical
    description: str
    affected_resources: List[str] = []
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class ComplianceReport(BaseModel):
    """Compliance reporting for exports."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str  # gdpr, ccpa, hipaa, sox
    period_start: datetime
    period_end: datetime
    total_requests: int
    completed_requests: int
    pending_requests: int
    overdue_requests: int
    average_response_time_hours: float
    compliance_score: float
    violations: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: int


# Response Models

class ExportListResponse(BaseModel):
    """Response for listing user exports."""
    exports: List[ExportResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
    total_pages: int
    filters_applied: Dict[str, Any] = {}
    sort_by: str = "created_at"
    sort_order: str = "desc"


class ReportListResponse(BaseModel):
    """Response for listing user reports."""
    reports: List[ReportResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
    total_pages: int
    filters_applied: Dict[str, Any] = {}
    sort_by: str = "created_at"
    sort_order: str = "desc"


class ExportMetrics(BaseModel):
    """Export system metrics."""
    total_exports: int
    successful_exports: int
    failed_exports: int
    cancelled_exports: int
    average_processing_time_seconds: float
    median_processing_time_seconds: float
    p95_processing_time_seconds: float
    total_data_exported_gb: float
    most_popular_format: ExportFormat
    most_requested_categories: List[DataCategory]
    peak_usage_hours: List[int]
    geographic_distribution: Dict[str, int] = {}
    user_satisfaction_score: Optional[float] = None
    system_uptime_percent: float = 99.9
    error_rate_percent: float = 0.1


class BulkExportRequest(BaseModel):
    """Request for bulk export operations."""
    bulk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_ids: List[int]
    export_format: ExportFormat
    data_categories: List[DataCategory]
    admin_user_id: int
    reason: str
    include_pii: bool = False
    encrypt_data: bool = True
    notification_email: str
    batch_size: int = 10
    priority: int = Field(default=3, ge=1, le=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExportValidation(BaseModel):
    """Validation results for export data."""
    export_id: str
    is_valid: bool
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    data_integrity_score: float
    completeness_percentage: float
    consistency_score: float
    quality_metrics: Dict[str, Any] = {}
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validator_version: str = "1.0.0"


# Advanced Configuration Models

class ExportConfiguration(BaseModel):
    """System-wide export configuration."""
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    max_concurrent_exports: int = 100
    max_queue_size: int = 1000
    default_retention_days: int = 30
    max_retention_days: int = 90
    max_file_size_mb: int = 1000
    supported_formats: List[ExportFormat] = list(ExportFormat)
    compression_enabled: bool = True
    encryption_enabled: bool = True
    rate_limit_per_user: int = 10
    rate_limit_window_minutes: int = 60
    maintenance_mode: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: int


class SystemHealth(BaseModel):
    """Export system health status."""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    queue_size: int
    processing_capacity: int
    active_exports: int
    system_load: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_latency_ms: float
    database_response_time_ms: float
    error_rate_last_hour: float
    uptime_hours: float
    last_maintenance: Optional[datetime] = None
    alerts: List[str] = [] 