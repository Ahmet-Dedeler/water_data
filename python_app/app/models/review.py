from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReviewStatus(str, Enum):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class ReviewType(str, Enum):
    """Review type enumeration."""
    TASTE = "taste"
    HEALTH = "health"
    VALUE = "value"
    OVERALL = "overall"
    PACKAGING = "packaging"


class Review(BaseModel):
    """Review model for water bottle reviews."""
    id: int = Field(..., description="Review ID")
    user_id: int = Field(..., description="User who wrote the review")
    water_id: int = Field(..., description="Water bottle being reviewed")
    rating: float = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
    title: str = Field(..., max_length=200, description="Review title")
    comment: str = Field(..., max_length=2000, description="Review comment")
    review_type: ReviewType = Field(default=ReviewType.OVERALL, description="Type of review")
    status: ReviewStatus = Field(default=ReviewStatus.PENDING, description="Review status")
    
    # Additional ratings
    taste_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Taste rating")
    health_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Health rating")
    value_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Value rating")
    packaging_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Packaging rating")
    
    # Metadata
    is_verified_purchase: bool = Field(default=False, description="Whether this is a verified purchase")
    helpful_votes: int = Field(default=0, description="Number of helpful votes")
    total_votes: int = Field(default=0, description="Total votes received")
    flagged_count: int = Field(default=0, description="Number of times flagged")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    
    # User info (populated from lookup)
    username: Optional[str] = Field(default=None, description="Username of reviewer")
    user_verified: Optional[bool] = Field(default=None, description="Whether user is verified")
    
    # Water info (populated from lookup)
    water_name: Optional[str] = Field(default=None, description="Name of water being reviewed")
    water_brand: Optional[str] = Field(default=None, description="Brand of water being reviewed")
    
    @field_validator('rating', 'taste_rating', 'health_rating', 'value_rating', 'packaging_rating')
    @classmethod
    def validate_ratings(cls, v):
        """Validate rating values."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @property
    def helpfulness_score(self) -> float:
        """Calculate helpfulness score."""
        if self.total_votes == 0:
            return 0.0
        return (self.helpful_votes / self.total_votes) * 100
    
    @property
    def average_detailed_rating(self) -> Optional[float]:
        """Calculate average of detailed ratings."""
        ratings = [r for r in [self.taste_rating, self.health_rating, 
                             self.value_rating, self.packaging_rating] if r is not None]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "water_id": 1,
                "rating": 4.5,
                "title": "Great water for daily hydration",
                "comment": "This water has excellent mineral content and tastes clean. Perfect for my health goals.",
                "review_type": "overall",
                "status": "approved",
                "taste_rating": 4.0,
                "health_rating": 5.0,
                "value_rating": 4.0,
                "packaging_rating": 3.5,
                "is_verified_purchase": True,
                "helpful_votes": 15,
                "total_votes": 18,
                "created_at": "2023-12-01T10:30:00Z"
            }
        }


class ReviewCreate(BaseModel):
    """Model for creating a new review."""
    water_id: int = Field(..., description="Water bottle being reviewed")
    rating: float = Field(..., ge=1, le=5, description="Overall rating from 1-5 stars")
    title: str = Field(..., max_length=200, description="Review title")
    comment: str = Field(..., max_length=2000, description="Review comment")
    review_type: ReviewType = Field(default=ReviewType.OVERALL, description="Type of review")
    
    # Optional detailed ratings
    taste_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Taste rating")
    health_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Health rating")
    value_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Value rating")
    packaging_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Packaging rating")
    
    is_verified_purchase: bool = Field(default=False, description="Whether this is a verified purchase")
    
    @field_validator('rating', 'taste_rating', 'health_rating', 'value_rating', 'packaging_rating')
    @classmethod
    def validate_ratings(cls, v):
        """Validate rating values."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "water_id": 1,
                "rating": 4.5,
                "title": "Great water for daily hydration",
                "comment": "This water has excellent mineral content and tastes clean.",
                "review_type": "overall",
                "taste_rating": 4.0,
                "health_rating": 5.0,
                "value_rating": 4.0,
                "packaging_rating": 3.5,
                "is_verified_purchase": True
            }
        }


class ReviewUpdate(BaseModel):
    """Model for updating a review."""
    rating: Optional[float] = Field(default=None, ge=1, le=5, description="Overall rating")
    title: Optional[str] = Field(default=None, max_length=200, description="Review title")
    comment: Optional[str] = Field(default=None, max_length=2000, description="Review comment")
    review_type: Optional[ReviewType] = Field(default=None, description="Type of review")
    
    # Optional detailed ratings
    taste_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Taste rating")
    health_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Health rating")
    value_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Value rating")
    packaging_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Packaging rating")
    
    @field_validator('rating', 'taste_rating', 'health_rating', 'value_rating', 'packaging_rating')
    @classmethod
    def validate_ratings(cls, v):
        """Validate rating values."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class ReviewModeration(BaseModel):
    """Model for moderating reviews."""
    status: ReviewStatus = Field(..., description="New review status")
    moderator_notes: Optional[str] = Field(default=None, max_length=500, description="Moderator notes")


class ReviewVote(BaseModel):
    """Model for review votes (helpful/not helpful)."""
    id: int = Field(..., description="Vote ID")
    review_id: int = Field(..., description="Review being voted on")
    user_id: int = Field(..., description="User who voted")
    is_helpful: bool = Field(..., description="Whether vote is helpful or not")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Vote timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "review_id": 1,
                "user_id": 2,
                "is_helpful": True,
                "created_at": "2023-12-01T11:00:00Z"
            }
        }


class ReviewVoteCreate(BaseModel):
    """Model for creating a review vote."""
    review_id: int = Field(..., description="Review being voted on")
    is_helpful: bool = Field(..., description="Whether vote is helpful or not")


class ReviewFlag(BaseModel):
    """Model for flagging inappropriate reviews."""
    id: int = Field(..., description="Flag ID")
    review_id: int = Field(..., description="Review being flagged")
    user_id: int = Field(..., description="User who flagged")
    reason: str = Field(..., max_length=500, description="Reason for flagging")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Flag timestamp")
    resolved: bool = Field(default=False, description="Whether flag has been resolved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "review_id": 1,
                "user_id": 3,
                "reason": "Inappropriate language",
                "created_at": "2023-12-01T12:00:00Z",
                "resolved": False
            }
        }


class ReviewFlagCreate(BaseModel):
    """Model for creating a review flag."""
    review_id: int = Field(..., description="Review being flagged")
    reason: str = Field(..., max_length=500, description="Reason for flagging")


class ReviewStats(BaseModel):
    """Model for review statistics."""
    water_id: int = Field(..., description="Water ID")
    total_reviews: int = Field(..., description="Total number of reviews")
    average_rating: float = Field(..., description="Average rating")
    rating_distribution: dict = Field(..., description="Distribution of ratings (1-5 stars)")
    
    # Detailed ratings averages
    average_taste_rating: Optional[float] = Field(default=None, description="Average taste rating")
    average_health_rating: Optional[float] = Field(default=None, description="Average health rating")
    average_value_rating: Optional[float] = Field(default=None, description="Average value rating")
    average_packaging_rating: Optional[float] = Field(default=None, description="Average packaging rating")
    
    # Review breakdown
    verified_purchase_count: int = Field(default=0, description="Number of verified purchase reviews")
    recent_reviews_count: int = Field(default=0, description="Number of recent reviews (last 30 days)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "water_id": 1,
                "total_reviews": 25,
                "average_rating": 4.2,
                "rating_distribution": {
                    "1": 1, "2": 2, "3": 5, "4": 8, "5": 9
                },
                "average_taste_rating": 4.1,
                "average_health_rating": 4.5,
                "average_value_rating": 3.8,
                "average_packaging_rating": 4.0,
                "verified_purchase_count": 18,
                "recent_reviews_count": 7
            }
        }


class UserReviewSummary(BaseModel):
    """Model for user's review summary."""
    user_id: int = Field(..., description="User ID")
    total_reviews: int = Field(..., description="Total reviews written")
    average_rating_given: float = Field(..., description="Average rating given by user")
    helpful_votes_received: int = Field(..., description="Total helpful votes received")
    verified_purchase_reviews: int = Field(..., description="Number of verified purchase reviews")
    recent_reviews: int = Field(..., description="Reviews in last 30 days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "total_reviews": 12,
                "average_rating_given": 4.1,
                "helpful_votes_received": 45,
                "verified_purchase_reviews": 8,
                "recent_reviews": 3
            }
        } 