import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Build the path to the database file
db_path = Path(__file__).parent.parent / "data" / "water_app.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Ensure the data directory exists
os.makedirs(db_path.parent, exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 