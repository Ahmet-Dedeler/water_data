from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from typing import Optional
from pydantic import BaseModel, Field

from app.db.database import Base

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar_url = Column(String)
    bio = Column(String)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # New fields for streaks
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_log_date = Column(DateTime, nullable=True)

    # Relationships
    water_logs = relationship("WaterLog", back_populates="user")
    health_goals = relationship("HealthGoal", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    followers = relationship("Follower", foreign_keys="[Follower.followed_id]", back_populates="followed", cascade="all, delete-orphan")
    following = relationship("Follower", foreign_keys="[Follower.follower_id]", back_populates="follower", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", uselist=False, back_populates="user")

class UserProfile(BaseModel):
    id: int
    user_id: int
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    profile_picture_url: Optional[str] = None
    banner_color_hex: Optional[str] = None
    is_public: bool
    current_streak: int
    longest_streak: int
    last_log_date: Optional[datetime] = None
    daily_goal_ml: int
    level: int
    xp: int
    points: int

    class Config:
        orm_mode = True

class UserProfileUpdate(BaseModel):
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    profile_picture_url: Optional[str] = None
    banner_color_hex: Optional[str] = None
    is_public: Optional[bool] = None
    daily_goal_ml: Optional[int] = None

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username must be between 3 and 50 characters.") 