from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Comment(BaseModel):
    id: int
    user_id: int
    user_achievement_id: int
    content: str
    created_at: datetime
    username: str
    profile_picture_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000) 