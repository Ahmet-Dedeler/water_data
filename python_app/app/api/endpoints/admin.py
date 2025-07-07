from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db
from app.core.auth import get_current_admin_user
from app.services.admin_service import admin_service
from app.models.admin import AdminDashboardStats, UserAdminView
from app.models.user import User
from app.schemas.admin import SiteStats, FullUserOut
from app.schemas.common import Message

router = APIRouter()

@router.get("/admin/dashboard-stats", response_model=AdminDashboardStats, dependencies=[Depends(get_current_admin_user)])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """[Admin] Get statistics for the admin dashboard."""
    return admin_service.get_dashboard_stats(db)

@router.get("/admin/users", response_model=List[UserAdminView], dependencies=[Depends(get_current_admin_user)])
def list_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """[Admin] Get a paginated list of all users."""
    users = admin_service.list_users(db, skip=(page - 1) * size, limit=size)
    return [UserAdminView.model_validate(user) for user in users]

@router.post("/admin/users/{user_id}/ban", response_model=UserAdminView, dependencies=[Depends(get_current_admin_user)])
def ban_user(user_id: int, db: Session = Depends(get_db)):
    """[Admin] Ban a user, deactivating their account and API keys."""
    user = admin_service.ban__user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserAdminView.model_validate(user)

@router.post("/admin/users/{user_id}/unban", response_model=UserAdminView, dependencies=[Depends(get_current_admin_user)])
def unban_user(user_id: int, db: Session = Depends(get_db)):
    """[Admin] Un-ban a user, reactivating their account."""
    user = admin_service.unban_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserAdminView.model_validate(user)

@router.delete("/admin/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_admin_user)])
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    """[Admin] Delete a comment for moderation."""
    success = admin_service.delete_comment(db, comment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    return 

@router.get(
    "/stats",
    response_model=SiteStats,
    summary="Get site-wide statistics",
    description="Retrieves a dashboard of statistics for the entire application. (Admin only)",
)
def get_site_statistics(
    db: Session = Depends(get_db),
    admin_user: FullUserOut = Depends(get_current_admin_user)
):
    return admin_service.get_site_stats(db)

@router.get(
    "/users",
    response_model=List[FullUserOut],
    summary="List all users",
    description="Retrieves a paginated list of all users in the system. (Admin only)",
)
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: FullUserOut = Depends(get_current_admin_user)
):
    return admin_service.get_all_users(db, skip=skip, limit=limit)

@router.post(
    "/users/{user_id}/ban",
    response_model=Message,
    summary="Ban a user",
    description="Bans a user, preventing them from logging in or using the API. (Admin only)",
    responses={
        404: {"description": "User not found"},
    }
)
def ban_user_new(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: FullUserOut = Depends(get_current_admin_user)
):
    if not admin_service.ban_user(db, user_id=user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": f"User {user_id} has been banned."}

@router.post(
    "/users/{user_id}/unban",
    response_model=Message,
    summary="Unban a user",
    description="Reverses a ban on a user. (Admin only)",
    responses={
        404: {"description": "User not found"},
    }
)
def unban_user_new(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: FullUserOut = Depends(get_current_admin_user)
):
    if not admin_service.unban_user(db, user_id=user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": f"User {user_id} has been unbanned."}

@router.delete(
    "/comments/{comment_id}",
    response_model=Message,
    summary="Delete a comment",
    description="Permanently deletes a comment by its ID. (Admin only)",
    responses={
        404: {"description": "Comment not found"},
    }
)
def delete_comment_new(
    comment_id: int,
    db: Session = Depends(get_db),
    admin_user: FullUserOut = Depends(get_current_admin_user)
):
    if not admin_service.delete_comment(db, comment_id=comment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return {"message": f"Comment {comment_id} has been deleted."} 