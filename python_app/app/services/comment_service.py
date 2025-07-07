from typing import List
from sqlalchemy.orm import Session
from app.db import models as db_models
from app.models.comment import CommentCreate
from app.services.push_notification_service import push_notification_service

class CommentService:
    def create_comment(
        self,
        db: Session,
        user_id: int,
        user_achievement_id: int,
        comment_data: CommentCreate
    ) -> db_models.Comment:
        # Verify the achievement exists and belongs to a friend or is public
        # (This logic can be enhanced based on privacy settings)
        user_achievement = db.query(db_models.UserAchievement).get(user_achievement_id)
        if not user_achievement:
            raise ValueError("Achievement not found.")

        db_comment = db_models.Comment(
            user_id=user_id,
            user_achievement_id=user_achievement_id,
            content=comment_data.content
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)

        # Send push notification to the achievement owner
        if user_achievement.user_id != user_id: # Don't notify for own comments
            commenter = db.query(db_models.User).get(user_id)
            push_notification_service.send_push_notification(
                db=db,
                user_id=user_achievement.user_id,
                title="New Comment on Your Achievement",
                body=f"{commenter.username} commented: \"{db_comment.content[:50]}...\"",
                data={
                    "user_achievement_id": user_achievement_id,
                    "comment_id": db_comment.id
                }
            )

        return db_comment

    def get_comments_for_achievement(
        self,
        db: Session,
        user_achievement_id: int
    ) -> List[db_models.Comment]:
        return db.query(db_models.Comment).filter(
            db_models.Comment.user_achievement_id == user_achievement_id
        ).order_by(db_models.Comment.created_at.asc()).all() 