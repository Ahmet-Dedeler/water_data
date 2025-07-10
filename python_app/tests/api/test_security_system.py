import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.security_system_service import SecuritySystemService
from app.schemas.security_system import SecurityEventCreate
from app.models.security_system import EventType, SeverityLevel

def test_get_audit_logs_unauthorized(test_client: TestClient):
    response = test_client.get("/api/v1/security/audit-logs")
    assert response.status_code == 401

def test_get_audit_logs_as_admin(test_client: TestClient, auth_headers_for_admin: dict):
    response = test_client.get("/api/v1/security/audit-logs", headers=auth_headers_for_admin)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_security_events_as_admin(test_client: TestClient, auth_headers_for_admin: dict):
    response = test_client.get("/api/v1/security/security-events", headers=auth_headers_for_admin)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_resolve_security_event_as_admin(
    db_session: Session, # Use session to create an event first
    test_client: TestClient, 
    auth_headers_for_admin: dict
):
    # Manually create a security event to resolve
    service = SecuritySystemService(db_session)
    event = await service.log_security_event(SecurityEventCreate(
        event_type=EventType.SECURITY_SCAN,
        severity=SeverityLevel.HIGH,
        description="Event to be resolved by API test"
    ))
    
    response = test_client.put(
        f"/api/v1/security/security-events/{event.id}/resolve",
        headers=auth_headers_for_admin
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == event.id
    assert data["is_resolved"] is True
    
    # Test resolving a non-existent event
    response = test_client.put(
        "/api/v1/security/security-events/99999/resolve",
        headers=auth_headers_for_admin
    )
    assert response.status_code == 404 