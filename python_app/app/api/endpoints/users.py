from fastapi import APIRouter, HTTPException, status, Depends, Query, Response, UploadFile, File
from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
import os

from app.models import BaseResponse
from app.models.user import (
    User, UserCreate, UserUpdate, UserProfile, UserProfileUpdate,
    UserLogin, PasswordChange, PasswordReset, PasswordResetConfirm,
    Token, UserPreferences, UserPreferencesUpdate, DailyStreak, StreakSummary
)
from app.services.user_service import UserService
from app.core.auth import (
    AuthManager, get_current_active_user,
    get_current_admin_user, get_current_user_optional
)
from app.api.dependencies import get_db
from app.utils.email_utils import send_email
from app.services.recommendation_service import RecommendationService
from app.models.recommendation import UserPreferenceProfile

logger = logging.getLogger(__name__)
router = APIRouter()
user_service = UserService()
recommendation_service = RecommendationService()

AVATAR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'avatars')
os.makedirs(AVATAR_DIR, exist_ok=True)

class UserDeletionConfirmation(BaseModel):
    """Model for confirming user deletion with a password."""
    password: str = Field(..., description="Your current password to confirm account deletion.")

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED, summary="Create a new user", description="Registers a new user in the system and sends a verification email.", responses={400: {"description": "Email already registered"}})
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        return user_service.create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token, summary="User Login", description="Authenticate a user and return an access token.", responses={401: {"description": "Incorrect username or password"}})
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = user_service.authenticate_user(db, email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = AuthManager.create_access_token(data=token_data)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User, summary="Get current user's profile", description="Fetches the profile of the currently authenticated user.")
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=User, summary="Update current user's profile", description="Updates the profile information (bio, name) of the currently authenticated user.")
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information."""
    try:
        return user_service.update_user(db, current_user.id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    user = user_service.authenticate_user(db, email=current_user.email, password=password_change.current_password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user_service.change_password(db, current_user.id, password_change.new_password)


@router.get("/me/profile", response_model=UserProfile)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile."""
    profile = user_service.get_user_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/me/profile", response_model=UserProfile)
def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    updated_profile = user_service.update_user_profile(db, current_user.id, profile_update)
    if not updated_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return updated_profile


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    confirmation: UserDeletionConfirmation,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's account and all associated data.
    This action is irreversible and requires password confirmation.
    """
    try:
        success = user_service.request_account_deletion(
            db=db,
            user_id=current_user.id,
            password=confirmation.password
        )
        if not success:
            # This case should ideally not be hit if the user is authenticated,
            # but it's good practice to handle it.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except ValueError as e:
        # This will be raised for an incorrect password
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Admin endpoints
@router.get("/", response_model=List[User], dependencies=[Depends(get_current_admin_user)])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """[Admin] Get all users with pagination."""
    return user_service.get_all_users(db, skip=skip, limit=limit)


@router.get("/search", response_model=List[User], dependencies=[Depends(get_current_admin_user)])
def search_users_admin(query: str, limit: int = 20, db: Session = Depends(get_db)):
    """[Admin] Search for users by username or email."""
    return user_service.search_users(db, query=query, limit=limit)


@router.get("/{user_id}", response_model=User, dependencies=[Depends(get_current_admin_user)], summary="Get user by ID", description="Fetches a user's public profile by their ID. Requires admin privileges.", responses={404: {"description": "User not found"}})
def get_user_by_id_admin(user_id: int, db: Session = Depends(get_db)):
    """[Admin] Get a specific user by ID."""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}/profile", response_model=UserProfile, dependencies=[Depends(get_current_admin_user)])
def update_user_profile_admin(user_id: int, profile_update: UserProfileUpdate, db: Session = Depends(get_db)):
    """[Admin] Update any user's profile."""
    profile = user_service.update_user_profile(db, user_id, profile_update)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.post("/{user_id}/activate", response_model=User, dependencies=[Depends(get_current_admin_user)])
def activate_user_admin(user_id: int, db: Session = Depends(get_db)):
    """[Admin] Activate a user account."""
    user_service.activate_user(db, user_id)
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/{user_id}/promote", response_model=User, dependencies=[Depends(get_current_admin_user)])
def promote_user_to_admin_admin(user_id: int, db: Session = Depends(get_db)):
    """[Admin] Promote a user to the admin role."""
    user = user_service.promote_to_admin(db, user_id)
    if not user:
        raise HTTPException(status_code=4.04, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_admin_user)])
def deactivate_user_admin(user_id: int, db: Session = Depends(get_db)):
    """[Admin] Deactivate a user account."""
    user_service.deactivate_user(db, user_id)
    return


@router.get("/profile", response_model=BaseResponse[UserProfile])
async def get_user_profile(current_user: dict = Depends(get_current_active_user)):
    """Get user profile."""
    try:
        profile = await user_service.get_user_profile(current_user["user_id"])
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return BaseResponse(
            data=profile,
            message="Profile retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/profile", response_model=BaseResponse[UserProfile])
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update user profile."""
    try:
        updated_profile = await user_service.update_user_profile(
            current_user["user_id"], 
            profile_update
        )
        if not updated_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return BaseResponse(
            data=updated_profile,
            message="Profile updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=BaseResponse[List[User]])
async def search_users(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Search users (admin only)."""
    try:
        users = await user_service.search_users(query=query, limit=limit)
        return BaseResponse(
            data=users,
            message=f"Found {len(users)} users matching '{query}'"
        )
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{user_id}/profile", response_model=BaseResponse[UserProfile])
async def update_any_user_profile(
    user_id: int,
    profile_update: UserProfileUpdate,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Update any user's profile (admin only)."""
    try:
        updated_profile = await user_service.update_user_profile(user_id, profile_update)
        if not updated_profile:
            raise HTTPException(status_code=404, detail="Profile not found for the specified user.")
        
        return BaseResponse(
            data=updated_profile,
            message="User profile updated successfully by admin."
        )
    except Exception as e:
        logger.error(f"Admin error updating profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify-email", response_model=BaseResponse[dict])
async def verify_email(token: str):
    """Verify user's email address."""
    try:
        email = AuthManager.verify_email_token(token)
        success = await user_service.verify_email(email)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return BaseResponse(
            data={"verified": True},
            message="Email verified successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/overview", response_model=BaseResponse[dict])
async def get_user_stats(admin_user: dict = Depends(get_current_admin_user)):
    """Get user statistics overview (admin only)."""
    try:
        total_users = await user_service.get_user_count()
        all_users = await user_service.get_all_users(skip=0, limit=10000)  # Get all for stats
        
        # Calculate statistics
        active_users = len([u for u in all_users if u.is_active])
        verified_users = len([u for u in all_users if u.is_verified])
        admin_users = len([u for u in all_users if u.role == "admin"])
        moderator_users = len([u for u in all_users if u.role == "moderator"])
        
        # Recent registrations (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = len([
            u for u in all_users 
            if datetime.fromisoformat(u.created_at.replace('Z', '+00:00')) > thirty_days_ago
        ])
        
        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "admin_users": admin_users,
            "moderator_users": moderator_users,
            "recent_registrations": recent_users,
            "verification_rate": round((verified_users / total_users) * 100, 1) if total_users > 0 else 0,
            "activity_rate": round((active_users / total_users) * 100, 1) if total_users > 0 else 0
        }
        
        return BaseResponse(
            data=stats,
            message="User statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/me/profile/avatar", response_model=UserProfile)
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a new profile picture for the current user."""
    ext = os.path.splitext(file.filename)[1]
    filename = f"user_{current_user.id}{ext}"
    file_path = os.path.join(AVATAR_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    url = f"/static/avatars/{filename}"
    profile_update = UserProfileUpdate(profile_picture_url=url)
    updated_profile = user_service.update_user_profile(db, current_user.id, profile_update)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return updated_profile


@router.get("/me/profile/avatar", summary="Get user avatar", description="Retrieves the current user's profile picture.", response_class=FileResponse, responses={200: {
    "content": {"image/png": {}, "image/jpeg": {}, "image/gif": {}},
    "description": "The user's avatar image.",
}, 404: {"description": "Avatar not found"}})
def get_avatar(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get the current user's profile picture file."""
    profile = user_service.get_user_profile(db, current_user.id)
    if not profile or not profile.profile_picture_url:
        raise HTTPException(status_code=404, detail="No avatar set")
    file_path = os.path.join(AVATAR_DIR, os.path.basename(profile.profile_picture_url))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Avatar file not found")
    return FileResponse(file_path)


@router.delete("/me/profile/avatar", response_model=UserProfile)
def delete_avatar(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Delete the current user's profile picture."""
    profile = user_service.get_user_profile(db, current_user.id)
    if not profile or not profile.profile_picture_url:
        raise HTTPException(status_code=404, detail="No avatar set")
    file_path = os.path.join(AVATAR_DIR, os.path.basename(profile.profile_picture_url))
    if os.path.exists(file_path):
        os.remove(file_path)
    profile_update = UserProfileUpdate(profile_picture_url=None)
    updated_profile = user_service.update_user_profile(db, current_user.id, profile_update)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return updated_profile


@router.post("/password-reset-request")
def password_reset_request(data: PasswordReset, db: Session = Depends(get_db)):
    """Request a password reset (send email with token)."""
    user = user_service.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = AuthManager.generate_password_reset_token(user.email)
    reset_link = f"https://yourdomain.com/reset-password?token={token}"
    send_email(
        to_email=user.email,
        subject="Password Reset Request",
        body=f"Click the link to reset your password: {reset_link}"
    )
    return {"message": "Password reset email sent."}


@router.post("/password-reset-confirm")
def password_reset_confirm(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset (set new password)."""
    email = AuthManager.verify_password_reset_token(data.token)
    user = user_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.change_password(db, user.id, data.new_password)
    return {"message": "Password has been reset."}


@router.post("/send-verification-email")
def send_verification_email(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Send email verification link to the current user."""
    token = AuthManager.generate_verification_token(current_user.email)
    verify_link = f"https://yourdomain.com/verify-email?token={token}"
    send_email(
        to_email=current_user.email,
        subject="Verify Your Email",
        body=f"Click the link to verify your email: {verify_link}"
    )
    return {"message": "Verification email sent."}


@router.get("/me/preferences", response_model=UserPreferenceProfile)
def get_my_preferences(current_user: User = Depends(get_current_active_user)):
    """Get the current user's preference profile."""
    profile = recommendation_service.get_user_preference_profile(current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Preference profile not found")
    return profile


@router.put("/me/preferences", response_model=UserPreferenceProfile)
def update_my_preferences(
    preferences: UserPreferenceProfile,
    current_user: User = Depends(get_current_active_user)
):
    """Update the current user's preference profile."""
    updated = recommendation_service.update_user_preference_profile(current_user.id, preferences)
    if not updated:
        raise HTTPException(status_code=404, detail="Preference profile not found")
    return updated


@router.get("/me/streaks/summary", response_model=StreakSummary)
def get_my_streak_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive streak summary for current user."""
    return user_service.get_streak_summary(db, current_user.id)


@router.get("/me/streaks", response_model=List[DailyStreak])
def get_my_daily_streaks(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily streak records for current user."""
    return user_service.get_daily_streaks(db, current_user.id, limit)


@router.get("/me/streaks/stats")
def get_my_streak_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed streak statistics for current user."""
    return user_service.get_streak_stats(db, current_user.id)


@router.get("/{user_id}/streaks/summary", response_model=StreakSummary)
def get_user_streak_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get streak summary for a specific user."""
    # Check if user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Allow access to public profiles or own profile
    profile = user_service.get_user_profile(db, user_id)
    if not profile or (not profile.is_public and user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return user_service.get_streak_summary(db, user_id)


@router.get("/{user_id}/streaks", response_model=List[DailyStreak])
def get_user_daily_streaks(
    user_id: int,
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily streak records for a specific user."""
    # Check if user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Allow access to public profiles or own profile
    profile = user_service.get_user_profile(db, user_id)
    if not profile or (not profile.is_public and user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return user_service.get_daily_streaks(db, user_id, limit)


@router.get("/{user_id}/streaks/stats")
def get_user_streak_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed streak statistics for a specific user."""
    # Check if user exists
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Allow access to public profiles or own profile
    profile = user_service.get_user_profile(db, user_id)
    if not profile or (not profile.is_public and user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return user_service.get_streak_stats(db, user_id)


# Profile Management Endpoints

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile with customization options"""
    from app.services.profile_service import profile_service
    
    # Record profile visit if different user
    if current_user.id != user_id:
        await profile_service.record_profile_visit(current_user.id, user_id)
    
    profile = await profile_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    from app.services.profile_service import profile_service
    
    profile = await profile_service.update_user_profile(
        current_user.id, 
        profile_data.dict(exclude_unset=True)
    )
    return profile

@router.get("/profile/avatar/assets", response_model=List[AvatarAssetResponse])
async def get_avatar_assets(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available avatar assets"""
    from app.services.profile_service import profile_service
    
    assets = await profile_service.get_avatar_assets(category)
    return assets

@router.get("/profile/avatar/owned", response_model=List[AvatarAssetResponse])
async def get_owned_avatar_assets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's owned avatar assets"""
    from app.services.profile_service import profile_service
    
    assets = await profile_service.get_user_avatar_assets(current_user.id)
    return assets

@router.post("/profile/avatar/unlock/{asset_id}")
async def unlock_avatar_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlock avatar asset with points"""
    from app.services.profile_service import profile_service
    
    try:
        user_asset = await profile_service.unlock_avatar_asset(current_user.id, asset_id)
        return {"message": "Avatar asset unlocked successfully", "asset": user_asset}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile/themes", response_model=List[ProfileThemeResponse])
async def get_available_themes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available profile themes"""
    from app.services.profile_service import profile_service
    
    themes = await profile_service.get_available_themes()
    return themes

@router.get("/profile/themes/owned", response_model=List[ProfileThemeResponse])
async def get_owned_themes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's owned themes"""
    from app.services.profile_service import profile_service
    
    themes = await profile_service.get_user_themes(current_user.id)
    return themes

@router.post("/profile/themes/unlock/{theme_id}")
async def unlock_theme(
    theme_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlock theme with points"""
    from app.services.profile_service import profile_service
    
    try:
        user_theme = await profile_service.unlock_theme(current_user.id, theme_id)
        return {"message": "Theme unlocked successfully", "theme": user_theme}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile/badges", response_model=List[ProfileBadgeResponse])
async def get_user_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's badges"""
    from app.services.profile_service import profile_service
    
    badges = await profile_service.get_user_badges(current_user.id)
    return badges

@router.get("/profile/titles", response_model=List[UserTitleResponse])
async def get_user_titles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's titles"""
    from app.services.profile_service import profile_service
    
    titles = await profile_service.get_user_titles(current_user.id)
    return titles

@router.post("/profile/titles/{title_id}/equip")
async def equip_title(
    title_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Equip a title"""
    from app.services.profile_service import profile_service
    
    try:
        await profile_service.equip_title(current_user.id, title_id)
        return {"message": "Title equipped successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/profile/titles/unequip")
async def unequip_title(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unequip current title"""
    from app.services.profile_service import profile_service
    
    await profile_service.unequip_title(current_user.id)
    return {"message": "Title unequipped successfully"}

@router.get("/profile/showcase", response_model=ProfileShowcaseResponse)
async def get_profile_showcase(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's profile showcase"""
    from app.services.profile_service import profile_service
    
    showcase = await profile_service.get_profile_showcase(current_user.id)
    if not showcase:
        raise HTTPException(status_code=404, detail="Showcase not found")
    
    return showcase

@router.put("/profile/showcase", response_model=ProfileShowcaseResponse)
async def update_profile_showcase(
    showcase_data: ProfileShowcaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's profile showcase"""
    from app.services.profile_service import profile_service
    
    showcase = await profile_service.update_profile_showcase(
        current_user.id,
        showcase_data.dict(exclude_unset=True)
    )
    return showcase

@router.get("/profile/visits", response_model=List[ProfileVisitResponse])
async def get_profile_visits(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent profile visits"""
    from app.services.profile_service import profile_service
    
    visits = await profile_service.get_profile_visits(current_user.id, days)
    return visits

@router.get("/profile/analytics", response_model=ProfileAnalyticsResponse)
async def get_profile_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive profile analytics"""
    from app.services.profile_service import profile_service
    
    analytics = await profile_service.get_profile_analytics(current_user.id)
    return analytics

@router.get("/profile/customization", response_model=ProfileCustomizationResponse)
async def get_profile_customization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's profile customization settings"""
    from app.services.profile_service import profile_service
    
    customization = await profile_service.get_profile_customization(current_user.id)
    if not customization:
        raise HTTPException(status_code=404, detail="Customization not found")
    
    return customization

@router.put("/profile/customization", response_model=ProfileCustomizationResponse)
async def update_profile_customization(
    customization_data: ProfileCustomizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's profile customization settings"""
    from app.services.profile_service import profile_service
    
    customization = await profile_service.update_profile_customization(
        current_user.id,
        customization_data.dict(exclude_unset=True)
    )
    return customization

# Admin Profile Management Endpoints

@router.post("/admin/profile/badges", response_model=ProfileBadgeResponse)
async def create_badge(
    badge_data: ProfileBadgeCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new badge (admin only)"""
    from app.services.profile_service import profile_service
    
    badge = await profile_service.create_badge(badge_data.dict())
    return badge

@router.post("/admin/profile/themes", response_model=ProfileThemeResponse)
async def create_theme(
    theme_data: ProfileThemeCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new theme (admin only)"""
    from app.services.profile_service import profile_service
    
    theme = await profile_service.create_theme(theme_data.dict())
    return theme

@router.post("/admin/profile/avatar-assets", response_model=AvatarAssetResponse)
async def create_avatar_asset(
    asset_data: AvatarAssetCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new avatar asset (admin only)"""
    from app.services.profile_service import profile_service
    
    asset = await profile_service.create_avatar_asset(asset_data.dict())
    return asset

@router.post("/admin/profile/titles", response_model=UserTitleResponse)
async def create_user_title(
    title_data: UserTitleCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user title (admin only)"""
    from app.services.profile_service import profile_service
    
    title = await profile_service.create_user_title(title_data.dict())
    return title

@router.post("/admin/profile/award-badge/{user_id}/{badge_id}")
async def award_badge(
    user_id: int,
    badge_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Award a badge to a user (admin only)"""
    from app.services.profile_service import profile_service
    
    try:
        user_badge = await profile_service.award_badge_to_user(user_id, badge_id, reason)
        return {"message": "Badge awarded successfully", "user_badge": user_badge}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/profile/award-title/{user_id}/{title_id}")
async def award_title(
    user_id: int,
    title_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Award a title to a user (admin only)"""
    from app.services.profile_service import profile_service
    
    try:
        ownership = await profile_service.award_title_to_user(user_id, title_id, reason)
        return {"message": "Title awarded successfully", "ownership": ownership}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/admin/profile/moderation-queue")
async def get_moderation_queue(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get profiles that need moderation (admin only)"""
    from app.services.profile_service import profile_service
    
    queue = await profile_service.get_profile_moderation_queue()
    return queue

@router.post("/admin/profile/moderate/{user_id}")
async def moderate_profile(
    user_id: int,
    action: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Moderate a user profile (admin only)"""
    from app.services.profile_service import profile_service
    
    if action not in ['approve', 'reject', 'flag']:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    success = await profile_service.moderate_profile(user_id, action, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {"message": f"Profile {action}ed successfully"} 