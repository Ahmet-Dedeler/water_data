from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from enum import Enum

class DailyWaterConsumption(BaseModel):
    date: date
    total_consumption: float

class WaterConsumptionAnalytics(BaseModel):
    total_consumption: float
    average_daily_consumption: float
    daily_consumption: List[DailyWaterConsumption]

class TimePeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    ALL_TIME = "all_time"

class LeaderboardType(str, Enum):
    CONSUMPTION = "consumption"
    STREAK = "streak"

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    value: float = Field(..., description="The value for the leaderboard, e.g., total volume or streak length.")
    streak: Optional[int] = None

class DailyCaffeineIntake(BaseModel):
    date: date
    total_caffeine_mg: int

class CaffeineIntakeAnalytics(BaseModel):
    total_caffeine_mg: int
    average_daily_caffeine_mg: float
    daily_intake: List[DailyCaffeineIntake] 