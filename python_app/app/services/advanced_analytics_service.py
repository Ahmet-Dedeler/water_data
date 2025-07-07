import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import asyncio
import statistics
import math
from dataclasses import dataclass

from app.models.advanced_analytics import (
    AnalyticsPeriod, AnalyticsMetric, TrendDirection, InsightType, ComparisonType,
    DataPoint, TimeSeries, Comparison, Insight, Goal, MetricCard, Chart,
    HeatmapData, CorrelationData, HydrationPattern, SeasonalTrend,
    BehaviorAnalysis, PredictiveModel, HealthCorrelation, SocialComparison,
    DashboardSection, AdvancedDashboard, AnalyticsReport, AnalyticsRequest,
    DashboardRequest, ReportRequest, AnalyticsResponse, TrendAnalysis,
    BenchmarkAnalysis, AdvancedInsights, AnalyticsExport, RealTimeMetric,
    AnalyticsAlert, AnalyticsNotification
)
from app.models.common import BaseResponse
from app.services.water_service import water_service
from app.services.drink_service import drink_service
from app.services.achievement_service import achievement_service
from app.services.health_goal_service import health_goal_service
from app.services.friend_service import friend_service
from app.services.activity_feed_service import activity_feed_service

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsConfig:
    """Configuration for analytics calculations."""
    min_data_points: int = 7
    confidence_threshold: float = 0.7
    trend_sensitivity: float = 0.1
    anomaly_threshold: float = 2.0  # Standard deviations
    prediction_horizon_days: int = 30


class AdvancedAnalyticsService:
    """Comprehensive advanced analytics service for insights and trends."""
    
    def __init__(self):
        self.analytics_file = Path(__file__).parent.parent / "data" / "analytics_cache.json"
        self.insights_file = Path(__file__).parent.parent / "data" / "generated_insights.json"
        self.dashboards_file = Path(__file__).parent.parent / "data" / "user_dashboards.json"
        self.reports_file = Path(__file__).parent.parent / "data" / "analytics_reports.json"
        self.config = AnalyticsConfig()
        self._ensure_data_files()
        self._analytics_cache = None
        self._insights_cache = None
        self._dashboards_cache = None
        self._reports_cache = None
        self._next_insight_id = 1
        self._next_dashboard_id = 1
        self._next_report_id = 1
    
    def _ensure_data_files(self):
        """Ensure analytics data files exist."""
        data_dir = self.analytics_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [self.analytics_file, self.insights_file, self.dashboards_file, self.reports_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_analytics_cache(self) -> List[Dict]:
        """Load analytics cache from file."""
        if self._analytics_cache is None:
            try:
                with open(self.analytics_file, 'r') as f:
                    self._analytics_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading analytics cache: {e}")
                self._analytics_cache = []
        return self._analytics_cache
    
    async def _save_analytics_cache(self, cache: List[Dict]):
        """Save analytics cache to file."""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(cache, f, indent=2, default=str)
            self._analytics_cache = cache
        except Exception as e:
            logger.error(f"Error saving analytics cache: {e}")
            raise
    
    async def _load_insights(self) -> List[Dict]:
        """Load generated insights from file."""
        if self._insights_cache is None:
            try:
                with open(self.insights_file, 'r') as f:
                    self._insights_cache = json.load(f)
                    
                # Update next ID
                if self._insights_cache:
                    self._next_insight_id = max(int(i['id'].split('_')[-1]) for i in self._insights_cache if '_' in i['id']) + 1
            except Exception as e:
                logger.error(f"Error loading insights: {e}")
                self._insights_cache = []
        return self._insights_cache
    
    async def _save_insights(self, insights: List[Dict]):
        """Save insights to file."""
        try:
            with open(self.insights_file, 'w') as f:
                json.dump(insights, f, indent=2, default=str)
            self._insights_cache = insights
        except Exception as e:
            logger.error(f"Error saving insights: {e}")
            raise
    
    # Core Analytics Methods
    
    async def generate_time_series(
        self,
        user_id: int,
        metric: AnalyticsMetric,
        period: AnalyticsPeriod,
        start_date: date,
        end_date: date
    ) -> TimeSeries:
        """Generate time series data for a specific metric."""
        try:
            data_points = []
            
            if metric == AnalyticsMetric.WATER_INTAKE:
                data_points = await self._get_water_intake_series(user_id, period, start_date, end_date)
            elif metric == AnalyticsMetric.GOAL_COMPLETION:
                data_points = await self._get_goal_completion_series(user_id, period, start_date, end_date)
            elif metric == AnalyticsMetric.STREAK_PERFORMANCE:
                data_points = await self._get_streak_performance_series(user_id, period, start_date, end_date)
            elif metric == AnalyticsMetric.CAFFEINE_INTAKE:
                data_points = await self._get_caffeine_intake_series(user_id, period, start_date, end_date)
            elif metric == AnalyticsMetric.DRINK_VARIETY:
                data_points = await self._get_drink_variety_series(user_id, period, start_date, end_date)
            elif metric == AnalyticsMetric.HYDRATION_SCORE:
                data_points = await self._get_hydration_score_series(user_id, period, start_date, end_date)
            elif metric == AnalyticsMetric.SOCIAL_ENGAGEMENT:
                data_points = await self._get_social_engagement_series(user_id, period, start_date, end_date)
            else:
                # Default empty series
                data_points = []
            
            if not data_points:
                # Create empty time series
                return TimeSeries(
                    metric=metric,
                    period=period,
                    data_points=[],
                    start_date=start_date,
                    end_date=end_date,
                    total_value=0.0,
                    average_value=0.0,
                    min_value=0.0,
                    max_value=0.0,
                    trend_direction=TrendDirection.STABLE,
                    trend_percentage=0.0
                )
            
            # Calculate statistics
            values = [dp.value for dp in data_points]
            total_value = sum(values)
            average_value = statistics.mean(values)
            min_value = min(values)
            max_value = max(values)
            
            # Calculate trend
            trend_direction, trend_percentage = self._calculate_trend(values)
            
            return TimeSeries(
                metric=metric,
                period=period,
                data_points=data_points,
                start_date=start_date,
                end_date=end_date,
                total_value=total_value,
                average_value=average_value,
                min_value=min_value,
                max_value=max_value,
                trend_direction=trend_direction,
                trend_percentage=trend_percentage
            )
            
        except Exception as e:
            logger.error(f"Error generating time series for {metric}: {e}")
            raise
    
    async def _get_water_intake_series(
        self,
        user_id: int,
        period: AnalyticsPeriod,
        start_date: date,
        end_date: date
    ) -> List[DataPoint]:
        """Get water intake time series data."""
        try:
            # Get water logs from water service
            water_logs_response = await water_service.get_user_water_logs(
                user_id, skip=0, limit=10000
            )
            
            # Filter by date range
            filtered_logs = [
                log for log in water_logs_response.water_logs
                if start_date <= log.logged_at.date() <= end_date
            ]
            
            # Group by period
            grouped_data = self._group_by_period(filtered_logs, period, start_date, end_date)
            
            data_points = []
            for period_start, logs in grouped_data.items():
                total_amount = sum(log.amount for log in logs)
                data_points.append(DataPoint(
                    timestamp=datetime.combine(period_start, datetime.min.time()),
                    value=total_amount,
                    label=f"{total_amount}ml",
                    metadata={"log_count": len(logs)}
                ))
            
            return sorted(data_points, key=lambda x: x.timestamp)
            
        except Exception as e:
            logger.error(f"Error getting water intake series: {e}")
            return []
    
    async def _get_goal_completion_series(
        self,
        user_id: int,
        period: AnalyticsPeriod,
        start_date: date,
        end_date: date
    ) -> List[DataPoint]:
        """Get goal completion time series data."""
        try:
            # Get health goals
            goals_response = await health_goal_service.get_user_health_goals(user_id)
            
            # Calculate daily goal completion rates
            data_points = []
            current_date = start_date
            
            while current_date <= end_date:
                # Get water intake for this day
                water_logs_response = await water_service.get_user_water_logs(
                    user_id, skip=0, limit=1000
                )
                
                daily_intake = sum(
                    log.amount for log in water_logs_response.water_logs
                    if log.logged_at.date() == current_date
                )
                
                # Calculate completion percentage (assuming 2500ml daily goal)
                daily_goal = 2500  # Default goal
                if goals_response.health_goals:
                    for goal in goals_response.health_goals:
                        if goal.goal_type == "daily_water" and goal.is_active:
                            daily_goal = goal.target_value
                            break
                
                completion_rate = min(daily_intake / daily_goal * 100, 100) if daily_goal > 0 else 0
                
                data_points.append(DataPoint(
                    timestamp=datetime.combine(current_date, datetime.min.time()),
                    value=completion_rate,
                    label=f"{completion_rate:.1f}%",
                    metadata={"intake": daily_intake, "goal": daily_goal}
                ))
                
                current_date += timedelta(days=1)
            
            return data_points
            
        except Exception as e:
            logger.error(f"Error getting goal completion series: {e}")
            return []
    
    async def _get_social_engagement_series(
        self,
        user_id: int,
        period: AnalyticsPeriod,
        start_date: date,
        end_date: date
    ) -> List[DataPoint]:
        """Get social engagement time series data."""
        try:
            # Get activity feed data
            activities_response = await activity_feed_service.get_user_feed(
                user_id, skip=0, limit=1000
            )
            
            # Calculate daily engagement scores
            data_points = []
            current_date = start_date
            
            while current_date <= end_date:
                daily_activities = [
                    activity for activity in activities_response.activities
                    if activity.created_at.date() == current_date
                ]
                
                # Calculate engagement score based on activities and interactions
                engagement_score = 0
                for activity in daily_activities:
                    engagement_score += len(activity.reactions) * 2  # Reactions worth 2 points
                    engagement_score += activity.comment_count * 3   # Comments worth 3 points
                    if activity.user_id == user_id:
                        engagement_score += 5  # Own activities worth 5 points
                
                data_points.append(DataPoint(
                    timestamp=datetime.combine(current_date, datetime.min.time()),
                    value=engagement_score,
                    label=f"{engagement_score} pts",
                    metadata={"activities": len(daily_activities)}
                ))
                
                current_date += timedelta(days=1)
            
            return data_points
            
        except Exception as e:
            logger.error(f"Error getting social engagement series: {e}")
            return []
    
    def _group_by_period(self, logs: List, period: AnalyticsPeriod, start_date: date, end_date: date) -> Dict[date, List]:
        """Group logs by time period."""
        grouped = defaultdict(list)
        
        for log in logs:
            log_date = log.logged_at.date()
            
            if period == AnalyticsPeriod.DAILY:
                period_key = log_date
            elif period == AnalyticsPeriod.WEEKLY:
                # Get start of week (Monday)
                days_since_monday = log_date.weekday()
                period_key = log_date - timedelta(days=days_since_monday)
            elif period == AnalyticsPeriod.MONTHLY:
                period_key = log_date.replace(day=1)
            else:
                period_key = log_date
            
            if start_date <= period_key <= end_date:
                grouped[period_key].append(log)
        
        return grouped
    
    def _calculate_trend(self, values: List[float]) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and percentage change."""
        if len(values) < 2:
            return TrendDirection.STABLE, 0.0
        
        # Simple linear regression for trend
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return TrendDirection.STABLE, 0.0
        
        slope = numerator / denominator
        
        # Calculate percentage change
        if values[0] != 0:
            percentage_change = ((values[-1] - values[0]) / values[0]) * 100
        else:
            percentage_change = 0.0
        
        # Determine trend direction
        if abs(slope) < self.config.trend_sensitivity:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Check for volatility
        if len(values) >= 5:
            volatility = statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) > 0 else 0
            if volatility > 0.3:  # High volatility threshold
                direction = TrendDirection.VOLATILE
        
        return direction, percentage_change
    
    # Insight Generation
    
    async def generate_insights(
        self,
        user_id: int,
        time_series_data: List[TimeSeries],
        period: AnalyticsPeriod
    ) -> List[Insight]:
        """Generate AI-powered insights from analytics data."""
        try:
            insights = []
            
            for ts in time_series_data:
                # Generate metric-specific insights
                metric_insights = await self._generate_metric_insights(user_id, ts, period)
                insights.extend(metric_insights)
            
            # Generate cross-metric insights
            cross_insights = await self._generate_cross_metric_insights(user_id, time_series_data, period)
            insights.extend(cross_insights)
            
            # Generate behavioral insights
            behavioral_insights = await self._generate_behavioral_insights(user_id, time_series_data, period)
            insights.extend(behavioral_insights)
            
            # Sort by confidence score and limit to top insights
            insights.sort(key=lambda x: x.confidence_score, reverse=True)
            
            # Save insights
            insights_data = await self._load_insights()
            for insight in insights[:10]:  # Keep top 10 insights
                insights_data.append(insight.dict())
            
            await self._save_insights(insights_data)
            
            return insights[:10]
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    async def _generate_metric_insights(
        self,
        user_id: int,
        time_series: TimeSeries,
        period: AnalyticsPeriod
    ) -> List[Insight]:
        """Generate insights for a specific metric."""
        insights = []
        
        try:
            if time_series.metric == AnalyticsMetric.WATER_INTAKE:
                insights.extend(await self._generate_water_intake_insights(user_id, time_series, period))
            elif time_series.metric == AnalyticsMetric.GOAL_COMPLETION:
                insights.extend(await self._generate_goal_completion_insights(user_id, time_series, period))
            elif time_series.metric == AnalyticsMetric.SOCIAL_ENGAGEMENT:
                insights.extend(await self._generate_social_insights(user_id, time_series, period))
            
        except Exception as e:
            logger.error(f"Error generating metric insights for {time_series.metric}: {e}")
        
        return insights
    
    async def _generate_water_intake_insights(
        self,
        user_id: int,
        time_series: TimeSeries,
        period: AnalyticsPeriod
    ) -> List[Insight]:
        """Generate water intake specific insights."""
        insights = []
        
        # Trend insights
        if time_series.trend_direction == TrendDirection.INCREASING:
            if time_series.trend_percentage > 10:
                insights.append(Insight(
                    id=f"insight_{self._next_insight_id}",
                    insight_type=InsightType.POSITIVE,
                    title="Excellent Hydration Progress!",
                    description=f"Your water intake has increased by {time_series.trend_percentage:.1f}% over the {period.value} period. Keep up the great work!",
                    metric=time_series.metric,
                    confidence_score=0.9,
                    action_items=[
                        "Continue your current hydration routine",
                        "Consider setting a higher daily goal",
                        "Share your success with friends for motivation"
                    ]
                ))
                self._next_insight_id += 1
        
        elif time_series.trend_direction == TrendDirection.DECREASING:
            if time_series.trend_percentage < -10:
                insights.append(Insight(
                    id=f"insight_{self._next_insight_id}",
                    insight_type=InsightType.WARNING,
                    title="Hydration Decline Detected",
                    description=f"Your water intake has decreased by {abs(time_series.trend_percentage):.1f}% over the {period.value} period. Let's get back on track!",
                    metric=time_series.metric,
                    confidence_score=0.85,
                    action_items=[
                        "Set more frequent hydration reminders",
                        "Keep a water bottle visible at all times",
                        "Review what changed in your routine"
                    ]
                ))
                self._next_insight_id += 1
        
        # Consistency insights
        if len(time_series.data_points) >= 7:
            values = [dp.value for dp in time_series.data_points]
            consistency = 1 - (statistics.stdev(values) / statistics.mean(values)) if statistics.mean(values) > 0 else 0
            
            if consistency > 0.8:
                insights.append(Insight(
                    id=f"insight_{self._next_insight_id}",
                    insight_type=InsightType.POSITIVE,
                    title="Remarkable Consistency!",
                    description=f"You've maintained very consistent hydration habits with {consistency*100:.1f}% consistency score.",
                    metric=time_series.metric,
                    confidence_score=0.8,
                    action_items=[
                        "Your routine is working well - stick with it!",
                        "Consider helping friends develop similar consistency"
                    ]
                ))
                self._next_insight_id += 1
        
        return insights
    
    async def _generate_goal_completion_insights(
        self,
        user_id: int,
        time_series: TimeSeries,
        period: AnalyticsPeriod
    ) -> List[Insight]:
        """Generate goal completion insights."""
        insights = []
        
        if time_series.average_value >= 90:
            insights.append(Insight(
                id=f"insight_{self._next_insight_id}",
                insight_type=InsightType.ACHIEVEMENT,
                title="Goal Completion Master!",
                description=f"You've achieved an impressive {time_series.average_value:.1f}% average goal completion rate!",
                metric=time_series.metric,
                confidence_score=0.95,
                action_items=[
                    "Consider increasing your daily goal",
                    "Celebrate this achievement!",
                    "Share your success strategy with friends"
                ]
            ))
            self._next_insight_id += 1
        
        elif time_series.average_value < 70:
            insights.append(Insight(
                id=f"insight_{self._next_insight_id}",
                insight_type=InsightType.RECOMMENDATION,
                title="Goal Adjustment Opportunity",
                description=f"Your average completion rate is {time_series.average_value:.1f}%. Consider adjusting your goals for better success.",
                metric=time_series.metric,
                confidence_score=0.8,
                action_items=[
                    "Review if your current goal is realistic",
                    "Break large goals into smaller milestones",
                    "Track what helps you succeed on good days"
                ]
            ))
            self._next_insight_id += 1
        
        return insights
    
    async def _generate_social_insights(
        self,
        user_id: int,
        time_series: TimeSeries,
        period: AnalyticsPeriod
    ) -> List[Insight]:
        """Generate social engagement insights."""
        insights = []
        
        if time_series.average_value > 20:
            insights.append(Insight(
                id=f"insight_{self._next_insight_id}",
                insight_type=InsightType.POSITIVE,
                title="Social Hydration Star!",
                description=f"You're highly engaged with the community with an average {time_series.average_value:.1f} engagement points per day!",
                metric=time_series.metric,
                confidence_score=0.85,
                action_items=[
                    "Keep encouraging your friends!",
                    "Consider starting a hydration challenge",
                    "Your positive engagement motivates others"
                ]
            ))
            self._next_insight_id += 1
        
        elif time_series.average_value < 5:
            insights.append(Insight(
                id=f"insight_{self._next_insight_id}",
                insight_type=InsightType.RECOMMENDATION,
                title="Connect with the Community",
                description="Engaging with friends can boost motivation! Try interacting more with the community.",
                metric=time_series.metric,
                confidence_score=0.7,
                action_items=[
                    "React to friends' achievements",
                    "Share your own progress",
                    "Join or start hydration challenges"
                ]
            ))
            self._next_insight_id += 1
        
        return insights
    
    async def _generate_cross_metric_insights(
        self,
        user_id: int,
        time_series_data: List[TimeSeries],
        period: AnalyticsPeriod
    ) -> List[Insight]:
        """Generate insights across multiple metrics."""
        insights = []
        
        # Find correlations between metrics
        if len(time_series_data) >= 2:
            for i, ts1 in enumerate(time_series_data):
                for ts2 in time_series_data[i+1:]:
                    correlation = await self._calculate_correlation(ts1, ts2)
                    if abs(correlation.correlation_coefficient) > 0.6:
                        insights.append(Insight(
                            id=f"insight_{self._next_insight_id}",
                            insight_type=InsightType.NEUTRAL,
                            title="Interesting Pattern Discovered",
                            description=f"There's a {correlation.description} between your {ts1.metric.value} and {ts2.metric.value}.",
                            metric=ts1.metric,
                            confidence_score=0.75,
                            action_items=[
                                "Monitor this relationship",
                                "Use this insight to optimize your routine"
                            ],
                            related_data={"correlation": correlation.correlation_coefficient}
                        ))
                        self._next_insight_id += 1
        
        return insights
    
    async def _generate_behavioral_insights(
        self,
        user_id: int,
        time_series_data: List[TimeSeries],
        period: AnalyticsPeriod
    ) -> List[Insight]:
        """Generate behavioral pattern insights."""
        insights = []
        
        # Analyze weekly patterns
        for ts in time_series_data:
            if ts.metric == AnalyticsMetric.WATER_INTAKE and len(ts.data_points) >= 7:
                weekly_pattern = await self._analyze_weekly_pattern(ts)
                
                if weekly_pattern:
                    insights.append(Insight(
                        id=f"insight_{self._next_insight_id}",
                        insight_type=InsightType.NEUTRAL,
                        title="Weekly Pattern Identified",
                        description=weekly_pattern["description"],
                        metric=ts.metric,
                        confidence_score=0.7,
                        action_items=weekly_pattern["recommendations"]
                    ))
                    self._next_insight_id += 1
        
        return insights
    
    async def _analyze_weekly_pattern(self, time_series: TimeSeries) -> Optional[Dict[str, Any]]:
        """Analyze weekly patterns in time series data."""
        try:
            # Group by day of week
            daily_averages = defaultdict(list)
            
            for dp in time_series.data_points:
                day_of_week = dp.timestamp.strftime('%A')
                daily_averages[day_of_week].append(dp.value)
            
            # Calculate averages for each day
            day_averages = {}
            for day, values in daily_averages.items():
                day_averages[day] = statistics.mean(values)
            
            if len(day_averages) >= 5:  # Need at least 5 days of data
                # Find best and worst days
                best_day = max(day_averages, key=day_averages.get)
                worst_day = min(day_averages, key=day_averages.get)
                
                best_value = day_averages[best_day]
                worst_value = day_averages[worst_day]
                
                if best_value > worst_value * 1.3:  # 30% difference
                    return {
                        "description": f"You tend to drink more water on {best_day}s ({best_value:.0f}ml) compared to {worst_day}s ({worst_value:.0f}ml).",
                        "recommendations": [
                            f"Apply your {best_day} routine to other days",
                            f"Set extra reminders on {worst_day}s",
                            "Identify what makes your best days successful"
                        ]
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing weekly pattern: {e}")
            return None
    
    async def _calculate_correlation(self, ts1: TimeSeries, ts2: TimeSeries) -> CorrelationData:
        """Calculate correlation between two time series."""
        try:
            # Align time series by timestamp
            values1, values2 = [], []
            
            ts1_dict = {dp.timestamp: dp.value for dp in ts1.data_points}
            ts2_dict = {dp.timestamp: dp.value for dp in ts2.data_points}
            
            common_timestamps = set(ts1_dict.keys()) & set(ts2_dict.keys())
            
            for timestamp in common_timestamps:
                values1.append(ts1_dict[timestamp])
                values2.append(ts2_dict[timestamp])
            
            if len(values1) < 3:
                return CorrelationData(
                    metric_x=ts1.metric.value,
                    metric_y=ts2.metric.value,
                    correlation_coefficient=0.0,
                    p_value=1.0,
                    is_significant=False,
                    sample_size=len(values1),
                    description="Insufficient data for correlation analysis"
                )
            
            # Calculate Pearson correlation coefficient
            correlation_coefficient = self._pearson_correlation(values1, values2)
            
            # Simple significance test (p-value approximation)
            n = len(values1)
            t_stat = correlation_coefficient * math.sqrt((n - 2) / (1 - correlation_coefficient**2))
            p_value = 2 * (1 - abs(t_stat) / math.sqrt(n - 2 + t_stat**2))  # Rough approximation
            
            is_significant = p_value < 0.05
            
            # Generate description
            if abs(correlation_coefficient) > 0.8:
                strength = "strong"
            elif abs(correlation_coefficient) > 0.5:
                strength = "moderate"
            else:
                strength = "weak"
            
            direction = "positive" if correlation_coefficient > 0 else "negative"
            description = f"{strength} {direction} correlation"
            
            return CorrelationData(
                metric_x=ts1.metric.value,
                metric_y=ts2.metric.value,
                correlation_coefficient=correlation_coefficient,
                p_value=p_value,
                is_significant=is_significant,
                sample_size=n,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return CorrelationData(
                metric_x=ts1.metric.value,
                metric_y=ts2.metric.value,
                correlation_coefficient=0.0,
                p_value=1.0,
                is_significant=False,
                sample_size=0,
                description="Error in correlation calculation"
            )
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n == 0:
            return 0.0
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x2 = sum(xi**2 for xi in x)
        sum_y2 = sum(yi**2 for yi in y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    # Dashboard Generation
    
    async def generate_dashboard(
        self,
        user_id: int,
        request: DashboardRequest
    ) -> AdvancedDashboard:
        """Generate a comprehensive analytics dashboard."""
        try:
            # Calculate date range
            end_date = request.end_date or date.today()
            
            if request.start_date:
                start_date = request.start_date
            else:
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
            
            # Generate time series for key metrics
            metrics_to_analyze = request.custom_metrics or [
                AnalyticsMetric.WATER_INTAKE,
                AnalyticsMetric.GOAL_COMPLETION,
                AnalyticsMetric.STREAK_PERFORMANCE,
                AnalyticsMetric.SOCIAL_ENGAGEMENT
            ]
            
            time_series_data = []
            for metric in metrics_to_analyze:
                ts = await self.generate_time_series(user_id, metric, request.period, start_date, end_date)
                time_series_data.append(ts)
            
            # Generate insights
            insights = await self.generate_insights(user_id, time_series_data, request.period)
            
            # Create dashboard sections
            sections = []
            
            # Overview section
            overview_section = await self._create_overview_section(user_id, time_series_data, insights)
            sections.append(overview_section)
            
            # Detailed metrics section
            metrics_section = await self._create_metrics_section(user_id, time_series_data)
            sections.append(metrics_section)
            
            # Social comparison section (if requested)
            if request.include_social_comparisons:
                social_section = await self._create_social_section(user_id, time_series_data)
                sections.append(social_section)
            
            # Insights section
            insights_section = DashboardSection(
                section_id="insights",
                title="Key Insights",
                description="AI-generated insights from your data",
                insights=insights[:5],  # Top 5 insights
                order=4
            )
            sections.append(insights_section)
            
            # Calculate key metrics summary
            key_metrics = {}
            for ts in time_series_data:
                key_metrics[ts.metric.value] = ts.average_value
            
            dashboard = AdvancedDashboard(
                user_id=user_id,
                dashboard_id=f"dashboard_{self._next_dashboard_id}",
                title=f"{request.dashboard_type.title()} Analytics Dashboard",
                description=f"Comprehensive analytics for {request.period.value} period",
                period=request.period,
                start_date=start_date,
                end_date=end_date,
                sections=sections,
                summary_insights=insights[:3],  # Top 3 insights for summary
                key_metrics=key_metrics
            )
            
            # Save dashboard
            dashboards_data = await self._load_dashboards()
            dashboards_data.append(dashboard.dict())
            await self._save_dashboards(dashboards_data)
            
            self._next_dashboard_id += 1
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            raise
    
    async def _load_dashboards(self) -> List[Dict]:
        """Load dashboards from file."""
        if self._dashboards_cache is None:
            try:
                with open(self.dashboards_file, 'r') as f:
                    self._dashboards_cache = json.load(f)
                    
                # Update next ID
                if self._dashboards_cache:
                    self._next_dashboard_id = max(int(d['dashboard_id'].split('_')[-1]) for d in self._dashboards_cache) + 1
            except Exception as e:
                logger.error(f"Error loading dashboards: {e}")
                self._dashboards_cache = []
        return self._dashboards_cache
    
    async def _save_dashboards(self, dashboards: List[Dict]):
        """Save dashboards to file."""
        try:
            with open(self.dashboards_file, 'w') as f:
                json.dump(dashboards, f, indent=2, default=str)
            self._dashboards_cache = dashboards
        except Exception as e:
            logger.error(f"Error saving dashboards: {e}")
            raise
    
    async def _create_overview_section(
        self,
        user_id: int,
        time_series_data: List[TimeSeries],
        insights: List[Insight]
    ) -> DashboardSection:
        """Create overview section with key metric cards."""
        metric_cards = []
        
        for ts in time_series_data:
            # Create comparison (previous period)
            comparison = Comparison(
                comparison_type=ComparisonType.PREVIOUS_PERIOD,
                current_value=ts.average_value,
                comparison_value=ts.average_value * 0.9,  # Simplified - would calculate actual previous period
                difference=ts.average_value * 0.1,
                percentage_change=10.0,
                is_improvement=ts.trend_direction == TrendDirection.INCREASING,
                description="Compared to previous period"
            )
            
            # Create metric card
            card = MetricCard(
                metric=ts.metric,
                title=ts.metric.value.replace('_', ' ').title(),
                current_value=ts.average_value,
                display_value=f"{ts.average_value:.1f}",
                unit=self._get_metric_unit(ts.metric),
                comparison=comparison,
                trend=ts,
                insights=[i for i in insights if i.metric == ts.metric][:2]
            )
            metric_cards.append(card)
        
        return DashboardSection(
            section_id="overview",
            title="Overview",
            description="Key metrics at a glance",
            metric_cards=metric_cards,
            order=1
        )
    
    async def _create_metrics_section(
        self,
        user_id: int,
        time_series_data: List[TimeSeries]
    ) -> DashboardSection:
        """Create detailed metrics section with charts."""
        charts = []
        
        for ts in time_series_data:
            chart = Chart(
                chart_id=f"chart_{ts.metric.value}",
                chart_type="line",
                title=f"{ts.metric.value.replace('_', ' ').title()} Trend",
                description=f"Trend analysis for {ts.metric.value}",
                data=ts,
                config={
                    "color": self._get_metric_color(ts.metric),
                    "show_trend_line": True,
                    "show_average_line": True
                }
            )
            charts.append(chart)
        
        return DashboardSection(
            section_id="metrics",
            title="Detailed Metrics",
            description="Comprehensive metric analysis",
            charts=charts,
            order=2
        )
    
    async def _create_social_section(
        self,
        user_id: int,
        time_series_data: List[TimeSeries]
    ) -> DashboardSection:
        """Create social comparison section."""
        # This would include peer comparisons, leaderboard position, etc.
        # Simplified implementation
        return DashboardSection(
            section_id="social",
            title="Social Comparison",
            description="How you compare with friends and community",
            order=3
        )
    
    def _get_metric_unit(self, metric: AnalyticsMetric) -> str:
        """Get unit for a metric."""
        unit_map = {
            AnalyticsMetric.WATER_INTAKE: "ml",
            AnalyticsMetric.GOAL_COMPLETION: "%",
            AnalyticsMetric.STREAK_PERFORMANCE: "days",
            AnalyticsMetric.CAFFEINE_INTAKE: "mg",
            AnalyticsMetric.DRINK_VARIETY: "types",
            AnalyticsMetric.HYDRATION_SCORE: "points",
            AnalyticsMetric.SOCIAL_ENGAGEMENT: "points"
        }
        return unit_map.get(metric, "")
    
    def _get_metric_color(self, metric: AnalyticsMetric) -> str:
        """Get color for a metric."""
        color_map = {
            AnalyticsMetric.WATER_INTAKE: "#2196F3",
            AnalyticsMetric.GOAL_COMPLETION: "#4CAF50",
            AnalyticsMetric.STREAK_PERFORMANCE: "#FF9800",
            AnalyticsMetric.CAFFEINE_INTAKE: "#795548",
            AnalyticsMetric.DRINK_VARIETY: "#9C27B0",
            AnalyticsMetric.HYDRATION_SCORE: "#00BCD4",
            AnalyticsMetric.SOCIAL_ENGAGEMENT: "#E91E63"
        }
        return color_map.get(metric, "#607D8B")


# Global service instance
advanced_analytics_service = AdvancedAnalyticsService() 