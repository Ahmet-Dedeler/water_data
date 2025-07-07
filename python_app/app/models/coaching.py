"""
Models for hydration coaching and AI-powered recommendations.
"""

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import uuid4


class CoachingLevel(str, Enum):
    """Coaching intensity levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CoachingStyle(str, Enum):
    """Coaching communication styles."""
    MOTIVATIONAL = "motivational"
    SCIENTIFIC = "scientific"
    CASUAL = "casual"
    STRICT = "strict"
    ENCOURAGING = "encouraging"


class TipCategory(str, Enum):
    """Categories for coaching tips."""
    HYDRATION_TIMING = "hydration_timing"
    WATER_QUALITY = "water_quality"
    HEALTH_BENEFITS = "health_benefits"
    HABIT_BUILDING = "habit_building"
    GOAL_SETTING = "goal_setting"
    MOTIVATION = "motivation"
    SCIENCE_FACTS = "science_facts"
    LIFESTYLE_INTEGRATION = "lifestyle_integration"


class CoachingSessionType(str, Enum):
    """Types of coaching sessions."""
    DAILY_CHECK_IN = "daily_check_in"
    WEEKLY_REVIEW = "weekly_review"
    GOAL_SETTING = "goal_setting"
    HABIT_FORMATION = "habit_formation"
    PROBLEM_SOLVING = "problem_solving"
    MOTIVATION_BOOST = "motivation_boost"


class CoachingTrigger(str, Enum):
    """Events that trigger coaching interventions."""
    MISSED_GOAL = "missed_goal"
    LOW_INTAKE = "low_intake"
    STREAK_BROKEN = "streak_broken"
    NEW_USER = "new_user"
    GOAL_ACHIEVED = "goal_achieved"
    WEEKLY_REVIEW = "weekly_review"
    USER_REQUEST = "user_request"
    SCHEDULE = "schedule"


class PersonalizationFactor(BaseModel):
    """Factors used for personalizing coaching."""
    factor_type: str = Field(..., description="Type of personalization factor")
    value: Any = Field(..., description="Value of the factor")
    weight: float = Field(default=1.0, ge=0, le=1, description="Weight in personalization algorithm")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When factor was last updated")


class CoachingTip(BaseModel):
    """Individual coaching tip or advice."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique tip identifier")
    category: TipCategory = Field(..., description="Category of the tip")
    title: str = Field(..., min_length=1, max_length=200, description="Tip title")
    content: str = Field(..., min_length=10, max_length=1000, description="Tip content")
    short_description: Optional[str] = Field(None, max_length=300, description="Brief summary")
    
    # Targeting
    coaching_level: List[CoachingLevel] = Field(default_factory=list, description="Applicable coaching levels")
    coaching_style: List[CoachingStyle] = Field(default_factory=list, description="Applicable coaching styles")
    triggers: List[CoachingTrigger] = Field(default_factory=list, description="When to show this tip")
    
    # Personalization
    personalization_tags: List[str] = Field(default_factory=list, description="Tags for personalization")
    min_user_level: int = Field(default=1, ge=1, description="Minimum user level to show tip")
    seasonal: bool = Field(default=False, description="Whether tip is seasonal")
    time_sensitive: bool = Field(default=False, description="Whether tip is time-sensitive")
    
    # Effectiveness tracking
    effectiveness_score: float = Field(default=0.0, ge=0, le=1, description="How effective this tip is")
    usage_count: int = Field(default=0, ge=0, description="How many times tip was shown")
    positive_feedback: int = Field(default=0, ge=0, description="Positive feedback count")
    negative_feedback: int = Field(default=0, ge=0, description="Negative feedback count")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When tip was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When tip was last updated")
    is_active: bool = Field(default=True, description="Whether tip is active")


class CoachingSession(BaseModel):
    """A coaching session with the user."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique session identifier")
    user_id: int = Field(..., description="User receiving coaching")
    session_type: CoachingSessionType = Field(..., description="Type of coaching session")
    trigger: CoachingTrigger = Field(..., description="What triggered this session")
    
    # Session content
    title: str = Field(..., min_length=1, max_length=200, description="Session title")
    introduction: str = Field(..., description="Session introduction message")
    tips: List[CoachingTip] = Field(default_factory=list, description="Tips provided in session")
    action_items: List[str] = Field(default_factory=list, description="Recommended actions")
    questions: List[str] = Field(default_factory=list, description="Questions for user reflection")
    
    # Personalization
    coaching_level: CoachingLevel = Field(..., description="User's coaching level")
    coaching_style: CoachingStyle = Field(..., description="Coaching style used")
    personalization_factors: List[PersonalizationFactor] = Field(default_factory=list, description="Factors used for personalization")
    
    # Session tracking
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When session started")
    completed_at: Optional[datetime] = Field(None, description="When session was completed")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Session duration in minutes")
    
    # User interaction
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="User responses during session")
    user_feedback: Optional[str] = Field(None, description="User feedback on session")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="User satisfaction rating")
    
    # Effectiveness
    goals_set: List[str] = Field(default_factory=list, description="Goals set during session")
    commitments_made: List[str] = Field(default_factory=list, description="User commitments")
    follow_up_scheduled: bool = Field(default=False, description="Whether follow-up is scheduled")
    follow_up_date: Optional[datetime] = Field(None, description="When to follow up")


class CoachingProfile(BaseModel):
    """User's coaching profile and preferences."""
    user_id: int = Field(..., description="User identifier")
    
    # Coaching preferences
    coaching_level: CoachingLevel = Field(default=CoachingLevel.BEGINNER, description="User's coaching level")
    coaching_style: CoachingStyle = Field(default=CoachingStyle.ENCOURAGING, description="Preferred coaching style")
    session_frequency: str = Field(default="weekly", description="Preferred session frequency")
    reminder_enabled: bool = Field(default=True, description="Whether to send coaching reminders")
    reminder_time: Optional[str] = Field(None, description="Preferred reminder time (HH:MM)")
    
    # Personalization data
    motivation_factors: List[str] = Field(default_factory=list, description="What motivates the user")
    challenges: List[str] = Field(default_factory=list, description="User's main challenges")
    goals: List[str] = Field(default_factory=list, description="User's hydration goals")
    lifestyle_factors: Dict[str, Any] = Field(default_factory=dict, description="Lifestyle information")
    health_conditions: List[str] = Field(default_factory=list, description="Relevant health conditions")
    
    # Progress tracking
    total_sessions: int = Field(default=0, ge=0, description="Total coaching sessions completed")
    current_streak: int = Field(default=0, ge=0, description="Current engagement streak")
    best_streak: int = Field(default=0, ge=0, description="Best engagement streak")
    last_session_date: Optional[date] = Field(None, description="Date of last session")
    
    # Effectiveness metrics
    goal_completion_rate: float = Field(default=0.0, ge=0, le=1, description="Rate of goal completion")
    engagement_score: float = Field(default=0.0, ge=0, le=1, description="User engagement score")
    satisfaction_average: float = Field(default=0.0, ge=0, le=5, description="Average satisfaction rating")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When profile was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When profile was last updated")
    is_active: bool = Field(default=True, description="Whether coaching is active")


class CoachingRecommendation(BaseModel):
    """AI-generated coaching recommendation."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique recommendation identifier")
    user_id: int = Field(..., description="Target user")
    
    # Recommendation content
    type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., min_length=1, max_length=200, description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    priority: int = Field(default=3, ge=1, le=5, description="Recommendation priority")
    
    # AI insights
    confidence_score: float = Field(..., ge=0, le=1, description="AI confidence in recommendation")
    reasoning: str = Field(..., description="AI reasoning for recommendation")
    data_points_used: List[str] = Field(default_factory=list, description="Data points used for recommendation")
    
    # Implementation
    action_steps: List[str] = Field(default_factory=list, description="Specific action steps")
    expected_outcome: str = Field(..., description="Expected outcome if followed")
    timeline: str = Field(..., description="Recommended timeline")
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When recommendation was generated")
    expires_at: Optional[datetime] = Field(None, description="When recommendation expires")
    viewed_at: Optional[datetime] = Field(None, description="When user viewed recommendation")
    acted_on: bool = Field(default=False, description="Whether user acted on recommendation")
    acted_on_at: Optional[datetime] = Field(None, description="When user acted on recommendation")
    
    # Feedback
    user_feedback: Optional[str] = Field(None, description="User feedback on recommendation")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating of effectiveness")


class CoachingAnalytics(BaseModel):
    """Analytics for coaching effectiveness."""
    user_id: int = Field(..., description="User identifier")
    period_start: date = Field(..., description="Analytics period start")
    period_end: date = Field(..., description="Analytics period end")
    
    # Session metrics
    total_sessions: int = Field(default=0, ge=0, description="Total sessions in period")
    completed_sessions: int = Field(default=0, ge=0, description="Completed sessions")
    average_session_duration: float = Field(default=0.0, ge=0, description="Average session duration")
    
    # Engagement metrics
    engagement_rate: float = Field(default=0.0, ge=0, le=1, description="User engagement rate")
    response_rate: float = Field(default=0.0, ge=0, le=1, description="Response rate to recommendations")
    satisfaction_score: float = Field(default=0.0, ge=0, le=5, description="Average satisfaction score")
    
    # Progress metrics
    goals_achieved: int = Field(default=0, ge=0, description="Goals achieved in period")
    habits_formed: int = Field(default=0, ge=0, description="New habits formed")
    behavior_changes: List[str] = Field(default_factory=list, description="Observed behavior changes")
    
    # Recommendation effectiveness
    recommendations_given: int = Field(default=0, ge=0, description="Recommendations provided")
    recommendations_followed: int = Field(default=0, ge=0, description="Recommendations followed")
    recommendation_success_rate: float = Field(default=0.0, ge=0, le=1, description="Success rate of recommendations")
    
    # Hydration improvement
    hydration_improvement: float = Field(default=0.0, description="Improvement in hydration metrics")
    goal_achievement_rate: float = Field(default=0.0, ge=0, le=1, description="Rate of goal achievement")
    consistency_improvement: float = Field(default=0.0, description="Improvement in consistency")
    
    # Generated insights
    key_insights: List[str] = Field(default_factory=list, description="Key insights from analysis")
    recommendations_for_improvement: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When analytics were generated")


# Request/Response models
class CoachingTipCreate(BaseModel):
    """Request model for creating coaching tips."""
    category: TipCategory
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10, max_length=1000)
    short_description: Optional[str] = Field(None, max_length=300)
    coaching_level: List[CoachingLevel] = Field(default_factory=list)
    coaching_style: List[CoachingStyle] = Field(default_factory=list)
    triggers: List[CoachingTrigger] = Field(default_factory=list)
    personalization_tags: List[str] = Field(default_factory=list)
    min_user_level: int = Field(default=1, ge=1)
    seasonal: bool = Field(default=False)
    time_sensitive: bool = Field(default=False)


class CoachingSessionCreate(BaseModel):
    """Request model for creating coaching sessions."""
    session_type: CoachingSessionType
    trigger: CoachingTrigger
    title: str = Field(..., min_length=1, max_length=200)
    introduction: str
    action_items: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)


class CoachingProfileUpdate(BaseModel):
    """Request model for updating coaching profile."""
    coaching_level: Optional[CoachingLevel] = None
    coaching_style: Optional[CoachingStyle] = None
    session_frequency: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None
    motivation_factors: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    lifestyle_factors: Optional[Dict[str, Any]] = None
    health_conditions: Optional[List[str]] = None


class CoachingSessionResponse(BaseModel):
    """Response model for coaching sessions."""
    user_responses: Dict[str, Any] = Field(default_factory=dict)
    user_feedback: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    goals_set: List[str] = Field(default_factory=list)
    commitments_made: List[str] = Field(default_factory=list)


class CoachingRecommendationFeedback(BaseModel):
    """Feedback on coaching recommendations."""
    user_feedback: str
    effectiveness_rating: int = Field(..., ge=1, le=5)
    acted_on: bool = Field(default=False) 