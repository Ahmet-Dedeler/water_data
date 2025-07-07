from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Base schema for Achievement properties
class AchievementBase(BaseModel):
    name: str
    description: str
    icon_url: Optional[str] = None
    criteria: Dict[str, Any]
    total_stages: int = 1
    secret: bool = False
    parent_id: Optional[int] = None

# Schema for creating an Achievement in the DB
class AchievementCreate(AchievementBase):
    pass

# Schema for updating an Achievement in the DB
class AchievementUpdate(AchievementBase):
    pass

# Schema for reading an Achievement from the DB
class AchievementOut(AchievementBase):
    id: int

    class Config:
        orm_mode = True

# Schema for representing a User's earned achievement
class UserAchievementOut(BaseModel):
    achievement_id: int
    current_stage: int
    earned_at: datetime
    achievement: AchievementOut

    class Config:
        orm_mode = True 