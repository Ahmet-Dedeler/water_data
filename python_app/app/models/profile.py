from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class AvatarStyle(str, Enum):
    DEFAULT = "default"
    CUSTOM = "custom"
    GENERATED = "generated"

class ThemePreference(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"

class LayoutStyle(str, Enum):
    DEFAULT = "default"
    COMPACT = "compact"
    DETAILED = "detailed"

class BadgeRarity(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class UserProfileUpdateExtended(BaseModel):
    # Basic profile info
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=150)
    pronouns: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)
    language_preference: Optional[str] = Field(None, max_length=10)
    
    # Customization
    avatar_style: Optional[AvatarStyle] = None
    avatar_data: Optional[Dict[str, Any]] = None
    theme_preference: Optional[ThemePreference] = None
    theme_data: Optional[Dict[str, Any]] = None
    banner_color_hex: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    banner_image_url: Optional[str] = Field(None, max_length=500)
    
    # Privacy settings
    show_email: Optional[bool] = None
    show_location: Optional[bool] = None
    show_achievements: Optional[bool] = None
    show_stats: Optional[bool] = None
    show_activity: Optional[bool] = None
    allow_friend_requests: Optional[bool] = None
    allow_challenge_invites: Optional[bool] = None
    
    # Gamification
    favorite_water_type: Optional[str] = Field(None, max_length=100)
    hydration_motto: Optional[str] = Field(None, max_length=200)
    achievements_showcase: Optional[List[str]] = None
    badges_showcase: Optional[List[int]] = None
    
    # Goals
    daily_goal_ml: Optional[int] = Field(None, ge=500, le=10000)

class ProfileBadgeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon_emoji: Optional[str] = Field(None, max_length=10)
    icon_url: Optional[str] = Field(None, max_length=500)
    rarity: BadgeRarity = BadgeRarity.COMMON
    unlock_criteria: Optional[Dict[str, Any]] = None
    is_active: bool = True

class ProfileBadgeCreate(ProfileBadgeBase):
    pass

class ProfileBadgeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon_emoji: Optional[str] = Field(None, max_length=10)
    icon_url: Optional[str] = Field(None, max_length=500)
    rarity: Optional[BadgeRarity] = None
    unlock_criteria: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ProfileBadge(ProfileBadgeBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserBadgeBase(BaseModel):
    user_id: int
    badge_id: int
    is_showcased: bool = False

class UserBadgeCreate(BaseModel):
    badge_id: int

class UserBadge(UserBadgeBase):
    id: int
    earned_at: datetime
    badge: Optional[ProfileBadge] = None
    
    class Config:
        from_attributes = True

class ProfileThemeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color_scheme: Dict[str, Any] = Field(..., description="JSON with color definitions")
    is_premium: bool = False
    unlock_level: int = Field(1, ge=1)
    unlock_points: int = Field(0, ge=0)
    preview_image_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True

class ProfileThemeCreate(ProfileThemeBase):
    pass

class ProfileThemeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color_scheme: Optional[Dict[str, Any]] = None
    is_premium: Optional[bool] = None
    unlock_level: Optional[int] = Field(None, ge=1)
    unlock_points: Optional[int] = Field(None, ge=0)
    preview_image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class ProfileTheme(ProfileThemeBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserThemeBase(BaseModel):
    user_id: int
    theme_id: int
    is_active: bool = False

class UserThemeCreate(BaseModel):
    theme_id: int

class UserTheme(UserThemeBase):
    id: int
    unlocked_at: datetime
    theme: Optional[ProfileTheme] = None
    
    class Config:
        from_attributes = True

class AvatarAssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    asset_url: str = Field(..., max_length=500)
    rarity: BadgeRarity = BadgeRarity.COMMON
    unlock_level: int = Field(1, ge=1)
    unlock_points: int = Field(0, ge=0)
    is_premium: bool = False
    is_active: bool = True

class AvatarAssetCreate(AvatarAssetBase):
    pass

class AvatarAssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    asset_url: Optional[str] = Field(None, max_length=500)
    rarity: Optional[BadgeRarity] = None
    unlock_level: Optional[int] = Field(None, ge=1)
    unlock_points: Optional[int] = Field(None, ge=0)
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None

class AvatarAsset(AvatarAssetBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserAvatarAssetBase(BaseModel):
    user_id: int
    asset_id: int

class UserAvatarAssetCreate(BaseModel):
    asset_id: int

class UserAvatarAsset(UserAvatarAssetBase):
    id: int
    unlocked_at: datetime
    asset: Optional[AvatarAsset] = None
    
    class Config:
        from_attributes = True

class ProfileCustomizationBase(BaseModel):
    user_id: int
    layout_style: LayoutStyle = LayoutStyle.DEFAULT
    widget_preferences: Optional[Dict[str, Any]] = None
    custom_css: Optional[str] = Field(None, max_length=10000)
    background_pattern: Optional[str] = Field(None, max_length=50)
    animation_preferences: Optional[Dict[str, Any]] = None
    font_preferences: Optional[Dict[str, Any]] = None

class ProfileCustomizationCreate(BaseModel):
    layout_style: Optional[LayoutStyle] = LayoutStyle.DEFAULT
    widget_preferences: Optional[Dict[str, Any]] = None
    custom_css: Optional[str] = Field(None, max_length=10000)
    background_pattern: Optional[str] = Field(None, max_length=50)
    animation_preferences: Optional[Dict[str, Any]] = None
    font_preferences: Optional[Dict[str, Any]] = None

class ProfileCustomizationUpdate(BaseModel):
    layout_style: Optional[LayoutStyle] = None
    widget_preferences: Optional[Dict[str, Any]] = None
    custom_css: Optional[str] = Field(None, max_length=10000)
    background_pattern: Optional[str] = Field(None, max_length=50)
    animation_preferences: Optional[Dict[str, Any]] = None
    font_preferences: Optional[Dict[str, Any]] = None

class ProfileCustomization(ProfileCustomizationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserTitleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    unlock_criteria: Optional[Dict[str, Any]] = None
    rarity: BadgeRarity = BadgeRarity.COMMON
    color_hex: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    is_active: bool = True

class UserTitleCreate(UserTitleBase):
    pass

class UserTitleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    unlock_criteria: Optional[Dict[str, Any]] = None
    rarity: Optional[BadgeRarity] = None
    color_hex: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    is_active: Optional[bool] = None

class UserTitle(UserTitleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserTitleOwnershipBase(BaseModel):
    user_id: int
    title_id: int
    is_active: bool = False

class UserTitleOwnershipCreate(BaseModel):
    title_id: int

class UserTitleOwnership(UserTitleOwnershipBase):
    id: int
    earned_at: datetime
    title: Optional[UserTitle] = None
    
    class Config:
        from_attributes = True

class ProfileShowcaseBase(BaseModel):
    user_id: int
    featured_achievement_id: Optional[str] = None
    featured_badge_ids: Optional[List[int]] = None
    featured_stats: Optional[List[str]] = None
    featured_quote: Optional[str] = Field(None, max_length=200)
    showcase_order: Optional[List[str]] = None

class ProfileShowcaseCreate(BaseModel):
    featured_achievement_id: Optional[str] = None
    featured_badge_ids: Optional[List[int]] = None
    featured_stats: Optional[List[str]] = None
    featured_quote: Optional[str] = Field(None, max_length=200)
    showcase_order: Optional[List[str]] = None

class ProfileShowcaseUpdate(BaseModel):
    featured_achievement_id: Optional[str] = None
    featured_badge_ids: Optional[List[int]] = None
    featured_stats: Optional[List[str]] = None
    featured_quote: Optional[str] = Field(None, max_length=200)
    showcase_order: Optional[List[str]] = None

class ProfileShowcase(ProfileShowcaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProfileVisitBase(BaseModel):
    visitor_id: int
    visited_id: int

class ProfileVisit(ProfileVisitBase):
    id: int
    visited_at: datetime
    
    class Config:
        from_attributes = True

class CompleteUserProfile(BaseModel):
    # Basic user info
    user_id: int
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    pronouns: Optional[str] = None
    
    # Profile images and theme
    profile_picture_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    banner_color_hex: Optional[str] = None
    avatar_style: str = "default"
    avatar_data: Optional[Dict[str, Any]] = None
    theme_preference: str = "auto"
    active_theme: Optional[ProfileTheme] = None
    
    # Stats and gamification
    level: int
    xp: int
    total_xp: int
    points: int
    current_streak: int
    longest_streak: int
    daily_goal_ml: int
    
    # Profile customization
    active_title: Optional[UserTitle] = None
    showcased_badges: List[ProfileBadge] = []
    showcased_achievements: List[str] = []
    profile_completion_percentage: float
    is_verified: bool
    verification_badge: Optional[str] = None
    
    # Privacy and social
    is_public: bool
    show_email: bool
    show_location: bool
    show_achievements: bool
    show_stats: bool
    show_activity: bool
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime
    
    # Social stats
    followers_count: int = 0
    following_count: int = 0
    profile_visits_count: int = 0

class ProfileAnalytics(BaseModel):
    user_id: int
    total_profile_views: int
    unique_profile_views: int
    profile_views_last_30_days: int
    profile_completion_score: float
    customization_level: str  # 'basic', 'intermediate', 'advanced'
    most_viewed_sections: List[Dict[str, Any]]
    engagement_metrics: Dict[str, Any]

class ProfileStats(BaseModel):
    total_profiles: int
    verified_profiles: int
    average_completion_percentage: float
    most_popular_themes: List[Dict[str, Any]]
    most_earned_badges: List[Dict[str, Any]]
    customization_adoption_rates: Dict[str, float]

class AvatarBuilder(BaseModel):
    user_id: int
    available_assets: Dict[str, List[AvatarAsset]]  # Grouped by category
    current_avatar: Dict[str, Any]
    unlocked_assets: List[int]
    recommended_assets: List[AvatarAsset]

class ThemePreview(BaseModel):
    theme_id: int
    name: str
    color_scheme: Dict[str, Any]
    preview_image_url: Optional[str]
    is_unlocked: bool
    unlock_requirements: Optional[Dict[str, Any]] 