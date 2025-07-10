import pytest
from sqlalchemy.orm import Session
from app.services.security_system_service import SecuritySystemService
from app.schemas.security_system import AuditLogCreate, SecurityEventCreate
from app.models.security_system import EventType, ActionStatus, SeverityLevel

@pytest.mark.asyncio
async def test_log_audit_event(db_session: Session):
    service = SecuritySystemService(db_session)
    event_data = AuditLogCreate(
        event_type=EventType.USER_LOGIN,
        status=ActionStatus.SUCCESS,
        user_id=1,
        ip_address="127.0.0.1"
    )
    log = await service.log_audit_event(event_data)
    assert log is not None
    assert log.event_type == EventType.USER_LOGIN
    assert log.user_id == 1

@pytest.mark.asyncio
async def test_log_security_event(db_session: Session):
    service = SecuritySystemService(db_session)
    event_data = SecurityEventCreate(
        event_type=EventType.FAILED_LOGIN_ATTEMPT,
        severity=SeverityLevel.MEDIUM,
        ip_address="127.0.0.1",
        description="Test failed login"
    )
    event = await service.log_security_event(event_data)
    assert event is not None
    assert event.severity == SeverityLevel.MEDIUM
    assert not event.is_resolved

@pytest.mark.asyncio
async def test_get_audit_logs(db_session: Session, test_user):
    service = SecuritySystemService(db_session)
    await service.log_audit_event(AuditLogCreate(
        event_type=EventType.USER_LOGIN, status=ActionStatus.SUCCESS, user_id=test_user.id
    ))
    await service.log_audit_event(AuditLogCreate(
        event_type=EventType.USER_LOGOUT, status=ActionStatus.SUCCESS, user_id=test_user.id
    ))
    
    logs = await service.get_audit_logs(user_id=test_user.id)
    assert len(logs) == 2
    
    logs_all = await service.get_audit_logs()
    assert len(logs_all) >= 2

@pytest.mark.asyncio
async def test_get_security_events(db_session: Session):
    service = SecuritySystemService(db_session)
    await service.log_security_event(SecurityEventCreate(
        event_type=EventType.FAILED_LOGIN_ATTEMPT, severity=SeverityLevel.HIGH, description="A"
    ))
    await service.log_security_event(SecurityEventCreate(
        event_type=EventType.PERMISSION_DENIED, severity=SeverityLevel.MEDIUM, description="B", is_resolved=True
    ))

    unresolved_events = await service.get_security_events(is_resolved=False)
    assert len(unresolved_events) >= 1 # Can be more due to other tests
    assert all(not e.is_resolved for e in unresolved_events)
    
    high_sev_events = await service.get_security_events(severity=SeverityLevel.HIGH)
    assert len(high_sev_events) >= 1

@pytest.mark.asyncio
async def test_resolve_security_event(db_session: Session, test_admin_user):
    service = SecuritySystemService(db_session)
    event = await service.log_security_event(SecurityEventCreate(
        event_type=EventType.SECURITY_SCAN, severity=SeverityLevel.CRITICAL, description="Test scan"
    ))
    
    assert not event.is_resolved
    
    resolved_event = await service.resolve_security_event(event.id, test_admin_user.id)
    assert resolved_event is not None
    assert resolved_event.is_resolved
    assert resolved_event.resolved_by_user_id == test_admin_user.id
    
    # Test resolving an already resolved event
    already_resolved = await service.resolve_security_event(event.id, test_admin_user.id)
    assert already_resolved is None 