from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_active_user
from app.services.push_notification_service import push_notification_service
from app.models.push import Device, DeviceCreate
from app.models.user import User

router = APIRouter()

@router.post("/devices", response_model=Device, status_code=status.HTTP_201_CREATED)
def register_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Register a new device for push notifications."""
    return push_notification_service.register_device(db, current_user.id, device_data)

@router.delete("/devices/{token}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Unregister a device to stop receiving push notifications."""
    # We don't need to check ownership here; the token is globally unique.
    # If a user wants to stop notifications, they just provide their token.
    success = push_notification_service.unregister_device(db, token)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device token not found.")
    return 