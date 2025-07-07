from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, get_current_active_user
from app.services.api_key_service import api_key_service
from app.models.api_key import APIKeyCreate, APIKeySchema, NewAPIKeyResponse
from app.models.user import User

router = APIRouter()

@router.post("/api-keys", response_model=NewAPIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a new API key for the current user."""
    db_key, plain_text_key = api_key_service.create_api_key(db, current_user.id, key_data)
    
    key_details = APIKeySchema.model_validate(db_key)

    return NewAPIKeyResponse(
        key_details=key_details,
        plain_text_key=plain_text_key
    )

@router.get("/api-keys", response_model=List[APIKeySchema])
def get_my_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve all active API keys for the current user."""
    keys = api_key_service.get_api_keys_for_user(db, current_user.id)
    return [APIKeySchema.model_validate(key) for key in keys]

@router.delete("/api-keys/{key_prefix}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_prefix: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Revoke an API key by its prefix."""
    success = api_key_service.revoke_api_key(db, current_user.id, key_prefix)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or you do not have permission to revoke it."
        )
    return 