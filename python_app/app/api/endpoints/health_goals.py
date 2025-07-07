from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
import logging
from sqlalchemy.orm import Session

from app.models.health_goal import (
    HealthGoal, HealthGoalCreate, HealthGoalUpdate, HealthGoalStatus,
    ProgressEntry, HealthGoalSummary, HealthGoalStats, HealthGoalListResponse,
    ProgressLogResponse, HealthGoalResponse, HealthGoalType
)
from app.services.health_goal_service import health_goal_service
from app.core.auth import get_current_user
from app.models.user import User
from app.models.common import BaseResponse
from app.api import dependencies

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=HealthGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a health goal",
    description="Creates a new health goal for the currently authenticated user.",
    responses={
        400: {"description": "Invalid goal type or date range"},
    }
)
async def create_health_goal(
    goal_data: HealthGoalCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new health goal for the authenticated user.
    - Define goal type, target, and timeline
    - Set custom milestones or use defaults
    """
    try:
        goal = await health_goal_service.create_health_goal(current_user.id, goal_data)
        return HealthGoalResponse(
            success=True,
            message="Health goal created successfully",
            goal=goal
        )
    except Exception as e:
        logger.error(f"Error creating health goal for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health goal"
        )


@router.get(
    "/",
    response_model=HealthGoalListResponse,
    summary="List user's health goals",
    description="Retrieves a list of all health goals for the currently authenticated user.",
)
async def get_user_health_goals(
    status: Optional[HealthGoalStatus] = Query(None, description="Filter goals by status"),
    goal_type: Optional[HealthGoalType] = Query(None, description="Filter goals by type"),
    sort_by: str = Query("priority", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_user)
):
    """
    Get all health goals for the authenticated user.
    - Filter by status and type
    - Sort results
    """
    try:
        goals = await health_goal_service.get_all_user_goals(
            current_user.id, status, goal_type, sort_by, sort_order
        )
        return HealthGoalListResponse(
            success=True,
            message="User health goals retrieved successfully",
            goals=goals,
            total=len(goals)
        )
    except Exception as e:
        logger.error(f"Error getting goals for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health goals"
        )


@router.get("/stats", response_model=BaseResponse[HealthGoalStats])
async def get_health_goal_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get overall health goal statistics for the user.
    - Track progress, achievements, and streaks
    """
    try:
        stats = await health_goal_service.get_user_goal_stats(current_user.id)
        return BaseResponse(
            data=stats,
            message="Health goal stats retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health goal stats"
        )


@router.get(
    "/{goal_id}",
    response_model=HealthGoalResponse,
    summary="Get a specific health goal",
    description="Retrieves a single health goal by its ID. The user must own this goal.",
    responses={
        404: {"description": "Health goal not found"},
        403: {"description": "User does not have permission to access this goal"},
    }
)
async def get_health_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific health goal by its ID."""
    try:
        goal = await health_goal_service.get_health_goal(goal_id, current_user.id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health goal not found")
        
        return HealthGoalResponse(
            success=True,
            message="Health goal retrieved successfully",
            goal=goal
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goal {goal_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health goal"
        )


@router.put(
    "/{goal_id}",
    response_model=HealthGoalResponse,
    summary="Update a health goal",
    description="Updates an existing health goal by its ID. The user must own this goal.",
    responses={
        404: {"description": "Health goal not found"},
        403: {"description": "User does not have permission to update this goal"},
    }
)
async def update_health_goal(
    goal_id: str,
    update_data: HealthGoalUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an existing health goal."""
    try:
        goal = await health_goal_service.update_health_goal(goal_id, current_user.id, update_data)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health goal not found")
        
        return HealthGoalResponse(
            success=True,
            message="Health goal updated successfully",
            goal=goal
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal {goal_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update health goal"
        )


@router.delete(
    "/{goal_id}",
    response_model=BaseResponse,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a health goal",
    description="Deletes a health goal by its ID. The user must own this goal.",
    responses={
        204: {"description": "Health goal deleted successfully"},
        404: {"description": "Health goal not found"},
        403: {"description": "User does not have permission to delete this goal"},
    }
)
async def delete_health_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a health goal."""
    try:
        success = await health_goal_service.delete_health_goal(goal_id, current_user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health goal not found")
        
        return BaseResponse(
            message="Health goal deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal {goal_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete health goal"
        )


@router.post("/{goal_id}/progress", response_model=ProgressLogResponse)
async def log_health_goal_progress(
    goal_id: str,
    entry: ProgressEntry,
    current_user: User = Depends(get_current_user)
):
    """
    Log progress for a health goal.
    - Submitting progress may unlock achievements.
    """
    try:
        measurement, new_achievements = await health_goal_service.log_progress(goal_id, current_user.id, entry)
        
        if not measurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health goal not found")
            
        goal = await health_goal_service.get_health_goal(goal_id, current_user.id)

        return ProgressLogResponse(
            success=True,
            message="Progress logged successfully",
            measurement=measurement,
            goal_progress=goal.progress,
            new_achievements=new_achievements,
            milestone_reached=next((m for m in goal.milestones if m.achieved and m.achieved_at.date() == datetime.utcnow().date()), None)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging progress for goal {goal_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log progress"
        )


@router.get("/{goal_id}/progress", response_model=BaseResponse)
async def get_health_goal_progress_history(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get the progress measurement history for a specific goal."""
    try:
        goal = await health_goal_service.get_health_goal(goal_id, current_user.id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health goal not found")
            
        return BaseResponse(
            data={
                "measurements": goal.measurements[offset : offset + limit],
                "total": len(goal.measurements)
            },
            message="Progress history retrieved"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress history for goal {goal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get progress history"
        )
        

@router.get("/achievements/all", response_model=BaseResponse)
async def get_all_user_achievements(
    current_user: User = Depends(get_current_user)
):
    """Get all achievements for the authenticated user across all goals."""
    try:
        achievements = await health_goal_service._load_achievements()
        user_achievements = [a for a in achievements if a['user_id'] == current_user.id]
        
        return BaseResponse(
            data={
                "achievements": user_achievements,
                "total": len(user_achievements)
            },
            message="All user achievements retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting all achievements for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get all user achievements"
        ) 