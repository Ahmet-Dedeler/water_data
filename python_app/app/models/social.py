from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    BLOCKED = "blocked"

class FriendRequest(BaseModel):
    id: int
    requester_id: int
    addressee_id: int
    status: FriendshipStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class FriendRequestCreate(BaseModel):
    addressee_id: int

class UserFollow(BaseModel):
    """Represents a follow relationship between two users."""
    follower_id: int = Field(..., description="The ID of the user who is following.")
    following_id: int = Field(..., description="The ID of the user who is being followed.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the follow relationship was created.")

    class Config:
        json_schema_extra = {
            "example": {
                "follower_id": 1,
                "following_id": 2,
                "created_at": "2023-10-27T10:00:00Z"
            }
        }

class Activity(BaseModel):
    """Represents an activity performed by a user, to be shown in a feed."""
    id: str = Field(..., description="A unique identifier for the activity.")
    user_id: int = Field(..., description="The ID of the user who performed the activity.")
    activity_type: Literal["water_log", "achievement", "followed_user"] = Field(..., description="The type of activity.")
    data: Dict[str, Any] = Field(..., description="Data associated with the activity, e.g., volume for water_log.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp of the activity.")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "some-unique-activity-id",
                "user_id": 1,
                "activity_type": "water_log",
                "data": {"volume": 1.5, "brand": "Fiji"},
                "created_at": "2023-10-28T12:00:00Z"
            }
        }

class FeedItem(BaseModel):
    id: int
    user_id: int
    username: str
    profile_picture_url: Optional[str]
    activity_type: str # e.g., 'new_achievement', 'friend_milestone'
    content: Dict[str, Any]
    created_at: datetime
    
class SocialFeed(BaseModel):
    items: List[FeedItem] 