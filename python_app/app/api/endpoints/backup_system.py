from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_current_user # Assuming an admin check would be added here
from app.models.user import User
from app.schemas.backup_system import (
    BackupJobCreate,
    BackupJobSchema,
    RestoreJobCreate,
    RestoreJobSchema
)
from app.services.backup_system_service import BackupSystemService

router = APIRouter()

@router.post("/backups", response_model=BackupJobSchema, status_code=202)
async def create_and_run_backup_job(
    backup_job_in: BackupJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    Create a new backup job. The job will be executed in the background.
    """
    service = BackupSystemService(db)
    new_job = await service.create_backup_job(job_data=backup_job_in, user_id=current_user.id)
    
    background_tasks.add_task(service.run_backup_job, job_id=new_job.id)
    
    return new_job

@router.get("/backups", response_model=List[BackupJobSchema])
async def list_backup_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    List all backup jobs in the system.
    """
    service = BackupSystemService(db)
    return await service.list_backup_jobs(skip=skip, limit=limit)

@router.get("/backups/{job_id}", response_model=BackupJobSchema)
async def get_backup_job_details(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    Get the details of a specific backup job.
    """
    service = BackupSystemService(db)
    job = await service.get_backup_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return job

@router.post("/restores", response_model=RestoreJobSchema, status_code=202)
async def create_and_run_restore_job(
    restore_job_in: RestoreJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    Create a new restore job from a completed backup. 
    The job will be executed in the background.
    WARNING: This is a destructive operation.
    """
    service = BackupSystemService(db)
    try:
        new_job = await service.create_restore_job(job_data=restore_job_in, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    background_tasks.add_task(service.run_restore_job, job_id=new_job.id)
    
    return new_job

@router.get("/restores/{job_id}", response_model=RestoreJobSchema)
async def get_restore_job_details(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    Get the details of a specific restore job.
    """
    service = BackupSystemService(db)
    job = await service.get_restore_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Restore job not found")
    return job 