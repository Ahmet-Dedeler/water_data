from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Reminder(BaseModel):
    """Model for a user-defined reminder."""
    id: int
    user_id: int
    cron_schedule: str = Field(..., description="Cron-style schedule (e.g., '0 9-17 * * *' for every hour from 9 to 5).")
    message: str = Field(default="Time to drink some water!", description="Custom reminder message.")
    is_active: bool = Field(default=True, description="Whether the reminder is active.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class ReminderCreate(BaseModel):
    """Model for creating a reminder."""
    cron_schedule: str
    message: Optional[str] = "Time to drink some water!"
    is_active: Optional[bool] = True

class ReminderUpdate(BaseModel):
    """Model for updating a reminder."""
    cron_schedule: Optional[str] = None
    message: Optional[str] = None
    is_active: Optional[bool] = None 