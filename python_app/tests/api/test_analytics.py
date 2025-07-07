import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from app.main import app
from app.db import models
from app.core.auth import create_access_token

client = TestClient(app)

def create_test_user(db: Session):
    user = models.User(
        username="testuser",
        email="testuser@example.com",
        hashed_password="fakehashedpassword",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_water_logs(db: Session, user_id: int):
    water_data = models.WaterData(name="Test Water", brand_name="Test Brand")
    db.add(water_data)
    db.commit()
    db.refresh(water_data)

    log1 = models.WaterLog(
        user_id=user_id,
        water_id=water_data.id,
        volume=500,
        date=datetime(2024, 1, 1, 10, 0, 0),
    )
    log2 = models.WaterLog(
        user_id=user_id,
        water_id=water_data.id,
        volume=1000,
        date=datetime(2024, 1, 2, 12, 0, 0),
    )
    log3 = models.WaterLog(
        user_id=user_id,
        water_id=water_data.id,
        volume=250,
        date=datetime(2024, 1, 5, 15, 0, 0), # Outside the test date range
    )
    db.add_all([log1, log2, log3])
    db.commit()

def test_get_water_consumption_analytics(db: Session):
    user = create_test_user(db)
    create_water_logs(db, user.id)

    access_token = create_access_token(data={"sub": user.username})
    headers = {"Authorization": f"Bearer {access_token}"}

    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 4)

    response = client.get(
        f"/api/v1/analytics/water-consumption/?start_date={start_date}&end_date={end_date}",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_consumption"] == 1500
    assert data["average_daily_consumption"] == (1500 / 4)
    assert len(data["daily_consumption"]) == 2
    assert data["daily_consumption"][0]["date"] == "2024-01-01"
    assert data["daily_consumption"][0]["total_consumption"] == 500
    assert data["daily_consumption"][1]["date"] == "2024-01-02"
    assert data["daily_consumption"][1]["total_consumption"] == 1000 