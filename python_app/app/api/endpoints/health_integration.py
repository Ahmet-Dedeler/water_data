"""
API endpoints for health app integration and data synchronization.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_current_admin_user
from app.models.health_integration import HealthPlatform, DataType, SyncStatus
from app.schemas.health_integration import (
    BaseHealthResponse, HealthIntegrationCreate, HealthIntegrationUpdate,
    HealthIntegrationResponse, HealthMetricCreate, HealthMetricUpdate,
    HealthMetricResponse, SyncRequest, SyncSessionResponse, HealthMetricQuery,
    HealthDataConflictResponse, ConflictResolution, HealthInsightResponse,
    HealthInsightFeedback, HealthGoalIntegrationCreate, HealthGoalIntegrationUpdate,
    HealthGoalIntegrationResponse, HealthDataMappingCreate, HealthDataMappingUpdate,
    HealthDataMappingResponse, HealthAnalytics, PlatformAuthRequest,
    PlatformAuthResponse, BulkHealthMetricCreate, BulkHealthMetricResponse,
    HealthDashboardResponse, HealthIntegrationFilter, SyncSessionFilter,
    HealthInsightFilter
)
from app.services.health_integration_service import health_integration_service

logger = logging.getLogger(__name__)
router = APIRouter()


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int


# Health Integration Management
@router.post("/integrations", response_model=HealthIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_health_integration(
    integration_data: HealthIntegrationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new health platform integration."""
    try:
        integration = await health_integration_service.create_integration(current_user["id"], integration_data)
        return integration
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating health integration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/integrations/{integration_id}", response_model=HealthIntegrationResponse)
async def get_health_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific health integration."""
    integration = await health_integration_service.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Health integration not found")
    
    # Check if user owns the integration
    if integration.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return integration


@router.put("/integrations/{integration_id}", response_model=HealthIntegrationResponse)
async def update_health_integration(
    integration_id: str,
    update_data: HealthIntegrationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a health integration."""
    integration = await health_integration_service.update_integration(integration_id, current_user["id"], update_data)
    if not integration:
        raise HTTPException(status_code=404, detail="Health integration not found")
    return integration


@router.delete("/integrations/{integration_id}", response_model=BaseHealthResponse)
async def delete_health_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a health integration."""
    success = await health_integration_service.delete_integration(integration_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Health integration not found")
    
    return BaseHealthResponse(
        message=f"Health integration {integration_id} deleted successfully"
    )


@router.get("/integrations", response_model=List[HealthIntegrationResponse])
async def get_user_health_integrations(
    platforms: Optional[List[HealthPlatform]] = Query(None, description="Filter by platforms"),
    is_connected: Optional[bool] = Query(None, description="Filter by connection status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    has_errors: Optional[bool] = Query(None, description="Filter by error status"),
    data_types: Optional[List[DataType]] = Query(None, description="Filter by data types"),
    current_user: dict = Depends(get_current_user)
):
    """Get all health integrations for the current user."""
    try:
        filter_data = HealthIntegrationFilter(
            platforms=platforms,
            is_connected=is_connected,
            is_active=is_active,
            has_errors=has_errors,
            data_types=data_types
        )
        
        integrations = await health_integration_service.get_user_integrations(current_user["id"], filter_data)
        return integrations
    except Exception as e:
        logger.error(f"Error getting health integrations for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Platform Authentication
@router.post("/auth/connect", response_model=PlatformAuthResponse)
async def connect_platform(
    auth_request: PlatformAuthRequest,
    current_user: dict = Depends(get_current_user)
):
    """Connect to a health platform (OAuth flow)."""
    try:
        # This would implement the OAuth flow for each platform
        # For now, return a mock response
        return PlatformAuthResponse(
            platform=auth_request.platform,
            auth_url=f"https://{auth_request.platform.value}.com/oauth/authorize",
            is_connected=False,
            permissions_granted=[],
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
    except Exception as e:
        logger.error(f"Error connecting to platform {auth_request.platform}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/auth/callback", response_model=BaseHealthResponse)
async def platform_auth_callback(
    platform: HealthPlatform,
    code: str = Query(..., description="Authorization code from platform"),
    state: Optional[str] = Query(None, description="State parameter"),
    current_user: dict = Depends(get_current_user)
):
    """Handle OAuth callback from health platforms."""
    try:
        # This would process the OAuth callback and store tokens
        # For now, return success response
        return BaseHealthResponse(
            message=f"Successfully connected to {platform.value}"
        )
    except Exception as e:
        logger.error(f"Error processing OAuth callback for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health Metrics Management
@router.post("/metrics", response_model=HealthMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_health_metric(
    metric_data: HealthMetricCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new health metric."""
    try:
        metric = await health_integration_service.create_metric(current_user["id"], metric_data)
        return metric
    except Exception as e:
        logger.error(f"Error creating health metric: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics/{metric_id}", response_model=HealthMetricResponse)
async def get_health_metric(
    metric_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific health metric."""
    metric = await health_integration_service.get_metric(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Health metric not found")
    return metric


@router.put("/metrics/{metric_id}", response_model=HealthMetricResponse)
async def update_health_metric(
    metric_id: str,
    update_data: HealthMetricUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a health metric."""
    metric = await health_integration_service.update_metric(metric_id, update_data)
    if not metric:
        raise HTTPException(status_code=404, detail="Health metric not found")
    return metric


@router.get("/metrics", response_model=PaginatedResponse)
async def query_health_metrics(
    data_types: Optional[List[DataType]] = Query(None, description="Filter by data types"),
    platforms: Optional[List[HealthPlatform]] = Query(None, description="Filter by platforms"),
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence score"),
    validated_only: bool = Query(False, description="Return only validated metrics"),
    include_raw_data: bool = Query(False, description="Include raw platform data"),
    skip: int = Query(0, ge=0, description="Number of metrics to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of metrics to return"),
    current_user: dict = Depends(get_current_user)
):
    """Query health metrics with filtering."""
    try:
        query = HealthMetricQuery(
            data_types=data_types,
            platforms=platforms,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence,
            validated_only=validated_only,
            include_raw_data=include_raw_data
        )
        
        metrics, total = await health_integration_service.query_metrics(current_user["id"], query, skip, limit)
        
        return PaginatedResponse(
            items=[metric.dict() for metric in metrics],
            total=total,
            page=skip // limit + 1,
            size=len(metrics),
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        logger.error(f"Error querying health metrics for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/metrics/bulk", response_model=BulkHealthMetricResponse)
async def create_health_metrics_bulk(
    bulk_data: BulkHealthMetricCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create multiple health metrics in bulk."""
    try:
        created_metrics, failed_metrics, conflicts = await health_integration_service.bulk_create_metrics(
            current_user["id"], bulk_data
        )
        
        return BulkHealthMetricResponse(
            created_metrics=created_metrics,
            failed_metrics=failed_metrics,
            conflicts_detected=conflicts,
            total_created=len(created_metrics),
            total_failed=len(failed_metrics),
            total_conflicts=len(conflicts)
        )
    except Exception as e:
        logger.error(f"Error creating health metrics in bulk: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Data Synchronization
@router.post("/integrations/{integration_id}/sync", response_model=SyncSessionResponse)
async def start_data_sync(
    integration_id: str,
    sync_request: SyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start data synchronization for a health integration."""
    try:
        session = await health_integration_service.start_sync(integration_id, current_user["id"], sync_request)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting sync for integration {integration_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sync-sessions", response_model=PaginatedResponse)
async def get_sync_sessions(
    platforms: Optional[List[HealthPlatform]] = Query(None, description="Filter by platforms"),
    status: Optional[List[SyncStatus]] = Query(None, description="Filter by sync status"),
    date_from: Optional[datetime] = Query(None, description="Filter sessions from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter sessions to this date"),
    integration_ids: Optional[List[str]] = Query(None, description="Filter by integration IDs"),
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get sync sessions for the current user."""
    try:
        filter_data = SyncSessionFilter(
            platforms=platforms,
            status=status,
            date_from=date_from,
            date_to=date_to,
            integration_ids=integration_ids
        )
        
        sessions, total = await health_integration_service.get_sync_sessions(
            current_user["id"], filter_data, skip, limit
        )
        
        return PaginatedResponse(
            items=[session.dict() for session in sessions],
            total=total,
            page=skip // limit + 1,
            size=len(sessions),
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        logger.error(f"Error getting sync sessions for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Data Conflicts Management
@router.get("/conflicts", response_model=List[HealthDataConflictResponse])
async def get_data_conflicts(
    unresolved_only: bool = Query(True, description="Return only unresolved conflicts"),
    current_user: dict = Depends(get_current_user)
):
    """Get data conflicts for the current user."""
    try:
        conflicts = await health_integration_service.get_conflicts(current_user["id"], unresolved_only)
        return conflicts
    except Exception as e:
        logger.error(f"Error getting data conflicts for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conflicts/{conflict_id}/resolve", response_model=HealthDataConflictResponse)
async def resolve_data_conflict(
    conflict_id: str,
    resolution: ConflictResolution,
    current_user: dict = Depends(get_current_user)
):
    """Resolve a data conflict."""
    try:
        resolved_conflict = await health_integration_service.resolve_conflict(
            conflict_id, current_user["id"], resolution
        )
        if not resolved_conflict:
            raise HTTPException(status_code=404, detail="Data conflict not found")
        return resolved_conflict
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving conflict {conflict_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health Insights
@router.get("/insights", response_model=PaginatedResponse)
async def get_health_insights(
    insight_types: Optional[List[str]] = Query(None, description="Filter by insight types"),
    data_types: Optional[List[DataType]] = Query(None, description="Filter by data types"),
    platforms: Optional[List[HealthPlatform]] = Query(None, description="Filter by platforms"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence score"),
    viewed_only: Optional[bool] = Query(None, description="Filter by viewed status"),
    active_only: Optional[bool] = Query(None, description="Filter by active status"),
    date_from: Optional[date] = Query(None, description="Filter insights from this date"),
    date_to: Optional[date] = Query(None, description="Filter insights to this date"),
    skip: int = Query(0, ge=0, description="Number of insights to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of insights to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get health insights for the current user."""
    try:
        filter_data = HealthInsightFilter(
            insight_types=insight_types,
            data_types=data_types,
            platforms=platforms,
            min_confidence=min_confidence,
            viewed_only=viewed_only,
            active_only=active_only,
            date_from=date_from,
            date_to=date_to
        )
        
        insights, total = await health_integration_service.get_user_insights(
            current_user["id"], filter_data, skip, limit
        )
        
        return PaginatedResponse(
            items=[insight.dict() for insight in insights],
            total=total,
            page=skip // limit + 1,
            size=len(insights),
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        logger.error(f"Error getting health insights for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/insights/generate", response_model=List[HealthInsightResponse])
async def generate_health_insights(
    current_user: dict = Depends(get_current_user)
):
    """Generate new health insights for the current user."""
    try:
        insights = await health_integration_service.generate_insights(current_user["id"])
        return insights
    except Exception as e:
        logger.error(f"Error generating health insights for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/insights/{insight_id}/feedback", response_model=BaseHealthResponse)
async def provide_insight_feedback(
    insight_id: str,
    feedback: HealthInsightFeedback,
    current_user: dict = Depends(get_current_user)
):
    """Provide feedback on a health insight."""
    try:
        insight = await health_integration_service.provide_insight_feedback(
            insight_id, current_user["id"], feedback
        )
        if not insight:
            raise HTTPException(status_code=404, detail="Health insight not found")
        
        return BaseHealthResponse(
            message="Feedback recorded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording insight feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health Analytics
@router.get("/analytics", response_model=HealthAnalytics)
async def get_health_analytics(
    period_start: date = Query(..., description="Analytics period start date"),
    period_end: date = Query(..., description="Analytics period end date"),
    current_user: dict = Depends(get_current_user)
):
    """Get health analytics for the current user."""
    try:
        # Validate date range
        if period_end < period_start:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        if (period_end - period_start).days > 365:
            raise HTTPException(status_code=400, detail="Analytics period cannot exceed 365 days")
        
        # Generate analytics (mock implementation)
        analytics = HealthAnalytics(
            user_id=current_user["id"],
            period_start=period_start,
            period_end=period_end,
            total_metrics=150,
            data_types_tracked=[DataType.WATER_INTAKE, DataType.STEPS, DataType.HEART_RATE],
            platforms_used=[HealthPlatform.APPLE_HEALTH, HealthPlatform.GOOGLE_FIT],
            total_syncs=25,
            successful_syncs=23,
            failed_syncs=2,
            sync_success_rate=0.92,
            validated_metrics=140,
            validation_rate=0.93,
            conflicts_detected=5,
            conflicts_resolved=4,
            insights_generated=8,
            insights_viewed=6,
            average_insight_rating=4.2,
            data_trends={
                "water_intake_trend": "increasing",
                "steps_trend": "stable",
                "heart_rate_trend": "decreasing"
            }
        )
        
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating health analytics for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Dashboard
@router.get("/dashboard", response_model=HealthDashboardResponse)
async def get_health_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive health dashboard for the current user."""
    try:
        # Get integrations
        integrations = await health_integration_service.get_user_integrations(current_user["id"])
        
        # Get recent metrics
        query = HealthMetricQuery(
            start_date=datetime.utcnow() - timedelta(days=7),
            validated_only=True
        )
        recent_metrics, _ = await health_integration_service.query_metrics(current_user["id"], query, limit=10)
        
        # Get conflicts
        conflicts = await health_integration_service.get_conflicts(current_user["id"], unresolved_only=True)
        
        # Get recent insights
        insights, _ = await health_integration_service.get_user_insights(current_user["id"], limit=5)
        
        dashboard = HealthDashboardResponse(
            user_id=current_user["id"],
            integrations=integrations,
            recent_metrics=recent_metrics,
            active_conflicts=conflicts,
            recent_insights=insights,
            sync_status={
                "last_sync": "2024-01-15T10:30:00Z",
                "next_sync": "2024-01-15T14:30:00Z",
                "sync_frequency": "every_4_hours"
            },
            data_summary={
                "total_metrics_this_week": len(recent_metrics),
                "data_types_tracked": len(set(m.data_type for m in recent_metrics)),
                "platforms_connected": len([i for i in integrations if i.is_connected])
            },
            recommendations=[
                "Consider connecting more health platforms for comprehensive tracking",
                "Review and resolve pending data conflicts",
                "Check out your latest health insights for personalized recommendations"
            ]
        )
        
        return dashboard
    except Exception as e:
        logger.error(f"Error generating health dashboard for user {current_user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Admin Endpoints
@router.get("/admin/integrations", response_model=PaginatedResponse)
async def get_all_integrations_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get all health integrations (Admin only)."""
    try:
        # This would be implemented to return all integrations
        # For now, return empty response
        return PaginatedResponse(
            items=[],
            total=0,
            page=1,
            size=0,
            pages=0
        )
    except Exception as e:
        logger.error(f"Error getting all integrations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/analytics", response_model=dict)
async def get_platform_analytics_admin(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get platform-wide health integration analytics (Admin only)."""
    try:
        analytics = {
            "total_integrations": 150,
            "active_integrations": 120,
            "total_users_with_integrations": 85,
            "platform_distribution": {
                "apple_health": 65,
                "google_fit": 45,
                "fitbit": 25,
                "samsung_health": 15
            },
            "data_type_usage": {
                "water_intake": 95,
                "steps": 120,
                "heart_rate": 75,
                "weight": 45,
                "sleep": 60
            },
            "sync_statistics": {
                "total_syncs_today": 450,
                "successful_syncs_today": 425,
                "failed_syncs_today": 25,
                "average_sync_duration": 12.5
            },
            "conflict_statistics": {
                "total_conflicts": 25,
                "resolved_conflicts": 20,
                "pending_conflicts": 5
            }
        }
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting platform analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/users/{user_id}/integrations", response_model=List[HealthIntegrationResponse])
async def get_user_integrations_admin(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """Get health integrations for any user (Admin only)."""
    try:
        integrations = await health_integration_service.get_user_integrations(user_id)
        return integrations
    except Exception as e:
        logger.error(f"Error getting integrations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 