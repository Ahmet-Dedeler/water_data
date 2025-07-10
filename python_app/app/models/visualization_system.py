from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
import enum

# --- Enums for Visualization ---

class ChartType(str, enum.Enum):
    TIME_SERIES = "time_series"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"

class TimeInterval(str, enum.Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# --- Generic Chart Data Structures ---

class DataPoint(BaseModel):
    x: Union[str, int, float, datetime, date]
    y: Union[int, float]
    z: Optional[Union[int, float]] = None # For bubble charts or 3D plots

class DataSet(BaseModel):
    label: str
    data: List[DataPoint]
    color: Optional[str] = None # e.g., "#FF5733"

# Time Series Chart
class TimeSeriesData(BaseModel):
    datasets: List[DataSet]
    x_axis_label: str = "Time"
    y_axis_label: str = "Value"

# Bar Chart
class BarChartData(BaseModel):
    labels: List[str] # e.g., ["Mon", "Tue", "Wed"]
    datasets: List[DataSet]
    y_axis_label: str = "Value"

# Pie/Doughnut Chart
class PieChartDataPoint(BaseModel):
    label: str
    value: Union[int, float]
    color: Optional[str] = None

class PieChartData(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]] # e.g., [{"data": [300, 50, 100], "backgroundColor": [...]}]

# Gauge Chart
class GaugeData(BaseModel):
    value: float
    max_value: float
    label: str
    color_ranges: Optional[List[Dict[str, Any]]] = None # e.g., [{"from": 0, "to": 50, "color": "red"}]

# --- Specific Dashboard/Report Schemas ---

class HydrationVsTimeData(BaseModel):
    chart_type: ChartType = ChartType.TIME_SERIES
    title: str = "Hydration Over Time"
    data: TimeSeriesData

class DrinkTypeDistributionData(BaseModel):
    chart_type: ChartType = ChartType.PIE
    title: str = "Drink Type Distribution"
    data: PieChartData

class DailyIntakeComparisonData(BaseModel):
    chart_type: ChartType = ChartType.BAR
    title: str = "Daily Intake vs. Goal"
    data: BarChartData

class UserEngagementHeatmapData(BaseModel):
    chart_type: ChartType = ChartType.HEATMAP
    title: str = "User Engagement Heatmap"
    data: List[DataPoint] # x=day, y=hour, z=intensity

class OverallHydrationScore(BaseModel):
    chart_type: ChartType = ChartType.GAUGE
    title: str = "Overall Hydration Score"
    data: GaugeData

# A composite model for a full dashboard
class HydrationDashboard(BaseModel):
    hydration_over_time: HydrationVsTimeData
    drink_distribution: DrinkTypeDistributionData
    daily_comparison: DailyIntakeComparisonData
    hydration_score: OverallHydrationScore 