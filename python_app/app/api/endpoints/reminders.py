from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, get_current_active_user
from app.services.reminder_service import ReminderService
from app.models.reminder import Reminder, ReminderCreate, ReminderUpdate
from app.models.user import User

router = APIRouter()
reminder_service = ReminderService()

@router.post("/", response_model=Reminder, status_code=201)
def create_reminder(
    reminder_data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new reminder for the current user."""
    return reminder_service.create_reminder(db=db, reminder_data=reminder_data, user_id=current_user.id)

@router.get("/", response_model=List[Reminder])
def get_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all reminders for the current user."""
    return reminder_service.get_reminders_by_user(db=db, user_id=current_user.id)

@router.get("/{reminder_id}", response_model=Reminder)
def get_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific reminder by ID."""
    reminder = reminder_service.get_reminder(db=db, reminder_id=reminder_id, user_id=current_user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder

@router.put("/{reminder_id}", response_model=Reminder)
def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing reminder."""
    updated_reminder = reminder_service.update_reminder(db=db, reminder_id=reminder_id, reminder_data=reminder_data, user_id=current_user.id)
    if not updated_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return updated_reminder

@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a reminder."""
    success = reminder_service.delete_reminder(db=db, reminder_id=reminder_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return 