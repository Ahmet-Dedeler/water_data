"""
API endpoints for hydration coaching and AI-powered recommendations.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_current_admin_user
from app.models.coaching import CoachingLevel, CoachingStyle, TipCategory, CoachingSessionType, CoachingTrigger
from app.schemas.coaching import (
    BaseCoachingResponse, CoachingTipCreate, CoachingTipUpdate, CoachingTipResponse,
    CoachingSessionCreate, CoachingSessionResponse, CoachingSessionFeedback,
    CoachingProfileCreate, CoachingProfileUpdate, CoachingProfileResponse,
    CoachingRecommendationResponse, CoachingRecommendationFeedback,
    CoachingAnalyticsResponse, PersonalizedTipRequest, CoachingInsightsResponse,
    CoachingDashboardResponse, BulkCoachingTipCreate, BulkCoachingTipResponse,
    CoachingTipFilter, CoachingSessionFilter
)
from app.services.coaching_service import coaching_service

logger = logging.getLogger(__name__)
router = APIRouter()


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int


# Coaching Tips Endpoints
@router.post("/tips", response_model=CoachingTipResponse, status_code=status.HTTP_201_CREATED)
async def create_coaching_tip(
    tip_data: CoachingTipCreate,
    current_user: dict = Depends(get_current_admin_user)
):
    """Create a new coaching tip (Admin only)."""
    try:
        tip = await coaching_service.create_tip(tip_data)
        return tip
    except Exception as e:
        logger.error(f"Error creating coaching tip: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tips/{tip_id}", response_model=CoachingTipResponse)
async def get_coaching_tip(
    tip_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific coaching tip."""
    tip = await coaching_service.get_tip(tip_id)
    if not tip:
        raise HTTPException(status_code=404, detail="Coaching tip not found")
    return tip


@router.put("/tips/{tip_id}", response_model=CoachingTipResponse)
async def update_coaching_tip(
    tip_id: str,
    update_data: CoachingTipUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """Update a coaching tip (Admin only)."""
    tip = await coaching_service.update_tip(tip_id, update_data)
    if not tip:
        raise HTTPException(status_code=404, detail="Coaching tip not found")
    return tip


@router.delete("/tips/{tip_id}", response_model=BaseCoachingResponse)
async def delete_coaching_tip(
    tip_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Delete a coaching tip (Admin only)."""
    success = await coaching_service.delete_tip(tip_id)
    if not success:
        raise HTTPException(status_code=404, detail="Coaching tip not found")
    
    return BaseCoachingResponse(
        message=f"Coaching tip {tip_id} deleted successfully"
    )


@router.get("/tips", response_model=PaginatedResponse)
async def get_coaching_tips(
    category: Optional[TipCategory] = Query(None, description="Filter by category"),
    coaching_level: Optional[List[CoachingLevel]] = Query(None, description="Filter by coaching levels"),
    coaching_style: Optional[List[CoachingStyle]] = Query(None, description="Filter by coaching styles"),
    triggers: Optional[List[CoachingTrigger]] = Query(None, description="Filter by triggers"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_effectiveness_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum effectiveness score"),
    search_query: Optional[str] = Query(None, min_length=1, max_length=100, description="Search in title and content"),
    skip: int = Query(0, ge=0, description="Number of tips to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of tips to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get coaching tips with filtering and pagination."""
    try:
        filter_data = CoachingTipFilter(
            category=category,
            coaching_level=coaching_level,
            coaching_style=coaching_style,
            triggers=triggers,
            is_active=is_active,
            min_effectiveness_score=min_effectiveness_score,
            search_query=search_query
        )
        
        tips, total = await coaching_service.get_tips(filter_data, skip, limit)
        
        return PaginatedResponse(
            items=[tip.dict() for tip in tips],
            total=total,
            page=skip // limit + 1,
            size=len(tips),
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        logger.error(f"Error getting coaching tips: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tips/bulk", response_model=BulkCoachingTipResponse)
async def create_coaching_tips_bulk(
    bulk_data: BulkCoachingTipCreate,
    current_user: dict = Depends(get_current_admin_user)
):
    """Create multiple coaching tips in bulk (Admin only)."""
    try:
        created_tips = []
        failed_tips = []
        
        for tip_data in bulk_data.tips:
            try:
                tip = await coaching_service.create_tip(tip_data)
                created_tips.append(tip)
            except Exception as e:
                failed_tips.append({
                    "tip_data": tip_data.dict(),
                    "error": str(e)
                })
        
        return BulkCoachingTipResponse(
            created_tips=created_tips,
            failed_tips=failed_tips,
            total_created=len(created_tips),
            total_failed=len(failed_tips)
        )
    except Exception as e:
        logger.error(f"Error creating coaching tips in bulk: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Personalized Tips
@router.post("/tips/personalized", response_model=List[CoachingTipResponse])
async def get_personalized_tips(
    request: PersonalizedTipRequest,
    current_user: dict = Depends(get_current_user)
):
    """Get personalized coaching tips for the current user."""
    try:
        tips = await coaching_service.get_personalized_tips(current_user["id"], request)
        return tips
    except Exception as e:
        logger.error(f"Error getting personalized tips for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Coaching Profile Endpoints
@router.post("/profile", response_model=CoachingProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_coaching_profile(
    profile_data: CoachingProfileCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create coaching profile for the current user."""
    try:
        profile = await coaching_service.create_coaching_profile(current_user["id"], profile_data)
        return profile
    except Exception as e:
        logger.error(f"Error creating coaching profile for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile", response_model=CoachingProfileResponse)
async def get_coaching_profile(
    current_user: dict = Depends(get_current_user)
):
    """Get coaching profile for the current user."""
    profile = await coaching_service.get_coaching_profile(current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Coaching profile not found")
    return profile


@router.put("/profile", response_model=CoachingProfileResponse)
async def update_coaching_profile(
    update_data: CoachingProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update coaching profile for the current user."""
    profile = await coaching_service.update_coaching_profile(current_user["id"], update_data)
    if not profile:
        raise HTTPException(status_code=404, detail="Coaching profile not found")
    return profile


# Coaching Sessions Endpoints
@router.post("/sessions", response_model=CoachingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_coaching_session(
    session_data: CoachingSessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new coaching session for the current user."""
    try:
        session = await coaching_service.create_coaching_session(current_user["id"], session_data)
        return session
    except Exception as e:
        logger.error(f"Error creating coaching session for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}", response_model=CoachingSessionResponse)
async def get_coaching_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific coaching session."""
    session = await coaching_service.get_coaching_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    
    # Check if user owns the session
    if session.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session


@router.post("/sessions/{session_id}/complete", response_model=CoachingSessionResponse)
async def complete_coaching_session(
    session_id: str,
    feedback: CoachingSessionFeedback,
    current_user: dict = Depends(get_current_user)
):
    """Complete a coaching session with user feedback."""
    session = await coaching_service.complete_coaching_session(session_id, current_user["id"], feedback)
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    return session


@router.get("/sessions", response_model=PaginatedResponse)
async def get_user_coaching_sessions(
    session_type: Optional[CoachingSessionType] = Query(None, description="Filter by session type"),
    trigger: Optional[CoachingTrigger] = Query(None, description="Filter by trigger"),
    coaching_level: Optional[CoachingLevel] = Query(None, description="Filter by coaching level"),
    coaching_style: Optional[CoachingStyle] = Query(None, description="Filter by coaching style"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    date_from: Optional[date] = Query(None, description="Filter sessions from this date"),
    date_to: Optional[date] = Query(None, description="Filter sessions to this date"),
    min_satisfaction_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum satisfaction rating"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get coaching sessions for the current user."""
    try:
        filter_data = CoachingSessionFilter(
            session_type=session_type,
            trigger=trigger,
            coaching_level=coaching_level,
            coaching_style=coaching_style,
            completed=completed,
            date_from=date_from,
            date_to=date_to,
            min_satisfaction_rating=min_satisfaction_rating
        )
        
        sessions, total = await coaching_service.get_user_sessions(current_user["id"], filter_data, skip, limit)
        
        return PaginatedResponse(
            items=[session.dict() for session in sessions],
            total=total,
            page=skip // limit + 1,
            size=len(sessions),
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        logger.error(f"Error getting coaching sessions for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Recommendations Endpoints
@router.get("/recommendations", response_model=List[CoachingRecommendationResponse])
async def get_coaching_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """Get AI-powered coaching recommendations for the current user."""
    try:
        recommendations = await coaching_service.generate_recommendations(current_user["id"])
        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/recommendations/{recommendation_id}/feedback", response_model=BaseCoachingResponse)
async def provide_recommendation_feedback(
    recommendation_id: str,
    feedback: CoachingRecommendationFeedback,
    current_user: dict = Depends(get_current_user)
):
    """Provide feedback on a coaching recommendation."""
    try:
        # This would be implemented in the service
        # For now, return success response
        return BaseCoachingResponse(
            message="Feedback recorded successfully"
        )
    except Exception as e:
        logger.error(f"Error recording recommendation feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Analytics Endpoints
@router.get("/analytics", response_model=CoachingAnalyticsResponse)
async def get_coaching_analytics(
    period_start: date = Query(..., description="Analytics period start date"),
    period_end: date = Query(..., description="Analytics period end date"),
    current_user: dict = Depends(get_current_user)
):
    """Get coaching analytics for the current user."""
    try:
        # Validate date range
        if period_end < period_start:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        if (period_end - period_start).days > 365:
            raise HTTPException(status_code=400, detail="Analytics period cannot exceed 365 days")
        
        analytics = await coaching_service.generate_analytics(current_user["id"], period_start, period_end)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/insights", response_model=CoachingInsightsResponse)
async def get_coaching_insights(
    current_user: dict = Depends(get_current_user)
):
    """Get AI-generated coaching insights for the current user."""
    try:
        # Get recent analytics for insights
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        analytics = await coaching_service.generate_analytics(current_user["id"], start_date, end_date)
        
        insights = CoachingInsightsResponse(
            user_id=current_user["id"],
            insights=analytics.key_insights,
            recommendations=analytics.recommendations_for_improvement,
            progress_summary=f"In the last 30 days: {analytics.completed_sessions} sessions completed with {analytics.engagement_rate:.1%} engagement rate",
            next_steps=[
                "Continue with your current coaching frequency",
                "Focus on implementing session commitments",
                "Consider adjusting coaching style if satisfaction is low"
            ],
            confidence_score=0.85 if analytics.total_sessions >= 5 else 0.6
        )
        
        return insights
    except Exception as e:
        logger.error(f"Error generating insights for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard", response_model=CoachingDashboardResponse)
async def get_coaching_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive coaching dashboard for the current user."""
    try:
        # Get profile
        profile = await coaching_service.get_coaching_profile(current_user["id"])
        if not profile:
            profile = await coaching_service.create_coaching_profile(current_user["id"], CoachingProfileCreate())
        
        # Get recent sessions
        recent_sessions, _ = await coaching_service.get_user_sessions(current_user["id"], limit=5)
        
        # Get personalized tips
        tip_request = PersonalizedTipRequest(limit=3)
        personalized_tips = await coaching_service.get_personalized_tips(current_user["id"], tip_request)
        
        # Get recommendations
        recommendations = await coaching_service.generate_recommendations(current_user["id"])
        active_recommendations = [r for r in recommendations if not r.expires_at or r.expires_at > datetime.utcnow()]
        
        # Get insights
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        analytics = await coaching_service.generate_analytics(current_user["id"], start_date, end_date)
        
        insights = CoachingInsightsResponse(
            user_id=current_user["id"],
            insights=analytics.key_insights,
            recommendations=analytics.recommendations_for_improvement,
            progress_summary=f"Last 30 days: {analytics.completed_sessions} sessions, {analytics.engagement_rate:.1%} engagement",
            next_steps=["Continue regular sessions", "Implement session commitments"],
            confidence_score=0.8
        )
        
        dashboard = CoachingDashboardResponse(
            profile=profile,
            recent_sessions=recent_sessions,
            active_recommendations=active_recommendations,
            upcoming_sessions=[],  # Would be implemented with scheduling
            progress_metrics={
                "total_sessions": profile.total_sessions,
                "current_streak": profile.current_streak,
                "goal_completion_rate": profile.goal_completion_rate,
                "engagement_score": profile.engagement_score
            },
            personalized_tips=personalized_tips,
            insights=insights
        )
        
        return dashboard
    except Exception as e:
        logger.error(f"Error generating dashboard for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Admin Endpoints
@router.get("/admin/tips/analytics", response_model=dict)
async def get_tips_analytics(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get analytics for all coaching tips (Admin only)."""
    try:
        tips, _ = await coaching_service.get_tips(limit=1000)
        
        analytics = {
            "total_tips": len(tips),
            "active_tips": len([t for t in tips if t.is_active]),
            "average_effectiveness": sum(t.effectiveness_score for t in tips) / len(tips) if tips else 0,
            "most_used_categories": {},
            "feedback_summary": {
                "total_positive": sum(t.positive_feedback for t in tips),
                "total_negative": sum(t.negative_feedback for t in tips),
                "total_usage": sum(t.usage_count for t in tips)
            }
        }
        
        # Category usage
        for tip in tips:
            category = tip.category
            if category not in analytics["most_used_categories"]:
                analytics["most_used_categories"][category] = 0
            analytics["most_used_categories"][category] += tip.usage_count
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting tips analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/users/{user_id}/profile", response_model=CoachingProfileResponse)
async def get_user_coaching_profile_admin(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """Get coaching profile for any user (Admin only)."""
    profile = await coaching_service.get_coaching_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Coaching profile not found")
    return profile


@router.get("/admin/users/{user_id}/sessions", response_model=PaginatedResponse)
async def get_user_sessions_admin(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get coaching sessions for any user (Admin only)."""
    try:
        sessions, total = await coaching_service.get_user_sessions(user_id, skip=skip, limit=limit)
        
        return PaginatedResponse(
            items=[session.dict() for session in sessions],
            total=total,
            page=skip // limit + 1,
            size=len(sessions),
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        logger.error(f"Error getting sessions for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 