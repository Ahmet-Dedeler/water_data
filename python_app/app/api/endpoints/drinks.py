from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import date

from app.core.auth import get_current_active_user
from app.db.models import User
from app.models.drink import (
    DrinkType, DrinkTypeCreate, DrinkTypeUpdate, DrinkLog, DrinkLogCreate,
    DrinkLogUpdate, DrinkSummary, DrinkRecommendation, DrinkStats,
    DrinkCategory
)
from app.models.common import BaseResponse
from app.services.drink_service import drink_service

router = APIRouter()


# Drink Types Management

@router.get("/types", response_model=BaseResponse[List[DrinkType]])
async def get_drink_types(
    category: Optional[DrinkCategory] = Query(None, description="Filter by drink category"),
    active_only: bool = Query(True, description="Show only active drink types"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return")
):
    """Get all drink types with optional filtering."""
    try:
        drink_types = await drink_service.get_all_drink_types(
            category=category,
            active_only=active_only,
            skip=skip,
            limit=limit
        )
        
        return BaseResponse(
            data=drink_types,
            message=f"Retrieved {len(drink_types)} drink types"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drink types: {str(e)}"
        )


@router.get("/types/{drink_type_id}", response_model=BaseResponse[DrinkType])
async def get_drink_type(drink_type_id: int):
    """Get a specific drink type by ID."""
    try:
        drink_type = await drink_service.get_drink_type(drink_type_id)
        if not drink_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drink type {drink_type_id} not found"
            )
        
        return BaseResponse(
            data=drink_type,
            message="Drink type retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drink type: {str(e)}"
        )


@router.post("/types", response_model=BaseResponse[DrinkType])
async def create_drink_type(
    drink_type_data: DrinkTypeCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new drink type."""
    try:
        drink_type = await drink_service.create_drink_type(drink_type_data)
        
        return BaseResponse(
            data=drink_type,
            message=f"Drink type '{drink_type.name}' created successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating drink type: {str(e)}"
        )


@router.put("/types/{drink_type_id}", response_model=BaseResponse[DrinkType])
async def update_drink_type(
    drink_type_id: int,
    update_data: DrinkTypeUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a drink type."""
    try:
        drink_type = await drink_service.update_drink_type(drink_type_id, update_data)
        if not drink_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drink type {drink_type_id} not found"
            )
        
        return BaseResponse(
            data=drink_type,
            message="Drink type updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating drink type: {str(e)}"
        )


@router.delete("/types/{drink_type_id}", response_model=BaseResponse[dict])
async def delete_drink_type(
    drink_type_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete (deactivate) a drink type."""
    try:
        success = await drink_service.delete_drink_type(drink_type_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drink type {drink_type_id} not found"
            )
        
        return BaseResponse(
            data={"drink_type_id": drink_type_id},
            message="Drink type deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting drink type: {str(e)}"
        )


# Drink Logging

@router.post("/log", response_model=BaseResponse[DrinkLog])
async def log_drink(
    log_data: DrinkLogCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Log a drink consumption."""
    try:
        drink_log = await drink_service.log_drink(current_user.id, log_data)
        
        return BaseResponse(
            data=drink_log,
            message="Drink logged successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging drink: {str(e)}"
        )


@router.get("/logs", response_model=BaseResponse[List[DrinkLog]])
async def get_drink_logs(
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    category: Optional[DrinkCategory] = Query(None, description="Filter by drink category"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return")
):
    """Get user's drink logs with optional filtering."""
    try:
        logs = await drink_service.get_user_drink_logs(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=limit
        )
        
        return BaseResponse(
            data=logs,
            message=f"Retrieved {len(logs)} drink logs"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drink logs: {str(e)}"
        )


@router.put("/logs/{log_id}", response_model=BaseResponse[DrinkLog])
async def update_drink_log(
    log_id: int,
    update_data: DrinkLogUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a drink log entry."""
    try:
        drink_log = await drink_service.update_drink_log(
            log_id, current_user.id, update_data
        )
        if not drink_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drink log {log_id} not found"
            )
        
        return BaseResponse(
            data=drink_log,
            message="Drink log updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating drink log: {str(e)}"
        )


@router.delete("/logs/{log_id}", response_model=BaseResponse[dict])
async def delete_drink_log(
    log_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a drink log entry."""
    try:
        success = await drink_service.delete_drink_log(log_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drink log {log_id} not found"
            )
        
        return BaseResponse(
            data={"log_id": log_id},
            message="Drink log deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting drink log: {str(e)}"
        )


# Analytics and Summaries

@router.get("/summary/daily", response_model=BaseResponse[DrinkSummary])
async def get_daily_summary(
    current_user: User = Depends(get_current_active_user),
    target_date: date = Query(default_factory=date.today, description="Date for summary")
):
    """Get daily drink consumption summary."""
    try:
        summary = await drink_service.get_daily_drink_summary(
            current_user.id, target_date
        )
        
        return BaseResponse(
            data=summary,
            message=f"Daily summary for {target_date} retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving daily summary: {str(e)}"
        )


@router.get("/recommendations", response_model=BaseResponse[List[DrinkRecommendation]])
async def get_drink_recommendations(
    current_user: User = Depends(get_current_active_user)
):
    """Get personalized drink recommendations."""
    try:
        recommendations = await drink_service.get_drink_recommendations(current_user.id)
        
        return BaseResponse(
            data=recommendations,
            message=f"Retrieved {len(recommendations)} drink recommendations"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recommendations: {str(e)}"
        )


@router.get("/stats", response_model=BaseResponse[DrinkStats])
async def get_drink_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """Get drink consumption statistics."""
    try:
        stats = await drink_service.get_drink_stats()
        
        return BaseResponse(
            data=stats,
            message="Drink statistics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving drink statistics: {str(e)}"
        )


# Initialization

@router.post("/initialize", response_model=BaseResponse[dict])
async def initialize_default_drinks(
    current_user: User = Depends(get_current_active_user)
):
    """Initialize system with default drink types."""
    try:
        await drink_service.initialize_default_drink_types()
        
        return BaseResponse(
            data={"initialized": True},
            message="Default drink types initialized successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing default drinks: {str(e)}"
        )


# Categories and Information

@router.get("/categories", response_model=BaseResponse[List[str]])
async def get_drink_categories():
    """Get all available drink categories."""
    try:
        categories = [category.value for category in DrinkCategory]
        
        return BaseResponse(
            data=categories,
            message="Drink categories retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        ) 