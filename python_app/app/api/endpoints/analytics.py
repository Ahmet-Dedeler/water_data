from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Literal
import logging
from datetime import date

from app.models import BaseResponse, WaterData
from app.models.analytics import UserAnalytics, GlobalAnalytics, ProgressAnalytics, ConsumptionHeatmap, BrandAnalytics, GlobalStats, ProgressOverTime, TimeSeriesAnalytics
from app.services import water_service, data_service
from app.services.analytics_service import analytics_service
from app.core.auth import get_current_active_user, get_current_admin_user
from app.api.dependencies import get_db
from app.models.user import User
from app.api import dependencies
from app.schemas.analytics import UserStats, TimeSeriesData, TimePeriod, LeaderboardEntry, WaterConsumptionAnalytics, LeaderboardType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/global", response_model=GlobalStats)
def get_global_analytics(db: Session = Depends(get_db)):
    """Get aggregated, anonymous, platform-wide analytics."""
    try:
        return analytics_service.get_global_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not retrieve global analytics.")


@router.get("/me/heatmap", response_model=ConsumptionHeatmap)
def get_my_consumption_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a heatmap of the current user's water consumption for the last year."""
    try:
        heatmap_data = analytics_service.get_consumption_heatmap(db, current_user.id)
        return ConsumptionHeatmap(heatmap=heatmap_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not retrieve consumption heatmap.")


@router.get("/me/progress", response_model=ProgressOverTime)
def get_my_progress_over_time(
    db: Session = Depends(get_db),
    granularity: Literal["weekly", "monthly"] = Query("weekly", description="The time granularity for the data."),
    current_user: User = Depends(get_current_active_user)
):
    """Get personalized consumption progress over time."""
    try:
        # The service implementation is basic, but the endpoint is ready for enhancement
        progress_data = analytics_service.get_progress_over_time(db, current_user.id, granularity)
        return progress_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not retrieve progress data.")


@router.get("/users/me/analytics", response_model=BaseResponse[UserAnalytics])
async def get_my_personal_analytics(current_user: dict = Depends(get_current_active_user)):
    """Get personalized consumption analytics for the current user."""
    try:
        user_id = current_user["user_id"]
        analytics = await analytics_service.get_user_analytics(user_id)
        if not analytics:
            # This can happen if the user has no recent logs
            raise HTTPException(
                status_code=404,
                detail="No recent consumption data found to generate analytics."
            )
        
        return BaseResponse(
            data=analytics,
            message="Personal analytics retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personal analytics for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/brand/{brand_name}", response_model=BrandAnalytics)
def get_my_brand_specific_analytics(
    brand_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get personalized consumption analytics for a specific brand."""
    try:
        analytics = analytics_service.get_brand_analytics_for_user(db, current_user.id, brand_name)
        if not analytics:
            raise HTTPException(
                status_code=404,
                detail=f"No consumption data found for brand '{brand_name}'."
            )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not retrieve brand analytics.")


@router.get("/water/{water_id}", response_model=BaseResponse[Dict])
async def get_water_analytics(water_id: int):
    """Get detailed analytics for a specific water."""
    try:
        analytics = await water_service.get_water_analytics(water_id)
        if not analytics:
            raise HTTPException(status_code=404, detail=f"Water with ID {water_id} not found")
        
        return BaseResponse(
            data=analytics,
            message="Water analytics retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting water analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/overview")
async def get_analytics_overview():
    """Get overall analytics and statistics."""
    try:
        stats = await data_service.get_statistics()
        
        # Additional analytics
        all_waters = await data_service.get_all_water_data()
        
        # Score distribution
        score_ranges = {
            "90-100": len([w for w in all_waters if 90 <= w.score <= 100]),
            "80-89": len([w for w in all_waters if 80 <= w.score < 90]),
            "70-79": len([w for w in all_waters if 70 <= w.score < 80]),
            "60-69": len([w for w in all_waters if 60 <= w.score < 70]),
            "50-59": len([w for w in all_waters if 50 <= w.score < 60]),
            "0-49": len([w for w in all_waters if w.score < 50])
        }
        
        # Top and bottom performers
        top_performers = sorted(all_waters, key=lambda x: x.score, reverse=True)[:5]
        bottom_performers = sorted(all_waters, key=lambda x: x.score)[:5]
        
        analytics_data = {
            "summary": stats,
            "score_distribution": score_ranges,
            "top_performers": [
                {"id": w.id, "name": w.name, "brand": w.brand.name, "score": w.score}
                for w in top_performers
            ],
            "bottom_performers": [
                {"id": w.id, "name": w.name, "brand": w.brand.name, "score": w.score}
                for w in bottom_performers
            ]
        }
        
        return BaseResponse(
            data=analytics_data,
            message="Analytics overview retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trends")
async def get_trends_analysis():
    """Get trends and patterns in water data."""
    try:
        all_waters = await data_service.get_all_water_data()
        
        # Contaminant analysis
        contaminant_frequency = {}
        for water in all_waters:
            for ingredient in water.contaminants:
                if ingredient.name:
                    contaminant_frequency[ingredient.name] = contaminant_frequency.get(ingredient.name, 0) + 1
        
        most_common_contaminants = sorted(
            contaminant_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Nutrient analysis
        nutrient_frequency = {}
        for water in all_waters:
            for ingredient in water.nutrients:
                if ingredient.name:
                    nutrient_frequency[ingredient.name] = nutrient_frequency.get(ingredient.name, 0) + 1
        
        most_common_nutrients = sorted(
            nutrient_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Lab testing trends
        lab_tested_by_brand = {}
        for water in all_waters:
            brand = water.brand.name
            if brand not in lab_tested_by_brand:
                lab_tested_by_brand[brand] = {"total": 0, "lab_tested": 0}
            
            lab_tested_by_brand[brand]["total"] += 1
            if water.lab_tested:
                lab_tested_by_brand[brand]["lab_tested"] += 1
        
        # Calculate lab testing percentages
        brand_lab_testing = {}
        for brand, data in lab_tested_by_brand.items():
            if data["total"] >= 3:  # Only brands with 3+ products
                percentage = (data["lab_tested"] / data["total"]) * 100
                brand_lab_testing[brand] = {
                    "total_products": data["total"],
                    "lab_tested_products": data["lab_tested"],
                    "lab_testing_percentage": round(percentage, 1)
                }
        
        trends_data = {
            "most_common_contaminants": [
                {"name": name, "frequency": freq} 
                for name, freq in most_common_contaminants
            ],
            "most_common_nutrients": [
                {"name": name, "frequency": freq} 
                for name, freq in most_common_nutrients
            ],
            "lab_testing_by_brand": brand_lab_testing,
            "overall_trends": {
                "total_waters_analyzed": len(all_waters),
                "average_ingredients_per_water": round(
                    sum(len(w.ingredients) for w in all_waters) / len(all_waters), 1
                ),
                "waters_with_contaminants": len([w for w in all_waters if len(w.contaminants) > 0]),
                "contaminant_free_percentage": round(
                    len([w for w in all_waters if len(w.contaminants) == 0]) / len(all_waters) * 100, 1
                )
            }
        }
        
        return BaseResponse(
            data=trends_data,
            message="Trends analysis retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting trends analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/brand/{brand_name}")
async def get_brand_analytics(brand_name: str):
    """Get detailed analytics for a specific brand."""
    try:
        brand_waters = await water_service.get_waters_by_brand(brand_name)
        if not brand_waters:
            raise HTTPException(status_code=404, detail=f"No waters found for brand: {brand_name}")
        
        # Calculate brand statistics
        scores = [w.score for w in brand_waters]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        # Product performance
        top_product = max(brand_waters, key=lambda x: x.score)
        worst_product = min(brand_waters, key=lambda x: x.score)
        
        # Lab testing analysis
        lab_tested_count = len([w for w in brand_waters if w.lab_tested])
        lab_testing_percentage = (lab_tested_count / len(brand_waters)) * 100
        
        # Packaging analysis
        packaging_breakdown = {}
        for water in brand_waters:
            packaging = water.packaging
            packaging_breakdown[packaging] = packaging_breakdown.get(packaging, 0) + 1
        
        # Contaminant analysis
        total_contaminants = sum(len(w.contaminants) for w in brand_waters)
        avg_contaminants = total_contaminants / len(brand_waters)
        
        # Health status breakdown
        health_status_count = {}
        for water in brand_waters:
            status = water.health_status
            health_status_count[status] = health_status_count.get(status, 0) + 1
        
        brand_analytics = {
            "brand_name": brand_name,
            "total_products": len(brand_waters),
            "performance_metrics": {
                "average_score": round(avg_score, 2),
                "min_score": min_score,
                "max_score": max_score,
                "score_range": max_score - min_score
            },
            "top_product": {
                "id": top_product.id,
                "name": top_product.name,
                "score": top_product.score
            },
            "worst_product": {
                "id": worst_product.id,
                "name": worst_product.name,
                "score": worst_product.score
            },
            "lab_testing": {
                "lab_tested_products": lab_tested_count,
                "lab_testing_percentage": round(lab_testing_percentage, 1)
            },
            "packaging_breakdown": packaging_breakdown,
            "health_analysis": {
                "average_contaminants_per_product": round(avg_contaminants, 2),
                "health_status_breakdown": health_status_count
            },
            "products": [
                {
                    "id": w.id,
                    "name": w.name,
                    "score": w.score,
                    "health_status": w.health_status,
                    "lab_tested": w.lab_tested,
                    "packaging": w.packaging,
                    "contaminants_count": len(w.contaminants),
                    "nutrients_count": len(w.nutrients)
                }
                for w in sorted(brand_waters, key=lambda x: x.score, reverse=True)
            ]
        }
        
        return BaseResponse(
            data=brand_analytics,
            message=f"Analytics for {brand_name} retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/compare")
async def compare_analytics(
    water_ids: List[int] = Query(..., description="List of water IDs to compare")
):
    """Get comparative analytics for multiple waters."""
    try:
        if len(water_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 water IDs required for comparison")
        
        if len(water_ids) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 waters can be compared at once")
        
        waters = await water_service.compare_waters(water_ids)
        
        if len(waters) != len(water_ids):
            missing_ids = set(water_ids) - {w.id for w in waters}
            raise HTTPException(status_code=404, detail=f"Waters not found: {list(missing_ids)}")
        
        # Comparison analytics
        scores = [w.score for w in waters]
        best_water = max(waters, key=lambda x: x.score)
        worst_water = min(waters, key=lambda x: x.score)
        
        comparison_data = {
            "waters_compared": len(waters),
            "best_performer": {
                "id": best_water.id,
                "name": best_water.name,
                "brand": best_water.brand.name,
                "score": best_water.score
            },
            "worst_performer": {
                "id": worst_water.id,
                "name": worst_water.name,
                "brand": worst_water.brand.name,
                "score": worst_water.score
            },
            "score_statistics": {
                "average": round(sum(scores) / len(scores), 2),
                "min": min(scores),
                "max": max(scores),
                "range": max(scores) - min(scores)
            },
            "detailed_comparison": [
                {
                    "id": w.id,
                    "name": w.name,
                    "brand": w.brand.name,
                    "score": w.score,
                    "health_status": w.health_status,
                    "lab_tested": w.lab_tested,
                    "packaging": w.packaging,
                    "microplastics_risk": w.microplastics_risk,
                    "contaminants_count": len(w.contaminants),
                    "nutrients_count": len(w.nutrients),
                    "total_ingredients": len(w.ingredients)
                }
                for w in sorted(waters, key=lambda x: x.score, reverse=True)
            ]
        }
        
        return BaseResponse(
            data=comparison_data,
            message="Comparative analytics retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comparative analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/timeseries", response_model=TimeSeriesAnalytics)
def get_user_intake_timeseries(
    start_date: date,
    end_date: date,
    granularity: Literal["daily", "weekly", "monthly"] = "daily",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a time series of the current user's water intake over a specified period.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date.")
    
    if (end_date - start_date).days > 366: # Limit to one year of data
        raise HTTPException(status_code=400, detail="Date range cannot exceed one year.")

    return analytics_service.get_water_intake_timeseries(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )


@router.get("/{user_id}/timeseries", response_model=TimeSeriesAnalytics, dependencies=[Depends(get_current_admin_user)])
def get_any_user_intake_timeseries(
    user_id: int,
    start_date: date,
    end_date: date,
    granularity: Literal["daily", "weekly", "monthly"] = "daily",
    db: Session = Depends(get_db)
):
    """
    [Admin] Get a time series of any user's water intake.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date.")

    return analytics_service.get_water_intake_timeseries(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )


@router.get(
    "/me/stats",
    response_model=UserStats,
    summary="Get current user's statistics",
    description="Retrieves a comprehensive statistics report for the currently authenticated user.",
)
def get_user_statistics(
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    return analytics_service.get_user_stats(db, user_id=current_user.id)


@router.get(
    "/me/timeseries",
    response_model=List[TimeSeriesData],
    summary="Get user's time series data",
    description="Retrieves time series data of water intake for the current user, aggregated by day, week, or month.",
)
def get_user_timeseries_data(
    period: TimePeriod = Query(TimePeriod.WEEK, description="The time period to aggregate data by."),
    current_user: User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    return analytics_service.get_user_intake_timeseries(db, user_id=current_user.id, period=period)


@router.get(
    "/leaderboard",
    response_model=List[LeaderboardEntry],
    summary="Get the leaderboard",
    description="Retrieves the public leaderboard, ranking users by water intake over different time periods.",
)
def get_leaderboard(
    leaderboard_type: LeaderboardType = Query(LeaderboardType.CONSUMPTION, description="The type of leaderboard to retrieve."),
    period: TimePeriod = Query(TimePeriod.WEEK, description="The time period for the leaderboard."),
    limit: int = Query(10, ge=1, le=100, description="The number of users to return."),
    db: Session = Depends(dependencies.get_db),
):
    """
    Retrieves the public leaderboard. Can be sorted by consumption or streak.
    """
    return analytics_service.get_leaderboard(
        db, leaderboard_type=leaderboard_type, period=period, limit=limit
    )


@router.get("/water-consumption/", response_model=WaterConsumptionAnalytics)
def get_water_consumption_analytics(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get water consumption analytics for the current user between two dates.
    """
    try:
        analytics_data = analytics_service.get_water_consumption_analytics(
            db, user_id=current_user.id, start_date=start_date, end_date=end_date
        )
        return analytics_data
    except Exception as e:
        logger.error(
            f"Error getting water consumption analytics for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Could not retrieve water consumption analytics."
        ) 