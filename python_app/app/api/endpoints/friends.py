from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.models.friend import (
    Friendship, FriendRequest, FriendRequestResponse, FriendUpdate,
    FriendProfile, FriendSearchResult, FriendStats, FriendRecommendation,
    FriendListResponse, FriendshipStatus
)
from app.models.common import BaseResponse
from app.services.friend_service import friend_service
from app.api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Friend Request Management

@router.post("/requests", response_model=BaseResponse[Friendship])
async def send_friend_request(
    request_data: FriendRequest,
    current_user = Depends(get_current_user)
):
    """Send a friend request to another user."""
    try:
        friendship = await friend_service.send_friend_request(
            user_id=current_user.id,
            request_data=request_data
        )
        
        return BaseResponse(
            success=True,
            message="Friend request sent successfully",
            data=friendship
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending friend request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send friend request"
        )


@router.get("/requests", response_model=BaseResponse[List[Friendship]])
async def get_friend_requests(
    incoming: bool = Query(True, description="Get incoming (true) or outgoing (false) requests"),
    current_user = Depends(get_current_user)
):
    """Get pending friend requests for the current user."""
    try:
        requests = await friend_service.get_pending_friend_requests(
            user_id=current_user.id,
            incoming=incoming
        )
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {'incoming' if incoming else 'outgoing'} friend requests",
            data=requests
        )
        
    except Exception as e:
        logger.error(f"Error getting friend requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve friend requests"
        )


@router.post("/requests/{friendship_id}/respond", response_model=BaseResponse[Friendship])
async def respond_to_friend_request(
    friendship_id: int,
    response: FriendRequestResponse,
    current_user = Depends(get_current_user)
):
    """Accept or decline a friend request."""
    try:
        friendship = await friend_service.respond_to_friend_request(
            user_id=current_user.id,
            friendship_id=friendship_id,
            response=response
        )
        
        action = "accepted" if response.accept else "declined"
        return BaseResponse(
            success=True,
            message=f"Friend request {action} successfully",
            data=friendship
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error responding to friend request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to respond to friend request"
        )


# Friend Management

@router.get("/", response_model=BaseResponse[FriendListResponse])
async def get_friends(
    close_friends_only: bool = Query(False, description="Only return close friends"),
    online_only: bool = Query(False, description="Only return online friends"),
    skip: int = Query(0, ge=0, description="Number of friends to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of friends to return"),
    current_user = Depends(get_current_user)
):
    """Get the current user's friends list."""
    try:
        friends_response = await friend_service.get_friends(
            user_id=current_user.id,
            close_friends_only=close_friends_only,
            online_only=online_only,
            skip=skip,
            limit=limit
        )
        
        return BaseResponse(
            success=True,
            message="Retrieved friends list successfully",
            data=friends_response
        )
        
    except Exception as e:
        logger.error(f"Error getting friends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve friends"
        )


@router.patch("/{friendship_id}", response_model=BaseResponse[Friendship])
async def update_friendship(
    friendship_id: int,
    update_data: FriendUpdate,
    current_user = Depends(get_current_user)
):
    """Update friendship settings (nickname, privacy, etc.)."""
    try:
        friendship = await friend_service.update_friendship(
            user_id=current_user.id,
            friendship_id=friendship_id,
            update_data=update_data
        )
        
        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friendship not found"
            )
        
        return BaseResponse(
            success=True,
            message="Friendship updated successfully",
            data=friendship
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating friendship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update friendship"
        )


@router.delete("/{friendship_id}", response_model=BaseResponse[bool])
async def remove_friend(
    friendship_id: int,
    current_user = Depends(get_current_user)
):
    """Remove a friend (delete friendship)."""
    try:
        success = await friend_service.remove_friend(
            user_id=current_user.id,
            friendship_id=friendship_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friendship not found"
            )
        
        return BaseResponse(
            success=True,
            message="Friend removed successfully",
            data=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing friend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove friend"
        )


@router.post("/block/{user_id}", response_model=BaseResponse[bool])
async def block_user(
    user_id: int,
    current_user = Depends(get_current_user)
):
    """Block a user."""
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot block yourself"
            )
        
        success = await friend_service.block_user(
            user_id=current_user.id,
            target_user_id=user_id
        )
        
        return BaseResponse(
            success=True,
            message="User blocked successfully",
            data=success
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block user"
        )


# Friend Search and Discovery

@router.get("/search", response_model=BaseResponse[List[FriendSearchResult]])
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    current_user = Depends(get_current_user)
):
    """Search for users to potentially befriend."""
    try:
        search_results = await friend_service.search_users(
            user_id=current_user.id,
            query=q,
            limit=limit
        )
        
        return BaseResponse(
            success=True,
            message=f"Found {len(search_results)} users matching '{q}'",
            data=search_results
        )
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )


@router.get("/recommendations", response_model=BaseResponse[List[FriendRecommendation]])
async def get_friend_recommendations(
    limit: int = Query(10, ge=1, le=20, description="Maximum number of recommendations"),
    current_user = Depends(get_current_user)
):
    """Get friend recommendations for the current user."""
    try:
        recommendations = await friend_service.get_friend_recommendations(
            user_id=current_user.id,
            limit=limit
        )
        
        return BaseResponse(
            success=True,
            message=f"Generated {len(recommendations)} friend recommendations",
            data=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error getting friend recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get friend recommendations"
        )


# Friend Statistics

@router.get("/stats", response_model=BaseResponse[FriendStats])
async def get_friend_stats(
    current_user = Depends(get_current_user)
):
    """Get comprehensive friend statistics for the current user."""
    try:
        stats = await friend_service.get_friend_stats(current_user.id)
        
        return BaseResponse(
            success=True,
            message="Retrieved friend statistics successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting friend stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve friend statistics"
        )


# Friend Profile and Details

@router.get("/{friend_id}/profile", response_model=BaseResponse[FriendProfile])
async def get_friend_profile(
    friend_id: int,
    current_user = Depends(get_current_user)
):
    """Get detailed profile information for a specific friend."""
    try:
        # First, get the user's friends to verify friendship and get friendship details
        friends_response = await friend_service.get_friends(
            user_id=current_user.id,
            skip=0,
            limit=1000  # Get all friends to search
        )
        
        # Find the specific friend
        friend_profile = None
        for friend in friends_response.friends:
            if friend.user_id == friend_id:
                friend_profile = friend
                break
        
        if not friend_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend not found or not in your friends list"
            )
        
        return BaseResponse(
            success=True,
            message="Retrieved friend profile successfully",
            data=friend_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting friend profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve friend profile"
        )


# Bulk Operations

@router.post("/bulk/remove", response_model=BaseResponse[Dict[str, int]])
async def bulk_remove_friends(
    friendship_ids: List[int],
    current_user = Depends(get_current_user)
):
    """Remove multiple friends at once."""
    try:
        if len(friendship_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove more than 50 friends at once"
            )
        
        removed_count = 0
        failed_count = 0
        
        for friendship_id in friendship_ids:
            try:
                success = await friend_service.remove_friend(
                    user_id=current_user.id,
                    friendship_id=friendship_id
                )
                if success:
                    removed_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
        
        result = {
            "removed": removed_count,
            "failed": failed_count,
            "total": len(friendship_ids)
        }
        
        return BaseResponse(
            success=True,
            message=f"Bulk remove completed: {removed_count} removed, {failed_count} failed",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk remove: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk remove"
        )


@router.patch("/bulk/update", response_model=BaseResponse[Dict[str, int]])
async def bulk_update_friendships(
    updates: List[Dict[str, Any]],  # List of {"friendship_id": int, "updates": FriendUpdate}
    current_user = Depends(get_current_user)
):
    """Update multiple friendships at once."""
    try:
        if len(updates) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update more than 50 friendships at once"
            )
        
        updated_count = 0
        failed_count = 0
        
        for update_item in updates:
            try:
                friendship_id = update_item.get("friendship_id")
                update_data = FriendUpdate(**update_item.get("updates", {}))
                
                friendship = await friend_service.update_friendship(
                    user_id=current_user.id,
                    friendship_id=friendship_id,
                    update_data=update_data
                )
                
                if friendship:
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
        
        result = {
            "updated": updated_count,
            "failed": failed_count,
            "total": len(updates)
        }
        
        return BaseResponse(
            success=True,
            message=f"Bulk update completed: {updated_count} updated, {failed_count} failed",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk update"
        )


# Friend List Filtering

@router.get("/filter/close", response_model=BaseResponse[List[FriendProfile]])
async def get_close_friends(
    current_user = Depends(get_current_user)
):
    """Get only close friends."""
    try:
        friends_response = await friend_service.get_friends(
            user_id=current_user.id,
            close_friends_only=True,
            skip=0,
            limit=1000
        )
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(friends_response.friends)} close friends",
            data=friends_response.friends
        )
        
    except Exception as e:
        logger.error(f"Error getting close friends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve close friends"
        )


@router.get("/filter/online", response_model=BaseResponse[List[FriendProfile]])
async def get_online_friends(
    current_user = Depends(get_current_user)
):
    """Get only online friends."""
    try:
        friends_response = await friend_service.get_friends(
            user_id=current_user.id,
            online_only=True,
            skip=0,
            limit=1000
        )
        
        return BaseResponse(
            success=True,
            message=f"Retrieved {len(friends_response.friends)} online friends",
            data=friends_response.friends
        )
        
    except Exception as e:
        logger.error(f"Error getting online friends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve online friends"
        )


# Friend Activity and Interactions

@router.post("/{friend_id}/interact", response_model=BaseResponse[bool])
async def record_friend_interaction(
    friend_id: int,
    interaction_type: str = Query(..., description="Type of interaction"),
    current_user = Depends(get_current_user)
):
    """Record an interaction with a friend (for analytics)."""
    try:
        # This would typically update interaction counters and last interaction time
        # For now, we'll just validate the friendship exists
        friends_response = await friend_service.get_friends(
            user_id=current_user.id,
            skip=0,
            limit=1000
        )
        
        friend_exists = any(f.user_id == friend_id for f in friends_response.friends)
        
        if not friend_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend not found"
            )
        
        # In a real implementation, this would:
        # 1. Update interaction count
        # 2. Update last interaction time
        # 3. Create activity record
        # 4. Update analytics
        
        logger.info(f"Recorded {interaction_type} interaction between user {current_user.id} and friend {friend_id}")
        
        return BaseResponse(
            success=True,
            message="Interaction recorded successfully",
            data=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording friend interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record interaction"
        )


# Export friend data

@router.get("/export", response_model=BaseResponse[Dict[str, Any]])
async def export_friend_data(
    current_user = Depends(get_current_user)
):
    """Export user's friend data for backup or transfer."""
    try:
        # Get all friend data
        friends_response = await friend_service.get_friends(
            user_id=current_user.id,
            skip=0,
            limit=10000  # Get all friends
        )
        
        stats = await friend_service.get_friend_stats(current_user.id)
        
        export_data = {
            "user_id": current_user.id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "friends": [friend.dict() for friend in friends_response.friends],
            "statistics": stats.dict(),
            "total_friends": friends_response.total_count,
            "close_friends_count": friends_response.close_friends_count
        }
        
        return BaseResponse(
            success=True,
            message="Friend data exported successfully",
            data=export_data
        )
        
    except Exception as e:
        logger.error(f"Error exporting friend data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export friend data"
        ) 