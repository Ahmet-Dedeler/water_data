from fastapi import APIRouter, Depends, Query
from datetime import datetime, date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.visualization_system import (
    HydrationDashboard,
    TimeSeriesData,
    PieChartData,
    BarChartData,
    GaugeData
)
from app.services.visualization_system_service import VisualizationSystemService

router = APIRouter()

# Helper to get default date range
def get_default_date_range():
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    return start_date, end_date

@router.get("/dashboards/hydration", response_model=HydrationDashboard)
async def get_hydration_dashboard(
    start_date: date = Query(None, description="Start date for the data range (YYYY-MM-DD)."),
    end_date: date = Query(None, description="End date for the data range (YYYY-MM-DD)."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all data required to render the main hydration dashboard.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        
    service = VisualizationSystemService(db)
    return await service.get_hydration_dashboard_data(
        user_id=current_user.id,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time())
    )

# --- Individual Chart Endpoints ---

@router.get("/charts/hydration-over-time", response_model=TimeSeriesData)
async def get_hydration_over_time_chart(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data specifically for the hydration over time chart.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
    
    service = VisualizationSystemService(db)
    return await service._get_hydration_over_time(
        user_id=current_user.id,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time())
    )

@router.get("/charts/drink-distribution", response_model=PieChartData)
async def get_drink_distribution_chart(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data specifically for the drink type distribution pie chart.
    """
    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()

    service = VisualizationSystemService(db)
    return await service._get_drink_type_distribution(
        user_id=current_user.id,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time())
    ) 