import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict, Counter

from app.models.drink import (
    DrinkType, DrinkTypeCreate, DrinkTypeUpdate, DrinkLog, DrinkLogCreate,
    DrinkLogUpdate, DrinkSummary, DrinkRecommendation, DrinkStats,
    DrinkCategory, CaffeineLevel, HydrationEffect
)
from app.models.common import BaseResponse
from app.services.user_service import user_service

logger = logging.getLogger(__name__)


class DrinkService:
    """Comprehensive drink types and logging service."""
    
    def __init__(self):
        self.drink_types_file = Path(__file__).parent.parent / "data" / "drink_types.json"
        self.drink_logs_file = Path(__file__).parent.parent / "data" / "drink_logs.json"
        self._ensure_data_files()
        self._drink_types_cache = None
        self._drink_logs_cache = None
        self._next_drink_type_id = 1
        self._next_log_id = 1
    
    def _ensure_data_files(self):
        """Ensure drink data files exist."""
        data_dir = self.drink_types_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [self.drink_types_file, self.drink_logs_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_drink_types(self) -> List[Dict]:
        """Load drink types from file."""
        if self._drink_types_cache is None:
            try:
                with open(self.drink_types_file, 'r') as f:
                    self._drink_types_cache = json.load(f)
                    
                # Update next ID
                if self._drink_types_cache:
                    self._next_drink_type_id = max(dt['id'] for dt in self._drink_types_cache) + 1
            except Exception as e:
                logger.error(f"Error loading drink types: {e}")
                self._drink_types_cache = []
        return self._drink_types_cache
    
    async def _save_drink_types(self, drink_types: List[Dict]):
        """Save drink types to file."""
        try:
            with open(self.drink_types_file, 'w') as f:
                json.dump(drink_types, f, indent=2, default=str)
            self._drink_types_cache = drink_types
        except Exception as e:
            logger.error(f"Error saving drink types: {e}")
            raise
    
    async def _load_drink_logs(self) -> List[Dict]:
        """Load drink logs from file."""
        if self._drink_logs_cache is None:
            try:
                with open(self.drink_logs_file, 'r') as f:
                    self._drink_logs_cache = json.load(f)
                    
                # Update next ID
                if self._drink_logs_cache:
                    self._next_log_id = max(log['id'] for log in self._drink_logs_cache) + 1
            except Exception as e:
                logger.error(f"Error loading drink logs: {e}")
                self._drink_logs_cache = []
        return self._drink_logs_cache
    
    async def _save_drink_logs(self, drink_logs: List[Dict]):
        """Save drink logs to file."""
        try:
            with open(self.drink_logs_file, 'w') as f:
                json.dump(drink_logs, f, indent=2, default=str)
            self._drink_logs_cache = drink_logs
        except Exception as e:
            logger.error(f"Error saving drink logs: {e}")
            raise
    
    # Drink Types Management
    
    async def create_drink_type(self, drink_type_data: DrinkTypeCreate) -> DrinkType:
        """Create a new drink type."""
        try:
            drink_types = await self._load_drink_types()
            
            # Check if drink type with same name exists
            existing = next((dt for dt in drink_types if dt['name'].lower() == drink_type_data.name.lower()), None)
            if existing:
                raise ValueError(f"Drink type '{drink_type_data.name}' already exists")
            
            # Create new drink type
            drink_type_dict = {
                "id": self._next_drink_type_id,
                **drink_type_data.dict(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Set hydration effect based on multiplier
            drink_type_dict["hydration_effect"] = self._get_hydration_effect(drink_type_data.hydration_multiplier)
            
            drink_types.append(drink_type_dict)
            await self._save_drink_types(drink_types)
            
            self._next_drink_type_id += 1
            
            logger.info(f"Created drink type: {drink_type_data.name}")
            return DrinkType(**drink_type_dict)
            
        except Exception as e:
            logger.error(f"Error creating drink type: {e}")
            raise
    
    def _get_hydration_effect(self, multiplier: float) -> HydrationEffect:
        """Determine hydration effect based on multiplier."""
        if multiplier >= 1.2:
            return HydrationEffect.HIGHLY_HYDRATING
        elif multiplier >= 1.0:
            return HydrationEffect.HYDRATING
        elif multiplier >= 0.8:
            return HydrationEffect.NEUTRAL
        elif multiplier >= 0.6:
            return HydrationEffect.MILDLY_DEHYDRATING
        else:
            return HydrationEffect.DEHYDRATING
    
    async def get_drink_type(self, drink_type_id: int) -> Optional[DrinkType]:
        """Get a specific drink type by ID."""
        try:
            drink_types = await self._load_drink_types()
            drink_type_dict = next((dt for dt in drink_types if dt['id'] == drink_type_id), None)
            
            if not drink_type_dict:
                return None
            
            return DrinkType(**drink_type_dict)
            
        except Exception as e:
            logger.error(f"Error getting drink type: {e}")
            return None
    
    async def get_all_drink_types(
        self,
        category: Optional[DrinkCategory] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[DrinkType]:
        """Get all drink types with optional filtering."""
        try:
            drink_types = await self._load_drink_types()
            
            # Apply filters
            if active_only:
                drink_types = [dt for dt in drink_types if dt.get('is_active', True)]
            
            if category:
                drink_types = [dt for dt in drink_types if dt['category'] == category.value]
            
            # Sort by name
            drink_types.sort(key=lambda x: x['name'])
            
            # Apply pagination
            drink_types = drink_types[skip:skip + limit]
            
            return [DrinkType(**dt) for dt in drink_types]
            
        except Exception as e:
            logger.error(f"Error getting drink types: {e}")
            return []
    
    async def update_drink_type(
        self,
        drink_type_id: int,
        update_data: DrinkTypeUpdate
    ) -> Optional[DrinkType]:
        """Update a drink type."""
        try:
            drink_types = await self._load_drink_types()
            
            # Find drink type
            drink_type_index = next((i for i, dt in enumerate(drink_types) if dt['id'] == drink_type_id), None)
            if drink_type_index is None:
                return None
            
            # Update fields
            drink_type_dict = drink_types[drink_type_index]
            update_dict = update_data.dict(exclude_unset=True)
            
            drink_type_dict.update(update_dict)
            drink_type_dict['updated_at'] = datetime.utcnow().isoformat()
            
            # Update hydration effect if multiplier changed
            if 'hydration_multiplier' in update_dict:
                drink_type_dict['hydration_effect'] = self._get_hydration_effect(
                    update_dict['hydration_multiplier']
                ).value
            
            drink_types[drink_type_index] = drink_type_dict
            await self._save_drink_types(drink_types)
            
            logger.info(f"Updated drink type {drink_type_id}")
            return DrinkType(**drink_type_dict)
            
        except Exception as e:
            logger.error(f"Error updating drink type: {e}")
            return None
    
    async def delete_drink_type(self, drink_type_id: int) -> bool:
        """Delete a drink type (soft delete by setting inactive)."""
        try:
            update_data = DrinkTypeUpdate(is_active=False)
            result = await self.update_drink_type(drink_type_id, update_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error deleting drink type: {e}")
            return False
    
    # Drink Logging
    
    async def log_drink(self, user_id: int, log_data: DrinkLogCreate) -> DrinkLog:
        """Log a drink consumption."""
        try:
            # Verify drink type exists
            drink_type = await self.get_drink_type(log_data.drink_type_id)
            if not drink_type:
                raise ValueError(f"Drink type {log_data.drink_type_id} not found")
            
            drink_logs = await self._load_drink_logs()
            
            # Calculate contributions
            hydration_contribution = log_data.volume_ml * drink_type.hydration_multiplier
            
            # Use actual caffeine if provided, otherwise calculate from drink type
            caffeine_mg = log_data.actual_caffeine_mg
            if caffeine_mg is None:
                caffeine_mg = (log_data.volume_ml / 100) * drink_type.caffeine_mg_per_100ml
            
            # Create log entry
            log_dict = {
                "id": self._next_log_id,
                "user_id": user_id,
                **log_data.dict(),
                "consumed_at": datetime.utcnow().isoformat(),
                "hydration_contribution": hydration_contribution,
                "caffeine_contribution": caffeine_mg
            }
            
            drink_logs.append(log_dict)
            await self._save_drink_logs(drink_logs)
            
            self._next_log_id += 1
            
            logger.info(f"Logged drink for user {user_id}: {drink_type.name} ({log_data.volume_ml}ml)")
            return DrinkLog(**log_dict)
            
        except Exception as e:
            logger.error(f"Error logging drink: {e}")
            raise
    
    async def get_user_drink_logs(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[DrinkCategory] = None,
        limit: int = 100
    ) -> List[DrinkLog]:
        """Get drink logs for a user."""
        try:
            drink_logs = await self._load_drink_logs()
            drink_types = await self._load_drink_types()
            
            # Create drink type lookup
            drink_type_map = {dt['id']: dt for dt in drink_types}
            
            # Filter by user
            user_logs = [log for log in drink_logs if log['user_id'] == user_id]
            
            # Apply date filters
            if start_date or end_date:
                filtered_logs = []
                for log in user_logs:
                    log_date = datetime.fromisoformat(log['consumed_at']).date()
                    if start_date and log_date < start_date:
                        continue
                    if end_date and log_date > end_date:
                        continue
                    filtered_logs.append(log)
                user_logs = filtered_logs
            
            # Apply category filter
            if category:
                user_logs = [
                    log for log in user_logs
                    if drink_type_map.get(log['drink_type_id'], {}).get('category') == category.value
                ]
            
            # Sort by consumption time (most recent first)
            user_logs.sort(key=lambda x: x['consumed_at'], reverse=True)
            
            # Apply limit
            user_logs = user_logs[:limit]
            
            return [DrinkLog(**log) for log in user_logs]
            
        except Exception as e:
            logger.error(f"Error getting user drink logs: {e}")
            return []
    
    async def update_drink_log(
        self,
        log_id: int,
        user_id: int,
        update_data: DrinkLogUpdate
    ) -> Optional[DrinkLog]:
        """Update a drink log entry."""
        try:
            drink_logs = await self._load_drink_logs()
            
            # Find log entry
            log_index = next((
                i for i, log in enumerate(drink_logs)
                if log['id'] == log_id and log['user_id'] == user_id
            ), None)
            
            if log_index is None:
                return None
            
            # Update fields
            log_dict = drink_logs[log_index]
            update_dict = update_data.dict(exclude_unset=True)
            log_dict.update(update_dict)
            
            # Recalculate hydration contribution if volume changed
            if 'volume_ml' in update_dict:
                drink_type = await self.get_drink_type(log_dict['drink_type_id'])
                if drink_type:
                    log_dict['hydration_contribution'] = update_dict['volume_ml'] * drink_type.hydration_multiplier
            
            drink_logs[log_index] = log_dict
            await self._save_drink_logs(drink_logs)
            
            logger.info(f"Updated drink log {log_id} for user {user_id}")
            return DrinkLog(**log_dict)
            
        except Exception as e:
            logger.error(f"Error updating drink log: {e}")
            return None
    
    async def delete_drink_log(self, log_id: int, user_id: int) -> bool:
        """Delete a drink log entry."""
        try:
            drink_logs = await self._load_drink_logs()
            
            # Find and remove log entry
            original_count = len(drink_logs)
            drink_logs = [
                log for log in drink_logs
                if not (log['id'] == log_id and log['user_id'] == user_id)
            ]
            
            if len(drink_logs) == original_count:
                return False  # Log not found
            
            await self._save_drink_logs(drink_logs)
            
            logger.info(f"Deleted drink log {log_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting drink log: {e}")
            return False
    
    # Analytics and Summaries
    
    async def get_daily_drink_summary(self, user_id: int, target_date: date) -> DrinkSummary:
        """Get daily drink consumption summary for a user."""
        try:
            # Get logs for the specific date
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            drink_logs = await self._load_drink_logs()
            drink_types = await self._load_drink_types()
            
            # Create drink type lookup
            drink_type_map = {dt['id']: dt for dt in drink_types}
            
            # Filter logs for user and date
            day_logs = []
            for log in drink_logs:
                if log['user_id'] != user_id:
                    continue
                log_datetime = datetime.fromisoformat(log['consumed_at'])
                if start_datetime <= log_datetime <= end_datetime:
                    day_logs.append(log)
            
            # Calculate totals
            total_volume = sum(log['volume_ml'] for log in day_logs)
            total_hydration = sum(log.get('hydration_contribution', 0) for log in day_logs)
            total_caffeine = sum(log.get('caffeine_contribution', 0) for log in day_logs)
            
            # Calculate calories
            total_calories = 0
            for log in day_logs:
                drink_type = drink_type_map.get(log['drink_type_id'])
                if drink_type:
                    calories = (log['volume_ml'] / 100) * drink_type.get('calories_per_100ml', 0)
                    total_calories += log.get('actual_calories', calories)
            
            # Group by category
            consumption_by_category = defaultdict(float)
            caffeine_by_category = defaultdict(float)
            
            for log in day_logs:
                drink_type = drink_type_map.get(log['drink_type_id'])
                if drink_type:
                    category = drink_type['category']
                    consumption_by_category[category] += log['volume_ml']
                    caffeine_by_category[category] += log.get('caffeine_contribution', 0)
            
            # Get user's hydration goal
            user_profile = await user_service.get_user_profile(user_id)
            hydration_goal = user_profile.daily_goal_ml if user_profile else 2000
            
            # Check goals
            hydration_goal_met = total_hydration >= hydration_goal
            caffeine_within_limits = total_caffeine <= 400  # 400mg daily limit
            
            # Generate recommendations
            recommendations = []
            if not hydration_goal_met:
                remaining = hydration_goal - total_hydration
                recommendations.append(f"Drink {remaining:.0f}ml more water to meet your hydration goal")
            
            if total_caffeine > 300:
                recommendations.append("Consider reducing caffeine intake")
            
            if total_calories > 500:
                recommendations.append("Consider lower-calorie drink options")
            
            return DrinkSummary(
                user_id=user_id,
                date=datetime.combine(target_date, datetime.min.time()),
                total_volume_ml=total_volume,
                total_hydration_contribution=total_hydration,
                total_caffeine_mg=total_caffeine,
                total_calories=total_calories,
                consumption_by_category=dict(consumption_by_category),
                caffeine_by_category=dict(caffeine_by_category),
                hydration_goal_met=hydration_goal_met,
                caffeine_within_limits=caffeine_within_limits,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error getting daily drink summary: {e}")
            raise
    
    async def get_drink_recommendations(self, user_id: int) -> List[DrinkRecommendation]:
        """Get personalized drink recommendations for a user."""
        try:
            # Get recent drink logs to understand preferences
            recent_logs = await self.get_user_drink_logs(
                user_id,
                start_date=date.today() - timedelta(days=7),
                end_date=date.today()
            )
            
            # Get all drink types
            drink_types = await self.get_all_drink_types()
            
            # Analyze consumption patterns
            consumed_categories = set()
            total_caffeine_today = 0
            
            today_logs = [
                log for log in recent_logs
                if log.consumed_at.date() == date.today()
            ]
            
            for log in today_logs:
                drink_type = await self.get_drink_type(log.drink_type_id)
                if drink_type:
                    consumed_categories.add(drink_type.category)
                    total_caffeine_today += log.caffeine_contribution or 0
            
            recommendations = []
            
            # Recommend water if not enough hydration
            if DrinkCategory.WATER not in consumed_categories:
                water_types = [dt for dt in drink_types if dt.category == DrinkCategory.WATER]
                if water_types:
                    recommendations.append(DrinkRecommendation(
                        drink_type=water_types[0],
                        recommended_volume_ml=500,
                        reason="Increase pure water intake for better hydration",
                        best_time="throughout the day",
                        preparation_tips=["Drink at room temperature", "Add lemon for flavor"],
                        health_notes=["Essential for optimal hydration"]
                    ))
            
            # Recommend tea if high caffeine intake
            if total_caffeine_today > 200:
                tea_types = [dt for dt in drink_types if dt.category == DrinkCategory.TEA and dt.caffeine_mg_per_100ml < 50]
                if tea_types:
                    recommendations.append(DrinkRecommendation(
                        drink_type=tea_types[0],
                        recommended_volume_ml=250,
                        reason="Lower caffeine alternative to coffee",
                        best_time="afternoon",
                        preparation_tips=["Steep for 3-5 minutes", "Add honey instead of sugar"],
                        health_notes=["Contains antioxidants", "Lower caffeine than coffee"]
                    ))
            
            # Add more recommendations based on time of day, health goals, etc.
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            logger.error(f"Error getting drink recommendations: {e}")
            return []
    
    async def get_drink_stats(self) -> DrinkStats:
        """Get overall drink consumption statistics."""
        try:
            drink_types = await self._load_drink_types()
            drink_logs = await self._load_drink_logs()
            
            # Calculate statistics
            total_drink_types = len([dt for dt in drink_types if dt.get('is_active', True)])
            
            # Most popular category
            category_counts = Counter()
            total_volume = 0
            total_caffeine = 0
            
            for log in drink_logs:
                drink_type_id = log['drink_type_id']
                drink_type = next((dt for dt in drink_types if dt['id'] == drink_type_id), None)
                if drink_type:
                    category_counts[drink_type['category']] += 1
                    total_volume += log['volume_ml']
                    total_caffeine += log.get('caffeine_contribution', 0)
            
            most_popular_category = DrinkCategory.WATER
            if category_counts:
                most_popular_category = DrinkCategory(category_counts.most_common(1)[0][0])
            
            # Calculate averages (simplified)
            unique_users = len(set(log['user_id'] for log in drink_logs))
            avg_daily_volume = total_volume / max(unique_users, 1)
            avg_caffeine = total_caffeine / max(unique_users, 1)
            
            # Hydration compliance (simplified)
            hydration_compliance = 0.75  # Placeholder
            
            return DrinkStats(
                total_drink_types=total_drink_types,
                most_popular_category=most_popular_category,
                average_daily_volume=avg_daily_volume,
                average_caffeine_intake=avg_caffeine,
                hydration_compliance_rate=hydration_compliance
            )
            
        except Exception as e:
            logger.error(f"Error getting drink stats: {e}")
            raise
    
    async def initialize_default_drink_types(self):
        """Initialize the system with default drink types."""
        try:
            drink_types = await self._load_drink_types()
            if drink_types:
                return  # Already initialized
            
            default_drinks = [
                # Water
                DrinkTypeCreate(
                    name="Pure Water",
                    category=DrinkCategory.WATER,
                    hydration_multiplier=1.0,
                    description="Pure, clean water - the best choice for hydration"
                ),
                DrinkTypeCreate(
                    name="Sparkling Water",
                    category=DrinkCategory.WATER,
                    hydration_multiplier=1.0,
                    description="Carbonated water - hydrating with a refreshing fizz"
                ),
                
                # Tea
                DrinkTypeCreate(
                    name="Green Tea",
                    category=DrinkCategory.TEA,
                    hydration_multiplier=0.9,
                    caffeine_mg_per_100ml=25,
                    antioxidants=True,
                    health_benefits=["Rich in antioxidants", "May boost metabolism"],
                    best_times_to_consume=["morning", "afternoon"],
                    common_varieties=["Sencha", "Matcha", "Jasmine"],
                    description="Light, refreshing tea with moderate caffeine and high antioxidants"
                ),
                DrinkTypeCreate(
                    name="Black Tea",
                    category=DrinkCategory.TEA,
                    hydration_multiplier=0.9,
                    caffeine_mg_per_100ml=40,
                    antioxidants=True,
                    health_benefits=["Heart health", "Mental alertness"],
                    best_times_to_consume=["morning", "afternoon"],
                    avoid_times=["evening"],
                    common_varieties=["Earl Grey", "English Breakfast", "Assam"],
                    description="Bold, full-bodied tea with moderate to high caffeine"
                ),
                
                # Coffee
                DrinkTypeCreate(
                    name="Coffee",
                    category=DrinkCategory.COFFEE,
                    hydration_multiplier=0.8,
                    caffeine_mg_per_100ml=95,
                    antioxidants=True,
                    health_benefits=["Increased alertness", "Antioxidants"],
                    health_warnings=["High caffeine content", "May cause jitters"],
                    recommended_daily_limit_ml=400,
                    best_times_to_consume=["morning"],
                    avoid_times=["evening", "night"],
                    preparation_methods=["Drip", "Espresso", "French Press"],
                    description="Popular caffeinated beverage with high alertness benefits"
                ),
                
                # Juice
                DrinkTypeCreate(
                    name="Orange Juice",
                    category=DrinkCategory.JUICE,
                    hydration_multiplier=0.9,
                    calories_per_100ml=45,
                    sugar_g_per_100ml=10,
                    vitamins=["Vitamin C", "Folate"],
                    health_benefits=["Vitamin C", "Natural sugars for energy"],
                    health_warnings=["High in natural sugars"],
                    recommended_daily_limit_ml=250,
                    best_times_to_consume=["morning"],
                    description="Citrus juice rich in vitamin C and natural sugars"
                ),
                
                # Sports Drink
                DrinkTypeCreate(
                    name="Sports Drink",
                    category=DrinkCategory.SPORTS_DRINK,
                    hydration_multiplier=1.1,
                    calories_per_100ml=25,
                    sugar_g_per_100ml=6,
                    sodium_mg_per_100ml=110,
                    electrolytes=True,
                    minerals=["Sodium", "Potassium"],
                    health_benefits=["Electrolyte replacement", "Quick hydration"],
                    best_times_to_consume=["during exercise", "after exercise"],
                    description="Electrolyte-enhanced drink for active individuals"
                )
            ]
            
            for drink_data in default_drinks:
                await self.create_drink_type(drink_data)
            
            logger.info(f"Initialized {len(default_drinks)} default drink types")
            
        except Exception as e:
            logger.error(f"Error initializing default drink types: {e}")


# Global service instance
drink_service = DrinkService() 