from datetime import datetime
import enum
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as EnumSQL,
    Boolean,
    Text,
    JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()

# Enums for the backup system
class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

class BackupType(str, enum.Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    DATABASE_ONLY = "database_only"
    FILES_ONLY = "files_only"

class StorageLocation(str, enum.Enum):
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GOOGLE_CLOUD_STORAGE = "google_cloud_storage"

# --- SQLAlchemy Models ---

class BackupJob(Base):
    __tablename__ = "backup_jobs"
    id = Column(Integer, primary_key=True, index=True)
    initiated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(EnumSQL(JobStatus), default=JobStatus.PENDING, nullable=False)
    backup_type = Column(EnumSQL(BackupType), nullable=False)
    storage_location = Column(EnumSQL(StorageLocation), nullable=False)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    metadata = Column(JSON)  # e.g., {"tables_backed_up": ["users", "water_logs"], "file_count": 1024}
    logs = Column(Text) # To store detailed logs of the job execution
    error_message = Column(Text)
    
    archive_path = Column(String) # Path to the backup file, e.g., an S3 URI

    user = relationship("User")
    
class RestoreJob(Base):
    __tablename__ = "restore_jobs"
    id = Column(Integer, primary_key=True, index=True)
    initiated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    backup_job_id = Column(Integer, ForeignKey("backup_jobs.id"), nullable=False)
    
    status = Column(EnumSQL(JobStatus), default=JobStatus.PENDING, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    logs = Column(Text)
    error_message = Column(Text)
    
    user = relationship("User")
    backup_job = relationship("BackupJob")

# --- Pydantic Schemas ---

class BackupJobBase(BaseModel):
    backup_type: BackupType
    storage_location: StorageLocation
    metadata: Optional[Dict[str, Any]] = None

class BackupJobCreate(BackupJobBase):
    pass

class BackupJobSchema(BackupJobBase):
    id: int
    initiated_by_user_id: Optional[int]
    status: JobStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    archive_path: Optional[str]
    error_message: Optional[str]

    class Config:
        orm_mode = True

class RestoreJobBase(BaseModel):
    backup_job_id: int

class RestoreJobCreate(RestoreJobBase):
    pass

class RestoreJobSchema(RestoreJobBase):
    id: int
    initiated_by_user_id: int
    status: JobStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        orm_mode = True 