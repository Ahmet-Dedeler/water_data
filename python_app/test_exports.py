import os
import sys
import json
from fastapi.testclient import TestClient
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from test_main import app
from app.core.auth import get_current_user
from app.models.user import User

def get_current_user_override():
    return User(id=1, email="test@test.com", username="testuser", role="user", is_active=True, is_verified=True, hashed_password="x")

app.dependency_overrides[get_current_user] = get_current_user_override

client = TestClient(app)

# Test data paths
EXPORT_JOBS_FILE = os.path.join(os.path.dirname(__file__), 'app/data/export_jobs.json')
WATER_DATA_FILE = os.path.join(os.path.dirname(__file__), 'app/data/water_data.json')
INGREDIENTS_FILE = os.path.join(os.path.dirname(__file__), 'app/data/ingredients.json')


def setup_test_data():
    """Set up initial data for tests."""
    # Clear existing data
    if os.path.exists(EXPORT_JOBS_FILE):
        os.remove(EXPORT_JOBS_FILE)
    
    # Create dummy water data
    dummy_water_data = [
        {
            "id": 1, "name": "Water A", "brand": {"name": "Brand A"}, "score": 90,
            "ingredients": [], "nutrients": [], "contaminants": [], "packaging": "bottle",
            "source": "spring", "lab_tested": True, "health_status": "excellent",
            "description": "A fine water.", "image": "http://example.com/a.jpg",
            "price_per_liter": 1.0, "microplastics_risk": "low"
        },
        {
            "id": 2, "name": "Water B", "brand": {"name": "Brand B"}, "score": 80,
            "ingredients": [], "nutrients": [], "contaminants": [], "packaging": "can",
            "source": "artesian", "lab_tested": False, "health_status": "good",
            "description": "An okay water.", "image": "http://example.com/b.jpg",
            "price_per_liter": 0.5, "microplastics_risk": "medium"
        },
    ]
    with open(WATER_DATA_FILE, 'w') as f:
        json.dump(dummy_water_data, f)

    # Create dummy ingredients data
    with open(INGREDIENTS_FILE, 'w') as f:
        json.dump({}, f)


@pytest.fixture(autouse=True)
async def run_around_tests(monkeypatch):
    from app.core import config
    monkeypatch.setattr(config, 'settings', config.Settings(
        water_data_path=WATER_DATA_FILE,
        ingredients_data_path=INGREDIENTS_FILE,
    ))
    setup_test_data()
    from app.services.data_service import data_service
    await data_service.reload_data()
    yield
    # Teardown
    if os.path.exists(EXPORT_JOBS_FILE):
        os.remove(EXPORT_JOBS_FILE)
    export_dir = os.path.join(os.path.dirname(__file__), 'app/data/exports')
    if os.path.exists(export_dir):
        for f in os.listdir(export_dir):
            os.remove(os.path.join(export_dir, f))
        os.rmdir(export_dir)
    if os.path.exists(WATER_DATA_FILE):
        os.remove(WATER_DATA_FILE)
    if os.path.exists(INGREDIENTS_FILE):
        os.remove(INGREDIENTS_FILE)

async def test_create_export_job():
    config = {
        "file_name": "test_export",
        "export_format": "json",
        "scope": "all_water_data"
    }
    response = client.post("/api/v1/exports/", json=config)
    assert response.status_code == 202
    job = response.json()
    assert job["config"]["file_name"] == "test_export"
    assert job["status"] == "completed"
    assert job["file_path"] is not None

async def test_get_user_export_jobs():
    # Create a job first
    config = {
        "file_name": "test_export_list",
        "export_format": "csv",
        "scope": "all_water_data"
    }
    client.post("/api/v1/exports/", json=config)

    response = client.get("/api/v1/exports/")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert jobs[0]["config"]["file_name"] == "test_export_list"

async def test_get_export_job_status():
    config = {
        "file_name": "test_export_status",
        "export_format": "json",
        "scope": "all_water_data"
    }
    create_response = client.post("/api/v1/exports/", json=config)
    job_id = create_response.json()["id"]

    response = client.get(f"/api/v1/exports/{job_id}")
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == job_id
    assert job["status"] == "completed"

async def test_export_file_content_json():
    config = {
        "file_name": "water_data_export",
        "export_format": "json",
        "scope": "all_water_data"
    }
    create_response = client.post("/api/v1/exports/", json=config)
    job = create_response.json()
    
    file_path = job["file_path"]
    assert os.path.exists(file_path)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["name"] == "Water A"

async def test_export_file_content_csv():
    config = {
        "file_name": "water_data_export",
        "export_format": "csv",
        "scope": "all_water_data"
    }
    create_response = client.post("/api/v1/exports/", json=config)
    job = create_response.json()
    
    file_path = job["file_path"]
    assert os.path.exists(file_path)
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 3 # Header + 2 rows
    assert "id,name,brand,score" in lines[0]
    assert lines[1].strip().startswith("1,") 