import logging
import json
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from app.db import models as db_models
from app.services.user_service import user_service # Use singleton instance
from app.core.websockets import manager
from app.models.social import FriendshipStatus, Follower, FriendRequest, Comment
from app.services.push_notification_service import push_notification_service
from app.services.base_service import BaseService
from app.models.user import User
from app.schemas.social import FriendRequestCreate, FriendRequestUpdate, CommentCreate, CommentUpdate
from app.services import notification_service

logger = logging.getLogger(__name__)

class SocialService(BaseService[Follower, None, None]):  # Follower has no create/update schema here
    def __init__(self):
        # In a real app, a proper dependency injection system would be used
        self.user_service = user_service

    async def create_activity(
        self, db: Session, user_id: int, activity_type: str, data: dict
    ) -> db_models.Activity:
        """Create and store a new activity in the database."""
        new_activity = db_models.Activity(
            user_id=user_id,
            activity_type=activity_type,
            content=data.get("content", "")
        )
        db.add(new_activity)
        # The commit is expected to be handled by the calling service that orchestrates the operation.
        return new_activity

    async def get_user_activity_feed(self, db: Session, user_id: int, limit: int = 50) -> List[db_models.Activity]:
        """
        Get the activity feed for a user, including their own activities and
        those of users they follow.
        """
        following_relations = self.get_following(db, user_id)
        following_ids = [f.following_id for f in following_relations]
        user_ids_for_feed = following_ids + [user_id]
        
        return db.query(db_models.Activity)\
                 .filter(db_models.Activity.user_id.in_(user_ids_for_feed))\
                 .order_by(db_models.Activity.created_at.desc())\
                 .limit(limit)\
                 .all()

    def follow_user(self, db: Session, *, follower_id: int, followed_id: int) -> Follower:
        if follower_id == followed_id:
            raise ValueError("User cannot follow themselves.")
        
        existing = db.query(Follower).filter_by(follower_id=follower_id, followed_id=followed_id).first()
        if existing:
            return existing

        db_follower = Follower(follower_id=follower_id, followed_id=followed_id)
        db.add(db_follower)
        db.commit()
        db.refresh(db_follower)
        logger.info(f"User {follower_id} is now following {followed_id}")
        return db_follower

    def unfollow_user(self, db: Session, *, follower_id: int, followed_id: int) -> bool:
        db_follower = db.query(Follower).filter_by(follower_id=follower_id, followed_id=followed_id).first()
        if db_follower:
            db.delete(db_follower)
            db.commit()
            logger.info(f"User {follower_id} unfollowed {followed_id}")
            return True
        return False

    def get_followers(self, db: Session, *, user_id: int) -> List[User]:
        return db.query(User).join(Follower, User.id == Follower.follower_id).filter(Follower.followed_id == user_id).all()

    def get_following(self, db: Session, *, user_id: int) -> List[User]:
        return db.query(User).join(Follower, User.id == Follower.followed_id).filter(Follower.follower_id == user_id).all()

    def get_friends(self, db: Session, *, user_id: int) -> List[User]:
        # Friends are mutual followers
        following = {user.id for user in self.get_following(db, user_id=user_id)}
        followers = {user.id for user in self.get_followers(db, user_id=user_id)}
        friend_ids = following.intersection(followers)
        return db.query(User).filter(User.id.in_(friend_ids)).all()

    def get_follow_counts(self, db: Session, user_id: int) -> Dict[str, int]:
        """Get follower and following counts for a user."""
        followers_count = db.query(Follower).filter_by(followed_id=user_id).count()
        following_count = db.query(Follower).filter_by(follower_id=user_id).count()
        return {"followers_count": followers_count, "following_count": following_count}

    def create_friend_request(self, db: Session, *, requester_id: int, addressee_id: int) -> FriendRequest:
        if requester_id == addressee_id:
            raise ValueError("Cannot send a friend request to oneself.")
        
        existing_request = db.query(FriendRequest).filter_by(requester_id=requester_id, addressee_id=addressee_id, status="pending").first()
        if existing_request:
            return existing_request # Or raise an error that request is already pending

        db_request = FriendRequest(requester_id=requester_id, addressee_id=addressee_id)
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        notification_service.create_friend_request_notification(db, user_id=addressee_id, requester_id=requester_id)
        logger.info(f"Friend request sent from {requester_id} to {addressee_id}")
        return db_request

    def respond_to_friend_request(self, db: Session, *, request_id: int, new_status: str, user_id: int) -> FriendRequest:
        db_request = db.query(FriendRequest).get(request_id)
        if not db_request or db_request.addressee_id != user_id:
            raise ValueError("Friend request not found or user not authorized.")
        
        db_request.status = new_status
        if new_status == "accepted":
            self.follow_user(db, follower_id=db_request.requester_id, followed_id=db_request.addressee_id)
            self.follow_user(db, follower_id=db_request.addressee_id, followed_id=db_request.requester_id)
        
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    def get_pending_requests(self, db: Session, *, user_id: int) -> List[FriendRequest]:
        return db.query(FriendRequest).filter_by(addressee_id=user_id, status="pending").all()

    def get_social_feed(self, db: Session, user_id: int, limit: int = 50) -> List[dict]:
        """
        Get the social feed for a user, containing activities from their friends.
        """
        friends = self.get_friends(db, user_id)
        friend_ids = [friend.id for friend in friends]

        if not friend_ids:
            return []

        # Get activities from friends
        activities = db.query(
            db_models.Activity,
            db_models.User.username,
            db_models.UserProfile.profile_picture_url
        ).join(
            db_models.User, db_models.Activity.user_id == db_models.User.id
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id, isouter=True
        ).filter(
            db_models.Activity.user_id.in_(friend_ids)
        ).order_by(
            db_models.Activity.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": activity.id,
                "user_id": activity.user_id,
                "username": username,
                "profile_picture_url": profile_picture_url,
                "activity_type": activity.activity_type,
                "content": activity.data,
                "created_at": activity.created_at
            }
            for activity, username, profile_picture_url in activities
        ]

    def create_comment(self, db: Session, *, user_achievement_id: int, user_id: int, content: str) -> Comment:
        db_comment = Comment(user_achievement_id=user_achievement_id, user_id=user_id, content=content)
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        # Notify the achievement owner
        # achievement_owner_id = ... get owner from user_achievement_id
        # notification_service.create_comment_notification(db, user_id=achievement_owner_id, commenter_id=user_id)
        return db_comment

    def get_comments(self, db: Session, *, user_achievement_id: int) -> List[Comment]:
        return db.query(Comment).filter_by(user_achievement_id=user_achievement_id).order_by(Comment.timestamp.asc()).all()
        
    def delete_comment(self, db: Session, *, comment_id: int) -> bool:
        comment = db.query(Comment).get(comment_id)
        if comment:
            db.delete(comment)
            db.commit()
            return True
        return False

social_service = SocialService() 