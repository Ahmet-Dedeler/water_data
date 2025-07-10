import pytest
from typing import Generator, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import httpx

from app.db.database import Base, get_db
from app.main import app
from app.core.auth import create_access_token
from app.db import models as db_models
from app.core.security import get_password_hash
from app.core.config import settings

# --- Database Fixtures ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Override settings for tests
    settings.DATABASE_URL = SQLALCHEMY_DATABASE_URL
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, Any, Any]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# --- API Client Fixture ---
@pytest.fixture(scope="function")
def test_client(db_session: Session) -> Generator[TestClient, Any, Any]:
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    del app.dependency_overrides[get_db]

@pytest.fixture(scope="function")
async def async_test_client(db_session: Session) -> Generator[httpx.AsyncClient, Any, Any]:
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
    del app.dependency_overrides[get_db]

# --- Test Data Fixtures ---
@pytest.fixture(scope="function")
def test_user(db_session: Session) -> db_models.User:
    user = db_models.User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True,
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_admin_user(db_session: Session) -> db_models.User:
    admin = db_models.User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True,
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture(scope="function")
def auth_headers_for_user(test_user: db_models.User) -> dict:
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def auth_headers_for_admin(test_admin_user: db_models.User) -> dict:
    token = create_access_token(data={"sub": test_admin_user.username})
    return {"Authorization": f"Bearer {token}"} 