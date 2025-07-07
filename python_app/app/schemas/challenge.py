from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ChallengeType(str, Enum):
    TOTAL_VOLUME = "total_volume"
    STREAK_DAYS = "streak_days"
    DAILY_GOAL = "daily_goal"
    CONSISTENCY = "consistency"
    SOCIAL_SHARING = "social_sharing"
    WEEKLY_GOALS = "weekly_goals"
    MONTHLY_GOALS = "monthly_goals"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTREME = "extreme"

class ChallengeCategory(str, Enum):
    HYDRATION = "hydration"
    STREAK = "streak"
    SOCIAL = "social"
    CONSISTENCY = "consistency"

class ChallengeBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    challenge_type: ChallengeType
    goal: float = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    is_public: bool = True
    max_participants: Optional[int] = Field(None, gt=0)
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    reward_points: int = Field(0, ge=0)
    reward_xp: int = Field(0, ge=0)
    category: Optional[ChallengeCategory] = None
    is_team_challenge: bool = False
    team_size: int = Field(1, ge=1, le=10)
    entry_fee_points: int = Field(0, ge=0)

class ChallengeCreate(ChallengeBase):
    pass

class ChallengeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    max_participants: Optional[int] = Field(None, gt=0)
    difficulty_level: Optional[DifficultyLevel] = None
    reward_points: Optional[int] = Field(None, ge=0)
    reward_xp: Optional[int] = Field(None, ge=0)

class Challenge(ChallengeBase):
    id: int
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    participant_count: Optional[int] = 0
    completion_rate: Optional[float] = 0.0
    
    class Config:
        from_attributes = True

class UserChallengeBase(BaseModel):
    user_id: int
    challenge_id: int
    progress: float = 0.0

class UserChallengeCreate(UserChallengeBase):
    pass

class UserChallengeUpdate(BaseModel):
    progress: Optional[float] = None
    is_abandoned: Optional[bool] = None

class UserChallenge(UserChallengeBase):
    id: int
    completed_at: Optional[datetime] = None
    joined_at: datetime
    is_abandoned: bool = False
    abandoned_at: Optional[datetime] = None
    final_rank: Optional[int] = None
    points_earned: int = 0
    xp_earned: int = 0
    team_id: Optional[int] = None
    challenge: Challenge
    
    class Config:
        from_attributes = True

class ChallengeTeamBase(BaseModel):
    challenge_id: int
    name: str = Field(..., min_length=3, max_length=50)
    leader_id: int

class ChallengeTeamCreate(ChallengeTeamBase):
    pass

class ChallengeTeam(ChallengeTeamBase):
    id: int
    total_progress: float = 0.0
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime
    member_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class ChallengeInvitationBase(BaseModel):
    challenge_id: int
    invitee_id: int

class ChallengeInvitationCreate(ChallengeInvitationBase):
    pass

class ChallengeInvitation(ChallengeInvitationBase):
    id: int
    inviter_id: int
    status: str = "pending"
    created_at: datetime
    responded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChallengeCommentBase(BaseModel):
    challenge_id: int
    content: str = Field(..., min_length=1, max_length=500)

class ChallengeCommentCreate(ChallengeCommentBase):
    pass

class ChallengeComment(ChallengeCommentBase):
    id: int
    user_id: int
    created_at: datetime
    username: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChallengeLeaderboard(BaseModel):
    challenge_id: int
    challenge_name: str
    entries: List[dict]
    total_participants: int
    completion_rate: float

class ChallengeStats(BaseModel):
    total_challenges: int
    active_challenges: int
    completed_challenges: int
    user_participation_rate: float
    average_completion_rate: float
    most_popular_challenge_type: str

class ChallengeProgress(BaseModel):
    challenge_id: int
    challenge_name: str
    progress: float
    goal: float
    percentage_complete: float
    days_remaining: int
    is_completed: bool
    rank: Optional[int] = None
    points_earned: int = 0
    xp_earned: int = 0 