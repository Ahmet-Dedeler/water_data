"""
Service for managing health goals, progress, and achievements.
"""

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.models.health_goal import (
    HealthGoal, HealthGoalCreate, HealthGoalUpdate, HealthGoalStatus,
    ProgressEntry, ProgressMeasurement, HealthGoalProgress, Milestone,
    Achievement, HealthGoalStats, HealthGoalSummary, HealthGoalType
)
from app.services.user_service import user_service
# from app.services.notification_service import notification_service # Placeholder for later feature
from app.services.data_service import DataService
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class HealthGoalService(BaseService[HealthGoal, HealthGoalCreate, HealthGoalUpdate]):
    """Service for managing user health goals."""
    
    def __init__(self):
        self.goals_file = Path(__file__).parent.parent / "data" / "health_goals.json"
        self.achievements_file = Path(__file__).parent.parent / "data" / "achievements.json"
        self._ensure_data_files()
        self._goals_cache = None
        self._achievements_cache = None
        self.data_service = DataService()
    
    def _ensure_data_files(self):
        """Ensure health goal data files exist."""
        data_dir = self.goals_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [self.goals_file, self.achievements_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_goals(self) -> List[Dict]:
        """Load health goals from file."""
        if self._goals_cache is None:
            try:
                with open(self.goals_file, 'r') as f:
                    self._goals_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading health goals: {e}")
                self._goals_cache = []
        return self._goals_cache
    
    async def _save_goals(self, goals: List[Dict]):
        """Save health goals to file."""
        try:
            with open(self.goals_file, 'w') as f:
                json.dump(goals, f, indent=2, default=str)
            self._goals_cache = goals
        except Exception as e:
            logger.error(f"Error saving health goals: {e}")
            raise
    
    async def _load_achievements(self) -> List[Dict]:
        """Load achievements from file."""
        if self._achievements_cache is None:
            try:
                with open(self.achievements_file, 'r') as f:
                    self._achievements_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading achievements: {e}")
                self._achievements_cache = []
        return self._achievements_cache
    
    async def _save_achievements(self, achievements: List[Dict]):
        """Save achievements to file."""
        try:
            with open(self.achievements_file, 'w') as f:
                json.dump(achievements, f, indent=2, default=str)
            self._achievements_cache = achievements
        except Exception as e:
            logger.error(f"Error saving achievements: {e}")
            raise

    def get_goals_by_user(self, db: Session, *, user_id: int) -> List[HealthGoal]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

    def create_goal(self, db: Session, *, user_id: int, goal_in: HealthGoalCreate) -> HealthGoal:
        goal_data = goal_in.dict()
        db_obj = self.model(**goal_data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        self.check_and_update_goal_status(db, db_obj)
        return db_obj

    def get_goal(self, db: Session, *, goal_id: int) -> Optional[HealthGoal]:
        return self.get(db, id=goal_id)

    def update_goal(self, db: Session, *, goal_obj: HealthGoal, goal_in: HealthGoalUpdate) -> HealthGoal:
        updated_goal = self.update(db, db_obj=goal_obj, obj_in=goal_in)
        self.check_and_update_goal_status(db, updated_goal)
        return updated_goal

    def delete_goal(self, db: Session, *, goal_id: int):
        self.remove(db, id=goal_id)

    def check_and_update_goal_status(self, db: Session, goal: HealthGoal):
        """
        Checks if a goal's end date has passed and updates its status to 'completed' if so.
        This could be called periodically by a background task.
        """
        if goal.end_date < date.today() and goal.status == "active":
            goal.status = "completed"
            db.add(goal)
            db.commit()
            db.refresh(goal)
            logger.info(f"Goal {goal.id} for user {goal.user_id} has been automatically completed.")

    async def create_health_goal(self, user_id: int, goal_data: HealthGoalCreate) -> HealthGoal:
        """Create a new health goal for a user."""
        goals = await self._load_goals()
        
        goal_id = str(uuid.uuid4())
        
        if not goal_data.custom_milestones:
            milestones = self._generate_default_milestones(goal_id, goal_data)
        else:
            milestones = goal_data.custom_milestones
            for i, ms in enumerate(milestones):
                ms.id = str(uuid.uuid4())
                # ms.goal_id = goal_id # This would require a model change, skipping for now
                ms.order = i
        
        goal = HealthGoal(
            id=goal_id,
            user_id=user_id,
            milestones=milestones,
            **goal_data.dict(exclude={"custom_milestones"})
        )
        
        goal.progress = await self._calculate_goal_progress(goal)
        
        goals.append(goal.dict())
        await self._save_goals(goals)
        
        logger.info(f"Created health goal {goal_id} for user {user_id}")
        # await notification_service.send_notification(user_id, f"New goal '{goal.name}' created!") # Placeholder
        
        return goal

    def _generate_default_milestones(self, goal_id: str, goal_data: HealthGoalCreate) -> List[Milestone]:
        """Generate default milestones for a goal."""
        milestones = []
        target = goal_data.target_value
        unit = goal_data.unit
        
        levels = [0.1, 0.25, 0.5, 0.75, 1.0]
        names = ["First Step", "Getting Serious", "Halfway There", "Almost Done", "Goal Achieved!"]
        points = [10, 25, 50, 75, 100]
        
        for i, level in enumerate(levels):
            milestone = Milestone(
                id=str(uuid.uuid4()),
                # goal_id=goal_id,
                name=names[i],
                description=f"Achieve {level*100}% of your goal",
                target_value=target * level,
                unit=unit,
                reward_points=points[i],
                order=i
            )
            milestones.append(milestone)
        
        return milestones

    async def get_health_goal(self, goal_id: str, user_id: int) -> Optional[HealthGoal]:
        """Get a specific health goal for a user."""
        goals = await self._load_goals()
        goal_dict = next((g for g in goals if g['id'] == goal_id and g['user_id'] == user_id), None)
        
        if not goal_dict:
            return None
            
        goal = HealthGoal(**goal_dict)
        goal.progress = await self._calculate_goal_progress(goal)
        return goal

    async def get_all_user_goals(
        self,
        user_id: int,
        status: Optional[HealthGoalStatus] = None,
        goal_type: Optional[HealthGoalType] = None,
        sort_by: str = "priority",
        sort_order: str = "desc"
    ) -> List[HealthGoalSummary]:
        """Get all health goals for a user."""
        goals = await self._load_goals()
        user_goals = [HealthGoal(**g) for g in goals if g['user_id'] == user_id]
        
        if status:
            user_goals = [g for g in user_goals if g.status == status]
        if goal_type:
            user_goals = [g for g in user_goals if g.goal_type == goal_type]
        
        # Sort goals
        reverse = sort_order == "desc"
        user_goals.sort(key=lambda g: getattr(g, sort_by, 0), reverse=reverse)
        
        summaries = []
        for goal in user_goals:
            goal.progress = await self._calculate_goal_progress(goal)
            summaries.append(self._create_goal_summary(goal))
            
        return summaries

    async def update_health_goal(self, goal_id: str, user_id: int, update_data: HealthGoalUpdate) -> Optional[HealthGoal]:
        """Update a health goal."""
        goals = await self._load_goals()
        goal_index = next((i for i, g in enumerate(goals) if g['id'] == goal_id and g['user_id'] == user_id), None)
        
        if goal_index is None:
            return None
        
        goal_dict = goals[goal_index]
        update_dict = update_data.dict(exclude_unset=True)
        
        goal_dict.update(update_dict)
        goal_dict['updated_at'] = datetime.utcnow()
        
        goal = HealthGoal(**goal_dict)
        goals[goal_index] = goal.dict()
        await self._save_goals(goals)
        
        logger.info(f"Updated health goal {goal_id} for user {user_id}")
        return goal

    async def delete_health_goal(self, goal_id: str, user_id: int) -> bool:
        """Delete a health goal."""
        goals = await self._load_goals()
        initial_len = len(goals)
        
        goals = [g for g in goals if not (g['id'] == goal_id and g['user_id'] == user_id)]
        
        if len(goals) < initial_len:
            await self._save_goals(goals)
            logger.info(f"Deleted health goal {goal_id} for user {user_id}")
            return True
        return False

    async def log_progress(self, goal_id: str, user_id: int, entry: ProgressEntry) -> Tuple[Optional[ProgressMeasurement], List[Achievement]]:
        """Log progress for a health goal."""
        goals = await self._load_goals()
        goal_index = next((i for i, g in enumerate(goals) if g['id'] == goal_id and g['user_id'] == user_id), None)
        if goal_index is None:
            return None, []
        
        goal = HealthGoal(**goals[goal_index])
        
        measurement = ProgressMeasurement(
            id=str(uuid.uuid4()),
            goal_id=goal_id,
            **entry.dict()
        )
        
        goal.measurements.append(measurement)
        
        # Update current value
        if goal.goal_type == HealthGoalType.DAILY_HYDRATION:
            # Accumulate for the day
            today = date.today()
            daily_total = sum(m.value for m in goal.measurements if m.measured_at.date() == today)
            goal.current_value = daily_total
        else:
            goal.current_value += entry.value

        goal.updated_at = datetime.utcnow()
        
        # Check for milestone achievements
        new_achievements = await self._check_for_milestones(goal)
        
        # Update goal progress summary
        goal.progress = await self._calculate_goal_progress(goal)
        
        # Save updated goal
        goals[goal_index] = goal.dict()
        await self._save_goals(goals)
        
        logger.info(f"Logged progress for goal {goal_id} for user {user_id}")
        return measurement, new_achievements

    async def _check_for_milestones(self, goal: HealthGoal) -> List[Achievement]:
        """Check for and award new milestones."""
        new_achievements = []
        
        for milestone in goal.milestones:
            if not milestone.achieved and goal.current_value >= milestone.target_value:
                milestone.achieved = True
                milestone.achieved_at = datetime.utcnow()
                
                achievement = Achievement(
                    id=str(uuid.uuid4()),
                    user_id=goal.user_id,
                    goal_id=goal.id,
                    milestone_id=milestone.id,
                    points_earned=milestone.reward_points,
                    badge_earned=milestone.badge_name,
                    celebration_message=f"You've reached the '{milestone.name}' milestone for your goal: '{goal.name}'!"
                )
                
                goal.achievements.append(achievement)
                new_achievements.append(achievement)
                
                # Update user profile with points, etc. (future)
                # await user_service.add_points(goal.user_id, achievement.points_earned)
                
                # Save achievement
                all_achievements = await self._load_achievements()
                all_achievements.append(achievement.dict())
                await self._save_achievements(all_achievements)
                
                logger.info(f"User {goal.user_id} achieved milestone {milestone.id} for goal {goal.id}")
                # await notification_service.send_notification(goal.user_id, achievement.celebration_message) # Placeholder
        
        return new_achievements

    async def _calculate_goal_progress(self, goal: HealthGoal) -> HealthGoalProgress:
        """Calculate the progress summary for a goal."""
        completion_percentage = 0
        if goal.target_value > 0:
            completion_percentage = min((goal.current_value / goal.target_value) * 100, 100)
        
        streak_days, best_streak = self._calculate_streaks(goal.measurements)
        
        # More complex calculations can be added here
        
        return HealthGoalProgress(
            goal_id=goal.id,
            current_value=goal.current_value,
            target_value=goal.target_value,
            unit=goal.unit,
            completion_percentage=completion_percentage,
            streak_days=streak_days,
            best_streak=best_streak,
            total_measurements=len(goal.measurements),
            last_measurement_at=goal.measurements[-1].measured_at if goal.measurements else None,
            milestones_achieved=len([m for m in goal.milestones if m.achieved]),
            total_milestones=len(goal.milestones)
        )

    def _calculate_streaks(self, measurements: List[ProgressMeasurement]) -> Tuple[int, int]:
        """Calculate current and best streak."""
        if not measurements:
            return 0, 0
            
        # Group measurements by day
        daily_entries = sorted(list({m.measured_at.date() for m in measurements}))
        
        if not daily_entries:
            return 0, 0
            
        current_streak = 0
        best_streak = 0
        
        if daily_entries[-1] == date.today() or daily_entries[-1] == date.today() - timedelta(days=1):
            current_streak = 1
            for i in range(len(daily_entries) - 1, 0, -1):
                if (daily_entries[i] - daily_entries[i-1]).days == 1:
                    current_streak += 1
                else:
                    break
        
        temp_streak = 1
        for i in range(len(daily_entries) -1):
            if (daily_entries[i+1] - daily_entries[i]).days == 1:
                temp_streak += 1
            else:
                best_streak = max(best_streak, temp_streak)
                temp_streak = 1
        best_streak = max(best_streak, temp_streak)
        
        return current_streak, best_streak

    def _create_goal_summary(self, goal: HealthGoal) -> HealthGoalSummary:
        """Create a summary view of a health goal."""
        days_remaining = None
        if goal.target_date and goal.status == HealthGoalStatus.ACTIVE:
            days_remaining = (goal.target_date - date.today()).days
        
        return HealthGoalSummary(
            id=goal.id,
            name=goal.name,
            goal_type=goal.goal_type,
            status=goal.status,
            priority=goal.priority,
            target_value=goal.target_value,
            current_value=goal.current_value,
            unit=goal.unit,
            completion_percentage=goal.progress.completion_percentage if goal.progress else 0.0,
            streak_days=goal.progress.streak_days if goal.progress else 0,
            days_remaining=days_remaining,
            milestones_achieved=goal.progress.milestones_achieved if goal.progress else 0,
            total_milestones=goal.progress.total_milestones if goal.progress else 0,
            last_activity=goal.updated_at
        )

    async def get_user_goal_stats(self, user_id: int) -> HealthGoalStats:
        """Get overall goal statistics for a user."""
        summaries = await self.get_all_user_goals(user_id)
        achievements = await self._load_achievements()
        user_achievements = [Achievement(**a) for a in achievements if a['user_id'] == user_id]
        
        # This is a bit inefficient, loading all goals to create summaries, then loading them again inside get_all_user_goals
        # A refactor could optimize this.
        goals = await self._load_goals()
        user_goals = [HealthGoal(**g) for g in goals if g['user_id'] == user_id]

        if not user_goals:
            return HealthGoalStats()
        
        active_goals = [g for g in user_goals if g.status == HealthGoalStatus.ACTIVE]
        completed_goals = [g for g in user_goals if g.status == HealthGoalStatus.COMPLETED]
        
        # Most active goal type
        goal_types = [g.goal_type for g in active_goals]
        most_active_type = max(set(goal_types), key=goal_types.count) if goal_types else None
        
        # Calculate completion rates by type
        completion_rates = defaultdict(list)
        for goal in user_goals:
            progress = await self._calculate_goal_progress(goal)
            completion_rates[goal.goal_type].append(progress.completion_percentage)
        
        avg_completion_by_type = {
            k: sum(v) / len(v) for k, v in completion_rates.items()
        }

        all_streaks = []
        for goal in user_goals:
            progress = await self._calculate_goal_progress(goal)
            all_streaks.append(progress.best_streak)


        return HealthGoalStats(
            total_goals=len(user_goals),
            active_goals=len(active_goals),
            completed_goals=len(completed_goals),
            total_achievements=len(user_achievements),
            total_points_earned=sum(a.points_earned for a in user_achievements),
            current_streaks=sum(1 for g in active_goals if (await self._calculate_goal_progress(g)).streak_days > 0),
            longest_streak=max(all_streaks, default=0),
            average_completion_rate=sum(v[0] for v in avg_completion_by_type.values()) / len(avg_completion_by_type) if avg_completion_by_type else 0.0,
            most_active_goal_type=most_active_type,
            completion_rate_by_type=avg_completion_by_type,
            recent_achievements=sorted(user_achievements, key=lambda a: a.achieved_at, reverse=True)[:5]
        )


health_goal_service = HealthGoalService() 