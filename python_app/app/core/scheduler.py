from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.notification_service import NotificationService
from app.models.notification import NotificationCreate, NotificationType
from app.db.models import Reminder
import logging

logger = logging.getLogger(__name__)

class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.notification_service = NotificationService()

    async def _send_reminder(self, user_id: int, message: str):
        """The job function that sends a reminder notification."""
        logger.info(f"Executing reminder job for user {user_id}")
        try:
            notification = NotificationCreate(
                user_id=user_id,
                notification_type=NotificationType.GOAL_REMINDER,
                title="Hydration Reminder",
                message=message,
                data={"source": "scheduler"}
            )
            await self.notification_service.send_notification(notification)
            logger.info(f"Successfully sent reminder to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user_id}: {e}")

    def add_job(self, reminder: Reminder):
        """Adds a new reminder job to the scheduler."""
        if reminder.is_active:
            try:
                self.scheduler.add_job(
                    self._send_reminder,
                    trigger=CronTrigger.from_crontab(reminder.cron_schedule),
                    id=str(reminder.id),
                    args=[reminder.user_id, reminder.message],
                    replace_existing=True
                )
                logger.info(f"Scheduled reminder {reminder.id} for user {reminder.user_id} with schedule '{reminder.cron_schedule}'")
            except Exception as e:
                logger.error(f"Failed to add job for reminder {reminder.id}: {e}")

    def remove_job(self, reminder_id: int):
        """Removes a job from the scheduler."""
        job_id = str(reminder_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed reminder job {job_id} from scheduler.")

    def update_job(self, reminder: Reminder):
        """Updates an existing job in the scheduler."""
        self.remove_job(reminder.id)
        self.add_job(reminder)
    
    def start(self):
        """Starts the scheduler and loads all active reminders from the DB."""
        logger.info("Starting scheduler and loading jobs...")
        db: Session = SessionLocal()
        try:
            reminders = db.query(Reminder).filter(Reminder.is_active == True).all()
            for reminder in reminders:
                self.add_job(reminder)
        finally:
            db.close()
        
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")

    def shutdown(self):
        """Shuts down the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down.")

# Global scheduler instance
scheduler_manager = SchedulerManager() 