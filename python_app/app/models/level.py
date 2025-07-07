from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class RewardType(str, Enum):
    POINTS = "points"
    BADGE = "badge"
    FEATURE_UNLOCK = "feature_unlock"
    TITLE = "title"
    COSMETIC = "cosmetic"

class XPSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    base_xp: int = Field(0, ge=0)
    multiplier: float = Field(1.0, ge=0.1, le=10.0)
    daily_limit: Optional[int] = Field(None, ge=1)
    is_active: bool = True

class XPSourceCreate(XPSourceBase):
    pass

class XPSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    base_xp: Optional[int] = Field(None, ge=0)
    multiplier: Optional[float] = Field(None, ge=0.1, le=10.0)
    daily_limit: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None

class XPSource(XPSourceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserXPLogBase(BaseModel):
    user_id: int
    xp_source_id: int
    xp_gained: int = Field(..., ge=1)
    description: Optional[str] = Field(None, max_length=200)

class UserXPLogCreate(UserXPLogBase):
    pass

class UserXPLog(UserXPLogBase):
    id: int
    created_at: datetime
    xp_source: Optional[XPSource] = None
    
    class Config:
        from_attributes = True

class LevelRewardBase(BaseModel):
    level: int = Field(..., ge=1)
    reward_type: RewardType
    reward_value: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=200)
    is_claimed_automatically: bool = True

class LevelRewardCreate(LevelRewardBase):
    pass

class LevelRewardUpdate(BaseModel):
    level: Optional[int] = Field(None, ge=1)
    reward_type: Optional[RewardType] = None
    reward_value: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=200)
    is_claimed_automatically: Optional[bool] = None

class LevelReward(LevelRewardBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLevelRewardBase(BaseModel):
    user_id: int
    level_reward_id: int

class UserLevelRewardCreate(UserLevelRewardBase):
    pass

class UserLevelReward(UserLevelRewardBase):
    id: int
    claimed_at: datetime
    level_reward: Optional[LevelReward] = None
    
    class Config:
        from_attributes = True

class PrestigeLevelBase(BaseModel):
    user_id: int
    prestige_level: int = Field(0, ge=0)
    total_resets: int = Field(0, ge=0)
    prestige_points: int = Field(0, ge=0)
    last_prestige_at: Optional[datetime] = None

class PrestigeLevelCreate(PrestigeLevelBase):
    pass

class PrestigeLevelUpdate(BaseModel):
    prestige_level: Optional[int] = Field(None, ge=0)
    total_resets: Optional[int] = Field(None, ge=0)
    prestige_points: Optional[int] = Field(None, ge=0)
    last_prestige_at: Optional[datetime] = None

class PrestigeLevel(PrestigeLevelBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LevelMilestoneBase(BaseModel):
    level: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    badge_emoji: Optional[str] = Field(None, max_length=10)
    xp_bonus_multiplier: float = Field(1.0, ge=1.0, le=5.0)
    special_privileges: Optional[Dict[str, Any]] = None

class LevelMilestoneCreate(LevelMilestoneBase):
    pass

class LevelMilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    badge_emoji: Optional[str] = Field(None, max_length=10)
    xp_bonus_multiplier: Optional[float] = Field(None, ge=1.0, le=5.0)
    special_privileges: Optional[Dict[str, Any]] = None

class LevelMilestone(LevelMilestoneBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SeasonalXPBoostBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    multiplier: float = Field(..., ge=1.0, le=10.0)
    start_date: datetime
    end_date: datetime
    is_active: bool = True

class SeasonalXPBoostCreate(SeasonalXPBoostBase):
    pass

class SeasonalXPBoostUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    multiplier: Optional[float] = Field(None, ge=1.0, le=10.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class SeasonalXPBoost(SeasonalXPBoostBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLevelInfo(BaseModel):
    user_id: int
    level: int
    current_xp: int
    total_xp: int
    xp_to_next_level: int
    level_progress_percentage: float
    prestige_level: int = 0
    prestige_points: int = 0
    level_title: Optional[str] = None
    level_badge: Optional[str] = None
    xp_multiplier: float = 1.0
    next_milestone: Optional[LevelMilestone] = None

class LevelProgressHistory(BaseModel):
    user_id: int
    level_history: List[Dict[str, Any]]
    xp_history: List[Dict[str, Any]]
    milestones_reached: List[LevelMilestone]
    total_xp_gained: int
    average_daily_xp: float

class XPBreakdown(BaseModel):
    user_id: int
    total_xp: int
    xp_by_source: Dict[str, int]
    daily_xp_last_30_days: List[Dict[str, Any]]
    top_xp_sources: List[Dict[str, Any]]
    xp_multipliers_active: List[Dict[str, Any]]

class LevelLeaderboard(BaseModel):
    entries: List[Dict[str, Any]]
    user_rank: Optional[int] = None
    total_users: int
    leaderboard_type: str  # 'level', 'xp', 'prestige'

class LevelStats(BaseModel):
    total_users: int
    average_level: float
    highest_level: int
    total_xp_distributed: int
    active_xp_sources: int
    level_distribution: Dict[str, int]
    prestige_users: int 