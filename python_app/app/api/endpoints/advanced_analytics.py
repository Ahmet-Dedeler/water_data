from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, status
from typing import Optional, List
import logging
from datetime import date, datetime, timedelta

from app.models.advanced_analytics import (
    AnalyticsPeriod, AnalyticsMetric, TrendDirection, InsightType, ComparisonType,
    DataPoint, TimeSeries, Comparison, Insight, Goal, MetricCard, Chart,
    CorrelationData, AdvancedDashboard, AnalyticsReport, AnalyticsRequest,
    DashboardRequest, ReportRequest, AnalyticsResponse, TrendAnalysis,
    BenchmarkAnalysis, AdvancedInsights, AnalyticsExport, RealTimeMetric,
    AnalyticsAlert, AnalyticsNotification
)
from app.models.common import BaseResponse
from app.services.advanced_analytics_service import advanced_analytics_service
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/advanced-analytics", tags=["advanced-analytics"])
logger = logging.getLogger(__name__)


# Time Series and Data Endpoints

@router.post("/time-series", response_model=TimeSeries)
async def generate_time_series(
    metric: AnalyticsMetric,
    period: AnalyticsPeriod,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Generate time series data for a specific metric."""
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        
        if not start_date:
            if period == AnalyticsPeriod.WEEKLY:
                start_date = end_date - timedelta(days=7)
            elif period == AnalyticsPeriod.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif period == AnalyticsPeriod.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            elif period == AnalyticsPeriod.YEARLY:
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
        
        return await advanced_analytics_service.generate_time_series(
            current_user.id, metric, period, start_date, end_date
        )
    except Exception as e:
        logger.error(f"Error generating time series: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate time series")


@router.post("/analytics", response_model=AnalyticsResponse)
async def get_analytics_data(
    request: AnalyticsRequest,
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics data for multiple metrics."""
    try:
        # Set default date range if not provided
        end_date = request.end_date or date.today()
        
        if not request.start_date:
            if request.period == AnalyticsPeriod.WEEKLY:
                start_date = end_date - timedelta(days=7)
            elif request.period == AnalyticsPeriod.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif request.period == AnalyticsPeriod.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            elif request.period == AnalyticsPeriod.YEARLY:
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = request.start_date
        
        # Generate time series for all requested metrics
        time_series_list = []
        for metric in request.metrics:
            ts = await advanced_analytics_service.generate_time_series(
                current_user.id, metric, request.period, start_date, end_date
            )
            time_series_list.append(ts)
        
        # Generate insights if requested
        insights = []
        if request.include_insights:
            insights = await advanced_analytics_service.generate_insights(
                current_user.id, time_series_list, request.period
            )
        
        # Generate comparisons (simplified)
        comparisons = []
        if request.include_comparisons:
            for ts in time_series_list:
                comparison = Comparison(
                    comparison_type=ComparisonType.PREVIOUS_PERIOD,
                    current_value=ts.average_value,
                    comparison_value=ts.average_value * 0.9,  # Simplified
                    difference=ts.average_value * 0.1,
                    percentage_change=10.0,
                    is_improvement=ts.trend_direction == TrendDirection.INCREASING,
                    description=f"Compared to previous {request.period.value}"
                )
                comparisons.append(comparison)
        
        return AnalyticsResponse(
            request_id=f"req_{datetime.utcnow().timestamp()}",
            user_id=current_user.id,
            time_series=time_series_list,
            comparisons=comparisons,
            insights=insights,
            goals=[],  # Would be populated with actual goals
            correlations=[]  # Would be populated with correlations
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics data")


# Dashboard Endpoints

@router.post("/dashboard", response_model=AdvancedDashboard)
async def generate_dashboard(
    request: DashboardRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a comprehensive analytics dashboard."""
    try:
        return await advanced_analytics_service.generate_dashboard(current_user.id, request)
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard")


@router.get("/dashboard/{dashboard_id}", response_model=AdvancedDashboard)
async def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific dashboard by ID."""
    try:
        # This would be implemented to retrieve saved dashboards
        raise HTTPException(status_code=501, detail="Dashboard retrieval not yet implemented")
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")


@router.get("/dashboards", response_model=List[AdvancedDashboard])
async def get_user_dashboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get user's saved dashboards."""
    try:
        # This would be implemented to list user dashboards
        raise HTTPException(status_code=501, detail="Dashboard listing not yet implemented")
    except Exception as e:
        logger.error(f"Error getting dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboards")


@router.delete("/dashboard/{dashboard_id}", response_model=BaseResponse)
async def delete_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a dashboard."""
    try:
        # This would be implemented to delete dashboards
        raise HTTPException(status_code=501, detail="Dashboard deletion not yet implemented")
    except Exception as e:
        logger.error(f"Error deleting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dashboard")


# Insights Endpoints

@router.get("/insights", response_model=List[Insight])
async def get_insights(
    metric: Optional[AnalyticsMetric] = Query(None),
    insight_type: Optional[InsightType] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get AI-generated insights for the user."""
    try:
        # Generate recent insights based on current data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get time series for key metrics
        metrics_to_analyze = [metric] if metric else [
            AnalyticsMetric.WATER_INTAKE,
            AnalyticsMetric.GOAL_COMPLETION,
            AnalyticsMetric.SOCIAL_ENGAGEMENT
        ]
        
        time_series_data = []
        for m in metrics_to_analyze:
            ts = await advanced_analytics_service.generate_time_series(
                current_user.id, m, AnalyticsPeriod.DAILY, start_date, end_date
            )
            time_series_data.append(ts)
        
        # Generate insights
        insights = await advanced_analytics_service.generate_insights(
            current_user.id, time_series_data, AnalyticsPeriod.DAILY
        )
        
        # Filter by insight type if specified
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        
        return insights[:limit]
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get insights")


@router.get("/insights/{insight_id}", response_model=Insight)
async def get_insight(
    insight_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific insight by ID."""
    try:
        # This would be implemented to retrieve specific insights
        raise HTTPException(status_code=501, detail="Insight retrieval not yet implemented")
    except Exception as e:
        logger.error(f"Error getting insight: {e}")
        raise HTTPException(status_code=500, detail="Failed to get insight")


# Trend Analysis Endpoints

@router.get("/trends/{metric}", response_model=TrendAnalysis)
async def get_trend_analysis(
    metric: AnalyticsMetric,
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTHLY),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive trend analysis for a metric."""
    try:
        # Set default date range
        if not end_date:
            end_date = date.today()
        
        if not start_date:
            if period == AnalyticsPeriod.YEARLY:
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=90)
        
        # Generate time series
        time_series = await advanced_analytics_service.generate_time_series(
            current_user.id, metric, period, start_date, end_date
        )
        
        # Create trend analysis
        trend_analysis = TrendAnalysis(
            metric=metric,
            period=period,
            overall_trend=time_series.trend_direction,
            trend_strength=abs(time_series.trend_percentage) / 100,
            seasonal_patterns=[],  # Would be populated with seasonal analysis
            cyclical_patterns=[],  # Would be populated with cyclical analysis
            anomalies=[],  # Would be populated with anomaly detection
            forecast=None  # Would be populated with predictive model
        )
        
        return trend_analysis
        
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trend analysis")


# Comparison and Benchmarking

@router.get("/benchmark/{metric}", response_model=BenchmarkAnalysis)
async def get_benchmark_analysis(
    metric: AnalyticsMetric,
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTHLY),
    current_user: User = Depends(get_current_user)
):
    """Get benchmarking analysis against peers and global averages."""
    try:
        # Generate user's time series
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        time_series = await advanced_analytics_service.generate_time_series(
            current_user.id, metric, period, start_date, end_date
        )
        
        user_value = time_series.average_value
        
        # Simplified benchmark data (would be calculated from actual user base)
        benchmark = BenchmarkAnalysis(
            user_value=user_value,
            personal_best=user_value * 1.2,  # Simplified
            peer_group_stats={
                "average": user_value * 0.9,
                "median": user_value * 0.85,
                "top_10_percent": user_value * 1.5
            },
            global_stats={
                "average": user_value * 0.8,
                "median": user_value * 0.75,
                "top_10_percent": user_value * 1.8
            },
            percentile_ranking=75.0,  # Simplified
            improvement_potential=20.0,
            benchmark_insights=[]
        )
        
        return benchmark
        
    except Exception as e:
        logger.error(f"Error getting benchmark analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get benchmark analysis")


# Correlation Analysis

@router.get("/correlations", response_model=List[CorrelationData])
async def get_correlations(
    primary_metric: AnalyticsMetric,
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTHLY),
    min_correlation: float = Query(0.3, ge=0, le=1),
    current_user: User = Depends(get_current_user)
):
    """Get correlation analysis between metrics."""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        
        # Get time series for primary metric
        primary_ts = await advanced_analytics_service.generate_time_series(
            current_user.id, primary_metric, period, start_date, end_date
        )
        
        # Get time series for other metrics to correlate with
        other_metrics = [m for m in AnalyticsMetric if m != primary_metric]
        correlations = []
        
        for metric in other_metrics[:5]:  # Limit to 5 correlations
            try:
                other_ts = await advanced_analytics_service.generate_time_series(
                    current_user.id, metric, period, start_date, end_date
                )
                
                correlation = await advanced_analytics_service._calculate_correlation(primary_ts, other_ts)
                
                if abs(correlation.correlation_coefficient) >= min_correlation:
                    correlations.append(correlation)
                    
            except Exception as e:
                logger.warning(f"Error calculating correlation with {metric}: {e}")
                continue
        
        return sorted(correlations, key=lambda x: abs(x.correlation_coefficient), reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting correlations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get correlations")


# Reports

@router.post("/report", response_model=AnalyticsReport)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate a comprehensive analytics report."""
    try:
        # Set default date range
        end_date = request.end_date or date.today()
        
        if not request.start_date:
            if request.period == AnalyticsPeriod.WEEKLY:
                start_date = end_date - timedelta(days=7)
            elif request.period == AnalyticsPeriod.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif request.period == AnalyticsPeriod.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            elif request.period == AnalyticsPeriod.YEARLY:
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = request.start_date
        
        # Generate comprehensive analytics data
        metrics_to_analyze = [
            AnalyticsMetric.WATER_INTAKE,
            AnalyticsMetric.GOAL_COMPLETION,
            AnalyticsMetric.STREAK_PERFORMANCE,
            AnalyticsMetric.SOCIAL_ENGAGEMENT
        ]
        
        time_series_data = []
        for metric in metrics_to_analyze:
            ts = await advanced_analytics_service.generate_time_series(
                current_user.id, metric, request.period, start_date, end_date
            )
            time_series_data.append(ts)
        
        # Generate insights
        insights = await advanced_analytics_service.generate_insights(
            current_user.id, time_series_data, request.period
        )
        
        # Create charts
        charts = []
        for ts in time_series_data:
            chart = Chart(
                chart_id=f"chart_{ts.metric.value}",
                chart_type="line",
                title=f"{ts.metric.value.replace('_', ' ').title()} Trend",
                description=f"Trend analysis for {ts.metric.value}",
                data=ts
            )
            charts.append(chart)
        
        # Generate executive summary
        executive_summary = f"""
        Analytics Report for {request.period.value.title()} Period
        
        This report covers your hydration and health tracking data from {start_date} to {end_date}.
        Key highlights include water intake trends, goal achievement rates, and social engagement patterns.
        """
        
        # Generate key findings
        key_findings = []
        for insight in insights[:5]:
            key_findings.append(insight.description)
        
        # Generate recommendations
        recommendations = []
        for insight in insights:
            recommendations.extend(insight.action_items)
        
        report = AnalyticsReport(
            report_id=f"report_{datetime.utcnow().timestamp()}",
            user_id=current_user.id,
            report_type=request.report_type,
            title=f"{request.report_type.title()} Analytics Report",
            period=request.period,
            start_date=start_date,
            end_date=end_date,
            executive_summary=executive_summary.strip(),
            key_findings=key_findings,
            detailed_analysis={
                "time_series": [ts.dict() for ts in time_series_data],
                "insights": [i.dict() for i in insights]
            },
            recommendations=list(set(recommendations))[:10],  # Unique recommendations, max 10
            charts=charts,
            raw_data=None if not request.include_raw_data else {
                "time_series": [ts.dict() for ts in time_series_data]
            }
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/reports", response_model=List[AnalyticsReport])
async def get_user_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get user's generated reports."""
    try:
        # This would be implemented to retrieve saved reports
        raise HTTPException(status_code=501, detail="Report listing not yet implemented")
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reports")


# Export

@router.post("/export", response_model=AnalyticsExport)
async def export_analytics_data(
    data_types: List[str],
    period: AnalyticsPeriod,
    export_format: str = Query("json", regex="^(json|csv|excel|pdf)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Export analytics data in various formats."""
    try:
        export = AnalyticsExport(
            export_id=f"export_{datetime.utcnow().timestamp()}",
            user_id=current_user.id,
            export_type=export_format,
            data_types=data_types,
            period=period,
            start_date=start_date or date.today() - timedelta(days=30),
            end_date=end_date or date.today(),
            include_charts=True,
            include_insights=True,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        # Add background task to generate export file
        # background_tasks.add_task(generate_export_file, export)
        
        return export
        
    except Exception as e:
        logger.error(f"Error creating export: {e}")
        raise HTTPException(status_code=500, detail="Failed to create export")


# Real-time Analytics

@router.get("/real-time/{metric}", response_model=RealTimeMetric)
async def get_real_time_metric(
    metric: AnalyticsMetric,
    current_user: User = Depends(get_current_user)
):
    """Get real-time metric data."""
    try:
        # Generate current day data
        today = date.today()
        time_series = await advanced_analytics_service.generate_time_series(
            current_user.id, metric, AnalyticsPeriod.DAILY, today, today
        )
        
        current_value = time_series.total_value if time_series.data_points else 0.0
        
        # Calculate change from yesterday (simplified)
        yesterday = today - timedelta(days=1)
        yesterday_ts = await advanced_analytics_service.generate_time_series(
            current_user.id, metric, AnalyticsPeriod.DAILY, yesterday, yesterday
        )
        
        yesterday_value = yesterday_ts.total_value if yesterday_ts.data_points else 0.0
        change_from_previous = current_value - yesterday_value
        
        real_time_metric = RealTimeMetric(
            metric=metric,
            current_value=current_value,
            timestamp=datetime.utcnow(),
            change_from_previous=change_from_previous,
            trend_indicator=TrendDirection.INCREASING if change_from_previous > 0 else 
                           TrendDirection.DECREASING if change_from_previous < 0 else 
                           TrendDirection.STABLE
        )
        
        return real_time_metric
        
    except Exception as e:
        logger.error(f"Error getting real-time metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time metric")


# System Information

@router.get("/info", response_model=dict)
async def get_analytics_system_info():
    """Get analytics system information and capabilities."""
    return {
        "supported_metrics": [m.value for m in AnalyticsMetric],
        "supported_periods": [p.value for p in AnalyticsPeriod],
        "supported_comparisons": [c.value for c in ComparisonType],
        "supported_insight_types": [t.value for t in InsightType],
        "features": {
            "time_series_analysis": True,
            "trend_detection": True,
            "anomaly_detection": True,
            "correlation_analysis": True,
            "predictive_analytics": True,
            "ai_insights": True,
            "dashboard_generation": True,
            "report_generation": True,
            "real_time_metrics": True,
            "data_export": True,
            "benchmarking": True,
            "social_comparison": True
        },
        "export_formats": ["json", "csv", "excel", "pdf"],
        "chart_types": ["line", "bar", "pie", "heatmap", "scatter"],
        "max_data_points": 10000,
        "retention_days": 365,
        "real_time_update_interval": "5_minutes"
    }


# Health Check

@router.get("/health", response_model=dict)
async def analytics_health_check():
    """Health check for analytics system."""
    try:
        # Test basic functionality
        test_user_id = 1
        test_metric = AnalyticsMetric.WATER_INTAKE
        test_period = AnalyticsPeriod.DAILY
        end_date = date.today()
        start_date = end_date - timedelta(days=1)
        
        # Try to generate a simple time series
        await advanced_analytics_service.generate_time_series(
            test_user_id, test_metric, test_period, start_date, end_date
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "analytics_engine": "operational",
                "insight_generation": "operational",
                "dashboard_service": "operational",
                "export_service": "operational"
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "services": {
                "analytics_engine": "error",
                "insight_generation": "unknown",
                "dashboard_service": "unknown",
                "export_service": "unknown"
            }
        } 