from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
import logging
from sqlalchemy.orm import Session

from app.models.achievement import UserAchievementDetail
from app.services.achievement_service import achievement_service
from app.core.auth import get_current_user
from app.models.user import User
from app.api import dependencies
from app.schemas.achievement import AchievementOut, UserAchievementOut

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/",
    response_model=List[AchievementOut],
    summary="List all available achievements",
    description="Retrieves a list of all public (non-secret) achievements defined in the system.",
)
def get_all_achievements(db: Session = Depends(dependencies.get_db)):
    return achievement_service.get_visible_achievements(db)

@router.get(
    "/me",
    response_model=List[UserAchievementOut],
    summary="List user's earned achievements",
    description="Retrieves a list of all achievements earned by the currently authenticated user, including their current stage.",
)
def get_user_achievements(
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db)
):
    return achievement_service.get_user_achievements(db, user_id=current_user.id)

@router.get(
    "/{achievement_id}",
    response_model=AchievementOut,
    summary="Get a specific achievement",
    description="Retrieves the details of a specific achievement by its ID.",
    responses={
        404: {"description": "Achievement not found"},
    }
)
def get_achievement(
    achievement_id: int,
    db: Session = Depends(dependencies.get_db)
):
    achievement = achievement_service.get_achievement(db, achievement_id=achievement_id)
    if not achievement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement not found")
    return achievement

@router.get("/", response_model=List[UserAchievementDetail])
async def get_my_achievements(
    current_user: User = Depends(get_current_user)
):
    """
    Get all achievements earned by the authenticated user.
    """
    try:
        user_achievements = await achievement_service.get_user_achievements(current_user.id)
        all_achievements = await achievement_service.get_achievements()
        
        all_achievements_map = {ach.id: ach for ach in all_achievements}
        
        detailed_achievements = []
        for ua in user_achievements:
            achievement_details = all_achievements_map.get(ua.achievement_id)
            if achievement_details:
                detailed_achievements.append(
                    UserAchievementDetail(
                        **achievement_details.dict(),
                        date_earned=ua.date_earned
                    )
                )
        
        return detailed_achievements
    except Exception as e:
        logger.error(f"Error getting achievements for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve achievements"
        ) 