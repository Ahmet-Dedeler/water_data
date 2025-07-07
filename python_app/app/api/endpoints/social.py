from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict
from sqlalchemy.orm import Session

from app.models import BaseResponse
from app.models.social import UserFollow, Activity, FriendRequest, FriendRequestCreate, FriendshipStatus, SocialFeed, FeedItem
from app.models.user import User
from app.services.social_service import social_service
from app.core.auth import get_current_active_user
from app.core.database import get_db

router = APIRouter()

@router.post(
    "/follow/{user_id}",
    response_model=BaseResponse[UserFollow],
    status_code=status.HTTP_201_CREATED,
    summary="Follow a user",
    description="Makes the current user follow another user specified by user_id.",
    responses={404: {"description": "User to follow not found"}, 400: {"description": "User cannot follow themselves or is already following"}},
)
async def follow_user(user_id: int, current_user: dict = Depends(get_current_active_user)):
    """Follow a user."""
    try:
        follower_id = current_user["user_id"]
        follow_relationship = await social_service.follow_user(follower_id, user_id)
        if not follow_relationship:
            raise HTTPException(status_code=404, detail="User to follow not found.")
        
        return BaseResponse(
            data=follow_relationship,
            message="User followed successfully."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/unfollow/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a user",
    description="Makes the current user unfollow another user specified by user_id.",
    responses={404: {"description": "User to unfollow not found or not being followed"}},
)
async def unfollow_user(user_id: int, current_user: dict = Depends(get_current_active_user)):
    """Unfollow a user."""
    follower_id = current_user["user_id"]
    success = await social_service.unfollow_user(follower_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User to unfollow not found or not being followed.")
    
    return BaseResponse(
        data={"success": True},
        message="User unfollowed successfully."
    )


@router.get("/feed", response_model=BaseResponse[List[Activity]])
async def get_my_feed(
    current_user: dict = Depends(get_current_active_user),
    limit: int = Query(50, ge=1, le=200, description="Number of activities to return")
):
    """Get the current user's personalized activity feed."""
    user_id = current_user["user_id"]
    feed = await social_service.get_user_activity_feed(user_id, limit)
    return BaseResponse(
        data=feed,
        message="Activity feed retrieved successfully."
    )


@router.get(
    "/followers",
    response_model=BaseResponse[List[UserFollow]],
    summary="Get user's followers",
    description="Retrieves a list of users who are following the current user.",
)
async def get_user_followers(user_id: int):
    """Get a list of followers for a user."""
    followers = await social_service.get_followers(user_id)
    return BaseResponse(
        data=followers,
        message="Followers retrieved successfully."
    )


@router.get(
    "/following",
    response_model=BaseResponse[List[UserFollow]],
    summary="Get users the user is following",
    description="Retrieves a list of users that the current user is following.",
)
async def get_user_following(user_id: int):
    """Get a list of users a user is following."""
    following = await social_service.get_following(user_id)
    return BaseResponse(
        data=following,
        message="Following list retrieved successfully."
    )


@router.get("/{user_id}/follow-counts", response_model=BaseResponse[Dict[str, int]])
async def get_user_follow_counts(user_id: int):
    """Get follower and following counts for a user."""
    counts = await social_service.get_follow_counts(user_id)
    return BaseResponse(
        data=counts,
        message="Follow counts retrieved successfully."
    )

@router.post(
    "/friends/requests",
    response_model=FriendRequest,
    status_code=status.HTTP_201_CREATED,
    summary="Send a friend request",
    description="Sends a friend request from the current user to another user.",
    responses={404: {"description": "Recipient not found"}, 400: {"description": "Invalid friend request"}},
)
def send_friend_request(
    request_data: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        return social_service.send_friend_request(db, current_user.id, request_data.addressee_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put(
    "/friends/requests/{request_id}",
    response_model=FriendRequest,
    summary="Respond to a friend request",
    description="Accept or decline a pending friend request. Must be the recipient of the request.",
    responses={404: {"description": "Friend request not found"}, 403: {"description": "Not authorized to respond to this request"}},
)
def respond_to_friend_request(
    request_id: int,
    status: FriendshipStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if status not in [FriendshipStatus.ACCEPTED, FriendshipStatus.DECLINED]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'accepted' or 'declined'.")
    try:
        return social_service.respond_to_friend_request(db, request_id, current_user.id, status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/friends/requests", response_model=List[FriendRequest])
def get_friend_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return social_service.get_friend_requests(db, current_user.id)

@router.get(
    "/friends",
    response_model=List[User],
    summary="Get user's friends",
    description="Retrieves a list of users who are friends with the current user (mutual followers).",
)
def get_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return social_service.get_friends(db, current_user.id)

@router.get(
    "/feed",
    response_model=SocialFeed,
    summary="Get social feed",
    description="Retrieves the social feed for the current user, showing recent activities from friends.",
)
def get_social_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current user's social feed, showing recent activity from friends.
    """
    feed_data = social_service.get_social_feed(db, current_user.id, limit)
    items = [FeedItem(**item) for item in feed_data]
    return SocialFeed(items=items) 