from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    EXCEL = "xlsx"


class ExportScope(str, Enum):
    """Data scopes for export."""
    ALL_WATER_DATA = "all_water_data"
    USER_PROFILE = "user_profile"
    USER_REVIEWS = "user_reviews"
    USER_HEALTH_GOALS = "user_health_goals"
    RECOMMENDATION_HISTORY = "recommendation_history"


class ExportConfig(BaseModel):
    """Configuration for a data export job."""
    file_name: str = Field(..., description="Name of the export file")
    export_format: ExportFormat = Field(..., description="Format of the export")
    scope: ExportScope = Field(..., description="Scope of the data to export")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters to apply to the data")


class ExportJobStatus(str, Enum):
    """Status of an export job."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJob(BaseModel):
    """Represents a data export job."""
    id: str = Field(..., description="Unique identifier for the export job")
    user_id: int = Field(..., description="User who initiated the export")
    config: ExportConfig = Field(..., description="Configuration for the export")
    status: ExportJobStatus = Field(default=ExportJobStatus.PENDING, description="Current status of the job")
    file_path: Optional[str] = Field(default=None, description="Path to the exported file")
    error_message: Optional[str] = Field(default=None, description="Error message if the job failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the job was created")
    completed_at: Optional[datetime] = Field(default=None, description="When the job was completed") 