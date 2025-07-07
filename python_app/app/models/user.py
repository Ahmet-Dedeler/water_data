from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserProfile(BaseModel):
    """Extended user profile with preferences."""
    user_id: int = Field(..., description="User ID")
    bio: Optional[str] = Field(default=None, max_length=500, description="User's biography")
    location: Optional[str] = Field(default=None, max_length=100, description="User's location")
    website: Optional[str] = Field(default=None, max_length=200, description="User's personal or social media website")
    status: Optional[str] = Field(default=None, max_length=150, description="A short status message from the user.")
    profile_picture_url: Optional[str] = Field(default=None, max_length=500, description="URL of the user's profile picture.")
    banner_color_hex: Optional[str] = Field(default=None, max_length=7, description="Hex color code for the profile banner.")
    is_public: bool = Field(default=True, description="Whether the user's profile is public.")
    
    # Streaks
    current_streak: int = Field(default=0, description="Current daily logging streak.")
    longest_streak: int = Field(default=0, description="Longest daily logging streak.")
    last_log_date: Optional[datetime] = Field(default=None, description="The date of the last water log.")

    # Goals
    daily_goal_ml: int = Field(default=2000, ge=0, description="Custom daily water intake goal in milliliters.")
    health_goals: List[str] = Field(default=[], description="User's health goals")
    dietary_restrictions: List[str] = Field(default=[], description="Dietary restrictions")
    preferred_packaging: List[str] = Field(default=[], description="Preferred packaging types")
    max_budget: Optional[float] = Field(default=None, ge=0, description="Maximum budget per bottle")
    avoid_contaminants: List[str] = Field(default=[], description="Contaminants to avoid")
    min_health_score: Optional[int] = Field(default=None, ge=0, le=100, description="Minimum acceptable health score")
    notifications_enabled: bool = Field(default=True, description="Enable notifications")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Profile update timestamp")
    level: int
    xp: int
    points: int
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "health_goals": ["hydration", "mineral_balance", "detox"],
                "dietary_restrictions": ["low_sodium", "fluoride_free"],
                "preferred_packaging": ["glass", "aluminum"],
                "max_budget": 5.0,
                "avoid_contaminants": ["chlorine", "heavy_metals"],
                "min_health_score": 80,
                "notifications_enabled": True
            }
        }


class User(BaseModel):
    """User model for authentication."""
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Full name")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Account status")
    is_verified: bool = Field(default=False, description="Email verification status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    profile_picture: Optional[str] = Field(default=None, description="Profile picture URL")
    profile: Optional[UserProfile] = Field(default=None, description="User profile")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "wateruser123",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "created_at": "2023-01-01T00:00:00Z",
                "last_login": "2023-12-01T10:30:00Z",
                "profile": None
            }
        }


class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr = Field(..., description="Email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Full name")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "wateruser123",
                "password": "SecurePass123",
                "full_name": "John Doe"
            }
        }


class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[EmailStr] = Field(default=None, description="Email address")
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="Username")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Full name")
    profile_picture: Optional[str] = Field(default=None, description="Profile picture URL")


class UserProfileUpdate(BaseModel):
    """Model for updating user profile."""
    bio: Optional[str] = Field(default=None, max_length=500, description="User's biography")
    location: Optional[str] = Field(default=None, max_length=100, description="User's location")
    website: Optional[str] = Field(default=None, max_length=200, description="User's personal or social media website")
    status: Optional[str] = Field(default=None, max_length=150, description="A short status message from the user.")
    profile_picture_url: Optional[str] = Field(default=None, max_length=500, description="URL of the user's profile picture.")
    banner_color_hex: Optional[str] = Field(default=None, max_length=7, description="Hex color code for the profile banner.")
    is_public: Optional[bool] = Field(default=None, description="Whether the user's profile is public.")
    daily_goal_ml: Optional[int] = Field(default=None, ge=0, description="Custom daily water intake goal in milliliters.")
    health_goals: Optional[List[str]] = Field(default=None, description="User's health goals")
    dietary_restrictions: Optional[List[str]] = Field(default=None, description="Dietary restrictions")
    preferred_packaging: Optional[List[str]] = Field(default=None, description="Preferred packaging types")
    max_budget: Optional[float] = Field(default=None, ge=0, description="Maximum budget per bottle")
    avoid_contaminants: Optional[List[str]] = Field(default=None, description="Contaminants to avoid")
    min_health_score: Optional[int] = Field(default=None, ge=0, le=100, description="Minimum acceptable health score")
    notifications_enabled: Optional[bool] = Field(default=None, description="Enable notifications")


class Token(BaseModel):
    """JWT token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class PasswordChange(BaseModel):
    """Model for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordReset(BaseModel):
    """Model for password reset."""
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserPreferencesUpdate(BaseModel):
    dark_mode: Optional[bool] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notification_frequency: Optional[str] = None


class DailyStreakBase(BaseModel):
    date: datetime
    goal_met: bool = False
    total_volume_ml: float = 0.0
    goal_volume_ml: float
    percentage_completed: float = 0.0
    streak_day: int = 0


class DailyStreakCreate(DailyStreakBase):
    pass


class DailyStreakUpdate(BaseModel):
    goal_met: Optional[bool] = None
    total_volume_ml: Optional[float] = None
    goal_volume_ml: Optional[float] = None
    percentage_completed: Optional[float] = None
    streak_day: Optional[int] = None


class DailyStreak(DailyStreakBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


class StreakSummary(BaseModel):
    current_streak: int
    longest_streak: int
    total_streak_days: int
    last_streak_date: Optional[datetime]
    current_streak_percentage: float
    streak_history: List[DailyStreak] 