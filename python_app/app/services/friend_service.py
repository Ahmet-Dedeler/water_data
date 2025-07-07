import json
import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import re

from app.models.friend import (
    Friendship, FriendRequest, FriendRequestResponse, FriendUpdate,
    FriendProfile, FriendActivity, FriendSearchResult, FriendStats,
    FriendRecommendation, FriendNotificationSettings, FriendListResponse,
    MutualFriend, FriendshipStatus, FriendRequestType, PrivacyLevel,
    NotificationPreference
)
from app.models.common import BaseResponse
from app.services.user_service import user_service

logger = logging.getLogger(__name__)


class FriendService:
    """Comprehensive friend system service."""
    
    def __init__(self):
        self.friendships_file = Path(__file__).parent.parent / "data" / "friendships.json"
        self.friend_activities_file = Path(__file__).parent.parent / "data" / "friend_activities.json"
        self._ensure_data_files()
        self._friendships_cache = None
        self._activities_cache = None
        self._next_friendship_id = 1
        self._next_activity_id = 1
    
    def _ensure_data_files(self):
        """Ensure friend data files exist."""
        data_dir = self.friendships_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [self.friendships_file, self.friend_activities_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_friendships(self) -> List[Dict]:
        """Load friendships from file."""
        if self._friendships_cache is None:
            try:
                with open(self.friendships_file, 'r') as f:
                    self._friendships_cache = json.load(f)
                    
                # Update next ID
                if self._friendships_cache:
                    self._next_friendship_id = max(f['id'] for f in self._friendships_cache) + 1
            except Exception as e:
                logger.error(f"Error loading friendships: {e}")
                self._friendships_cache = []
        return self._friendships_cache
    
    async def _save_friendships(self, friendships: List[Dict]):
        """Save friendships to file."""
        try:
            with open(self.friendships_file, 'w') as f:
                json.dump(friendships, f, indent=2, default=str)
            self._friendships_cache = friendships
        except Exception as e:
            logger.error(f"Error saving friendships: {e}")
            raise
    
    async def _load_activities(self) -> List[Dict]:
        """Load friend activities from file."""
        if self._activities_cache is None:
            try:
                with open(self.friend_activities_file, 'r') as f:
                    self._activities_cache = json.load(f)
                    
                # Update next ID
                if self._activities_cache:
                    self._next_activity_id = max(a['id'] for a in self._activities_cache) + 1
            except Exception as e:
                logger.error(f"Error loading activities: {e}")
                self._activities_cache = []
        return self._activities_cache
    
    async def _save_activities(self, activities: List[Dict]):
        """Save friend activities to file."""
        try:
            with open(self.friend_activities_file, 'w') as f:
                json.dump(activities, f, indent=2, default=str)
            self._activities_cache = activities
        except Exception as e:
            logger.error(f"Error saving activities: {e}")
            raise
    
    # Friend Request Management
    
    async def send_friend_request(
        self,
        user_id: int,
        request_data: FriendRequest
    ) -> Friendship:
        """Send a friend request to another user."""
        try:
            # Find target user
            target_user = None
            if request_data.friend_id:
                target_user = await user_service.get_user_by_id(request_data.friend_id)
            elif request_data.friend_username:
                target_user = await user_service.get_user_by_username(request_data.friend_username)
            elif request_data.friend_email:
                target_user = await user_service.get_user_by_email(request_data.friend_email)
            
            if not target_user:
                raise ValueError("User not found")
            
            if target_user.id == user_id:
                raise ValueError("Cannot send friend request to yourself")
            
            friendships = await self._load_friendships()
            
            # Check if friendship already exists
            existing = self._find_friendship(friendships, user_id, target_user.id)
            if existing:
                if existing['status'] == FriendshipStatus.ACCEPTED:
                    raise ValueError("Already friends with this user")
                elif existing['status'] == FriendshipStatus.PENDING:
                    raise ValueError("Friend request already pending")
                elif existing['status'] == FriendshipStatus.BLOCKED:
                    raise ValueError("Cannot send request to blocked user")
            
            # Create friendship record
            friendship_dict = {
                "id": self._next_friendship_id,
                "user_id": user_id,
                "friend_id": target_user.id,
                "status": FriendshipStatus.PENDING.value,
                "request_type": request_data.request_type.value,
                "requested_at": datetime.utcnow().isoformat(),
                "responded_at": None,
                "last_interaction": None,
                "is_close_friend": False,
                "is_favorite": False,
                "nickname": None,
                "notes": None,
                "can_see_water_logs": True,
                "can_see_health_goals": True,
                "can_see_achievements": True,
                "can_see_activity": True,
                "total_interactions": 0,
                "shared_challenges": 0,
                "mutual_friends": await self._count_mutual_friends(user_id, target_user.id),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            friendships.append(friendship_dict)
            await self._save_friendships(friendships)
            
            self._next_friendship_id += 1
            
            # Create activity for friend request
            await self._create_friend_activity(
                user_id=user_id,
                friend_id=target_user.id,
                activity_type="friend_request_sent",
                activity_data={"message": request_data.message},
                message=f"Sent a friend request"
            )
            
            logger.info(f"Friend request sent from user {user_id} to user {target_user.id}")
            return Friendship(**friendship_dict)
            
        except Exception as e:
            logger.error(f"Error sending friend request: {e}")
            raise
    
    def _find_friendship(self, friendships: List[Dict], user1_id: int, user2_id: int) -> Optional[Dict]:
        """Find friendship between two users (bidirectional)."""
        for friendship in friendships:
            if ((friendship['user_id'] == user1_id and friendship['friend_id'] == user2_id) or
                (friendship['user_id'] == user2_id and friendship['friend_id'] == user1_id)):
                return friendship
        return None
    
    async def respond_to_friend_request(
        self,
        user_id: int,
        friendship_id: int,
        response: FriendRequestResponse
    ) -> Friendship:
        """Respond to a friend request (accept or decline)."""
        try:
            friendships = await self._load_friendships()
            
            # Find the friendship
            friendship_index = next((
                i for i, f in enumerate(friendships)
                if f['id'] == friendship_id and f['friend_id'] == user_id and f['status'] == FriendshipStatus.PENDING.value
            ), None)
            
            if friendship_index is None:
                raise ValueError("Friend request not found or not pending")
            
            friendship_dict = friendships[friendship_index]
            
            # Update friendship status
            if response.accept:
                friendship_dict['status'] = FriendshipStatus.ACCEPTED.value
                activity_type = "friend_request_accepted"
                message = "Accepted friend request"
            else:
                friendship_dict['status'] = FriendshipStatus.DECLINED.value
                activity_type = "friend_request_declined"
                message = "Declined friend request"
            
            friendship_dict['responded_at'] = datetime.utcnow().isoformat()
            friendship_dict['updated_at'] = datetime.utcnow().isoformat()
            
            friendships[friendship_index] = friendship_dict
            await self._save_friendships(friendships)
            
            # Create activity
            await self._create_friend_activity(
                user_id=user_id,
                friend_id=friendship_dict['user_id'],
                activity_type=activity_type,
                activity_data={"message": response.message},
                message=message
            )
            
            logger.info(f"Friend request {friendship_id} {'accepted' if response.accept else 'declined'} by user {user_id}")
            return Friendship(**friendship_dict)
            
        except Exception as e:
            logger.error(f"Error responding to friend request: {e}")
            raise
    
    async def get_pending_friend_requests(
        self,
        user_id: int,
        incoming: bool = True
    ) -> List[Friendship]:
        """Get pending friend requests for a user."""
        try:
            friendships = await self._load_friendships()
            
            if incoming:
                # Requests received by the user
                pending = [
                    f for f in friendships
                    if f['friend_id'] == user_id and f['status'] == FriendshipStatus.PENDING.value
                ]
            else:
                # Requests sent by the user
                pending = [
                    f for f in friendships
                    if f['user_id'] == user_id and f['status'] == FriendshipStatus.PENDING.value
                ]
            
            # Sort by request date (most recent first)
            pending.sort(key=lambda x: x['requested_at'], reverse=True)
            
            return [Friendship(**f) for f in pending]
            
        except Exception as e:
            logger.error(f"Error getting pending friend requests: {e}")
            return []
    
    # Friend Management
    
    async def get_friends(
        self,
        user_id: int,
        close_friends_only: bool = False,
        online_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> FriendListResponse:
        """Get user's friends list."""
        try:
            friendships = await self._load_friendships()
            
            # Get accepted friendships for the user
            user_friendships = [
                f for f in friendships
                if ((f['user_id'] == user_id or f['friend_id'] == user_id) and
                    f['status'] == FriendshipStatus.ACCEPTED.value)
            ]
            
            # Filter by close friends if requested
            if close_friends_only:
                user_friendships = [f for f in user_friendships if f.get('is_close_friend', False)]
            
            friend_profiles = []
            online_count = 0
            
            for friendship in user_friendships:
                # Get the friend's user ID (not the current user)
                friend_user_id = friendship['friend_id'] if friendship['user_id'] == user_id else friendship['user_id']
                
                # Get friend's profile
                friend_user = await user_service.get_user_by_id(friend_user_id)
                if not friend_user:
                    continue
                
                # Check if online (simplified - would need real presence tracking)
                is_online = await self._is_user_online(friend_user_id)
                if online_only and not is_online:
                    continue
                
                if is_online:
                    online_count += 1
                
                # Get friend's stats if visible
                stats = await self._get_friend_visible_stats(user_id, friend_user_id, friendship)
                
                friend_profile = FriendProfile(
                    user_id=friend_user_id,
                    username=friend_user.username,
                    display_name=getattr(friend_user, 'display_name', None),
                    avatar_url=getattr(friend_user, 'avatar_url', None),
                    bio=getattr(friend_user, 'bio', None),
                    friendship_id=friendship['id'],
                    friendship_status=FriendshipStatus(friendship['status']),
                    is_close_friend=friendship.get('is_close_friend', False),
                    is_favorite=friendship.get('is_favorite', False),
                    nickname=friendship.get('nickname'),
                    last_seen=stats.get('last_seen'),
                    current_streak=stats.get('current_streak'),
                    total_achievements=stats.get('total_achievements'),
                    weekly_goal_completion=stats.get('weekly_goal_completion'),
                    favorite_drink_type=stats.get('favorite_drink_type'),
                    mutual_friends_count=friendship.get('mutual_friends', 0),
                    shared_challenges_count=friendship.get('shared_challenges', 0)
                )
                
                friend_profiles.append(friend_profile)
            
            # Sort friends (favorites first, then by name)
            friend_profiles.sort(key=lambda x: (not x.is_favorite, x.username))
            
            # Apply pagination
            total_count = len(friend_profiles)
            paginated_friends = friend_profiles[skip:skip + limit]
            
            close_friends_count = sum(1 for f in friend_profiles if f.is_close_friend)
            
            return FriendListResponse(
                friends=paginated_friends,
                total_count=total_count,
                close_friends_count=close_friends_count,
                online_friends_count=online_count,
                page=skip // limit + 1,
                page_size=limit,
                has_next=skip + limit < total_count
            )
            
        except Exception as e:
            logger.error(f"Error getting friends: {e}")
            return FriendListResponse(
                friends=[],
                total_count=0,
                close_friends_count=0,
                online_friends_count=0,
                page=1,
                page_size=limit,
                has_next=False
            )
    
    async def _is_user_online(self, user_id: int) -> bool:
        """Check if user is currently online (simplified implementation)."""
        # In a real implementation, this would check recent activity or websocket connections
        # For now, return a random status based on user activity
        try:
            user_profile = await user_service.get_user_profile(user_id)
            if user_profile and hasattr(user_profile, 'last_active'):
                last_active = user_profile.last_active
                if last_active and (datetime.utcnow() - last_active).total_seconds() < 300:  # 5 minutes
                    return True
            return False
        except:
            return False
    
    async def _get_friend_visible_stats(
        self,
        user_id: int,
        friend_id: int,
        friendship: Dict
    ) -> Dict[str, Any]:
        """Get friend's stats that are visible to the user."""
        stats = {}
        
        try:
            if friendship.get('can_see_activity', True):
                # Get basic activity stats
                user_profile = await user_service.get_user_profile(friend_id)
                if user_profile:
                    stats['last_seen'] = getattr(user_profile, 'last_active', None)
                    stats['current_streak'] = getattr(user_profile, 'current_streak', None)
            
            if friendship.get('can_see_achievements', True):
                # Would get achievement count from achievement service
                stats['total_achievements'] = 0  # Placeholder
            
            if friendship.get('can_see_health_goals', True):
                # Would get goal completion from health goals service
                stats['weekly_goal_completion'] = None  # Placeholder
            
            # Get favorite drink type from drink logs
            stats['favorite_drink_type'] = None  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting friend stats: {e}")
        
        return stats
    
    async def update_friendship(
        self,
        user_id: int,
        friendship_id: int,
        update_data: FriendUpdate
    ) -> Optional[Friendship]:
        """Update friendship settings."""
        try:
            friendships = await self._load_friendships()
            
            # Find the friendship
            friendship_index = next((
                i for i, f in enumerate(friendships)
                if f['id'] == friendship_id and (f['user_id'] == user_id or f['friend_id'] == user_id)
            ), None)
            
            if friendship_index is None:
                return None
            
            friendship_dict = friendships[friendship_index]
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            friendship_dict.update(update_dict)
            friendship_dict['updated_at'] = datetime.utcnow().isoformat()
            
            friendships[friendship_index] = friendship_dict
            await self._save_friendships(friendships)
            
            logger.info(f"Updated friendship {friendship_id} for user {user_id}")
            return Friendship(**friendship_dict)
            
        except Exception as e:
            logger.error(f"Error updating friendship: {e}")
            return None
    
    async def remove_friend(self, user_id: int, friendship_id: int) -> bool:
        """Remove a friend (delete friendship)."""
        try:
            friendships = await self._load_friendships()
            
            # Find and remove the friendship
            original_count = len(friendships)
            friendships = [
                f for f in friendships
                if not (f['id'] == friendship_id and (f['user_id'] == user_id or f['friend_id'] == user_id))
            ]
            
            if len(friendships) == original_count:
                return False  # Friendship not found
            
            await self._save_friendships(friendships)
            
            logger.info(f"Removed friendship {friendship_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing friend: {e}")
            return False
    
    async def block_user(self, user_id: int, target_user_id: int) -> bool:
        """Block a user."""
        try:
            friendships = await self._load_friendships()
            
            # Find existing friendship
            existing = self._find_friendship(friendships, user_id, target_user_id)
            
            if existing:
                # Update to blocked status
                existing['status'] = FriendshipStatus.BLOCKED.value
                existing['updated_at'] = datetime.utcnow().isoformat()
            else:
                # Create new blocked relationship
                friendship_dict = {
                    "id": self._next_friendship_id,
                    "user_id": user_id,
                    "friend_id": target_user_id,
                    "status": FriendshipStatus.BLOCKED.value,
                    "request_type": FriendRequestType.DIRECT.value,
                    "requested_at": datetime.utcnow().isoformat(),
                    "responded_at": datetime.utcnow().isoformat(),
                    "last_interaction": None,
                    "is_close_friend": False,
                    "is_favorite": False,
                    "nickname": None,
                    "notes": None,
                    "can_see_water_logs": False,
                    "can_see_health_goals": False,
                    "can_see_achievements": False,
                    "can_see_activity": False,
                    "total_interactions": 0,
                    "shared_challenges": 0,
                    "mutual_friends": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                friendships.append(friendship_dict)
                self._next_friendship_id += 1
            
            await self._save_friendships(friendships)
            
            logger.info(f"User {user_id} blocked user {target_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            return False
    
    # Friend Search and Discovery
    
    async def search_users(
        self,
        user_id: int,
        query: str,
        limit: int = 20
    ) -> List[FriendSearchResult]:
        """Search for users to potentially befriend."""
        try:
            # Get all users (in a real app, this would be a database query)
            all_users = await user_service.get_all_users()
            friendships = await self._load_friendships()
            
            # Get current friend IDs
            friend_ids = set()
            for friendship in friendships:
                if friendship['user_id'] == user_id and friendship['status'] == FriendshipStatus.ACCEPTED.value:
                    friend_ids.add(friendship['friend_id'])
                elif friendship['friend_id'] == user_id and friendship['status'] == FriendshipStatus.ACCEPTED.value:
                    friend_ids.add(friendship['user_id'])
            
            # Get pending request IDs
            pending_ids = set()
            for friendship in friendships:
                if friendship['status'] == FriendshipStatus.PENDING.value:
                    if friendship['user_id'] == user_id:
                        pending_ids.add(friendship['friend_id'])
                    elif friendship['friend_id'] == user_id:
                        pending_ids.add(friendship['user_id'])
            
            search_results = []
            query_lower = query.lower()
            
            for user in all_users:
                if user.id == user_id:  # Skip self
                    continue
                
                # Calculate search score
                score = 0.0
                if query_lower in user.username.lower():
                    score += 0.8
                if hasattr(user, 'display_name') and user.display_name and query_lower in user.display_name.lower():
                    score += 0.6
                if hasattr(user, 'email') and user.email and query_lower in user.email.lower():
                    score += 0.4
                
                if score == 0:
                    continue  # No match
                
                # Get relationship status
                is_friend = user.id in friend_ids
                has_pending = user.id in pending_ids
                friendship_status = None
                
                if is_friend:
                    friendship_status = FriendshipStatus.ACCEPTED
                elif has_pending:
                    friendship_status = FriendshipStatus.PENDING
                
                # Count mutual friends
                mutual_count = await self._count_mutual_friends(user_id, user.id)
                
                search_result = FriendSearchResult(
                    user_id=user.id,
                    username=user.username,
                    display_name=getattr(user, 'display_name', None),
                    avatar_url=getattr(user, 'avatar_url', None),
                    friendship_status=friendship_status,
                    is_friend=is_friend,
                    has_pending_request=has_pending,
                    mutual_friends_count=mutual_count,
                    mutual_friends_preview=[],  # Would get actual names
                    search_score=score,
                    suggested_reason=f"Username matches '{query}'" if query_lower in user.username.lower() else None
                )
                
                search_results.append(search_result)
            
            # Sort by search score (highest first)
            search_results.sort(key=lambda x: x.search_score, reverse=True)
            
            return search_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    async def get_friend_recommendations(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[FriendRecommendation]:
        """Get friend recommendations for a user."""
        try:
            friendships = await self._load_friendships()
            all_users = await user_service.get_all_users()
            
            # Get current friends
            current_friends = set()
            for friendship in friendships:
                if friendship['user_id'] == user_id and friendship['status'] == FriendshipStatus.ACCEPTED.value:
                    current_friends.add(friendship['friend_id'])
                elif friendship['friend_id'] == user_id and friendship['status'] == FriendshipStatus.ACCEPTED.value:
                    current_friends.add(friendship['user_id'])
            
            recommendations = []
            
            for user in all_users:
                if user.id == user_id or user.id in current_friends:
                    continue
                
                # Calculate recommendation score based on mutual friends
                mutual_count = await self._count_mutual_friends(user_id, user.id)
                
                if mutual_count == 0:
                    continue  # Skip users with no mutual connections
                
                # Score based on mutual friends (more = higher score)
                score = min(mutual_count / 10.0, 1.0)  # Cap at 1.0
                
                reasons = []
                if mutual_count > 0:
                    reasons.append(f"{mutual_count} mutual friend{'s' if mutual_count > 1 else ''}")
                
                # Get mutual friend names (simplified)
                mutual_names = []  # Would get actual names
                
                recommendation = FriendRecommendation(
                    user_id=user.id,
                    username=user.username,
                    display_name=getattr(user, 'display_name', None),
                    avatar_url=getattr(user, 'avatar_url', None),
                    recommendation_score=score,
                    recommendation_reasons=reasons,
                    mutual_friends_count=mutual_count,
                    mutual_friends_names=mutual_names,
                    shared_interests=[],  # Would analyze user preferences
                    connection_strength="Medium" if mutual_count > 2 else "Weak",
                    last_interaction=None
                )
                
                recommendations.append(recommendation)
            
            # Sort by recommendation score (highest first)
            recommendations.sort(key=lambda x: x.recommendation_score, reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting friend recommendations: {e}")
            return []
    
    async def _count_mutual_friends(self, user1_id: int, user2_id: int) -> int:
        """Count mutual friends between two users."""
        try:
            friendships = await self._load_friendships()
            
            # Get friends of user1
            user1_friends = set()
            for friendship in friendships:
                if friendship['status'] == FriendshipStatus.ACCEPTED.value:
                    if friendship['user_id'] == user1_id:
                        user1_friends.add(friendship['friend_id'])
                    elif friendship['friend_id'] == user1_id:
                        user1_friends.add(friendship['user_id'])
            
            # Get friends of user2
            user2_friends = set()
            for friendship in friendships:
                if friendship['status'] == FriendshipStatus.ACCEPTED.value:
                    if friendship['user_id'] == user2_id:
                        user2_friends.add(friendship['friend_id'])
                    elif friendship['friend_id'] == user2_id:
                        user2_friends.add(friendship['user_id'])
            
            # Count mutual friends
            mutual_friends = user1_friends.intersection(user2_friends)
            return len(mutual_friends)
            
        except Exception as e:
            logger.error(f"Error counting mutual friends: {e}")
            return 0
    
    # Friend Activities
    
    async def _create_friend_activity(
        self,
        user_id: int,
        friend_id: int,
        activity_type: str,
        activity_data: Dict[str, Any],
        message: str,
        privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC,
        is_milestone: bool = False
    ) -> FriendActivity:
        """Create a friend activity entry."""
        try:
            activities = await self._load_activities()
            
            activity_dict = {
                "id": self._next_activity_id,
                "user_id": user_id,
                "friend_id": friend_id,
                "activity_type": activity_type,
                "activity_data": activity_data,
                "message": message,
                "privacy_level": privacy_level.value,
                "is_milestone": is_milestone,
                "likes_count": 0,
                "comments_count": 0,
                "has_liked": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            activities.append(activity_dict)
            await self._save_activities(activities)
            
            self._next_activity_id += 1
            
            return FriendActivity(**activity_dict)
            
        except Exception as e:
            logger.error(f"Error creating friend activity: {e}")
            raise
    
    async def get_friend_stats(self, user_id: int) -> FriendStats:
        """Get comprehensive friend statistics for a user."""
        try:
            friendships = await self._load_friendships()
            
            # Filter friendships for this user
            user_friendships = [
                f for f in friendships
                if (f['user_id'] == user_id or f['friend_id'] == user_id)
            ]
            
            # Count by status
            total_friends = sum(1 for f in user_friendships if f['status'] == FriendshipStatus.ACCEPTED.value)
            close_friends = sum(1 for f in user_friendships if f['status'] == FriendshipStatus.ACCEPTED.value and f.get('is_close_friend', False))
            pending_sent = sum(1 for f in user_friendships if f['user_id'] == user_id and f['status'] == FriendshipStatus.PENDING.value)
            pending_received = sum(1 for f in user_friendships if f['friend_id'] == user_id and f['status'] == FriendshipStatus.PENDING.value)
            
            # Activity stats (simplified)
            week_ago = datetime.utcnow() - timedelta(days=7)
            month_ago = datetime.utcnow() - timedelta(days=30)
            
            active_this_week = 0  # Would check actual user activity
            interactions_this_month = sum(f.get('total_interactions', 0) for f in user_friendships)
            
            # Network analysis
            mutual_friends_counts = [f.get('mutual_friends', 0) for f in user_friendships if f['status'] == FriendshipStatus.ACCEPTED.value]
            avg_mutual = sum(mutual_friends_counts) / len(mutual_friends_counts) if mutual_friends_counts else 0
            
            # Longest friendship
            accepted_friendships = [f for f in user_friendships if f['status'] == FriendshipStatus.ACCEPTED.value]
            longest_days = 0
            if accepted_friendships:
                oldest = min(accepted_friendships, key=lambda x: x['requested_at'])
                oldest_date = datetime.fromisoformat(oldest['requested_at'])
                longest_days = (datetime.utcnow() - oldest_date).days
            
            return FriendStats(
                total_friends=total_friends,
                close_friends=close_friends,
                pending_requests_sent=pending_sent,
                pending_requests_received=pending_received,
                active_friends_this_week=active_this_week,
                shared_challenges_active=0,  # Would get from challenges service
                total_interactions_this_month=interactions_this_month,
                average_mutual_friends=round(avg_mutual, 1),
                most_connected_friend=None,  # Would analyze actual connections
                longest_friendship_days=longest_days
            )
            
        except Exception as e:
            logger.error(f"Error getting friend stats: {e}")
            raise


# Global service instance
friend_service = FriendService() 