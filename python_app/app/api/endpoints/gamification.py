from fastapi import APIRouter, Query, Depends
from typing import Literal
from sqlalchemy.orm import Session

from app.models import BaseResponse
from app.models.gamification import Leaderboard, AchievementShare
from app.models.leaderboard import Leaderboard, LeaderboardEntry
from app.services.gamification_service import gamification_service
from app.core.auth import get_current_active_user
from app.core.database import get_db

router = APIRouter()

@router.get("/leaderboard", response_model=Leaderboard)
def get_leaderboard(
    period: Literal["weekly", "monthly", "all_time"] = "weekly",
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get the leaderboard showing top users by water intake.
    """
    entries_data = gamification_service.get_leaderboard(db=db, period=period, limit=limit)
    
    # The service returns dicts, we need to convert them to the Pydantic model
    entries = [LeaderboardEntry(**data) for data in entries_data]

    return Leaderboard(period=period, entries=entries)

@router.get("/achievements/{achievement_id}/share", response_model=BaseResponse[AchievementShare])
async def get_achievement_share_data(
    achievement_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get shareable data for a specific earned achievement."""
    user_id = current_user["user_id"]
    share_data = await gamification_service.get_achievement_share_data(user_id, achievement_id)
    
    if not share_data:
        raise HTTPException(status_code=404, detail="Achievement not found or not earned by the user.")
        
    return BaseResponse(
        data=share_data,
        message="Achievement share data retrieved successfully."
    ) 