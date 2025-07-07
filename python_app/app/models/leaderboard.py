from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class LeaderboardType(str, Enum):
    CONSUMPTION = "consumption"
    STREAK = "streak"
    POINTS = "points"
    XP = "xp"
    CONSISTENCY = "consistency"
    WEEKLY_GOALS = "weekly_goals"
    MONTHLY_GOALS = "monthly_goals"

class LeaderboardPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"
    CURRENT_WEEK = "current_week"
    CURRENT_MONTH = "current_month"

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    value: float
    display_value: str  # Formatted value for display (e.g., "2.5L", "15 days")
    profile_picture_url: Optional[str] = None
    level: Optional[int] = None
    streak: Optional[int] = None
    change_from_previous: Optional[int] = None  # Rank change from previous period
    badge: Optional[str] = None  # Special badge for top performers
    additional_stats: Optional[Dict[str, Any]] = None

class Leaderboard(BaseModel):
    period: LeaderboardPeriod
    leaderboard_type: LeaderboardType
    entries: List[LeaderboardEntry]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_participants: int
    user_rank: Optional[int] = None  # Current user's rank if not in top entries
    user_entry: Optional[LeaderboardEntry] = None  # Current user's entry if not in top

class LeaderboardStats(BaseModel):
    total_users: int
    active_users_today: int
    active_users_this_week: int
    average_daily_consumption: float
    top_performer_this_week: Optional[str] = None
    most_improved_user: Optional[str] = None

class CompetitiveLeaderboard(BaseModel):
    """Enhanced leaderboard with competitive features"""
    main_leaderboard: Leaderboard
    mini_leaderboards: List[Leaderboard]  # Different categories
    stats: LeaderboardStats
    achievements_this_week: List[Dict[str, Any]]
    trending_users: List[LeaderboardEntry]  # Users with biggest improvements 