import logging
from typing import List
from sqlalchemy.orm import Session
from app.db import models as db_models
from app.models.push import DeviceCreate

logger = logging.getLogger(__name__)

class PushNotificationService:
    def register_device(self, db: Session, user_id: int, device_data: DeviceCreate) -> db_models.Device:
        # Check if this token is already registered for another user
        existing_device = db.query(db_models.Device).filter_by(token=device_data.token).first()
        if existing_device and existing_device.user_id != user_id:
            # Re-assign device to the new user
            existing_device.user_id = user_id
            db.commit()
            db.refresh(existing_device)
            return existing_device

        # If token exists for the same user, just return it
        if existing_device and existing_device.user_id == user_id:
            return existing_device

        new_device = db_models.Device(
            user_id=user_id,
            token=device_data.token,
            device_type=device_data.device_type.value
        )
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        return new_device

    def unregister_device(self, db: Session, token: str) -> bool:
        device = db.query(db_models.Device).filter_by(token=token).first()
        if device:
            db.delete(device)
            db.commit()
            return True
        return False

    def send_push_notification(self, db: Session, user_id: int, title: str, body: str, data: dict = None):
        """
        Mock implementation of sending a push notification.
        In a real app, this would integrate with a service like FCM or APNs.
        """
        devices = db.query(db_models.Device).filter_by(user_id=user_id).all()
        if not devices:
            logger.warning(f"No registered devices found for user {user_id}. Cannot send push notification.")
            return

        for device in devices:
            logger.info(
                f"MOCK PUSH SENT to user {user_id} on device {device.token} ({device.device_type}):\n"
                f"Title: {title}\n"
                f"Body: {body}\n"
                f"Data: {data or {}}"
            )
            # Here, you would add the actual push sending logic, e.g.:
            # if device.device_type == 'ios':
            #     send_to_apns(device.token, title, body, data)
            # elif device.device_type == 'android':
            #     send_to_fcm(device.token, title, body, data)

# Global service instance
push_notification_service = PushNotificationService() 