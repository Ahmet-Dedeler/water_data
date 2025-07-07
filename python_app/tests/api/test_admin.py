import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import models as db_models

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

# --- Test Authentication ---
def test_admin_route_access_denied_for_regular_user(test_client: TestClient, auth_headers_for_user: dict):
    response = test_client.get("/api/v1/admin/dashboard-stats", headers=auth_headers_for_user)
    assert response.status_code == 403

def test_admin_route_access_denied_for_no_auth(test_client: TestClient):
    response = test_client.get("/api/v1/admin/dashboard-stats")
    assert response.status_code == 401

# --- Test Admin Endpoints ---
def test_get_dashboard_stats(test_client: TestClient, auth_headers_for_admin: dict, db_session: Session, test_user: db_models.User):
    # Setup: Create some data
    db_session.add(db_models.WaterLog(user_id=test_user.id, water_id=1, volume=500)) # Assume water_id=1 exists
    db_session.commit()

    response = test_client.get("/api/v1/admin/dashboard-stats", headers=auth_headers_for_admin)
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_users"] >= 2 # admin and test user
    assert stats["total_water_logs"] == 1
    assert stats["total_volume_logged_ml"] == 500

def test_list_users(test_client: TestClient, auth_headers_for_admin: dict, test_user: db_models.User):
    response = test_client.get("/api/v1/admin/users", headers=auth_headers_for_admin)
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 2
    assert any(u["username"] == "testuser" for u in users)
    assert any(u["username"] == "adminuser" for u in users)

def test_ban_user(test_client: TestClient, auth_headers_for_admin: dict, db_session: Session, test_user: db_models.User):
    # Ban the user
    response = test_client.post(f"/api/v1/admin/users/{test_user.id}/ban", headers=auth_headers_for_admin)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Verify in DB
    db_session.refresh(test_user)
    assert test_user.is_active is False

def test_unban_user(test_client: TestClient, auth_headers_for_admin: dict, db_session: Session, test_user: db_models.User):
    # First, ban the user to set up the state
    test_user.is_active = False
    db_session.commit()

    # Un-ban the user
    response = test_client.post(f"/api/v1/admin/users/{test_user.id}/unban", headers=auth_headers_for_admin)
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    # Verify in DB
    db_session.refresh(test_user)
    assert test_user.is_active is True

def test_delete_comment(
    test_client: TestClient, 
    auth_headers_for_admin: dict, 
    db_session: Session, 
    test_user: db_models.User
):
    # Setup: Create achievement and comment
    user_ach = db_models.UserAchievement(user_id=test_user.id, achievement_id="first_log")
    db_session.add(user_ach)
    db_session.commit()
    comment = db_models.Comment(user_id=test_user.id, user_achievement_id=user_ach.id, content="Test comment")
    db_session.add(comment)
    db_session.commit()
    
    # Delete the comment
    response = test_client.delete(f"/api/v1/admin/comments/{comment.id}", headers=auth_headers_for_admin)
    assert response.status_code == 204

    # Verify deletion
    deleted_comment = db_session.query(db_models.Comment).filter_by(id=comment.id).first()
    assert deleted_comment is None 