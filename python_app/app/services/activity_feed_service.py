import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import asyncio

from app.models.activity_feed import (
    ActivityFeedItem, ActivityEngagement, ActivityComment, ActivityFeedFilter,
    ActivityFeedResponse, ActivityCreate, ActivityUpdate, ActivityEngagementCreate,
    ActivityCommentCreate, ActivityCommentUpdate, ActivityNotification, ActivityStats,
    ActivityUserProfile, ActivityFeedSettings, ActivityFeedSettingsUpdate,
    ActivityTemplate, ActivityDigest, ActivityType, ActivityPriority,
    ActivityVisibility, EngagementType
)
from app.models.common import BaseResponse
from app.services.friend_service import friend_service
from app.services.user_service import user_service

logger = logging.getLogger(__name__)


class ActivityFeedService:
    """Comprehensive activity feed service for real-time social updates."""
    
    def __init__(self):
        self.activities_file = Path(__file__).parent.parent / "data" / "activity_feed.json"
        self.engagements_file = Path(__file__).parent.parent / "data" / "activity_engagements.json"
        self.comments_file = Path(__file__).parent.parent / "data" / "activity_comments.json"
        self.settings_file = Path(__file__).parent.parent / "data" / "activity_feed_settings.json"
        self.templates_file = Path(__file__).parent.parent / "data" / "activity_templates.json"
        self._ensure_data_files()
        self._activities_cache = None
        self._engagements_cache = None
        self._comments_cache = None
        self._settings_cache = None
        self._templates_cache = None
        self._next_activity_id = 1
        self._next_engagement_id = 1
        self._next_comment_id = 1
    
    def _ensure_data_files(self):
        """Ensure activity feed data files exist."""
        data_dir = self.activities_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [
            self.activities_file, self.engagements_file, self.comments_file,
            self.settings_file, self.templates_file
        ]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_activities(self) -> List[Dict]:
        """Load activities from file."""
        if self._activities_cache is None:
            try:
                with open(self.activities_file, 'r') as f:
                    self._activities_cache = json.load(f)
                    
                # Update next ID
                if self._activities_cache:
                    self._next_activity_id = max(a['id'] for a in self._activities_cache) + 1
            except Exception as e:
                logger.error(f"Error loading activities: {e}")
                self._activities_cache = []
        return self._activities_cache
    
    async def _save_activities(self, activities: List[Dict]):
        """Save activities to file."""
        try:
            with open(self.activities_file, 'w') as f:
                json.dump(activities, f, indent=2, default=str)
            self._activities_cache = activities
        except Exception as e:
            logger.error(f"Error saving activities: {e}")
            raise
    
    async def _load_engagements(self) -> List[Dict]:
        """Load engagements from file."""
        if self._engagements_cache is None:
            try:
                with open(self.engagements_file, 'r') as f:
                    self._engagements_cache = json.load(f)
                    
                # Update next ID
                if self._engagements_cache:
                    self._next_engagement_id = max(e['id'] for e in self._engagements_cache) + 1
            except Exception as e:
                logger.error(f"Error loading engagements: {e}")
                self._engagements_cache = []
        return self._engagements_cache
    
    async def _save_engagements(self, engagements: List[Dict]):
        """Save engagements to file."""
        try:
            with open(self.engagements_file, 'w') as f:
                json.dump(engagements, f, indent=2, default=str)
            self._engagements_cache = engagements
        except Exception as e:
            logger.error(f"Error saving engagements: {e}")
            raise
    
    async def _load_comments(self) -> List[Dict]:
        """Load comments from file."""
        if self._comments_cache is None:
            try:
                with open(self.comments_file, 'r') as f:
                    self._comments_cache = json.load(f)
                    
                # Update next ID
                if self._comments_cache:
                    self._next_comment_id = max(c['id'] for c in self._comments_cache) + 1
            except Exception as e:
                logger.error(f"Error loading comments: {e}")
                self._comments_cache = []
        return self._comments_cache
    
    async def _save_comments(self, comments: List[Dict]):
        """Save comments to file."""
        try:
            with open(self.comments_file, 'w') as f:
                json.dump(comments, f, indent=2, default=str)
            self._comments_cache = comments
        except Exception as e:
            logger.error(f"Error saving comments: {e}")
            raise
    
    async def _load_settings(self) -> List[Dict]:
        """Load activity feed settings from file."""
        if self._settings_cache is None:
            try:
                with open(self.settings_file, 'r') as f:
                    self._settings_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                self._settings_cache = []
        return self._settings_cache
    
    async def _save_settings(self, settings: List[Dict]):
        """Save activity feed settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2, default=str)
            self._settings_cache = settings
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise
    
    async def _load_templates(self) -> List[Dict]:
        """Load activity templates from file."""
        if self._templates_cache is None:
            try:
                with open(self.templates_file, 'r') as f:
                    self._templates_cache = json.load(f)
                    
                # Initialize default templates if empty
                if not self._templates_cache:
                    await self._initialize_default_templates()
            except Exception as e:
                logger.error(f"Error loading templates: {e}")
                self._templates_cache = []
                await self._initialize_default_templates()
        return self._templates_cache
    
    async def _initialize_default_templates(self):
        """Initialize default activity templates."""
        default_templates = [
            {
                "activity_type": "daily_goal_reached",
                "title_template": "{username} reached their daily hydration goal! 💧",
                "description_template": "Completed {goal_amount}ml goal with {actual_amount}ml",
                "default_visibility": "friends",
                "default_priority": "normal",
                "icon": "🎯",
                "is_milestone_trigger": False
            },
            {
                "activity_type": "achievement_unlocked",
                "title_template": "{username} unlocked the '{achievement_name}' achievement! 🏆",
                "description_template": "{achievement_description}",
                "default_visibility": "friends",
                "default_priority": "high",
                "icon": "🏆",
                "is_milestone_trigger": True
            },
            {
                "activity_type": "hydration_streak",
                "title_template": "{username} is on a {streak_days}-day hydration streak! 🔥",
                "description_template": "Consistently meeting daily goals for {streak_days} days",
                "default_visibility": "friends",
                "default_priority": "high",
                "icon": "🔥",
                "is_milestone_trigger": True
            },
            {
                "activity_type": "friend_added",
                "title_template": "{username} and {friend_name} are now hydration buddies! 👥",
                "description_template": "Let's cheer them on their hydration journey!",
                "default_visibility": "friends",
                "default_priority": "normal",
                "icon": "👥",
                "is_milestone_trigger": False
            },
            {
                "activity_type": "challenge_completed",
                "title_template": "{username} completed the '{challenge_name}' challenge! 🎉",
                "description_template": "Finished in {completion_time} with {final_score} points",
                "default_visibility": "friends",
                "default_priority": "high",
                "icon": "🎉",
                "is_milestone_trigger": True
            }
        ]
        
        self._templates_cache = default_templates
        await self._save_templates(default_templates)
    
    async def _save_templates(self, templates: List[Dict]):
        """Save activity templates to file."""
        try:
            with open(self.templates_file, 'w') as f:
                json.dump(templates, f, indent=2, default=str)
            self._templates_cache = templates
        except Exception as e:
            logger.error(f"Error saving templates: {e}")
            raise
    
    # Activity Management
    
    async def create_activity(
        self,
        user_id: int,
        activity_data: ActivityCreate
    ) -> ActivityFeedItem:
        """Create a new activity in the feed."""
        try:
            activities = await self._load_activities()
            
            # Get user settings to check auto-sharing preferences
            settings = await self.get_user_settings(user_id)
            
            # Apply user's default visibility if not specified
            if not activity_data.visibility:
                activity_data.visibility = settings.default_visibility if settings else ActivityVisibility.FRIENDS
            
            activity_dict = {
                "id": self._next_activity_id,
                "user_id": user_id,
                "activity_type": activity_data.activity_type.value,
                "title": activity_data.title,
                "description": activity_data.description,
                "activity_data": activity_data.activity_data,
                "priority": activity_data.priority.value,
                "visibility": activity_data.visibility.value,
                "is_milestone": activity_data.is_milestone,
                "image_url": activity_data.image_url,
                "icon": activity_data.icon,
                "likes_count": 0,
                "comments_count": 0,
                "engagements": {},
                "has_liked": False,
                "has_commented": False,
                "user_engagement": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None,
                "related_user_id": activity_data.related_user_id,
                "related_object_id": activity_data.related_object_id,
                "related_object_type": activity_data.related_object_type
            }
            
            activities.append(activity_dict)
            await self._save_activities(activities)
            
            self._next_activity_id += 1
            
            # Send notifications to friends if appropriate
            await self._send_activity_notifications(activity_dict)
            
            logger.info(f"Created activity {activity_dict['id']} for user {user_id}")
            return ActivityFeedItem(**activity_dict)
            
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            raise
    
    async def create_activity_from_template(
        self,
        user_id: int,
        activity_type: ActivityType,
        template_data: Dict[str, Any]
    ) -> Optional[ActivityFeedItem]:
        """Create activity using a template."""
        try:
            templates = await self._load_templates()
            
            # Find template for activity type
            template = next((t for t in templates if t['activity_type'] == activity_type.value), None)
            if not template:
                logger.warning(f"No template found for activity type: {activity_type}")
                return None
            
            # Get user info for template formatting
            user = await user_service.get_user_by_id(user_id)
            if not user:
                return None
            
            # Format title and description
            format_data = {
                "username": user.username,
                "display_name": getattr(user, 'display_name', user.username),
                **template_data
            }
            
            title = template['title_template'].format(**format_data)
            description = None
            if template.get('description_template'):
                try:
                    description = template['description_template'].format(**format_data)
                except KeyError as e:
                    logger.warning(f"Missing template data for {e}, using partial description")
                    description = template['description_template']
            
            # Create activity
            activity_create = ActivityCreate(
                activity_type=activity_type,
                title=title,
                description=description,
                activity_data=template_data,
                priority=ActivityPriority(template['default_priority']),
                visibility=ActivityVisibility(template['default_visibility']),
                is_milestone=template.get('is_milestone_trigger', False),
                icon=template.get('icon')
            )
            
            return await self.create_activity(user_id, activity_create)
            
        except Exception as e:
            logger.error(f"Error creating activity from template: {e}")
            return None
    
    async def get_user_feed(
        self,
        user_id: int,
        filter_options: Optional[ActivityFeedFilter] = None,
        skip: int = 0,
        limit: int = 20
    ) -> ActivityFeedResponse:
        """Get personalized activity feed for a user."""
        try:
            activities = await self._load_activities()
            engagements = await self._load_engagements()
            comments = await self._load_comments()
            
            # Get user's friends to filter activities
            friends_response = await friend_service.get_friends(user_id, skip=0, limit=1000)
            friend_ids = {f.user_id for f in friends_response.friends}
            close_friend_ids = {f.user_id for f in friends_response.friends if f.is_close_friend}
            
            # Get user's feed settings
            settings = await self.get_user_settings(user_id)
            
            # Filter activities based on visibility and user preferences
            visible_activities = []
            for activity in activities:
                activity_user_id = activity['user_id']
                visibility = ActivityVisibility(activity['visibility'])
                
                # Check if user can see this activity
                can_see = False
                
                if activity_user_id == user_id:
                    # User's own activities
                    can_see = True
                elif visibility == ActivityVisibility.PUBLIC:
                    # Public activities (visible to all friends)
                    can_see = activity_user_id in friend_ids
                elif visibility == ActivityVisibility.FRIENDS:
                    # Friends-only activities
                    can_see = activity_user_id in friend_ids
                elif visibility == ActivityVisibility.CLOSE_FRIENDS:
                    # Close friends only
                    can_see = activity_user_id in close_friend_ids
                # PRIVATE activities are never visible to others
                
                if not can_see:
                    continue
                
                # Apply user's feed preferences
                activity_type = ActivityType(activity['activity_type'])
                if not self._should_show_activity(activity_type, settings):
                    continue
                
                # Apply additional filters
                if filter_options and not self._activity_matches_filter(activity, filter_options):
                    continue
                
                visible_activities.append(activity)
            
            # Sort by creation time (newest first) and priority
            visible_activities.sort(
                key=lambda x: (
                    x.get('priority') == ActivityPriority.URGENT.value,
                    x.get('priority') == ActivityPriority.HIGH.value,
                    x['created_at']
                ),
                reverse=True
            )
            
            # Apply pagination
            total_count = len(visible_activities)
            paginated_activities = visible_activities[skip:skip + limit]
            
            # Enrich activities with engagement data
            enriched_activities = []
            for activity in paginated_activities:
                enriched_activity = await self._enrich_activity_with_engagement(
                    activity, user_id, engagements, comments
                )
                enriched_activities.append(ActivityFeedItem(**enriched_activity))
            
            # Calculate unread count (simplified - would use last_read_at in real implementation)
            unread_count = len([a for a in visible_activities if a['user_id'] != user_id])
            
            return ActivityFeedResponse(
                activities=enriched_activities,
                total_count=total_count,
                unread_count=unread_count,
                page=skip // limit + 1,
                page_size=limit,
                has_next=skip + limit < total_count,
                last_read_at=datetime.utcnow()  # Would be stored per user
            )
            
        except Exception as e:
            logger.error(f"Error getting user feed: {e}")
            return ActivityFeedResponse(
                activities=[],
                total_count=0,
                unread_count=0,
                page=1,
                page_size=limit,
                has_next=False
            )
    
    def _should_show_activity(self, activity_type: ActivityType, settings: Optional[ActivityFeedSettings]) -> bool:
        """Check if activity should be shown based on user preferences."""
        if not settings:
            return True  # Default: show all
        
        # Check specific activity type preferences
        if activity_type in [ActivityType.ACHIEVEMENT_UNLOCKED, ActivityType.MILESTONE_REACHED, ActivityType.LEVEL_UP]:
            return settings.show_friend_achievements
        elif activity_type in [ActivityType.HYDRATION_STREAK, ActivityType.WEEKLY_GOAL_REACHED]:
            return settings.show_friend_milestones
        elif activity_type in [ActivityType.WATER_LOGGED, ActivityType.DAILY_GOAL_REACHED]:
            return settings.show_friend_daily_activities
        elif activity_type in [ActivityType.APP_ANNIVERSARY, ActivityType.SPECIAL_EVENT]:
            return settings.show_system_activities
        
        return True  # Default: show if not specifically filtered
    
    def _activity_matches_filter(self, activity: Dict, filter_options: ActivityFeedFilter) -> bool:
        """Check if activity matches the provided filters."""
        if filter_options.activity_types and ActivityType(activity['activity_type']) not in filter_options.activity_types:
            return False
        
        if filter_options.user_ids and activity['user_id'] not in filter_options.user_ids:
            return False
        
        if filter_options.priority and ActivityPriority(activity['priority']) != filter_options.priority:
            return False
        
        if filter_options.is_milestone is not None and activity['is_milestone'] != filter_options.is_milestone:
            return False
        
        if filter_options.date_from:
            activity_date = datetime.fromisoformat(activity['created_at'])
            if activity_date < filter_options.date_from:
                return False
        
        if filter_options.date_to:
            activity_date = datetime.fromisoformat(activity['created_at'])
            if activity_date > filter_options.date_to:
                return False
        
        if filter_options.has_engagement is not None:
            has_engagement = activity['likes_count'] > 0 or activity['comments_count'] > 0
            if has_engagement != filter_options.has_engagement:
                return False
        
        return True
    
    async def _enrich_activity_with_engagement(
        self,
        activity: Dict,
        user_id: int,
        engagements: List[Dict],
        comments: List[Dict]
    ) -> Dict:
        """Enrich activity with user-specific engagement data."""
        activity_id = activity['id']
        
        # Get engagements for this activity
        activity_engagements = [e for e in engagements if e['activity_id'] == activity_id]
        activity_comments = [c for c in comments if c['activity_id'] == activity_id]
        
        # Calculate engagement counts by type
        engagement_counts = defaultdict(int)
        for engagement in activity_engagements:
            engagement_counts[engagement['engagement_type']] += 1
        
        # Check user's engagement
        user_engagement = next((e for e in activity_engagements if e['user_id'] == user_id), None)
        user_commented = any(c['user_id'] == user_id for c in activity_comments)
        
        # Update activity with engagement data
        activity['engagements'] = dict(engagement_counts)
        activity['likes_count'] = engagement_counts.get('like', 0)
        activity['comments_count'] = len(activity_comments)
        activity['has_liked'] = user_engagement is not None
        activity['has_commented'] = user_commented
        activity['user_engagement'] = user_engagement['engagement_type'] if user_engagement else None
        
        return activity
    
    # Engagement Management
    
    async def engage_with_activity(
        self,
        user_id: int,
        activity_id: int,
        engagement_data: ActivityEngagementCreate
    ) -> Optional[ActivityEngagement]:
        """Add or update user's engagement with an activity."""
        try:
            activities = await self._load_activities()
            engagements = await self._load_engagements()
            
            # Find the activity
            activity = next((a for a in activities if a['id'] == activity_id), None)
            if not activity:
                raise ValueError("Activity not found")
            
            # Check if user can see this activity
            if not await self._can_user_see_activity(user_id, activity):
                raise ValueError("Activity not accessible")
            
            # Check if user already engaged
            existing_engagement = next((
                e for e in engagements
                if e['activity_id'] == activity_id and e['user_id'] == user_id
            ), None)
            
            if existing_engagement:
                # Update existing engagement
                existing_engagement['engagement_type'] = engagement_data.engagement_type.value
                existing_engagement['created_at'] = datetime.utcnow().isoformat()
            else:
                # Create new engagement
                engagement_dict = {
                    "id": self._next_engagement_id,
                    "activity_id": activity_id,
                    "user_id": user_id,
                    "engagement_type": engagement_data.engagement_type.value,
                    "created_at": datetime.utcnow().isoformat()
                }
                engagements.append(engagement_dict)
                self._next_engagement_id += 1
            
            await self._save_engagements(engagements)
            
            # Update activity engagement counts
            await self._update_activity_engagement_counts(activity_id)
            
            # Send notification to activity owner
            if activity['user_id'] != user_id:
                await self._send_engagement_notification(activity, user_id, engagement_data.engagement_type)
            
            logger.info(f"User {user_id} engaged with activity {activity_id}")
            return ActivityEngagement(**engagement_dict) if not existing_engagement else ActivityEngagement(**existing_engagement)
            
        except Exception as e:
            logger.error(f"Error engaging with activity: {e}")
            raise
    
    async def remove_engagement(self, user_id: int, activity_id: int) -> bool:
        """Remove user's engagement with an activity."""
        try:
            engagements = await self._load_engagements()
            
            # Find and remove the engagement
            original_count = len(engagements)
            engagements = [
                e for e in engagements
                if not (e['activity_id'] == activity_id and e['user_id'] == user_id)
            ]
            
            if len(engagements) == original_count:
                return False  # No engagement found
            
            await self._save_engagements(engagements)
            
            # Update activity engagement counts
            await self._update_activity_engagement_counts(activity_id)
            
            logger.info(f"Removed engagement from user {user_id} on activity {activity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing engagement: {e}")
            return False
    
    async def _update_activity_engagement_counts(self, activity_id: int):
        """Update engagement counts for an activity."""
        try:
            activities = await self._load_activities()
            engagements = await self._load_engagements()
            comments = await self._load_comments()
            
            # Find the activity
            activity_index = next((i for i, a in enumerate(activities) if a['id'] == activity_id), None)
            if activity_index is None:
                return
            
            # Count engagements
            activity_engagements = [e for e in engagements if e['activity_id'] == activity_id]
            activity_comments = [c for c in comments if c['activity_id'] == activity_id]
            
            engagement_counts = defaultdict(int)
            for engagement in activity_engagements:
                engagement_counts[engagement['engagement_type']] += 1
            
            # Update activity
            activities[activity_index]['engagements'] = dict(engagement_counts)
            activities[activity_index]['likes_count'] = engagement_counts.get('like', 0)
            activities[activity_index]['comments_count'] = len(activity_comments)
            activities[activity_index]['updated_at'] = datetime.utcnow().isoformat()
            
            await self._save_activities(activities)
            
        except Exception as e:
            logger.error(f"Error updating engagement counts: {e}")
    
    # Comment Management
    
    async def add_comment(
        self,
        user_id: int,
        activity_id: int,
        comment_data: ActivityCommentCreate
    ) -> Optional[ActivityComment]:
        """Add a comment to an activity."""
        try:
            activities = await self._load_activities()
            comments = await self._load_comments()
            
            # Find the activity
            activity = next((a for a in activities if a['id'] == activity_id), None)
            if not activity:
                raise ValueError("Activity not found")
            
            # Check if user can see this activity
            if not await self._can_user_see_activity(user_id, activity):
                raise ValueError("Activity not accessible")
            
            comment_dict = {
                "id": self._next_comment_id,
                "activity_id": activity_id,
                "user_id": user_id,
                "content": comment_data.content,
                "likes_count": 0,
                "has_liked": False,
                "parent_comment_id": comment_data.parent_comment_id,
                "replies_count": 0,
                "is_edited": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None
            }
            
            comments.append(comment_dict)
            await self._save_comments(comments)
            
            self._next_comment_id += 1
            
            # Update parent comment reply count if this is a reply
            if comment_data.parent_comment_id:
                await self._update_comment_reply_count(comment_data.parent_comment_id)
            
            # Update activity comment count
            await self._update_activity_engagement_counts(activity_id)
            
            # Send notification to activity owner and parent comment owner
            if activity['user_id'] != user_id:
                await self._send_comment_notification(activity, user_id, comment_data.content)
            
            logger.info(f"User {user_id} commented on activity {activity_id}")
            return ActivityComment(**comment_dict)
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            raise
    
    async def _update_comment_reply_count(self, parent_comment_id: int):
        """Update reply count for a parent comment."""
        try:
            comments = await self._load_comments()
            
            # Find parent comment
            parent_index = next((i for i, c in enumerate(comments) if c['id'] == parent_comment_id), None)
            if parent_index is None:
                return
            
            # Count replies
            reply_count = sum(1 for c in comments if c.get('parent_comment_id') == parent_comment_id)
            
            # Update parent comment
            comments[parent_index]['replies_count'] = reply_count
            comments[parent_index]['updated_at'] = datetime.utcnow().isoformat()
            
            await self._save_comments(comments)
            
        except Exception as e:
            logger.error(f"Error updating comment reply count: {e}")
    
    async def _can_user_see_activity(self, user_id: int, activity: Dict) -> bool:
        """Check if user can see a specific activity."""
        activity_user_id = activity['user_id']
        visibility = ActivityVisibility(activity['visibility'])
        
        if activity_user_id == user_id:
            return True  # User's own activity
        
        if visibility == ActivityVisibility.PRIVATE:
            return False  # Private activities not visible to others
        
        # Get friendship status
        friends_response = await friend_service.get_friends(user_id, skip=0, limit=1000)
        friend_ids = {f.user_id for f in friends_response.friends}
        close_friend_ids = {f.user_id for f in friends_response.friends if f.is_close_friend}
        
        if visibility == ActivityVisibility.PUBLIC:
            return activity_user_id in friend_ids
        elif visibility == ActivityVisibility.FRIENDS:
            return activity_user_id in friend_ids
        elif visibility == ActivityVisibility.CLOSE_FRIENDS:
            return activity_user_id in close_friend_ids
        
        return False
    
    # Settings Management
    
    async def get_user_settings(self, user_id: int) -> Optional[ActivityFeedSettings]:
        """Get user's activity feed settings."""
        try:
            settings_list = await self._load_settings()
            
            user_settings = next((s for s in settings_list if s['user_id'] == user_id), None)
            if not user_settings:
                # Create default settings
                return await self.create_default_settings(user_id)
            
            return ActivityFeedSettings(**user_settings)
            
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return None
    
    async def create_default_settings(self, user_id: int) -> ActivityFeedSettings:
        """Create default activity feed settings for a user."""
        try:
            settings_list = await self._load_settings()
            
            default_settings = {
                "user_id": user_id,
                "default_visibility": ActivityVisibility.FRIENDS.value,
                "auto_share_achievements": True,
                "auto_share_milestones": True,
                "auto_share_goals": False,
                "show_friend_achievements": True,
                "show_friend_milestones": True,
                "show_friend_daily_activities": True,
                "show_system_activities": False,
                "notify_on_engagement": True,
                "notify_on_comments": True,
                "notify_on_friend_milestones": True,
                "feed_refresh_interval": 300,
                "max_activities_per_load": 20,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None
            }
            
            settings_list.append(default_settings)
            await self._save_settings(settings_list)
            
            return ActivityFeedSettings(**default_settings)
            
        except Exception as e:
            logger.error(f"Error creating default settings: {e}")
            raise
    
    async def update_user_settings(
        self,
        user_id: int,
        settings_update: ActivityFeedSettingsUpdate
    ) -> Optional[ActivityFeedSettings]:
        """Update user's activity feed settings."""
        try:
            settings_list = await self._load_settings()
            
            # Find user's settings
            settings_index = next((i for i, s in enumerate(settings_list) if s['user_id'] == user_id), None)
            if settings_index is None:
                # Create default settings first
                await self.create_default_settings(user_id)
                settings_list = await self._load_settings()
                settings_index = next((i for i, s in enumerate(settings_list) if s['user_id'] == user_id), None)
            
            # Update settings
            update_dict = settings_update.dict(exclude_unset=True)
            settings_list[settings_index].update(update_dict)
            settings_list[settings_index]['updated_at'] = datetime.utcnow().isoformat()
            
            await self._save_settings(settings_list)
            
            return ActivityFeedSettings(**settings_list[settings_index])
            
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return None
    
    # Notification Management
    
    async def _send_activity_notifications(self, activity: Dict):
        """Send notifications to friends about new activity."""
        try:
            # Only send notifications for milestone activities or high priority
            if not activity['is_milestone'] and activity['priority'] not in ['high', 'urgent']:
                return
            
            user_id = activity['user_id']
            friends_response = await friend_service.get_friends(user_id, skip=0, limit=1000)
            
            for friend in friends_response.friends:
                friend_settings = await self.get_user_settings(friend.user_id)
                
                # Check if friend wants notifications for this type
                if friend_settings and friend_settings.notify_on_friend_milestones:
                    # In a real implementation, this would create actual notifications
                    logger.info(f"Would notify user {friend.user_id} about activity {activity['id']}")
            
        except Exception as e:
            logger.error(f"Error sending activity notifications: {e}")
    
    async def _send_engagement_notification(self, activity: Dict, engaging_user_id: int, engagement_type: EngagementType):
        """Send notification about engagement to activity owner."""
        try:
            activity_owner_id = activity['user_id']
            owner_settings = await self.get_user_settings(activity_owner_id)
            
            if owner_settings and owner_settings.notify_on_engagement:
                # In a real implementation, this would create actual notifications
                logger.info(f"Would notify user {activity_owner_id} about {engagement_type} from user {engaging_user_id}")
            
        except Exception as e:
            logger.error(f"Error sending engagement notification: {e}")
    
    async def _send_comment_notification(self, activity: Dict, commenting_user_id: int, comment_content: str):
        """Send notification about comment to activity owner."""
        try:
            activity_owner_id = activity['user_id']
            owner_settings = await self.get_user_settings(activity_owner_id)
            
            if owner_settings and owner_settings.notify_on_comments:
                # In a real implementation, this would create actual notifications
                logger.info(f"Would notify user {activity_owner_id} about comment from user {commenting_user_id}")
            
        except Exception as e:
            logger.error(f"Error sending comment notification: {e}")
    
    # Statistics and Analytics
    
    async def get_user_activity_stats(self, user_id: int) -> ActivityStats:
        """Get comprehensive activity statistics for a user."""
        try:
            activities = await self._load_activities()
            engagements = await self._load_engagements()
            comments = await self._load_comments()
            
            # Filter user's activities
            user_activities = [a for a in activities if a['user_id'] == user_id]
            
            # Calculate engagement stats
            total_engagements_received = sum(
                len([e for e in engagements if e['activity_id'] == activity['id']])
                for activity in user_activities
            )
            
            total_comments_received = sum(
                len([c for c in comments if c['activity_id'] == activity['id']])
                for activity in user_activities
            )
            
            total_engagements_given = len([e for e in engagements if e['user_id'] == user_id])
            total_comments_given = len([c for c in comments if c['user_id'] == user_id])
            
            # Activity breakdown by type
            activities_by_type = defaultdict(int)
            for activity in user_activities:
                activities_by_type[activity['activity_type']] += 1
            
            # Time-based stats
            week_ago = datetime.utcnow() - timedelta(days=7)
            month_ago = datetime.utcnow() - timedelta(days=30)
            
            activities_this_week = len([
                a for a in user_activities
                if datetime.fromisoformat(a['created_at']) >= week_ago
            ])
            
            activities_this_month = len([
                a for a in user_activities
                if datetime.fromisoformat(a['created_at']) >= month_ago
            ])
            
            # Average engagements per activity
            avg_engagements = (
                total_engagements_received / len(user_activities)
                if user_activities else 0
            )
            
            return ActivityStats(
                total_activities=len(user_activities),
                total_engagements_received=total_engagements_received,
                total_comments_received=total_comments_received,
                total_engagements_given=total_engagements_given,
                total_comments_given=total_comments_given,
                activities_by_type=dict(activities_by_type),
                most_engaged_activity_type=max(activities_by_type.items(), key=lambda x: x[1])[0] if activities_by_type else None,
                activities_this_week=activities_this_week,
                activities_this_month=activities_this_month,
                average_engagements_per_activity=round(avg_engagements, 2),
                most_active_friend=None,  # Would analyze friend engagement patterns
                most_supportive_friend=None  # Would analyze friend comment patterns
            )
            
        except Exception as e:
            logger.error(f"Error getting activity stats: {e}")
            raise


# Global service instance
activity_feed_service = ActivityFeedService() 