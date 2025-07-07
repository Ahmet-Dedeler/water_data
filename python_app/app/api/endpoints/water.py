from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date

from app.models.water import (
    WaterData, WaterListResponse, WaterSummary, 
    WaterLogCreate, WaterCreate
)
from app.models.user import User
from app.services.water_service import WaterService
from app.api.dependencies import get_db
from app.core.auth import get_current_active_user
from app.schemas.water import WaterLogCreate, WaterLogOut, WaterLogUpdate

router = APIRouter()
water_service = WaterService()

@router.get("/", response_model=WaterListResponse)
def search_waters_handler(
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None, description="Search query for name, brand, or description"),
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum health score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum health score"),
    packaging: Optional[str] = Query(None, description="Filter by packaging type"),
    lab_tested: Optional[bool] = Query(None, description="Filter by lab tested status"),
    sort_by: str = Query("score", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
):
    """
    Get all waters with comprehensive filtering, sorting, and pagination.
    This single endpoint replaces the previous basic listing and separate search endpoint.
    """
    return water_service.search_waters(
        db, query=query, brand=brand, min_score=min_score, max_score=max_score,
        packaging=packaging, lab_tested=lab_tested, sort_by=sort_by,
        sort_order=sort_order, page=page, size=size
    )

@router.get("/summary", response_model=WaterSummary)
def get_water_summary(db: Session = Depends(get_db)):
    """Get summary statistics for all waters."""
    return water_service.get_water_summary(db)

@router.get("/top", response_model=List[WaterData])
def get_top_waters(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top-rated waters."""
    return water_service.get_top_waters(db, limit=limit)

@router.get("/brands", response_model=List[str])
def get_brands(db: Session = Depends(get_db)):
    """Get a list of all distinct brands."""
    return water_service.get_brands(db)

@router.get("/packaging-types", response_model=List[str])
def get_packaging_types(db: Session = Depends(get_db)):
    """Get a list of all distinct packaging types."""
    return water_service.get_packaging_types(db)

@router.get("/{water_id}", response_model=WaterData)
def get_water_by_id(water_id: int, db: Session = Depends(get_db)):
    """Get a specific water by its ID."""
    water = water_service.get_water_by_id(db, water_id)
    if not water:
        raise HTTPException(status_code=404, detail=f"Water with ID {water_id} not found")
    return water

@router.post("/log", response_model=WaterLogOut, status_code=status.HTTP_201_CREATED)
def log_water_intake(
    log_data: WaterLogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logs a user's water intake."""
    result = water_service.log_water_intake(
        db, 
        user_id=current_user.id, 
        water_id=log_data.water_id, 
        volume=log_data.volume,
        drink_type_id=log_data.drink_type_id,
        caffeine_mg=log_data.caffeine_mg
    )
    return {
        "message": "Water intake logged successfully.",
        "log_id": result["log"].id,
        "new_achievements": result["new_achievements"]
    }

@router.post("/submit-draft", status_code=202)
def submit_water_product_draft(
    product_data: WaterCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit a new water product as a draft for admin review."""
    draft = water_service.submit_draft_product(db, user_id=current_user.id, product_data=product_data)
    return {
        "message": "Product draft submitted for review.",
        "draft_id": draft.id
    }

@router.get(
    "/logs", 
    response_model=List[WaterLogOut],
    summary="Get user's water logs",
    description="Retrieves a list of water consumption records for the current user, with optional date filtering.",
)
def read_water_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[date] = Query(None, description="Start date for filtering logs (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering logs (YYYY-MM-DD)"),
):
    return water_service.get_logs_by_user(
        db, user_id=current_user.id, start_date=start_date, end_date=end_date
    )

@router.get(
    "/logs/{log_id}", 
    response_model=WaterLogOut,
    summary="Get a specific water log",
    description="Retrieves a single water log by its ID. User must be the owner.",
    responses={
        404: {"description": "Log not found"},
        403: {"description": "Not authorized to access this log"},
    }
)
def read_water_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    log = water_service.get_log(db, log_id=log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    if log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this log")
    return log

@router.put(
    "/logs/{log_id}", 
    response_model=WaterLogOut,
    summary="Update a water log",
    description="Updates a specific water log entry by its ID. User must be the owner.",
    responses={
        404: {"description": "Log not found"},
        403: {"description": "Not authorized to update this log"},
    }
)
def update_water_log(
    log_id: int,
    log_update: WaterLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_log = water_service.get_log(db, log_id=log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Log not found")
    if db_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this log")
    return water_service.update_log(db=db, db_obj=db_log, obj_in=log_update)

@router.delete(
    "/logs/{log_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a water log",
    description="Deletes a specific water log entry by its ID. User must be the owner.",
    responses={
        204: {"description": "Log deleted successfully"},
        404: {"description": "Log not found"},
        403: {"description": "Not authorized to delete this log"},
    }
)
def delete_water_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    log = water_service.get_log(db, log_id=log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    if log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this log")
    water_service.delete_log(db, log_id=log_id)
    return

@router.get("/logs/me", response_model=List[WaterLog])
def get_user_water_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[date] = Query(None, description="Start date for filtering logs (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering logs (YYYY-MM-DD)"),
):
    return water_service.get_logs_by_user(
        db, user_id=current_user.id, start_date=start_date, end_date=end_date
    )