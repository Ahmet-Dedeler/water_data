from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import math

from app.db.models import (
    UserProfile, XPSource, UserXPLog, LevelReward, UserLevelReward,
    PrestigeLevel, LevelMilestone, SeasonalXPBoost, User
)
from app.models.level import (
    UserLevelInfo, LevelProgressHistory, XPBreakdown, LevelLeaderboard,
    LevelStats, XPSourceCreate, LevelRewardCreate, LevelMilestoneCreate
)
from app.services.points_service import points_service

class LevelService:
    def __init__(self):
        self.points_service = points_service
        # Enhanced XP formula: exponential growth with scaling
        self.BASE_XP_PER_LEVEL = 100
        self.LEVEL_SCALING_FACTOR = 1.15
        self.PRESTIGE_LEVEL_REQUIREMENT = 100
        self.PRESTIGE_POINTS_PER_LEVEL = 5

    def get_xp_for_level(self, level: int) -> int:
        """Calculate total XP required to reach a specific level"""
        if level <= 1:
            return 0
        
        total_xp = 0
        for i in range(1, level):
            total_xp += int(self.BASE_XP_PER_LEVEL * (self.LEVEL_SCALING_FACTOR ** (i - 1)))
        return total_xp

    def get_xp_for_next_level(self, current_level: int) -> int:
        """Calculate XP needed for the next level"""
        return int(self.BASE_XP_PER_LEVEL * (self.LEVEL_SCALING_FACTOR ** (current_level - 1)))

    def get_level_from_total_xp(self, total_xp: int) -> int:
        """Calculate level from total XP"""
        if total_xp <= 0:
            return 1
        
        level = 1
        xp_needed = 0
        
        while xp_needed <= total_xp:
            xp_for_next = self.get_xp_for_next_level(level)
            if xp_needed + xp_for_next > total_xp:
                break
            xp_needed += xp_for_next
            level += 1
        
        return level

    def add_xp(self, db: Session, user_id: int, xp_to_add: int, source_name: str = "general", description: str = None) -> Dict[str, Any]:
        """Add XP to a user and handle level ups"""
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return {"success": False, "message": "User profile not found"}

        # Get or create XP source
        xp_source = db.query(XPSource).filter_by(name=source_name).first()
        if not xp_source:
            xp_source = XPSource(name=source_name, base_xp=xp_to_add, description=f"Auto-created for {source_name}")
            db.add(xp_source)
            db.commit()
            db.refresh(xp_source)

        # Check daily limit for this source
        if xp_source.daily_limit:
            today = datetime.utcnow().date()
            daily_xp = db.query(func.sum(UserXPLog.xp_gained)).filter(
                UserXPLog.user_id == user_id,
                UserXPLog.xp_source_id == xp_source.id,
                func.date(UserXPLog.created_at) == today
            ).scalar() or 0
            
            if daily_xp + xp_to_add > xp_source.daily_limit:
                xp_to_add = max(0, xp_source.daily_limit - daily_xp)
                if xp_to_add <= 0:
                    return {"success": False, "message": "Daily XP limit reached for this source"}

        # Apply XP multipliers
        final_xp = int(xp_to_add * xp_source.multiplier)
        
        # Apply seasonal boosts
        seasonal_multiplier = self.get_active_seasonal_multiplier(db)
        final_xp = int(final_xp * seasonal_multiplier)

        # Apply prestige multiplier
        prestige_multiplier = self.get_prestige_multiplier(db, user_id)
        final_xp = int(final_xp * prestige_multiplier)

        # Store old level for comparison
        old_level = user_profile.level
        old_total_xp = user_profile.total_xp or 0

        # Update user XP
        user_profile.total_xp = old_total_xp + final_xp
        new_level = self.get_level_from_total_xp(user_profile.total_xp)
        user_profile.level = new_level
        user_profile.xp = user_profile.total_xp - self.get_xp_for_level(new_level)

        # Log XP gain
        xp_log = UserXPLog(
            user_id=user_id,
            xp_source_id=xp_source.id,
            xp_gained=final_xp,
            description=description
        )
        db.add(xp_log)

        # Handle level ups
        levels_gained = new_level - old_level
        rewards_earned = []
        
        if levels_gained > 0:
            # Award level rewards
            for level in range(old_level + 1, new_level + 1):
                level_rewards = self.process_level_rewards(db, user_id, level)
                rewards_earned.extend(level_rewards)
            
            # Check for milestone rewards
            milestone_rewards = self.check_milestone_rewards(db, user_id, new_level)
            rewards_earned.extend(milestone_rewards)

        db.add(user_profile)
        db.commit()

        return {
            "success": True,
            "xp_gained": final_xp,
            "old_level": old_level,
            "new_level": new_level,
            "levels_gained": levels_gained,
            "rewards_earned": rewards_earned,
            "total_xp": user_profile.total_xp,
            "multipliers_applied": {
                "source": xp_source.multiplier,
                "seasonal": seasonal_multiplier,
                "prestige": prestige_multiplier
            }
        }

    def get_user_level_info(self, db: Session, user_id: int) -> Optional[UserLevelInfo]:
        """Get comprehensive level information for a user"""
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return None

        # Get prestige info
        prestige = db.query(PrestigeLevel).filter_by(user_id=user_id).first()
        prestige_level = prestige.prestige_level if prestige else 0
        prestige_points = prestige.prestige_points if prestige else 0

        # Get current level info
        current_level = user_profile.level
        current_xp = user_profile.xp
        total_xp = user_profile.total_xp or 0
        xp_to_next = self.get_xp_for_next_level(current_level)
        progress_percentage = (current_xp / xp_to_next * 100) if xp_to_next > 0 else 0

        # Get level milestone info
        milestone = db.query(LevelMilestone).filter_by(level=current_level).first()
        level_title = milestone.title if milestone else f"Level {current_level}"
        level_badge = milestone.badge_emoji if milestone else None

        # Get XP multiplier
        xp_multiplier = self.get_total_xp_multiplier(db, user_id)

        # Get next milestone
        next_milestone = db.query(LevelMilestone).filter(
            LevelMilestone.level > current_level
        ).order_by(LevelMilestone.level.asc()).first()

        return UserLevelInfo(
            user_id=user_id,
            level=current_level,
            current_xp=current_xp,
            total_xp=total_xp,
            xp_to_next_level=xp_to_next,
            level_progress_percentage=progress_percentage,
            prestige_level=prestige_level,
            prestige_points=prestige_points,
            level_title=level_title,
            level_badge=level_badge,
            xp_multiplier=xp_multiplier,
            next_milestone=next_milestone
        )

    def get_xp_breakdown(self, db: Session, user_id: int, days: int = 30) -> Optional[XPBreakdown]:
        """Get detailed XP breakdown for a user"""
        # Get total XP
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return None

        total_xp = user_profile.total_xp or 0

        # Get XP by source
        xp_by_source_query = db.query(
            XPSource.name,
            func.sum(UserXPLog.xp_gained).label('total_xp')
        ).join(
            UserXPLog, XPSource.id == UserXPLog.xp_source_id
        ).filter(
            UserXPLog.user_id == user_id
        ).group_by(XPSource.name).all()

        xp_by_source = {source.name: source.total_xp for source in xp_by_source_query}

        # Get daily XP for last N days
        start_date = datetime.utcnow() - timedelta(days=days)
        daily_xp_query = db.query(
            func.date(UserXPLog.created_at).label('date'),
            func.sum(UserXPLog.xp_gained).label('xp')
        ).filter(
            UserXPLog.user_id == user_id,
            UserXPLog.created_at >= start_date
        ).group_by(func.date(UserXPLog.created_at)).all()

        daily_xp_last_30_days = [
            {"date": str(day.date), "xp": day.xp}
            for day in daily_xp_query
        ]

        # Get top XP sources
        top_xp_sources = [
            {"source": source.name, "total_xp": source.total_xp}
            for source in sorted(xp_by_source_query, key=lambda x: x.total_xp, reverse=True)[:5]
        ]

        # Get active multipliers
        xp_multipliers_active = self.get_active_multipliers(db, user_id)

        return XPBreakdown(
            user_id=user_id,
            total_xp=total_xp,
            xp_by_source=xp_by_source,
            daily_xp_last_30_days=daily_xp_last_30_days,
            top_xp_sources=top_xp_sources,
            xp_multipliers_active=xp_multipliers_active
        )

    def get_level_leaderboard(self, db: Session, leaderboard_type: str = "level", limit: int = 20) -> LevelLeaderboard:
        """Get level leaderboard"""
        if leaderboard_type == "level":
            query = db.query(
                User.id,
                User.username,
                UserProfile.level,
                UserProfile.total_xp
            ).join(
                UserProfile, User.id == UserProfile.user_id
            ).order_by(
                desc(UserProfile.level),
                desc(UserProfile.total_xp)
            ).limit(limit)
        elif leaderboard_type == "xp":
            query = db.query(
                User.id,
                User.username,
                UserProfile.level,
                UserProfile.total_xp
            ).join(
                UserProfile, User.id == UserProfile.user_id
            ).order_by(
                desc(UserProfile.total_xp)
            ).limit(limit)
        elif leaderboard_type == "prestige":
            query = db.query(
                User.id,
                User.username,
                UserProfile.level,
                PrestigeLevel.prestige_level,
                PrestigeLevel.prestige_points
            ).join(
                UserProfile, User.id == UserProfile.user_id
            ).join(
                PrestigeLevel, User.id == PrestigeLevel.user_id
            ).order_by(
                desc(PrestigeLevel.prestige_level),
                desc(PrestigeLevel.prestige_points)
            ).limit(limit)
        else:
            raise ValueError("Invalid leaderboard type")

        results = query.all()
        entries = []
        
        for i, result in enumerate(results):
            entry = {
                "rank": i + 1,
                "user_id": result.id,
                "username": result.username,
                "level": result.level
            }
            
            if leaderboard_type == "prestige":
                entry["prestige_level"] = result.prestige_level
                entry["prestige_points"] = result.prestige_points
            else:
                entry["total_xp"] = result.total_xp or 0
            
            entries.append(entry)

        total_users = db.query(UserProfile).count()

        return LevelLeaderboard(
            entries=entries,
            total_users=total_users,
            leaderboard_type=leaderboard_type
        )

    def prestige_reset(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Reset user level for prestige points"""
        user_profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if not user_profile:
            return {"success": False, "message": "User profile not found"}

        if user_profile.level < self.PRESTIGE_LEVEL_REQUIREMENT:
            return {"success": False, "message": f"Must be level {self.PRESTIGE_LEVEL_REQUIREMENT} to prestige"}

        # Get or create prestige record
        prestige = db.query(PrestigeLevel).filter_by(user_id=user_id).first()
        if not prestige:
            prestige = PrestigeLevel(user_id=user_id)
            db.add(prestige)

        # Calculate prestige points earned
        prestige_points_earned = user_profile.level * self.PRESTIGE_POINTS_PER_LEVEL

        # Update prestige
        prestige.prestige_level += 1
        prestige.total_resets += 1
        prestige.prestige_points += prestige_points_earned
        prestige.last_prestige_at = datetime.utcnow()

        # Reset user level but keep some benefits
        old_level = user_profile.level
        user_profile.level = 1
        user_profile.xp = 0
        user_profile.total_xp = 0

        db.commit()

        return {
            "success": True,
            "old_level": old_level,
            "prestige_level": prestige.prestige_level,
            "prestige_points_earned": prestige_points_earned,
            "total_prestige_points": prestige.prestige_points
        }

    def process_level_rewards(self, db: Session, user_id: int, level: int) -> List[Dict[str, Any]]:
        """Process rewards for reaching a level"""
        rewards = db.query(LevelReward).filter_by(level=level).all()
        rewards_earned = []

        for reward in rewards:
            # Check if already claimed
            existing_claim = db.query(UserLevelReward).filter_by(
                user_id=user_id,
                level_reward_id=reward.id
            ).first()

            if existing_claim:
                continue

            # Claim reward
            user_reward = UserLevelReward(
                user_id=user_id,
                level_reward_id=reward.id
            )
            db.add(user_reward)

            # Process reward based on type
            if reward.reward_type == "points":
                points_amount = int(reward.reward_value)
                self.points_service.add_points(db, user_id, points_amount)
            elif reward.reward_type == "badge":
                # Badge handling would be implemented elsewhere
                pass
            elif reward.reward_type == "feature_unlock":
                # Feature unlock handling would be implemented elsewhere
                pass

            rewards_earned.append({
                "type": reward.reward_type,
                "value": reward.reward_value,
                "description": reward.description
            })

        return rewards_earned

    def check_milestone_rewards(self, db: Session, user_id: int, level: int) -> List[Dict[str, Any]]:
        """Check and award milestone rewards"""
        milestone = db.query(LevelMilestone).filter_by(level=level).first()
        if not milestone:
            return []

        return [{
            "type": "milestone",
            "value": milestone.title,
            "description": milestone.description,
            "badge": milestone.badge_emoji,
            "xp_multiplier": milestone.xp_bonus_multiplier
        }]

    def get_active_seasonal_multiplier(self, db: Session) -> float:
        """Get current seasonal XP multiplier"""
        now = datetime.utcnow()
        boost = db.query(SeasonalXPBoost).filter(
            SeasonalXPBoost.is_active == True,
            SeasonalXPBoost.start_date <= now,
            SeasonalXPBoost.end_date >= now
        ).first()

        return boost.multiplier if boost else 1.0

    def get_prestige_multiplier(self, db: Session, user_id: int) -> float:
        """Get prestige-based XP multiplier"""
        prestige = db.query(PrestigeLevel).filter_by(user_id=user_id).first()
        if not prestige:
            return 1.0

        # 5% bonus per prestige level
        return 1.0 + (prestige.prestige_level * 0.05)

    def get_total_xp_multiplier(self, db: Session, user_id: int) -> float:
        """Get total XP multiplier for a user"""
        base_multiplier = 1.0
        seasonal_multiplier = self.get_active_seasonal_multiplier(db)
        prestige_multiplier = self.get_prestige_multiplier(db, user_id)

        return base_multiplier * seasonal_multiplier * prestige_multiplier

    def get_active_multipliers(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get list of active XP multipliers"""
        multipliers = []

        # Seasonal boost
        seasonal_mult = self.get_active_seasonal_multiplier(db)
        if seasonal_mult > 1.0:
            boost = db.query(SeasonalXPBoost).filter(
                SeasonalXPBoost.is_active == True,
                SeasonalXPBoost.start_date <= datetime.utcnow(),
                SeasonalXPBoost.end_date >= datetime.utcnow()
            ).first()
            if boost:
                multipliers.append({
                    "type": "seasonal",
                    "name": boost.name,
                    "multiplier": boost.multiplier,
                    "description": boost.description
                })

        # Prestige multiplier
        prestige_mult = self.get_prestige_multiplier(db, user_id)
        if prestige_mult > 1.0:
            multipliers.append({
                "type": "prestige",
                "name": "Prestige Bonus",
                "multiplier": prestige_mult,
                "description": f"Bonus from prestige levels"
            })

        return multipliers

    def get_level_stats(self, db: Session) -> LevelStats:
        """Get overall level statistics"""
        total_users = db.query(UserProfile).count()
        
        # Average level
        avg_level = db.query(func.avg(UserProfile.level)).scalar() or 0
        
        # Highest level
        highest_level = db.query(func.max(UserProfile.level)).scalar() or 0
        
        # Total XP distributed
        total_xp = db.query(func.sum(UserProfile.total_xp)).scalar() or 0
        
        # Active XP sources
        active_sources = db.query(XPSource).filter_by(is_active=True).count()
        
        # Level distribution
        level_dist_query = db.query(
            UserProfile.level,
            func.count(UserProfile.level).label('count')
        ).group_by(UserProfile.level).all()
        
        level_distribution = {f"Level {ld.level}": ld.count for ld in level_dist_query}
        
        # Prestige users
        prestige_users = db.query(PrestigeLevel).filter(
            PrestigeLevel.prestige_level > 0
        ).count()

        return LevelStats(
            total_users=total_users,
            average_level=avg_level,
            highest_level=highest_level,
            total_xp_distributed=total_xp,
            active_xp_sources=active_sources,
            level_distribution=level_distribution,
            prestige_users=prestige_users
        )

    # Admin methods for managing XP sources and rewards
    def create_xp_source(self, db: Session, xp_source_data: XPSourceCreate) -> XPSource:
        """Create a new XP source"""
        xp_source = XPSource(**xp_source_data.model_dump())
        db.add(xp_source)
        db.commit()
        db.refresh(xp_source)
        return xp_source

    def create_level_reward(self, db: Session, reward_data: LevelRewardCreate) -> LevelReward:
        """Create a new level reward"""
        reward = LevelReward(**reward_data.model_dump())
        db.add(reward)
        db.commit()
        db.refresh(reward)
        return reward

    def create_level_milestone(self, db: Session, milestone_data: LevelMilestoneCreate) -> LevelMilestone:
        """Create a new level milestone"""
        milestone = LevelMilestone(**milestone_data.model_dump())
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return milestone

level_service = LevelService() 