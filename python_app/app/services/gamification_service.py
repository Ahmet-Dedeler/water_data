import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.gamification import Leaderboard, LeaderboardEntry, AchievementShare
from app.services.user_service import user_service
from app.services.achievement_service import achievement_service
from app.models import User as db_models

logger = logging.getLogger(__name__)

class GamificationService:
    def __init__(self):
        self.water_logs_file = Path(__file__).parent.parent / "data" / "user_water_logs.json"

    async def _read_user_logs(self) -> List[Dict]:
        try:
            with open(self.water_logs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    async def get_leaderboard(
        self,
        db: Session,
        period: str = "weekly",
        limit: int = 20
    ) -> List[dict]:
        """
        Get the leaderboard for a given period.
        Periods can be 'weekly', 'monthly', or 'all_time'.
        """
        end_date = datetime.utcnow()
        if period == "weekly":
            start_date = end_date - timedelta(days=end_date.weekday())
        elif period == "monthly":
            start_date = end_date.replace(day=1)
        else: # all_time
            start_date = None

        query = db.query(
            db_models.User.id,
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            func.sum(db_models.WaterLog.volume).label("total_volume")
        ).join(
            db_models.WaterLog, db_models.User.id == db_models.WaterLog.user_id
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id, isouter=True
        )

        if start_date:
            query = query.filter(db_models.WaterLog.date >= start_date)
        
        leaderboard_data = query.group_by(
            db_models.User.id, db_models.User.username, db_models.UserProfile.profile_picture_url
        ).order_by(
            desc("total_volume")
        ).limit(limit).all()

        return [
            {
                "rank": i + 1,
                "user_id": row.id,
                "username": row.username,
                "profile_picture_url": row.profile_picture_url,
                "total_volume": row.total_volume
            }
            for i, row in enumerate(leaderboard_data)
        ]

    async def get_achievement_share_data(self, user_id: int, achievement_id: str) -> Optional[AchievementShare]:
        """Prepare the data for sharing a specific earned achievement."""
        user = await user_service.get_user_by_id(user_id)
        if not user:
            return None
        
        user_achievements = await achievement_service.get_user_achievements(user_id)
        user_achievement = next((ua for ua in user_achievements if ua.achievement_id == achievement_id), None)
        
        if not user_achievement:
            return None # User hasn't earned this achievement
            
        all_achievements = await achievement_service.get_achievements()
        achievement_details = next((a for a in all_achievements if a.id == achievement_id), None)

        if not achievement_details:
            return None # Should not happen if data is consistent

        # In a real app, this URL would point to a public page for the achievement
        share_url = f"https://water-app.example.com/shared/achievement/{user.id}/{achievement_id}"

        return AchievementShare(
            achievement_name=achievement_details.name,
            achievement_description=achievement_details.description,
            username=user.username,
            earned_at=user_achievement.earned_at,
            stage=user_achievement.stage,
            share_url=share_url
        )


gamification_service = GamificationService() 