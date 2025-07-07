import secrets
import hashlib
from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime

from app.db import models as db_models
from app.models.api_key import APIKeyCreate

class APIKeyService:
    def _generate_key(self) -> Tuple[str, str, str]:
        """Generates a new API key tuple (prefix, plain_text, hashed)."""
        plain_text_key = f"sk_{secrets.token_urlsafe(32)}"
        prefix = plain_text_key[:6] # e.g., "sk_abc1"
        hashed_key = hashlib.sha256(plain_text_key.encode()).hexdigest()
        return prefix, plain_text_key, hashed_key

    def create_api_key(self, db: Session, user_id: int, key_data: APIKeyCreate) -> Tuple[db_models.APIKey, str]:
        prefix, plain_text_key, hashed_key = self._generate_key()
        
        db_key = db_models.APIKey(
            key_prefix=prefix,
            hashed_key=hashed_key,
            user_id=user_id,
            name=key_data.name
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        return db_key, plain_text_key

    def get_api_keys_for_user(self, db: Session, user_id: int) -> List[db_models.APIKey]:
        return db.query(db_models.APIKey).filter_by(user_id=user_id, is_active=True).all()

    def revoke_api_key(self, db: Session, user_id: int, key_prefix: str) -> bool:
        db_key = db.query(db_models.APIKey).filter_by(user_id=user_id, key_prefix=key_prefix).first()
        if db_key and db_key.is_active:
            db_key.is_active = False
            db.commit()
            return True
        return False

    def get_user_by_api_key(self, db: Session, plain_text_key: str) -> db_models.User:
        hashed_key = hashlib.sha256(plain_text_key.encode()).hexdigest()
        db_key = db.query(db_models.APIKey).filter_by(hashed_key=hashed_key, is_active=True).first()
        
        if not db_key:
            return None
        
        # Update last used timestamp
        db_key.last_used_at = datetime.utcnow()
        db.commit()
        
        return db_key.user

# Global service instance
api_key_service = APIKeyService() 