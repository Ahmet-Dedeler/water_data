from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.water_quality_service import WaterQualityService
from app.schemas.water_quality import (
    WaterSourceCreate, WaterSourceUpdate, WaterSourceResponse,
    WaterQualityTestCreate, WaterQualityTestUpdate, WaterQualityTestResponse,
    ContaminationReportCreate, ContaminationReportUpdate, ContaminationReportResponse,
    WaterQualityAlertCreate, WaterQualityAlertUpdate, WaterQualityAlertResponse,
    WaterFilterMaintenanceCreate, WaterFilterMaintenanceUpdate, WaterFilterMaintenanceResponse,
    WaterQualityPreferencesCreate, WaterQualityPreferencesUpdate, WaterQualityPreferencesResponse,
    WaterQualityAnalytics, WaterQualityTrend, WaterQualitySummary
)

router = APIRouter()

def get_water_quality_service(db: Session = Depends(get_db)) -> WaterQualityService:
    return WaterQualityService(db)

# Water Source Endpoints
@router.post("/sources", response_model=WaterSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_water_source(
    source_data: WaterSourceCreate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Create a new water source"""
    try:
        return service.create_water_source(current_user.id, source_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sources", response_model=List[WaterSourceResponse])
async def get_water_sources(
    active_only: bool = Query(True, description="Only return active sources"),
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get all water sources for the current user"""
    return service.get_user_water_sources(current_user.id, active_only)

@router.get("/sources/{source_id}", response_model=WaterSourceResponse)
async def get_water_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get a specific water source"""
    source = service.get_water_source(current_user.id, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found")
    return source

@router.put("/sources/{source_id}", response_model=WaterSourceResponse)
async def update_water_source(
    source_id: int,
    update_data: WaterSourceUpdate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Update a water source"""
    source = service.update_water_source(current_user.id, source_id, update_data)
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found")
    return source

@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_water_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Delete (deactivate) a water source"""
    success = service.delete_water_source(current_user.id, source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Water source not found")

# Water Quality Test Endpoints
@router.post("/tests", response_model=WaterQualityTestResponse, status_code=status.HTTP_201_CREATED)
async def create_quality_test(
    test_data: WaterQualityTestCreate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Create a new water quality test"""
    try:
        return service.create_quality_test(current_user.id, test_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tests", response_model=List[WaterQualityTestResponse])
async def get_quality_tests(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get water quality tests"""
    return service.get_quality_tests(current_user.id, source_id)

@router.get("/tests/{test_id}", response_model=WaterQualityTestResponse)
async def get_quality_test(
    test_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get a specific water quality test"""
    tests = service.get_quality_tests(current_user.id)
    test = next((t for t in tests if t.id == test_id), None)
    if not test:
        raise HTTPException(status_code=404, detail="Quality test not found")
    return test

@router.put("/tests/{test_id}", response_model=WaterQualityTestResponse)
async def update_quality_test(
    test_id: int,
    update_data: WaterQualityTestUpdate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Update a water quality test"""
    test = service.update_quality_test(current_user.id, test_id, update_data)
    if not test:
        raise HTTPException(status_code=404, detail="Quality test not found")
    return test

# Contamination Report Endpoints
@router.post("/contamination-reports", response_model=ContaminationReportResponse, status_code=status.HTTP_201_CREATED)
async def create_contamination_report(
    report_data: ContaminationReportCreate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Create a contamination report"""
    try:
        return service.create_contamination_report(current_user.id, report_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contamination-reports", response_model=List[ContaminationReportResponse])
async def get_contamination_reports(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get contamination reports"""
    return service.get_contamination_reports(current_user.id, source_id)

@router.get("/contamination-reports/{report_id}", response_model=ContaminationReportResponse)
async def get_contamination_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get a specific contamination report"""
    reports = service.get_contamination_reports(current_user.id)
    report = next((r for r in reports if r.id == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Contamination report not found")
    return report

@router.put("/contamination-reports/{report_id}", response_model=ContaminationReportResponse)
async def update_contamination_report(
    report_id: int,
    update_data: ContaminationReportUpdate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Update a contamination report"""
    report = service.update_contamination_report(current_user.id, report_id, update_data)
    if not report:
        raise HTTPException(status_code=404, detail="Contamination report not found")
    return report

# Water Quality Alert Endpoints
@router.post("/alerts", response_model=WaterQualityAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: WaterQualityAlertCreate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Create a water quality alert"""
    return service.create_alert(current_user.id, alert_data)

@router.get("/alerts", response_model=List[WaterQualityAlertResponse])
async def get_alerts(
    active_only: bool = Query(True, description="Only return active alerts"),
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get water quality alerts"""
    return service.get_user_alerts(current_user.id, active_only)

@router.get("/alerts/{alert_id}", response_model=WaterQualityAlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get a specific water quality alert"""
    alerts = service.get_user_alerts(current_user.id, active_only=False)
    alert = next((a for a in alerts if a.id == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/alerts/{alert_id}/acknowledge", response_model=WaterQualityAlertResponse)
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Acknowledge an alert"""
    alert = service.acknowledge_alert(current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/alerts/{alert_id}/resolve", response_model=WaterQualityAlertResponse)
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Resolve an alert"""
    alert = service.resolve_alert(current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

# Filter Maintenance Endpoints
@router.post("/filter-maintenance", response_model=WaterFilterMaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_filter_maintenance(
    maintenance_data: WaterFilterMaintenanceCreate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Create a filter maintenance record"""
    try:
        return service.create_filter_maintenance(current_user.id, maintenance_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/filter-maintenance", response_model=List[WaterFilterMaintenanceResponse])
async def get_filter_maintenance(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get filter maintenance records"""
    return service.get_filter_maintenance(current_user.id, source_id)

@router.get("/filter-maintenance/{maintenance_id}", response_model=WaterFilterMaintenanceResponse)
async def get_filter_maintenance_record(
    maintenance_id: int,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get a specific filter maintenance record"""
    maintenance_records = service.get_filter_maintenance(current_user.id)
    record = next((m for m in maintenance_records if m.id == maintenance_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Filter maintenance record not found")
    return record

@router.put("/filter-maintenance/{maintenance_id}", response_model=WaterFilterMaintenanceResponse)
async def update_filter_maintenance(
    maintenance_id: int,
    update_data: WaterFilterMaintenanceUpdate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Update a filter maintenance record"""
    record = service.update_filter_maintenance(current_user.id, maintenance_id, update_data)
    if not record:
        raise HTTPException(status_code=404, detail="Filter maintenance record not found")
    return record

# Water Quality Preferences Endpoints
@router.get("/preferences", response_model=WaterQualityPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get water quality preferences"""
    return service.get_or_create_preferences(current_user.id)

@router.put("/preferences", response_model=WaterQualityPreferencesResponse)
async def update_preferences(
    update_data: WaterQualityPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Update water quality preferences"""
    return service.update_preferences(current_user.id, update_data)

# Analytics and Reporting Endpoints
@router.get("/analytics", response_model=WaterQualityAnalytics)
async def get_quality_analytics(
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get water quality analytics"""
    return service.get_quality_analytics(current_user.id)

@router.get("/trends", response_model=List[WaterQualityTrend])
async def get_quality_trends(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get water quality trends over time"""
    return service.get_quality_trends(current_user.id, days)

@router.get("/summary", response_model=WaterQualitySummary)
async def get_quality_summary(
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Get comprehensive water quality summary"""
    return service.get_quality_summary(current_user.id)

# Bulk Operations
@router.post("/sources/bulk-import", response_model=List[WaterSourceResponse])
async def bulk_import_sources(
    sources_data: List[WaterSourceCreate],
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Bulk import water sources"""
    created_sources = []
    for source_data in sources_data:
        try:
            source = service.create_water_source(current_user.id, source_data)
            created_sources.append(source)
        except ValueError as e:
            # Log error but continue with other sources
            continue
    
    return created_sources

@router.post("/tests/bulk-import", response_model=List[WaterQualityTestResponse])
async def bulk_import_tests(
    tests_data: List[WaterQualityTestCreate],
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Bulk import water quality tests"""
    created_tests = []
    for test_data in tests_data:
        try:
            test = service.create_quality_test(current_user.id, test_data)
            created_tests.append(test)
        except ValueError as e:
            # Log error but continue with other tests
            continue
    
    return created_tests

# Admin Endpoints (for system administrators)
@router.get("/admin/sources", response_model=List[WaterSourceResponse])
async def admin_get_all_sources(
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Admin: Get all water sources (requires admin privileges)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # This would need to be implemented in the service
    # For now, return empty list
    return []

@router.get("/admin/contamination-summary")
async def admin_contamination_summary(
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Admin: Get contamination summary across all users"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # This would need to be implemented in the service
    return {"message": "Admin contamination summary endpoint"}

@router.get("/admin/quality-trends")
async def admin_quality_trends(
    current_user: User = Depends(get_current_user),
    service: WaterQualityService = Depends(get_water_quality_service)
):
    """Admin: Get quality trends across all users"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    # This would need to be implemented in the service
    return {"message": "Admin quality trends endpoint"} 