from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.leaderboard import (
    Leaderboard, LeaderboardEntry, LeaderboardType, LeaderboardPeriod,
    LeaderboardStats, CompetitiveLeaderboard
)
from app.services.leaderboard_service import leaderboard_service

router = APIRouter()

@router.get("/", response_model=Leaderboard)
def get_leaderboard(
    leaderboard_type: LeaderboardType = Query(LeaderboardType.CONSUMPTION, description="Type of leaderboard"),
    period: LeaderboardPeriod = Query(LeaderboardPeriod.WEEKLY, description="Time period for leaderboard"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get leaderboard with competitive features"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=leaderboard_type,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/competitive", response_model=CompetitiveLeaderboard)
def get_competitive_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive competitive leaderboard with multiple categories"""
    return leaderboard_service.get_competitive_leaderboard(
        db=db,
        current_user_id=current_user.id
    )

@router.get("/stats", response_model=LeaderboardStats)
def get_leaderboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overall leaderboard statistics"""
    return leaderboard_service.get_leaderboard_stats(db)

@router.get("/consumption", response_model=Leaderboard)
def get_consumption_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.WEEKLY, description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get water consumption leaderboard"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=LeaderboardType.CONSUMPTION,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/streaks", response_model=Leaderboard)
def get_streak_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.ALL_TIME, description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get streak leaderboard"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=LeaderboardType.STREAK,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/points", response_model=Leaderboard)
def get_points_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.MONTHLY, description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get points leaderboard"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=LeaderboardType.POINTS,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/xp", response_model=Leaderboard)
def get_xp_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.MONTHLY, description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get XP leaderboard"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=LeaderboardType.XP,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/consistency", response_model=Leaderboard)
def get_consistency_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.MONTHLY, description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get consistency leaderboard (percentage of days with water logs)"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=LeaderboardType.CONSISTENCY,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/weekly-goals", response_model=Leaderboard)
def get_weekly_goals_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.CURRENT_WEEK, description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get weekly goals met leaderboard"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=LeaderboardType.WEEKLY_GOALS,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/monthly-goals", response_model=Leaderboard)
def get_monthly_goals_leaderboard(
    period: LeaderboardPeriod = Query(LeaderboardPeriod.CURRENT_MONTH, description="Time period"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get monthly goals met leaderboard"""
    return leaderboard_service.get_leaderboard(
        db=db,
        leaderboard_type=LeaderboardType.MONTHLY_GOALS,
        period=period,
        limit=limit,
        current_user_id=current_user.id
    )

@router.get("/my-rank/{leaderboard_type}/{period}")
def get_my_rank(
    leaderboard_type: LeaderboardType,
    period: LeaderboardPeriod,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's rank in a specific leaderboard"""
    rank = leaderboard_service._get_user_rank(
        db=db,
        user_id=current_user.id,
        leaderboard_type=leaderboard_type,
        period=period
    )
    
    if rank is None:
        raise HTTPException(status_code=404, detail="User not found in leaderboard")
    
    return {
        "user_id": current_user.id,
        "rank": rank,
        "leaderboard_type": leaderboard_type,
        "period": period
    } 