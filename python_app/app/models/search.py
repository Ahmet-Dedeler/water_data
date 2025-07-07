from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class WaterLogSearchCriteria(BaseModel):
    start_date: Optional[date] = Field(default=None, description="The start date for the search range.")
    end_date: Optional[date] = Field(default=None, description="The end date for the search range.")
    min_volume: Optional[float] = Field(default=None, ge=0, description="Minimum volume in a single log (ml).")
    max_volume: Optional[float] = Field(default=None, ge=0, description="Maximum volume in a single log (ml).")
    brand_names: Optional[List[str]] = Field(default=None, description="A list of brand names to include.")
    packaging_types: Optional[List[str]] = Field(default=None, description="A list of packaging types to include.")

class WaterLogDetails(BaseModel):
    id: int
    date: datetime
    volume: float
    water_data: WaterData
    
    class Config:
        from_attributes = True 