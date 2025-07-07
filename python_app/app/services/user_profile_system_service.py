from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json
import uuid
import logging
from enum import Enum
import hashlib
import os
from PIL import Image
import requests
from io import BytesIO
import boto3
from dataclasses import dataclass

from app.models.user_profile_system import (
    UserProfile, UserPreferences, UserPrivacySettings, UserCustomizations,
    UserAchievement, UserSocialConnection, UserHealthProfile, UserActivityProfile,
    ProfileVisibility, ThemePreference, LanguageCode, UnitSystem, ActivityLevel,
    HealthGoalType, NotificationFrequency, DataSharingLevel, PrivacyLevel
)
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ProfileAnalytics:
    completion_percentage: float
    missing_fields: List[str]
    recommendations: List[str]
    verification_status: str
    engagement_score: float

class UserProfileSystemService:
    def __init__(self, db: Session):
        self.db = db
        self.profile_cache = {}
        self.preferences_cache = {}
        self.s3_client = self._initialize_s3_client()
        
    def _initialize_s3_client(self):
        """Initialize S3 client for avatar and media uploads"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {str(e)}")
            return None

    # Profile Management
    def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> UserProfile:
        """Create a new user profile"""
        try:
            # Check if profile already exists
            existing_profile = self.get_user_profile(user_id)
            if existing_profile:
                raise ValueError("Profile already exists for this user")
            
            profile = UserProfile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                display_name=profile_data.get("display_name"),
                bio=profile_data.get("bio"),
                location=profile_data.get("location"),
                website=profile_data.get("website"),
                birth_date=profile_data.get("birth_date"),
                gender=profile_data.get("gender"),
                height=profile_data.get("height"),
                weight=profile_data.get("weight"),
                activity_level=profile_data.get("activity_level", ActivityLevel.MODERATELY_ACTIVE),
                timezone=profile_data.get("timezone"),
                wake_up_time=profile_data.get("wake_up_time"),
                sleep_time=profile_data.get("sleep_time"),
                profile_visibility=profile_data.get("profile_visibility", ProfileVisibility.FRIENDS),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            
            # Create default preferences
            self._create_default_preferences(profile.id)
            
            # Create default privacy settings
            self._create_default_privacy_settings(profile.id)
            
            # Create default customizations
            self._create_default_customizations(profile.id)
            
            # Calculate initial completion percentage
            self._update_profile_completion(profile)
            
            # Clear cache
            self.profile_cache.pop(user_id, None)
            
            logger.info(f"Created user profile for user: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            self.db.rollback()
            raise

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID"""
        if user_id in self.profile_cache:
            return self.profile_cache[user_id]
            
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if profile:
            self.profile_cache[user_id] = profile
            
        return profile

    def get_profile_by_id(self, profile_id: str) -> Optional[UserProfile]:
        """Get profile by profile ID"""
        return self.db.query(UserProfile).filter(
            UserProfile.id == profile_id
        ).first()

    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Optional[UserProfile]:
        """Update user profile"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return None
                
            # Update profile fields
            for key, value in update_data.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)
                    
            profile.updated_at = datetime.utcnow()
            profile.last_profile_update = datetime.utcnow()
            
            # Update completion percentage
            self._update_profile_completion(profile)
            
            self.db.commit()
            self.db.refresh(profile)
            
            # Clear cache
            self.profile_cache.pop(user_id, None)
            
            logger.info(f"Updated user profile: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            self.db.rollback()
            raise

    def delete_user_profile(self, user_id: str) -> bool:
        """Delete user profile and all associated data"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
                
            # Delete associated data
            self.db.query(UserPreferences).filter(
                UserPreferences.profile_id == profile.id
            ).delete()
            
            self.db.query(UserPrivacySettings).filter(
                UserPrivacySettings.profile_id == profile.id
            ).delete()
            
            self.db.query(UserCustomizations).filter(
                UserCustomizations.profile_id == profile.id
            ).delete()
            
            self.db.query(UserAchievement).filter(
                UserAchievement.profile_id == profile.id
            ).delete()
            
            self.db.query(UserSocialConnection).filter(
                UserSocialConnection.profile_id == profile.id
            ).delete()
            
            self.db.query(UserHealthProfile).filter(
                UserHealthProfile.profile_id == profile.id
            ).delete()
            
            self.db.query(UserActivityProfile).filter(
                UserActivityProfile.profile_id == profile.id
            ).delete()
            
            # Delete profile
            self.db.delete(profile)
            self.db.commit()
            
            # Clear cache
            self.profile_cache.pop(user_id, None)
            
            logger.info(f"Deleted user profile: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user profile: {str(e)}")
            self.db.rollback()
            raise

    def _create_default_preferences(self, profile_id: str) -> UserPreferences:
        """Create default user preferences"""
        try:
            preferences = UserPreferences(
                id=str(uuid.uuid4()),
                profile_id=profile_id,
                language=LanguageCode.EN,
                unit_system=UnitSystem.METRIC,
                theme=ThemePreference.AUTO,
                notification_frequency=NotificationFrequency.NORMAL,
                default_container_size=500,
                reminder_interval=60,
                smart_reminders=True,
                weather_adjustments=True,
                activity_adjustments=True,
                allow_friend_requests=True,
                show_online_status=True,
                data_sharing_level=DataSharingLevel.AGGREGATED,
                analytics_tracking=True,
                personalized_insights=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(preferences)
            self.db.commit()
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error creating default preferences: {str(e)}")
            self.db.rollback()
            raise

    def _create_default_privacy_settings(self, profile_id: str) -> UserPrivacySettings:
        """Create default privacy settings"""
        try:
            privacy_settings = UserPrivacySettings(
                id=str(uuid.uuid4()),
                profile_id=profile_id,
                privacy_level=PrivacyLevel.BALANCED,
                allow_analytics=True,
                allow_crash_reporting=True,
                profile_searchable=True,
                show_in_leaderboards=True,
                share_anonymous_data=True,
                allow_marketing_emails=False,
                allow_product_updates=True,
                allow_location_tracking=False,
                two_factor_enabled=False,
                login_notifications=True,
                data_retention_period=365,
                auto_delete_old_data=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(privacy_settings)
            self.db.commit()
            
            return privacy_settings
            
        except Exception as e:
            logger.error(f"Error creating default privacy settings: {str(e)}")
            self.db.rollback()
            raise

    def _create_default_customizations(self, profile_id: str) -> UserCustomizations:
        """Create default customizations"""
        try:
            customizations = UserCustomizations(
                id=str(uuid.uuid4()),
                profile_id=profile_id,
                primary_color="#2196F3",
                secondary_color="#FFC107",
                accent_color="#FF5722",
                dashboard_layout={
                    "widgets": [
                        {"type": "hydration_progress", "position": 1, "size": "large"},
                        {"type": "daily_goal", "position": 2, "size": "medium"},
                        {"type": "streak_counter", "position": 3, "size": "small"},
                        {"type": "recent_activity", "position": 4, "size": "medium"}
                    ]
                },
                widget_preferences={
                    "hydration_progress": {"enabled": True, "style": "circular"},
                    "daily_goal": {"enabled": True, "show_percentage": True},
                    "streak_counter": {"enabled": True, "show_best_streak": True},
                    "weather_widget": {"enabled": True, "show_recommendations": True}
                },
                custom_hydration_goals={
                    "morning_goal": 500,
                    "afternoon_goal": 1000,
                    "evening_goal": 500
                },
                favorite_drink_types=["water", "herbal_tea", "fruit_water"],
                quick_actions=["log_water", "set_reminder", "view_progress", "start_challenge"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(customizations)
            self.db.commit()
            
            return customizations
            
        except Exception as e:
            logger.error(f"Error creating default customizations: {str(e)}")
            self.db.rollback()
            raise

    def _update_profile_completion(self, profile: UserProfile) -> None:
        """Update profile completion percentage"""
        try:
            required_fields = [
                'display_name', 'bio', 'location', 'birth_date', 'gender',
                'height', 'weight', 'activity_level', 'timezone',
                'wake_up_time', 'sleep_time', 'avatar_url'
            ]
            
            completed_fields = 0
            for field in required_fields:
                value = getattr(profile, field)
                if value is not None and value != "":
                    completed_fields += 1
            
            completion_percentage = (completed_fields / len(required_fields)) * 100
            profile.profile_completion_percentage = completion_percentage
            
        except Exception as e:
            logger.error(f"Error updating profile completion: {str(e)}")

    # Preferences Management
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences"""
        cache_key = f"preferences_{user_id}"
        if cache_key in self.preferences_cache:
            return self.preferences_cache[cache_key]
            
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
            
        preferences = self.db.query(UserPreferences).filter(
            UserPreferences.profile_id == profile.id
        ).first()
        
        if preferences:
            self.preferences_cache[cache_key] = preferences
            
        return preferences

    def update_user_preferences(self, user_id: str, update_data: Dict[str, Any]) -> Optional[UserPreferences]:
        """Update user preferences"""
        try:
            preferences = self.get_user_preferences(user_id)
            if not preferences:
                return None
                
            # Update preferences fields
            for key, value in update_data.items():
                if hasattr(preferences, key) and value is not None:
                    setattr(preferences, key, value)
                    
            preferences.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(preferences)
            
            # Clear cache
            cache_key = f"preferences_{user_id}"
            self.preferences_cache.pop(cache_key, None)
            
            logger.info(f"Updated user preferences: {user_id}")
            return preferences
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            self.db.rollback()
            raise

    # Privacy Settings Management
    def get_user_privacy_settings(self, user_id: str) -> Optional[UserPrivacySettings]:
        """Get user privacy settings"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
            
        return self.db.query(UserPrivacySettings).filter(
            UserPrivacySettings.profile_id == profile.id
        ).first()

    def update_user_privacy_settings(self, user_id: str, update_data: Dict[str, Any]) -> Optional[UserPrivacySettings]:
        """Update user privacy settings"""
        try:
            privacy_settings = self.get_user_privacy_settings(user_id)
            if not privacy_settings:
                return None
                
            # Update privacy settings fields
            for key, value in update_data.items():
                if hasattr(privacy_settings, key) and value is not None:
                    setattr(privacy_settings, key, value)
                    
            privacy_settings.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(privacy_settings)
            
            logger.info(f"Updated user privacy settings: {user_id}")
            return privacy_settings
            
        except Exception as e:
            logger.error(f"Error updating user privacy settings: {str(e)}")
            self.db.rollback()
            raise

    # Customizations Management
    def get_user_customizations(self, user_id: str) -> Optional[UserCustomizations]:
        """Get user customizations"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
            
        return self.db.query(UserCustomizations).filter(
            UserCustomizations.profile_id == profile.id
        ).first()

    def update_user_customizations(self, user_id: str, update_data: Dict[str, Any]) -> Optional[UserCustomizations]:
        """Update user customizations"""
        try:
            customizations = self.get_user_customizations(user_id)
            if not customizations:
                return None
                
            # Update customizations fields
            for key, value in update_data.items():
                if hasattr(customizations, key) and value is not None:
                    setattr(customizations, key, value)
                    
            customizations.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(customizations)
            
            logger.info(f"Updated user customizations: {user_id}")
            return customizations
            
        except Exception as e:
            logger.error(f"Error updating user customizations: {str(e)}")
            self.db.rollback()
            raise

    # Avatar and Media Management
    def upload_avatar(self, user_id: str, image_data: bytes, filename: str) -> Optional[str]:
        """Upload user avatar"""
        try:
            if not self.s3_client:
                logger.warning("S3 client not available, using local storage")
                return self._upload_avatar_local(user_id, image_data, filename)
            
            # Process image
            processed_image = self._process_avatar_image(image_data)
            
            # Generate S3 key
            file_extension = filename.split('.')[-1].lower()
            s3_key = f"avatars/{user_id}/{uuid.uuid4()}.{file_extension}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=os.getenv('AWS_S3_BUCKET'),
                Key=s3_key,
                Body=processed_image,
                ContentType=f'image/{file_extension}',
                ACL='public-read'
            )
            
            # Generate URL
            avatar_url = f"https://{os.getenv('AWS_S3_BUCKET')}.s3.amazonaws.com/{s3_key}"
            
            # Update profile
            profile = self.get_user_profile(user_id)
            if profile:
                profile.avatar_url = avatar_url
                profile.updated_at = datetime.utcnow()
                self.db.commit()
                
                # Clear cache
                self.profile_cache.pop(user_id, None)
            
            logger.info(f"Uploaded avatar for user: {user_id}")
            return avatar_url
            
        except Exception as e:
            logger.error(f"Error uploading avatar: {str(e)}")
            return None

    def _upload_avatar_local(self, user_id: str, image_data: bytes, filename: str) -> Optional[str]:
        """Upload avatar to local storage"""
        try:
            # Create directory if it doesn't exist
            avatar_dir = os.path.join("static", "avatars", user_id)
            os.makedirs(avatar_dir, exist_ok=True)
            
            # Process image
            processed_image = self._process_avatar_image(image_data)
            
            # Save file
            file_extension = filename.split('.')[-1].lower()
            avatar_filename = f"{uuid.uuid4()}.{file_extension}"
            avatar_path = os.path.join(avatar_dir, avatar_filename)
            
            with open(avatar_path, 'wb') as f:
                f.write(processed_image)
            
            # Generate URL
            avatar_url = f"/static/avatars/{user_id}/{avatar_filename}"
            
            # Update profile
            profile = self.get_user_profile(user_id)
            if profile:
                profile.avatar_url = avatar_url
                profile.updated_at = datetime.utcnow()
                self.db.commit()
                
                # Clear cache
                self.profile_cache.pop(user_id, None)
            
            return avatar_url
            
        except Exception as e:
            logger.error(f"Error uploading avatar locally: {str(e)}")
            return None

    def _process_avatar_image(self, image_data: bytes) -> bytes:
        """Process avatar image (resize, optimize)"""
        try:
            # Open image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to standard avatar size
            avatar_size = (200, 200)
            image = image.resize(avatar_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error processing avatar image: {str(e)}")
            return image_data

    # Profile Analytics
    def get_profile_analytics(self, user_id: str) -> ProfileAnalytics:
        """Get profile analytics and recommendations"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return ProfileAnalytics(
                    completion_percentage=0.0,
                    missing_fields=[],
                    recommendations=[],
                    verification_status="unverified",
                    engagement_score=0.0
                )
            
            # Calculate completion percentage
            completion_percentage = profile.profile_completion_percentage or 0.0
            
            # Identify missing fields
            missing_fields = []
            required_fields = {
                'display_name': 'Display Name',
                'bio': 'Bio',
                'location': 'Location',
                'birth_date': 'Birth Date',
                'gender': 'Gender',
                'height': 'Height',
                'weight': 'Weight',
                'avatar_url': 'Profile Picture'
            }
            
            for field, display_name in required_fields.items():
                value = getattr(profile, field)
                if value is None or value == "":
                    missing_fields.append(display_name)
            
            # Generate recommendations
            recommendations = self._generate_profile_recommendations(profile, missing_fields)
            
            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(profile)
            
            # Determine verification status
            verification_status = "verified" if profile.is_verified else "unverified"
            
            return ProfileAnalytics(
                completion_percentage=completion_percentage,
                missing_fields=missing_fields,
                recommendations=recommendations,
                verification_status=verification_status,
                engagement_score=engagement_score
            )
            
        except Exception as e:
            logger.error(f"Error getting profile analytics: {str(e)}")
            return ProfileAnalytics(
                completion_percentage=0.0,
                missing_fields=[],
                recommendations=[],
                verification_status="error",
                engagement_score=0.0
            )

    def _generate_profile_recommendations(self, profile: UserProfile, missing_fields: List[str]) -> List[str]:
        """Generate personalized profile recommendations"""
        recommendations = []
        
        # Completion recommendations
        if profile.profile_completion_percentage < 50:
            recommendations.append("Complete your profile to unlock personalized features")
        
        if 'Profile Picture' in missing_fields:
            recommendations.append("Add a profile picture to make your profile more engaging")
        
        if 'Bio' in missing_fields:
            recommendations.append("Write a bio to tell others about your hydration journey")
        
        if 'Height' in missing_fields or 'Weight' in missing_fields:
            recommendations.append("Add your physical stats for more accurate hydration recommendations")
        
        # Privacy recommendations
        if not profile.is_verified:
            recommendations.append("Verify your account to increase trust and unlock features")
        
        # Engagement recommendations
        if profile.profile_visibility == ProfileVisibility.PRIVATE:
            recommendations.append("Consider making your profile visible to friends to increase engagement")
        
        # Activity recommendations
        if not profile.show_activity:
            recommendations.append("Enable activity sharing to motivate friends and get motivated")
        
        return recommendations

    def _calculate_engagement_score(self, profile: UserProfile) -> float:
        """Calculate user engagement score"""
        try:
            score = 0.0
            
            # Profile completion (30%)
            completion_score = (profile.profile_completion_percentage or 0) * 0.3
            score += completion_score
            
            # Profile visibility (20%)
            visibility_scores = {
                ProfileVisibility.PUBLIC: 20,
                ProfileVisibility.FRIENDS: 15,
                ProfileVisibility.CUSTOM: 10,
                ProfileVisibility.PRIVATE: 5
            }
            score += visibility_scores.get(profile.profile_visibility, 0)
            
            # Activity sharing (20%)
            if profile.show_activity:
                score += 20
            
            # Verification status (15%)
            if profile.is_verified:
                score += 15
            
            # Recent activity (15%)
            if profile.last_profile_update:
                days_since_update = (datetime.utcnow() - profile.last_profile_update).days
                if days_since_update <= 7:
                    score += 15
                elif days_since_update <= 30:
                    score += 10
                elif days_since_update <= 90:
                    score += 5
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {str(e)}")
            return 0.0

    # Search and Discovery
    def search_profiles(self, query: str, filters: Dict[str, Any] = None, 
                       limit: int = 20) -> List[UserProfile]:
        """Search user profiles"""
        try:
            # Base query for searchable profiles
            base_query = self.db.query(UserProfile).filter(
                and_(
                    UserProfile.profile_visibility.in_([
                        ProfileVisibility.PUBLIC, 
                        ProfileVisibility.FRIENDS
                    ]),
                    # Add privacy filter for searchable profiles
                    UserProfile.id.in_(
                        self.db.query(UserPrivacySettings.profile_id).filter(
                            UserPrivacySettings.profile_searchable == True
                        )
                    )
                )
            )
            
            # Apply search query
            if query:
                search_filter = or_(
                    UserProfile.display_name.ilike(f"%{query}%"),
                    UserProfile.bio.ilike(f"%{query}%"),
                    UserProfile.location.ilike(f"%{query}%")
                )
                base_query = base_query.filter(search_filter)
            
            # Apply filters
            if filters:
                if 'location' in filters:
                    base_query = base_query.filter(
                        UserProfile.location.ilike(f"%{filters['location']}%")
                    )
                
                if 'activity_level' in filters:
                    base_query = base_query.filter(
                        UserProfile.activity_level == filters['activity_level']
                    )
                
                if 'gender' in filters:
                    base_query = base_query.filter(
                        UserProfile.gender == filters['gender']
                    )
                
                if 'verified_only' in filters and filters['verified_only']:
                    base_query = base_query.filter(
                        UserProfile.is_verified == True
                    )
            
            # Order by relevance and completion
            results = base_query.order_by(
                desc(UserProfile.profile_completion_percentage),
                desc(UserProfile.is_verified),
                desc(UserProfile.updated_at)
            ).limit(limit).all()
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching profiles: {str(e)}")
            return []

    def get_profile_suggestions(self, user_id: str, limit: int = 10) -> List[UserProfile]:
        """Get profile suggestions for user"""
        try:
            user_profile = self.get_user_profile(user_id)
            if not user_profile:
                return []
            
            # Get suggestions based on similar interests, location, activity level
            suggestions_query = self.db.query(UserProfile).filter(
                and_(
                    UserProfile.user_id != user_id,
                    UserProfile.profile_visibility.in_([
                        ProfileVisibility.PUBLIC,
                        ProfileVisibility.FRIENDS
                    ])
                )
            )
            
            # Prioritize by similar attributes
            if user_profile.location:
                suggestions_query = suggestions_query.filter(
                    UserProfile.location.ilike(f"%{user_profile.location}%")
                )
            
            if user_profile.activity_level:
                suggestions_query = suggestions_query.filter(
                    UserProfile.activity_level == user_profile.activity_level
                )
            
            suggestions = suggestions_query.order_by(
                desc(UserProfile.profile_completion_percentage),
                desc(UserProfile.is_verified),
                desc(UserProfile.updated_at)
            ).limit(limit).all()
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting profile suggestions: {str(e)}")
            return []

    # Profile Verification
    def verify_profile(self, user_id: str, verification_type: str = "email") -> bool:
        """Verify user profile"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            profile.is_verified = True
            profile.verification_date = datetime.utcnow()
            profile.verification_type = verification_type
            profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Clear cache
            self.profile_cache.pop(user_id, None)
            
            logger.info(f"Verified profile for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying profile: {str(e)}")
            self.db.rollback()
            return False

    def unverify_profile(self, user_id: str) -> bool:
        """Remove verification from profile"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            profile.is_verified = False
            profile.verification_date = None
            profile.verification_type = None
            profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Clear cache
            self.profile_cache.pop(user_id, None)
            
            logger.info(f"Unverified profile for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unverifying profile: {str(e)}")
            self.db.rollback()
            return False

    # Utility Methods
    def get_profile_statistics(self) -> Dict[str, Any]:
        """Get overall profile statistics"""
        try:
            total_profiles = self.db.query(UserProfile).count()
            verified_profiles = self.db.query(UserProfile).filter(
                UserProfile.is_verified == True
            ).count()
            
            # Average completion percentage
            avg_completion = self.db.query(
                func.avg(UserProfile.profile_completion_percentage)
            ).scalar() or 0.0
            
            # Profile visibility distribution
            visibility_stats = self.db.query(
                UserProfile.profile_visibility,
                func.count(UserProfile.id).label('count')
            ).group_by(UserProfile.profile_visibility).all()
            
            return {
                "total_profiles": total_profiles,
                "verified_profiles": verified_profiles,
                "verification_rate": (verified_profiles / total_profiles * 100) if total_profiles > 0 else 0,
                "average_completion": round(avg_completion, 2),
                "visibility_distribution": {
                    str(visibility): count for visibility, count in visibility_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting profile statistics: {str(e)}")
            return {}

    def cleanup_inactive_profiles(self, days_inactive: int = 365) -> int:
        """Clean up inactive profiles"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
            
            # Find inactive profiles
            inactive_profiles = self.db.query(UserProfile).filter(
                and_(
                    UserProfile.last_profile_update < cutoff_date,
                    UserProfile.is_verified == False
                )
            ).all()
            
            deleted_count = 0
            for profile in inactive_profiles:
                try:
                    self.delete_user_profile(profile.user_id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting inactive profile {profile.id}: {str(e)}")
            
            logger.info(f"Cleaned up {deleted_count} inactive profiles")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive profiles: {str(e)}")
            return 0 