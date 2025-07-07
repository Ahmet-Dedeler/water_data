from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import date, timedelta

class ProgressDataPoint(BaseModel):
    period_start: date = Field(..., description="The start date of the data point's period.")
    period_end: date = Field(..., description="The end date of the data point's period.")
    value: float = Field(..., description="The value for this data point (e.g., average daily volume).")

class ProgressAnalytics(BaseModel):
    user_id: int = Field(..., description="The ID of the user.")
    time_granularity: str = Field(..., description="The granularity of the time series (e.g., 'weekly', 'monthly').")
    data_points: List[ProgressDataPoint] = Field(..., description="The list of data points for the time series.")

class GlobalAnalytics(BaseModel):
    total_users: int = Field(..., description="Total number of registered users.")
    total_water_logs: int = Field(..., description="Total number of water logs across all users.")
    total_volume_logged: float = Field(..., description="Total volume of water logged in liters.")
    most_popular_brand: Optional[str] = Field(None, description="The most frequently logged water brand across the platform.")
    platform_wide_packaging_breakdown: Dict[str, int] = Field(..., description="A breakdown of logs by packaging type across the platform.")

class UserAnalytics(BaseModel):
    """Personalized analytics for a user's water consumption."""
    user_id: int = Field(..., description="The ID of the user.")
    period_start_date: date = Field(..., description="The start date of the analytics period.")
    period_end_date: date = Field(..., description="The end date of the analytics period.")
    
    total_logs: int = Field(..., description="Total number of water intake logs in the period.")
    total_volume: float = Field(..., description="Total volume of water consumed in liters.")
    average_daily_volume: float = Field(..., description="Average daily consumption in liters.")
    
    most_frequent_brand: Optional[str] = Field(None, description="The most frequently logged water brand.")
    packaging_breakdown: Dict[str, int] = Field(..., description="A breakdown of logs by packaging type.")
    consumption_heatmap: Dict[str, List[int]] = Field(..., description="Consumption heatmap by day of week and hour.")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "period_start_date": "2023-01-01",
                "period_end_date": "2023-01-31",
                "total_logs": 58,
                "total_volume": 116.5,
                "average_daily_volume": 3.76,
                "most_frequent_brand": "Fiji",
                "packaging_breakdown": {
                    "plastic": 40,
                    "glass": 18
                },
                "consumption_heatmap": {
                    "monday": [0, 0, ..., 2, 5, 1, 0],
                    "tuesday": [0, 1, ..., 3, 4, 2, 0]
                }
            }
        }

class ConsumptionHeatmap(BaseModel):
    """
    Represents a heatmap of water consumption, where keys are dates (YYYY-MM-DD)
    and values are the total volume consumed on that day.
    """
    heatmap: Dict[str, float]

class BrandAnalytics(BaseModel):
    """Analytics specific to a water brand for a user."""
    brand_name: str
    total_volume_ml: float
    total_logs: int
    first_logged_date: str
    last_logged_date: str

class GlobalStats(BaseModel):
    """Anonymous, global statistics about water consumption."""
    total_users: int
    total_water_logs: int
    total_volume_logged_ml: float
    most_popular_brand: str
    average_daily_intake_ml: float

class ProgressOverTime(BaseModel):
    user_id: int
    period: str
    data_points: List[ProgressDataPoint]

class TimeSeriesDataPoint(BaseModel):
    timestamp: date
    value: float

class TimeSeriesAnalytics(BaseModel):
    user_id: int
    start_date: date
    end_date: date
    granularity: str  # 'daily', 'weekly', 'monthly'
    data_points: List[TimeSeriesDataPoint] 