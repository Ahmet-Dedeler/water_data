from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.models.activity_feed import (
    ActivityFeedItem, ActivityEngagement, ActivityComment, ActivityFeedFilter,
    ActivityFeedResponse, ActivityCreate, ActivityUpdate, ActivityEngagementCreate,
    ActivityCommentCreate, ActivityCommentUpdate, ActivityStats,
    ActivityFeedSettings, ActivityFeedSettingsUpdate, ActivityType,
    ActivityPriority, ActivityVisibility, EngagementType
)
from app.models.common import BaseResponse
from app.services.activity_feed_service import activity_feed_service
from app.api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Activity Feed Management

@router.get("/", response_model=BaseResponse[ActivityFeedResponse])
async def get_activity_feed(
    activity_types: Optional[List[ActivityType]] = Query(None, description="Filter by activity types"),
    user_ids: Optional[List[int]] = Query(None, description="Filter by specific users"),
    priority: Optional[ActivityPriority] = Query(None, description="Filter by priority"),
    is_milestone: Optional[bool] = Query(None, description="Filter milestone activities"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    has_engagement: Optional[bool] = Query(None, description="Filter activities with engagement"),
    skip: int = Query(0, ge=0, description="Number of activities to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activities to return"),
    current_user = Depends(get_current_user)
):
    """Get personalized activity feed for the current user."""
    try:
        # Build filter options
        filter_options = None
        if any([activity_types, user_ids, priority, is_milestone, date_from, date_to, has_engagement]):
            filter_options = ActivityFeedFilter(
                activity_types=activity_types,
                user_ids=user_ids,
                priority=priority,
                is_milestone=is_milestone,
                date_from=date_from,
                date_to=date_to,
                has_engagement=has_engagement
            )
        
        feed_response = await activity_feed_service.get_user_feed(
            user_id=current_user.id,
            filter_options=filter_options,
            skip=skip,
            limit=limit
        )
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(feed_response.activities)} activities",
            data=feed_response
        )
        
    except Exception as e:
        logger.error(f"Error getting activity feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity feed"
        )


@router.post("/", response_model=BaseResponse[ActivityFeedItem])
async def create_activity(
    activity_data: ActivityCreate,
    current_user = Depends(get_current_user)
):
    """Create a new activity in the feed."""
    try:
        activity = await activity_feed_service.create_activity(
            user_id=current_user.id,
            activity_data=activity_data
        )
        
        return BaseResponse(
            success=True,
            message="Activity created successfully",
            data=activity
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create activity"
        )


@router.post("/template/{activity_type}", response_model=BaseResponse[ActivityFeedItem])
async def create_activity_from_template(
    activity_type: ActivityType,
    template_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Create activity using a predefined template."""
    try:
        activity = await activity_feed_service.create_activity_from_template(
            user_id=current_user.id,
            activity_type=activity_type,
            template_data=template_data
        )
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No template found for activity type: {activity_type}"
            )
        
        return BaseResponse(
            success=True,
            message="Activity created from template successfully",
            data=activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating activity from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create activity from template"
        )


# Activity Engagement

@router.post("/{activity_id}/engage", response_model=BaseResponse[ActivityEngagement])
async def engage_with_activity(
    activity_id: int,
    engagement_data: ActivityEngagementCreate,
    current_user = Depends(get_current_user)
):
    """Add or update engagement with an activity."""
    try:
        engagement = await activity_feed_service.engage_with_activity(
            user_id=current_user.id,
            activity_id=activity_id,
            engagement_data=engagement_data
        )
        
        if not engagement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found or not accessible"
            )
        
        return BaseResponse(
            success=True,
            message=f"Successfully {engagement_data.engagement_type.value}d the activity",
            data=engagement
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error engaging with activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to engage with activity"
        )


@router.delete("/{activity_id}/engage", response_model=BaseResponse[bool])
async def remove_engagement(
    activity_id: int,
    current_user = Depends(get_current_user)
):
    """Remove engagement from an activity."""
    try:
        success = await activity_feed_service.remove_engagement(
            user_id=current_user.id,
            activity_id=activity_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Engagement not found"
            )
        
        return BaseResponse(
            success=True,
            message="Engagement removed successfully",
            data=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing engagement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove engagement"
        )


# Activity Comments

@router.post("/{activity_id}/comments", response_model=BaseResponse[ActivityComment])
async def add_comment(
    activity_id: int,
    comment_data: ActivityCommentCreate,
    current_user = Depends(get_current_user)
):
    """Add a comment to an activity."""
    try:
        comment = await activity_feed_service.add_comment(
            user_id=current_user.id,
            activity_id=activity_id,
            comment_data=comment_data
        )
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found or not accessible"
            )
        
        return BaseResponse(
            success=True,
            message="Comment added successfully",
            data=comment
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add comment"
        )


@router.get("/{activity_id}/comments", response_model=BaseResponse[List[ActivityComment]])
async def get_activity_comments(
    activity_id: int,
    skip: int = Query(0, ge=0, description="Number of comments to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of comments to return"),
    current_user = Depends(get_current_user)
):
    """Get comments for an activity."""
    try:
        # In a real implementation, this would be a separate service method
        # For now, we'll simulate it by checking if user can see the activity
        activities = await activity_feed_service._load_activities()
        comments = await activity_feed_service._load_comments()
        
        # Find the activity
        activity = next((a for a in activities if a['id'] == activity_id), None)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check if user can see this activity
        if not await activity_feed_service._can_user_see_activity(current_user.id, activity):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Activity not accessible"
            )
        
        # Get comments for this activity
        activity_comments = [
            ActivityComment(**c) for c in comments
            if c['activity_id'] == activity_id
        ]
        
        # Sort by creation time (oldest first for comments)
        activity_comments.sort(key=lambda x: x.created_at)
        
        # Apply pagination
        paginated_comments = activity_comments[skip:skip + limit]
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(paginated_comments)} comments",
            data=paginated_comments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comments"
        )


# Activity Feed Settings

@router.get("/settings", response_model=BaseResponse[ActivityFeedSettings])
async def get_feed_settings(
    current_user = Depends(get_current_user)
):
    """Get user's activity feed settings."""
    try:
        settings = await activity_feed_service.get_user_settings(current_user.id)
        
        if not settings:
            # Create default settings
            settings = await activity_feed_service.create_default_settings(current_user.id)
        
        return BaseResponse(
            success=True,
            message="Retrieved activity feed settings",
            data=settings
        )
        
    except Exception as e:
        logger.error(f"Error getting feed settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feed settings"
        )


@router.patch("/settings", response_model=BaseResponse[ActivityFeedSettings])
async def update_feed_settings(
    settings_update: ActivityFeedSettingsUpdate,
    current_user = Depends(get_current_user)
):
    """Update user's activity feed settings."""
    try:
        settings = await activity_feed_service.update_user_settings(
            user_id=current_user.id,
            settings_update=settings_update
        )
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Settings not found"
            )
        
        return BaseResponse(
            success=True,
            message="Activity feed settings updated successfully",
            data=settings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feed settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feed settings"
        )


# Activity Statistics

@router.get("/stats", response_model=BaseResponse[ActivityStats])
async def get_activity_stats(
    current_user = Depends(get_current_user)
):
    """Get comprehensive activity statistics for the current user."""
    try:
        stats = await activity_feed_service.get_user_activity_stats(current_user.id)
        
        return BaseResponse(
            success=True,
            message="Retrieved activity statistics",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting activity stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity statistics"
        )


# Milestone Activities

@router.get("/milestones", response_model=BaseResponse[List[ActivityFeedItem]])
async def get_milestone_activities(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user = Depends(get_current_user)
):
    """Get milestone activities for the user and their friends."""
    try:
        # Create filter for milestone activities
        date_from = datetime.utcnow() - timedelta(days=days)
        filter_options = ActivityFeedFilter(
            is_milestone=True,
            date_from=date_from
        )
        
        feed_response = await activity_feed_service.get_user_feed(
            user_id=current_user.id,
            filter_options=filter_options,
            skip=0,
            limit=100  # Get more milestones
        )
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(feed_response.activities)} milestone activities",
            data=feed_response.activities
        )
        
    except Exception as e:
        logger.error(f"Error getting milestone activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve milestone activities"
        )


# Friend Activities

@router.get("/friends", response_model=BaseResponse[ActivityFeedResponse])
async def get_friend_activities(
    friend_ids: Optional[List[int]] = Query(None, description="Specific friend IDs to filter"),
    activity_types: Optional[List[ActivityType]] = Query(None, description="Filter by activity types"),
    skip: int = Query(0, ge=0, description="Number of activities to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activities to return"),
    current_user = Depends(get_current_user)
):
    """Get activities from friends only."""
    try:
        # Get user's friends
        from app.services.friend_service import friend_service
        friends_response = await friend_service.get_friends(current_user.id, skip=0, limit=1000)
        friend_user_ids = [f.user_id for f in friends_response.friends]
        
        # Filter by specific friends if provided
        if friend_ids:
            friend_user_ids = [uid for uid in friend_user_ids if uid in friend_ids]
        
        # Create filter options
        filter_options = ActivityFeedFilter(
            user_ids=friend_user_ids,
            activity_types=activity_types
        )
        
        feed_response = await activity_feed_service.get_user_feed(
            user_id=current_user.id,
            filter_options=filter_options,
            skip=skip,
            limit=limit
        )
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(feed_response.activities)} friend activities",
            data=feed_response
        )
        
    except Exception as e:
        logger.error(f"Error getting friend activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve friend activities"
        )


# Activity Discovery

@router.get("/trending", response_model=BaseResponse[List[ActivityFeedItem]])
async def get_trending_activities(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back for trending"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of trending activities"),
    current_user = Depends(get_current_user)
):
    """Get trending activities based on engagement."""
    try:
        # Get recent activities with high engagement
        date_from = datetime.utcnow() - timedelta(hours=hours)
        filter_options = ActivityFeedFilter(
            date_from=date_from,
            has_engagement=True
        )
        
        feed_response = await activity_feed_service.get_user_feed(
            user_id=current_user.id,
            filter_options=filter_options,
            skip=0,
            limit=100  # Get more to sort by engagement
        )
        
        # Sort by engagement (likes + comments)
        trending_activities = sorted(
            feed_response.activities,
            key=lambda x: x.likes_count + x.comments_count,
            reverse=True
        )[:limit]
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(trending_activities)} trending activities",
            data=trending_activities
        )
        
    except Exception as e:
        logger.error(f"Error getting trending activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trending activities"
        )


# Activity Management

@router.patch("/{activity_id}", response_model=BaseResponse[ActivityFeedItem])
async def update_activity(
    activity_id: int,
    activity_update: ActivityUpdate,
    current_user = Depends(get_current_user)
):
    """Update an activity (only by the activity owner)."""
    try:
        # Load activities to check ownership
        activities = await activity_feed_service._load_activities()
        activity = next((a for a in activities if a['id'] == activity_id), None)
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if activity['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only update your own activities"
            )
        
        # Update activity
        update_dict = activity_update.dict(exclude_unset=True)
        activity.update(update_dict)
        activity['updated_at'] = datetime.utcnow().isoformat()
        
        # Save activities
        await activity_feed_service._save_activities(activities)
        
        return BaseResponse(
            success=True,
            message="Activity updated successfully",
            data=ActivityFeedItem(**activity)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update activity"
        )


@router.delete("/{activity_id}", response_model=BaseResponse[bool])
async def delete_activity(
    activity_id: int,
    current_user = Depends(get_current_user)
):
    """Delete an activity (only by the activity owner)."""
    try:
        # Load activities to check ownership
        activities = await activity_feed_service._load_activities()
        activity = next((a for a in activities if a['id'] == activity_id), None)
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        if activity['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete your own activities"
            )
        
        # Remove activity
        activities = [a for a in activities if a['id'] != activity_id]
        await activity_feed_service._save_activities(activities)
        
        # Also remove related engagements and comments
        engagements = await activity_feed_service._load_engagements()
        engagements = [e for e in engagements if e['activity_id'] != activity_id]
        await activity_feed_service._save_engagements(engagements)
        
        comments = await activity_feed_service._load_comments()
        comments = [c for c in comments if c['activity_id'] != activity_id]
        await activity_feed_service._save_comments(comments)
        
        return BaseResponse(
            success=True,
            message="Activity deleted successfully",
            data=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete activity"
        )


# Bulk Operations

@router.post("/bulk/engage", response_model=BaseResponse[Dict[str, int]])
async def bulk_engage_activities(
    engagements: List[Dict[str, Any]],  # List of {"activity_id": int, "engagement_type": str}
    current_user = Depends(get_current_user)
):
    """Engage with multiple activities at once."""
    try:
        if len(engagements) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot engage with more than 20 activities at once"
            )
        
        success_count = 0
        failed_count = 0
        
        for engagement_item in engagements:
            try:
                activity_id = engagement_item.get("activity_id")
                engagement_type = EngagementType(engagement_item.get("engagement_type"))
                
                engagement_data = ActivityEngagementCreate(engagement_type=engagement_type)
                
                result = await activity_feed_service.engage_with_activity(
                    user_id=current_user.id,
                    activity_id=activity_id,
                    engagement_data=engagement_data
                )
                
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
        
        result = {
            "successful": success_count,
            "failed": failed_count,
            "total": len(engagements)
        }
        
        return BaseResponse(
            success=True,
            message=f"Bulk engagement completed: {success_count} successful, {failed_count} failed",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk engage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk engagement"
        ) 