from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="A user-friendly name for the API key.")

class APIKeySchema(BaseModel):
    """Metadata for an API key. The secret key is not included."""
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NewAPIKeyResponse(BaseModel):
    """The response when creating a new API key, including the one-time secret."""
    message: str = "Key generated successfully. This is the only time the full key will be shown."
    key_details: APIKeySchema
    plain_text_key: str = Field(..., description="The full, unhashed API key. Store this securely.") 