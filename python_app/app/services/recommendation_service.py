from typing import Optional, List, Dict, Any, Tuple
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
import logging
from collections import defaultdict, Counter

from app.models.recommendation import (
    Recommendation, RecommendationCriteria, RecommendationScore,
    RecommendationReason, RecommendationType, RecommendationRequest,
    RecommendationResponse, UserPreferenceProfile, RecommendationFeedback
)
from app.models.water import WaterData
from app.services.data_service import DataService
from app.services.user_service import user_service
from app.services.review_service import review_service

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating personalized water recommendations."""
    
    def __init__(self):
        self.profiles_file = Path(__file__).parent.parent / "data" / "user_preference_profiles.json"
        self.feedback_file = Path(__file__).parent.parent / "data" / "recommendation_feedback.json"
        self._ensure_data_files()
        self._profiles_cache = None
        self._feedback_cache = None
        self.data_service = DataService()
    
    def _ensure_data_files(self):
        """Ensure recommendation data files exist."""
        data_dir = self.profiles_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [self.profiles_file, self.feedback_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_profiles(self) -> List[Dict]:
        """Load user preference profiles from file."""
        if self._profiles_cache is None:
            try:
                with open(self.profiles_file, 'r') as f:
                    self._profiles_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading profiles: {e}")
                self._profiles_cache = []
        return self._profiles_cache
    
    async def _save_profiles(self, profiles: List[Dict]):
        """Save user preference profiles to file."""
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump(profiles, f, indent=2, default=str)
            self._profiles_cache = profiles
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")
            raise
    
    async def _load_feedback(self) -> List[Dict]:
        """Load recommendation feedback from file."""
        if self._feedback_cache is None:
            try:
                with open(self.feedback_file, 'r') as f:
                    self._feedback_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading feedback: {e}")
                self._feedback_cache = []
        return self._feedback_cache
    
    async def _save_feedback(self, feedback: List[Dict]):
        """Save recommendation feedback to file."""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(feedback, f, indent=2, default=str)
            self._feedback_cache = feedback
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            raise
    
    async def get_user_preference_profile(self, user_id: int) -> Optional[UserPreferenceProfile]:
        """Get or create user preference profile."""
        profiles = await self._load_profiles()
        
        profile_dict = next((p for p in profiles if p['user_id'] == user_id), None)
        if profile_dict:
            return UserPreferenceProfile(**profile_dict)
        
        # Create new profile from user data
        return await self._create_user_profile(user_id)
    
    async def _create_user_profile(self, user_id: int) -> UserPreferenceProfile:
        """Create user preference profile from existing data."""
        # Get user profile and reviews
        user_profile = await user_service.get_user_profile(user_id)
        user_reviews, _ = await review_service.get_reviews_by_user(user_id, limit=100)
        
        # Initialize empty profile
        profile = UserPreferenceProfile(user_id=user_id)
        
        if user_profile:
            # Use explicit preferences
            profile.preferred_health_score_range = (
                user_profile.min_health_score or 80, 100
            )
            
            # Convert user preferences to scoring
            if user_profile.preferred_packaging:
                profile.packaging_preferences = {
                    pkg: 1.0 for pkg in user_profile.preferred_packaging
                }
        
        if user_reviews:
            # Learn from review patterns
            profile = await self._learn_from_reviews(profile, user_reviews)
        
        # Save profile
        profiles = await self._load_profiles()
        profiles.append(profile.dict())
        await self._save_profiles(profiles)
        
        return profile
    
    async def _learn_from_reviews(self, profile: UserPreferenceProfile, reviews: List) -> UserPreferenceProfile:
        """Learn preferences from user reviews."""
        if not reviews:
            return profile
        
        # Analyze brand preferences
        brand_ratings = defaultdict(list)
        packaging_ratings = defaultdict(list)
        
        for review in reviews:
            if review.water_brand:
                brand_ratings[review.water_brand].append(review.rating)
            
            # Get water data to analyze packaging
            try:
                water = await self.data_service.get_water_by_id(review.water_id)
                if water and water.packaging:
                    packaging_ratings[water.packaging].append(review.rating)
            except Exception:
                pass
        
        # Calculate brand affinity
        for brand, ratings in brand_ratings.items():
            avg_rating = sum(ratings) / len(ratings)
            profile.brand_affinity[brand] = min(avg_rating / 5.0, 1.0)
        
        # Calculate packaging preferences
        for packaging, ratings in packaging_ratings.items():
            avg_rating = sum(ratings) / len(ratings)
            profile.packaging_preferences[packaging] = min(avg_rating / 5.0, 1.0)
        
        # Update confidence and metadata
        profile.data_points = len(reviews)
        profile.preference_confidence = min(len(reviews) / 20.0, 1.0)  # Max confidence at 20+ reviews
        profile.last_updated = datetime.utcnow()
        
        return profile
    
    async def generate_recommendations(
        self, 
        user_id: Optional[int] = None,
        request: Optional[RecommendationRequest] = None
    ) -> RecommendationResponse:
        """Generate personalized recommendations."""
        
        # Get all available waters
        waters = await self.data_service.get_all_water_data()
        
        # Get user profile if user is authenticated
        user_profile = None
        preference_profile = None
        if user_id:
            user_profile = await user_service.get_user_profile(user_id)
            preference_profile = await self.get_user_preference_profile(user_id)
        
        # Merge criteria from user profile and request
        criteria = await self._merge_criteria(user_profile, preference_profile, request)
        
        # Filter waters based on criteria
        candidate_waters = await self._filter_waters(waters, criteria, request)
        
        # Generate scores for each water
        scored_waters = []
        for water in candidate_waters:
            score = await self._calculate_recommendation_score(
                water, criteria, preference_profile, user_id
            )
            
            if score.overall > 0.1:  # Minimum threshold
                reason = await self._generate_recommendation_reason(
                    water, criteria, score, preference_profile
                )
                
                recommendation = Recommendation(
                    water=water,
                    score=score,
                    reason=reason,
                    recommendation_type=await self._determine_recommendation_type(
                        water, criteria, score
                    ),
                    confidence=await self._calculate_confidence(score, preference_profile),
                    priority=0,  # Will be set after sorting
                    estimated_cost_per_month=await self._estimate_monthly_cost(water),
                    availability_score=0.9,  # Default availability
                    freshness_score=await self._calculate_freshness_score(water)
                )
                
                scored_waters.append(recommendation)
        
        # Sort by overall score
        scored_waters.sort(key=lambda x: x.score.overall, reverse=True)
        
        # Set priorities and apply diversity
        final_recommendations = await self._apply_diversity_and_ranking(
            scored_waters, criteria, request
        )
        
        # Limit results
        limit = request.limit if request else 10
        final_recommendations = final_recommendations[:limit]
        
        # Set final priorities
        for i, rec in enumerate(final_recommendations):
            rec.priority = i + 1
        
        # Calculate response metadata
        response = RecommendationResponse(
            recommendations=final_recommendations,
            total_analyzed=len(waters),
            criteria_used=criteria.dict() if criteria else {},
            generation_metadata={
                "algorithm_version": "1.0",
                "generation_time_ms": 0,  # Could track actual time
                "user_authenticated": user_id is not None,
                "personalization_level": "high" if preference_profile else "basic"
            },
            average_confidence=sum(r.confidence for r in final_recommendations) / len(final_recommendations) if final_recommendations else 0,
            diversity_score=await self._calculate_diversity_score(final_recommendations),
            personalization_score=0.8 if preference_profile else 0.3
        )
        
        return response
    
    async def _merge_criteria(
        self, 
        user_profile: Optional[Any], 
        preference_profile: Optional[UserPreferenceProfile],
        request: Optional[RecommendationRequest]
    ) -> RecommendationCriteria:
        """Merge criteria from various sources."""
        
        criteria_dict = {}
        
        # Start with user profile preferences
        if user_profile:
            criteria_dict.update({
                'health_goals': user_profile.health_goals,
                'dietary_restrictions': user_profile.dietary_restrictions,
                'avoid_contaminants': user_profile.avoid_contaminants,
                'min_health_score': user_profile.min_health_score,
                'preferred_packaging': user_profile.preferred_packaging,
                'max_budget': user_profile.max_budget
            })
        
        # Add learned preferences
        if preference_profile:
            if preference_profile.brand_affinity:
                top_brands = sorted(
                    preference_profile.brand_affinity.items(),
                    key=lambda x: x[1], reverse=True
                )[:3]
                criteria_dict['preferred_brands'] = [brand for brand, _ in top_brands]
        
        # Override with request criteria
        if request and request.criteria:
            request_criteria = request.criteria.dict(exclude_unset=True)
            criteria_dict.update(request_criteria)
        
        # Remove None values
        criteria_dict = {k: v for k, v in criteria_dict.items() if v is not None}
        
        return RecommendationCriteria(**criteria_dict)
    
    async def _filter_waters(
        self, 
        waters: List[WaterData], 
        criteria: RecommendationCriteria,
        request: Optional[RecommendationRequest]
    ) -> List[WaterData]:
        """Filter waters based on criteria."""
        
        filtered_waters = []
        
        for water in waters:
            # Health score filter
            if criteria.min_health_score and water.score < criteria.min_health_score:
                continue
            
            # Packaging filter
            if criteria.preferred_packaging and water.packaging:
                if water.packaging not in criteria.preferred_packaging:
                    continue
            
            # Brand filter
            if criteria.preferred_brands and water.brand:
                if water.brand.name not in criteria.preferred_brands:
                    continue
            
            # Contaminant avoidance
            if criteria.avoid_contaminants:
                water_contaminants = [ing.name for ing in water.contaminants if ing.name]
                if any(contaminant in water_contaminants for contaminant in criteria.avoid_contaminants):
                    continue
            
            # Exclude specific waters
            if request and request.exclude_water_ids:
                if water.id in request.exclude_water_ids:
                    continue
            
            filtered_waters.append(water)
        
        return filtered_waters
    
    async def _calculate_recommendation_score(
        self,
        water: WaterData,
        criteria: RecommendationCriteria,
        preference_profile: Optional[UserPreferenceProfile],
        user_id: Optional[int]
    ) -> RecommendationScore:
        """Calculate recommendation score for a water."""
        
        # Health match score
        health_match = await self._calculate_health_match(water, criteria)
        
        # Preference match score
        preference_match = await self._calculate_preference_match(water, criteria, preference_profile)
        
        # User similarity score (based on similar users' preferences)
        user_similarity = await self._calculate_user_similarity_score(water, user_id)
        
        # Popularity score (based on reviews and ratings)
        popularity = await self._calculate_popularity_score(water)
        
        # Novelty score (how new/undiscovered this water is)
        novelty = await self._calculate_novelty_score(water, user_id)
        
        # Overall score (weighted combination)
        overall = (
            health_match * 0.3 +
            preference_match * 0.25 +
            user_similarity * 0.2 +
            popularity * 0.15 +
            novelty * 0.1
        )
        
        return RecommendationScore(
            health_match=health_match,
            preference_match=preference_match,
            user_similarity=user_similarity,
            popularity=popularity,
            novelty=novelty,
            overall=overall
        )
    
    async def _calculate_health_match(self, water: WaterData, criteria: RecommendationCriteria) -> float:
        """Calculate health-based matching score."""
        score = 0.0
        factors = 0
        
        # Health score match
        if criteria.min_health_score:
            score_ratio = water.score / 100.0
            if water.score >= criteria.min_health_score:
                score += score_ratio
            else:
                score += score_ratio * 0.5  # Penalty for not meeting minimum
            factors += 1
        
        # Contaminant-free bonus
        if criteria.avoid_contaminants:
            contaminant_free = len(water.contaminants) == 0
            score += 1.0 if contaminant_free else 0.5
            factors += 1
        
        # Health goals alignment
        if criteria.health_goals:
            # Simple keyword matching for now
            health_keywords = {
                'hydration': ['electrolyte', 'mineral'],
                'detox': ['pure', 'filtered'],
                'mineral_balance': ['calcium', 'magnesium', 'mineral']
            }
            
            goal_match = 0.0
            for goal in criteria.health_goals:
                if goal in health_keywords:
                    keywords = health_keywords[goal]
                    water_nutrients = [ing.name.lower() for ing in water.nutrients if ing.name]
                    if any(keyword in ' '.join(water_nutrients) for keyword in keywords):
                        goal_match += 1.0
            
            if criteria.health_goals:
                score += goal_match / len(criteria.health_goals)
                factors += 1
        
        return score / factors if factors > 0 else 0.0
    
    async def _calculate_preference_match(
        self, 
        water: WaterData, 
        criteria: RecommendationCriteria,
        preference_profile: Optional[UserPreferenceProfile]
    ) -> float:
        """Calculate preference-based matching score."""
        score = 0.0
        factors = 0
        
        # Packaging preference
        if criteria.preferred_packaging and water.packaging:
            if water.packaging in criteria.preferred_packaging:
                score += 1.0
            factors += 1
        
        # Brand preference from learned profile
        if preference_profile and preference_profile.brand_affinity and water.brand:
            brand_score = preference_profile.brand_affinity.get(water.brand.name, 0.5)
            score += brand_score
            factors += 1
        
        # Budget considerations
        if criteria.max_budget:
            # Estimate water cost (placeholder logic)
            estimated_cost = 3.0  # Default cost estimate
            if estimated_cost <= criteria.max_budget:
                score += 1.0
            else:
                score += max(0, 1.0 - (estimated_cost - criteria.max_budget) / criteria.max_budget)
            factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    async def _calculate_user_similarity_score(self, water: WaterData, user_id: Optional[int]) -> float:
        """Calculate score based on similar users' preferences."""
        if not user_id:
            return 0.5  # Neutral score for anonymous users
        
        # Placeholder: In a real implementation, this would:
        # 1. Find users with similar preferences/reviews
        # 2. Look at their ratings for this water
        # 3. Calculate similarity-weighted average
        
        return 0.6  # Default similarity score
    
    async def _calculate_popularity_score(self, water: WaterData) -> float:
        """Calculate popularity score based on reviews and ratings."""
        try:
            review_stats = await review_service.get_review_stats(water.id)
            
            if review_stats.total_reviews == 0:
                return 0.3  # Low score for no reviews
            
            # Normalize average rating (1-5 scale to 0-1 scale)
            rating_score = (review_stats.average_rating - 1) / 4
            
            # Review count factor (more reviews = more confidence)
            review_factor = min(review_stats.total_reviews / 50.0, 1.0)  # Cap at 50 reviews
            
            return rating_score * review_factor
            
        except Exception:
            return 0.3  # Default for error cases
    
    async def _calculate_novelty_score(self, water: WaterData, user_id: Optional[int]) -> float:
        """Calculate novelty/discovery score."""
        if not user_id:
            return 0.7  # Higher novelty for anonymous users
        
        # Check if user has reviewed this water
        try:
            user_reviews, _ = await review_service.get_reviews_by_user(user_id, limit=100)
            reviewed_water_ids = {review.water_id for review in user_reviews}
            
            if water.id in reviewed_water_ids:
                return 0.2  # Low novelty for already tried
            else:
                return 0.8  # High novelty for new discovery
                
        except Exception:
            return 0.5  # Default
    
    async def _generate_recommendation_reason(
        self,
        water: WaterData,
        criteria: RecommendationCriteria,
        score: RecommendationScore,
        preference_profile: Optional[UserPreferenceProfile]
    ) -> RecommendationReason:
        """Generate explanation for why this water is recommended."""
        
        # Determine primary reason based on highest scoring factor
        score_factors = {
            'health': score.health_match,
            'preference': score.preference_match,
            'popularity': score.popularity,
            'similarity': score.user_similarity
        }
        
        primary_factor = max(score_factors, key=score_factors.get)
        
        primary_reasons = {
            'health': f"Excellent health match with a score of {water.score:.1f}/100",
            'preference': "Perfect match for your personal preferences",
            'popularity': "Highly rated by other users",
            'similarity': "Recommended by users with similar tastes"
        }
        
        primary_reason = primary_reasons[primary_factor]
        
        # Generate supporting reasons
        supporting_reasons = []
        
        if water.score >= 90:
            supporting_reasons.append(f"Outstanding health score of {water.score:.1f}/100")
        
        if len(water.contaminants) == 0:
            supporting_reasons.append("Completely contaminant-free")
        
        if water.packaging and criteria.preferred_packaging:
            if water.packaging in criteria.preferred_packaging:
                supporting_reasons.append(f"Comes in preferred {water.packaging} packaging")
        
        if len(water.nutrients) > 0:
            top_nutrients = water.nutrients[:2]
            nutrient_names = [n.name for n in top_nutrients if n.name]
            if nutrient_names:
                supporting_reasons.append(f"Rich in {', '.join(nutrient_names)}")
        
        # Health benefits
        health_benefits = []
        for nutrient in water.nutrients[:3]:
            if nutrient.benefits:
                health_benefits.append(nutrient.benefits)
        
        # Match details
        match_details = {
            'health_score': water.score,
            'contaminant_free': len(water.contaminants) == 0,
            'nutrient_count': len(water.nutrients),
            'packaging': water.packaging
        }
        
        return RecommendationReason(
            primary_reason=primary_reason,
            supporting_reasons=supporting_reasons,
            health_benefits=health_benefits,
            match_details=match_details
        )
    
    async def _determine_recommendation_type(
        self, 
        water: WaterData, 
        criteria: RecommendationCriteria,
        score: RecommendationScore
    ) -> RecommendationType:
        """Determine the type of recommendation."""
        
        if score.health_match > 0.8:
            return RecommendationType.HEALTH_BASED
        elif score.preference_match > 0.8:
            return RecommendationType.PREFERENCE_BASED
        elif score.user_similarity > 0.8:
            return RecommendationType.SIMILAR_USERS
        elif score.popularity > 0.8:
            return RecommendationType.TRENDING
        else:
            return RecommendationType.PERSONALIZED
    
    async def _calculate_confidence(
        self, 
        score: RecommendationScore,
        preference_profile: Optional[UserPreferenceProfile]
    ) -> float:
        """Calculate confidence in the recommendation."""
        
        base_confidence = score.overall
        
        # Boost confidence if we have good user profile data
        if preference_profile:
            profile_confidence = preference_profile.preference_confidence
            base_confidence = base_confidence * 0.7 + profile_confidence * 0.3
        
        return min(base_confidence, 1.0)
    
    async def _estimate_monthly_cost(self, water: WaterData) -> float:
        """Estimate monthly cost for this water."""
        # Placeholder: In real implementation, this would use:
        # - Water price data
        # - User's consumption patterns
        # - Regional pricing
        
        base_cost = 2.5  # Base cost per bottle
        
        # Adjust based on health score (premium pricing)
        if water.score > 90:
            base_cost *= 1.5
        elif water.score > 80:
            base_cost *= 1.2
        
        # Assume 30 bottles per month
        return base_cost * 30
    
    async def _calculate_freshness_score(self, water: WaterData) -> float:
        """Calculate how fresh/trending this recommendation is."""
        # Placeholder: Could be based on:
        # - Recent review activity
        # - New product launches
        # - Seasonal trends
        
        return 0.8  # Default freshness
    
    async def _apply_diversity_and_ranking(
        self,
        recommendations: List[Recommendation],
        criteria: RecommendationCriteria,
        request: Optional[RecommendationRequest]
    ) -> List[Recommendation]:
        """Apply diversity and final ranking to recommendations."""
        
        if not recommendations:
            return []
        
        # Get diversity factor
        diversity_factor = 0.5
        if criteria and criteria.diversity_factor:
            diversity_factor = criteria.diversity_factor
        
        if diversity_factor > 0.5:
            # Apply diversity: ensure variety in brands, packaging, etc.
            diverse_recommendations = []
            used_brands = set()
            used_packaging = set()
            
            # First pass: add highest scoring unique items
            for rec in recommendations:
                brand = rec.water.brand.name if rec.water.brand else "Unknown"
                packaging = rec.water.packaging or "Unknown"
                
                if len(diverse_recommendations) < 3:  # Always include top 3
                    diverse_recommendations.append(rec)
                    used_brands.add(brand)
                    used_packaging.add(packaging)
                elif brand not in used_brands or packaging not in used_packaging:
                    diverse_recommendations.append(rec)
                    used_brands.add(brand)
                    used_packaging.add(packaging)
                elif len(diverse_recommendations) < len(recommendations) * 0.8:
                    # Fill remaining spots with high-scoring items
                    diverse_recommendations.append(rec)
            
            return diverse_recommendations
        else:
            # No diversity - return by score only
            return recommendations
    
    async def _calculate_diversity_score(self, recommendations: List[Recommendation]) -> float:
        """Calculate diversity score of recommendation list."""
        if len(recommendations) < 2:
            return 1.0
        
        brands = [r.water.brand.name if r.water.brand else "Unknown" for r in recommendations]
        packaging = [r.water.packaging or "Unknown" for r in recommendations]
        
        brand_diversity = len(set(brands)) / len(brands)
        packaging_diversity = len(set(packaging)) / len(packaging)
        
        return (brand_diversity + packaging_diversity) / 2
    
    async def record_feedback(
        self, 
        user_id: int, 
        recommendation_id: str,
        feedback: RecommendationFeedback
    ) -> bool:
        """Record user feedback on a recommendation."""
        try:
            feedback_list = await self._load_feedback()
            
            feedback_dict = feedback.dict()
            feedback_dict.update({
                'user_id': user_id,
                'recommendation_id': recommendation_id,
                'created_at': datetime.utcnow().isoformat()
            })
            
            feedback_list.append(feedback_dict)
            await self._save_feedback(feedback_list)
            
            # Update user preference profile based on feedback
            await self._update_profile_from_feedback(user_id, feedback)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False
    
    async def _update_profile_from_feedback(
        self, 
        user_id: int, 
        feedback: RecommendationFeedback
    ):
        """Update user preference profile based on feedback."""
        try:
            profiles = await self._load_profiles()
            profile_index = next(
                (i for i, p in enumerate(profiles) if p['user_id'] == user_id), 
                None
            )
            
            if profile_index is not None:
                # Update profile based on feedback
                # This is a simplified update - real implementation would be more sophisticated
                profile = profiles[profile_index]
                profile['last_updated'] = datetime.utcnow().isoformat()
                profile['data_points'] = profile.get('data_points', 0) + 1
                
                await self._save_profiles(profiles)
                
        except Exception as e:
            logger.error(f"Error updating profile from feedback: {e}")


# Global service instance
recommendation_service = RecommendationService() 