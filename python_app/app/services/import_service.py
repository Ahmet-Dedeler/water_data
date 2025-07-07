import csv
import io
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.db import models as db_models
from app.models.import_summary import ImportSummary

logger = logging.getLogger(__name__)

class ImportService:
    """Service for data import operations."""

    def import_water_logs_from_csv(self, db: Session, user_id: int, file_content: bytes) -> ImportSummary:
        """
        Imports water logs for a user from a CSV file.
        Expects columns: 'Date', 'Volume (ml)', 'Product Name', 'Brand'
        """
        content_str = file_content.decode('utf-8')
        file_io = io.StringIO(content_str)
        reader = csv.DictReader(file_io)

        records_processed = 0
        records_imported = 0
        errors = []

        # Create a lookup for existing water products to avoid many DB queries
        all_waters = db.query(db_models.WaterData).all()
        water_lookup = {(w.name.lower(), w.brand_name.lower()): w.id for w in all_waters}

        new_logs = []
        for i, row in enumerate(reader):
            records_processed += 1
            line_num = i + 2  # Account for header
            try:
                date_str = row.get('Date')
                volume_str = row.get('Volume (ml)')
                product_name = row.get('Product Name')
                brand_name = row.get('Brand')

                if not all([date_str, volume_str, product_name, brand_name]):
                    errors.append(f"Line {line_num}: Missing required data.")
                    continue

                log_date = datetime.fromisoformat(date_str)
                volume = float(volume_str)
                
                water_key = (product_name.lower(), brand_name.lower())
                water_id = water_lookup.get(water_key)
                
                if not water_id:
                    errors.append(f"Line {line_num}: Product '{product_name}' by '{brand_name}' not found.")
                    continue

                new_logs.append(db_models.WaterLog(
                    user_id=user_id,
                    water_id=water_id,
                    date=log_date,
                    volume=volume
                ))
                records_imported += 1

            except Exception as e:
                errors.append(f"Line {line_num}: Error processing row - {e}")
        
        if new_logs:
            db.bulk_save_objects(new_logs)
            db.commit()

        return ImportSummary(
            records_processed=records_processed,
            records_imported=records_imported,
            errors=errors
        ) 