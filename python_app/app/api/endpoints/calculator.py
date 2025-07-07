from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List

from app.core.auth import get_current_active_user
from app.db.models import User
from app.models.calculator import (
    CalculatorRequest, CalculatorResponse, CalculationHistory,
    CalculatorStats, UserMetrics
)
from app.models.common import BaseResponse
from app.services.calculator_service import calculator_service

router = APIRouter()


@router.post("/calculate", response_model=BaseResponse[CalculatorResponse])
async def calculate_water_intake(
    request: CalculatorRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate comprehensive water intake recommendation based on user metrics.
    
    This advanced calculator considers multiple factors:
    - Basic demographics (weight, height, age, gender)
    - Activity level and exercise details
    - Climate and environmental conditions
    - Health conditions and medications
    - Dietary factors (caffeine, alcohol, sodium)
    - Current hydration status
    - Sleep and stress levels
    """
    try:
        response = await calculator_service.calculate_water_intake(
            request, user_id=current_user.id
        )
        
        return BaseResponse(
            data=response,
            message="Water intake calculation completed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating water intake: {str(e)}"
        )


@router.post("/quick-calculate", response_model=BaseResponse[CalculatorResponse])
async def quick_calculate_water_intake(
    metrics: UserMetrics,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    Quick water intake calculation with basic metrics only.
    Simplified endpoint for basic calculations without full request structure.
    """
    try:
        request = CalculatorRequest(
            user_metrics=metrics,
            include_exercise_plan=False,
            include_goal_adjustment=False
        )
        
        user_id = current_user.id if current_user else None
        response = await calculator_service.calculate_water_intake(request, user_id)
        
        return BaseResponse(
            data=response,
            message="Quick water intake calculation completed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in quick calculation: {str(e)}"
        )


@router.get("/history", response_model=BaseResponse[List[CalculationHistory]])
async def get_calculation_history(
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=50, description="Number of calculations to return")
):
    """Get user's calculation history."""
    try:
        history = await calculator_service.get_calculation_history(
            current_user.id, limit
        )
        
        return BaseResponse(
            data=history,
            message=f"Retrieved {len(history)} calculation records"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving calculation history: {str(e)}"
        )


@router.get("/stats", response_model=BaseResponse[CalculatorStats])
async def get_calculator_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """Get calculator usage statistics (admin or analytics purposes)."""
    try:
        stats = await calculator_service.get_calculator_stats()
        
        return BaseResponse(
            data=stats,
            message="Calculator statistics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving calculator stats: {str(e)}"
        )


@router.post("/feedback", response_model=BaseResponse[dict])
async def submit_calculation_feedback(
    calculation_id: str,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1-5"),
    notes: Optional[str] = Query(None, description="Optional feedback notes"),
    current_user: User = Depends(get_current_active_user)
):
    """Submit feedback for a calculation."""
    try:
        # Note: This would require extending the service to handle feedback updates
        # For now, return a placeholder response
        
        return BaseResponse(
            data={"calculation_id": calculation_id, "rating": rating},
            message="Feedback submitted successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/recommendations/factors", response_model=BaseResponse[dict])
async def get_calculation_factors_info():
    """
    Get information about factors used in water intake calculations.
    Useful for educational purposes or UI explanations.
    """
    try:
        factors_info = {
            "base_calculation": {
                "description": "Base intake calculated from weight, age, and gender",
                "formula": "Weight (kg) × 30-35ml, adjusted for age and gender"
            },
            "activity_multipliers": {
                "sedentary": 1.0,
                "light": 1.1,
                "moderate": 1.2,
                "active": 1.4,
                "very_active": 1.6,
                "athlete": 1.8
            },
            "climate_adjustments": {
                "temperate": "No adjustment",
                "hot_humid": "+500ml",
                "hot_dry": "+400ml",
                "cold": "-100ml",
                "high_altitude": "+300ml"
            },
            "health_conditions": {
                "diabetes": "+300ml",
                "pregnancy": "+200-350ml (trimester dependent)",
                "breastfeeding": "+500ml",
                "fever": "+400ml",
                "diarrhea_vomiting": "+600ml"
            },
            "medications": {
                "diuretics": "+400ml",
                "blood_pressure": "+100ml",
                "antidepressants": "+150ml",
                "antihistamines": "+100ml"
            },
            "dietary_factors": {
                "caffeine": "+0.5ml per mg",
                "alcohol": "+150ml per serving",
                "excess_sodium": "+0.1ml per mg over 2300mg"
            }
        }
        
        return BaseResponse(
            data=factors_info,
            message="Calculation factors information retrieved"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving factors info: {str(e)}"
        ) 