from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class WaterSourceType(enum.Enum):
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

class WaterQualityRating(enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"

class ContaminantType(enum.Enum):
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

class WaterSource(Base):
    __tablename__ = "water_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(WaterSourceType), nullable=False)
    brand = Column(String(100), nullable=True)  # For bottled water
    location = Column(String(200), nullable=True)  # Where the source is located
    description = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False)  # User's main water source
    is_active = Column(Boolean, default=True)
    ph_level = Column(Float, nullable=True)  # pH level of water
    tds_level = Column(Float, nullable=True)  # Total Dissolved Solids (ppm)
    hardness = Column(Float, nullable=True)  # Water hardness (mg/L)
    temperature_preference = Column(Float, nullable=True)  # Preferred temperature
    cost_per_liter = Column(Float, nullable=True)  # Cost tracking
    last_tested = Column(DateTime, nullable=True)
    next_test_due = Column(DateTime, nullable=True)
    quality_rating = Column(SQLEnum(WaterQualityRating), default=WaterQualityRating.UNKNOWN)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="water_sources")
    quality_tests = relationship("WaterQualityTest", back_populates="source", cascade="all, delete-orphan")
    water_logs = relationship("WaterLog", back_populates="water_source")
    contamination_reports = relationship("ContaminationReport", back_populates="source", cascade="all, delete-orphan")

class WaterQualityTest(Base):
    __tablename__ = "water_quality_tests"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("water_sources.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    test_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    test_type = Column(String(50), nullable=False)  # "home_kit", "professional", "laboratory"
    lab_name = Column(String(100), nullable=True)  # Testing laboratory
    
    # Water quality metrics
    ph_level = Column(Float, nullable=True)
    tds_level = Column(Float, nullable=True)  # Total Dissolved Solids
    hardness = Column(Float, nullable=True)  # Water hardness
    chlorine_level = Column(Float, nullable=True)  # mg/L
    fluoride_level = Column(Float, nullable=True)  # mg/L
    lead_level = Column(Float, nullable=True)  # µg/L
    bacteria_count = Column(Integer, nullable=True)  # CFU/mL
    nitrate_level = Column(Float, nullable=True)  # mg/L
    sulfate_level = Column(Float, nullable=True)  # mg/L
    iron_level = Column(Float, nullable=True)  # mg/L
    copper_level = Column(Float, nullable=True)  # mg/L
    
    # Overall ratings
    overall_rating = Column(SQLEnum(WaterQualityRating), nullable=False)
    safety_score = Column(Integer, nullable=True)  # 0-100 safety score
    taste_score = Column(Integer, nullable=True)  # 0-10 taste rating
    odor_score = Column(Integer, nullable=True)  # 0-10 odor rating
    clarity_score = Column(Integer, nullable=True)  # 0-10 clarity rating
    
    # Test results and recommendations
    test_results = Column(JSON, nullable=True)  # Detailed test results
    recommendations = Column(Text, nullable=True)
    issues_found = Column(JSON, nullable=True)  # List of issues
    cost = Column(Float, nullable=True)  # Cost of testing
    
    # Certification and validation
    certified = Column(Boolean, default=False)
    certificate_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source = relationship("WaterSource", back_populates="quality_tests")
    user = relationship("User", back_populates="water_quality_tests")

class ContaminationReport(Base):
    __tablename__ = "contamination_reports"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("water_sources.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contaminant_type = Column(SQLEnum(ContaminantType), nullable=False)
    severity_level = Column(Integer, nullable=False)  # 1-5 severity scale
    detected_level = Column(Float, nullable=True)  # Measured level
    safe_limit = Column(Float, nullable=True)  # Safe limit for comparison
    unit = Column(String(20), nullable=True)  # Unit of measurement
    
    # Report details
    detection_method = Column(String(100), nullable=True)
    symptoms_reported = Column(JSON, nullable=True)  # Health symptoms
    action_taken = Column(Text, nullable=True)  # What user did about it
    resolved = Column(Boolean, default=False)
    resolution_date = Column(DateTime, nullable=True)
    
    # Location and timing
    location_details = Column(Text, nullable=True)
    first_noticed = Column(DateTime, nullable=True)
    last_observed = Column(DateTime, nullable=True)
    
    # Verification
    verified_by_authority = Column(Boolean, default=False)
    authority_name = Column(String(100), nullable=True)
    public_health_notified = Column(Boolean, default=False)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("WaterSource", back_populates="contamination_reports")
    user = relationship("User", back_populates="contamination_reports")

class WaterQualityAlert(Base):
    __tablename__ = "water_quality_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("water_sources.id"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)  # "test_due", "contamination", "quality_drop"
    severity = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert triggers
    trigger_data = Column(JSON, nullable=True)  # Data that triggered the alert
    threshold_exceeded = Column(Boolean, default=False)
    
    # Alert status
    is_active = Column(Boolean, default=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Notification tracking
    notification_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="water_quality_alerts")

class WaterFilterMaintenance(Base):
    __tablename__ = "water_filter_maintenance"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("water_sources.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filter_type = Column(String(100), nullable=False)  # "carbon", "reverse_osmosis", "uv", etc.
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    
    # Installation and maintenance
    installation_date = Column(DateTime, nullable=False)
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance_due = Column(DateTime, nullable=False)
    maintenance_frequency_days = Column(Integer, nullable=False, default=90)
    
    # Filter status
    filter_life_percentage = Column(Float, default=100.0)  # 0-100%
    gallons_filtered = Column(Float, default=0.0)
    max_gallons = Column(Float, nullable=True)  # Filter capacity
    
    # Maintenance tracking
    maintenance_cost = Column(Float, nullable=True)
    replacement_cost = Column(Float, nullable=True)
    maintenance_notes = Column(Text, nullable=True)
    
    # Alerts
    low_life_alert_sent = Column(Boolean, default=False)
    replacement_alert_sent = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("WaterSource")
    user = relationship("User")

class WaterQualityPreference(Base):
    __tablename__ = "water_quality_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Quality preferences
    preferred_ph_min = Column(Float, default=6.5)
    preferred_ph_max = Column(Float, default=8.5)
    preferred_tds_max = Column(Float, default=500)  # ppm
    preferred_hardness_max = Column(Float, default=150)  # mg/L
    
    # Taste preferences
    chlorine_sensitivity = Column(Boolean, default=True)
    fluoride_preference = Column(String(20), default="neutral")  # "avoid", "neutral", "prefer"
    temperature_preference = Column(Float, nullable=True)  # Celsius
    
    # Alert preferences
    test_reminder_frequency = Column(Integer, default=90)  # days
    quality_alert_threshold = Column(String(20), default="medium")  # "low", "medium", "high"
    contamination_alerts = Column(Boolean, default=True)
    filter_maintenance_alerts = Column(Boolean, default=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="water_quality_preferences") 