from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.security_system import (
    AuditLog,
    SecurityEvent,
    EventType,
    SeverityLevel,
    ActionStatus
)
from app.schemas.security_system import (
    AuditLogCreate,
    SecurityEventCreate,
    AuditLogSchema,
    SecurityEventSchema
)

class SecuritySystemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_audit_event(self, event_data: AuditLogCreate) -> AuditLog:
        """
        Logs a standard audit event. This is the primary method for recording actions.
        """
        audit_log = AuditLog(**event_data.dict())
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        return audit_log

    async def log_security_event(self, event_data: SecurityEventCreate) -> SecurityEvent:
        """
        Logs a security-sensitive event that may require review.
        """
        security_event = SecurityEvent(**event_data.dict())
        self.db.add(security_event)
        await self.db.commit()
        await self.db.refresh(security_event)
        
        # In a real system, this might trigger an alert (e.g., email, PagerDuty)
        if security_event.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            print(f"ALERT: Critical security event logged: {security_event.description}")
            # alert_service.trigger_alert(...)
            
        return security_event

    async def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        event_type: Optional[EventType] = None
    ) -> List[AuditLogSchema]:
        """
        Retrieves a filtered list of audit logs.
        """
        query = select(AuditLog).order_by(AuditLog.timestamp.desc())
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
            
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_security_events(
        self,
        skip: int = 0,
        limit: int = 100,
        is_resolved: Optional[bool] = None,
        severity: Optional[SeverityLevel] = None
    ) -> List[SecurityEventSchema]:
        """
        Retrieves a filtered list of security events.
        """
        query = select(SecurityEvent).order_by(SecurityEvent.timestamp.desc())
        
        if is_resolved is not None:
            query = query.filter(SecurityEvent.is_resolved == is_resolved)
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
            
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def resolve_security_event(self, event_id: int, resolver_user_id: int) -> Optional[SecurityEvent]:
        """
        Marks a security event as resolved.
        """
        result = await self.db.execute(select(SecurityEvent).filter(SecurityEvent.id == event_id))
        event = result.scalars().first()
        
        if not event or event.is_resolved:
            return None
            
        event.is_resolved = True
        event.resolved_by_user_id = resolver_user_id
        event.resolved_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(event)
        return event

    # --- Example Helper for other services ---
    
    async def log_failed_login(self, ip_address: str, user_agent: str, username: str):
        """
        A specific helper to handle failed login attempts, which logs both
        an audit event and a security event.
        """
        audit_data = AuditLogCreate(
            event_type=EventType.FAILED_LOGIN_ATTEMPT,
            status=ActionStatus.FAILURE,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"username": username}
        )
        await self.log_audit_event(audit_data)
        
        # You could add logic here to check for brute-force attacks
        # e.g., if > 5 failed logins from same IP in 1 minute, create CRITICAL event.
        
        security_event_data = SecurityEventCreate(
            event_type=EventType.FAILED_LOGIN_ATTEMPT,
            severity=SeverityLevel.MEDIUM,
            ip_address=ip_address,
            description=f"Failed login attempt for username: {username}",
            metadata={"user_agent": user_agent}
        )
        await self.log_security_event(security_event_data) 