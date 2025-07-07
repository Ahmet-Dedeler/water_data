from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .water import WaterData


class RecommendationType(str, Enum):
    """Types of recommendations."""
    HEALTH_BASED = "health_based"
    PREFERENCE_BASED = "preference_based"
    SIMILAR_USERS = "similar_users"
    TRENDING = "trending"
    PERSONALIZED = "personalized"
    BUDGET_FRIENDLY = "budget_friendly"
    LIFESTYLE = "lifestyle"


class RecommendationCriteria(BaseModel):
    """Criteria for generating recommendations."""
    # Health-based criteria
    health_goals: Optional[List[str]] = Field(default=None, description="User's health goals")
    dietary_restrictions: Optional[List[str]] = Field(default=None, description="Dietary restrictions")
    avoid_contaminants: Optional[List[str]] = Field(default=None, description="Contaminants to avoid")
    min_health_score: Optional[float] = Field(default=None, ge=0, le=100, description="Minimum health score")
    
    # Preference-based criteria
    preferred_packaging: Optional[List[str]] = Field(default=None, description="Preferred packaging types")
    max_budget: Optional[float] = Field(default=None, ge=0, description="Maximum budget per bottle")
    preferred_brands: Optional[List[str]] = Field(default=None, description="Preferred brands")
    
    # Taste preferences
    taste_preferences: Optional[List[str]] = Field(default=None, description="Taste preferences")
    mineral_preferences: Optional[List[str]] = Field(default=None, description="Preferred minerals")
    
    # Lifestyle factors
    activity_level: Optional[str] = Field(default=None, description="Activity level (low, moderate, high)")
    hydration_goal: Optional[float] = Field(default=None, ge=0, description="Daily hydration goal in liters")
    environment: Optional[str] = Field(default=None, description="Environment (urban, rural, travel)")
    
    # Recommendation settings
    exclude_tried: bool = Field(default=False, description="Exclude already tried waters")
    include_premium: bool = Field(default=True, description="Include premium options")
    diversity_factor: float = Field(default=0.5, ge=0, le=1, description="Diversity vs similarity (0=similar, 1=diverse)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "health_goals": ["hydration", "mineral_balance", "detox"],
                "dietary_restrictions": ["low_sodium", "fluoride_free"],
                "avoid_contaminants": ["chlorine", "heavy_metals"],
                "min_health_score": 80,
                "preferred_packaging": ["glass", "aluminum"],
                "max_budget": 5.0,
                "preferred_brands": ["Evian", "Fiji"],
                "taste_preferences": ["crisp", "clean", "mineral_rich"],
                "mineral_preferences": ["calcium", "magnesium"],
                "activity_level": "high",
                "hydration_goal": 3.0,
                "environment": "urban",
                "exclude_tried": True,
                "include_premium": True,
                "diversity_factor": 0.7
            }
        }


class RecommendationScore(BaseModel):
    """Individual scoring components for a recommendation."""
    health_match: float = Field(..., ge=0, le=1, description="Health criteria match score")
    preference_match: float = Field(..., ge=0, le=1, description="Preference match score")
    user_similarity: float = Field(..., ge=0, le=1, description="Similar users score")
    popularity: float = Field(..., ge=0, le=1, description="General popularity score")
    novelty: float = Field(..., ge=0, le=1, description="Novelty/discovery score")
    overall: float = Field(..., ge=0, le=1, description="Overall recommendation score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "health_match": 0.95,
                "preference_match": 0.87,
                "user_similarity": 0.72,
                "popularity": 0.68,
                "novelty": 0.45,
                "overall": 0.84
            }
        }


class RecommendationReason(BaseModel):
    """Explanation for why a water is recommended."""
    primary_reason: str = Field(..., description="Main reason for recommendation")
    supporting_reasons: List[str] = Field(default=[], description="Additional supporting reasons")
    health_benefits: List[str] = Field(default=[], description="Specific health benefits")
    match_details: Dict[str, Any] = Field(default={}, description="Detailed matching criteria")
    
    class Config:
        json_schema_extra = {
            "example": {
                "primary_reason": "Perfect match for your hydration and mineral balance goals",
                "supporting_reasons": [
                    "High calcium content supports bone health",
                    "Glass packaging aligns with your preferences",
                    "Excellent health score of 92/100"
                ],
                "health_benefits": [
                    "Supports bone and teeth health",
                    "Aids in muscle function",
                    "Promotes cardiovascular health"
                ],
                "match_details": {
                    "health_score": 92,
                    "packaging_match": "glass",
                    "mineral_content": "high_calcium_magnesium",
                    "contaminant_free": True
                }
            }
        }


class Recommendation(BaseModel):
    """Single water recommendation."""
    water: WaterData = Field(..., description="Recommended water data")
    score: RecommendationScore = Field(..., description="Recommendation scoring")
    reason: RecommendationReason = Field(..., description="Explanation for recommendation")
    recommendation_type: RecommendationType = Field(..., description="Type of recommendation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in recommendation")
    priority: int = Field(..., description="Priority ranking (1=highest)")
    
    # Additional metadata
    estimated_cost_per_month: Optional[float] = Field(default=None, description="Estimated monthly cost")
    availability_score: float = Field(default=1.0, ge=0, le=1, description="Availability score")
    freshness_score: float = Field(default=1.0, ge=0, le=1, description="How recent/trending this recommendation is")
    
    class Config:
        json_schema_extra = {
            "example": {
                "water": {"id": 1, "name": "Evian Natural Spring Water"},
                "score": {
                    "health_match": 0.95,
                    "preference_match": 0.87,
                    "user_similarity": 0.72,
                    "popularity": 0.68,
                    "novelty": 0.45,
                    "overall": 0.84
                },
                "reason": {
                    "primary_reason": "Perfect match for your hydration goals",
                    "supporting_reasons": ["High mineral content", "Glass packaging"]
                },
                "recommendation_type": "health_based",
                "confidence": 0.89,
                "priority": 1,
                "estimated_cost_per_month": 75.50,
                "availability_score": 0.95,
                "freshness_score": 0.88
            }
        }


class RecommendationRequest(BaseModel):
    """Request for personalized recommendations."""
    criteria: Optional[RecommendationCriteria] = Field(default=None, description="Specific criteria")
    limit: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    recommendation_types: Optional[List[RecommendationType]] = Field(default=None, description="Types to include")
    exclude_water_ids: Optional[List[int]] = Field(default=None, description="Water IDs to exclude")
    include_explanations: bool = Field(default=True, description="Include detailed explanations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "criteria": {
                    "health_goals": ["hydration", "mineral_balance"],
                    "max_budget": 5.0,
                    "preferred_packaging": ["glass"]
                },
                "limit": 10,
                "recommendation_types": ["health_based", "preference_based"],
                "exclude_water_ids": [1, 5, 10],
                "include_explanations": True
            }
        }


class CustomRecommendationRequest(BaseModel):
    """Request for custom recommendations."""
    user_id: Optional[str] = None
    criteria: RecommendationCriteria
    limit: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    exclude_water_ids: Optional[List[int]] = Field(default=None, description="Water IDs to exclude")


class RecommendationResponse(BaseModel):
    """Response containing personalized recommendations."""
    recommendations: List[Recommendation] = Field(..., description="List of recommendations")
    total_analyzed: int = Field(..., description="Total waters analyzed")
    criteria_used: Dict[str, Any] = Field(..., description="Criteria used for recommendations")
    generation_metadata: Dict[str, Any] = Field(..., description="Metadata about recommendation generation")
    
    # Summary statistics
    average_confidence: float = Field(..., description="Average confidence across recommendations")
    diversity_score: float = Field(..., description="Diversity of recommendations")
    personalization_score: float = Field(..., description="How personalized the recommendations are")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendations": [],
                "total_analyzed": 150,
                "criteria_used": {
                    "health_goals": ["hydration"],
                    "user_preferences": True,
                    "review_history": True
                },
                "generation_metadata": {
                    "algorithm_version": "1.2",
                    "generation_time_ms": 125,
                    "fallback_used": False
                },
                "average_confidence": 0.82,
                "diversity_score": 0.75,
                "personalization_score": 0.89
            }
        }


class UserPreferenceProfile(BaseModel):
    """Learned user preferences from behavior."""
    user_id: int = Field(..., description="User ID")
    
    # Learned preferences
    preferred_health_score_range: tuple = Field(default=(80, 100), description="Preferred health score range")
    preferred_price_range: tuple = Field(default=(0, 10), description="Preferred price range")
    brand_affinity: Dict[str, float] = Field(default={}, description="Brand preference scores")
    packaging_preferences: Dict[str, float] = Field(default={}, description="Packaging preference scores")
    
    # Taste and mineral preferences
    mineral_preferences: Dict[str, float] = Field(default={}, description="Mineral preference scores")
    taste_preferences: Dict[str, float] = Field(default={}, description="Taste preference scores")
    
    # Behavioral patterns
    review_patterns: Dict[str, Any] = Field(default={}, description="Review behavior patterns")
    purchase_patterns: Dict[str, Any] = Field(default={}, description="Purchase behavior patterns")
    seasonal_preferences: Dict[str, Any] = Field(default={}, description="Seasonal preference changes")
    
    # Confidence scores
    preference_confidence: float = Field(default=0.5, ge=0, le=1, description="Confidence in learned preferences")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last profile update")
    data_points: int = Field(default=0, description="Number of data points used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "preferred_health_score_range": [85, 95],
                "preferred_price_range": [2.0, 6.0],
                "brand_affinity": {
                    "Evian": 0.9,
                    "Fiji": 0.7,
                    "Smartwater": 0.6
                },
                "packaging_preferences": {
                    "glass": 0.9,
                    "plastic": 0.3,
                    "aluminum": 0.7
                },
                "mineral_preferences": {
                    "calcium": 0.8,
                    "magnesium": 0.7,
                    "sodium": 0.2
                },
                "preference_confidence": 0.85,
                "data_points": 25
            }
        }


class RecommendationFeedback(BaseModel):
    """Feedback on a recommendation."""
    recommendation_id: str = Field(..., description="Unique recommendation ID")
    user_id: int = Field(..., description="User ID")
    feedback_type: str = Field(..., description="Type of feedback (like, dislike, tried, purchased)")
    rating: Optional[float] = Field(default=None, ge=1, le=5, description="Rating if tried")
    comments: Optional[str] = Field(default=None, max_length=500, description="User comments")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Feedback timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendation_id": "rec_123456",
                "user_id": 1,
                "feedback_type": "tried",
                "rating": 4.5,
                "comments": "Great recommendation! Really matched my taste preferences.",
                "created_at": "2023-12-01T15:30:00Z"
            }
        } 