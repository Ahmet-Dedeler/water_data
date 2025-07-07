from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    """Types of activities that can appear in the feed."""
    # Water logging activities
    WATER_LOGGED = "water_logged"
    DAILY_GOAL_REACHED = "daily_goal_reached"
    WEEKLY_GOAL_REACHED = "weekly_goal_reached"
    HYDRATION_STREAK = "hydration_streak"
    
    # Achievement activities
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    MILESTONE_REACHED = "milestone_reached"
    LEVEL_UP = "level_up"
    BADGE_EARNED = "badge_earned"
    
    # Social activities
    FRIEND_ADDED = "friend_added"
    CHALLENGE_JOINED = "challenge_joined"
    CHALLENGE_COMPLETED = "challenge_completed"
    CHALLENGE_WON = "challenge_won"
    
    # Health activities
    HEALTH_GOAL_SET = "health_goal_set"
    HEALTH_GOAL_ACHIEVED = "health_goal_achieved"
    WORKOUT_LOGGED = "workout_logged"
    
    # Drink activities
    NEW_DRINK_TRIED = "new_drink_tried"
    FAVORITE_DRINK_UPDATED = "favorite_drink_updated"
    CAFFEINE_LIMIT_REACHED = "caffeine_limit_reached"
    
    # Profile activities
    PROFILE_UPDATED = "profile_updated"
    AVATAR_CHANGED = "avatar_changed"
    
    # System activities
    APP_ANNIVERSARY = "app_anniversary"
    SPECIAL_EVENT = "special_event"


class ActivityPriority(str, Enum):
    """Priority levels for activities."""
    LOW = "low"           # Minor updates, profile changes
    NORMAL = "normal"     # Regular activities, daily goals
    HIGH = "high"         # Achievements, milestones
    URGENT = "urgent"     # Major milestones, special events


class ActivityVisibility(str, Enum):
    """Visibility levels for activities."""
    PUBLIC = "public"           # Visible to all friends
    FRIENDS = "friends"         # Visible to friends only
    CLOSE_FRIENDS = "close_friends"  # Visible to close friends only
    PRIVATE = "private"         # Not visible to others


class EngagementType(str, Enum):
    """Types of engagement with activities."""
    LIKE = "like"
    LOVE = "love"
    CELEBRATE = "celebrate"
    ENCOURAGE = "encourage"
    AMAZING = "amazing"


class ActivityFeedItem(BaseModel):
    """Core model for activity feed items."""
    id: Optional[int] = Field(None, description="Activity ID")
    user_id: int = Field(..., description="User who performed the activity")
    activity_type: ActivityType = Field(..., description="Type of activity")
    
    # Content
    title: str = Field(..., max_length=200, description="Activity title")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description")
    activity_data: Dict[str, Any] = Field(default_factory=dict, description="Activity-specific data")
    
    # Metadata
    priority: ActivityPriority = Field(ActivityPriority.NORMAL, description="Activity priority")
    visibility: ActivityVisibility = Field(ActivityVisibility.FRIENDS, description="Who can see this activity")
    is_milestone: bool = Field(False, description="Whether this is a milestone activity")
    
    # Media
    image_url: Optional[str] = Field(None, description="Activity image URL")
    icon: Optional[str] = Field(None, description="Activity icon")
    
    # Engagement
    likes_count: int = Field(0, description="Number of likes")
    comments_count: int = Field(0, description="Number of comments")
    engagements: Dict[str, int] = Field(default_factory=dict, description="Engagement counts by type")
    
    # User context (filled when retrieving for specific user)
    has_liked: bool = Field(False, description="Whether current user has liked")
    has_commented: bool = Field(False, description="Whether current user has commented")
    user_engagement: Optional[EngagementType] = Field(None, description="Current user's engagement type")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When activity occurred")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    
    # Related data
    related_user_id: Optional[int] = Field(None, description="Related user (for friend activities)")
    related_object_id: Optional[int] = Field(None, description="Related object ID")
    related_object_type: Optional[str] = Field(None, description="Related object type")


class ActivityEngagement(BaseModel):
    """Model for user engagement with activities."""
    id: Optional[int] = Field(None, description="Engagement ID")
    activity_id: int = Field(..., description="Activity ID")
    user_id: int = Field(..., description="User who engaged")
    engagement_type: EngagementType = Field(..., description="Type of engagement")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When engagement occurred")


class ActivityComment(BaseModel):
    """Model for comments on activities."""
    id: Optional[int] = Field(None, description="Comment ID")
    activity_id: int = Field(..., description="Activity ID")
    user_id: int = Field(..., description="User who commented")
    content: str = Field(..., max_length=500, description="Comment content")
    
    # Engagement on comments
    likes_count: int = Field(0, description="Number of likes on comment")
    has_liked: bool = Field(False, description="Whether current user liked this comment")
    
    # Threading
    parent_comment_id: Optional[int] = Field(None, description="Parent comment for replies")
    replies_count: int = Field(0, description="Number of replies")
    
    # Metadata
    is_edited: bool = Field(False, description="Whether comment was edited")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When comment was created")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class ActivityFeedFilter(BaseModel):
    """Filter options for activity feed."""
    activity_types: Optional[List[ActivityType]] = Field(None, description="Filter by activity types")
    user_ids: Optional[List[int]] = Field(None, description="Filter by specific users")
    priority: Optional[ActivityPriority] = Field(None, description="Filter by priority")
    is_milestone: Optional[bool] = Field(None, description="Filter milestone activities")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    has_engagement: Optional[bool] = Field(None, description="Filter activities with engagement")


class ActivityFeedResponse(BaseModel):
    """Response model for activity feed queries."""
    activities: List[ActivityFeedItem] = Field(..., description="List of activities")
    total_count: int = Field(..., description="Total number of activities")
    unread_count: int = Field(0, description="Number of unread activities")
    
    # Pagination
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    
    # Context
    last_read_at: Optional[datetime] = Field(None, description="When user last read the feed")


class ActivityCreate(BaseModel):
    """Model for creating new activities."""
    activity_type: ActivityType = Field(..., description="Type of activity")
    title: str = Field(..., max_length=200, description="Activity title")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description")
    activity_data: Dict[str, Any] = Field(default_factory=dict, description="Activity-specific data")
    priority: ActivityPriority = Field(ActivityPriority.NORMAL, description="Activity priority")
    visibility: ActivityVisibility = Field(ActivityVisibility.FRIENDS, description="Who can see this activity")
    is_milestone: bool = Field(False, description="Whether this is a milestone activity")
    image_url: Optional[str] = Field(None, description="Activity image URL")
    icon: Optional[str] = Field(None, description="Activity icon")
    related_user_id: Optional[int] = Field(None, description="Related user ID")
    related_object_id: Optional[int] = Field(None, description="Related object ID")
    related_object_type: Optional[str] = Field(None, description="Related object type")


class ActivityUpdate(BaseModel):
    """Model for updating activities."""
    title: Optional[str] = Field(None, max_length=200, description="Activity title")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description")
    visibility: Optional[ActivityVisibility] = Field(None, description="Who can see this activity")
    image_url: Optional[str] = Field(None, description="Activity image URL")


class ActivityEngagementCreate(BaseModel):
    """Model for creating activity engagement."""
    engagement_type: EngagementType = Field(..., description="Type of engagement")


class ActivityCommentCreate(BaseModel):
    """Model for creating comments."""
    content: str = Field(..., max_length=500, description="Comment content")
    parent_comment_id: Optional[int] = Field(None, description="Parent comment for replies")


class ActivityCommentUpdate(BaseModel):
    """Model for updating comments."""
    content: str = Field(..., max_length=500, description="Updated comment content")


class ActivityNotification(BaseModel):
    """Model for activity-related notifications."""
    id: Optional[int] = Field(None, description="Notification ID")
    user_id: int = Field(..., description="User to notify")
    activity_id: int = Field(..., description="Related activity")
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    is_read: bool = Field(False, description="Whether notification is read")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When notification was created")


class ActivityStats(BaseModel):
    """Statistics about user's activity feed engagement."""
    total_activities: int = Field(..., description="Total activities posted")
    total_engagements_received: int = Field(..., description="Total engagements received")
    total_comments_received: int = Field(..., description="Total comments received")
    total_engagements_given: int = Field(..., description="Total engagements given")
    total_comments_given: int = Field(..., description="Total comments given")
    
    # Activity breakdown
    activities_by_type: Dict[str, int] = Field(default_factory=dict, description="Activity count by type")
    most_engaged_activity_type: Optional[str] = Field(None, description="Activity type with most engagement")
    
    # Time-based stats
    activities_this_week: int = Field(..., description="Activities this week")
    activities_this_month: int = Field(..., description="Activities this month")
    average_engagements_per_activity: float = Field(..., description="Average engagements per activity")
    
    # Social stats
    most_active_friend: Optional[str] = Field(None, description="Friend who engages most")
    most_supportive_friend: Optional[str] = Field(None, description="Friend who comments most")


class ActivityUserProfile(BaseModel):
    """User profile information for activity feed context."""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_friend: bool = Field(False, description="Whether user is a friend")
    is_close_friend: bool = Field(False, description="Whether user is a close friend")
    friendship_duration_days: Optional[int] = Field(None, description="Days since friendship")


class ActivityFeedSettings(BaseModel):
    """User settings for activity feed."""
    id: Optional[int] = Field(None, description="Settings ID")
    user_id: int = Field(..., description="User ID")
    
    # Visibility settings
    default_visibility: ActivityVisibility = Field(ActivityVisibility.FRIENDS, description="Default activity visibility")
    auto_share_achievements: bool = Field(True, description="Auto-share achievements")
    auto_share_milestones: bool = Field(True, description="Auto-share milestones")
    auto_share_goals: bool = Field(False, description="Auto-share goal completions")
    
    # Feed preferences
    show_friend_achievements: bool = Field(True, description="Show friend achievements")
    show_friend_milestones: bool = Field(True, description="Show friend milestones")
    show_friend_daily_activities: bool = Field(True, description="Show friend daily activities")
    show_system_activities: bool = Field(False, description="Show system activities")
    
    # Notification preferences
    notify_on_engagement: bool = Field(True, description="Notify when someone engages with activities")
    notify_on_comments: bool = Field(True, description="Notify when someone comments")
    notify_on_friend_milestones: bool = Field(True, description="Notify on friend milestones")
    
    # Advanced settings
    feed_refresh_interval: int = Field(300, description="Feed refresh interval in seconds")
    max_activities_per_load: int = Field(20, description="Maximum activities to load at once")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Settings created")
    updated_at: Optional[datetime] = Field(None, description="Last settings update")


class ActivityFeedSettingsUpdate(BaseModel):
    """Model for updating activity feed settings."""
    default_visibility: Optional[ActivityVisibility] = Field(None, description="Default activity visibility")
    auto_share_achievements: Optional[bool] = Field(None, description="Auto-share achievements")
    auto_share_milestones: Optional[bool] = Field(None, description="Auto-share milestones")
    auto_share_goals: Optional[bool] = Field(None, description="Auto-share goal completions")
    show_friend_achievements: Optional[bool] = Field(None, description="Show friend achievements")
    show_friend_milestones: Optional[bool] = Field(None, description="Show friend milestones")
    show_friend_daily_activities: Optional[bool] = Field(None, description="Show friend daily activities")
    show_system_activities: Optional[bool] = Field(None, description="Show system activities")
    notify_on_engagement: Optional[bool] = Field(None, description="Notify when someone engages")
    notify_on_comments: Optional[bool] = Field(None, description="Notify when someone comments")
    notify_on_friend_milestones: Optional[bool] = Field(None, description="Notify on friend milestones")
    feed_refresh_interval: Optional[int] = Field(None, description="Feed refresh interval in seconds")
    max_activities_per_load: Optional[int] = Field(None, description="Maximum activities to load at once")


class ActivityTemplate(BaseModel):
    """Template for generating activities automatically."""
    activity_type: ActivityType = Field(..., description="Activity type")
    title_template: str = Field(..., description="Title template with placeholders")
    description_template: Optional[str] = Field(None, description="Description template")
    default_visibility: ActivityVisibility = Field(ActivityVisibility.FRIENDS, description="Default visibility")
    default_priority: ActivityPriority = Field(ActivityPriority.NORMAL, description="Default priority")
    icon: Optional[str] = Field(None, description="Default icon")
    is_milestone_trigger: bool = Field(False, description="Whether this triggers milestone detection")


class ActivityDigest(BaseModel):
    """Daily/weekly digest of activities."""
    id: Optional[int] = Field(None, description="Digest ID")
    user_id: int = Field(..., description="User ID")
    digest_type: str = Field(..., description="Type of digest (daily/weekly)")
    period_start: datetime = Field(..., description="Digest period start")
    period_end: datetime = Field(..., description="Digest period end")
    
    # Content
    total_activities: int = Field(..., description="Total activities in period")
    milestone_activities: List[ActivityFeedItem] = Field(default_factory=list, description="Milestone activities")
    top_engaged_activities: List[ActivityFeedItem] = Field(default_factory=list, description="Most engaged activities")
    friend_highlights: List[ActivityFeedItem] = Field(default_factory=list, description="Friend activity highlights")
    
    # Stats
    total_engagements: int = Field(..., description="Total engagements in period")
    new_friends: int = Field(..., description="New friends added")
    achievements_unlocked: int = Field(..., description="Achievements unlocked")
    
    # Metadata
    is_sent: bool = Field(False, description="Whether digest was sent")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Digest creation time") 