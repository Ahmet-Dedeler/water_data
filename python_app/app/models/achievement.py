from pydantic import BaseModel
from datetime import datetime

# This is a Pydantic model for response serialization, not a SQLAlchemy model.
# The SQLAlchemy models have been moved to app/db/models.py to avoid circular imports
# and table re-definition errors.
class UserAchievementDetail(BaseModel):
    id: int
    name: str
    description: str
    icon_url: str | None
    total_stages: int
    secret: bool
    parent_id: int | None
    criteria: dict
    date_earned: datetime

    class Config:
        from_attributes = True 