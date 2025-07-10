from datetime import datetime
import enum
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as EnumSQL,
    Text,
    JSON,
    Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()

# Enums for the security system
class EventType(str, enum.Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_PASSWORD_RESET_REQUEST = "user_password_reset_request"
    USER_ROLE_CHANGE = "user_role_change"
    
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"
    
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    BACKUP_STARTED = "backup_started"
    RESTORE_STARTED = "restore_started"

    SECURITY_SCAN = "security_scan"
    PERMISSION_DENIED = "permission_denied"
    FAILED_LOGIN_ATTEMPT = "failed_login_attempt"

class SeverityLevel(str, enum.Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ActionStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"

# --- SQLAlchemy Models ---

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_info = Column(String) # For system actions or unauthenticated users
    
    event_type = Column(EnumSQL(EventType), nullable=False)
    status = Column(EnumSQL(ActionStatus), nullable=False)
    
    ip_address = Column(String)
    user_agent = Column(String)
    
    details = Column(JSON) # e.g., {"target_user_id": 5, "role_changed_to": "admin"}
    
    user = relationship("User")

class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    event_type = Column(EnumSQL(EventType), nullable=False)
    severity = Column(EnumSQL(SeverityLevel), nullable=False)
    
    ip_address = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    description = Column(Text, nullable=False)
    metadata = Column(JSON)
    
    is_resolved = Column(Boolean, default=False)
    resolved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime)
    
    user = relationship("User", foreign_keys=[user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])


# --- Pydantic Schemas ---

class AuditLogBase(BaseModel):
    event_type: EventType
    status: ActionStatus
    user_id: Optional[int] = None
    actor_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogSchema(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class SecurityEventBase(BaseModel):
    event_type: EventType
    severity: SeverityLevel
    description: str
    ip_address: Optional[str] = None
    user_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class SecurityEventCreate(SecurityEventBase):
    pass

class SecurityEventSchema(SecurityEventBase):
    id: int
    timestamp: datetime
    is_resolved: bool
    resolved_by_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True 