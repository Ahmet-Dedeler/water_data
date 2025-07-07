from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.db.models import (
    User, UserProfile, ProfileBadge, UserBadge, ProfileTheme, UserTheme,
    AvatarAsset, UserAvatarAsset, ProfileCustomization, UserTitle,
    UserTitleOwnership, ProfileShowcase, ProfileVisit
)
from app.models.profile import (
    CompleteUserProfile, ProfileAnalytics, ProfileStats, AvatarBuilder,
    ThemePreview, UserProfileUpdateExtended, ProfileBadgeCreate, ProfileThemeCreate,
    AvatarAssetCreate, UserTitleCreate, ProfileCustomizationCreate,
    ProfileShowcaseCreate
)
from app.services.points_service import points_service
from app.services.level_service import level_service

class ProfileService:
    def __init__(self):
        self.points_service = points_service
        self.level_service = level_service

    def get_complete_profile(self, db: Session, user_id: int, viewer_id: Optional[int] = None) -> Optional[CompleteUserProfile]:
        """Get complete user profile with all customization data"""
        user = db.query(User).filter_by(id=user_id).first()
        if not user or not user.profile:
            return None

        profile = user.profile

        # Check privacy settings
        if viewer_id != user_id and not profile.is_public:
            return None

        # Record profile visit if viewer is different
        if viewer_id and viewer_id != user_id:
            self._record_profile_visit(db, viewer_id, user_id)

        # Get active title
        active_title_ownership = db.query(UserTitleOwnership).filter(
            UserTitleOwnership.user_id == user_id,
            UserTitleOwnership.is_active == True
        ).first()
        active_title = active_title_ownership.title if active_title_ownership else None

        # Get showcased badges
        showcased_badges = db.query(ProfileBadge).join(
            UserBadge, ProfileBadge.id == UserBadge.badge_id
        ).filter(
            UserBadge.user_id == user_id,
            UserBadge.is_showcased == True
        ).all()

        # Get active theme
        active_user_theme = db.query(UserTheme).filter(
            UserTheme.user_id == user_id,
            UserTheme.is_active == True
        ).first()
        active_theme = active_user_theme.theme if active_user_theme else None

        # Get social stats
        followers_count = db.query(func.count()).select_from(
            db.query(User).join(User.followers).filter(User.id == user_id).subquery()
        ).scalar() or 0
        
        following_count = db.query(func.count()).select_from(
            db.query(User).join(User.following).filter(User.id == user_id).subquery()
        ).scalar() or 0

        profile_visits_count = db.query(ProfileVisit).filter_by(visited_id=user_id).count()

        return CompleteUserProfile(
            user_id=user.id,
            username=user.username,
            display_name=profile.display_name,
            bio=profile.bio,
            location=profile.location if profile.show_location else None,
            website=profile.website,
            status=profile.status,
            pronouns=profile.pronouns,
            profile_picture_url=profile.profile_picture_url,
            banner_image_url=profile.banner_image_url,
            banner_color_hex=profile.banner_color_hex,
            avatar_style=profile.avatar_style,
            avatar_data=profile.avatar_data,
            theme_preference=profile.theme_preference,
            active_theme=active_theme,
            level=profile.level,
            xp=profile.xp,
            total_xp=profile.total_xp,
            points=profile.points,
            current_streak=profile.current_streak,
            longest_streak=profile.longest_streak,
            daily_goal_ml=profile.daily_goal_ml,
            active_title=active_title,
            showcased_badges=showcased_badges,
            showcased_achievements=profile.achievements_showcase or [],
            profile_completion_percentage=profile.profile_completion_percentage,
            is_verified=profile.is_verified,
            verification_badge=profile.verification_badge,
            is_public=profile.is_public,
            show_email=profile.show_email,
            show_location=profile.show_location,
            show_achievements=profile.show_achievements,
            show_stats=profile.show_stats,
            show_activity=profile.show_activity,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            last_active_at=profile.last_active_at,
            followers_count=followers_count,
            following_count=following_count,
            profile_visits_count=profile_visits_count
        )

    def update_profile_extended(self, db: Session, user_id: int, profile_data: UserProfileUpdateExtended) -> Dict[str, Any]:
        """Update user profile with extended customization options"""
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not profile:
            return {"success": False, "message": "Profile not found"}

        # Update fields
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        # Update completion percentage
        profile.profile_completion_percentage = self._calculate_profile_completion(profile)
        profile.updated_at = datetime.utcnow()

        db.add(profile)
        db.commit()

        return {
            "success": True,
            "profile_completion_percentage": profile.profile_completion_percentage,
            "updated_fields": list(update_data.keys())
        }

    def unlock_badge(self, db: Session, user_id: int, badge_id: int) -> Dict[str, Any]:
        """Unlock a badge for a user"""
        # Check if badge exists
        badge = db.query(ProfileBadge).filter_by(id=badge_id).first()
        if not badge:
            return {"success": False, "message": "Badge not found"}

        # Check if already unlocked
        existing = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id
        ).first()
        if existing:
            return {"success": False, "message": "Badge already unlocked"}

        # Check unlock criteria (simplified)
        if badge.unlock_criteria:
            # Implementation would check specific criteria
            pass

        # Unlock badge
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge_id
        )
        db.add(user_badge)
        db.commit()

        return {
            "success": True,
            "badge_name": badge.name,
            "rarity": badge.rarity
        }

    def showcase_badge(self, db: Session, user_id: int, badge_id: int, showcase: bool = True) -> Dict[str, Any]:
        """Toggle badge showcase status"""
        user_badge = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id
        ).first()
        
        if not user_badge:
            return {"success": False, "message": "Badge not owned"}

        # Check showcase limit (e.g., max 5 badges)
        if showcase:
            showcased_count = db.query(UserBadge).filter(
                UserBadge.user_id == user_id,
                UserBadge.is_showcased == True
            ).count()
            
            if showcased_count >= 5:
                return {"success": False, "message": "Maximum showcase limit reached"}

        user_badge.is_showcased = showcase
        db.add(user_badge)
        db.commit()

        return {"success": True, "showcased": showcase}

    def unlock_theme(self, db: Session, user_id: int, theme_id: int) -> Dict[str, Any]:
        """Unlock a theme for a user"""
        theme = db.query(ProfileTheme).filter_by(id=theme_id).first()
        if not theme:
            return {"success": False, "message": "Theme not found"}

        # Check if already unlocked
        existing = db.query(UserTheme).filter(
            UserTheme.user_id == user_id,
            UserTheme.theme_id == theme_id
        ).first()
        if existing:
            return {"success": False, "message": "Theme already unlocked"}

        # Check requirements
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if user_profile.level < theme.unlock_level:
            return {"success": False, "message": f"Level {theme.unlock_level} required"}
        
        if user_profile.points < theme.unlock_points:
            return {"success": False, "message": f"{theme.unlock_points} points required"}

        # Deduct points if required
        if theme.unlock_points > 0:
            self.points_service.subtract_points(
                db, user_id, theme.unlock_points,
                description=f"Unlocked theme: {theme.name}",
                reference_type="theme_unlock",
                reference_id=theme_id
            )

        # Unlock theme
        user_theme = UserTheme(
            user_id=user_id,
            theme_id=theme_id
        )
        db.add(user_theme)
        db.commit()

        return {
            "success": True,
            "theme_name": theme.name,
            "points_spent": theme.unlock_points
        }

    def activate_theme(self, db: Session, user_id: int, theme_id: int) -> Dict[str, Any]:
        """Activate a theme for a user"""
        # Check if user owns the theme
        user_theme = db.query(UserTheme).filter(
            UserTheme.user_id == user_id,
            UserTheme.theme_id == theme_id
        ).first()
        
        if not user_theme:
            return {"success": False, "message": "Theme not owned"}

        # Deactivate current theme
        db.query(UserTheme).filter(
            UserTheme.user_id == user_id,
            UserTheme.is_active == True
        ).update({"is_active": False})

        # Activate new theme
        user_theme.is_active = True
        db.add(user_theme)
        db.commit()

        return {"success": True, "theme_name": user_theme.theme.name}

    def unlock_avatar_asset(self, db: Session, user_id: int, asset_id: int) -> Dict[str, Any]:
        """Unlock an avatar asset for a user"""
        asset = db.query(AvatarAsset).filter_by(id=asset_id).first()
        if not asset:
            return {"success": False, "message": "Asset not found"}

        # Check if already unlocked
        existing = db.query(UserAvatarAsset).filter(
            UserAvatarAsset.user_id == user_id,
            UserAvatarAsset.asset_id == asset_id
        ).first()
        if existing:
            return {"success": False, "message": "Asset already unlocked"}

        # Check requirements
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if user_profile.level < asset.unlock_level:
            return {"success": False, "message": f"Level {asset.unlock_level} required"}
        
        if user_profile.points < asset.unlock_points:
            return {"success": False, "message": f"{asset.unlock_points} points required"}

        # Deduct points if required
        if asset.unlock_points > 0:
            self.points_service.subtract_points(
                db, user_id, asset.unlock_points,
                description=f"Unlocked avatar asset: {asset.name}",
                reference_type="avatar_asset_unlock",
                reference_id=asset_id
            )

        # Unlock asset
        user_asset = UserAvatarAsset(
            user_id=user_id,
            asset_id=asset_id
        )
        db.add(user_asset)
        db.commit()

        return {
            "success": True,
            "asset_name": asset.name,
            "category": asset.category,
            "points_spent": asset.unlock_points
        }

    def get_avatar_builder(self, db: Session, user_id: int) -> AvatarBuilder:
        """Get avatar builder data for a user"""
        # Get all available assets grouped by category
        all_assets = db.query(AvatarAsset).filter_by(is_active=True).all()
        available_assets = {}
        for asset in all_assets:
            if asset.category not in available_assets:
                available_assets[asset.category] = []
            available_assets[asset.category].append(asset)

        # Get unlocked assets
        unlocked_asset_ids = [
            ua.asset_id for ua in db.query(UserAvatarAsset).filter_by(user_id=user_id).all()
        ]

        # Get current avatar data
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        current_avatar = profile.avatar_data or {}

        # Get recommended assets based on level and points
        recommended_assets = db.query(AvatarAsset).filter(
            AvatarAsset.unlock_level <= profile.level,
            AvatarAsset.unlock_points <= profile.points,
            ~AvatarAsset.id.in_(unlocked_asset_ids)
        ).limit(10).all()

        return AvatarBuilder(
            user_id=user_id,
            available_assets=available_assets,
            current_avatar=current_avatar,
            unlocked_assets=unlocked_asset_ids,
            recommended_assets=recommended_assets
        )

    def update_avatar(self, db: Session, user_id: int, avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's avatar configuration"""
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not profile:
            return {"success": False, "message": "Profile not found"}

        # Validate that user owns all assets in the avatar
        asset_ids = [asset_id for asset_id in avatar_data.values() if isinstance(asset_id, int)]
        owned_assets = db.query(UserAvatarAsset.asset_id).filter(
            UserAvatarAsset.user_id == user_id,
            UserAvatarAsset.asset_id.in_(asset_ids)
        ).all()
        owned_asset_ids = [asset.asset_id for asset in owned_assets]

        for asset_id in asset_ids:
            if asset_id not in owned_asset_ids:
                return {"success": False, "message": f"Asset {asset_id} not owned"}

        # Update avatar
        profile.avatar_data = avatar_data
        profile.avatar_style = "custom"
        profile.updated_at = datetime.utcnow()
        
        db.add(profile)
        db.commit()

        return {"success": True, "avatar_updated": True}

    def award_title(self, db: Session, user_id: int, title_id: int) -> Dict[str, Any]:
        """Award a title to a user"""
        title = db.query(UserTitle).filter_by(id=title_id).first()
        if not title:
            return {"success": False, "message": "Title not found"}

        # Check if already owned
        existing = db.query(UserTitleOwnership).filter(
            UserTitleOwnership.user_id == user_id,
            UserTitleOwnership.title_id == title_id
        ).first()
        if existing:
            return {"success": False, "message": "Title already owned"}

        # Award title
        title_ownership = UserTitleOwnership(
            user_id=user_id,
            title_id=title_id
        )
        db.add(title_ownership)
        db.commit()

        return {
            "success": True,
            "title_name": title.name,
            "rarity": title.rarity
        }

    def activate_title(self, db: Session, user_id: int, title_id: int) -> Dict[str, Any]:
        """Activate a title for a user"""
        # Check if user owns the title
        title_ownership = db.query(UserTitleOwnership).filter(
            UserTitleOwnership.user_id == user_id,
            UserTitleOwnership.title_id == title_id
        ).first()
        
        if not title_ownership:
            return {"success": False, "message": "Title not owned"}

        # Deactivate current title
        db.query(UserTitleOwnership).filter(
            UserTitleOwnership.user_id == user_id,
            UserTitleOwnership.is_active == True
        ).update({"is_active": False})

        # Activate new title
        title_ownership.is_active = True
        db.add(title_ownership)
        
        # Update profile title field
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        profile.title = title_ownership.title.name
        db.add(profile)
        
        db.commit()

        return {"success": True, "title_name": title_ownership.title.name}

    def update_profile_showcase(self, db: Session, user_id: int, showcase_data: ProfileShowcaseCreate) -> Dict[str, Any]:
        """Update user's profile showcase"""
        # Get or create showcase
        showcase = db.query(ProfileShowcase).filter_by(user_id=user_id).first()
        if not showcase:
            showcase = ProfileShowcase(user_id=user_id)
            db.add(showcase)

        # Update showcase data
        update_data = showcase_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(showcase, field, value)

        showcase.updated_at = datetime.utcnow()
        db.commit()

        return {"success": True, "showcase_updated": True}

    def get_profile_analytics(self, db: Session, user_id: int) -> ProfileAnalytics:
        """Get profile analytics for a user"""
        # Get profile visits
        total_views = db.query(ProfileVisit).filter_by(visited_id=user_id).count()
        unique_views = db.query(func.count(func.distinct(ProfileVisit.visitor_id))).filter(
            ProfileVisit.visited_id == user_id
        ).scalar() or 0

        # Views in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_views = db.query(ProfileVisit).filter(
            ProfileVisit.visited_id == user_id,
            ProfileVisit.visited_at >= thirty_days_ago
        ).count()

        # Profile completion
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        completion_score = profile.profile_completion_percentage if profile else 0.0

        # Customization level
        customization_level = self._get_customization_level(db, user_id)

        return ProfileAnalytics(
            user_id=user_id,
            total_profile_views=total_views,
            unique_profile_views=unique_views,
            profile_views_last_30_days=recent_views,
            profile_completion_score=completion_score,
            customization_level=customization_level,
            most_viewed_sections=[],  # Would be implemented with detailed tracking
            engagement_metrics={}
        )

    def _record_profile_visit(self, db: Session, visitor_id: int, visited_id: int):
        """Record a profile visit"""
        # Check if already visited today
        today = datetime.utcnow().date()
        existing_visit = db.query(ProfileVisit).filter(
            ProfileVisit.visitor_id == visitor_id,
            ProfileVisit.visited_id == visited_id,
            func.date(ProfileVisit.visited_at) == today
        ).first()

        if not existing_visit:
            visit = ProfileVisit(
                visitor_id=visitor_id,
                visited_id=visited_id
            )
            db.add(visit)
            db.commit()

    def _calculate_profile_completion(self, profile: UserProfile) -> float:
        """Calculate profile completion percentage"""
        total_fields = 15  # Total number of profile fields to check
        completed_fields = 0

        # Check each field
        if profile.display_name:
            completed_fields += 1
        if profile.bio:
            completed_fields += 1
        if profile.location:
            completed_fields += 1
        if profile.website:
            completed_fields += 1
        if profile.profile_picture_url:
            completed_fields += 1
        if profile.banner_color_hex or profile.banner_image_url:
            completed_fields += 1
        if profile.pronouns:
            completed_fields += 1
        if profile.timezone:
            completed_fields += 1
        if profile.favorite_water_type:
            completed_fields += 1
        if profile.hydration_motto:
            completed_fields += 1
        if profile.achievements_showcase:
            completed_fields += 1
        if profile.badges_showcase:
            completed_fields += 1
        if profile.avatar_data:
            completed_fields += 1
        if profile.theme_preference != 'auto':
            completed_fields += 1
        if profile.daily_goal_ml != 2000:  # Custom goal
            completed_fields += 1

        return (completed_fields / total_fields) * 100.0

    def _get_customization_level(self, db: Session, user_id: int) -> str:
        """Determine user's customization level"""
        # Count customization elements
        themes_unlocked = db.query(UserTheme).filter_by(user_id=user_id).count()
        badges_earned = db.query(UserBadge).filter_by(user_id=user_id).count()
        assets_unlocked = db.query(UserAvatarAsset).filter_by(user_id=user_id).count()
        titles_owned = db.query(UserTitleOwnership).filter_by(user_id=user_id).count()

        total_customizations = themes_unlocked + badges_earned + assets_unlocked + titles_owned

        if total_customizations >= 50:
            return "advanced"
        elif total_customizations >= 20:
            return "intermediate"
        else:
            return "basic"

    # Admin methods for managing customization content
    def create_badge(self, db: Session, badge_data: ProfileBadgeCreate) -> ProfileBadge:
        """Create a new profile badge"""
        badge = ProfileBadge(**badge_data.model_dump())
        db.add(badge)
        db.commit()
        db.refresh(badge)
        return badge

    def create_theme(self, db: Session, theme_data: ProfileThemeCreate) -> ProfileTheme:
        """Create a new profile theme"""
        theme = ProfileTheme(**theme_data.model_dump())
        db.add(theme)
        db.commit()
        db.refresh(theme)
        return theme

    def create_avatar_asset(self, db: Session, asset_data: AvatarAssetCreate) -> AvatarAsset:
        """Create a new avatar asset"""
        asset = AvatarAsset(**asset_data.model_dump())
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    def create_title(self, db: Session, title_data: UserTitleCreate) -> UserTitle:
        """Create a new user title"""
        title = UserTitle(**title_data.model_dump())
        db.add(title)
        db.commit()
        db.refresh(title)
        return title

    async def get_profile_showcase(self, user_id: int) -> Optional[ProfileShowcase]:
        """Get user's profile showcase"""
        return await self.db.scalar(
            select(ProfileShowcase).where(ProfileShowcase.user_id == user_id)
        )

    async def update_profile_showcase(self, user_id: int, showcase_data: dict) -> ProfileShowcase:
        """Update user's profile showcase"""
        showcase = await self.get_profile_showcase(user_id)
        if not showcase:
            showcase = ProfileShowcase(user_id=user_id, **showcase_data)
            self.db.add(showcase)
        else:
            for key, value in showcase_data.items():
                setattr(showcase, key, value)
        
        await self.db.commit()
        await self.db.refresh(showcase)
        return showcase

    async def record_profile_visit(self, visitor_id: int, profile_user_id: int) -> ProfileVisit:
        """Record a profile visit"""
        # Don't record self-visits
        if visitor_id == profile_user_id:
            return None
        
        # Check if visit already recorded today
        today = datetime.utcnow().date()
        existing_visit = await self.db.scalar(
            select(ProfileVisit).where(
                and_(
                    ProfileVisit.visitor_id == visitor_id,
                    ProfileVisit.profile_user_id == profile_user_id,
                    func.date(ProfileVisit.created_at) == today
                )
            )
        )
        
        if existing_visit:
            return existing_visit
        
        visit = ProfileVisit(
            visitor_id=visitor_id,
            profile_user_id=profile_user_id
        )
        self.db.add(visit)
        await self.db.commit()
        await self.db.refresh(visit)
        return visit

    async def get_profile_visits(self, user_id: int, days: int = 30) -> List[ProfileVisit]:
        """Get recent profile visits"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(ProfileVisit)
            .where(
                and_(
                    ProfileVisit.profile_user_id == user_id,
                    ProfileVisit.created_at >= cutoff_date
                )
            )
            .order_by(ProfileVisit.created_at.desc())
        )
        return result.scalars().all()

    async def get_profile_analytics(self, user_id: int) -> dict:
        """Get comprehensive profile analytics"""
        # Profile views
        total_views = await self.db.scalar(
            select(func.count(ProfileVisit.id))
            .where(ProfileVisit.profile_user_id == user_id)
        )
        
        # Views last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_views = await self.db.scalar(
            select(func.count(ProfileVisit.id))
            .where(
                and_(
                    ProfileVisit.profile_user_id == user_id,
                    ProfileVisit.created_at >= thirty_days_ago
                )
            )
        )
        
        # Unique visitors
        unique_visitors = await self.db.scalar(
            select(func.count(func.distinct(ProfileVisit.visitor_id)))
            .where(ProfileVisit.profile_user_id == user_id)
        )
        
        # Badge count
        badge_count = await self.db.scalar(
            select(func.count(UserBadge.id))
            .where(UserBadge.user_id == user_id)
        )
        
        # Title count
        title_count = await self.db.scalar(
            select(func.count(UserTitleOwnership.id))
            .where(UserTitleOwnership.user_id == user_id)
        )
        
        # Profile completeness
        profile = await self.get_user_profile(user_id)
        completeness = 0
        if profile:
            total_fields = 10
            filled_fields = 0
            if profile.display_name: filled_fields += 1
            if profile.bio: filled_fields += 1
            if profile.avatar_style != 'default': filled_fields += 1
            if profile.theme_preference != 'default': filled_fields += 1
            if profile.location: filled_fields += 1
            if profile.website: filled_fields += 1
            if profile.social_links: filled_fields += 1
            if profile.interests: filled_fields += 1
            if profile.favorite_quotes: filled_fields += 1
            if profile.achievements_display: filled_fields += 1
            
            completeness = (filled_fields / total_fields) * 100
        
        return {
            'total_views': total_views or 0,
            'recent_views': recent_views or 0,
            'unique_visitors': unique_visitors or 0,
            'badge_count': badge_count or 0,
            'title_count': title_count or 0,
            'profile_completeness': round(completeness, 2),
            'profile_rank': await self._calculate_profile_rank(user_id)
        }

    async def _calculate_profile_rank(self, user_id: int) -> str:
        """Calculate user's profile rank based on completeness and engagement"""
        analytics = await self.get_profile_analytics(user_id)
        
        score = 0
        score += analytics['profile_completeness'] * 0.4
        score += min(analytics['total_views'] / 10, 30) * 0.3
        score += min(analytics['badge_count'] * 5, 20) * 0.2
        score += min(analytics['unique_visitors'] * 2, 10) * 0.1
        
        if score >= 80:
            return 'Legendary'
        elif score >= 60:
            return 'Elite'
        elif score >= 40:
            return 'Advanced'
        elif score >= 20:
            return 'Intermediate'
        else:
            return 'Beginner'

    # Admin methods
    async def create_badge(self, badge_data: dict) -> ProfileBadge:
        """Create a new badge (admin only)"""
        badge = ProfileBadge(**badge_data)
        self.db.add(badge)
        await self.db.commit()
        await self.db.refresh(badge)
        return badge

    async def create_theme(self, theme_data: dict) -> ProfileTheme:
        """Create a new theme (admin only)"""
        theme = ProfileTheme(**theme_data)
        self.db.add(theme)
        await self.db.commit()
        await self.db.refresh(theme)
        return theme

    async def create_avatar_asset(self, asset_data: dict) -> AvatarAsset:
        """Create a new avatar asset (admin only)"""
        asset = AvatarAsset(**asset_data)
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def create_user_title(self, title_data: dict) -> UserTitle:
        """Create a new user title (admin only)"""
        title = UserTitle(**title_data)
        self.db.add(title)
        await self.db.commit()
        await self.db.refresh(title)
        return title

    async def award_badge_to_user(self, user_id: int, badge_id: int, reason: str = None) -> UserBadge:
        """Award a badge to a user (admin only)"""
        # Check if user already has this badge
        existing = await self.db.scalar(
            select(UserBadge).where(
                and_(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge_id
                )
            )
        )
        
        if existing:
            raise ValueError("User already has this badge")
        
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge_id,
            reason=reason
        )
        self.db.add(user_badge)
        await self.db.commit()
        await self.db.refresh(user_badge)
        return user_badge

    async def award_title_to_user(self, user_id: int, title_id: int, reason: str = None) -> UserTitleOwnership:
        """Award a title to a user (admin only)"""
        # Check if user already has this title
        existing = await self.db.scalar(
            select(UserTitleOwnership).where(
                and_(
                    UserTitleOwnership.user_id == user_id,
                    UserTitleOwnership.title_id == title_id
                )
            )
        )
        
        if existing:
            raise ValueError("User already has this title")
        
        ownership = UserTitleOwnership(
            user_id=user_id,
            title_id=title_id,
            reason=reason
        )
        self.db.add(ownership)
        await self.db.commit()
        await self.db.refresh(ownership)
        return ownership

    async def get_profile_moderation_queue(self) -> List[dict]:
        """Get profiles that need moderation (admin only)"""
        # Get profiles with potentially inappropriate content
        result = await self.db.execute(
            select(UserProfile)
            .where(
                or_(
                    UserProfile.display_name.ilike('%inappropriate%'),
                    UserProfile.bio.ilike('%inappropriate%'),
                    UserProfile.is_verified == False
                )
            )
            .order_by(UserProfile.updated_at.desc())
        )
        
        profiles = result.scalars().all()
        return [
            {
                'user_id': profile.user_id,
                'display_name': profile.display_name,
                'bio': profile.bio,
                'updated_at': profile.updated_at,
                'is_verified': profile.is_verified
            }
            for profile in profiles
        ]

    async def moderate_profile(self, user_id: int, action: str, reason: str = None) -> bool:
        """Moderate a user profile (admin only)"""
        profile = await self.get_user_profile(user_id)
        if not profile:
            return False
        
        if action == 'approve':
            profile.is_verified = True
            profile.moderation_notes = f"Approved: {reason}" if reason else "Approved"
        elif action == 'reject':
            profile.is_verified = False
            profile.moderation_notes = f"Rejected: {reason}" if reason else "Rejected"
            # Reset inappropriate content
            profile.display_name = f"User{user_id}"
            profile.bio = ""
        elif action == 'flag':
            profile.moderation_notes = f"Flagged: {reason}" if reason else "Flagged for review"
        
        await self.db.commit()
        return True

profile_service = ProfileService() 