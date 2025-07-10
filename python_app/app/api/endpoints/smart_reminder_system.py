from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.smart_reminder_system import ModelType
from app.schemas.smart_reminder_system import (
    SmartReminder,
    SmartReminderCreate,
    SmartReminderUpdate,
    ReminderInteraction,
    ReminderInteractionCreate,
    MLModel,
    MLModelCreate,
    UserBehaviorPattern,
    UserBehaviorPatternCreate,
    ContextData,
    ContextDataCreate
)
from app.services.smart_reminder_system_service import SmartReminderSystemService

router = APIRouter()

@router.post("/", response_model=SmartReminder, status_code=201)
async def create_smart_reminder(
    reminder_in: SmartReminderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new smart reminder for the current user.
    """
    reminder_in.user_id = current_user.id
    service = SmartReminderSystemService(db)
    return await service.create_smart_reminder(reminder_data=reminder_in)

@router.get("/", response_model=List[SmartReminder])
async def get_user_smart_reminders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all smart reminders for the current user.
    """
    service = SmartReminderSystemService(db)
    return await service.get_smart_reminders_for_user(user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{reminder_id}", response_model=SmartReminder)
async def get_smart_reminder(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific smart reminder by its ID.
    """
    service = SmartReminderSystemService(db)
    reminder = await service.get_smart_reminder(reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder

@router.put("/{reminder_id}", response_model=SmartReminder)
async def update_smart_reminder(
    reminder_id: int,
    reminder_in: SmartReminderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing smart reminder.
    """
    service = SmartReminderSystemService(db)
    reminder = await service.get_smart_reminder(reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return await service.update_smart_reminder(reminder_id, reminder_data=reminder_in)

@router.delete("/{reminder_id}", status_code=204)
async def delete_smart_reminder(
    reminder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a smart reminder.
    """
    service = SmartReminderSystemService(db)
    reminder = await service.get_smart_reminder(reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    deleted = await service.delete_smart_reminder(reminder_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return

@router.post("/interactions/", response_model=ReminderInteraction, status_code=201)
async def record_interaction(
    interaction_in: ReminderInteractionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record an interaction with a reminder instance.
    """
    # TODO: Add validation to ensure the user owns the reminder instance
    service = SmartReminderSystemService(db)
    return await service.record_reminder_interaction(interaction_data=interaction_in)

@router.post("/schedule", status_code=202)
async def schedule_reminders_for_user(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger the smart scheduling process for the current user.
    This runs as a background task.
    """
    service = SmartReminderSystemService(db)
    background_tasks.add_task(service.schedule_reminders_for_user, user_id=current_user.id)
    return {"message": "Smart reminder scheduling initiated for user."}

# --- Admin / System Endpoints ---

@router.post("/trigger-pending", status_code=200, tags=["admin"])
async def trigger_all_pending_reminders(
    db: AsyncSession = Depends(get_db)
    # TODO: Add admin user dependency
):
    """
    System-level endpoint to trigger all pending reminders.
    Should be protected and called by a scheduler.
    """
    service = SmartReminderSystemService(db)
    count = await service.trigger_pending_reminders()
    return {"message": f"Triggered {count} pending reminders."}

@router.post("/ml-models/", response_model=MLModel, status_code=201, tags=["admin"])
async def create_ml_model(
    model_in: MLModelCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new ML model entry. (Admin)
    """
    service = SmartReminderSystemService(db)
    return await service.create_ml_model(model_data=model_in)

@router.post("/log-behavior/", response_model=UserBehaviorPattern, status_code=201, tags=["system"])
async def log_user_behavior(
    pattern_in: UserBehaviorPatternCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log a user behavior pattern.
    """
    pattern_in.user_id = current_user.id
    service = SmartReminderSystemService(db)
    return await service.create_user_behavior_pattern(pattern_data=pattern_in)

@router.post("/log-context/", response_model=ContextData, status_code=201, tags=["system"])
async def log_user_context(
    context_in: ContextDataCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log contextual data for a user.
    """
    context_in.user_id = current_user.id
    service = SmartReminderSystemService(db)
    return await service.log_context_data(context_data=context_in) 