from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HealthIntegrationBase(BaseModel):
    provider: str
    access_token: str
    refresh_token: Optional[str] = None

class HealthIntegrationCreate(HealthIntegrationBase):
    pass

class HealthIntegration(HealthIntegrationBase):
    id: int
    user_id: int
    last_sync_at: Optional[datetime] = None

    class Config:
        orm_mode = True 