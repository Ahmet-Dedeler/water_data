from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging
from sqlalchemy.orm import Session

from app.models import WaterData, WaterListResponse, BaseResponse
from app.services import water_service, search_service
from app.models.search import WaterLogSearchCriteria, WaterLogDetails
from app.models.user import User
from app.database.db import get_db
from app.utils.auth import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=WaterListResponse)
async def search_waters(
    query: Optional[str] = Query(None, description="Search query for name or brand"),
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum health score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum health score"),
    packaging: Optional[str] = Query(None, description="Filter by packaging type"),
    has_contaminants: Optional[bool] = Query(None, description="Filter by presence of contaminants"),
    lab_tested: Optional[bool] = Query(None, description="Filter by lab testing status"),
    sort_by: str = Query("score", description="Sort field (name, score, brand, packaging)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
):
    """Search waters with comprehensive filtering and sorting."""
    try:
        # Validate score range
        if min_score is not None and max_score is not None and min_score > max_score:
            raise HTTPException(status_code=400, detail="min_score cannot be greater than max_score")
        
        result = await water_service.search_waters(
            query=query,
            brand=brand,
            min_score=min_score,
            max_score=max_score,
            packaging=packaging,
            has_contaminants=has_contaminants,
            lab_tested=lab_tested,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching waters: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suggestions", response_model=BaseResponse[List[str]])
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(6, ge=1, le=20, description="Number of suggestions to return")
):
    """Get search suggestions for autocomplete."""
    try:
        suggestions = await search_service.get_search_suggestions(query, limit)
        return BaseResponse(
            data=suggestions,
            message="Search suggestions retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/by-ingredient/{ingredient_name}", response_model=BaseResponse[List[WaterData]])
async def search_waters_by_ingredient(ingredient_name: str):
    """Search waters containing a specific ingredient."""
    try:
        waters = await water_service.get_waters_with_ingredient(ingredient_name)
        return BaseResponse(
            data=waters,
            message=f"Waters containing {ingredient_name} retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error searching waters by ingredient: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/advanced")
async def advanced_search(
    # Text search
    query: Optional[str] = Query(None, description="Search query for name or brand"),
    brand: Optional[str] = Query(None, description="Filter by specific brand"),
    
    # Score filters
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum health score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum health score"),
    health_status: Optional[str] = Query(None, description="Health status: excellent, good, fair, poor"),
    
    # Feature filters
    packaging: Optional[str] = Query(None, description="Packaging type: plastic, glass, etc."),
    has_contaminants: Optional[bool] = Query(None, description="Has contaminants (true/false)"),
    lab_tested: Optional[bool] = Query(None, description="Lab tested (true/false)"),
    
    # Ingredient filters
    ingredient: Optional[str] = Query(None, description="Contains specific ingredient"),
    min_ingredients: Optional[int] = Query(None, ge=0, description="Minimum number of ingredients"),
    max_ingredients: Optional[int] = Query(None, ge=0, description="Maximum number of ingredients"),
    
    # Sorting and pagination
    sort_by: str = Query("score", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
):
    """Advanced search with multiple filter options."""
    try:
        # Start with basic search
        results = await water_service.search_waters(
            query=query,
            brand=brand,
            min_score=min_score,
            max_score=max_score,
            packaging=packaging,
            has_contaminants=has_contaminants,
            lab_tested=lab_tested,
            sort_by=sort_by,
            sort_order=sort_order,
            page=1,  # Get all results first for additional filtering
            size=1000  # Large number to get all results
        )
        
        filtered_waters = results.data
        
        # Apply additional filters
        if health_status:
            health_filtered = await water_service.get_waters_by_health_status(health_status)
            health_ids = {w.id for w in health_filtered}
            filtered_waters = [w for w in filtered_waters if w.id in health_ids]
        
        if ingredient:
            ingredient_waters = await water_service.get_waters_with_ingredient(ingredient)
            ingredient_ids = {w.id for w in ingredient_waters}
            filtered_waters = [w for w in filtered_waters if w.id in ingredient_ids]
        
        if min_ingredients is not None:
            filtered_waters = [w for w in filtered_waters if len(w.ingredients) >= min_ingredients]
        
        if max_ingredients is not None:
            filtered_waters = [w for w in filtered_waters if len(w.ingredients) <= max_ingredients]
        
        # Apply pagination
        total = len(filtered_waters)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_results = filtered_waters[start_idx:end_idx]
        
        return {
            "success": True,
            "message": "Advanced search completed successfully",
            "data": paginated_results,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size,
            "filters_applied": {
                "query": query,
                "brand": brand,
                "score_range": f"{min_score or 0}-{max_score or 100}",
                "health_status": health_status,
                "packaging": packaging,
                "has_contaminants": has_contaminants,
                "lab_tested": lab_tested,
                "ingredient": ingredient,
                "ingredient_count_range": f"{min_ingredients or 0}-{max_ingredients or 'unlimited'}"
            }
        }
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/filters/options")
async def get_filter_options():
    """Get available filter options for search."""
    try:
        brands = await water_service.get_brands()
        packaging_types = await water_service.get_packaging_types()
        
        # Get ingredient names from a sample of waters
        all_waters = await water_service.get_all_waters()
        ingredients = set()
        for water in all_waters.data[:100]:  # Sample first 100 waters
            for ingredient in water.ingredients:
                if ingredient.name:
                    ingredients.add(ingredient.name)
        
        return BaseResponse(
            data={
                "brands": brands,
                "packaging_types": packaging_types,
                "health_statuses": ["excellent", "good", "fair", "poor"],
                "sort_fields": ["name", "score", "brand", "packaging"],
                "sort_orders": ["asc", "desc"],
                "common_ingredients": sorted(list(ingredients))[:50]  # Top 50 most common
            },
            message="Filter options retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/me/water-logs", response_model=List[WaterLogDetails])
def search_my_water_logs(
    criteria: WaterLogSearchCriteria,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform an advanced search on the current user's water logs.
    """
    logs = water_service.search_water_logs(
        db=db,
        user_id=current_user.id,
        criteria=criteria,
        skip=(page - 1) * size,
        limit=size
    )
    # Convert DB models to Pydantic models
    return [
        WaterLogDetails(
            id=log.id,
            date=log.date,
            volume=log.volume,
            water_data=log.water  # This works because of the joinedload in the service
        )
        for log in logs
    ] 