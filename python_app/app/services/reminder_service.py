from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Reminder
from app.models.reminder import ReminderCreate, ReminderUpdate
from app.core.scheduler import scheduler_manager

class ReminderService:
    def get_reminder(self, db: Session, reminder_id: int, user_id: int) -> Optional[Reminder]:
        return db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user_id).first()

    def get_reminders_by_user(self, db: Session, user_id: int) -> List[Reminder]:
        return db.query(Reminder).filter(Reminder.user_id == user_id).all()

    def create_reminder(self, db: Session, reminder_data: ReminderCreate, user_id: int) -> Reminder:
        db_reminder = Reminder(**reminder_data.model_dump(), user_id=user_id)
        db.add(db_reminder)
        db.commit()
        db.refresh(db_reminder)
        scheduler_manager.add_job(db_reminder)
        return db_reminder

    def update_reminder(self, db: Session, reminder_id: int, reminder_data: ReminderUpdate, user_id: int) -> Optional[Reminder]:
        db_reminder = self.get_reminder(db, reminder_id, user_id)
        if not db_reminder:
            return None
        update_data = reminder_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_reminder, key, value)
        db.commit()
        db.refresh(db_reminder)
        scheduler_manager.update_job(db_reminder)
        return db_reminder

    def delete_reminder(self, db: Session, reminder_id: int, user_id: int) -> bool:
        db_reminder = self.get_reminder(db, reminder_id, user_id)
        if db_reminder:
            scheduler_manager.remove_job(reminder_id)
            db.delete(db_reminder)
            db.commit()
            return True
        return False 