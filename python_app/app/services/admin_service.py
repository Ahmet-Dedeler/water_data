from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.db import models as db_models
from app.models.admin import AdminDashboardStats
from app.models.user import User
from app.models.water import WaterLog
from app.models.social import Comment
from app.schemas.admin import SiteStats, FullUserOut
import logging

log = logging.getLogger(__name__)

class AdminService:
    def get_site_stats(self, db: Session) -> SiteStats:
        """
        Gathers high-level statistics about the entire application.
        """
        total_users = db.query(User).count()
        total_water_logs = db.query(WaterLog).count()
        total_volume_ml = db.query(func.sum(WaterLog.volume_ml)).scalar() or 0
        total_comments = db.query(Comment).count()

        return SiteStats(
            total_users=total_users,
            total_water_logs=total_water_logs,
            total_volume_ml=total_volume_ml,
            total_comments=total_comments,
        )

    def get_all_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[FullUserOut]:
        """
        Retrieves a list of all users with their full profile information.
        """
        users = db.query(User).offset(skip).limit(limit).all()
        return [FullUserOut.from_orm(user) for user in users]

    def ban_user(self, db: Session, *, user_id: int) -> bool:
        """
        Marks a user as inactive (banned).
        """
        user = db.query(User).get(user_id)
        if user:
            user.is_active = False
            db.commit()
            log.warning(f"Admin has banned user {user_id}.")
            return True
        return False

    def unban_user(self, db: Session, *, user_id: int) -> bool:
        """
        Marks a user as active (unbanned).
        """
        user = db.query(User).get(user_id)
        if user:
            user.is_active = True
            db.commit()
            log.info(f"Admin has unbanned user {user_id}.")
            return True
        return False

    def delete_comment(self, db: Session, *, comment_id: int) -> bool:
        """
        Permanently deletes a comment from the database.
        """
        comment = db.query(Comment).get(comment_id)
        if comment:
            db.delete(comment)
            db.commit()
            log.warning(f"Admin has deleted comment {comment_id}.")
            return True
        return False

# Global service instance
admin_service = AdminService() 