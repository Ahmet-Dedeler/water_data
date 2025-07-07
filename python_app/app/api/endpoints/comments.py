from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, get_current_active_user
from app.services.comment_service import CommentService
from app.models.comment import Comment, CommentCreate
from app.models.user import User

router = APIRouter()
comment_service = CommentService()

@router.post("/achievements/{user_achievement_id}/comments", response_model=Comment, status_code=201)
def post_comment_on_achievement(
    user_achievement_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Post a comment on a specific user achievement."""
    try:
        comment = comment_service.create_comment(db, current_user.id, user_achievement_id, comment_data)
        # Manually construct the response model since the service returns a DB model
        return Comment(
            id=comment.id,
            user_id=comment.user_id,
            user_achievement_id=comment.user_achievement_id,
            content=comment.content,
            created_at=comment.created_at,
            username=comment.user.username,
            profile_picture_url=comment.user.profile.profile_picture_url if comment.user.profile else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/achievements/{user_achievement_id}/comments", response_model=List[Comment])
def get_comments_for_achievement(
    user_achievement_id: int,
    db: Session = Depends(get_db)
):
    """Get all comments for a specific user achievement."""
    comments = comment_service.get_comments_for_achievement(db, user_achievement_id)
    # Manually construct the response model to include user details
    return [
        Comment(
            id=c.id,
            user_id=c.user_id,
            user_achievement_id=c.user_achievement_id,
            content=c.content,
            created_at=c.created_at,
            username=c.user.username,
            profile_picture_url=c.user.profile.profile_picture_url if c.user.profile else None
        ) for c in comments
    ] 