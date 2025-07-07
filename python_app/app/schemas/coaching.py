"""
Pydantic schemas for hydration coaching API endpoints.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.models.coaching import (
    CoachingLevel, CoachingStyle, TipCategory, CoachingSessionType,
    CoachingTrigger, CoachingTip, CoachingSession, CoachingProfile,
    CoachingRecommendation, CoachingAnalytics, PersonalizationFactor
)


# Base response models
class BaseCoachingResponse(BaseModel):
    """Base response model for coaching endpoints."""
    success: bool = Field(default=True, description="Whether request was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class CoachingTipBase(BaseModel):
    """Base schema for coaching tips."""
    category: TipCategory = Field(..., description="Category of the tip")
    title: str = Field(..., min_length=1, max_length=200, description="Tip title")
    content: str = Field(..., min_length=10, max_length=1000, description="Tip content")
    short_description: Optional[str] = Field(None, max_length=300, description="Brief summary")
    coaching_level: List[CoachingLevel] = Field(default_factory=list, description="Applicable coaching levels")
    coaching_style: List[CoachingStyle] = Field(default_factory=list, description="Applicable coaching styles")
    triggers: List[CoachingTrigger] = Field(default_factory=list, description="When to show this tip")
    personalization_tags: List[str] = Field(default_factory=list, description="Tags for personalization")
    min_user_level: int = Field(default=1, ge=1, description="Minimum user level to show tip")
    seasonal: bool = Field(default=False, description="Whether tip is seasonal")
    time_sensitive: bool = Field(default=False, description="Whether tip is time-sensitive")


class CoachingTipCreate(CoachingTipBase):
    """Schema for creating coaching tips."""
    pass


class CoachingTipUpdate(BaseModel):
    """Schema for updating coaching tips."""
    category: Optional[TipCategory] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=10, max_length=1000)
    short_description: Optional[str] = Field(None, max_length=300)
    coaching_level: Optional[List[CoachingLevel]] = None
    coaching_style: Optional[List[CoachingStyle]] = None
    triggers: Optional[List[CoachingTrigger]] = None
    personalization_tags: Optional[List[str]] = None
    min_user_level: Optional[int] = Field(None, ge=1)
    seasonal: Optional[bool] = None
    time_sensitive: Optional[bool] = None
    is_active: Optional[bool] = None


class CoachingTipResponse(CoachingTipBase):
    """Schema for coaching tip responses."""
    id: str = Field(..., description="Unique tip identifier")
    effectiveness_score: float = Field(..., ge=0, le=1, description="How effective this tip is")
    usage_count: int = Field(..., ge=0, description="How many times tip was shown")
    positive_feedback: int = Field(..., ge=0, description="Positive feedback count")
    negative_feedback: int = Field(..., ge=0, description="Negative feedback count")
    created_at: datetime = Field(..., description="When tip was created")
    updated_at: datetime = Field(..., description="When tip was last updated")
    is_active: bool = Field(..., description="Whether tip is active")


class CoachingSessionBase(BaseModel):
    """Base schema for coaching sessions."""
    session_type: CoachingSessionType = Field(..., description="Type of coaching session")
    trigger: CoachingTrigger = Field(..., description="What triggered this session")
    title: str = Field(..., min_length=1, max_length=200, description="Session title")
    introduction: str = Field(..., description="Session introduction message")
    action_items: List[str] = Field(default_factory=list, description="Recommended actions")
    questions: List[str] = Field(default_factory=list, description="Questions for user reflection")


class CoachingSessionCreate(CoachingSessionBase):
    """Schema for creating coaching sessions."""
    pass


class CoachingSessionResponse(CoachingSessionBase):
    """Schema for coaching session responses."""
    id: str = Field(..., description="Unique session identifier")
    user_id: int = Field(..., description="User receiving coaching")
    tips: List[CoachingTipResponse] = Field(default_factory=list, description="Tips provided in session")
    coaching_level: CoachingLevel = Field(..., description="User's coaching level")
    coaching_style: CoachingStyle = Field(..., description="Coaching style used")
    personalization_factors: List[PersonalizationFactor] = Field(default_factory=list, description="Factors used for personalization")
    started_at: datetime = Field(..., description="When session started")
    completed_at: Optional[datetime] = Field(None, description="When session was completed")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Session duration in minutes")
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="User responses during session")
    user_feedback: Optional[str] = Field(None, description="User feedback on session")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="User satisfaction rating")
    goals_set: List[str] = Field(default_factory=list, description="Goals set during session")
    commitments_made: List[str] = Field(default_factory=list, description="User commitments")
    follow_up_scheduled: bool = Field(default=False, description="Whether follow-up is scheduled")
    follow_up_date: Optional[datetime] = Field(None, description="When to follow up")


class CoachingSessionFeedback(BaseModel):
    """Schema for coaching session feedback."""
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="User responses during session")
    user_feedback: Optional[str] = Field(None, description="User feedback on session")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="User satisfaction rating")
    goals_set: List[str] = Field(default_factory=list, description="Goals set during session")
    commitments_made: List[str] = Field(default_factory=list, description="User commitments")


class CoachingProfileBase(BaseModel):
    """Base schema for coaching profiles."""
    coaching_level: CoachingLevel = Field(default=CoachingLevel.BEGINNER, description="User's coaching level")
    coaching_style: CoachingStyle = Field(default=CoachingStyle.ENCOURAGING, description="Preferred coaching style")
    session_frequency: str = Field(default="weekly", description="Preferred session frequency")
    reminder_enabled: bool = Field(default=True, description="Whether to send coaching reminders")
    reminder_time: Optional[str] = Field(None, description="Preferred reminder time (HH:MM)")
    motivation_factors: List[str] = Field(default_factory=list, description="What motivates the user")
    challenges: List[str] = Field(default_factory=list, description="User's main challenges")
    goals: List[str] = Field(default_factory=list, description="User's hydration goals")
    lifestyle_factors: Dict[str, Any] = Field(default_factory=dict, description="Lifestyle information")
    health_conditions: List[str] = Field(default_factory=list, description="Relevant health conditions")

    @field_validator('reminder_time')
    @classmethod
    def validate_reminder_time(cls, v):
        if v is not None:
            try:
                hour, minute = map(int, v.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError('Invalid time format')
            except (ValueError, TypeError):
                raise ValueError('Time must be in HH:MM format')
        return v


class CoachingProfileCreate(CoachingProfileBase):
    """Schema for creating coaching profiles."""
    pass


class CoachingProfileUpdate(BaseModel):
    """Schema for updating coaching profiles."""
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

    @field_validator('reminder_time')
    @classmethod
    def validate_reminder_time(cls, v):
        if v is not None:
            try:
                hour, minute = map(int, v.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError('Invalid time format')
            except (ValueError, TypeError):
                raise ValueError('Time must be in HH:MM format')
        return v


class CoachingProfileResponse(CoachingProfileBase):
    """Schema for coaching profile responses."""
    user_id: int = Field(..., description="User identifier")
    total_sessions: int = Field(..., ge=0, description="Total coaching sessions completed")
    current_streak: int = Field(..., ge=0, description="Current engagement streak")
    best_streak: int = Field(..., ge=0, description="Best engagement streak")
    last_session_date: Optional[date] = Field(None, description="Date of last session")
    goal_completion_rate: float = Field(..., ge=0, le=1, description="Rate of goal completion")
    engagement_score: float = Field(..., ge=0, le=1, description="User engagement score")
    satisfaction_average: float = Field(..., ge=0, le=5, description="Average satisfaction rating")
    created_at: datetime = Field(..., description="When profile was created")
    updated_at: datetime = Field(..., description="When profile was last updated")
    is_active: bool = Field(..., description="Whether coaching is active")


class CoachingRecommendationBase(BaseModel):
    """Base schema for coaching recommendations."""
    type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., min_length=1, max_length=200, description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    priority: int = Field(default=3, ge=1, le=5, description="Recommendation priority")
    action_steps: List[str] = Field(default_factory=list, description="Specific action steps")
    expected_outcome: str = Field(..., description="Expected outcome if followed")
    timeline: str = Field(..., description="Recommended timeline")


class CoachingRecommendationCreate(CoachingRecommendationBase):
    """Schema for creating coaching recommendations."""
    confidence_score: float = Field(..., ge=0, le=1, description="AI confidence in recommendation")
    reasoning: str = Field(..., description="AI reasoning for recommendation")
    data_points_used: List[str] = Field(default_factory=list, description="Data points used for recommendation")
    expires_at: Optional[datetime] = Field(None, description="When recommendation expires")


class CoachingRecommendationResponse(CoachingRecommendationBase):
    """Schema for coaching recommendation responses."""
    id: str = Field(..., description="Unique recommendation identifier")
    user_id: int = Field(..., description="Target user")
    confidence_score: float = Field(..., ge=0, le=1, description="AI confidence in recommendation")
    reasoning: str = Field(..., description="AI reasoning for recommendation")
    data_points_used: List[str] = Field(default_factory=list, description="Data points used for recommendation")
    created_at: datetime = Field(..., description="When recommendation was generated")
    expires_at: Optional[datetime] = Field(None, description="When recommendation expires")
    viewed_at: Optional[datetime] = Field(None, description="When user viewed recommendation")
    acted_on: bool = Field(default=False, description="Whether user acted on recommendation")
    acted_on_at: Optional[datetime] = Field(None, description="When user acted on recommendation")
    user_feedback: Optional[str] = Field(None, description="User feedback on recommendation")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating of effectiveness")


class CoachingRecommendationFeedback(BaseModel):
    """Schema for coaching recommendation feedback."""
    user_feedback: str = Field(..., description="User feedback on recommendation")
    effectiveness_rating: int = Field(..., ge=1, le=5, description="User rating of effectiveness")
    acted_on: bool = Field(default=False, description="Whether user acted on recommendation")


class CoachingAnalyticsResponse(BaseModel):
    """Schema for coaching analytics responses."""
    user_id: int = Field(..., description="User identifier")
    period_start: date = Field(..., description="Analytics period start")
    period_end: date = Field(..., description="Analytics period end")
    total_sessions: int = Field(..., ge=0, description="Total sessions in period")
    completed_sessions: int = Field(..., ge=0, description="Completed sessions")
    average_session_duration: float = Field(..., ge=0, description="Average session duration")
    engagement_rate: float = Field(..., ge=0, le=1, description="User engagement rate")
    response_rate: float = Field(..., ge=0, le=1, description="Response rate to recommendations")
    satisfaction_score: float = Field(..., ge=0, le=5, description="Average satisfaction score")
    goals_achieved: int = Field(..., ge=0, description="Goals achieved in period")
    habits_formed: int = Field(..., ge=0, description="New habits formed")
    behavior_changes: List[str] = Field(default_factory=list, description="Observed behavior changes")
    recommendations_given: int = Field(..., ge=0, description="Recommendations provided")
    recommendations_followed: int = Field(..., ge=0, description="Recommendations followed")
    recommendation_success_rate: float = Field(..., ge=0, le=1, description="Success rate of recommendations")
    hydration_improvement: float = Field(..., description="Improvement in hydration metrics")
    goal_achievement_rate: float = Field(..., ge=0, le=1, description="Rate of goal achievement")
    consistency_improvement: float = Field(..., description="Improvement in consistency")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from analysis")
    recommendations_for_improvement: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    created_at: datetime = Field(..., description="When analytics were generated")


class PersonalizedTipRequest(BaseModel):
    """Schema for requesting personalized tips."""
    category: Optional[TipCategory] = Field(None, description="Specific category to focus on")
    trigger: Optional[CoachingTrigger] = Field(None, description="Specific trigger context")
    limit: int = Field(default=5, ge=1, le=20, description="Number of tips to return")
    include_seasonal: bool = Field(default=True, description="Whether to include seasonal tips")
    include_time_sensitive: bool = Field(default=True, description="Whether to include time-sensitive tips")


class CoachingInsightsResponse(BaseModel):
    """Schema for coaching insights responses."""
    user_id: int = Field(..., description="User identifier")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    progress_summary: str = Field(..., description="Summary of user progress")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in insights")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When insights were generated")


class CoachingDashboardResponse(BaseModel):
    """Schema for coaching dashboard responses."""
    profile: CoachingProfileResponse = Field(..., description="User's coaching profile")
    recent_sessions: List[CoachingSessionResponse] = Field(default_factory=list, description="Recent coaching sessions")
    active_recommendations: List[CoachingRecommendationResponse] = Field(default_factory=list, description="Active recommendations")
    upcoming_sessions: List[Dict[str, Any]] = Field(default_factory=list, description="Upcoming scheduled sessions")
    progress_metrics: Dict[str, Any] = Field(default_factory=dict, description="Progress metrics")
    personalized_tips: List[CoachingTipResponse] = Field(default_factory=list, description="Personalized tips")
    insights: CoachingInsightsResponse = Field(..., description="AI-generated insights")


# Bulk operation schemas
class BulkCoachingTipCreate(BaseModel):
    """Schema for bulk creating coaching tips."""
    tips: List[CoachingTipCreate] = Field(..., min_items=1, max_items=100, description="Tips to create")


class BulkCoachingTipResponse(BaseModel):
    """Schema for bulk coaching tip creation responses."""
    created_tips: List[CoachingTipResponse] = Field(default_factory=list, description="Successfully created tips")
    failed_tips: List[Dict[str, Any]] = Field(default_factory=list, description="Failed tip creations with errors")
    total_created: int = Field(..., ge=0, description="Total tips created")
    total_failed: int = Field(..., ge=0, description="Total tips failed")


# Filter and search schemas
class CoachingTipFilter(BaseModel):
    """Schema for filtering coaching tips."""
    category: Optional[TipCategory] = None
    coaching_level: Optional[List[CoachingLevel]] = None
    coaching_style: Optional[List[CoachingStyle]] = None
    triggers: Optional[List[CoachingTrigger]] = None
    is_active: Optional[bool] = None
    min_effectiveness_score: Optional[float] = Field(None, ge=0, le=1)
    search_query: Optional[str] = Field(None, min_length=1, max_length=100)


class CoachingSessionFilter(BaseModel):
    """Schema for filtering coaching sessions."""
    session_type: Optional[CoachingSessionType] = None
    trigger: Optional[CoachingTrigger] = None
    coaching_level: Optional[CoachingLevel] = None
    coaching_style: Optional[CoachingStyle] = None
    completed: Optional[bool] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_satisfaction_rating: Optional[int] = Field(None, ge=1, le=5) 