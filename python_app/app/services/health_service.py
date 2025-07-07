from sqlalchemy.orm import Session
from typing import Optional

from app.db import models
from app.schemas import health as health_schema

class HealthService:
    def get_integration(self, db: Session, user_id: int) -> Optional[models.HealthIntegration]:
        return db.query(models.HealthIntegration).filter_by(user_id=user_id).first()

    def create_or_update_integration(self, db: Session, user_id: int, integration: health_schema.HealthIntegrationCreate) -> models.HealthIntegration:
        db_integration = self.get_integration(db, user_id)
        if db_integration:
            # Update existing integration
            for field, value in integration.model_dump().items():
                setattr(db_integration, field, value)
        else:
            # Create new integration
            db_integration = models.HealthIntegration(**integration.model_dump(), user_id=user_id)
        
        db.add(db_integration)
        db.commit()
        db.refresh(db_integration)
        return db_integration

    def delete_integration(self, db: Session, user_id: int):
        db_integration = self.get_integration(db, user_id)
        if db_integration:
            db.delete(db_integration)
            db.commit()

health_service = HealthService() 