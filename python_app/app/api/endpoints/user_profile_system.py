from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from pydantic import BaseModel

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.user_profile_system import (
    UserProfile, UserPreferences, UserPrivacySettings, UserCustomizations,
    ProfileVisibility, ThemePreference, LanguageCode, UnitSystem, ActivityLevel,
    NotificationFrequency, DataSharingLevel, PrivacyLevel,
    UserProfileCreate, UserProfileUpdate, UserPreferencesUpdate,
    UserPrivacySettingsUpdate, UserCustomizationsUpdate,
    UserProfileResponse, UserPreferencesResponse, UserPrivacySettingsResponse,
    UserHealthProfileResponse
)
from app.services.user_profile_system_service import UserProfileSystemService

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependency to get profile service
def get_profile_service(db: Session = Depends(get_db)) -> UserProfileSystemService:
    return UserProfileSystemService(db)

# Profile Management Endpoints
@router.post("/profile", response_model=Dict[str, Any])
async def create_user_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Create a new user profile"""
    try:
        profile = service.create_user_profile(current_user.id, profile_data.dict(exclude_unset=True))
        
        return {
            "success": True,
            "message": "Profile created successfully",
            "profile": {
                "id": profile.id,
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "profile_completion_percentage": profile.profile_completion_percentage,
                "created_at": profile.created_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get current user's profile"""
    try:
        profile = service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return UserProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            display_name=profile.display_name,
            bio=profile.bio,
            location=profile.location,
            website=profile.website,
            birth_date=profile.birth_date,
            gender=profile.gender,
            avatar_url=profile.avatar_url,
            profile_visibility=profile.profile_visibility,
            height=profile.height,
            weight=profile.weight,
            activity_level=profile.activity_level,
            timezone=profile.timezone,
            is_verified=profile.is_verified,
            profile_completion_percentage=profile.profile_completion_percentage,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_profile_by_user_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get another user's profile (respecting privacy settings)"""
    try:
        profile = service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Check if profile is visible to current user
        if profile.profile_visibility == ProfileVisibility.PRIVATE and profile.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Profile is private")
        
        # Return limited information based on privacy settings
        return UserProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            display_name=profile.display_name if profile.show_real_name or profile.user_id == current_user.id else None,
            bio=profile.bio,
            location=profile.location if profile.show_location or profile.user_id == current_user.id else None,
            website=profile.website,
            birth_date=None,  # Never show birth date to others
            gender=profile.gender,
            avatar_url=profile.avatar_url,
            profile_visibility=profile.profile_visibility,
            height=None,  # Don't show physical stats to others
            weight=None,
            activity_level=profile.activity_level if profile.show_stats else None,
            timezone=None,  # Don't show timezone to others
            is_verified=profile.is_verified,
            profile_completion_percentage=profile.profile_completion_percentage if profile.show_stats else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Update current user's profile"""
    try:
        profile = service.update_user_profile(
            current_user.id, 
            profile_update.dict(exclude_unset=True)
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile": {
                "id": profile.id,
                "display_name": profile.display_name,
                "profile_completion_percentage": profile.profile_completion_percentage,
                "updated_at": profile.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/profile", response_model=Dict[str, Any])
async def delete_user_profile(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Delete current user's profile"""
    try:
        success = service.delete_user_profile(current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "message": "Profile deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Avatar Management
@router.post("/profile/avatar", response_model=Dict[str, Any])
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Upload user avatar"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if avatar.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
        
        # Validate file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB
        avatar_data = await avatar.read()
        if len(avatar_data) > max_size:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")
        
        # Upload avatar
        avatar_url = service.upload_avatar(current_user.id, avatar_data, avatar.filename)
        if not avatar_url:
            raise HTTPException(status_code=500, detail="Failed to upload avatar")
        
        return {
            "success": True,
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/profile/avatar", response_model=Dict[str, Any])
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Delete user avatar"""
    try:
        profile = service.update_user_profile(current_user.id, {"avatar_url": None})
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "message": "Avatar deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Preferences Management
@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get current user's preferences"""
    try:
        preferences = service.get_user_preferences(current_user.id)
        if not preferences:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        return UserPreferencesResponse(
            language=preferences.language,
            timezone=preferences.timezone,
            unit_system=preferences.unit_system,
            theme=preferences.theme,
            notification_frequency=preferences.notification_frequency,
            default_container_size=preferences.default_container_size,
            reminder_interval=preferences.reminder_interval,
            smart_reminders=preferences.smart_reminders,
            weather_adjustments=preferences.weather_adjustments,
            activity_adjustments=preferences.activity_adjustments,
            data_sharing_level=preferences.data_sharing_level,
            analytics_tracking=preferences.analytics_tracking,
            updated_at=preferences.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences", response_model=Dict[str, Any])
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Update current user's preferences"""
    try:
        preferences = service.update_user_preferences(
            current_user.id, 
            preferences_update.dict(exclude_unset=True)
        )
        if not preferences:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": {
                "language": preferences.language.value,
                "unit_system": preferences.unit_system.value,
                "theme": preferences.theme.value,
                "updated_at": preferences.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Privacy Settings Management
@router.get("/privacy", response_model=UserPrivacySettingsResponse)
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get current user's privacy settings"""
    try:
        privacy_settings = service.get_user_privacy_settings(current_user.id)
        if not privacy_settings:
            raise HTTPException(status_code=404, detail="Privacy settings not found")
        
        return UserPrivacySettingsResponse(
            privacy_level=privacy_settings.privacy_level,
            allow_analytics=privacy_settings.allow_analytics,
            profile_searchable=privacy_settings.profile_searchable,
            show_in_leaderboards=privacy_settings.show_in_leaderboards,
            share_anonymous_data=privacy_settings.share_anonymous_data,
            allow_marketing_emails=privacy_settings.allow_marketing_emails,
            allow_location_tracking=privacy_settings.allow_location_tracking,
            two_factor_enabled=privacy_settings.two_factor_enabled,
            data_retention_period=privacy_settings.data_retention_period,
            updated_at=privacy_settings.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/privacy", response_model=Dict[str, Any])
async def update_privacy_settings(
    privacy_update: UserPrivacySettingsUpdate,
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Update current user's privacy settings"""
    try:
        privacy_settings = service.update_user_privacy_settings(
            current_user.id, 
            privacy_update.dict(exclude_unset=True)
        )
        if not privacy_settings:
            raise HTTPException(status_code=404, detail="Privacy settings not found")
        
        return {
            "success": True,
            "message": "Privacy settings updated successfully",
            "privacy_settings": {
                "privacy_level": privacy_settings.privacy_level.value,
                "allow_analytics": privacy_settings.allow_analytics,
                "profile_searchable": privacy_settings.profile_searchable,
                "updated_at": privacy_settings.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Customizations Management
@router.get("/customizations", response_model=Dict[str, Any])
async def get_user_customizations(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get current user's customizations"""
    try:
        customizations = service.get_user_customizations(current_user.id)
        if not customizations:
            raise HTTPException(status_code=404, detail="Customizations not found")
        
        return {
            "primary_color": customizations.primary_color,
            "secondary_color": customizations.secondary_color,
            "accent_color": customizations.accent_color,
            "dashboard_layout": customizations.dashboard_layout,
            "widget_preferences": customizations.widget_preferences,
            "custom_hydration_goals": customizations.custom_hydration_goals,
            "favorite_drink_types": customizations.favorite_drink_types,
            "quick_actions": customizations.quick_actions,
            "updated_at": customizations.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/customizations", response_model=Dict[str, Any])
async def update_user_customizations(
    customizations_update: UserCustomizationsUpdate,
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Update current user's customizations"""
    try:
        customizations = service.update_user_customizations(
            current_user.id, 
            customizations_update.dict(exclude_unset=True)
        )
        if not customizations:
            raise HTTPException(status_code=404, detail="Customizations not found")
        
        return {
            "success": True,
            "message": "Customizations updated successfully",
            "customizations": {
                "primary_color": customizations.primary_color,
                "secondary_color": customizations.secondary_color,
                "accent_color": customizations.accent_color,
                "updated_at": customizations.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Profile Analytics
@router.get("/analytics", response_model=Dict[str, Any])
async def get_profile_analytics(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get profile analytics and recommendations"""
    try:
        analytics = service.get_profile_analytics(current_user.id)
        
        return {
            "completion_percentage": analytics.completion_percentage,
            "missing_fields": analytics.missing_fields,
            "recommendations": analytics.recommendations,
            "verification_status": analytics.verification_status,
            "engagement_score": analytics.engagement_score,
            "analytics_generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting profile analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Profile Search and Discovery
@router.get("/search", response_model=List[UserProfileResponse])
async def search_profiles(
    query: str = Query(..., min_length=2, max_length=100),
    location: Optional[str] = Query(None, max_length=200),
    activity_level: Optional[ActivityLevel] = None,
    verified_only: Optional[bool] = False,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Search user profiles"""
    try:
        filters = {}
        if location:
            filters["location"] = location
        if activity_level:
            filters["activity_level"] = activity_level
        if verified_only:
            filters["verified_only"] = verified_only
        
        profiles = service.search_profiles(query, filters, limit)
        
        return [
            UserProfileResponse(
                id=profile.id,
                user_id=profile.user_id,
                display_name=profile.display_name,
                bio=profile.bio,
                location=profile.location if profile.show_location else None,
                website=profile.website,
                birth_date=None,  # Never show in search results
                gender=profile.gender,
                avatar_url=profile.avatar_url,
                profile_visibility=profile.profile_visibility,
                height=None,  # Don't show in search results
                weight=None,
                activity_level=profile.activity_level if profile.show_stats else None,
                timezone=None,
                is_verified=profile.is_verified,
                profile_completion_percentage=profile.profile_completion_percentage if profile.show_stats else None,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
            for profile in profiles
        ]
    except Exception as e:
        logger.error(f"Error searching profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions", response_model=List[UserProfileResponse])
async def get_profile_suggestions(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get profile suggestions for current user"""
    try:
        suggestions = service.get_profile_suggestions(current_user.id, limit)
        
        return [
            UserProfileResponse(
                id=profile.id,
                user_id=profile.user_id,
                display_name=profile.display_name,
                bio=profile.bio,
                location=profile.location if profile.show_location else None,
                website=profile.website,
                birth_date=None,
                gender=profile.gender,
                avatar_url=profile.avatar_url,
                profile_visibility=profile.profile_visibility,
                height=None,
                weight=None,
                activity_level=profile.activity_level if profile.show_stats else None,
                timezone=None,
                is_verified=profile.is_verified,
                profile_completion_percentage=profile.profile_completion_percentage if profile.show_stats else None,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
            for profile in suggestions
        ]
    except Exception as e:
        logger.error(f"Error getting profile suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Profile Verification
@router.post("/verify", response_model=Dict[str, Any])
async def verify_profile(
    verification_type: str = "email",
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Verify current user's profile"""
    try:
        success = service.verify_profile(current_user.id, verification_type)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "message": "Profile verified successfully",
            "verification_type": verification_type,
            "verified_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/verify", response_model=Dict[str, Any])
async def unverify_profile(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Remove verification from current user's profile"""
    try:
        success = service.unverify_profile(current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "message": "Profile verification removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unverifying profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# System Endpoints
@router.get("/statistics", response_model=Dict[str, Any])
async def get_profile_statistics(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Get overall profile system statistics"""
    try:
        statistics = service.get_profile_statistics()
        return statistics
    except Exception as e:
        logger.error(f"Error getting profile statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_inactive_profiles(
    days_inactive: int = Query(365, ge=30, le=3650),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Clean up inactive profiles (admin only)"""
    try:
        # Add admin check here if needed
        background_tasks.add_task(service.cleanup_inactive_profiles, days_inactive)
        
        return {
            "success": True,
            "message": f"Cleanup started for profiles inactive for {days_inactive} days"
        }
    except Exception as e:
        logger.error(f"Error starting cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Profile Export
@router.get("/export", response_model=Dict[str, Any])
async def export_profile_data(
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Export user's profile data (GDPR compliance)"""
    try:
        profile = service.get_user_profile(current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        preferences = service.get_user_preferences(current_user.id)
        privacy_settings = service.get_user_privacy_settings(current_user.id)
        customizations = service.get_user_customizations(current_user.id)
        
        export_data = {
            "profile": {
                "id": profile.id,
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "bio": profile.bio,
                "location": profile.location,
                "website": profile.website,
                "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
                "gender": profile.gender,
                "height": profile.height,
                "weight": profile.weight,
                "activity_level": profile.activity_level.value if profile.activity_level else None,
                "timezone": profile.timezone,
                "wake_up_time": profile.wake_up_time,
                "sleep_time": profile.sleep_time,
                "is_verified": profile.is_verified,
                "verification_date": profile.verification_date.isoformat() if profile.verification_date else None,
                "profile_completion_percentage": profile.profile_completion_percentage,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            },
            "preferences": {
                "language": preferences.language.value if preferences else None,
                "timezone": preferences.timezone if preferences else None,
                "unit_system": preferences.unit_system.value if preferences else None,
                "theme": preferences.theme.value if preferences else None,
                "notification_frequency": preferences.notification_frequency.value if preferences else None,
                "default_container_size": preferences.default_container_size if preferences else None,
                "reminder_interval": preferences.reminder_interval if preferences else None,
                "smart_reminders": preferences.smart_reminders if preferences else None,
                "weather_adjustments": preferences.weather_adjustments if preferences else None,
                "activity_adjustments": preferences.activity_adjustments if preferences else None
            } if preferences else None,
            "privacy_settings": {
                "privacy_level": privacy_settings.privacy_level.value if privacy_settings else None,
                "allow_analytics": privacy_settings.allow_analytics if privacy_settings else None,
                "profile_searchable": privacy_settings.profile_searchable if privacy_settings else None,
                "show_in_leaderboards": privacy_settings.show_in_leaderboards if privacy_settings else None,
                "share_anonymous_data": privacy_settings.share_anonymous_data if privacy_settings else None,
                "allow_marketing_emails": privacy_settings.allow_marketing_emails if privacy_settings else None,
                "allow_location_tracking": privacy_settings.allow_location_tracking if privacy_settings else None,
                "data_retention_period": privacy_settings.data_retention_period if privacy_settings else None
            } if privacy_settings else None,
            "customizations": {
                "primary_color": customizations.primary_color if customizations else None,
                "secondary_color": customizations.secondary_color if customizations else None,
                "accent_color": customizations.accent_color if customizations else None,
                "dashboard_layout": customizations.dashboard_layout if customizations else None,
                "widget_preferences": customizations.widget_preferences if customizations else None,
                "custom_hydration_goals": customizations.custom_hydration_goals if customizations else None,
                "favorite_drink_types": customizations.favorite_drink_types if customizations else None,
                "quick_actions": customizations.quick_actions if customizations else None
            } if customizations else None,
            "export_date": datetime.utcnow().isoformat(),
            "export_version": "1.0"
        }
        
        return {
            "success": True,
            "message": "Profile data exported successfully",
            "data": export_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting profile data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Profile Import
@router.post("/import", response_model=Dict[str, Any])
async def import_profile_data(
    import_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    service: UserProfileSystemService = Depends(get_profile_service)
):
    """Import user's profile data"""
    try:
        # Validate import data structure
        if "profile" not in import_data:
            raise HTTPException(status_code=400, detail="Invalid import data: missing profile section")
        
        # Import profile data
        profile_data = import_data["profile"]
        profile_data.pop("id", None)  # Remove ID to avoid conflicts
        profile_data.pop("user_id", None)  # Remove user_id to avoid conflicts
        
        # Update or create profile
        existing_profile = service.get_user_profile(current_user.id)
        if existing_profile:
            profile = service.update_user_profile(current_user.id, profile_data)
        else:
            profile = service.create_user_profile(current_user.id, profile_data)
        
        # Import preferences if provided
        if "preferences" in import_data and import_data["preferences"]:
            service.update_user_preferences(current_user.id, import_data["preferences"])
        
        # Import privacy settings if provided
        if "privacy_settings" in import_data and import_data["privacy_settings"]:
            service.update_user_privacy_settings(current_user.id, import_data["privacy_settings"])
        
        # Import customizations if provided
        if "customizations" in import_data and import_data["customizations"]:
            service.update_user_customizations(current_user.id, import_data["customizations"])
        
        return {
            "success": True,
            "message": "Profile data imported successfully",
            "profile_id": profile.id if profile else None,
            "imported_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing profile data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 