import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import random
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.smart_reminder_system import (
    SmartReminder,
    ReminderInstance,
    ReminderInteraction,
    MLModel,
    UserBehaviorPattern,
    ContextData,
    ReminderStatus,
    InteractionType,
    ModelType,
    ChannelType
)
from app.schemas.smart_reminder_system import (
    SmartReminderCreate,
    SmartReminderUpdate,
    ReminderInteractionCreate,
    MLModelCreate,
    UserBehaviorPatternCreate,
    ContextDataCreate
)

class SmartReminderSystemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_smart_reminder(self, reminder_data: SmartReminderCreate) -> SmartReminder:
        new_reminder = SmartReminder(**reminder_data.dict())
        self.db.add(new_reminder)
        await self.db.commit()
        await self.db.refresh(new_reminder)
        return new_reminder

    async def get_smart_reminder(self, reminder_id: int) -> Optional[SmartReminder]:
        result = await self.db.execute(
            select(SmartReminder).filter(SmartReminder.id == reminder_id)
            .options(selectinload(SmartReminder.instances).selectinload(ReminderInstance.interactions))
        )
        return result.scalars().first()

    async def get_smart_reminders_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[SmartReminder]:
        result = await self.db.execute(
            select(SmartReminder)
            .filter(SmartReminder.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_smart_reminder(self, reminder_id: int, reminder_data: SmartReminderUpdate) -> Optional[SmartReminder]:
        reminder = await self.get_smart_reminder(reminder_id)
        if not reminder:
            return None
        
        update_data = reminder_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reminder, key, value)
            
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder

    async def delete_smart_reminder(self, reminder_id: int) -> bool:
        reminder = await self.get_smart_reminder(reminder_id)
        if not reminder:
            return False
        await self.db.delete(reminder)
        await self.db.commit()
        return True

    async def record_reminder_interaction(self, interaction_data: ReminderInteractionCreate) -> ReminderInteraction:
        new_interaction = ReminderInteraction(**interaction_data.dict())
        
        instance = await self.db.get(ReminderInstance, new_interaction.reminder_instance_id)
        if instance:
            if new_interaction.interaction_type == InteractionType.COMPLETED:
                instance.status = ReminderStatus.COMPLETED
            elif new_interaction.interaction_type == InteractionType.DISMISSED:
                instance.status = ReminderStatus.DISMISSED
            # Update reminder's adaptive properties based on interaction
            reminder = await self.get_smart_reminder(instance.reminder_id)
            if reminder:
                # Basic learning: adjust priority based on completion
                if new_interaction.interaction_type == InteractionType.COMPLETED:
                    reminder.priority = min(10, reminder.priority + 1)
                else:
                    reminder.priority = max(1, reminder.priority - 1)

        self.db.add(new_interaction)
        await self.db.commit()
        await self.db.refresh(new_interaction)
        return new_interaction

    async def schedule_reminders_for_user(self, user_id: int):
        """
        Main logic for scheduling reminders. This would be a complex function
        integrating ML predictions. For now, it uses a simplified logic.
        """
        reminders = await self.get_smart_reminders_for_user(user_id)
        ml_model = await self.get_active_ml_model(ModelType.SCHEDULING)
        
        for reminder in reminders:
            if not reminder.is_active:
                continue

            # In a real system, this would call ml_model.predict()
            predicted_time = self._predict_optimal_time(user_id, reminder, ml_model)
            
            # Check for conflicts
            if not await self._has_scheduling_conflict(user_id, predicted_time):
                instance = ReminderInstance(
                    reminder_id=reminder.id,
                    user_id=user_id,
                    scheduled_time=predicted_time,
                    status=ReminderStatus.SCHEDULED,
                    channel=random.choice(list(ChannelType)) # Or predict channel
                )
                self.db.add(instance)
        
        await self.db.commit()

    async def trigger_pending_reminders(self):
        """
        A function to be called periodically (e.g., by a cron job or scheduler)
        to send out scheduled reminders.
        """
        now = datetime.utcnow()
        result = await self.db.execute(
            select(ReminderInstance)
            .filter(ReminderInstance.status == ReminderStatus.SCHEDULED)
            .filter(ReminderInstance.scheduled_time <= now)
        )
        instances_to_send = result.scalars().all()

        for instance in instances_to_send:
            # Here you would integrate with a notification service (e.g., email, push)
            print(f"Sending reminder {instance.id} for user {instance.user_id} via {instance.channel}")
            instance.status = ReminderStatus.SENT
            await self.db.commit()
        
        return len(instances_to_send)
    
    # --- ML and Data Handling ---

    async def create_ml_model(self, model_data: MLModelCreate) -> MLModel:
        new_model = MLModel(**model_data.dict())
        self.db.add(new_model)
        await self.db.commit()
        await self.db.refresh(new_model)
        return new_model

    async def get_active_ml_model(self, model_type: ModelType) -> Optional[MLModel]:
        result = await self.db.execute(
            select(MLModel)
            .filter(MLModel.model_type == model_type, MLModel.is_active == True)
            .order_by(MLModel.version.desc())
        )
        return result.scalars().first()

    async def create_user_behavior_pattern(self, pattern_data: UserBehaviorPatternCreate) -> UserBehaviorPattern:
        new_pattern = UserBehaviorPattern(**pattern_data.dict())
        self.db.add(new_pattern)
        await self.db.commit()
        await self.db.refresh(new_pattern)
        return new_pattern

    async def log_context_data(self, context_data: ContextDataCreate) -> ContextData:
        new_context = ContextData(**context_data.dict())
        self.db.add(new_context)
        await self.db.commit()
        await self.db.refresh(new_context)
        return new_context

    # --- Private Helper Methods ---

    def _predict_optimal_time(self, user_id: int, reminder: SmartReminder, model: Optional[MLModel]) -> datetime:
        """
        Placeholder for ML-based prediction.
        Falls back to a simple logic if no model is available.
        """
        if model:
            # features = self._gather_features(user_id, reminder)
            # prediction = model.predict(features)
            # For now, simulate a prediction
            offset_minutes = random.randint(15, 120)
            return datetime.utcnow() + timedelta(minutes=offset_minutes)
        else:
            # Simple fallback logic
            if reminder.end_time:
                # Schedule sometime between now and the end time
                now = datetime.utcnow()
                if now < reminder.end_time:
                    time_diff_seconds = (reminder.end_time - now).total_seconds()
                    random_seconds = random.uniform(0, time_diff_seconds)
                    return now + timedelta(seconds=random_seconds)
            return datetime.utcnow() + timedelta(hours=random.uniform(1, 5))

    async def _has_scheduling_conflict(self, user_id: int, scheduled_time: datetime, buffer_minutes: int = 15) -> bool:
        """
        Checks if another reminder is scheduled too close to the given time.
        """
        time_buffer = timedelta(minutes=buffer_minutes)
        result = await self.db.execute(
            select(ReminderInstance.id)
            .filter(
                ReminderInstance.user_id == user_id,
                ReminderInstance.status == ReminderStatus.SCHEDULED,
                ReminderInstance.scheduled_time >= scheduled_time - time_buffer,
                ReminderInstance.scheduled_time <= scheduled_time + time_buffer
            )
        )
        return result.scalars().first() is not None

    async def get_user_behavior_patterns(self, user_id: int) -> List[UserBehaviorPattern]:
        result = await self.db.execute(
            select(UserBehaviorPattern)
            .filter(UserBehaviorPattern.user_id == user_id)
            .order_by(UserBehaviorPattern.timestamp.desc())
            .limit(100)
        )
        return result.scalars().all()

    async def get_user_context_data(self, user_id: int) -> List[ContextData]:
        result = await self.db.execute(
            select(ContextData)
            .filter(ContextData.user_id == user_id)
            .order_by(ContextData.timestamp.desc())
            .limit(100)
        )
        return result.scalars().all()

    async def retrain_model(self, model_type: ModelType):
        """
        Placeholder for a full-scale model retraining pipeline.
        """
        # 1. Gather all historical data (interactions, contexts)
        # 2. Preprocess and create a new dataset
        # 3. Train a new model version
        # 4. Evaluate the model
        # 5. If successful, save the new model and mark it as active
        print(f"Initiating retraining for {model_type.value} models.")
        await asyncio.sleep(10) # Simulate a long-running task
        print("Retraining complete.") 