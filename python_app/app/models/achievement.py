from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.database import Base

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    icon_url = Column(String)
    
    # New fields for multi-stage and secret achievements
    total_stages = Column(Integer, default=1, nullable=False)
    secret = Column(Boolean, default=False, nullable=False)
    
    # Self-referencing foreign key for multi-stage achievements
    parent_id = Column(Integer, ForeignKey("achievements.id"), nullable=True)
    parent = relationship("Achievement", remote_side=[id], back_populates="stages")
    stages = relationship("Achievement", back_populates="parent")
    
    # A JSON field to hold the criteria for unlocking the achievement
    # Example: {"type": "log_count", "value": 10}
    # Example: {"type": "streak_days", "values": [1, 3, 7, 14]}
    criteria = Column(JSON, nullable=False)

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    
    # New field to track progress for multi-stage achievements
    current_stage = Column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")

class UserAchievementDetail(Achievement):
    date_earned: datetime 