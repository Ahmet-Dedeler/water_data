from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.db import models
from app.schemas import challenge as challenge_schema
from app.services.user_service import user_service
from app.services.points_service import points_service
from app.services.level_service import level_service

class ChallengeService:
    def __init__(self):
        self.user_service = user_service
        self.points_service = points_service
        self.level_service = level_service

    def get_challenge(self, db: Session, challenge_id: int) -> Optional[models.Challenge]:
        """Get a challenge by ID"""
        return db.query(models.Challenge).filter(models.Challenge.id == challenge_id).first()

    def get_challenges(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        challenge_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_by_user: Optional[bool] = None
    ) -> List[models.Challenge]:
        """Get challenges with filtering options"""
        query = db.query(models.Challenge)
        
        if category:
            query = query.filter(models.Challenge.category == category)
        if difficulty:
            query = query.filter(models.Challenge.difficulty_level == difficulty)
        if challenge_type:
            query = query.filter(models.Challenge.challenge_type == challenge_type)
        if is_active is not None:
            query = query.filter(models.Challenge.is_active == is_active)
        if created_by_user is not None:
            if created_by_user:
                query = query.filter(models.Challenge.created_by_user_id.isnot(None))
            else:
                query = query.filter(models.Challenge.created_by_user_id.is_(None))
        
        return query.offset(skip).limit(limit).all()

    def create_challenge(self, db: Session, challenge: challenge_schema.ChallengeCreate, creator_id: Optional[int] = None) -> models.Challenge:
        """Create a new challenge"""
        challenge_data = challenge.model_dump()
        challenge_data['created_by_user_id'] = creator_id
        
        db_challenge = models.Challenge(**challenge_data)
        db.add(db_challenge)
        db.commit()
        db.refresh(db_challenge)
        
        # Award points to creator if it's a user-created challenge
        if creator_id:
            self.points_service.add_points(db, creator_id, 50)  # 50 points for creating a challenge
        
        return db_challenge

    def update_challenge(self, db: Session, challenge_id: int, challenge_update: challenge_schema.ChallengeUpdate) -> Optional[models.Challenge]:
        """Update a challenge"""
        db_challenge = self.get_challenge(db, challenge_id)
        if not db_challenge:
            return None
        
        update_data = challenge_update.model_dump(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_challenge, field, value)
        
        db.commit()
        db.refresh(db_challenge)
        return db_challenge

    def delete_challenge(self, db: Session, challenge_id: int) -> bool:
        """Delete a challenge"""
        db_challenge = self.get_challenge(db, challenge_id)
        if not db_challenge:
            return False
        
        db.delete(db_challenge)
        db.commit()
        return True

    def get_active_challenges(self, db: Session) -> List[models.Challenge]:
        """Get all active challenges"""
        now = datetime.utcnow()
        return db.query(models.Challenge).filter(
            models.Challenge.is_active == True,
            models.Challenge.start_date <= now,
            models.Challenge.end_date >= now
        ).all()

    def get_popular_challenges(self, db: Session, limit: int = 10) -> List[models.Challenge]:
        """Get popular challenges based on participation"""
        return db.query(models.Challenge).join(
            models.UserChallenge
        ).group_by(models.Challenge.id).order_by(
            desc(func.count(models.UserChallenge.id))
        ).limit(limit).all()

    def join_challenge(self, db: Session, user_id: int, challenge_id: int) -> Optional[models.UserChallenge]:
        """Join a challenge"""
        # Check if user is already in challenge
        existing_uc = db.query(models.UserChallenge).filter_by(
            user_id=user_id, challenge_id=challenge_id
        ).first()
        if existing_uc:
            return existing_uc

        # Check if challenge exists and is active
        challenge = self.get_challenge(db, challenge_id)
        if not challenge or not challenge.is_active:
            return None

        # Check if challenge has started
        if challenge.start_date > datetime.utcnow():
            return None

        # Check if challenge is full
        if challenge.max_participants:
            participant_count = db.query(models.UserChallenge).filter_by(
                challenge_id=challenge_id
            ).count()
            if participant_count >= challenge.max_participants:
                return None

        # Check if user has enough points for entry fee
        if challenge.entry_fee_points > 0:
            user_profile = self.user_service.get_user_profile(db, user_id)
            if not user_profile or user_profile.points < challenge.entry_fee_points:
                return None
            
            # Deduct entry fee
            self.points_service.subtract_points(db, user_id, challenge.entry_fee_points)

        db_user_challenge = models.UserChallenge(
            user_id=user_id, 
            challenge_id=challenge_id,
            joined_at=datetime.utcnow()
        )
        db.add(db_user_challenge)
        db.commit()
        db.refresh(db_user_challenge)
        return db_user_challenge

    def leave_challenge(self, db: Session, user_id: int, challenge_id: int) -> bool:
        """Leave/abandon a challenge"""
        user_challenge = db.query(models.UserChallenge).filter_by(
            user_id=user_id, challenge_id=challenge_id
        ).first()
        
        if not user_challenge or user_challenge.completed_at:
            return False
        
        user_challenge.is_abandoned = True
        user_challenge.abandoned_at = datetime.utcnow()
        db.commit()
        return True

    def update_challenge_progress(self, db: Session, user_id: int, challenge_type: str, value: float):
        """Update progress for all active challenges of a certain type for a user"""
        active_challenges = self.get_active_challenges(db)
        user_challenges = db.query(models.UserChallenge).filter(
            models.UserChallenge.user_id == user_id,
            models.UserChallenge.challenge_id.in_([c.id for c in active_challenges if c.challenge_type == challenge_type]),
            models.UserChallenge.completed_at.is_(None),
            models.UserChallenge.is_abandoned == False
        ).all()

        for uc in user_challenges:
            # Update progress based on challenge type
            if challenge_type == "total_volume":
                uc.progress += value
            elif challenge_type == "streak_days":
                # This would be updated from the streak service
                pass
            elif challenge_type == "daily_goal":
                # Check if daily goal was met
                if value >= uc.challenge.goal:
                    uc.progress += 1
            elif challenge_type == "consistency":
                # This would be calculated based on logging frequency
                pass
            
            # Check if challenge is completed
            if uc.progress >= uc.challenge.goal and not uc.completed_at:
                uc.completed_at = datetime.utcnow()
                uc.points_earned = uc.challenge.reward_points
                uc.xp_earned = uc.challenge.reward_xp
                
                # Award points and XP
                if uc.challenge.reward_points > 0:
                    self.points_service.add_points(db, user_id, uc.challenge.reward_points)
                if uc.challenge.reward_xp > 0:
                    self.level_service.add_xp(db, user_id, uc.challenge.reward_xp)
            
            db.add(uc)
        
        db.commit()

    def get_user_challenges(self, db: Session, user_id: int, include_completed: bool = True) -> List[models.UserChallenge]:
        """Get all challenges for a user"""
        query = db.query(models.UserChallenge).filter(
            models.UserChallenge.user_id == user_id
        )
        
        if not include_completed:
            query = query.filter(models.UserChallenge.completed_at.is_(None))
        
        return query.all()

    def get_challenge_leaderboard(self, db: Session, challenge_id: int, limit: int = 20) -> challenge_schema.ChallengeLeaderboard:
        """Get leaderboard for a specific challenge"""
        challenge = self.get_challenge(db, challenge_id)
        if not challenge:
            return None

        # Get user challenges ordered by progress
        user_challenges = db.query(
            models.UserChallenge.user_id,
            models.UserChallenge.progress,
            models.UserChallenge.completed_at,
            models.User.username
        ).join(
            models.User, models.UserChallenge.user_id == models.User.id
        ).filter(
            models.UserChallenge.challenge_id == challenge_id,
            models.UserChallenge.is_abandoned == False
        ).order_by(
            desc(models.UserChallenge.progress),
            models.UserChallenge.completed_at.asc()
        ).limit(limit).all()

        # Calculate completion rate
        total_participants = db.query(models.UserChallenge).filter(
            models.UserChallenge.challenge_id == challenge_id
        ).count()
        
        completed_participants = db.query(models.UserChallenge).filter(
            models.UserChallenge.challenge_id == challenge_id,
            models.UserChallenge.completed_at.isnot(None)
        ).count()
        
        completion_rate = (completed_participants / total_participants * 100) if total_participants > 0 else 0

        # Format leaderboard entries
        entries = []
        for i, uc in enumerate(user_challenges):
            entries.append({
                'rank': i + 1,
                'user_id': uc.user_id,
                'username': uc.username,
                'progress': uc.progress,
                'percentage': (uc.progress / challenge.goal * 100) if challenge.goal > 0 else 0,
                'completed': uc.completed_at is not None,
                'completed_at': uc.completed_at
            })

        return challenge_schema.ChallengeLeaderboard(
            challenge_id=challenge_id,
            challenge_name=challenge.name,
            entries=entries,
            total_participants=total_participants,
            completion_rate=completion_rate
        )

    def get_challenge_stats(self, db: Session) -> challenge_schema.ChallengeStats:
        """Get overall challenge statistics"""
        total_challenges = db.query(models.Challenge).count()
        active_challenges = db.query(models.Challenge).filter(
            models.Challenge.is_active == True,
            models.Challenge.start_date <= datetime.utcnow(),
            models.Challenge.end_date >= datetime.utcnow()
        ).count()
        
        completed_challenges = db.query(models.Challenge).filter(
            models.Challenge.end_date < datetime.utcnow()
        ).count()
        
        # Calculate user participation rate
        total_users = db.query(models.User).count()
        participating_users = db.query(func.count(func.distinct(models.UserChallenge.user_id))).scalar()
        user_participation_rate = (participating_users / total_users * 100) if total_users > 0 else 0
        
        # Calculate average completion rate
        challenge_completion_rates = db.query(
            models.Challenge.id,
            func.count(models.UserChallenge.id).label('total_participants'),
            func.sum(func.case([(models.UserChallenge.completed_at.isnot(None), 1)], else_=0)).label('completed_participants')
        ).outerjoin(
            models.UserChallenge, models.Challenge.id == models.UserChallenge.challenge_id
        ).group_by(models.Challenge.id).all()
        
        completion_rates = []
        for ccr in challenge_completion_rates:
            if ccr.total_participants > 0:
                completion_rates.append(ccr.completed_participants / ccr.total_participants * 100)
        
        average_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # Get most popular challenge type
        popular_type = db.query(
            models.Challenge.challenge_type,
            func.count(models.UserChallenge.id).label('participant_count')
        ).outerjoin(
            models.UserChallenge, models.Challenge.id == models.UserChallenge.challenge_id
        ).group_by(models.Challenge.challenge_type).order_by(
            desc('participant_count')
        ).first()
        
        most_popular_challenge_type = popular_type.challenge_type if popular_type else "None"
        
        return challenge_schema.ChallengeStats(
            total_challenges=total_challenges,
            active_challenges=active_challenges,
            completed_challenges=completed_challenges,
            user_participation_rate=user_participation_rate,
            average_completion_rate=average_completion_rate,
            most_popular_challenge_type=most_popular_challenge_type
        )

    def get_user_challenge_progress(self, db: Session, user_id: int, challenge_id: int) -> Optional[challenge_schema.ChallengeProgress]:
        """Get detailed progress for a user's challenge"""
        user_challenge = db.query(models.UserChallenge).filter(
            models.UserChallenge.user_id == user_id,
            models.UserChallenge.challenge_id == challenge_id
        ).first()
        
        if not user_challenge:
            return None
        
        challenge = user_challenge.challenge
        
        # Calculate days remaining
        now = datetime.utcnow()
        days_remaining = (challenge.end_date - now).days if challenge.end_date > now else 0
        
        # Calculate percentage complete
        percentage_complete = (user_challenge.progress / challenge.goal * 100) if challenge.goal > 0 else 0
        
        # Get user's rank in the challenge
        rank = db.query(func.count(models.UserChallenge.id)).filter(
            models.UserChallenge.challenge_id == challenge_id,
            models.UserChallenge.progress > user_challenge.progress,
            models.UserChallenge.is_abandoned == False
        ).scalar() + 1
        
        return challenge_schema.ChallengeProgress(
            challenge_id=challenge_id,
            challenge_name=challenge.name,
            progress=user_challenge.progress,
            goal=challenge.goal,
            percentage_complete=percentage_complete,
            days_remaining=days_remaining,
            is_completed=user_challenge.completed_at is not None,
            rank=rank,
            points_earned=user_challenge.points_earned,
            xp_earned=user_challenge.xp_earned
        )

    # Team Challenge Methods
    def create_team(self, db: Session, team_data: challenge_schema.ChallengeTeamCreate, leader_id: int) -> models.ChallengeTeam:
        """Create a team for a team challenge"""
        challenge = self.get_challenge(db, team_data.challenge_id)
        if not challenge or not challenge.is_team_challenge:
            return None
        
        db_team = models.ChallengeTeam(
            challenge_id=team_data.challenge_id,
            name=team_data.name,
            leader_id=leader_id
        )
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        return db_team

    def join_team(self, db: Session, user_id: int, team_id: int) -> bool:
        """Join a team"""
        team = db.query(models.ChallengeTeam).filter(models.ChallengeTeam.id == team_id).first()
        if not team:
            return False
        
        # Check if team is full
        member_count = db.query(models.UserChallenge).filter(
            models.UserChallenge.team_id == team_id
        ).count()
        
        if member_count >= team.challenge.team_size:
            return False
        
        # Join the challenge first
        user_challenge = self.join_challenge(db, user_id, team.challenge_id)
        if not user_challenge:
            return False
        
        # Assign to team
        user_challenge.team_id = team_id
        db.commit()
        return True

    # Invitation Methods
    def send_invitation(self, db: Session, inviter_id: int, invitee_id: int, challenge_id: int) -> models.ChallengeInvitation:
        """Send a challenge invitation"""
        # Check if invitation already exists
        existing_invitation = db.query(models.ChallengeInvitation).filter(
            models.ChallengeInvitation.inviter_id == inviter_id,
            models.ChallengeInvitation.invitee_id == invitee_id,
            models.ChallengeInvitation.challenge_id == challenge_id,
            models.ChallengeInvitation.status == 'pending'
        ).first()
        
        if existing_invitation:
            return existing_invitation
        
        invitation = models.ChallengeInvitation(
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            challenge_id=challenge_id
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    def respond_to_invitation(self, db: Session, invitation_id: int, response: str) -> bool:
        """Respond to a challenge invitation"""
        invitation = db.query(models.ChallengeInvitation).filter(
            models.ChallengeInvitation.id == invitation_id
        ).first()
        
        if not invitation or invitation.status != 'pending':
            return False
        
        invitation.status = response
        invitation.responded_at = datetime.utcnow()
        
        if response == 'accepted':
            # Join the challenge
            self.join_challenge(db, invitation.invitee_id, invitation.challenge_id)
        
        db.commit()
        return True

    # Comment Methods
    def add_comment(self, db: Session, user_id: int, challenge_id: int, content: str) -> models.ChallengeComment:
        """Add a comment to a challenge"""
        comment = models.ChallengeComment(
            user_id=user_id,
            challenge_id=challenge_id,
            content=content
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    def get_comments(self, db: Session, challenge_id: int, limit: int = 50) -> List[models.ChallengeComment]:
        """Get comments for a challenge"""
        return db.query(models.ChallengeComment).filter(
            models.ChallengeComment.challenge_id == challenge_id
        ).order_by(desc(models.ChallengeComment.created_at)).limit(limit).all()

challenge_service = ChallengeService() 