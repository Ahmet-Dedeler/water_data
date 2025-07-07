from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class DeviceType(str, Enum):
    IOS = "ios"
    ANDROID = "android"

class Device(BaseModel):
    id: int
    user_id: int
    token: str
    device_type: DeviceType
    
    class Config:
        from_attributes = True

class DeviceCreate(BaseModel):
    token: str = Field(..., description="The unique device token for push notifications.")
    device_type: DeviceType 