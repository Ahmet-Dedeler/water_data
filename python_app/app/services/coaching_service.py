"""
Service for hydration coaching with AI-powered personalization and recommendations.
"""
# imports
import json
import logging
import random
import uuid
from collections import defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from statistics import mean, median

from app.models.coaching import (
    CoachingTip, CoachingSession, CoachingProfile, CoachingRecommendation,
    CoachingAnalytics, PersonalizationFactor, CoachingLevel, CoachingStyle,
    TipCategory, CoachingSessionType, CoachingTrigger
)
from app.schemas.coaching import (
    CoachingTipCreate, CoachingTipUpdate, CoachingSessionCreate,
    CoachingSessionFeedback, CoachingProfileCreate, CoachingProfileUpdate,
    CoachingRecommendationCreate, CoachingRecommendationFeedback,
    PersonalizedTipRequest, CoachingTipFilter, CoachingSessionFilter
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CoachingService(BaseService):
    """Service for managing hydration coaching and AI-powered recommendations."""

    def __init__(self):
        super().__init__()
        self.data_dir = Path("app/data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Data files
        self.tips_file = self.data_dir / "coaching_tips.json"
        self.sessions_file = self.data_dir / "coaching_sessions.json"
        self.profiles_file = self.data_dir / "coaching_profiles.json"
        self.recommendations_file = self.data_dir / "coaching_recommendations.json"
        self.analytics_file = self.data_dir / "coaching_analytics.json"
        
        # Initialize default tips if not exists
        self._initialize_default_tips()

    async def _load_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        if not file_path.exists():
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return []

    async def _save_data(self, file_path: Path, data: List[Dict[str, Any]]):
        """Save data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {e}")
            raise

    def _initialize_default_tips(self):
        """Initialize default coaching tips if file doesn't exist."""
        if self.tips_file.exists():
            return
            
        default_tips = [
            {
                "id": str(uuid.uuid4()),
                "category": "hydration_timing",
                "title": "Start Your Day with Water",
                "content": "Begin each morning with a large glass of water to kickstart your hydration and metabolism. Your body loses water overnight through breathing and sweating, so replenishing first thing helps you start the day energized.",
                "short_description": "Drink water first thing in the morning",
                "coaching_level": ["beginner", "intermediate"],
                "coaching_style": ["encouraging", "motivational"],
                "triggers": ["new_user", "missed_goal"],
                "personalization_tags": ["morning_routine", "energy_boost"],
                "min_user_level": 1,
                "seasonal": False,
                "time_sensitive": True,
                "effectiveness_score": 0.85,
                "usage_count": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "category": "habit_building",
                "title": "Use Visual Cues",
                "content": "Place a water bottle in visible locations around your home and workspace. Visual reminders are powerful triggers for building lasting hydration habits. When you see the bottle, you're more likely to drink.",
                "short_description": "Keep water bottles visible as reminders",
                "coaching_level": ["beginner", "intermediate", "advanced"],
                "coaching_style": ["casual", "scientific", "encouraging"],
                "triggers": ["habit_formation", "user_request"],
                "personalization_tags": ["visual_learner", "habit_building"],
                "min_user_level": 1,
                "seasonal": False,
                "time_sensitive": False,
                "effectiveness_score": 0.78,
                "usage_count": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "category": "motivation",
                "title": "Celebrate Small Wins",
                "content": "Acknowledge every glass of water as a victory toward your health goals. Small, consistent actions compound into significant results. Each sip is an investment in your wellbeing and energy levels.",
                "short_description": "Recognize progress with each glass",
                "coaching_level": ["beginner", "intermediate"],
                "coaching_style": ["motivational", "encouraging"],
                "triggers": ["goal_achieved", "motivation_boost"],
                "personalization_tags": ["motivation", "positive_reinforcement"],
                "min_user_level": 1,
                "seasonal": False,
                "time_sensitive": False,
                "effectiveness_score": 0.82,
                "usage_count": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True
            }
        ]
        
        try:
            with open(self.tips_file, 'w', encoding='utf-8') as f:
                json.dump(default_tips, f, indent=2, ensure_ascii=False)
            logger.info(f"Initialized {len(default_tips)} default coaching tips")
        except Exception as e:
            logger.error(f"Error initializing default tips: {e}")

    # Coaching Tips Management
    async def create_tip(self, tip_data: CoachingTipCreate) -> CoachingTip:
        """Create a new coaching tip."""
        tips = await self._load_data(self.tips_file)
        
        tip = CoachingTip(
            id=str(uuid.uuid4()),
            **tip_data.dict()
        )
        
        tips.append(tip.dict())
        await self._save_data(self.tips_file, tips)
        
        logger.info(f"Created coaching tip: {tip.id}")
        return tip

    async def get_tip(self, tip_id: str) -> Optional[CoachingTip]:
        """Get a specific coaching tip."""
        tips = await self._load_data(self.tips_file)
        tip_data = next((t for t in tips if t['id'] == tip_id), None)
        return CoachingTip(**tip_data) if tip_data else None

    async def update_tip(self, tip_id: str, update_data: CoachingTipUpdate) -> Optional[CoachingTip]:
        """Update a coaching tip."""
        tips = await self._load_data(self.tips_file)
        tip_index = next((i for i, t in enumerate(tips) if t['id'] == tip_id), None)
        
        if tip_index is None:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        tips[tip_index].update(update_dict)
        tips[tip_index]['updated_at'] = datetime.utcnow().isoformat()
        
        await self._save_data(self.tips_file, tips)
        
        logger.info(f"Updated coaching tip: {tip_id}")
        return CoachingTip(**tips[tip_index])

    async def delete_tip(self, tip_id: str) -> bool:
        """Delete a coaching tip."""
        tips = await self._load_data(self.tips_file)
        initial_len = len(tips)
        
        tips = [t for t in tips if t['id'] != tip_id]
        
        if len(tips) < initial_len:
            await self._save_data(self.tips_file, tips)
            logger.info(f"Deleted coaching tip: {tip_id}")
            return True
        return False

    async def get_tips(
        self,
        filter_data: Optional[CoachingTipFilter] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[CoachingTip], int]:
        """Get coaching tips with filtering."""
        tips = await self._load_data(self.tips_file)
        
        # Apply filters
        if filter_data:
            if filter_data.category:
                tips = [t for t in tips if t.get('category') == filter_data.category]
            if filter_data.coaching_level:
                tips = [t for t in tips if any(level in t.get('coaching_level', []) for level in filter_data.coaching_level)]
            if filter_data.coaching_style:
                tips = [t for t in tips if any(style in t.get('coaching_style', []) for style in filter_data.coaching_style)]
            if filter_data.triggers:
                tips = [t for t in tips if any(trigger in t.get('triggers', []) for trigger in filter_data.triggers)]
            if filter_data.is_active is not None:
                tips = [t for t in tips if t.get('is_active') == filter_data.is_active]
            if filter_data.min_effectiveness_score is not None:
                tips = [t for t in tips if t.get('effectiveness_score', 0) >= filter_data.min_effectiveness_score]
            if filter_data.search_query:
                query = filter_data.search_query.lower()
                tips = [t for t in tips if query in t.get('title', '').lower() or query in t.get('content', '').lower()]
        
        total = len(tips)
        
        # Apply pagination
        tips = tips[skip:skip + limit]
        
        return [CoachingTip(**tip) for tip in tips], total

    async def get_personalized_tips(
        self,
        user_id: int,
        request: PersonalizedTipRequest
    ) -> List[CoachingTip]:
        """Get personalized tips for a user using AI-powered selection."""
        profile = await self.get_coaching_profile(user_id)
        if not profile:
            # Create default profile if none exists
            profile = await self.create_coaching_profile(user_id, CoachingProfileCreate())
        
        tips = await self._load_data(self.tips_file)
        
        # Filter tips based on user profile and request
        suitable_tips = []
        for tip_data in tips:
            if not tip_data.get('is_active', True):
                continue
                
            tip = CoachingTip(**tip_data)
            
            # Check category filter
            if request.category and tip.category != request.category:
                continue
                
            # Check trigger filter
            if request.trigger and request.trigger not in tip.triggers:
                continue
                
            # Check user level
            if tip.min_user_level > profile.total_sessions + 1:
                continue
                
            # Check coaching level compatibility
            if tip.coaching_level and profile.coaching_level not in tip.coaching_level:
                continue
                
            # Check coaching style compatibility
            if tip.coaching_style and profile.coaching_style not in tip.coaching_style:
                continue
                
            # Check seasonal filter
            if not request.include_seasonal and tip.seasonal:
                continue
                
            # Check time-sensitive filter
            if not request.include_time_sensitive and tip.time_sensitive:
                continue
            
            suitable_tips.append(tip)
        
        # AI-powered personalization scoring
        scored_tips = []
        for tip in suitable_tips:
            score = await self._calculate_personalization_score(tip, profile)
            scored_tips.append((tip, score))
        
        # Sort by personalization score and return top results
        scored_tips.sort(key=lambda x: x[1], reverse=True)
        selected_tips = [tip for tip, score in scored_tips[:request.limit]]
        
        # Update usage count for selected tips
        await self._update_tip_usage(selected_tips)
        
        return selected_tips

    async def _calculate_personalization_score(
        self,
        tip: CoachingTip,
        profile: CoachingProfile
    ) -> float:
        """Calculate AI-powered personalization score for a tip."""
        score = 0.0
        
        # Base effectiveness score
        score += tip.effectiveness_score * 0.3
        
        # Coaching level match
        if profile.coaching_level in tip.coaching_level:
            score += 0.2
        
        # Coaching style match
        if profile.coaching_style in tip.coaching_style:
            score += 0.2
        
        # Personalization tags match
        user_tags = set(profile.motivation_factors + profile.challenges + profile.goals)
        tip_tags = set(tip.personalization_tags)
        tag_overlap = len(user_tags.intersection(tip_tags))
        if user_tags:
            score += (tag_overlap / len(user_tags)) * 0.15
        
        # Recency and variety bonus
        if tip.usage_count < 5:  # Prefer less used tips for variety
            score += 0.1
        
        # Positive feedback ratio
        total_feedback = tip.positive_feedback + tip.negative_feedback
        if total_feedback > 0:
            feedback_ratio = tip.positive_feedback / total_feedback
            score += feedback_ratio * 0.05
        
        return min(score, 1.0)

    async def _update_tip_usage(self, tips: List[CoachingTip]):
        """Update usage count for tips."""
        all_tips = await self._load_data(self.tips_file)
        tip_ids = {tip.id for tip in tips}
        
        for tip_data in all_tips:
            if tip_data['id'] in tip_ids:
                tip_data['usage_count'] = tip_data.get('usage_count', 0) + 1
                tip_data['updated_at'] = datetime.utcnow().isoformat()
        
        await self._save_data(self.tips_file, all_tips)

    # Coaching Profiles Management
    async def create_coaching_profile(
        self,
        user_id: int,
        profile_data: CoachingProfileCreate
    ) -> CoachingProfile:
        """Create a coaching profile for a user."""
        profiles = await self._load_data(self.profiles_file)
        
        # Check if profile already exists
        existing = next((p for p in profiles if p['user_id'] == user_id), None)
        if existing:
            return CoachingProfile(**existing)
        
        profile = CoachingProfile(
            user_id=user_id,
            **profile_data.dict()
        )
        
        profiles.append(profile.dict())
        await self._save_data(self.profiles_file, profiles)
        
        logger.info(f"Created coaching profile for user: {user_id}")
        return profile

    async def get_coaching_profile(self, user_id: int) -> Optional[CoachingProfile]:
        """Get coaching profile for a user."""
        profiles = await self._load_data(self.profiles_file)
        profile_data = next((p for p in profiles if p['user_id'] == user_id), None)
        return CoachingProfile(**profile_data) if profile_data else None

    async def update_coaching_profile(
        self,
        user_id: int,
        update_data: CoachingProfileUpdate
    ) -> Optional[CoachingProfile]:
        """Update coaching profile for a user."""
        profiles = await self._load_data(self.profiles_file)
        profile_index = next((i for i, p in enumerate(profiles) if p['user_id'] == user_id), None)
        
        if profile_index is None:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        profiles[profile_index].update(update_dict)
        profiles[profile_index]['updated_at'] = datetime.utcnow().isoformat()
        
        await self._save_data(self.profiles_file, profiles)
        
        logger.info(f"Updated coaching profile for user: {user_id}")
        return CoachingProfile(**profiles[profile_index])

    # Coaching Sessions Management
    async def create_coaching_session(
        self,
        user_id: int,
        session_data: CoachingSessionCreate
    ) -> CoachingSession:
        """Create a new coaching session."""
        sessions = await self._load_data(self.sessions_file)
        profile = await self.get_coaching_profile(user_id)
        
        if not profile:
            profile = await self.create_coaching_profile(user_id, CoachingProfileCreate())
        
        # Get personalized tips for the session
        tip_request = PersonalizedTipRequest(
            category=None,
            trigger=session_data.trigger,
            limit=3
        )
        tips = await self.get_personalized_tips(user_id, tip_request)
        
        # Generate personalization factors
        factors = await self._generate_personalization_factors(user_id, profile)
        
        session = CoachingSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tips=tips,
            coaching_level=profile.coaching_level,
            coaching_style=profile.coaching_style,
            personalization_factors=factors,
            **session_data.dict()
        )
        
        sessions.append(session.dict())
        await self._save_data(self.sessions_file, sessions)
        
        # Update profile statistics
        await self._update_profile_after_session(user_id, session)
        
        logger.info(f"Created coaching session: {session.id} for user: {user_id}")
        return session

    async def get_coaching_session(self, session_id: str) -> Optional[CoachingSession]:
        """Get a specific coaching session."""
        sessions = await self._load_data(self.sessions_file)
        session_data = next((s for s in sessions if s['id'] == session_id), None)
        return CoachingSession(**session_data) if session_data else None

    async def complete_coaching_session(
        self,
        session_id: str,
        user_id: int,
        feedback: CoachingSessionFeedback
    ) -> Optional[CoachingSession]:
        """Complete a coaching session with user feedback."""
        sessions = await self._load_data(self.sessions_file)
        session_index = next((i for i, s in enumerate(sessions) if s['id'] == session_id and s['user_id'] == user_id), None)
        
        if session_index is None:
            return None
        
        # Update session with feedback
        session_data = sessions[session_index]
        session_data.update(feedback.dict())
        session_data['completed_at'] = datetime.utcnow().isoformat()
        
        if session_data.get('started_at'):
            start_time = datetime.fromisoformat(session_data['started_at'])
            duration = (datetime.utcnow() - start_time).total_seconds() / 60
            session_data['duration_minutes'] = int(duration)
        
        await self._save_data(self.sessions_file, sessions)
        
        # Update tip feedback based on session satisfaction
        if feedback.satisfaction_rating:
            await self._update_tip_feedback(session_data.get('tips', []), feedback.satisfaction_rating)
        
        logger.info(f"Completed coaching session: {session_id}")
        return CoachingSession(**session_data)

    async def get_user_sessions(
        self,
        user_id: int,
        filter_data: Optional[CoachingSessionFilter] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[CoachingSession], int]:
        """Get coaching sessions for a user."""
        sessions = await self._load_data(self.sessions_file)
        user_sessions = [s for s in sessions if s['user_id'] == user_id]
        
        # Apply filters
        if filter_data:
            if filter_data.session_type:
                user_sessions = [s for s in user_sessions if s.get('session_type') == filter_data.session_type]
            if filter_data.trigger:
                user_sessions = [s for s in user_sessions if s.get('trigger') == filter_data.trigger]
            if filter_data.coaching_level:
                user_sessions = [s for s in user_sessions if s.get('coaching_level') == filter_data.coaching_level]
            if filter_data.coaching_style:
                user_sessions = [s for s in user_sessions if s.get('coaching_style') == filter_data.coaching_style]
            if filter_data.completed is not None:
                if filter_data.completed:
                    user_sessions = [s for s in user_sessions if s.get('completed_at')]
                else:
                    user_sessions = [s for s in user_sessions if not s.get('completed_at')]
            if filter_data.date_from:
                user_sessions = [s for s in user_sessions if datetime.fromisoformat(s['started_at']).date() >= filter_data.date_from]
            if filter_data.date_to:
                user_sessions = [s for s in user_sessions if datetime.fromisoformat(s['started_at']).date() <= filter_data.date_to]
            if filter_data.min_satisfaction_rating:
                user_sessions = [s for s in user_sessions if s.get('satisfaction_rating', 0) >= filter_data.min_satisfaction_rating]
        
        # Sort by start date (newest first)
        user_sessions.sort(key=lambda s: s['started_at'], reverse=True)
        
        total = len(user_sessions)
        user_sessions = user_sessions[skip:skip + limit]
        
        return [CoachingSession(**session) for session in user_sessions], total

    async def _generate_personalization_factors(
        self,
        user_id: int,
        profile: CoachingProfile
    ) -> List[PersonalizationFactor]:
        """Generate personalization factors for a session."""
        factors = []
        
        # User engagement level
        factors.append(PersonalizationFactor(
            factor_type="engagement_score",
            value=profile.engagement_score,
            weight=0.8
        ))
        
        # Session frequency preference
        factors.append(PersonalizationFactor(
            factor_type="session_frequency",
            value=profile.session_frequency,
            weight=0.6
        ))
        
        # Current streak
        factors.append(PersonalizationFactor(
            factor_type="current_streak",
            value=profile.current_streak,
            weight=0.7
        ))
        
        # Goal completion rate
        factors.append(PersonalizationFactor(
            factor_type="goal_completion_rate",
            value=profile.goal_completion_rate,
            weight=0.9
        ))
        
        return factors

    async def _update_profile_after_session(self, user_id: int, session: CoachingSession):
        """Update coaching profile statistics after a session."""
        profiles = await self._load_data(self.profiles_file)
        profile_index = next((i for i, p in enumerate(profiles) if p['user_id'] == user_id), None)
        
        if profile_index is not None:
            profile_data = profiles[profile_index]
            profile_data['total_sessions'] = profile_data.get('total_sessions', 0) + 1
            profile_data['last_session_date'] = session.started_at.date().isoformat()
            profile_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update streak
            last_date = profile_data.get('last_session_date')
            if last_date:
                last_session_date = datetime.fromisoformat(last_date).date()
                today = date.today()
                if (today - last_session_date).days == 1:
                    profile_data['current_streak'] = profile_data.get('current_streak', 0) + 1
                elif (today - last_session_date).days > 1:
                    profile_data['current_streak'] = 1
                
                # Update best streak
                current_streak = profile_data.get('current_streak', 0)
                if current_streak > profile_data.get('best_streak', 0):
                    profile_data['best_streak'] = current_streak
            
            await self._save_data(self.profiles_file, profiles)

    async def _update_tip_feedback(self, tips: List[Dict[str, Any]], satisfaction_rating: int):
        """Update tip feedback based on session satisfaction."""
        all_tips = await self._load_data(self.tips_file)
        tip_ids = {tip['id'] for tip in tips}
        
        for tip_data in all_tips:
            if tip_data['id'] in tip_ids:
                if satisfaction_rating >= 4:
                    tip_data['positive_feedback'] = tip_data.get('positive_feedback', 0) + 1
                elif satisfaction_rating <= 2:
                    tip_data['negative_feedback'] = tip_data.get('negative_feedback', 0) + 1
                
                # Update effectiveness score
                total_feedback = tip_data.get('positive_feedback', 0) + tip_data.get('negative_feedback', 0)
                if total_feedback > 0:
                    positive_ratio = tip_data.get('positive_feedback', 0) / total_feedback
                    # Weighted average with current effectiveness score
                    current_score = tip_data.get('effectiveness_score', 0.5)
                    tip_data['effectiveness_score'] = (current_score * 0.7) + (positive_ratio * 0.3)
                
                tip_data['updated_at'] = datetime.utcnow().isoformat()
        
        await self._save_data(self.tips_file, all_tips)

    # AI-Powered Recommendations
    async def generate_recommendations(self, user_id: int) -> List[CoachingRecommendation]:
        """Generate AI-powered coaching recommendations for a user."""
        profile = await self.get_coaching_profile(user_id)
        if not profile:
            return []
        
        sessions, _ = await self.get_user_sessions(user_id, limit=10)
        
        recommendations = []
        
        # Analyze user patterns and generate recommendations
        if profile.goal_completion_rate < 0.5:
            rec = await self._create_goal_improvement_recommendation(user_id, profile)
            recommendations.append(rec)
        
        if profile.current_streak == 0 and profile.total_sessions > 3:
            rec = await self._create_engagement_recommendation(user_id, profile)
            recommendations.append(rec)
        
        if len(sessions) >= 3:
            rec = await self._create_pattern_based_recommendation(user_id, profile, sessions)
            recommendations.append(rec)
        
        # Save recommendations
        all_recommendations = await self._load_data(self.recommendations_file)
        for rec in recommendations:
            all_recommendations.append(rec.dict())
        await self._save_data(self.recommendations_file, all_recommendations)
        
        return recommendations

    async def _create_goal_improvement_recommendation(
        self,
        user_id: int,
        profile: CoachingProfile
    ) -> CoachingRecommendation:
        """Create recommendation for improving goal completion."""
        return CoachingRecommendation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="goal_improvement",
            title="Boost Your Goal Achievement",
            description="Based on your current progress, breaking down your hydration goals into smaller, daily targets could significantly improve your success rate.",
            priority=4,
            confidence_score=0.85,
            reasoning="User's goal completion rate is below 50%, indicating need for more achievable milestones",
            data_points_used=["goal_completion_rate", "total_sessions", "challenges"],
            action_steps=[
                "Set smaller daily hydration targets (e.g., 2 glasses by noon)",
                "Use hourly reminders for the first week",
                "Celebrate each small achievement",
                "Track progress visually with a simple chart"
            ],
            expected_outcome="Improved goal completion rate and sustained motivation",
            timeline="2-3 weeks to see significant improvement",
            expires_at=datetime.utcnow() + timedelta(days=14)
        )

    async def _create_engagement_recommendation(
        self,
        user_id: int,
        profile: CoachingProfile
    ) -> CoachingRecommendation:
        """Create recommendation for improving engagement."""
        return CoachingRecommendation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="engagement_boost",
            title="Rebuild Your Hydration Momentum",
            description="Let's get back on track! Your previous sessions showed great potential. A simple restart strategy can help you regain your hydration momentum.",
            priority=3,
            confidence_score=0.78,
            reasoning="User has broken their streak but has history of engagement",
            data_points_used=["current_streak", "best_streak", "total_sessions"],
            action_steps=[
                "Choose one specific time each day for hydration check-in",
                "Start with just one extra glass of water per day",
                "Use a favorite cup or bottle to make it enjoyable",
                "Set a gentle reminder for your chosen time"
            ],
            expected_outcome="Renewed engagement and streak rebuilding",
            timeline="1 week to restart, 2-3 weeks to establish new routine",
            expires_at=datetime.utcnow() + timedelta(days=10)
        )

    async def _create_pattern_based_recommendation(
        self,
        user_id: int,
        profile: CoachingProfile,
        sessions: List[CoachingSession]
    ) -> CoachingRecommendation:
        """Create recommendation based on user patterns."""
        # Analyze session patterns
        satisfaction_scores = [s.satisfaction_rating for s in sessions if s.satisfaction_rating]
        avg_satisfaction = mean(satisfaction_scores) if satisfaction_scores else 3.0
        
        if avg_satisfaction >= 4.0:
            rec_type = "advanced_techniques"
            title = "Ready for Advanced Strategies"
            description = "Your high engagement suggests you're ready for more sophisticated hydration optimization techniques."
            confidence = 0.9
        else:
            rec_type = "approach_adjustment"
            title = "Let's Adjust Your Approach"
            description = "Based on your session feedback, we can fine-tune your coaching style for better results."
            confidence = 0.75
        
        return CoachingRecommendation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=rec_type,
            title=title,
            description=description,
            priority=3,
            confidence_score=confidence,
            reasoning=f"Based on analysis of {len(sessions)} sessions with average satisfaction of {avg_satisfaction:.1f}",
            data_points_used=["session_satisfaction", "coaching_style", "session_frequency"],
            action_steps=[
                "Experiment with different coaching styles",
                "Adjust session frequency based on your schedule",
                "Focus on strategies that have worked best for you"
            ],
            expected_outcome="Improved satisfaction and better results",
            timeline="2-4 weeks to see optimization effects",
            expires_at=datetime.utcnow() + timedelta(days=21)
        )

    # Analytics and Insights
    async def generate_analytics(
        self,
        user_id: int,
        period_start: date,
        period_end: date
    ) -> CoachingAnalytics:
        """Generate coaching analytics for a user."""
        sessions, _ = await self.get_user_sessions(user_id)
        profile = await self.get_coaching_profile(user_id)
        
        # Filter sessions by period
        period_sessions = [
            s for s in sessions
            if period_start <= s.started_at.date() <= period_end
        ]
        
        completed_sessions = [s for s in period_sessions if s.completed_at]
        
        # Calculate metrics
        total_sessions = len(period_sessions)
        completed_count = len(completed_sessions)
        
        avg_duration = 0.0
        if completed_sessions:
            durations = [s.duration_minutes for s in completed_sessions if s.duration_minutes]
            avg_duration = mean(durations) if durations else 0.0
        
        engagement_rate = completed_count / total_sessions if total_sessions > 0 else 0.0
        
        satisfaction_scores = [s.satisfaction_rating for s in completed_sessions if s.satisfaction_rating]
        avg_satisfaction = mean(satisfaction_scores) if satisfaction_scores else 0.0
        
        # Generate insights
        insights = await self._generate_insights(user_id, period_sessions, profile)
        
        analytics = CoachingAnalytics(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            total_sessions=total_sessions,
            completed_sessions=completed_count,
            average_session_duration=avg_duration,
            engagement_rate=engagement_rate,
            satisfaction_score=avg_satisfaction,
            key_insights=insights,
            recommendations_for_improvement=await self._generate_improvement_recommendations(user_id, period_sessions)
        )
        
        # Save analytics
        all_analytics = await self._load_data(self.analytics_file)
        all_analytics.append(analytics.dict())
        await self._save_data(self.analytics_file, all_analytics)
        
        return analytics

    async def _generate_insights(
        self,
        user_id: int,
        sessions: List[CoachingSession],
        profile: Optional[CoachingProfile]
    ) -> List[str]:
        """Generate AI insights from user data."""
        insights = []
        
        if not sessions:
            insights.append("Start with regular coaching sessions to build personalized insights.")
            return insights
        
        # Session frequency insights
        if len(sessions) >= 4:
            dates = [s.started_at.date() for s in sessions]
            date_diffs = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
            avg_gap = mean(date_diffs) if date_diffs else 0
            
            if avg_gap <= 2:
                insights.append("You maintain excellent session consistency with regular engagement.")
            elif avg_gap <= 7:
                insights.append("Your weekly session rhythm shows good commitment to improvement.")
            else:
                insights.append("Consider more frequent sessions to maintain momentum and see faster progress.")
        
        # Satisfaction trends
        completed = [s for s in sessions if s.satisfaction_rating]
        if len(completed) >= 3:
            recent_satisfaction = mean([s.satisfaction_rating for s in completed[:3]])
            older_satisfaction = mean([s.satisfaction_rating for s in completed[3:6]]) if len(completed) > 3 else recent_satisfaction
            
            if recent_satisfaction > older_satisfaction + 0.5:
                insights.append("Your satisfaction with coaching sessions is trending upward - great progress!")
            elif recent_satisfaction < older_satisfaction - 0.5:
                insights.append("Recent sessions show lower satisfaction - let's adjust your coaching approach.")
        
        # Goal setting patterns
        goals_set = sum(len(s.goals_set) for s in sessions)
        if goals_set > len(sessions) * 2:
            insights.append("You're excellent at setting goals during sessions - focus on implementation now.")
        elif goals_set < len(sessions) * 0.5:
            insights.append("Setting more specific goals during sessions could boost your progress.")
        
        return insights

    async def _generate_improvement_recommendations(
        self,
        user_id: int,
        sessions: List[CoachingSession]
    ) -> List[str]:
        """Generate improvement recommendations based on session analysis."""
        recommendations = []
        
        if not sessions:
            return ["Complete a few coaching sessions to receive personalized recommendations."]
        
        # Analyze completion rates
        completion_rate = len([s for s in sessions if s.completed_at]) / len(sessions)
        if completion_rate < 0.7:
            recommendations.append("Try shorter, more focused sessions to improve completion rates.")
        
        # Analyze satisfaction patterns
        satisfaction_scores = [s.satisfaction_rating for s in sessions if s.satisfaction_rating]
        if satisfaction_scores:
            avg_satisfaction = mean(satisfaction_scores)
            if avg_satisfaction < 3.5:
                recommendations.append("Experiment with different coaching styles to find what resonates best with you.")
        
        # Analyze engagement patterns
        if len(sessions) >= 5:
            recent_sessions = sessions[:3]
            older_sessions = sessions[3:]
            
            recent_engagement = len([s for s in recent_sessions if s.completed_at]) / len(recent_sessions)
            older_engagement = len([s for s in older_sessions if s.completed_at]) / len(older_sessions)
            
            if recent_engagement < older_engagement - 0.2:
                recommendations.append("Consider adjusting session frequency or style to reignite engagement.")
        
        return recommendations


# Create global instance
coaching_service = CoachingService() 