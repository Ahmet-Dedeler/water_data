from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum


class AnalyticsPeriod(str, Enum):
    """Time periods for analytics."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class AnalyticsMetric(str, Enum):
    """Available analytics metrics."""
    WATER_INTAKE = "water_intake"
    GOAL_COMPLETION = "goal_completion"
    STREAK_PERFORMANCE = "streak_performance"
    CAFFEINE_INTAKE = "caffeine_intake"
    DRINK_VARIETY = "drink_variety"
    HYDRATION_SCORE = "hydration_score"
    ACTIVITY_CORRELATION = "activity_correlation"
    SLEEP_CORRELATION = "sleep_correlation"
    WEATHER_CORRELATION = "weather_correlation"
    SOCIAL_ENGAGEMENT = "social_engagement"
    ACHIEVEMENT_PROGRESS = "achievement_progress"
    HEALTH_TRENDS = "health_trends"


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class InsightType(str, Enum):
    """Types of insights."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    WARNING = "warning"
    ACHIEVEMENT = "achievement"
    RECOMMENDATION = "recommendation"


class ComparisonType(str, Enum):
    """Types of comparisons."""
    PREVIOUS_PERIOD = "previous_period"
    SAME_PERIOD_LAST_YEAR = "same_period_last_year"
    PERSONAL_AVERAGE = "personal_average"
    PEER_AVERAGE = "peer_average"
    GLOBAL_AVERAGE = "global_average"


# Core Analytics Models

class DataPoint(BaseModel):
    """Individual data point for time series."""
    timestamp: datetime
    value: float
    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TimeSeries(BaseModel):
    """Time series data structure."""
    metric: AnalyticsMetric
    period: AnalyticsPeriod
    data_points: List[DataPoint]
    start_date: date
    end_date: date
    total_value: float
    average_value: float
    min_value: float
    max_value: float
    trend_direction: TrendDirection
    trend_percentage: float


class Comparison(BaseModel):
    """Comparison between two values or periods."""
    comparison_type: ComparisonType
    current_value: float
    comparison_value: float
    difference: float
    percentage_change: float
    is_improvement: bool
    description: str


class Insight(BaseModel):
    """Generated insight from data analysis."""
    id: str
    insight_type: InsightType
    title: str
    description: str
    metric: AnalyticsMetric
    confidence_score: float = Field(..., ge=0, le=1)
    action_items: List[str] = []
    related_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Goal(BaseModel):
    """Goal tracking for analytics."""
    metric: AnalyticsMetric
    target_value: float
    current_value: float
    progress_percentage: float
    is_achieved: bool
    days_remaining: Optional[int] = None
    projected_completion: Optional[date] = None


# Dashboard Components

class MetricCard(BaseModel):
    """Individual metric card for dashboard."""
    metric: AnalyticsMetric
    title: str
    current_value: float
    display_value: str
    unit: str
    comparison: Optional[Comparison] = None
    trend: Optional[TimeSeries] = None
    goal: Optional[Goal] = None
    insights: List[Insight] = []


class Chart(BaseModel):
    """Chart configuration and data."""
    chart_id: str
    chart_type: str  # line, bar, pie, heatmap, etc.
    title: str
    description: Optional[str] = None
    data: Union[TimeSeries, List[TimeSeries], Dict[str, Any]]
    config: Dict[str, Any] = {}
    insights: List[Insight] = []


class HeatmapData(BaseModel):
    """Heatmap data structure."""
    date: date
    hour: int
    value: float
    intensity: float = Field(..., ge=0, le=1)


class CorrelationData(BaseModel):
    """Correlation analysis data."""
    metric_x: str
    metric_y: str
    correlation_coefficient: float = Field(..., ge=-1, le=1)
    p_value: float
    is_significant: bool
    sample_size: int
    description: str


# Advanced Analytics Models

class HydrationPattern(BaseModel):
    """User's hydration patterns."""
    hourly_distribution: List[float]  # 24 hours
    daily_distribution: List[float]   # 7 days
    weekly_average: float
    peak_hours: List[int]
    low_hours: List[int]
    consistency_score: float = Field(..., ge=0, le=1)


class SeasonalTrend(BaseModel):
    """Seasonal trend analysis."""
    season: str
    average_intake: float
    trend_direction: TrendDirection
    year_over_year_change: float
    peak_months: List[str]
    low_months: List[str]


class BehaviorAnalysis(BaseModel):
    """Behavioral pattern analysis."""
    habit_strength: float = Field(..., ge=0, le=1)
    consistency_score: float = Field(..., ge=0, le=1)
    improvement_rate: float
    plateau_periods: List[Dict[str, Any]]
    breakthrough_moments: List[Dict[str, Any]]
    behavioral_triggers: List[str]


class PredictiveModel(BaseModel):
    """Predictive analytics results."""
    model_type: str
    prediction_horizon_days: int
    predicted_values: List[DataPoint]
    confidence_intervals: List[Dict[str, float]]
    accuracy_metrics: Dict[str, float]
    feature_importance: Dict[str, float]


class HealthCorrelation(BaseModel):
    """Health metric correlations."""
    health_metric: str
    hydration_correlation: float
    statistical_significance: bool
    effect_size: str  # small, medium, large
    recommendations: List[str]


class SocialComparison(BaseModel):
    """Social comparison analytics."""
    user_percentile: float
    peer_group_average: float
    global_average: float
    rank_in_peer_group: int
    total_peers: int
    improvement_suggestions: List[str]


# Dashboard and Report Models

class DashboardSection(BaseModel):
    """Dashboard section configuration."""
    section_id: str
    title: str
    description: Optional[str] = None
    metric_cards: List[MetricCard] = []
    charts: List[Chart] = []
    insights: List[Insight] = []
    order: int = 0


class AdvancedDashboard(BaseModel):
    """Complete advanced dashboard."""
    user_id: int
    dashboard_id: str
    title: str
    description: Optional[str] = None
    period: AnalyticsPeriod
    start_date: date
    end_date: date
    sections: List[DashboardSection]
    summary_insights: List[Insight]
    key_metrics: Dict[str, float]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AnalyticsReport(BaseModel):
    """Comprehensive analytics report."""
    report_id: str
    user_id: int
    report_type: str
    title: str
    period: AnalyticsPeriod
    start_date: date
    end_date: date
    executive_summary: str
    key_findings: List[str]
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]
    charts: List[Chart]
    raw_data: Optional[Dict[str, Any]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models

class AnalyticsRequest(BaseModel):
    """Request for analytics data."""
    metrics: List[AnalyticsMetric]
    period: AnalyticsPeriod
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_comparisons: bool = True
    include_insights: bool = True
    include_predictions: bool = False
    comparison_types: List[ComparisonType] = [ComparisonType.PREVIOUS_PERIOD]


class DashboardRequest(BaseModel):
    """Request for dashboard generation."""
    dashboard_type: str = "comprehensive"
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_predictions: bool = False
    include_social_comparisons: bool = True
    custom_metrics: List[AnalyticsMetric] = []


class ReportRequest(BaseModel):
    """Request for report generation."""
    report_type: str
    period: AnalyticsPeriod
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_raw_data: bool = False
    format: str = "json"  # json, pdf, html
    sections: List[str] = []


class AnalyticsResponse(BaseModel):
    """Response containing analytics data."""
    request_id: str
    user_id: int
    time_series: List[TimeSeries]
    comparisons: List[Comparison]
    insights: List[Insight]
    goals: List[Goal]
    correlations: List[CorrelationData]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TrendAnalysis(BaseModel):
    """Comprehensive trend analysis."""
    metric: AnalyticsMetric
    period: AnalyticsPeriod
    overall_trend: TrendDirection
    trend_strength: float = Field(..., ge=0, le=1)
    seasonal_patterns: List[SeasonalTrend]
    cyclical_patterns: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    forecast: Optional[PredictiveModel] = None


class BenchmarkAnalysis(BaseModel):
    """Benchmarking against various groups."""
    user_value: float
    personal_best: float
    peer_group_stats: Dict[str, float]
    global_stats: Dict[str, float]
    percentile_ranking: float
    improvement_potential: float
    benchmark_insights: List[Insight]


class AdvancedInsights(BaseModel):
    """Advanced insights and recommendations."""
    behavioral_analysis: BehaviorAnalysis
    health_correlations: List[HealthCorrelation]
    social_comparison: SocialComparison
    predictive_insights: List[Insight]
    optimization_opportunities: List[Dict[str, Any]]
    risk_factors: List[Dict[str, Any]]


# Export and Integration Models

class AnalyticsExport(BaseModel):
    """Analytics data export configuration."""
    export_id: str
    user_id: int
    export_type: str  # csv, json, pdf, excel
    data_types: List[str]
    period: AnalyticsPeriod
    start_date: date
    end_date: date
    include_charts: bool = True
    include_insights: bool = True
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class AnalyticsIntegration(BaseModel):
    """Third-party analytics integration."""
    integration_id: str
    user_id: int
    platform: str  # google_analytics, mixpanel, etc.
    api_key: str
    sync_frequency: str
    last_sync: Optional[datetime] = None
    sync_status: str
    metrics_to_sync: List[AnalyticsMetric]
    configuration: Dict[str, Any] = {}


# Real-time Analytics

class RealTimeMetric(BaseModel):
    """Real-time metric update."""
    metric: AnalyticsMetric
    current_value: float
    timestamp: datetime
    change_from_previous: float
    trend_indicator: TrendDirection
    alert_level: Optional[str] = None


class AnalyticsAlert(BaseModel):
    """Analytics-based alert."""
    alert_id: str
    user_id: int
    metric: AnalyticsMetric
    alert_type: str  # threshold, anomaly, goal
    severity: str    # low, medium, high, critical
    title: str
    description: str
    threshold_value: Optional[float] = None
    current_value: float
    suggested_actions: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False


class AnalyticsNotification(BaseModel):
    """Analytics notification."""
    notification_id: str
    user_id: int
    title: str
    message: str
    notification_type: str  # insight, achievement, alert, report
    priority: str  # low, normal, high
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow) 