from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FriendshipStatus(str, Enum):
    """Status of friendship between users."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    DECLINED = "declined"


class FriendRequestType(str, Enum):
    """Type of friend request."""
    DIRECT = "direct"          # Direct friend request
    MUTUAL_FRIEND = "mutual_friend"  # Through mutual friends
    QR_CODE = "qr_code"       # Via QR code
    USERNAME = "username"      # Via username search
    EMAIL = "email"           # Via email invitation
    PHONE = "phone"           # Via phone number


class PrivacyLevel(str, Enum):
    """Privacy levels for sharing data with friends."""
    PUBLIC = "public"          # Visible to all friends
    CLOSE_FRIENDS = "close_friends"  # Only close friends
    PRIVATE = "private"        # Not visible to friends


class NotificationPreference(str, Enum):
    """Friend-related notification preferences."""
    ALL = "all"               # All friend notifications
    IMPORTANT = "important"    # Only important notifications
    NONE = "none"             # No friend notifications


class Friendship(BaseModel):
    """Model representing a friendship between two users."""
    id: Optional[int] = Field(None, description="Friendship ID")
    user_id: int = Field(..., description="User who initiated the friendship")
    friend_id: int = Field(..., description="User who received the friendship")
    status: FriendshipStatus = Field(..., description="Current status of friendship")
    request_type: FriendRequestType = Field(FriendRequestType.DIRECT, description="How the friendship was initiated")
    
    # Timestamps
    requested_at: datetime = Field(default_factory=datetime.utcnow, description="When friendship was requested")
    responded_at: Optional[datetime] = Field(None, description="When friendship was accepted/declined")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction between friends")
    
    # Friendship details
    is_close_friend: bool = Field(False, description="Whether this is marked as a close friend")
    is_favorite: bool = Field(False, description="Whether this friend is favorited")
    nickname: Optional[str] = Field(None, max_length=50, description="Custom nickname for this friend")
    notes: Optional[str] = Field(None, max_length=500, description="Private notes about this friend")
    
    # Privacy and sharing
    can_see_water_logs: bool = Field(True, description="Can see water consumption logs")
    can_see_health_goals: bool = Field(True, description="Can see health goals and progress")
    can_see_achievements: bool = Field(True, description="Can see achievements")
    can_see_activity: bool = Field(True, description="Can see general activity")
    
    # Interaction stats
    total_interactions: int = Field(0, description="Total number of interactions")
    shared_challenges: int = Field(0, description="Number of shared challenges")
    mutual_friends: int = Field(0, description="Number of mutual friends")
    
    # Metadata
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class FriendRequest(BaseModel):
    """Model for friend request creation."""
    friend_username: Optional[str] = Field(None, description="Username of user to befriend")
    friend_email: Optional[str] = Field(None, description="Email of user to befriend")
    friend_id: Optional[int] = Field(None, description="Direct user ID")
    request_type: FriendRequestType = Field(FriendRequestType.DIRECT, description="Type of friend request")
    message: Optional[str] = Field(None, max_length=200, description="Optional message with request")
    
    @validator('friend_username', 'friend_email', 'friend_id')
    def at_least_one_identifier(cls, v, values):
        """Ensure at least one way to identify the friend is provided."""
        if not any([values.get('friend_username'), values.get('friend_email'), values.get('friend_id'), v]):
            raise ValueError('Must provide username, email, or user ID')
        return v


class FriendRequestResponse(BaseModel):
    """Model for responding to a friend request."""
    accept: bool = Field(..., description="Whether to accept the friend request")
    message: Optional[str] = Field(None, max_length=200, description="Optional response message")


class FriendUpdate(BaseModel):
    """Model for updating friendship settings."""
    is_close_friend: Optional[bool] = Field(None, description="Mark as close friend")
    is_favorite: Optional[bool] = Field(None, description="Mark as favorite")
    nickname: Optional[str] = Field(None, max_length=50, description="Custom nickname")
    notes: Optional[str] = Field(None, max_length=500, description="Private notes")
    can_see_water_logs: Optional[bool] = Field(None, description="Water logs visibility")
    can_see_health_goals: Optional[bool] = Field(None, description="Health goals visibility")
    can_see_achievements: Optional[bool] = Field(None, description="Achievements visibility")
    can_see_activity: Optional[bool] = Field(None, description="Activity visibility")


class FriendProfile(BaseModel):
    """Public profile information for a friend."""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    bio: Optional[str] = Field(None, description="User bio")
    
    # Friendship context
    friendship_id: int = Field(..., description="Friendship ID")
    friendship_status: FriendshipStatus = Field(..., description="Friendship status")
    is_close_friend: bool = Field(False, description="Is close friend")
    is_favorite: bool = Field(False, description="Is favorite")
    nickname: Optional[str] = Field(None, description="Custom nickname")
    
    # Activity info (if visible)
    last_seen: Optional[datetime] = Field(None, description="Last activity")
    current_streak: Optional[int] = Field(None, description="Current hydration streak")
    total_achievements: Optional[int] = Field(None, description="Total achievements")
    
    # Stats (if visible)
    weekly_goal_completion: Optional[float] = Field(None, description="Weekly goal completion rate")
    favorite_drink_type: Optional[str] = Field(None, description="Most consumed drink type")
    
    # Mutual connections
    mutual_friends_count: int = Field(0, description="Number of mutual friends")
    shared_challenges_count: int = Field(0, description="Number of shared challenges")


class FriendActivity(BaseModel):
    """Model representing friend activity for activity feed."""
    id: Optional[int] = Field(None, description="Activity ID")
    user_id: int = Field(..., description="User who performed the activity")
    friend_id: int = Field(..., description="Friend who can see this activity")
    
    # Activity details
    activity_type: str = Field(..., description="Type of activity")
    activity_data: Dict[str, Any] = Field(..., description="Activity-specific data")
    message: str = Field(..., description="Human-readable activity message")
    
    # Visibility and privacy
    privacy_level: PrivacyLevel = Field(PrivacyLevel.PUBLIC, description="Who can see this activity")
    is_milestone: bool = Field(False, description="Whether this is a milestone activity")
    
    # Engagement
    likes_count: int = Field(0, description="Number of likes")
    comments_count: int = Field(0, description="Number of comments")
    has_liked: bool = Field(False, description="Whether current user has liked")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When activity occurred")


class FriendSearchResult(BaseModel):
    """Model for friend search results."""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    
    # Relationship status
    friendship_status: Optional[FriendshipStatus] = Field(None, description="Current friendship status")
    is_friend: bool = Field(False, description="Whether already friends")
    has_pending_request: bool = Field(False, description="Whether there's a pending request")
    
    # Mutual connections
    mutual_friends_count: int = Field(0, description="Number of mutual friends")
    mutual_friends_preview: List[str] = Field(default_factory=list, description="Preview of mutual friend names")
    
    # Relevance
    search_score: float = Field(0.0, description="Search relevance score")
    suggested_reason: Optional[str] = Field(None, description="Why this user is suggested")


class FriendStats(BaseModel):
    """Statistics about user's friend network."""
    total_friends: int = Field(..., description="Total number of friends")
    close_friends: int = Field(..., description="Number of close friends")
    pending_requests_sent: int = Field(..., description="Pending requests sent")
    pending_requests_received: int = Field(..., description="Pending requests received")
    
    # Activity stats
    active_friends_this_week: int = Field(..., description="Friends active this week")
    shared_challenges_active: int = Field(..., description="Active shared challenges")
    total_interactions_this_month: int = Field(..., description="Total interactions this month")
    
    # Network analysis
    average_mutual_friends: float = Field(..., description="Average mutual friends per friend")
    most_connected_friend: Optional[str] = Field(None, description="Friend with most mutual connections")
    longest_friendship_days: int = Field(..., description="Longest friendship in days")


class FriendRecommendation(BaseModel):
    """Model for friend recommendations."""
    user_id: int = Field(..., description="Recommended user ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    
    # Recommendation details
    recommendation_score: float = Field(..., description="Recommendation strength (0-1)")
    recommendation_reasons: List[str] = Field(..., description="Why this user is recommended")
    
    # Connection info
    mutual_friends_count: int = Field(0, description="Number of mutual friends")
    mutual_friends_names: List[str] = Field(default_factory=list, description="Names of mutual friends")
    shared_interests: List[str] = Field(default_factory=list, description="Shared interests or activities")
    
    # Context
    connection_strength: str = Field(..., description="How strong the potential connection is")
    last_interaction: Optional[datetime] = Field(None, description="Last interaction if any")


class FriendNotificationSettings(BaseModel):
    """Notification settings for friend-related activities."""
    friend_requests: NotificationPreference = Field(NotificationPreference.ALL, description="Friend request notifications")
    friend_achievements: NotificationPreference = Field(NotificationPreference.IMPORTANT, description="Friend achievement notifications")
    friend_milestones: NotificationPreference = Field(NotificationPreference.ALL, description="Friend milestone notifications")
    challenge_invites: NotificationPreference = Field(NotificationPreference.ALL, description="Challenge invite notifications")
    activity_updates: NotificationPreference = Field(NotificationPreference.IMPORTANT, description="Activity update notifications")
    
    # Specific friend notifications
    close_friends_only: bool = Field(False, description="Only notify for close friends")
    quiet_hours_enabled: bool = Field(True, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field("22:00", description="Quiet hours start time")
    quiet_hours_end: Optional[str] = Field("08:00", description="Quiet hours end time")


class FriendListResponse(BaseModel):
    """Response model for friend list queries."""
    friends: List[FriendProfile] = Field(..., description="List of friends")
    total_count: int = Field(..., description="Total number of friends")
    close_friends_count: int = Field(..., description="Number of close friends")
    online_friends_count: int = Field(..., description="Number of currently online friends")
    
    # Pagination
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class MutualFriend(BaseModel):
    """Model representing mutual friends between users."""
    user_id: int = Field(..., description="Mutual friend user ID")
    username: str = Field(..., description="Mutual friend username")
    display_name: Optional[str] = Field(None, description="Mutual friend display name")
    avatar_url: Optional[str] = Field(None, description="Mutual friend avatar")
    friendship_duration_days: int = Field(..., description="How long they've been friends with both users") 