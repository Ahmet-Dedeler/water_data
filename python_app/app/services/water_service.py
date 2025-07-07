from typing import List, Optional, Tuple, Dict
import math
from datetime import datetime, timedelta, date
import json
from pathlib import Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, asc, or_, text

from app.models import (
    WaterData, WaterCreate, WaterUpdate, WaterListResponse, 
    PaginationParams, SearchParams, SortParams, WaterSummary, WaterLogSearchCriteria
)
from app.db import models as db_models
from app.services.achievement_service import AchievementService
from app.services.social_service import SocialService, social_service
from app.services.user_service import UserService, user_service
from app.services.base_service import BaseService
from app.models.water import WaterLog
from app.schemas.water import WaterLogCreate, WaterLogUpdate
from app.services import achievement_service
from app.services.challenge_service import challenge_service
from app.services.level_service import level_service
from app.services.points_service import points_service
import logging

log = logging.getLogger(__name__)

class WaterService(BaseService[WaterLog, WaterLogCreate, WaterLogUpdate]):
    """Service for water data operations using a database."""
    
    def __init__(self):
        # In a real app, these would be injected.
        self.achievement_service = AchievementService()
        self.social_service = social_service
        self.user_service = user_service

    def get_water_by_id(self, db: Session, water_id: int) -> Optional[db_models.WaterData]:
        """Get water by ID."""
        return db.query(db_models.WaterData).filter(db_models.WaterData.id == water_id).first()

    def get_all_waters(
        self,
        db: Session,
        pagination: PaginationParams,
    ) -> WaterListResponse:
        """Get all waters with pagination."""
        query = db.query(db_models.WaterData)
        
        total = query.count()
        
        results = query.offset(pagination.skip).limit(pagination.limit).all()
        
        total_pages = math.ceil(total / pagination.size)
            
        return WaterListResponse(
            data=results,
            total=total,
            page=pagination.page,
            size=pagination.size,
            total_pages=total_pages
        )

    async def log_water_intake(
        self,
        db: Session,
        user_id: int,
        water_id: int,
        volume: float,
        drink_type_id: Optional[int] = None,
        caffeine_mg: Optional[int] = None
    ):
        """Logs a user's water intake and triggers related events."""
        new_log = db_models.WaterLog(
            user_id=user_id,
            water_id=water_id,
            volume=volume,
            date=datetime.utcnow(),
            drink_type_id=drink_type_id,
            caffeine_mg=caffeine_mg
        )
        db.add(new_log)

        # This method needs to be implemented in UserService
        self.user_service.update_hydration_streak(db, user_id)
        
        # Calculate total volume for today and update daily streak
        today = datetime.utcnow().date()
        total_today = db.query(func.sum(db_models.WaterLog.volume)).filter(
            db_models.WaterLog.user_id == user_id,
            func.date(db_models.WaterLog.date) == today
        ).scalar() or 0.0
        
        # Update daily streak record
        self.user_service.create_or_update_daily_streak(
            db, user_id, datetime.utcnow(), total_today
        )
        
        # Update challenge progress
        challenge_service.update_challenge_progress(db, user_id, "total_volume", volume)

        # Grant XP for logging
        level_service.add_xp(db, user_id, 10) # Grant 10 XP per log

        # Grant points for logging
        points_service.add_points(db, user_id, 5) # Grant 5 points per log

        # This method needs to be implemented in AchievementService
        new_achievements = await self.achievement_service.check_and_grant_achievements(db, user_id)
        
        water = self.get_water_by_id(db, water_id)
        water_name = water.name if water else "water"

        # This method needs to be implemented in SocialService
        await self.social_service.create_activity(
            db,
            user_id=user_id,
            activity_type="logged_water",
            data={"volume": volume, "water_name": water_name}
        )

        db.commit()
        db.refresh(new_log)
        
        return {
            "log": new_log,
            "new_achievements": new_achievements
        }
        
    def get_user_log_history(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[db_models.WaterLog]:
        """Get a user's water log history."""
        return db.query(db_models.WaterLog)\
                 .filter(db_models.WaterLog.user_id == user_id)\
                 .order_by(desc(db_models.WaterLog.timestamp))\
                 .offset(skip)\
                 .limit(limit)\
                 .all()

    def get_water_summary(self, db: Session) -> WaterSummary:
        """Get summary statistics for all waters."""
        total_products = db.query(db_models.WaterData).count()
        total_brands = db.query(func.count(func.distinct(db_models.WaterData.brand))).scalar()
        average_score = db.query(func.avg(db_models.WaterData.score)).scalar() or 0
        
        # More complex stats might need more queries or different approaches
        return WaterSummary(
            total_products=total_products,
            total_brands=total_brands,
            average_score=round(average_score, 2),
            most_common_packaging= "Bottle", # Placeholder, requires a more complex query
            lab_tested_percentage= 50.0 # Placeholder
        )
        
    def get_top_waters(self, db: Session, limit: int = 10) -> List[db_models.WaterData]:
        """Get top-rated waters."""
        return db.query(db_models.WaterData).order_by(desc(db_models.WaterData.score)).limit(limit).all()

    def get_brands(self, db: Session) -> List[str]:
        """Get a list of all distinct brands."""
        return [b[0] for b in db.query(db_models.WaterData.brand).distinct().all()]

    def get_packaging_types(self, db: Session) -> List[str]:
        """Get a list of all distinct packaging types."""
        return [p[0] for p in db.query(db_models.WaterData.packaging).distinct().all()]
        
    def submit_draft_product(self, db: Session, user_id: int, product_data: WaterCreate) -> db_models.DraftProduct:
        """Saves a user-submitted product as a draft for admin review."""
        draft = db_models.DraftProduct(
            submitted_by_user_id=user_id,
            product_data=product_data.model_dump(),
            status="pending"
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    def search_waters(
        self,
        db: Session,
        query: Optional[str] = None,
        brand: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        packaging: Optional[str] = None,
        has_contaminants: Optional[bool] = None,
        lab_tested: Optional[bool] = None,
        sort_by: str = "score",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20
    ) -> WaterListResponse:
        """Search waters with comprehensive filtering and sorting."""
        
        q = db.query(db_models.WaterData)
        
        if query:
            # Use FTS for the text search
            # Note: The syntax for FTS can vary between DBs. This is for SQLite.
            fts_query = db.query(db_models.WaterDataFTS.rowid).filter(
                db_models.WaterDataFTS.name.match(query) |
                db_models.WaterDataFTS.description.match(query) |
                db_models.WaterDataFTS.brand_name.match(query)
            ).subquery()
            q = q.join(fts_query, db_models.WaterData.id == fts_query.c.rowid)

        if brand:
            q = q.filter(db_models.WaterData.brand_name.ilike(f"%{brand}%"))
        if min_score is not None:
            q = q.filter(db_models.WaterData.score >= min_score)
        if max_score is not None:
            q = q.filter(db_models.WaterData.score <= max_score)
        if packaging:
            q = q.filter(db_models.WaterData.packaging == packaging)
        if lab_tested is not None:
            q = q.filter(db_models.WaterData.lab_tested == lab_tested)
        if has_contaminants is not None:
            if has_contaminants:
                q = q.filter(db_models.WaterData.contaminants != None) # Checks for presence
            else:
                q = q.filter(db_models.WaterData.contaminants == None)

        # Sorting
        sort_column = getattr(db_models.WaterData, sort_by, db_models.WaterData.score)
        if sort_order == "desc":
            q = q.order_by(desc(sort_column))
        else:
            q = q.order_by(asc(sort_column))
            
        total = q.count()
        
        # Pagination
        skip = (page - 1) * size
        results = q.offset(skip).limit(size).all()
        
        total_pages = math.ceil(total / size)
            
        return WaterListResponse(
            data=results,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )

    def search_water_logs(
        self,
        db: Session,
        user_id: int,
        criteria: WaterLogSearchCriteria,
        skip: int = 0,
        limit: int = 100
    ) -> List[db_models.WaterLog]:
        """
        Performs an advanced search for a user's water logs based on criteria.
        """
        query = db.query(db_models.WaterLog).filter(db_models.WaterLog.user_id == user_id)
        
        # Eager load the related WaterData to avoid N+1 query problem
        query = query.options(joinedload(db_models.WaterLog.water))

        if criteria.start_date:
            query = query.filter(db_models.WaterLog.date >= criteria.start_date)
        if criteria.end_date:
            query = query.filter(db_models.WaterLog.date <= criteria.end_date)
        if criteria.min_volume is not None:
            query = query.filter(db_models.WaterLog.volume >= criteria.min_volume)
        if criteria.max_volume is not None:
            query = query.filter(db_models.WaterLog.volume <= criteria.max_volume)

        if criteria.brand_names or criteria.packaging_types:
            query = query.join(db_models.WaterData)
            if criteria.brand_names:
                query = query.filter(db_models.WaterData.brand_name.in_(criteria.brand_names))
            if criteria.packaging_types:
                query = query.filter(db_models.WaterData.packaging.in_(criteria.packaging_types))

        return query.order_by(db_models.WaterLog.date.desc()).offset(skip).limit(limit).all()

    def get_logs_by_user(
        self, db: Session, *, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[WaterLog]:
        query = db.query(self.model).filter(self.model.user_id == user_id)
        if start_date:
            query = query.filter(self.model.timestamp >= start_date)
        if end_date:
            query = query.filter(self.model.timestamp <= end_date)
        return query.order_by(self.model.timestamp.desc()).all()

    def create_log(self, db: Session, *, user_id: int, log_in: WaterLogCreate) -> WaterLog:
        db_obj = self.create(db, obj_in=log_in, user_id=user_id)
        
        # After logging, check if any achievements were unlocked.
        # This is a good example of cross-service interaction.
        achievement_service.check_and_grant_achievements(db, user_id=user_id)
        
        log.info(f"Water logged for user {user_id}. Volume: {log_in.volume_ml}ml.")
        return db_obj

    def get_log(self, db: Session, *, log_id: int) -> Optional[WaterLog]:
        return self.get(db, id=log_id)

    def update_log(self, db: Session, *, db_obj: WaterLog, obj_in: WaterLogUpdate) -> WaterLog:
        return self.update(db, db_obj=db_obj, obj_in=obj_in)

    def delete_log(self, db: Session, *, log_id: int) -> None:
        self.remove(db, id=log_id)

# Global instance
water_service = WaterService() 