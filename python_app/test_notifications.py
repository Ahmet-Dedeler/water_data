import os
import sys
import json
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.services.notification_service import notification_service
from app.models.notification import (
    Notification, UserNotificationSettings, NotificationType, 
    NotificationChannel, NotificationStatus, NotificationCreate
)
from app.core.auth import get_current_user
from app.models.user import User

def get_current_user_override():
    return User(id=1, email="test@test.com", username="testuser", role="user", is_active=True, is_verified=True, hashed_password="x")

app.dependency_overrides[get_current_user] = get_current_user_override

client = TestClient(app)

# Test data paths
NOTIFICATIONS_FILE = os.path.join(os.path.dirname(__file__), 'app/data/notifications.json')
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'app/data/notification_settings.json')

def setup_test_data():
    """Set up initial data for tests."""
    # Clear existing data
    with open(NOTIFICATIONS_FILE, 'w') as f:
        json.dump([], f)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump([], f)

    # Add sample settings
    sample_settings = [
        {
            "user_id": 1,
            "master_enabled": True,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "email_enabled": True,
            "push_enabled": True,
            "new_product_alerts_enabled": False,
            "recall_alerts_enabled": True,
            "health_warnings_enabled": True,
            "goal_milestones_enabled": True,
            "goal_reminders_enabled": True,
            "review_responses_enabled": True,
            "system_announcements_enabled": True,
            "new_recommendations_enabled": True,
            "sms_enabled": False,
            "last_updated": "2023-01-01T12:00:00"
        }
    ]
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(sample_settings, f, indent=4)

async def test_get_notifications():
    setup_test_data()
    
    # Send a notification to be retrieved
    await notification_service.send_notification(NotificationCreate(
        user_id=1,
        title="Test Notification",
        message="This is a test notification.",
        notification_type=NotificationType.HEALTH_WARNING
    ))
    
    response = client.get(f"/api/v1/notifications/")
    assert response.status_code == 200
    notifications = response.json()
    assert isinstance(notifications['notifications'], list)
    assert len(notifications['notifications']) > 0
    assert notifications['notifications'][0]["title"] == "Test Notification"
    assert notifications['notifications'][0]["user_id"] == 1

async def test_mark_notification_as_read():
    setup_test_data()
    
    sent_notification = await notification_service.send_notification(NotificationCreate(
        user_id=1,
        title="Unread Notification",
        message="This should be marked as read.",
        notification_type=NotificationType.NEW_PRODUCT
    ))
    assert sent_notification is not None
    notification_id = sent_notification.id
    
    response = client.post(f"/api/v1/notifications/mark-read/{notification_id}")
    assert response.status_code == 200
    read_notification_response = response.json()
    assert read_notification_response["message"] == "Notification marked as read."

    # Verify it's updated in the data file
    user_notifications, _ = await notification_service.get_user_notifications(1)
    assert user_notifications[0].status == NotificationStatus.READ

async def test_get_notification_settings():
    setup_test_data()
    response = client.get(f"/api/v1/notifications/settings")
    assert response.status_code == 200
    settings = response.json()
    assert settings["master_enabled"] is True
    assert settings["new_product_alerts_enabled"] is False

async def test_update_notification_settings():
    setup_test_data()
    new_settings_data = {
        "master_enabled": False,
        "quiet_hours_enabled": False,
        "email_enabled": False,
        "push_enabled": False
    }
    
    response = client.put(f"/api/v1/notifications/settings", json=new_settings_data)
    assert response.status_code == 200
    updated_settings = response.json()
    
    assert updated_settings["master_enabled"] is False
    assert updated_settings["email_enabled"] is False

    # Verify update in the service
    retrieved_settings = await notification_service.get_user_notification_settings(1)
    assert retrieved_settings is not None
    assert retrieved_settings.master_enabled is False
    assert retrieved_settings.email_enabled is False

@patch('app.services.notification_service.datetime')
async def test_send_notification_quiet_hours(mock_datetime):
    setup_test_data()
    user_id = 1
    
    # Mock current time to be within quiet hours
    settings = await notification_service.get_user_notification_settings(user_id)
    assert settings is not None
    
    start_time_str = settings.quiet_hours_start
    start_hour = int(start_time_str.split(":")[0])
    
    # Set time to be inside quiet hours (e.g., 23:00 if start is 22:00)
    inside_quiet_hours_time = datetime.now().replace(hour=(start_hour + 1) % 24, minute=0, second=0)
    
    mock_datetime.now.return_value = inside_quiet_hours_time
    
    # Try sending notification
    notification = NotificationCreate(
        user_id=1,
        title="Quiet Hours Test",
        message="This should not be sent.",
        notification_type=NotificationType.NEW_PRODUCT
    )
    sent_notification = await notification_service.send_notification(notification)
    
    # Notification should not be sent, as it's in quiet hours and that type is enabled
    assert sent_notification is not None
    assert notification_service._should_send(sent_notification, settings) is False

async def test_send_notification_disabled_type():
    setup_test_data()
    
    notification = NotificationCreate(
        user_id=1,
        title="New Product Spam",
        message="This should be blocked.",
        notification_type=NotificationType.NEW_PRODUCT
    )
    
    # Get settings to check against
    settings = await notification_service.get_user_notification_settings(1)
    
    # Manually create notification to check _should_send
    notification_obj = Notification(id="test", **notification.model_dump())
    
    assert notification_service._should_send(notification_obj, settings) is False

async def test_send_notification_globally_disabled():
    setup_test_data()
    user_id = 3
    
    # Set up user with notifications disabled
    await notification_service.update_user_notification_settings(user_id, UserNotificationSettings(
        user_id=3,
        master_enabled=False
    ))
    
    notification = NotificationCreate(
        user_id=3,
        title="Disabled Account Test",
        message="This should not be sent.",
        notification_type=NotificationType.SYSTEM_ANNOUNCEMENT
    )
    
    # Get settings to check against
    settings = await notification_service.get_user_notification_settings(user_id)

    # Manually create notification to check _should_send
    notification_obj = Notification(id="test", **notification.model_dump())
    assert notification_service._should_send(notification_obj, settings) is False

if __name__ == "__main__":
    # This allows running the tests directly
    import pytest
    sys.exit(pytest.main(["-v", __file__])) 