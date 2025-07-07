from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class LeaderboardEntry(BaseModel):
    """Represents a single entry in a leaderboard."""
    user_id: int = Field(..., description="The ID of the user.")
    username: str = Field(..., description="The username of the user.")
    rank: int = Field(..., description="The user's rank on the leaderboard.")
    total_volume: float = Field(..., description="The total volume of water consumed by the user.")

class Leaderboard(BaseModel):
    """Represents the entire leaderboard for a specific period."""
    period: str = Field(..., description="The period the leaderboard covers (e.g., 'weekly', 'all_time').")
    entries: List[LeaderboardEntry] = Field(..., description="The list of entries in the leaderboard.")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the leaderboard was generated.")

class AchievementShare(BaseModel):
    """Represents the data for sharing a specific earned achievement."""
    achievement_name: str = Field(..., description="The name of the achievement.")
    achievement_description: str = Field(..., description="The description of the achievement.")
    username: str = Field(..., description="The username of the user who earned it.")
    earned_at: datetime = Field(..., description="When the achievement was earned.")
    stage: int = Field(..., description="The stage of the achievement that was earned.")
    share_url: str = Field(..., description="A URL to view the achievement (conceptual).") 