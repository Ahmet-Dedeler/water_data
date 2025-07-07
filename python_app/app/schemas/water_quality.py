from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class WaterSourceType(str, Enum):
    TAP = "tap"
    BOTTLED = "bottled"
    FILTERED = "filtered"
    WELL = "well"
    SPRING = "spring"
    DISTILLED = "distilled"
    SPARKLING = "sparkling"
    ALKALINE = "alkaline"
    REVERSE_OSMOSIS = "reverse_osmosis"
    UV_TREATED = "uv_treated"

class WaterQualityRating(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"

class ContaminantType(str, Enum):
    CHLORINE = "chlorine"
    FLUORIDE = "fluoride"
    LEAD = "lead"
    BACTERIA = "bacteria"
    PESTICIDES = "pesticides"
    HEAVY_METALS = "heavy_metals"
    MICROPLASTICS = "microplastics"
    NITRATES = "nitrates"
    SULFATES = "sulfates"
    SEDIMENT = "sediment"

# Water Source Schemas
class WaterSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: WaterSourceType
    brand: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_primary: bool = False
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    tds_level: Optional[float] = Field(None, ge=0)
    hardness: Optional[float] = Field(None, ge=0)
    temperature_preference: Optional[float] = Field(None, ge=-10, le=100)
    cost_per_liter: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class WaterSourceCreate(WaterSourceBase):
    pass

class WaterSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[WaterSourceType] = None
    brand: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_primary: Optional[bool] = None
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    tds_level: Optional[float] = Field(None, ge=0)
    hardness: Optional[float] = Field(None, ge=0)
    temperature_preference: Optional[float] = Field(None, ge=-10, le=100)
    cost_per_liter: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class WaterSourceResponse(WaterSourceBase):
    id: int
    user_id: int
    is_active: bool
    last_tested: Optional[datetime]
    next_test_due: Optional[datetime]
    quality_rating: WaterQualityRating
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Water Quality Test Schemas
class WaterQualityTestBase(BaseModel):
    test_type: str = Field(..., min_length=1, max_length=50)
    lab_name: Optional[str] = Field(None, max_length=100)
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    tds_level: Optional[float] = Field(None, ge=0)
    hardness: Optional[float] = Field(None, ge=0)
    chlorine_level: Optional[float] = Field(None, ge=0)
    fluoride_level: Optional[float] = Field(None, ge=0)
    lead_level: Optional[float] = Field(None, ge=0)
    bacteria_count: Optional[int] = Field(None, ge=0)
    nitrate_level: Optional[float] = Field(None, ge=0)
    sulfate_level: Optional[float] = Field(None, ge=0)
    iron_level: Optional[float] = Field(None, ge=0)
    copper_level: Optional[float] = Field(None, ge=0)
    overall_rating: WaterQualityRating
    safety_score: Optional[int] = Field(None, ge=0, le=100)
    taste_score: Optional[int] = Field(None, ge=0, le=10)
    odor_score: Optional[int] = Field(None, ge=0, le=10)
    clarity_score: Optional[int] = Field(None, ge=0, le=10)
    test_results: Optional[Dict[str, Any]] = None
    recommendations: Optional[str] = None
    issues_found: Optional[List[str]] = None
    cost: Optional[float] = Field(None, ge=0)
    certified: bool = False
    certificate_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None

class WaterQualityTestCreate(WaterQualityTestBase):
    source_id: int

class WaterQualityTestUpdate(BaseModel):
    test_type: Optional[str] = Field(None, min_length=1, max_length=50)
    lab_name: Optional[str] = Field(None, max_length=100)
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    tds_level: Optional[float] = Field(None, ge=0)
    hardness: Optional[float] = Field(None, ge=0)
    chlorine_level: Optional[float] = Field(None, ge=0)
    fluoride_level: Optional[float] = Field(None, ge=0)
    lead_level: Optional[float] = Field(None, ge=0)
    bacteria_count: Optional[int] = Field(None, ge=0)
    nitrate_level: Optional[float] = Field(None, ge=0)
    sulfate_level: Optional[float] = Field(None, ge=0)
    iron_level: Optional[float] = Field(None, ge=0)
    copper_level: Optional[float] = Field(None, ge=0)
    overall_rating: Optional[WaterQualityRating] = None
    safety_score: Optional[int] = Field(None, ge=0, le=100)
    taste_score: Optional[int] = Field(None, ge=0, le=10)
    odor_score: Optional[int] = Field(None, ge=0, le=10)
    clarity_score: Optional[int] = Field(None, ge=0, le=10)
    test_results: Optional[Dict[str, Any]] = None
    recommendations: Optional[str] = None
    issues_found: Optional[List[str]] = None
    cost: Optional[float] = Field(None, ge=0)
    certified: Optional[bool] = None
    certificate_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None

class WaterQualityTestResponse(WaterQualityTestBase):
    id: int
    source_id: int
    user_id: int
    test_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Contamination Report Schemas
class ContaminationReportBase(BaseModel):
    contaminant_type: ContaminantType
    severity_level: int = Field(..., ge=1, le=5)
    detected_level: Optional[float] = Field(None, ge=0)
    safe_limit: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    detection_method: Optional[str] = Field(None, max_length=100)
    symptoms_reported: Optional[List[str]] = None
    action_taken: Optional[str] = None
    location_details: Optional[str] = None
    first_noticed: Optional[datetime] = None
    last_observed: Optional[datetime] = None
    verified_by_authority: bool = False
    authority_name: Optional[str] = Field(None, max_length=100)
    public_health_notified: bool = False
    notes: Optional[str] = None

class ContaminationReportCreate(ContaminationReportBase):
    source_id: int

class ContaminationReportUpdate(BaseModel):
    contaminant_type: Optional[ContaminantType] = None
    severity_level: Optional[int] = Field(None, ge=1, le=5)
    detected_level: Optional[float] = Field(None, ge=0)
    safe_limit: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=20)
    detection_method: Optional[str] = Field(None, max_length=100)
    symptoms_reported: Optional[List[str]] = None
    action_taken: Optional[str] = None
    resolved: Optional[bool] = None
    resolution_date: Optional[datetime] = None
    location_details: Optional[str] = None
    first_noticed: Optional[datetime] = None
    last_observed: Optional[datetime] = None
    verified_by_authority: Optional[bool] = None
    authority_name: Optional[str] = Field(None, max_length=100)
    public_health_notified: Optional[bool] = None
    notes: Optional[str] = None

class ContaminationReportResponse(ContaminationReportBase):
    id: int
    source_id: int
    user_id: int
    resolved: bool
    resolution_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Water Quality Alert Schemas
class WaterQualityAlertBase(BaseModel):
    alert_type: str = Field(..., max_length=50)
    severity: str = Field(..., max_length=20)
    title: str = Field(..., max_length=200)
    message: str
    trigger_data: Optional[Dict[str, Any]] = None
    threshold_exceeded: bool = False
    expires_at: Optional[datetime] = None

class WaterQualityAlertCreate(WaterQualityAlertBase):
    source_id: Optional[int] = None

class WaterQualityAlertUpdate(BaseModel):
    acknowledged: Optional[bool] = None
    resolved: Optional[bool] = None

class WaterQualityAlertResponse(WaterQualityAlertBase):
    id: int
    user_id: int
    source_id: Optional[int]
    is_active: bool
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    resolved: bool
    resolved_at: Optional[datetime]
    notification_sent: bool
    email_sent: bool
    sms_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Filter Maintenance Schemas
class WaterFilterMaintenanceBase(BaseModel):
    filter_type: str = Field(..., max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    installation_date: datetime
    maintenance_frequency_days: int = Field(90, ge=1)
    max_gallons: Optional[float] = Field(None, ge=0)
    maintenance_cost: Optional[float] = Field(None, ge=0)
    replacement_cost: Optional[float] = Field(None, ge=0)
    maintenance_notes: Optional[str] = None

class WaterFilterMaintenanceCreate(WaterFilterMaintenanceBase):
    source_id: int

class WaterFilterMaintenanceUpdate(BaseModel):
    filter_type: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    last_maintenance: Optional[datetime] = None
    maintenance_frequency_days: Optional[int] = Field(None, ge=1)
    filter_life_percentage: Optional[float] = Field(None, ge=0, le=100)
    gallons_filtered: Optional[float] = Field(None, ge=0)
    max_gallons: Optional[float] = Field(None, ge=0)
    maintenance_cost: Optional[float] = Field(None, ge=0)
    replacement_cost: Optional[float] = Field(None, ge=0)
    maintenance_notes: Optional[str] = None
    is_active: Optional[bool] = None

class WaterFilterMaintenanceResponse(WaterFilterMaintenanceBase):
    id: int
    source_id: int
    user_id: int
    last_maintenance: Optional[datetime]
    next_maintenance_due: datetime
    filter_life_percentage: float
    gallons_filtered: float
    low_life_alert_sent: bool
    replacement_alert_sent: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Water Quality Preferences Schemas
class WaterQualityPreferencesBase(BaseModel):
    preferred_ph_min: float = Field(6.5, ge=0, le=14)
    preferred_ph_max: float = Field(8.5, ge=0, le=14)
    preferred_tds_max: float = Field(500, ge=0)
    preferred_hardness_max: float = Field(150, ge=0)
    chlorine_sensitivity: bool = True
    fluoride_preference: str = Field("neutral", regex="^(avoid|neutral|prefer)$")
    temperature_preference: Optional[float] = Field(None, ge=-10, le=100)
    test_reminder_frequency: int = Field(90, ge=1)
    quality_alert_threshold: str = Field("medium", regex="^(low|medium|high)$")
    contamination_alerts: bool = True
    filter_maintenance_alerts: bool = True
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True

    @validator('preferred_ph_max')
    def validate_ph_range(cls, v, values):
        if 'preferred_ph_min' in values and v <= values['preferred_ph_min']:
            raise ValueError('preferred_ph_max must be greater than preferred_ph_min')
        return v

class WaterQualityPreferencesCreate(WaterQualityPreferencesBase):
    pass

class WaterQualityPreferencesUpdate(BaseModel):
    preferred_ph_min: Optional[float] = Field(None, ge=0, le=14)
    preferred_ph_max: Optional[float] = Field(None, ge=0, le=14)
    preferred_tds_max: Optional[float] = Field(None, ge=0)
    preferred_hardness_max: Optional[float] = Field(None, ge=0)
    chlorine_sensitivity: Optional[bool] = None
    fluoride_preference: Optional[str] = Field(None, regex="^(avoid|neutral|prefer)$")
    temperature_preference: Optional[float] = Field(None, ge=-10, le=100)
    test_reminder_frequency: Optional[int] = Field(None, ge=1)
    quality_alert_threshold: Optional[str] = Field(None, regex="^(low|medium|high)$")
    contamination_alerts: Optional[bool] = None
    filter_maintenance_alerts: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None

class WaterQualityPreferencesResponse(WaterQualityPreferencesBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Analytics and Summary Schemas
class WaterQualityAnalytics(BaseModel):
    total_sources: int
    active_sources: int
    tests_conducted: int
    average_quality_rating: Optional[str]
    contamination_reports: int
    resolved_contaminations: int
    filters_maintained: int
    overdue_tests: int
    active_alerts: int
    
class WaterQualityTrend(BaseModel):
    date: datetime
    ph_level: Optional[float]
    tds_level: Optional[float]
    safety_score: Optional[int]
    quality_rating: Optional[str]

class WaterQualitySummary(BaseModel):
    user_id: int
    analytics: WaterQualityAnalytics
    recent_trends: List[WaterQualityTrend]
    active_alerts: List[WaterQualityAlertResponse]
    upcoming_tests: List[WaterSourceResponse]
    filter_maintenance_due: List[WaterFilterMaintenanceResponse] 