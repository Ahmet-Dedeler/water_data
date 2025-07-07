import logging
import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict

from app.db import models as db_models
from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.schemas.achievement import AchievementCreate, AchievementUpdate
from app.services.social_service import social_service # Use singleton
from app.core.websockets import manager
from app.services import notification_service
from app.services.base_service import BaseService
# UserService might not be directly needed if we query UserProfile directly

logger = logging.getLogger(__name__)

class AchievementService(BaseService[Achievement, AchievementCreate, AchievementUpdate]):
    def __init__(self):
        # In a real app, this would be handled by a proper DI system
        self.social_service = social_service

    def get_visible_achievements(self, db: Session) -> List[Achievement]:
        """Gets all non-secret achievements."""
        return db.query(Achievement).filter(Achievement.secret == False).all()

    def get_user_achievements(self, db: Session, *, user_id: int) -> List[UserAchievement]:
        return db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()

    def get_achievement(self, db: Session, *, achievement_id: int) -> Achievement:
        return db.query(Achievement).get(achievement_id)

    def grant_achievement_stage(self, db: Session, *, user: User, achievement: Achievement) -> UserAchievement:
        """Grants a single stage of an achievement to a user."""
        user_achievement = db.query(UserAchievement).filter_by(user_id=user.id, achievement_id=achievement.id).first()

        if not user_achievement:
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id, current_stage=1)
            db.add(user_achievement)
            logger.info(f"Achievement '{achievement.name}' (Stage 1) granted to user {user.id}")
        else:
            if user_achievement.current_stage < achievement.total_stages:
                user_achievement.current_stage += 1
                logger.info(f"Achievement '{achievement.name}' (Stage {user_achievement.current_stage}) granted to user {user.id}")

        db.commit()
        db.refresh(user_achievement)
        
        # Trigger a notification for the new achievement/stage
        notification_service.create_achievement_notification(
            db,
            user_id=user.id,
            achievement_name=f"{achievement.name} - Stage {user_achievement.current_stage}"
        )
        return user_achievement

    def check_and_grant_achievements(self, db: Session, *, user_id: int):
        """
        Checks all achievement conditions for a user and grants them if met.
        This is a data-driven approach that uses the `criteria` JSON field.
        """
        user = db.query(User).get(user_id)
        if not user:
            return

        all_achievements = db.query(Achievement).all()
        user_achievements = {ua.achievement_id: ua for ua in self.get_user_achievements(db, user_id=user_id)}

        for achievement in all_achievements:
            user_achievement = user_achievements.get(achievement.id)
            current_stage = user_achievement.current_stage if user_achievement else 0
            
            if current_stage >= achievement.total_stages:
                continue

            criteria = achievement.criteria
            criteria_type = criteria.get("type")
            target_values = criteria.get("values") # e.g., [1, 10, 50, 100]

            if not criteria_type or not isinstance(target_values, list) or current_stage >= len(target_values):
                continue
            
            target_value = target_values[current_stage]
            user_metric = 0

            if criteria_type == "log_count":
                user_metric = len(user.water_logs)
            elif criteria_type == "total_volume":
                user_metric = db.query(func.sum(WaterLog.volume_ml)).filter(WaterLog.user_id == user_id).scalar() or 0
            # Add other criteria types like 'streak_days' here in the future

            if user_metric >= target_value:
                self.grant_achievement_stage(db, user=user, achievement=achievement)

    def _get_stage_value(self, criteria: Dict, current_stage: int):
        """Get the target value for the next stage of a multi-stage achievement."""
        if "stages" in criteria and isinstance(criteria["stages"], list):
            if current_stage < len(criteria["stages"]):
                return criteria["stages"][current_stage]
        elif current_stage == 0: # For single-stage achievements
            return criteria.get("value")
        return None

    async def _award_achievement(
        self, db: Session, user_id: int, achievement: Achievement, new_stage: int
    ) -> bool:
        """Awards an achievement or advances its stage, and creates a social activity."""
        user_achievement = db.query(db_models.UserAchievement).filter_by(
            user_id=user_id, achievement_id=achievement.id
        ).first()

        if user_achievement:
            user_achievement.stage = new_stage
        else:
            user_achievement = db_models.UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                stage=new_stage
            )
            db.add(user_achievement)
        
        logger.info(f"User {user_id} advanced to stage {new_stage} for achievement: {achievement.name}")

        await self.social_service.create_activity(
            db,
            user_id=user_id,
            activity_type="achievement_unlocked",
            data={
                "achievement_name": achievement.name,
                "stage": new_stage
            }
        )

        # Send real-time notification via WebSocket
        notification_message = json.dumps({
            "type": "achievement_unlocked",
            "achievement": {
                "name": achievement.name,
                "description": achievement.description,
                "stage": new_stage
            }
        })
        await manager.send_personal_message(notification_message, str(user_id))
        
        # The commit will be handled by the calling service (e.g., WaterService)
        return True

achievement_service = AchievementService() 