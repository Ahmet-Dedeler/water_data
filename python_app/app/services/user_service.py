from typing import Optional, List, Any
from sqlalchemy.orm import Session
import logging
import os
from pathlib import Path
from datetime import date, timedelta, datetime

from app.db import models as db_models
from app.models.user import (
    User, UserCreate, UserUpdate, UserProfile, UserProfileUpdate, UserRole, UserPreferences
)
from app.core.auth import AuthManager
from app.core.security import get_password_hash, verify_password
from app.services.base_service import BaseService
from app.schemas.user import UserPreferencesUpdate
from app.db.models import User, UserProfile, UserPreferences
from app.models.user import DailyStreak, DailyStreakCreate, DailyStreakUpdate, StreakSummary

logger = logging.getLogger(__name__)

AVATAR_DIR = Path("static/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

class UserService(BaseService[User, UserCreate, UserProfileUpdate]):
    """Service for user management operations using a database."""
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user and a default profile."""
        if db.query(User).filter(User.email == obj_in.email).first():
            raise ValueError("Email already registered")
        if db.query(User).filter(User.username == obj_in.username).first():
            raise ValueError("Username already taken")

        hashed_password = get_password_hash(obj_in.password)
        
        db_user = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
            is_active=True,  # Users are active by default
            is_verified=False, # Email verification is required
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create a default profile
        self._create_default_profile(db, db_user.id)
        
        # Create default preferences
        self.get_or_create_preferences(db, user_id=db_user.id)
        
        return db_user

    def _create_default_profile(self, db: Session, user_id: int):
        """Create a default profile for a new user."""
        db_profile = db_models.UserProfile(user_id=user_id)
        db.add(db_profile)
        db.commit()

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_by_email(db, email=email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        # Optionally update last_login here if that field is added to the db model
        return user

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    def update_profile(self, db: Session, *, db_obj: User, obj_in: UserProfileUpdate) -> User:
        """Update user profile."""
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """Change user password."""
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def deactivate_user(self, db: Session, user_id: int) -> bool:
        """Deactivate a user."""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
            
        user.is_active = False
        db.commit()
        return True

    def activate_user(self, db: Session, user_id: int) -> bool:
        """Activate a user."""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_active = True
        db.commit()
        return True
        
    def promote_to_admin(self, db: Session, user_id: int) -> Optional[User]:
        """Promote a user to the admin role."""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.role = UserRole.ADMIN
        db.commit()
        db.refresh(user)
        return user

    def get_user_profile(self, db: Session, user_id: int) -> Optional[db_models.UserProfile]:
        """Get user profile by user ID."""
        return db.query(db_models.UserProfile).filter(db_models.UserProfile.user_id == user_id).first()

    def set_avatar_filename(self, db: Session, *, user: User, filename: str) -> User:
        user.avatar_url = filename
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_avatar_path(self, user_id: int) -> Optional[Path]:
        # This is a simplified example; in a real app, you'd query the user model
        # to get the avatar filename. For now, we find the first match.
        for ext in ["png", "jpg", "jpeg", "gif"]:
            avatar_path = AVATAR_DIR / f"{user_id}.{ext}"
            if avatar_path.exists():
                return avatar_path
        return None

    def delete_avatar(self, user_id: int) -> bool:
        avatar_path = self.get_avatar_path(user_id)
        if avatar_path:
            os.remove(avatar_path)
            # You would also clear the avatar_url in the user model here
            return True
        return False

    def get_or_create_preferences(self, db: Session, *, user_id: int) -> UserPreferences:
        preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        if not preferences:
            preferences = UserPreferences(user_id=user_id)
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        return preferences

    def update_preferences(self, db: Session, *, user_id: int, obj_in: UserPreferencesUpdate) -> UserPreferences:
        preferences = self.get_or_create_preferences(db, user_id=user_id)
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        return preferences

    def request_account_deletion(self, db: Session, user_id: int, password: str) -> bool:
        """
        Deletes a user's account and all associated data after verifying their password.
        The deletion of related data is handled by the 'ondelete=CASCADE' setting
        in the database models.
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False

        # Verify password before deletion
        if not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect password")

        db.delete(user)
        db.commit()
        
        logger.info(f"Successfully deleted account and all associated data for user_id: {user_id}")
        return True

    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return db.query(User).offset(skip).limit(limit).all()

    def get_user_count(self, db: Session) -> int:
        """Get the total number of users."""
        return db.query(User).count()

    def search_users(self, db: Session, query: str, limit: int = 20) -> List[User]:
        """Search for users by username or email."""
        search_query = f"%{query}%"
        return db.query(User).filter(
            (User.username.ilike(search_query)) |
            (User.email.ilike(search_query))
        ).limit(limit).all()

    def update_hydration_streak(self, db: Session, user_id: int):
        """
        Updates the user's hydration streak based on their latest water log.
        """
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            return

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Ensure last_log_date is a date object if it exists
        last_log_date = user_profile.last_log_date.date() if user_profile.last_log_date else None

        if last_log_date == today:
            # Already logged today, streak doesn't change
            return
        elif last_log_date == yesterday:
            # Logged yesterday, increment streak
            user_profile.current_streak += 1
        else:
            # Missed a day or first log, reset to 1
            user_profile.current_streak = 1
        
        # Update longest streak if the current one is greater
        if user_profile.current_streak > user_profile.longest_streak:
            user_profile.longest_streak = user_profile.current_streak

        # Update the last log date to today
        user_profile.last_log_date = datetime.utcnow()

        db.add(user_profile)
        db.commit()

    def create_or_update_daily_streak(self, db: Session, user_id: int, date: datetime, total_volume_ml: float) -> db_models.DailyStreak:
        """
        Create or update a daily streak record for a user.
        """
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            return None

        # Get or create daily streak record
        daily_streak = db.query(db_models.DailyStreak).filter(
            db_models.DailyStreak.user_id == user_id,
            db_models.DailyStreak.date == date.date()
        ).first()

        goal_volume = user_profile.daily_goal_ml
        percentage_completed = min((total_volume_ml / goal_volume) * 100, 100.0) if goal_volume > 0 else 0.0
        goal_met = percentage_completed >= 100.0

        if daily_streak:
            # Update existing record
            daily_streak.total_volume_ml = total_volume_ml
            daily_streak.percentage_completed = percentage_completed
            daily_streak.goal_met = goal_met
        else:
            # Create new record
            daily_streak = db_models.DailyStreak(
                user_id=user_id,
                date=date.date(),
                goal_met=goal_met,
                total_volume_ml=total_volume_ml,
                goal_volume_ml=goal_volume,
                percentage_completed=percentage_completed,
                streak_day=0  # Will be calculated in update_streak_days
            )
            db.add(daily_streak)

        db.commit()
        db.refresh(daily_streak)
        
        # Update streak days for all records
        self.update_streak_days(db, user_id)
        
        return daily_streak

    def update_streak_days(self, db: Session, user_id: int):
        """
        Update the streak_day field for all daily streak records for a user.
        """
        streaks = db.query(db_models.DailyStreak).filter(
            db_models.DailyStreak.user_id == user_id
        ).order_by(db_models.DailyStreak.date).all()

        current_streak = 0
        for streak in streaks:
            if streak.goal_met:
                current_streak += 1
                streak.streak_day = current_streak
            else:
                current_streak = 0
                streak.streak_day = 0

        db.commit()

    def get_streak_summary(self, db: Session, user_id: int) -> StreakSummary:
        """
        Get a comprehensive streak summary for a user.
        """
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            return None

        # Get all daily streaks
        daily_streaks = db.query(db_models.DailyStreak).filter(
            db_models.DailyStreak.user_id == user_id
        ).order_by(db_models.DailyStreak.date.desc()).all()

        # Calculate current streak
        current_streak = 0
        today = date.today()
        check_date = today
        
        for streak in daily_streaks:
            if streak.date == check_date and streak.goal_met:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Calculate total streak days
        total_streak_days = len([s for s in daily_streaks if s.goal_met])

        # Get last streak date
        last_streak_date = None
        for streak in daily_streaks:
            if streak.goal_met:
                last_streak_date = streak.date
                break

        # Calculate current streak percentage (last 7 days)
        recent_streaks = [s for s in daily_streaks if s.date >= today - timedelta(days=7)]
        current_streak_percentage = (len([s for s in recent_streaks if s.goal_met]) / 7) * 100 if recent_streaks else 0.0

        return StreakSummary(
            current_streak=current_streak,
            longest_streak=user_profile.longest_streak,
            total_streak_days=total_streak_days,
            last_streak_date=last_streak_date,
            current_streak_percentage=current_streak_percentage,
            streak_history=daily_streaks[:30]  # Last 30 days
        )

    def get_daily_streaks(self, db: Session, user_id: int, limit: int = 30) -> List[db_models.DailyStreak]:
        """
        Get daily streak records for a user.
        """
        return db.query(db_models.DailyStreak).filter(
            db_models.DailyStreak.user_id == user_id
        ).order_by(db_models.DailyStreak.date.desc()).limit(limit).all()

    def get_streak_stats(self, db: Session, user_id: int) -> dict:
        """
        Get detailed streak statistics for a user.
        """
        streaks = db.query(db_models.DailyStreak).filter(
            db_models.DailyStreak.user_id == user_id
        ).order_by(db_models.DailyStreak.date).all()

        if not streaks:
            return {
                "total_days": 0,
                "successful_days": 0,
                "success_rate": 0.0,
                "average_completion": 0.0,
                "longest_streak": 0,
                "current_streak": 0
            }

        total_days = len(streaks)
        successful_days = len([s for s in streaks if s.goal_met])
        success_rate = (successful_days / total_days) * 100 if total_days > 0 else 0.0
        average_completion = sum(s.percentage_completed for s in streaks) / total_days if total_days > 0 else 0.0

        # Calculate longest streak
        longest_streak = 0
        current_streak_count = 0
        for streak in streaks:
            if streak.goal_met:
                current_streak_count += 1
                longest_streak = max(longest_streak, current_streak_count)
            else:
                current_streak_count = 0

        # Calculate current streak
        current_streak = 0
        for streak in reversed(streaks):
            if streak.goal_met:
                current_streak += 1
            else:
                break

        return {
            "total_days": total_days,
            "successful_days": successful_days,
            "success_rate": success_rate,
            "average_completion": average_completion,
            "longest_streak": longest_streak,
            "current_streak": current_streak
        }

# Global service instance
user_service = UserService(User) 