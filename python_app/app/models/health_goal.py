from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date, time
from enum import Enum


class HealthGoalType(str, Enum):
    """Types of health goals users can set."""
    DAILY_HYDRATION = "daily_hydration"
    WEEKLY_HYDRATION = "weekly_hydration"
    MONTHLY_HYDRATION = "monthly_hydration"
    MINERAL_INTAKE = "mineral_intake"
    CONTAMINANT_AVOIDANCE = "contaminant_avoidance"
    HEALTH_SCORE_IMPROVEMENT = "health_score_improvement"
    WEIGHT_MANAGEMENT = "weight_management"
    ENERGY_BOOST = "energy_boost"
    SKIN_HEALTH = "skin_health"
    DIGESTIVE_HEALTH = "digestive_health"
    DETOX = "detox"
    ATHLETIC_PERFORMANCE = "athletic_performance"


class HealthGoalStatus(str, Enum):
    """Status of a health goal."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class HealthGoalPriority(str, Enum):
    """Priority levels for health goals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealthGoalFrequency(str, Enum):
    """Frequency for recurring health goals."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ProgressMeasurement(BaseModel):
    """Individual progress measurement for a health goal."""
    id: str = Field(..., description="Unique identifier for this measurement")
    goal_id: str = Field(..., description="Health goal this measurement belongs to")
    measured_at: datetime = Field(default_factory=datetime.utcnow, description="When measurement was taken")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    notes: Optional[str] = Field(None, description="Optional notes about this measurement")
    water_consumption: Optional[float] = Field(None, description="Water consumed (in liters)")
    water_ids: Optional[List[int]] = Field(default_factory=list, description="IDs of waters consumed")
    mood_score: Optional[int] = Field(None, ge=1, le=10, description="Mood/energy level (1-10)")
    symptoms: Optional[List[str]] = Field(default_factory=list, description="Reported symptoms")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context data")


class Milestone(BaseModel):
    """Achievement milestone for health goals."""
    id: str = Field(..., description="Unique identifier for this milestone")
    name: str = Field(..., description="Name of the milestone")
    description: str = Field(..., description="Description of what this milestone represents")
    target_value: float = Field(..., description="Target value to achieve this milestone")
    unit: str = Field(..., description="Unit of measurement")
    reward_points: int = Field(default=0, description="Points awarded for achieving this milestone")
    badge_name: Optional[str] = Field(None, description="Badge name for this milestone")
    achieved: bool = Field(default=False, description="Whether this milestone has been achieved")
    achieved_at: Optional[datetime] = Field(None, description="When this milestone was achieved")
    order: int = Field(default=0, description="Order of this milestone in the sequence")


class Achievement(BaseModel):
    """User achievement record."""
    id: str = Field(..., description="Unique identifier for this achievement")
    user_id: int = Field(..., description="User who earned this achievement")
    goal_id: str = Field(..., description="Health goal this achievement relates to")
    milestone_id: str = Field(..., description="Milestone that was achieved")
    achieved_at: datetime = Field(default_factory=datetime.utcnow, description="When achievement was earned")
    points_earned: int = Field(default=0, description="Points earned for this achievement")
    badge_earned: Optional[str] = Field(None, description="Badge earned")
    celebration_message: Optional[str] = Field(None, description="Personalized celebration message")
    shared: bool = Field(default=False, description="Whether user shared this achievement")


class HealthGoalProgress(BaseModel):
    """Progress summary for a health goal."""
    goal_id: str = Field(..., description="Health goal ID")
    current_value: float = Field(default=0.0, description="Current progress value")
    target_value: float = Field(..., description="Target value to achieve")
    unit: str = Field(..., description="Unit of measurement")
    completion_percentage: float = Field(default=0.0, ge=0, le=100, description="Completion percentage")
    streak_days: int = Field(default=0, description="Current streak in days")
    best_streak: int = Field(default=0, description="Best streak achieved")
    total_measurements: int = Field(default=0, description="Total number of measurements taken")
    last_measurement_at: Optional[datetime] = Field(None, description="When last measurement was taken")
    average_daily_progress: float = Field(default=0.0, description="Average daily progress")
    trend: str = Field(default="stable", description="Progress trend (improving/declining/stable)")
    time_to_completion: Optional[int] = Field(None, description="Estimated days to completion")
    milestones_achieved: int = Field(default=0, description="Number of milestones achieved")
    total_milestones: int = Field(default=0, description="Total number of milestones")


class HealthGoal(BaseModel):
    """Health goal model."""
    id: str = Field(..., description="Unique identifier for this goal")
    user_id: int = Field(..., description="User who owns this goal")
    name: str = Field(..., min_length=1, max_length=100, description="Name of the health goal")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description")
    goal_type: HealthGoalType = Field(..., description="Type of health goal")
    status: HealthGoalStatus = Field(default=HealthGoalStatus.ACTIVE, description="Current status")
    priority: HealthGoalPriority = Field(default=HealthGoalPriority.MEDIUM, description="Goal priority")
    
    # Target and measurement
    target_value: float = Field(..., gt=0, description="Target value to achieve")
    current_value: float = Field(default=0.0, ge=0, description="Current progress value")
    unit: str = Field(..., description="Unit of measurement (liters, glasses, points, etc.)")
    measurement_frequency: HealthGoalFrequency = Field(default=HealthGoalFrequency.DAILY, description="How often to measure progress")
    
    # Timeline
    start_date: date = Field(default_factory=date.today, description="When the goal starts")
    target_date: Optional[date] = Field(None, description="Target completion date")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When goal was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When goal was last updated")
    completed_at: Optional[datetime] = Field(None, description="When goal was completed")
    
    # Progress tracking
    is_recurring: bool = Field(default=False, description="Whether this goal repeats")
    recurrence_pattern: Optional[str] = Field(None, description="How often goal recurs if recurring")
    auto_reset: bool = Field(default=False, description="Whether to auto-reset when completed")
    
    # Reminders and notifications
    reminder_enabled: bool = Field(default=True, description="Whether to send reminders")
    reminder_time: Optional[str] = Field(None, description="Time for daily reminders (HH:MM)")
    reminder_frequency: Optional[HealthGoalFrequency] = Field(None, description="Reminder frequency")
    
    # Milestones and achievements
    milestones: List[Milestone] = Field(default_factory=list, description="Achievement milestones")
    custom_milestones: bool = Field(default=False, description="Whether user has customized milestones")
    
    # Motivation and context
    motivation: Optional[str] = Field(None, max_length=300, description="User's motivation for this goal")
    expected_benefits: List[str] = Field(default_factory=list, description="Expected health benefits")
    success_criteria: Optional[str] = Field(None, description="How user will measure success")
    
    # Progress data
    progress: Optional[HealthGoalProgress] = Field(None, description="Current progress summary")
    measurements: List[ProgressMeasurement] = Field(default_factory=list, description="Progress measurements")
    achievements: List[Achievement] = Field(default_factory=list, description="Earned achievements")
    
    # Analytics
    tags: List[str] = Field(default_factory=list, description="Custom tags for organization")
    difficulty_level: int = Field(default=3, ge=1, le=5, description="Difficulty level (1-5)")
    estimated_duration_days: Optional[int] = Field(None, description="Estimated days to complete")
    
    @field_validator('target_date')
    @classmethod
    def target_date_must_be_in_future(cls, v):
        if v <= date.today():
            raise ValueError('Target date must be in the future')
        return v
    
    @field_validator('reminder_time', mode='before')
    @classmethod
    def validate_reminder_time(cls, v):
        if isinstance(v, str):
            try:
                return time.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid time format for reminder_time")
        return v


class HealthGoalCreate(BaseModel):
    """Model for creating a health goal."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    goal_type: HealthGoalType
    priority: HealthGoalPriority = HealthGoalPriority.MEDIUM
    target_value: float = Field(..., gt=0)
    unit: str
    measurement_frequency: HealthGoalFrequency = HealthGoalFrequency.DAILY
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    reminder_enabled: bool = True
    reminder_time: Optional[str] = None
    reminder_frequency: Optional[HealthGoalFrequency] = None
    motivation: Optional[str] = Field(None, max_length=300)
    expected_benefits: List[str] = Field(default_factory=list)
    success_criteria: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    difficulty_level: int = Field(default=3, ge=1, le=5)
    custom_milestones: List[Milestone] = Field(default_factory=list)


class HealthGoalUpdate(BaseModel):
    """Model for updating a health goal."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[HealthGoalPriority] = None
    target_value: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    status: Optional[HealthGoalStatus] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None
    reminder_frequency: Optional[HealthGoalFrequency] = None
    motivation: Optional[str] = Field(None, max_length=300)
    expected_benefits: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)


class ProgressEntry(BaseModel):
    """Model for logging progress towards a health goal."""
    value: float = Field(..., description="Progress value")
    notes: Optional[str] = Field(None, max_length=300)
    water_consumption: Optional[float] = Field(None, ge=0)
    water_ids: List[int] = Field(default_factory=list)
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    symptoms: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


class HealthGoalSummary(BaseModel):
    """Summary view of a health goal."""
    id: str
    name: str
    goal_type: HealthGoalType
    status: HealthGoalStatus
    priority: HealthGoalPriority
    target_value: float
    current_value: float
    unit: str
    completion_percentage: float
    streak_days: int
    days_remaining: Optional[int]
    milestones_achieved: int
    total_milestones: int
    last_activity: Optional[datetime]


class HealthGoalStats(BaseModel):
    """Statistics for health goal tracking."""
    total_goals: int = 0
    active_goals: int = 0
    completed_goals: int = 0
    total_achievements: int = 0
    total_points_earned: int = 0
    current_streaks: int = 0
    longest_streak: int = 0
    average_completion_rate: float = 0.0
    most_active_goal_type: Optional[str] = None
    completion_rate_by_type: Dict[str, float] = Field(default_factory=dict)
    monthly_progress: Dict[str, float] = Field(default_factory=dict)
    recent_achievements: List[Achievement] = Field(default_factory=list)


class HealthGoalResponse(BaseModel):
    """Response model for health goal operations."""
    success: bool
    message: str
    goal: Optional[HealthGoal] = None
    progress: Optional[HealthGoalProgress] = None
    achievements: List[Achievement] = Field(default_factory=list)


class HealthGoalListResponse(BaseModel):
    """Response model for listing health goals."""
    success: bool
    message: str
    goals: List[HealthGoalSummary] = Field(default_factory=list)
    total: int = 0
    stats: Optional[HealthGoalStats] = None


class ProgressLogResponse(BaseModel):
    """Response model for progress logging."""
    success: bool
    message: str
    measurement: Optional[ProgressMeasurement] = None
    goal_progress: Optional[HealthGoalProgress] = None
    new_achievements: List[Achievement] = Field(default_factory=list)
    milestone_reached: Optional[Milestone] = None
