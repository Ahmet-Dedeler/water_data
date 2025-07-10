from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.security_system import EventType, SeverityLevel
from app.schemas.security_system import AuditLogSchema, SecurityEventSchema
from app.services.security_system_service import SecuritySystemService

router = APIRouter()

@router.get("/audit-logs", response_model=List[AuditLogSchema])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    Retrieve audit logs from the system. Requires administrative privileges.
    """
    service = SecuritySystemService(db)
    logs = await service.get_audit_logs(
        skip=skip,
        limit=limit,
        user_id=user_id,
        event_type=event_type
    )
    return logs

@router.get("/security-events", response_model=List[SecurityEventSchema])
async def get_security_events(
    skip: int = 0,
    limit: int = 100,
    is_resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity level"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    Retrieve security events from the system. Requires administrative privileges.
    """
    service = SecuritySystemService(db)
    events = await service.get_security_events(
        skip=skip,
        limit=limit,
        is_resolved=is_resolved,
        severity=severity
    )
    return events

@router.put("/security-events/{event_id}/resolve", response_model=SecurityEventSchema)
async def resolve_security_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Add admin role check
):
    """
    Mark a security event as resolved. Requires administrative privileges.
    """
    service = SecuritySystemService(db)
    event = await service.resolve_security_event(event_id=event_id, resolver_user_id=current_user.id)
    if not event:
        raise HTTPException(status_code=404, detail="Security event not found or already resolved")
    return event 