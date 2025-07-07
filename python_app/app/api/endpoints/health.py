from fastapi import APIRouter, status, Response, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path
from sqlalchemy.orm import Session

from app.api import dependencies
from app.db import models
from app.schemas import health as health_schema
from app.services.health_service import health_service
from app.core.auth import get_current_active_user

router = APIRouter()

class HealthCheck(BaseModel):
    status: str
    checks: List[Dict[str, str]]

@router.get("/health", response_model=HealthCheck, tags=["Health"])
def get_health_status(response: Response):
    """
    Performs a detailed health check of the application,
    verifying the accessibility of critical data files.
    """
    overall_status = "ok"
    checks = []
    
    # List of critical data files to check
    data_files = [
        "users.json",
        "user_profiles.json",
        "water_data.json",
        "user_water_logs.json",
        "achievements.json",
        "user_achievements.json"
    ]
    
    data_path = Path(__file__).parent.parent / "data"
    
    for file_name in data_files:
        file_path = data_path / file_name
        check = {"component": f"datafile:{file_name}", "status": "ok"}
        try:
            if not file_path.exists():
                check["status"] = "error"
                check["output"] = "File not found."
                overall_status = "error"
            elif not file_path.is_file():
                check["status"] = "error"
                check["output"] = "Path is not a file."
                overall_status = "error"
            # In a real app, you might also check read/write permissions
        except Exception as e:
            check["status"] = "error"
            check["output"] = str(e)
            overall_status = "error"
        
        checks.append(check)
        
    health_data = HealthCheck(status=overall_status, checks=checks)
    
    if overall_status == "error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return health_data 

@router.post("/connect", response_model=health_schema.HealthIntegration)
def connect_health_app(
    integration: health_schema.HealthIntegrationCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Connect a health app for the current user.
    """
    return health_service.create_or_update_integration(db, user_id=current_user.id, integration=integration)

@router.get("/connection", response_model=health_schema.HealthIntegration)
def get_health_app_connection(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Get the current user's health app connection details.
    """
    integration = health_service.get_integration(db, user_id=current_user.id)
    if not integration:
        raise HTTPException(status_code=404, detail="No health app connection found.")
    return integration

@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_health_app(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Disconnect the current user's health app.
    """
    health_service.delete_integration(db, user_id=current_user.id)
    return 