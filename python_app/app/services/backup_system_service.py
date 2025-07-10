import asyncio
from datetime import datetime
import os
import tarfile
import shutil
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.backup_system import BackupJob, RestoreJob, JobStatus, BackupType, StorageLocation
from app.schemas.backup_system import BackupJobCreate, RestoreJobCreate

# In a real app, these would be in a config file
BACKUP_BASE_DIR = "./backups"
DB_CONNECTION_STRING = "sqlite+aiosqlite:///./test.db" # Example

class BackupSystemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_backup_job(self, job_data: BackupJobCreate, user_id: Optional[int] = None) -> BackupJob:
        new_job = BackupJob(
            initiated_by_user_id=user_id,
            **job_data.dict()
        )
        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)
        return new_job

    async def run_backup_job(self, job_id: int):
        job = await self.get_backup_job(job_id)
        if not job or job.status != JobStatus.PENDING:
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        await self.db.commit()

        try:
            archive_path = await self._execute_backup(job)
            job.archive_path = archive_path
            job.status = JobStatus.COMPLETED
            job.logs = f"Backup completed successfully. Archive at {archive_path}"
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.logs = f"Backup failed. Reason: {e}"
        finally:
            job.completed_at = datetime.utcnow()
            await self.db.commit()
            
    async def get_backup_job(self, job_id: int) -> Optional[BackupJob]:
        result = await self.db.execute(select(BackupJob).filter(BackupJob.id == job_id))
        return result.scalars().first()
    
    async def list_backup_jobs(self, skip: int = 0, limit: int = 100) -> List[BackupJob]:
        result = await self.db.execute(select(BackupJob).order_by(BackupJob.id.desc()).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_restore_job(self, job_data: RestoreJobCreate, user_id: int) -> RestoreJob:
        # Verify that the backup job exists
        backup_job = await self.get_backup_job(job_data.backup_job_id)
        if not backup_job or backup_job.status != JobStatus.COMPLETED:
            raise ValueError("Valid backup job not found or backup is not complete.")

        new_job = RestoreJob(
            initiated_by_user_id=user_id,
            **job_data.dict()
        )
        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)
        return new_job
    
    async def run_restore_job(self, job_id: int):
        job = await self.get_restore_job(job_id)
        if not job or job.status != JobStatus.PENDING:
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        await self.db.commit()
        
        try:
            await self._execute_restore(job)
            job.status = JobStatus.COMPLETED
            job.logs = "Restore completed successfully."
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.logs = f"Restore failed. Reason: {e}"
        finally:
            job.completed_at = datetime.utcnow()
            await self.db.commit()

    async def get_restore_job(self, job_id: int) -> Optional[RestoreJob]:
        result = await self.db.execute(select(RestoreJob).filter(RestoreJob.id == job_id))
        return result.scalars().first()

    # --- Private Execution Logic ---

    async def _execute_backup(self, job: BackupJob) -> str:
        """
        Simulates the backup process. In a real application, this would involve
        calling database-specific dump tools and archiving files.
        """
        await asyncio.sleep(5) # Simulate work

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        archive_name = f"backup_{job.backup_type.value}_{timestamp}.tar.gz"
        
        # Create a temporary directory for the backup
        temp_backup_dir = os.path.join(BACKUP_BASE_DIR, f"temp_{job.id}")
        os.makedirs(temp_backup_dir, exist_ok=True)
        
        # Simulate backing up the database (e.g., using pg_dump)
        if job.backup_type in [BackupType.FULL, BackupType.DATABASE_ONLY]:
            with open(os.path.join(temp_backup_dir, "database.sql"), "w") as f:
                f.write("-- Simulated SQL Dump --\n")
                f.write(f"-- Backup from {datetime.utcnow()} --\n")

        # Simulate backing up files (e.g., user uploads)
        if job.backup_type in [BackupType.FULL, BackupType.FILES_ONLY]:
            files_dir = os.path.join(temp_backup_dir, "files")
            os.makedirs(files_dir, exist_ok=True)
            with open(os.path.join(files_dir, "example_file.txt"), "w") as f:
                f.write("This is a simulated user file.")

        # Create a tar.gz archive
        archive_path = os.path.join(BACKUP_BASE_DIR, archive_name)
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(temp_backup_dir, arcname=os.path.basename(temp_backup_dir))

        # Clean up temp directory
        shutil.rmtree(temp_backup_dir)

        # In a real scenario, this would upload to the chosen storage location
        if job.storage_location != StorageLocation.LOCAL:
            # e.g., s3_client.upload_file(archive_path, bucket, archive_name)
            print(f"Simulating upload of {archive_path} to {job.storage_location.value}")
        
        return archive_path

    async def _execute_restore(self, job: RestoreJob):
        """
        Simulates the restore process. This is a highly destructive operation
        and would require careful implementation in a real app.
        """
        await asyncio.sleep(5)
        
        backup_job = await self.get_backup_job(job.backup_job_id)
        if not backup_job or not backup_job.archive_path or not os.path.exists(backup_job.archive_path):
            raise FileNotFoundError("Backup archive not found.")

        # Here you would:
        # 1. Put the application in maintenance mode.
        # 2. Stop the application server.
        # 3. Clear the existing database/files.
        # 4. Restore the database from the SQL dump.
        # 5. Extract files to their proper locations.
        # 6. Restart the application server.
        # 7. Take the application out of maintenance mode.
        print(f"Simulating restore from {backup_job.archive_path}")
        print("This would be a very complex and destructive operation.")
        pass

    async def run_scheduled_backups(self):
        """
        A function to be called by a scheduler (e.g., cron) to run automated backups
        based on a predefined policy.
        """
        print("Checking for scheduled backups to run...")
        # Policy: Run a full backup every Sunday at 2 AM.
        now = datetime.utcnow()
        if now.weekday() == 6 and now.hour == 2:
            job_data = BackupJobCreate(
                backup_type=BackupType.FULL,
                storage_location=StorageLocation.S3,
                metadata={"reason": "Weekly scheduled backup"}
            )
            job = await self.create_backup_job(job_data)
            await self.run_backup_job(job.id)
            print(f"Started scheduled weekly backup job {job.id}") 