from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, case, text
from collections import defaultdict

from app.models.leaderboard import (
    Leaderboard, LeaderboardEntry, LeaderboardType, LeaderboardPeriod,
    LeaderboardStats, CompetitiveLeaderboard
)
from app.db import models as db_models
from app.services.user_service import user_service
from app.services.achievement_service import achievement_service


class LeaderboardService:
    """Enhanced leaderboard service with competitive features"""
    
    def __init__(self):
        self.user_service = user_service
        self.achievement_service = achievement_service

    def get_date_range(self, period: LeaderboardPeriod) -> tuple[Optional[datetime], datetime]:
        """Get start and end dates for a given period"""
        end_date = datetime.utcnow()
        
        if period == LeaderboardPeriod.DAILY:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == LeaderboardPeriod.WEEKLY:
            start_date = end_date - timedelta(days=7)
        elif period == LeaderboardPeriod.CURRENT_WEEK:
            start_date = end_date - timedelta(days=end_date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == LeaderboardPeriod.MONTHLY:
            start_date = end_date - timedelta(days=30)
        elif period == LeaderboardPeriod.CURRENT_MONTH:
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # ALL_TIME
            start_date = None
            
        return start_date, end_date

    def format_value(self, value: float, leaderboard_type: LeaderboardType) -> str:
        """Format value for display based on leaderboard type"""
        if leaderboard_type == LeaderboardType.CONSUMPTION:
            return f"{value/1000:.1f}L" if value >= 1000 else f"{value:.0f}ml"
        elif leaderboard_type in [LeaderboardType.STREAK, LeaderboardType.WEEKLY_GOALS, LeaderboardType.MONTHLY_GOALS]:
            return f"{int(value)} days" if value != 1 else "1 day"
        elif leaderboard_type in [LeaderboardType.POINTS, LeaderboardType.XP]:
            return f"{int(value):,} pts" if leaderboard_type == LeaderboardType.POINTS else f"{int(value):,} XP"
        elif leaderboard_type == LeaderboardType.CONSISTENCY:
            return f"{value:.1f}%"
        else:
            return str(value)

    def get_badge(self, rank: int, leaderboard_type: LeaderboardType) -> Optional[str]:
        """Get badge for top performers"""
        if rank == 1:
            return "🥇 Champion"
        elif rank == 2:
            return "🥈 Runner-up"
        elif rank == 3:
            return "🥉 Third Place"
        elif rank <= 5:
            return "⭐ Top 5"
        elif rank <= 10:
            return "🔥 Top 10"
        else:
            return None

    def get_leaderboard(
        self,
        db: Session,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod,
        limit: int = 20,
        current_user_id: Optional[int] = None
    ) -> Leaderboard:
        """Get enhanced leaderboard with competitive features"""
        
        start_date, end_date = self.get_date_range(period)
        
        # Build base query based on leaderboard type
        if leaderboard_type == LeaderboardType.CONSUMPTION:
            query = self._build_consumption_query(db, start_date, end_date)
        elif leaderboard_type == LeaderboardType.STREAK:
            query = self._build_streak_query(db, start_date, end_date)
        elif leaderboard_type == LeaderboardType.POINTS:
            query = self._build_points_query(db, start_date, end_date)
        elif leaderboard_type == LeaderboardType.XP:
            query = self._build_xp_query(db, start_date, end_date)
        elif leaderboard_type == LeaderboardType.CONSISTENCY:
            query = self._build_consistency_query(db, start_date, end_date)
        elif leaderboard_type == LeaderboardType.WEEKLY_GOALS:
            query = self._build_weekly_goals_query(db, start_date, end_date)
        elif leaderboard_type == LeaderboardType.MONTHLY_GOALS:
            query = self._build_monthly_goals_query(db, start_date, end_date)
        else:
            query = self._build_consumption_query(db, start_date, end_date)
        
        # Get total participants
        total_participants = query.count()
        
        # Get top entries
        top_entries = query.limit(limit).all()
        
        # Get current user's rank if specified
        user_rank = None
        user_entry = None
        if current_user_id:
            user_rank = self._get_user_rank(db, current_user_id, leaderboard_type, period)
            if user_rank and user_rank > limit:
                user_entry = self._get_user_entry(db, current_user_id, leaderboard_type, period, user_rank)
        
        # Build leaderboard entries
        entries = []
        for i, row in enumerate(top_entries):
            entry = LeaderboardEntry(
                rank=i + 1,
                user_id=row.user_id,
                username=row.username,
                value=row.value,
                display_value=self.format_value(row.value, leaderboard_type),
                profile_picture_url=getattr(row, 'profile_picture_url', None),
                level=getattr(row, 'level', None),
                streak=getattr(row, 'current_streak', None),
                badge=self.get_badge(i + 1, leaderboard_type),
                additional_stats=self._get_additional_stats(db, row.user_id, leaderboard_type)
            )
            entries.append(entry)
        
        return Leaderboard(
            period=period,
            leaderboard_type=leaderboard_type,
            entries=entries,
            total_participants=total_participants,
            user_rank=user_rank,
            user_entry=user_entry
        )

    def _build_consumption_query(self, db: Session, start_date: Optional[datetime], end_date: datetime):
        """Build query for consumption leaderboard"""
        query = db.query(
            db_models.User.id.label('user_id'),
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level,
            db_models.UserProfile.current_streak,
            func.coalesce(func.sum(db_models.WaterLog.volume), 0).label('value')
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id
        ).outerjoin(
            db_models.WaterLog, db_models.User.id == db_models.WaterLog.user_id
        )
        
        if start_date:
            query = query.filter(db_models.WaterLog.date >= start_date)
        query = query.filter(db_models.WaterLog.date <= end_date)
        
        return query.group_by(
            db_models.User.id, db_models.User.username, 
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level, db_models.UserProfile.current_streak
        ).order_by(desc('value'))

    def _build_streak_query(self, db: Session, start_date: Optional[datetime], end_date: datetime):
        """Build query for streak leaderboard"""
        return db.query(
            db_models.User.id.label('user_id'),
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level,
            db_models.UserProfile.current_streak,
            db_models.UserProfile.current_streak.label('value')
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id
        ).order_by(desc('value'))

    def _build_points_query(self, db: Session, start_date: Optional[datetime], end_date: datetime):
        """Build query for points leaderboard"""
        return db.query(
            db_models.User.id.label('user_id'),
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level,
            db_models.UserProfile.current_streak,
            db_models.UserProfile.points.label('value')
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id
        ).order_by(desc('value'))

    def _build_xp_query(self, db: Session, start_date: Optional[datetime], end_date: datetime):
        """Build query for XP leaderboard"""
        return db.query(
            db_models.User.id.label('user_id'),
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level,
            db_models.UserProfile.current_streak,
            db_models.UserProfile.xp.label('value')
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id
        ).order_by(desc('value'))

    def _build_consistency_query(self, db: Session, start_date: Optional[datetime], end_date: datetime):
        """Build query for consistency leaderboard (percentage of days with logs)"""
        if not start_date:
            start_date = end_date - timedelta(days=30)  # Default to last 30 days
        
        total_days = (end_date - start_date).days
        
        return db.query(
            db_models.User.id.label('user_id'),
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level,
            db_models.UserProfile.current_streak,
            ((func.count(func.distinct(func.date(db_models.WaterLog.date))) / total_days) * 100).label('value')
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id
        ).outerjoin(
            db_models.WaterLog, db_models.User.id == db_models.WaterLog.user_id
        ).filter(
            db_models.WaterLog.date >= start_date,
            db_models.WaterLog.date <= end_date
        ).group_by(
            db_models.User.id, db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level, db_models.UserProfile.current_streak
        ).order_by(desc('value'))

    def _build_weekly_goals_query(self, db: Session, start_date: Optional[datetime], end_date: datetime):
        """Build query for weekly goals met leaderboard"""
        return db.query(
            db_models.User.id.label('user_id'),
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level,
            db_models.UserProfile.current_streak,
            func.count(db_models.DailyStreak.id).label('value')
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id
        ).outerjoin(
            db_models.DailyStreak, db_models.User.id == db_models.DailyStreak.user_id
        ).filter(
            db_models.DailyStreak.goal_met == True,
            db_models.DailyStreak.date >= (start_date or end_date - timedelta(days=7)),
            db_models.DailyStreak.date <= end_date
        ).group_by(
            db_models.User.id, db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level, db_models.UserProfile.current_streak
        ).order_by(desc('value'))

    def _build_monthly_goals_query(self, db: Session, start_date: Optional[datetime], end_date: datetime):
        """Build query for monthly goals met leaderboard"""
        return db.query(
            db_models.User.id.label('user_id'),
            db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level,
            db_models.UserProfile.current_streak,
            func.count(db_models.DailyStreak.id).label('value')
        ).join(
            db_models.UserProfile, db_models.User.id == db_models.UserProfile.user_id
        ).outerjoin(
            db_models.DailyStreak, db_models.User.id == db_models.DailyStreak.user_id
        ).filter(
            db_models.DailyStreak.goal_met == True,
            db_models.DailyStreak.date >= (start_date or end_date - timedelta(days=30)),
            db_models.DailyStreak.date <= end_date
        ).group_by(
            db_models.User.id, db_models.User.username,
            db_models.UserProfile.profile_picture_url,
            db_models.UserProfile.level, db_models.UserProfile.current_streak
        ).order_by(desc('value'))

    def _get_user_rank(self, db: Session, user_id: int, leaderboard_type: LeaderboardType, period: LeaderboardPeriod) -> Optional[int]:
        """Get user's rank in the leaderboard"""
        start_date, end_date = self.get_date_range(period)
        
        # This is a simplified version - in a real implementation, you'd need to run the full query
        # and find the user's position
        return None  # Placeholder

    def _get_user_entry(self, db: Session, user_id: int, leaderboard_type: LeaderboardType, period: LeaderboardPeriod, rank: int) -> Optional[LeaderboardEntry]:
        """Get user's leaderboard entry"""
        # This would build the user's entry similar to the main query
        return None  # Placeholder

    def _get_additional_stats(self, db: Session, user_id: int, leaderboard_type: LeaderboardType) -> Dict[str, Any]:
        """Get additional stats for a user"""
        stats = {}
        
        # Get user's recent activity
        recent_logs = db.query(func.count(db_models.WaterLog.id)).filter(
            db_models.WaterLog.user_id == user_id,
            db_models.WaterLog.date >= datetime.utcnow() - timedelta(days=7)
        ).scalar()
        
        stats['logs_this_week'] = recent_logs or 0
        
        # Get user's achievements count
        achievements_count = db.query(func.count(db_models.UserAchievement.id)).filter(
            db_models.UserAchievement.user_id == user_id
        ).scalar()
        
        stats['total_achievements'] = achievements_count or 0
        
        return stats

    def get_leaderboard_stats(self, db: Session) -> LeaderboardStats:
        """Get overall leaderboard statistics"""
        today = datetime.utcnow().date()
        week_start = datetime.utcnow() - timedelta(days=7)
        
        total_users = db.query(func.count(db_models.User.id)).scalar()
        
        active_today = db.query(func.count(func.distinct(db_models.WaterLog.user_id))).filter(
            func.date(db_models.WaterLog.date) == today
        ).scalar()
        
        active_this_week = db.query(func.count(func.distinct(db_models.WaterLog.user_id))).filter(
            db_models.WaterLog.date >= week_start
        ).scalar()
        
        avg_consumption = db.query(func.avg(db_models.WaterLog.volume)).filter(
            db_models.WaterLog.date >= week_start
        ).scalar()
        
        return LeaderboardStats(
            total_users=total_users or 0,
            active_users_today=active_today or 0,
            active_users_this_week=active_this_week or 0,
            average_daily_consumption=avg_consumption or 0.0
        )

    def get_competitive_leaderboard(self, db: Session, current_user_id: Optional[int] = None) -> CompetitiveLeaderboard:
        """Get comprehensive competitive leaderboard"""
        
        # Main leaderboard (consumption)
        main_leaderboard = self.get_leaderboard(
            db, LeaderboardType.CONSUMPTION, LeaderboardPeriod.WEEKLY, 20, current_user_id
        )
        
        # Mini leaderboards for different categories
        mini_leaderboards = [
            self.get_leaderboard(db, LeaderboardType.STREAK, LeaderboardPeriod.ALL_TIME, 10, current_user_id),
            self.get_leaderboard(db, LeaderboardType.POINTS, LeaderboardPeriod.MONTHLY, 10, current_user_id),
            self.get_leaderboard(db, LeaderboardType.CONSISTENCY, LeaderboardPeriod.MONTHLY, 10, current_user_id),
        ]
        
        # Get stats
        stats = self.get_leaderboard_stats(db)
        
        # Get recent achievements
        recent_achievements = db.query(
            db_models.UserAchievement.user_id,
            db_models.User.username,
            db_models.Achievement.name,
            db_models.UserAchievement.earned_at
        ).join(
            db_models.User, db_models.UserAchievement.user_id == db_models.User.id
        ).join(
            db_models.Achievement, db_models.UserAchievement.achievement_id == db_models.Achievement.id
        ).filter(
            db_models.UserAchievement.earned_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(db_models.UserAchievement.earned_at)).limit(10).all()
        
        achievements_this_week = [
            {
                'user_id': a.user_id,
                'username': a.username,
                'achievement_name': a.name,
                'earned_at': a.earned_at
            }
            for a in recent_achievements
        ]
        
        return CompetitiveLeaderboard(
            main_leaderboard=main_leaderboard,
            mini_leaderboards=mini_leaderboards,
            stats=stats,
            achievements_this_week=achievements_this_week,
            trending_users=[]  # Could implement trending logic here
        )


# Global service instance
leaderboard_service = LeaderboardService() 