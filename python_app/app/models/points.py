from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class TransactionType(str, Enum):
    EARNED = "earned"
    SPENT = "spent"
    BONUS = "bonus"
    PENALTY = "penalty"
    TRANSFER = "transfer"

class RewardType(str, Enum):
    COSMETIC = "cosmetic"
    FEATURE = "feature"
    BADGE = "badge"
    XP_BOOST = "xp_boost"
    ITEM = "item"
    TITLE = "title"

class BonusType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    STREAK = "streak"
    SEASONAL = "seasonal"
    EVENT = "event"

class PointSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    base_points: int = Field(0, ge=0)
    multiplier: float = Field(1.0, ge=0.1, le=10.0)
    daily_limit: Optional[int] = Field(None, ge=1)
    weekly_limit: Optional[int] = Field(None, ge=1)
    is_active: bool = True

class PointSourceCreate(PointSourceBase):
    pass

class PointSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    base_points: Optional[int] = Field(None, ge=0)
    multiplier: Optional[float] = Field(None, ge=0.1, le=10.0)
    daily_limit: Optional[int] = Field(None, ge=1)
    weekly_limit: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None

class PointSource(PointSourceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PointTransactionBase(BaseModel):
    user_id: int
    point_source_id: Optional[int] = None
    transaction_type: TransactionType
    points_amount: int
    balance_after: int
    description: Optional[str] = Field(None, max_length=200)
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[int] = None

class PointTransactionCreate(BaseModel):
    point_source_id: Optional[int] = None
    transaction_type: TransactionType
    points_amount: int
    description: Optional[str] = Field(None, max_length=200)
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[int] = None

class PointTransaction(PointTransactionBase):
    id: int
    created_at: datetime
    point_source: Optional[PointSource] = None
    
    class Config:
        from_attributes = True

class PointRewardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    cost_points: int = Field(..., ge=1)
    reward_type: RewardType
    reward_data: Optional[Dict[str, Any]] = None
    is_available: bool = True
    is_limited: bool = False
    stock_quantity: Optional[int] = Field(None, ge=0)
    purchase_limit_per_user: Optional[int] = Field(None, ge=1)
    required_level: int = Field(1, ge=1)
    category: Optional[str] = Field(None, max_length=50)

class PointRewardCreate(PointRewardBase):
    pass

class PointRewardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    cost_points: Optional[int] = Field(None, ge=1)
    is_available: Optional[bool] = None
    is_limited: Optional[bool] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    purchase_limit_per_user: Optional[int] = Field(None, ge=1)
    required_level: Optional[int] = Field(None, ge=1)

class PointReward(PointRewardBase):
    id: int
    created_at: datetime
    purchases_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class PointPurchaseBase(BaseModel):
    user_id: int
    point_reward_id: int
    points_spent: int
    quantity: int = 1

class PointPurchaseCreate(BaseModel):
    point_reward_id: int
    quantity: int = 1

class PointPurchase(PointPurchaseBase):
    id: int
    purchase_date: datetime
    is_active: bool = True
    point_reward: Optional[PointReward] = None
    
    class Config:
        from_attributes = True

class PointBonusBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    bonus_type: BonusType
    bonus_amount: int = Field(..., ge=1)
    multiplier: float = Field(1.0, ge=1.0, le=10.0)
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    requirements: Optional[Dict[str, Any]] = None

class PointBonusCreate(PointBonusBase):
    pass

class PointBonusUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    bonus_amount: Optional[int] = Field(None, ge=1)
    multiplier: Optional[float] = Field(None, ge=1.0, le=10.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class PointBonus(PointBonusBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserPointBonusBase(BaseModel):
    user_id: int
    point_bonus_id: int
    points_awarded: int

class UserPointBonusCreate(UserPointBonusBase):
    pass

class UserPointBonus(UserPointBonusBase):
    id: int
    claimed_at: datetime
    point_bonus: Optional[PointBonus] = None
    
    class Config:
        from_attributes = True

class PointTransferBase(BaseModel):
    sender_id: int
    receiver_id: int
    points_amount: int = Field(..., ge=1)
    message: Optional[str] = Field(None, max_length=200)
    transfer_fee: int = Field(0, ge=0)

class PointTransferCreate(BaseModel):
    receiver_id: int
    points_amount: int = Field(..., ge=1)
    message: Optional[str] = Field(None, max_length=200)

class PointTransfer(PointTransferBase):
    id: int
    status: str = "completed"
    created_at: datetime
    sender_username: Optional[str] = None
    receiver_username: Optional[str] = None
    
    class Config:
        from_attributes = True

class PointMilestoneBase(BaseModel):
    points_threshold: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    reward_type: str = Field(..., min_length=1, max_length=50)
    reward_value: str = Field(..., min_length=1)
    badge_emoji: Optional[str] = Field(None, max_length=10)
    is_active: bool = True

class PointMilestoneCreate(PointMilestoneBase):
    pass

class PointMilestoneUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    reward_type: Optional[str] = Field(None, min_length=1, max_length=50)
    reward_value: Optional[str] = Field(None, min_length=1)
    badge_emoji: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None

class PointMilestone(PointMilestoneBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserPointMilestoneBase(BaseModel):
    user_id: int
    point_milestone_id: int

class UserPointMilestone(UserPointMilestoneBase):
    id: int
    achieved_at: datetime
    point_milestone: Optional[PointMilestone] = None
    
    class Config:
        from_attributes = True

class PointBalance(BaseModel):
    user_id: int
    total_points: int
    lifetime_earned: int
    lifetime_spent: int
    pending_points: int = 0
    available_points: int
    last_transaction_date: Optional[datetime] = None

class PointsBreakdown(BaseModel):
    user_id: int
    current_balance: int
    points_by_source: Dict[str, int]
    recent_transactions: List[PointTransaction]
    daily_points_last_30_days: List[Dict[str, Any]]
    top_earning_sources: List[Dict[str, Any]]
    spending_categories: Dict[str, int]

class PointsLeaderboard(BaseModel):
    entries: List[Dict[str, Any]]
    user_rank: Optional[int] = None
    total_users: int
    leaderboard_type: str  # 'total', 'earned', 'spent'

class PointsStats(BaseModel):
    total_users: int
    total_points_in_circulation: int
    total_points_earned: int
    total_points_spent: int
    average_user_balance: float
    active_point_sources: int
    available_rewards: int
    total_transactions: int
    most_popular_reward: Optional[str] = None

class PointsEconomy(BaseModel):
    total_supply: int
    circulation_rate: float
    inflation_rate: float
    top_earners: List[Dict[str, Any]]
    top_spenders: List[Dict[str, Any]]
    reward_popularity: List[Dict[str, Any]]
    source_effectiveness: List[Dict[str, Any]]

class DailyPointsSummary(BaseModel):
    user_id: int
    date: datetime
    points_earned: int
    points_spent: int
    net_points: int
    transactions_count: int
    top_source: Optional[str] = None
    bonuses_claimed: int = 0 