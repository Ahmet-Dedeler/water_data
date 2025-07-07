from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import dependencies
from app.db import models
from app.schemas import challenge as challenge_schema
from app.services.challenge_service import challenge_service
from app.core.auth import get_current_active_user, get_current_admin_user

router = APIRouter()

# Basic Challenge Endpoints
@router.get("/", response_model=List[challenge_schema.Challenge])
def get_challenges(
    db: Session = Depends(dependencies.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    challenge_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    created_by_user: Optional[bool] = Query(None)
):
    """Get challenges with filtering options"""
    return challenge_service.get_challenges(
        db=db, skip=skip, limit=limit, category=category,
        difficulty=difficulty, challenge_type=challenge_type,
        is_active=is_active, created_by_user=created_by_user
    )

@router.get("/active", response_model=List[challenge_schema.Challenge])
def get_active_challenges(db: Session = Depends(dependencies.get_db)):
    """Get all active challenges"""
    return challenge_service.get_active_challenges(db)

@router.get("/popular", response_model=List[challenge_schema.Challenge])
def get_popular_challenges(
    db: Session = Depends(dependencies.get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get popular challenges based on participation"""
    return challenge_service.get_popular_challenges(db, limit)

@router.get("/stats", response_model=challenge_schema.ChallengeStats)
def get_challenge_stats(db: Session = Depends(dependencies.get_db)):
    """Get overall challenge statistics"""
    return challenge_service.get_challenge_stats(db)

@router.post("/", response_model=challenge_schema.Challenge, status_code=201)
def create_challenge(
    challenge: challenge_schema.ChallengeCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a new challenge (users can create their own challenges)"""
    return challenge_service.create_challenge(db, challenge=challenge, creator_id=current_user.id)

@router.post("/admin", response_model=challenge_schema.Challenge, status_code=201)
def create_system_challenge(
    challenge: challenge_schema.ChallengeCreate,
    db: Session = Depends(dependencies.get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    """Create a system challenge (admin only)"""
    return challenge_service.create_challenge(db, challenge=challenge, creator_id=None)

@router.get("/{challenge_id}", response_model=challenge_schema.Challenge)
def get_challenge(challenge_id: int, db: Session = Depends(dependencies.get_db)):
    """Get a specific challenge by ID"""
    db_challenge = challenge_service.get_challenge(db, challenge_id=challenge_id)
    if db_challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return db_challenge

@router.put("/{challenge_id}", response_model=challenge_schema.Challenge)
def update_challenge(
    challenge_id: int,
    challenge_update: challenge_schema.ChallengeUpdate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update a challenge (only creator or admin can update)"""
    db_challenge = challenge_service.get_challenge(db, challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Check if user can update this challenge
    if db_challenge.created_by_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this challenge")
    
    updated_challenge = challenge_service.update_challenge(db, challenge_id, challenge_update)
    if not updated_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return updated_challenge

@router.delete("/{challenge_id}")
def delete_challenge(
    challenge_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete a challenge (only creator or admin can delete)"""
    db_challenge = challenge_service.get_challenge(db, challenge_id)
    if not db_challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Check if user can delete this challenge
    if db_challenge.created_by_user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this challenge")
    
    success = challenge_service.delete_challenge(db, challenge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return {"message": "Challenge deleted successfully"}

# Challenge Participation Endpoints
@router.post("/{challenge_id}/join", response_model=challenge_schema.UserChallenge)
def join_challenge(
    challenge_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Join a challenge"""
    user_challenge = challenge_service.join_challenge(db, user_id=current_user.id, challenge_id=challenge_id)
    if not user_challenge:
        raise HTTPException(status_code=400, detail="Unable to join challenge")
    
    return user_challenge

@router.post("/{challenge_id}/leave")
def leave_challenge(
    challenge_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Leave/abandon a challenge"""
    success = challenge_service.leave_challenge(db, user_id=current_user.id, challenge_id=challenge_id)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to leave challenge")
    
    return {"message": "Challenge abandoned successfully"}

@router.get("/{challenge_id}/leaderboard", response_model=challenge_schema.ChallengeLeaderboard)
def get_challenge_leaderboard(
    challenge_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(dependencies.get_db)
):
    """Get leaderboard for a specific challenge"""
    leaderboard = challenge_service.get_challenge_leaderboard(db, challenge_id, limit)
    if not leaderboard:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    return leaderboard

@router.get("/{challenge_id}/progress", response_model=challenge_schema.ChallengeProgress)
def get_my_challenge_progress(
    challenge_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get current user's progress in a specific challenge"""
    progress = challenge_service.get_user_challenge_progress(db, current_user.id, challenge_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Challenge progress not found")
    
    return progress

# User Challenge Management
@router.get("/me/challenges", response_model=List[challenge_schema.UserChallenge])
def get_my_challenges(
    include_completed: bool = Query(True),
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get current user's challenges"""
    return challenge_service.get_user_challenges(db, current_user.id, include_completed)

@router.get("/me/created", response_model=List[challenge_schema.Challenge])
def get_my_created_challenges(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """Get challenges created by current user"""
    return challenge_service.get_challenges(
        db, created_by_user=True, skip=0, limit=100
    )

# Team Challenge Endpoints
@router.post("/{challenge_id}/teams", response_model=challenge_schema.ChallengeTeam)
def create_team(
    challenge_id: int,
    team_data: challenge_schema.ChallengeTeamCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a team for a team challenge"""
    team_data.challenge_id = challenge_id
    team = challenge_service.create_team(db, team_data, current_user.id)
    if not team:
        raise HTTPException(status_code=400, detail="Unable to create team")
    
    return team

@router.post("/teams/{team_id}/join")
def join_team(
    team_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Join a team"""
    success = challenge_service.join_team(db, current_user.id, team_id)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to join team")
    
    return {"message": "Team joined successfully"}

# Invitation Endpoints
@router.post("/invitations", response_model=challenge_schema.ChallengeInvitation)
def send_invitation(
    invitation_data: challenge_schema.ChallengeInvitationCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Send a challenge invitation"""
    invitation = challenge_service.send_invitation(
        db, current_user.id, invitation_data.invitee_id, invitation_data.challenge_id
    )
    return invitation

@router.post("/invitations/{invitation_id}/respond")
def respond_to_invitation(
    invitation_id: int,
    response: str = Query(..., regex="^(accepted|declined)$"),
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Respond to a challenge invitation"""
    success = challenge_service.respond_to_invitation(db, invitation_id, response)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to respond to invitation")
    
    return {"message": f"Invitation {response} successfully"}

@router.get("/me/invitations", response_model=List[challenge_schema.ChallengeInvitation])
def get_my_invitations(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get current user's challenge invitations"""
    return db.query(models.ChallengeInvitation).filter(
        models.ChallengeInvitation.invitee_id == current_user.id,
        models.ChallengeInvitation.status == 'pending'
    ).all()

# Comment Endpoints
@router.post("/{challenge_id}/comments", response_model=challenge_schema.ChallengeComment)
def add_comment(
    challenge_id: int,
    comment_data: challenge_schema.ChallengeCommentCreate,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Add a comment to a challenge"""
    comment_data.challenge_id = challenge_id
    comment = challenge_service.add_comment(db, current_user.id, challenge_id, comment_data.content)
    return comment

@router.get("/{challenge_id}/comments", response_model=List[challenge_schema.ChallengeComment])
def get_comments(
    challenge_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(dependencies.get_db)
):
    """Get comments for a challenge"""
    return challenge_service.get_comments(db, challenge_id, limit) 