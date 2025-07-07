from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    ForeignKey, Table, Float, Text, JSON, DDL, event, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.database import Base
from datetime import datetime

# Association table for UserProfile and HealthGoal
user_profile_health_goal_association = Table(
    'user_profile_health_goal', Base.metadata,
    Column('user_profile_id', Integer, ForeignKey('user_profiles.id')),
    Column('health_goal_id', Integer, ForeignKey('health_goals.id'))
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="user")
    water_logs: Mapped[list["WaterLog"]] = relationship("WaterLog", back_populates="user")
    achievements: Mapped[list["UserAchievement"]] = relationship("UserAchievement", back_populates="user")
    activities: Mapped[list["Activity"]] = relationship("Activity", back_populates="user")
    reminders: Mapped[list["Reminder"]] = relationship("Reminder", back_populates="user")
    
    # Following/follower relationships
    following: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_follows",
        primaryjoin="User.id==UserFollow.follower_id",
        secondaryjoin="User.id==UserFollow.following_id",
        back_populates="followers"
    )
    followers: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_follows",
        primaryjoin="User.id==UserFollow.following_id",
        secondaryjoin="User.id==UserFollow.follower_id",
        back_populates="following"
    )

    # Social Features Models

    sent_friend_requests: Mapped[list["Friendship"]] = relationship("Friendship", foreign_keys="Friendship.requester_id", back_populates="requester")
    received_friend_requests: Mapped[list["Friendship"]] = relationship("Friendship", foreign_keys="Friendship.addressee_id", back_populates="addressee")
    sent_messages: Mapped[list["Message"]] = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages: Mapped[list["Message"]] = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    activity_feeds: Mapped[list["ActivityFeed"]] = relationship("ActivityFeed", back_populates="user", cascade="all, delete-orphan")
    activity_likes: Mapped[list["ActivityLike"]] = relationship("ActivityLike", back_populates="user", cascade="all, delete-orphan")
    activity_comments: Mapped[list["ActivityComment"]] = relationship("ActivityComment", back_populates="user", cascade="all, delete-orphan")
    activity_comment_likes: Mapped[list["ActivityCommentLike"]] = relationship("ActivityCommentLike", back_populates="user", cascade="all, delete-orphan")
    created_groups: Mapped[list["SocialGroup"]] = relationship("SocialGroup", back_populates="creator", cascade="all, delete-orphan")
    group_memberships: Mapped[list["SocialGroupMember"]] = relationship("SocialGroupMember", back_populates="user", cascade="all, delete-orphan")
    group_posts: Mapped[list["SocialGroupPost"]] = relationship("SocialGroupPost", back_populates="user", cascade="all, delete-orphan")
    group_post_likes: Mapped[list["SocialGroupPostLike"]] = relationship("SocialGroupPostLike", back_populates="user", cascade="all, delete-orphan")
    group_post_comments: Mapped[list["SocialGroupPostComment"]] = relationship("SocialGroupPostComment", back_populates="user", cascade="all, delete-orphan")
    social_achievements: Mapped[list["SocialAchievement"]] = relationship("SocialAchievement", back_populates="user", cascade="all, delete-orphan")
    social_notifications: Mapped[list["SocialNotification"]] = relationship("SocialNotification", foreign_keys="SocialNotification.user_id", back_populates="user", cascade="all, delete-orphan")
    
    # Water Quality relationships
    water_sources: Mapped[list["WaterSource"]] = relationship("WaterSource", back_populates="user", cascade="all, delete-orphan")
    water_quality_tests: Mapped[list["WaterQualityTest"]] = relationship("WaterQualityTest", back_populates="user", cascade="all, delete-orphan")
    contamination_reports: Mapped[list["ContaminationReport"]] = relationship("ContaminationReport", back_populates="user", cascade="all, delete-orphan")
    water_quality_alerts: Mapped[list["WaterQualityAlert"]] = relationship("WaterQualityAlert", back_populates="user", cascade="all, delete-orphan")
    water_quality_preferences: Mapped["WaterQualityPreference"] = relationship("WaterQualityPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Basic profile info
    bio = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    status = Column(String(150), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    banner_color_hex = Column(String(7), nullable=True)
    is_public = Column(Boolean, default=True)
    
    # Enhanced customization fields
    display_name = Column(String(100), nullable=True)  # Different from username
    title = Column(String(100), nullable=True)  # User-earned or custom title
    avatar_style = Column(String(50), default='default')  # 'default', 'custom', 'generated'
    avatar_data = Column(JSON, nullable=True)  # JSON for avatar customization
    theme_preference = Column(String(50), default='auto')  # 'light', 'dark', 'auto', 'custom'
    theme_data = Column(JSON, nullable=True)  # Custom theme colors and settings
    banner_image_url = Column(String(500), nullable=True)
    pronouns = Column(String(50), nullable=True)  # e.g., "they/them", "she/her"
    timezone = Column(String(50), nullable=True)
    language_preference = Column(String(10), default='en')
    
    # Privacy settings
    show_email = Column(Boolean, default=False)
    show_location = Column(Boolean, default=True)
    show_achievements = Column(Boolean, default=True)
    show_stats = Column(Boolean, default=True)
    show_activity = Column(Boolean, default=True)
    allow_friend_requests = Column(Boolean, default=True)
    allow_challenge_invites = Column(Boolean, default=True)
    
    # Profile completion and verification
    profile_completion_percentage = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    verification_badge = Column(String(50), nullable=True)
    
    # Gamification and social
    favorite_water_type = Column(String(100), nullable=True)
    hydration_motto = Column(String(200), nullable=True)
    achievements_showcase = Column(JSON, nullable=True)  # Array of achievement IDs to showcase
    badges_showcase = Column(JSON, nullable=True)  # Array of badge IDs to showcase
    
    # Stats and streaks
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_log_date = Column(DateTime, nullable=True)
    daily_goal_ml = Column(Integer, default=2000)
    total_xp = Column(Integer, default=0)  # Lifetime XP earned
    
    # Level and points
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    points = Column(Integer, default=0)
    
    # Profile timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="profile")
    health_goals = relationship("HealthGoal", secondary=user_profile_health_goal_association, back_populates="user_profiles")

# New models for profile customization

class ProfileBadge(Base):
    __tablename__ = 'profile_badges'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    icon_emoji = Column(String(10), nullable=True)
    icon_url = Column(String(500), nullable=True)
    rarity = Column(String(20), default='common')  # 'common', 'rare', 'epic', 'legendary'
    unlock_criteria = Column(JSON, nullable=True)  # JSON for unlock requirements
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserBadge(Base):
    __tablename__ = 'user_badges'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    badge_id = Column(Integer, ForeignKey('profile_badges.id'), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    is_showcased = Column(Boolean, default=False)
    
    user = relationship("User")
    badge = relationship("ProfileBadge")

class ProfileTheme(Base):
    __tablename__ = 'profile_themes'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    color_scheme = Column(JSON, nullable=False)  # JSON with color definitions
    is_premium = Column(Boolean, default=False)
    unlock_level = Column(Integer, default=1)
    unlock_points = Column(Integer, default=0)
    preview_image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserTheme(Base):
    __tablename__ = 'user_themes'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    theme_id = Column(Integer, ForeignKey('profile_themes.id'), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)
    
    user = relationship("User")
    theme = relationship("ProfileTheme")

class AvatarAsset(Base):
    __tablename__ = 'avatar_assets'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # 'hair', 'eyes', 'clothing', 'accessories', etc.
    asset_url = Column(String(500), nullable=False)
    rarity = Column(String(20), default='common')
    unlock_level = Column(Integer, default=1)
    unlock_points = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserAvatarAsset(Base):
    __tablename__ = 'user_avatar_assets'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    asset_id = Column(Integer, ForeignKey('avatar_assets.id'), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    asset = relationship("AvatarAsset")

class ProfileVisit(Base):
    __tablename__ = 'profile_visits'
    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    visited_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    visited_at = Column(DateTime, default=datetime.utcnow)
    
    visitor = relationship("User", foreign_keys=[visitor_id])
    visited = relationship("User", foreign_keys=[visited_id])

class ProfileCustomization(Base):
    __tablename__ = 'profile_customizations'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    layout_style = Column(String(50), default='default')  # 'default', 'compact', 'detailed'
    widget_preferences = Column(JSON, nullable=True)  # JSON for widget visibility and order
    custom_css = Column(Text, nullable=True)  # Custom CSS for advanced users
    background_pattern = Column(String(50), nullable=True)
    animation_preferences = Column(JSON, nullable=True)  # Animation settings
    font_preferences = Column(JSON, nullable=True)  # Font family, size preferences
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")

class UserTitle(Base):
    __tablename__ = 'user_titles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    unlock_criteria = Column(JSON, nullable=True)
    rarity = Column(String(20), default='common')
    color_hex = Column(String(7), nullable=True)  # Color for the title
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserTitleOwnership(Base):
    __tablename__ = 'user_title_ownership'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    title_id = Column(Integer, ForeignKey('user_titles.id'), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)  # Only one title can be active at a time
    
    user = relationship("User")
    title = relationship("UserTitle")

class ProfileShowcase(Base):
    __tablename__ = 'profile_showcases'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    featured_achievement_id = Column(Integer, ForeignKey('achievements.id'), nullable=True)
    featured_badge_ids = Column(JSON, nullable=True)  # Array of badge IDs
    featured_stats = Column(JSON, nullable=True)  # Array of stat types to show
    featured_quote = Column(String(200), nullable=True)
    showcase_order = Column(JSON, nullable=True)  # Order of showcase elements
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    featured_achievement = relationship("Achievement")

class HealthGoal(Base):
    __tablename__ = "health_goals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    
    user_profiles = relationship("UserProfile", secondary=user_profile_health_goal_association, back_populates="health_goals")

class WaterLog(Base):
    __tablename__ = "water_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    water_id = Column(Integer, ForeignKey("water_data.id"), nullable=False)
    volume = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    drink_type_id = Column(Integer, ForeignKey("drink_types.id"), nullable=True)
    water_source_id = Column(Integer, ForeignKey("water_sources.id"), nullable=True)
    caffeine_mg = Column(Integer, nullable=True)
    
    user = relationship("User", back_populates="water_logs")
    water = relationship("WaterData", back_populates="logs")
    drink_type = relationship("DrinkType")
    water_source = relationship("WaterSource", back_populates="water_logs")

class WaterData(Base):
    __tablename__ = 'water_data'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    brand_name = Column(String)
    packaging = Column(String)
    score = Column(Float)
    ph_level = Column(Float)
    tds = Column(Float)
    # Storing complex objects as JSON is simpler for this migration
    ingredients = Column(JSON)
    report = Column(JSON)
    
    reviews = relationship("Review", back_populates="water")
    logs = relationship("WaterLog", back_populates="water")

class WaterDataFTS(Base):
    __tablename__ = 'water_data_fts'
    rowid = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    brand_name = Column(String)

# DDL for creating FTS table and triggers
create_fts_table = DDL("""
CREATE VIRTUAL TABLE IF NOT EXISTS water_data_fts USING fts5(
    name,
    description,
    brand_name,
    content='water_data',
    content_rowid='id'
);
""")

# Triggers to keep FTS table synchronized with water_data table
create_fts_triggers = DDL("""
CREATE TRIGGER IF NOT EXISTS water_data_after_insert
AFTER INSERT ON water_data BEGIN
    INSERT INTO water_data_fts(rowid, name, description, brand_name)
    VALUES (new.id, new.name, new.description, new.brand_name);
END;

CREATE TRIGGER IF NOT EXISTS water_data_after_delete
AFTER DELETE ON water_data BEGIN
    INSERT INTO water_data_fts(water_data_fts, rowid, name, description, brand_name)
    VALUES ('delete', old.id, old.name, old.description, old.brand_name);
END;

CREATE TRIGGER IF NOT EXISTS water_data_after_update
AFTER UPDATE ON water_data BEGIN
    INSERT INTO water_data_fts(water_data_fts, rowid, name, description, brand_name)
    VALUES ('delete', old.id, old.name, old.description, old.brand_name);
    INSERT INTO water_data_fts(rowid, name, description, brand_name)
    VALUES (new.id, new.name, new.description, new.brand_name);
END;
""")

# Attach DDL to the table's metadata
event.listen(WaterData.__table__, 'after_create', create_fts_table)
event.listen(WaterData.__table__, 'after_create', create_fts_triggers)

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    water_id = Column(Integer, ForeignKey('water_data.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="reviews")
    water = relationship("WaterData", back_populates="reviews")

class UserFollow(Base):
    __tablename__ = "user_follows"
    follower_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    following_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    activity_type = Column(String, nullable=False)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activities")

class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    criteria = Column(JSON)
    total_stages = Column(Integer, default=1)

class UserAchievement(Base):
    __tablename__ = 'user_achievements'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    achievement_id = Column(String, ForeignKey('achievements.id'), nullable=False)
    stage = Column(Integer, default=1)
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")
    comments = relationship("Comment", back_populates="user_achievement", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user_achievement_id = Column(Integer, ForeignKey('user_achievements.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    user_achievement = relationship("UserAchievement", back_populates="comments")

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cron_schedule = Column(String, nullable=False)
    message = Column(String, default="Time to drink some water!")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    addressee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, accepted, declined, blocked
    created_at = Column(DateTime, default=datetime.utcnow)
    
    requester = relationship("User", foreign_keys=[requester_id])
    addressee = relationship("User", foreign_keys=[addressee_id])

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    device_type = Column(String, nullable=False) # 'ios' or 'android'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class APIKey(Base):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True, index=True)
    key_prefix = Column(String, unique=True, index=True, nullable=False)
    hashed_key = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User")

class Challenge(Base):
    __tablename__ = 'challenges'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    challenge_type = Column(String, nullable=False)  # e.g., 'total_volume', 'streak_days', 'daily_goal', 'consistency'
    goal = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Null for system challenges
    is_public = Column(Boolean, default=True)
    max_participants = Column(Integer, nullable=True)  # Null for unlimited
    difficulty_level = Column(String, default='medium')  # 'easy', 'medium', 'hard', 'extreme'
    reward_points = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    category = Column(String, nullable=True)  # 'hydration', 'streak', 'social', 'consistency'
    is_team_challenge = Column(Boolean, default=False)
    team_size = Column(Integer, default=1)
    entry_fee_points = Column(Integer, default=0)  # Points required to join
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    user_challenges = relationship("UserChallenge", back_populates="challenge")
    challenge_teams = relationship("ChallengeTeam", back_populates="challenge")

class UserChallenge(Base):
    __tablename__ = 'user_challenges'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete="CASCADE"), nullable=False)
    progress = Column(Float, default=0.0)
    completed_at = Column(DateTime, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_abandoned = Column(Boolean, default=False)
    abandoned_at = Column(DateTime, nullable=True)
    final_rank = Column(Integer, nullable=True)
    points_earned = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    team_id = Column(Integer, ForeignKey('challenge_teams.id'), nullable=True)
    
    user = relationship("User")
    challenge = relationship("Challenge", back_populates="user_challenges")
    team = relationship("ChallengeTeam", back_populates="members")

class ChallengeTeam(Base):
    __tablename__ = 'challenge_teams'
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    leader_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_progress = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    challenge = relationship("Challenge", back_populates="challenge_teams")
    leader = relationship("User", foreign_keys=[leader_id])
    members = relationship("UserChallenge", back_populates="team")

class ChallengeInvitation(Base):
    __tablename__ = 'challenge_invitations'
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete="CASCADE"), nullable=False)
    inviter_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    invitee_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    status = Column(String, default='pending')  # 'pending', 'accepted', 'declined'
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    
    challenge = relationship("Challenge")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])

class ChallengeComment(Base):
    __tablename__ = 'challenge_comments'
    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey('challenges.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    challenge = relationship("Challenge")
    user = relationship("User")

class CoachingTip(Base):
    __tablename__ = 'coaching_tips'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String) # e.g., 'general', 'morning', 'evening', 'exercise'

class UserCoaching(Base):
    __tablename__ = 'user_coaching'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    tip_id = Column(Integer, ForeignKey('coaching_tips.id', ondelete="CASCADE"), nullable=False)
    seen_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    tip = relationship("CoachingTip")

class HealthIntegration(Base):
    __tablename__ = 'health_integrations'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    provider = Column(String, nullable=False)  # e.g., 'apple_health', 'google_fit'
    access_token = Column(String, nullable=False)
    refresh_token = Column(String)
    last_sync_at = Column(DateTime)
    
    user = relationship("User")

class DrinkType(Base):
    __tablename__ = 'drink_types'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    hydration_multiplier = Column(Float, nullable=False, default=1.0) # e.g., coffee might be 0.8 

class DailyStreak(Base):
    __tablename__ = 'daily_streaks'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    goal_met = Column(Boolean, default=False)
    total_volume_ml = Column(Float, default=0.0)
    goal_volume_ml = Column(Float, nullable=False)
    percentage_completed = Column(Float, default=0.0)
    streak_day = Column(Integer, default=0)  # Which day of the current streak this is
    
    user = relationship("User")
    
    __table_args__ = (
        # Ensure one record per user per day
        Column('user_id', 'date', unique=True),
    ) 

class XPSource(Base):
    __tablename__ = 'xp_sources'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    base_xp = Column(Integer, default=0)
    multiplier = Column(Float, default=1.0)
    daily_limit = Column(Integer, nullable=True)  # Max XP per day from this source
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserXPLog(Base):
    __tablename__ = 'user_xp_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    xp_source_id = Column(Integer, ForeignKey('xp_sources.id'), nullable=False)
    xp_gained = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    xp_source = relationship("XPSource")

class LevelReward(Base):
    __tablename__ = 'level_rewards'
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, nullable=False)
    reward_type = Column(String, nullable=False)  # 'points', 'badge', 'feature_unlock', 'title'
    reward_value = Column(String, nullable=False)  # JSON string for complex rewards
    description = Column(Text)
    is_claimed_automatically = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserLevelReward(Base):
    __tablename__ = 'user_level_rewards'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    level_reward_id = Column(Integer, ForeignKey('level_rewards.id'), nullable=False)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    level_reward = relationship("LevelReward")

class PrestigeLevel(Base):
    __tablename__ = 'prestige_levels'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    prestige_level = Column(Integer, default=0)
    total_resets = Column(Integer, default=0)
    prestige_points = Column(Integer, default=0)
    last_prestige_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class LevelMilestone(Base):
    __tablename__ = 'level_milestones'
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, nullable=False, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    badge_emoji = Column(String, nullable=True)
    xp_bonus_multiplier = Column(Float, default=1.0)
    special_privileges = Column(JSON, nullable=True)  # JSON for special features unlocked
    created_at = Column(DateTime, default=datetime.utcnow)

class SeasonalXPBoost(Base):
    __tablename__ = 'seasonal_xp_boosts'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    multiplier = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PointSource(Base):
    __tablename__ = 'point_sources'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    base_points = Column(Integer, default=0)
    multiplier = Column(Float, default=1.0)
    daily_limit = Column(Integer, nullable=True)  # Max points per day from this source
    weekly_limit = Column(Integer, nullable=True)  # Max points per week from this source
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PointTransaction(Base):
    __tablename__ = 'point_transactions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    point_source_id = Column(Integer, ForeignKey('point_sources.id'), nullable=True)
    transaction_type = Column(String, nullable=False)  # 'earned', 'spent', 'bonus', 'penalty', 'transfer'
    points_amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)  # 'challenge', 'achievement', 'purchase', etc.
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    point_source = relationship("PointSource")

class PointReward(Base):
    __tablename__ = 'point_rewards'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    cost_points = Column(Integer, nullable=False)
    reward_type = Column(String, nullable=False)  # 'cosmetic', 'feature', 'badge', 'xp_boost', 'item'
    reward_data = Column(JSON, nullable=True)  # JSON data for the reward
    is_available = Column(Boolean, default=True)
    is_limited = Column(Boolean, default=False)
    stock_quantity = Column(Integer, nullable=True)  # For limited items
    purchase_limit_per_user = Column(Integer, nullable=True)
    required_level = Column(Integer, default=1)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PointPurchase(Base):
    __tablename__ = 'point_purchases'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    point_reward_id = Column(Integer, ForeignKey('point_rewards.id'), nullable=False)
    points_spent = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # For rewards that can be deactivated
    
    user = relationship("User")
    point_reward = relationship("PointReward")

class PointBonus(Base):
    __tablename__ = 'point_bonuses'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    bonus_type = Column(String, nullable=False)  # 'daily', 'weekly', 'streak', 'seasonal', 'event'
    bonus_amount = Column(Integer, nullable=False)
    multiplier = Column(Float, default=1.0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    requirements = Column(JSON, nullable=True)  # JSON for bonus requirements
    created_at = Column(DateTime, default=datetime.utcnow)

class UserPointBonus(Base):
    __tablename__ = 'user_point_bonuses'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    point_bonus_id = Column(Integer, ForeignKey('point_bonuses.id'), nullable=False)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    points_awarded = Column(Integer, nullable=False)
    
    user = relationship("User")
    point_bonus = relationship("PointBonus")

class PointTransfer(Base):
    __tablename__ = 'point_transfers'
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    points_amount = Column(Integer, nullable=False)
    message = Column(String, nullable=True)
    transfer_fee = Column(Integer, default=0)
    status = Column(String, default='completed')  # 'pending', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class PointMilestone(Base):
    __tablename__ = 'point_milestones'
    id = Column(Integer, primary_key=True, index=True)
    points_threshold = Column(Integer, nullable=False, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    reward_type = Column(String, nullable=False)  # 'badge', 'xp', 'feature_unlock', 'multiplier'
    reward_value = Column(String, nullable=False)
    badge_emoji = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserPointMilestone(Base):
    __tablename__ = 'user_point_milestones'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    point_milestone_id = Column(Integer, ForeignKey('point_milestones.id'), nullable=False)
    achieved_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    point_milestone = relationship("PointMilestone")

class Friendship(Base):
    __tablename__ = "friendships"
    
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    addressee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, accepted, blocked
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="sent_friend_requests")
    addressee = relationship("User", foreign_keys=[addressee_id], back_populates="received_friend_requests")
    
    __table_args__ = (
        UniqueConstraint('requester_id', 'addressee_id'),
        Index('ix_friendships_status', 'status'),
        Index('ix_friendships_requester_id', 'requester_id'),
        Index('ix_friendships_addressee_id', 'addressee_id'),
    )

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), nullable=False, default="text")  # text, image, system, achievement
    is_read = Column(Boolean, nullable=False, default=False)
    is_deleted_by_sender = Column(Boolean, nullable=False, default=False)
    is_deleted_by_recipient = Column(Boolean, nullable=False, default=False)
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    attachment_url = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
    reply_to = relationship("Message", remote_side=[id])
    
    __table_args__ = (
        Index('ix_messages_sender_id', 'sender_id'),
        Index('ix_messages_recipient_id', 'recipient_id'),
        Index('ix_messages_created_at', 'created_at'),
        Index('ix_messages_is_read', 'is_read'),
    )

class ActivityFeed(Base):
    __tablename__ = "activity_feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # water_logged, achievement_earned, level_up, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    activity_data = Column(JSON, nullable=True)
    visibility = Column(String(20), nullable=False, default="friends")  # public, friends, private
    likes_count = Column(Integer, nullable=False, default=0)
    comments_count = Column(Integer, nullable=False, default=0)
    is_pinned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activity_feeds")
    likes = relationship("ActivityLike", back_populates="activity", cascade="all, delete-orphan")
    comments = relationship("ActivityComment", back_populates="activity", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_activity_feeds_user_id', 'user_id'),
        Index('ix_activity_feeds_activity_type', 'activity_type'),
        Index('ix_activity_feeds_created_at', 'created_at'),
        Index('ix_activity_feeds_visibility', 'visibility'),
    )

class ActivityLike(Base):
    __tablename__ = "activity_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activity_feeds.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activity_likes")
    activity = relationship("ActivityFeed", back_populates="likes")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'activity_id'),
        Index('ix_activity_likes_user_id', 'user_id'),
        Index('ix_activity_likes_activity_id', 'activity_id'),
    )

class ActivityComment(Base):
    __tablename__ = "activity_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activity_feeds.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("activity_comments.id"), nullable=True)
    likes_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activity_comments")
    activity = relationship("ActivityFeed", back_populates="comments")
    reply_to = relationship("ActivityComment", remote_side=[id])
    comment_likes = relationship("ActivityCommentLike", back_populates="comment", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_activity_comments_user_id', 'user_id'),
        Index('ix_activity_comments_activity_id', 'activity_id'),
        Index('ix_activity_comments_created_at', 'created_at'),
    )

class ActivityCommentLike(Base):
    __tablename__ = "activity_comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_id = Column(Integer, ForeignKey("activity_comments.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activity_comment_likes")
    comment = relationship("ActivityComment", back_populates="comment_likes")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id'),
        Index('ix_activity_comment_likes_user_id', 'user_id'),
        Index('ix_activity_comment_likes_comment_id', 'comment_id'),
    )

class SocialGroup(Base):
    __tablename__ = "social_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    group_type = Column(String(20), nullable=False, default="public")  # public, private, invite_only
    icon_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    member_count = Column(Integer, nullable=False, default=0)
    max_members = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    group_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="created_groups")
    members = relationship("SocialGroupMember", back_populates="group", cascade="all, delete-orphan")
    posts = relationship("SocialGroupPost", back_populates="group", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_social_groups_creator_id', 'creator_id'),
        Index('ix_social_groups_group_type', 'group_type'),
        Index('ix_social_groups_created_at', 'created_at'),
    )

class SocialGroupMember(Base):
    __tablename__ = "social_group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("social_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default="member")  # member, moderator, admin
    status = Column(String(20), nullable=False, default="active")  # active, muted, banned
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=True)
    
    # Relationships
    group = relationship("SocialGroup", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
    
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id'),
        Index('ix_social_group_members_group_id', 'group_id'),
        Index('ix_social_group_members_user_id', 'user_id'),
        Index('ix_social_group_members_role', 'role'),
    )

class SocialGroupPost(Base):
    __tablename__ = "social_group_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("social_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    post_type = Column(String(20), nullable=False, default="text")  # text, image, poll, achievement
    attachment_url = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)
    likes_count = Column(Integer, nullable=False, default=0)
    comments_count = Column(Integer, nullable=False, default=0)
    is_pinned = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("SocialGroup", back_populates="posts")
    user = relationship("User", back_populates="group_posts")
    likes = relationship("SocialGroupPostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("SocialGroupPostComment", back_populates="post", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_social_group_posts_group_id', 'group_id'),
        Index('ix_social_group_posts_user_id', 'user_id'),
        Index('ix_social_group_posts_created_at', 'created_at'),
        Index('ix_social_group_posts_post_type', 'post_type'),
    )

class SocialGroupPostLike(Base):
    __tablename__ = "social_group_post_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_group_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    post = relationship("SocialGroupPost", back_populates="likes")
    user = relationship("User", back_populates="group_post_likes")
    
    __table_args__ = (
        UniqueConstraint('post_id', 'user_id'),
        Index('ix_social_group_post_likes_post_id', 'post_id'),
        Index('ix_social_group_post_likes_user_id', 'user_id'),
    )

class SocialGroupPostComment(Base):
    __tablename__ = "social_group_post_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_group_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("social_group_post_comments.id"), nullable=True)
    likes_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = relationship("SocialGroupPost", back_populates="comments")
    user = relationship("User", back_populates="group_post_comments")
    reply_to = relationship("SocialGroupPostComment", remote_side=[id])
    
    __table_args__ = (
        Index('ix_social_group_post_comments_post_id', 'post_id'),
        Index('ix_social_group_post_comments_user_id', 'user_id'),
        Index('ix_social_group_post_comments_created_at', 'created_at'),
    )

class SocialAchievement(Base):
    __tablename__ = "social_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_type = Column(String(50), nullable=False)  # friend_count, message_count, group_creator, etc.
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    badge_color = Column(String(7), nullable=True)
    points_awarded = Column(Integer, nullable=False, default=0)
    achievement_data = Column(JSON, nullable=True)
    is_visible = Column(Boolean, nullable=False, default=True)
    earned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="social_achievements")
    
    __table_args__ = (
        Index('ix_social_achievements_user_id', 'user_id'),
        Index('ix_social_achievements_achievement_type', 'achievement_type'),
        Index('ix_social_achievements_earned_at', 'earned_at'),
    )

class SocialNotification(Base):
    __tablename__ = "social_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # friend_request, message, activity_like, etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    action_url = Column(String(500), nullable=True)
    related_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    related_object_id = Column(Integer, nullable=True)
    related_object_type = Column(String(50), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="social_notifications")
    related_user = relationship("User", foreign_keys=[related_user_id])
    
    __table_args__ = (
        Index('ix_social_notifications_user_id', 'user_id'),
        Index('ix_social_notifications_notification_type', 'notification_type'),
        Index('ix_social_notifications_created_at', 'created_at'),
        Index('ix_social_notifications_is_read', 'is_read'),
    )

# Update User model to include social relationships
def update_user_relationships():
    # Add social relationships to User model
    User.sent_friend_requests = relationship("Friendship", foreign_keys="Friendship.requester_id", back_populates="requester")
    User.received_friend_requests = relationship("Friendship", foreign_keys="Friendship.addressee_id", back_populates="addressee")
    User.sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    User.received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    User.activity_feeds = relationship("ActivityFeed", back_populates="user", cascade="all, delete-orphan")
    User.activity_likes = relationship("ActivityLike", back_populates="user", cascade="all, delete-orphan")
    User.activity_comments = relationship("ActivityComment", back_populates="user", cascade="all, delete-orphan")
    User.activity_comment_likes = relationship("ActivityCommentLike", back_populates="user", cascade="all, delete-orphan")
    User.created_groups = relationship("SocialGroup", back_populates="creator", cascade="all, delete-orphan")
    User.group_memberships = relationship("SocialGroupMember", back_populates="user", cascade="all, delete-orphan")
    User.group_posts = relationship("SocialGroupPost", back_populates="user", cascade="all, delete-orphan")
    User.group_post_likes = relationship("SocialGroupPostLike", back_populates="user", cascade="all, delete-orphan")
    User.group_post_comments = relationship("SocialGroupPostComment", back_populates="user", cascade="all, delete-orphan")
    User.social_achievements = relationship("SocialAchievement", back_populates="user", cascade="all, delete-orphan")
    User.social_notifications = relationship("SocialNotification", foreign_keys="SocialNotification.user_id", back_populates="user", cascade="all, delete-orphan")

# Call the function to update relationships
update_user_relationships()

# Import water quality models to ensure they're included in the metadata
from app.models.water_quality import (
    WaterSource, WaterQualityTest, ContaminationReport, 
    WaterQualityAlert, WaterFilterMaintenance, WaterQualityPreference
) 