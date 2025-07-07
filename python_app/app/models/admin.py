from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class AdminDashboardStats(BaseModel):
    total_users: int
    new_users_today: int
    total_water_logs: int
    total_volume_logged_ml: float
    active_reminders: int
    active_api_keys: int

class UserAdminView(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True 