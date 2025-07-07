import logging
import json
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import engine, Base, SessionLocal
from app.db import models as db_models
from app.core.auth import AuthManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent.parent / "data"

def migrate_users(db: Session):
    logger.info("Migrating users...")
    try:
        with open(DATA_PATH / "users.json", "r") as f:
            users_data = json.load(f)
        
        for user_data in users_data:
            # Check if user already exists
            db_user = db.query(db_models.User).filter(db_models.User.email == user_data['email']).first()
            if not db_user:
                # Assuming the password in JSON is plain text and needs hashing.
                # If it's already hashed, this line should be adjusted.
                hashed_password = AuthManager.get_password_hash(user_data['password'])
                
                db_user = db_models.User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    hashed_password=hashed_password,
                    is_active=user_data.get('is_active', True),
                    role=user_data.get('role', 'user')
                )
                db.add(db_user)
        db.commit()
        logger.info("Users migrated successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not migrate users: {e}")

def migrate_user_profiles(db: Session):
    logger.info("Migrating user profiles...")
    try:
        with open(DATA_PATH / "user_profiles.json", "r") as f:
            profiles_data = json.load(f)

        for profile_data in profiles_data:
            db_profile = db.query(db_models.UserProfile).filter(db_models.UserProfile.user_id == profile_data['user_id']).first()
            if not db_profile and db.query(db_models.User).filter(db_models.User.id == profile_data['user_id']).first():
                db_profile = db_models.UserProfile(**profile_data)
                db.add(db_profile)
        db.commit()
        logger.info("User profiles migrated successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not migrate user profiles: {e}")

def migrate_water_data(db: Session):
    logger.info("Migrating water data...")
    try:
        with open(DATA_PATH / "water_data.json", "r") as f:
            waters_data = json.load(f)
        
        for water_data in waters_data:
            db_water = db.query(db_models.WaterData).filter(db_models.WaterData.id == water_data['id']).first()
            if not db_water:
                # Pydantic models in the JSON need to be converted to dicts for JSON columns
                water_data['ingredients'] = [i.model_dump() for i in water_data.get('ingredients', [])]
                water_data['report'] = water_data.get('report', {}).model_dump()
                db_water = db_models.WaterData(**water_data)
                db.add(db_water)
        db.commit()
        logger.info("Water data migrated successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not migrate water data: {e}")

# ... (similar migration functions for other JSON files) ...

def init_db() -> None:
    logger.info("Creating initial database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")
    
    # Explicitly create FTS triggers after tables are created
    create_fts_triggers_and_table()

def create_fts_triggers_and_table():
    """Create the FTS table and its sync triggers."""
    with engine.connect() as connection:
        try:
            logger.info("Creating FTS table for water_data...")
            connection.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS water_data_fts USING fts5(
                    name,
                    description,
                    brand_name,
                    content='water_data',
                    content_rowid='id'
                );
            """))
            logger.info("FTS table created.")
            
            logger.info("Creating FTS synchronization triggers...")
            connection.execute(text("""
                CREATE TRIGGER IF NOT EXISTS water_data_after_insert
                AFTER INSERT ON water_data BEGIN
                    INSERT INTO water_data_fts(rowid, name, description, brand_name)
                    VALUES (new.id, new.name, new.description, new.brand_name);
                END;
            """))
            connection.execute(text("""
                CREATE TRIGGER IF NOT EXISTS water_data_after_delete
                AFTER DELETE ON water_data BEGIN
                    INSERT INTO water_data_fts(water_data_fts, rowid, name, description, brand_name)
                    VALUES ('delete', old.id, old.name, old.description, old.brand_name);
                END;
            """))
            connection.execute(text("""
                CREATE TRIGGER IF NOT EXISTS water_data_after_update
                AFTER UPDATE ON water_data BEGIN
                    INSERT INTO water_data_fts(water_data_fts, rowid, name, description, brand_name)
                    VALUES ('delete', old.id, old.name, old.description, old.brand_name);
                    INSERT INTO water_data_fts(rowid, name, description, brand_name)
                    VALUES (new.id, new.name, new.description, new.brand_name);
                END;
            """))
            logger.info("FTS triggers created.")
            connection.commit()
        except Exception as e:
            logger.error(f"Error creating FTS setup: {e}")
            # Depending on the desired behavior, you might want to rollback
            # connection.rollback()

def migrate_all_data():
    db = SessionLocal()
    try:
        logger.info("Starting data migration from JSON to SQLite...")
        migrate_users(db)
        migrate_user_profiles(db)
        migrate_water_data(db)
        # Add calls to other migration functions here
        logger.info("Data migration completed.")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    migrate_all_data() 