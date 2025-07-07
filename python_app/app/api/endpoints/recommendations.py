from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
import logging

from app.models.recommendation import (
    Recommendation, RecommendationRequest, RecommendationResponse,
    UserPreferenceProfile, RecommendationFeedback, RecommendationType,
    CustomRecommendationRequest
)
from app.models.common import BaseResponse
from app.services.recommendation_service import recommendation_service
from app.core.auth import get_current_user, get_current_user_optional
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.get("/", response_model=RecommendationResponse)
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    recommendation_type: Optional[RecommendationType] = Query(None, description="Type of recommendations to filter by"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence threshold"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get personalized water recommendations.
    
    - **limit**: Number of recommendations (1-50)
    - **recommendation_type**: Filter by recommendation type
    - **min_confidence**: Minimum confidence score (0-1)
    
    Returns personalized recommendations if user is authenticated, 
    otherwise returns general popular recommendations.
    """
    try:
        request = RecommendationRequest(
            limit=limit,
            recommendation_type=recommendation_type,
            min_confidence=min_confidence
        )
        
        user_id = current_user.id if current_user else None
        recommendations = await recommendation_service.generate_recommendations(
            user_id=user_id,
            request=request
        )
        
        logger.info(f"Generated {len(recommendations.recommendations)} recommendations for user {user_id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.post("/personalized", response_model=BaseResponse[List[Recommendation]])
async def get_personalized_recommendations(
    request: RecommendationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get personalized water recommendations for a user."""
    try:
        user_id = current_user.id if current_user else request.user_id
        recommendations = await recommendation_service.generate_recommendations(
            user_id=user_id,
            request=request
        )
        return BaseResponse(
            data=recommendations,
            message="Personalized recommendations retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generic", response_model=BaseResponse[List[Recommendation]])
async def get_generic_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations")
):
    """Get generic recommendations."""
    try:
        recommendations = await recommendation_service.generate_generic_recommendations(limit=limit)
        return BaseResponse(
            data=recommendations,
            message="Generic recommendations retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting generic recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/custom", response_model=BaseResponse[List[Recommendation]])
async def get_custom_recommendations(
    request: CustomRecommendationRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get recommendations based on custom criteria."""
    try:
        user_id = current_user.id if current_user else request.user_id
        recommendations = await recommendation_service.generate_custom_recommendations(
            user_id=user_id,
            request=request
        )
        return BaseResponse(
            data=recommendations,
            message="Custom recommendations retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting custom recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/preferences/{user_id}", response_model=BaseResponse[UserPreferenceProfile])
async def get_user_preferences(user_id: str):
    """Get user preference profile."""
    try:
        profile = await recommendation_service.get_user_preference_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User preference profile not found")
        return BaseResponse(
            data=profile,
            message="User preference profile retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/preferences/{user_id}", response_model=BaseResponse[UserPreferenceProfile])
async def update_user_preferences(user_id: str, profile: UserPreferenceProfile):
    """Update user preference profile."""
    try:
        if profile.user_id != user_id:
            raise HTTPException(status_code=400, detail="User ID mismatch in profile data")
            
        updated_profile = await recommendation_service.update_user_preference_profile(profile)
        return BaseResponse(
            data=updated_profile,
            message="User preference profile updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/feedback", response_model=BaseResponse[RecommendationFeedback])
async def submit_feedback(feedback: RecommendationFeedback):
    """Submit feedback on a recommendation."""
    try:
        saved_feedback = await recommendation_service.save_feedback(feedback)
        return BaseResponse(
            data=saved_feedback,
            message="Feedback submitted successfully"
        )
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/similar/{water_id}", response_model=RecommendationResponse)
async def get_similar_waters(
    water_id: int,
    limit: int = Query(5, ge=1, le=20, description="Number of similar waters to return"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get waters similar to a specific water.
    
    - **water_id**: ID of the water to find similar waters for
    - **limit**: Number of similar waters to return (1-20)
    """
    try:
        request = RecommendationRequest(
            limit=limit,
            exclude_water_ids=[water_id],
            criteria=None  # Will be inferred from the target water
        )
        
        user_id = current_user.id if current_user else None
        recommendations = await recommendation_service.generate_recommendations(
            user_id=user_id,
            request=request
        )
        
        logger.info(f"Generated {len(recommendations.recommendations)} similar waters for water {water_id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error finding similar waters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar waters"
        )


@router.get("/profile", response_model=UserPreferenceProfile)
async def get_user_preference_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the user's preference profile.
    
    Returns learned preferences based on:
    - User's explicit preferences
    - Review history and ratings
    - Behavioral patterns
    """
    try:
        profile = await recommendation_service.get_user_preference_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User preference profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user preference profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preference profile"
        )


@router.get("/trending", response_model=RecommendationResponse)
async def get_trending_recommendations(
    limit: int = Query(10, ge=1, le=20, description="Number of trending waters to return"),
    time_period: str = Query("week", regex="^(day|week|month)$", description="Time period for trending calculation")
):
    """
    Get currently trending water recommendations.
    
    - **limit**: Number of trending waters (1-20)
    - **time_period**: Time window for trend calculation (day/week/month)
    
    Trending waters are determined by:
    - Recent review activity
    - Rating improvements
    - User engagement patterns
    """
    try:
        request = RecommendationRequest(
            limit=limit,
            recommendation_type=RecommendationType.TRENDING
        )
        
        recommendations = await recommendation_service.generate_recommendations(
            user_id=None,  # Anonymous trending recommendations
            request=request
        )
        
        logger.info(f"Generated {len(recommendations.recommendations)} trending recommendations")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating trending recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate trending recommendations"
        )


@router.get("/health-focused", response_model=RecommendationResponse)
async def get_health_focused_recommendations(
    health_goal: str = Query(..., description="Primary health goal (hydration, detox, mineral_balance, etc.)"),
    min_health_score: int = Query(80, ge=50, le=100, description="Minimum health score"),
    limit: int = Query(10, ge=1, le=20, description="Number of recommendations"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get health-focused recommendations for specific health goals.
    
    - **health_goal**: Primary health goal to optimize for
    - **min_health_score**: Minimum required health score (50-100)
    - **limit**: Number of recommendations (1-20)
    """
    try:
        from app.models.recommendation import RecommendationCriteria
        
        criteria = RecommendationCriteria(
            health_goals=[health_goal],
            min_health_score=min_health_score
        )
        
        request = RecommendationRequest(
            limit=limit,
            criteria=criteria,
            recommendation_type=RecommendationType.HEALTH_BASED
        )
        
        user_id = current_user.id if current_user else None
        recommendations = await recommendation_service.generate_recommendations(
            user_id=user_id,
            request=request
        )
        
        logger.info(f"Generated {len(recommendations.recommendations)} health-focused recommendations for goal: {health_goal}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating health-focused recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate health-focused recommendations"
        )


@router.get("/discover", response_model=RecommendationResponse)
async def get_discovery_recommendations(
    limit: int = Query(5, ge=1, le=10, description="Number of discovery recommendations"),
    novelty_weight: float = Query(0.8, ge=0.5, le=1.0, description="Weight for novelty factor"),
    current_user: User = Depends(get_current_user)
):
    """
    Get discovery recommendations for trying new waters.
    
    - **limit**: Number of discovery recommendations (1-10)
    - **novelty_weight**: How much to emphasize novelty vs. other factors (0.5-1.0)
    
    Discovery recommendations prioritize:
    - Waters the user hasn't tried
    - New products in the database
    - Unique flavor profiles
    """
    try:
        from app.models.recommendation import RecommendationCriteria
        
        criteria = RecommendationCriteria(
            novelty_factor=novelty_weight,
            diversity_factor=0.9  # High diversity for discovery
        )
        
        request = RecommendationRequest(
            limit=limit,
            criteria=criteria
        )
        
        recommendations = await recommendation_service.generate_recommendations(
            user_id=current_user.id,
            request=request
        )
        
        logger.info(f"Generated {len(recommendations.recommendations)} discovery recommendations for user {current_user.id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating discovery recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate discovery recommendations"
        )


@router.get("/stats", response_model=BaseResponse[dict])
async def get_recommendation_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get recommendation statistics for the current user.
    
    Returns:
    - Total recommendations received
    - Feedback given
    - Preference confidence level
    - Recommendation accuracy
    """
    try:
        profile = await recommendation_service.get_user_preference_profile(current_user.id)
        
        stats = {
            "preference_confidence": profile.preference_confidence if profile else 0.0,
            "data_points": profile.data_points if profile else 0,
            "last_updated": profile.last_updated.isoformat() if profile and profile.last_updated else None,
            "brand_preferences_count": len(profile.brand_affinity) if profile and profile.brand_affinity else 0,
            "packaging_preferences_count": len(profile.packaging_preferences) if profile and profile.packaging_preferences else 0
        }
        
        return BaseResponse(
            data=stats,
            message="Recommendation statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving recommendation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommendation statistics"
        )
