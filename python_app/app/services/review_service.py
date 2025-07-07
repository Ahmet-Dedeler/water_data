from typing import Optional, List, Dict, Any, Tuple
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
from collections import defaultdict

from app.models.review import (
    Review, ReviewCreate, ReviewUpdate, ReviewModeration,
    ReviewVote, ReviewVoteCreate, ReviewFlag, ReviewFlagCreate,
    ReviewStats, UserReviewSummary, ReviewStatus, ReviewType
)
from app.services.user_service import user_service
from app.services.data_service import DataService

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for review management operations."""
    
    def __init__(self):
        self.reviews_file = Path(__file__).parent.parent / "data" / "reviews.json"
        self.votes_file = Path(__file__).parent.parent / "data" / "review_votes.json"
        self.flags_file = Path(__file__).parent.parent / "data" / "review_flags.json"
        self._ensure_data_files()
        self._reviews_cache = None
        self._votes_cache = None
        self._flags_cache = None
        self._next_review_id = 1
        self._next_vote_id = 1
        self._next_flag_id = 1
        self.data_service = DataService()
    
    def _ensure_data_files(self):
        """Ensure review data files exist."""
        data_dir = self.reviews_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [self.reviews_file, self.votes_file, self.flags_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_reviews(self) -> List[Dict]:
        """Load reviews from file."""
        if self._reviews_cache is None:
            try:
                with open(self.reviews_file, 'r') as f:
                    self._reviews_cache = json.load(f)
                    
                # Update next review ID
                if self._reviews_cache:
                    self._next_review_id = max(review['id'] for review in self._reviews_cache) + 1
            except Exception as e:
                logger.error(f"Error loading reviews: {e}")
                self._reviews_cache = []
        
        return self._reviews_cache
    
    async def _save_reviews(self, reviews: List[Dict]):
        """Save reviews to file."""
        try:
            with open(self.reviews_file, 'w') as f:
                json.dump(reviews, f, indent=2, default=str)
            self._reviews_cache = reviews
        except Exception as e:
            logger.error(f"Error saving reviews: {e}")
            raise
    
    async def _load_votes(self) -> List[Dict]:
        """Load review votes from file."""
        if self._votes_cache is None:
            try:
                with open(self.votes_file, 'r') as f:
                    self._votes_cache = json.load(f)
                    
                # Update next vote ID
                if self._votes_cache:
                    self._next_vote_id = max(vote['id'] for vote in self._votes_cache) + 1
            except Exception as e:
                logger.error(f"Error loading votes: {e}")
                self._votes_cache = []
        
        return self._votes_cache
    
    async def _save_votes(self, votes: List[Dict]):
        """Save votes to file."""
        try:
            with open(self.votes_file, 'w') as f:
                json.dump(votes, f, indent=2, default=str)
            self._votes_cache = votes
        except Exception as e:
            logger.error(f"Error saving votes: {e}")
            raise
    
    async def _load_flags(self) -> List[Dict]:
        """Load review flags from file."""
        if self._flags_cache is None:
            try:
                with open(self.flags_file, 'r') as f:
                    self._flags_cache = json.load(f)
                    
                # Update next flag ID
                if self._flags_cache:
                    self._next_flag_id = max(flag['id'] for flag in self._flags_cache) + 1
            except Exception as e:
                logger.error(f"Error loading flags: {e}")
                self._flags_cache = []
        
        return self._flags_cache
    
    async def _save_flags(self, flags: List[Dict]):
        """Save flags to file."""
        try:
            with open(self.flags_file, 'w') as f:
                json.dump(flags, f, indent=2, default=str)
            self._flags_cache = flags
        except Exception as e:
            logger.error(f"Error saving flags: {e}")
            raise
    
    async def _populate_review_metadata(self, review_dict: Dict) -> Dict:
        """Populate user and water metadata for a review."""
        # Get user info
        user = await user_service.get_user_by_id(review_dict['user_id'])
        if user:
            review_dict['username'] = user.username
            review_dict['user_verified'] = user.is_verified
        
        # Get water info
        try:
            water_data = await self.data_service.get_water_by_id(review_dict['water_id'])
            if water_data:
                review_dict['water_name'] = water_data.name
                review_dict['water_brand'] = water_data.brand.name if water_data.brand else None
        except Exception as e:
            logger.warning(f"Could not load water data for review {review_dict['id']}: {e}")
        
        return review_dict
    
    async def create_review(self, user_id: int, review_data: ReviewCreate) -> Review:
        """Create a new review."""
        reviews = await self._load_reviews()
        
        # Check if user already reviewed this water
        existing_review = next(
            (review for review in reviews 
             if review['user_id'] == user_id and review['water_id'] == review_data.water_id),
            None
        )
        if existing_review:
            raise ValueError("You have already reviewed this water bottle")
        
        # Verify water exists
        try:
            water_data = await self.data_service.get_water_by_id(review_data.water_id)
            if not water_data:
                raise ValueError("Water bottle not found")
        except Exception:
            raise ValueError("Water bottle not found")
        
        # Create review
        review_dict = {
            "id": self._next_review_id,
            "user_id": user_id,
            "water_id": review_data.water_id,
            "rating": review_data.rating,
            "title": review_data.title,
            "comment": review_data.comment,
            "review_type": review_data.review_type,
            "status": ReviewStatus.PENDING,
            "taste_rating": review_data.taste_rating,
            "health_rating": review_data.health_rating,
            "value_rating": review_data.value_rating,
            "packaging_rating": review_data.packaging_rating,
            "is_verified_purchase": review_data.is_verified_purchase,
            "helpful_votes": 0,
            "total_votes": 0,
            "flagged_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "approved_at": None
        }
        
        reviews.append(review_dict)
        await self._save_reviews(reviews)
        
        self._next_review_id += 1
        
        # Populate metadata and return
        review_dict = await self._populate_review_metadata(review_dict)
        return Review(**review_dict)
    
    async def get_review_by_id(self, review_id: int) -> Optional[Review]:
        """Get review by ID."""
        reviews = await self._load_reviews()
        
        review_dict = next((review for review in reviews if review['id'] == review_id), None)
        if not review_dict:
            return None
        
        # Populate metadata
        review_dict = await self._populate_review_metadata(review_dict)
        return Review(**review_dict)
    
    async def update_review(self, user_id: int, review_id: int, review_update: ReviewUpdate) -> Optional[Review]:
        """Update a review (only by the author)."""
        reviews = await self._load_reviews()
        
        review_index = next((i for i, review in enumerate(reviews) if review['id'] == review_id), None)
        if review_index is None:
            return None
        
        # Check if user owns the review
        if reviews[review_index]['user_id'] != user_id:
            raise ValueError("You can only update your own reviews")
        
        # Update review
        update_data = review_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Reset status to pending if content was changed
        content_fields = ['rating', 'title', 'comment', 'taste_rating', 'health_rating', 'value_rating', 'packaging_rating']
        if any(field in update_data for field in content_fields):
            update_data['status'] = ReviewStatus.PENDING
            update_data['approved_at'] = None
        
        reviews[review_index].update(update_data)
        await self._save_reviews(reviews)
        
        # Populate metadata and return
        review_dict = await self._populate_review_metadata(reviews[review_index])
        return Review(**review_dict)
    
    async def delete_review(self, user_id: int, review_id: int, is_admin: bool = False) -> bool:
        """Delete a review (by author or admin)."""
        reviews = await self._load_reviews()
        
        review_index = next((i for i, review in enumerate(reviews) if review['id'] == review_id), None)
        if review_index is None:
            return False
        
        # Check permissions
        if not is_admin and reviews[review_index]['user_id'] != user_id:
            raise ValueError("You can only delete your own reviews")
        
        # Remove review
        reviews.pop(review_index)
        await self._save_reviews(reviews)
        
        return True
    
    async def moderate_review(self, review_id: int, moderation: ReviewModeration) -> Optional[Review]:
        """Moderate a review (admin/moderator only)."""
        reviews = await self._load_reviews()
        
        review_index = next((i for i, review in enumerate(reviews) if review['id'] == review_id), None)
        if review_index is None:
            return None
        
        # Update review status
        reviews[review_index]['status'] = moderation.status
        reviews[review_index]['updated_at'] = datetime.utcnow().isoformat()
        
        if moderation.status == ReviewStatus.APPROVED:
            reviews[review_index]['approved_at'] = datetime.utcnow().isoformat()
        
        # Add moderator notes if provided
        if moderation.moderator_notes:
            reviews[review_index]['moderator_notes'] = moderation.moderator_notes
        
        await self._save_reviews(reviews)
        
        # Populate metadata and return
        review_dict = await self._populate_review_metadata(reviews[review_index])
        return Review(**review_dict)
    
    async def get_reviews_for_water(
        self, 
        water_id: int, 
        status: Optional[ReviewStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Review], int]:
        """Get reviews for a specific water bottle."""
        reviews = await self._load_reviews()
        
        # Filter by water_id
        water_reviews = [review for review in reviews if review['water_id'] == water_id]
        
        # Filter by status if provided
        if status:
            water_reviews = [review for review in water_reviews if review['status'] == status]
        
        # Sort reviews
        reverse = sort_order.lower() == "desc"
        if sort_by == "helpful":
            water_reviews.sort(key=lambda x: x.get('helpful_votes', 0), reverse=reverse)
        elif sort_by == "rating":
            water_reviews.sort(key=lambda x: x.get('rating', 0), reverse=reverse)
        else:  # created_at
            water_reviews.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
        
        total = len(water_reviews)
        
        # Apply pagination
        paginated_reviews = water_reviews[skip:skip + limit]
        
        # Populate metadata
        result_reviews = []
        for review_dict in paginated_reviews:
            review_dict = await self._populate_review_metadata(review_dict)
            result_reviews.append(Review(**review_dict))
        
        return result_reviews, total
    
    async def get_reviews_by_user(
        self, 
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Review], int]:
        """Get reviews written by a specific user."""
        reviews = await self._load_reviews()
        
        # Filter by user_id
        user_reviews = [review for review in reviews if review['user_id'] == user_id]
        
        # Sort by creation date (newest first)
        user_reviews.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        total = len(user_reviews)
        
        # Apply pagination
        paginated_reviews = user_reviews[skip:skip + limit]
        
        # Populate metadata
        result_reviews = []
        for review_dict in paginated_reviews:
            review_dict = await self._populate_review_metadata(review_dict)
            result_reviews.append(Review(**review_dict))
        
        return result_reviews, total
    
    async def vote_on_review(self, user_id: int, vote_data: ReviewVoteCreate) -> ReviewVote:
        """Vote on a review (helpful/not helpful)."""
        votes = await self._load_votes()
        reviews = await self._load_reviews()
        
        # Check if user already voted on this review
        existing_vote = next(
            (vote for vote in votes 
             if vote['user_id'] == user_id and vote['review_id'] == vote_data.review_id),
            None
        )
        if existing_vote:
            raise ValueError("You have already voted on this review")
        
        # Check if review exists
        review_index = next((i for i, review in enumerate(reviews) if review['id'] == vote_data.review_id), None)
        if review_index is None:
            raise ValueError("Review not found")
        
        # Check if user is trying to vote on their own review
        if reviews[review_index]['user_id'] == user_id:
            raise ValueError("You cannot vote on your own review")
        
        # Create vote
        vote_dict = {
            "id": self._next_vote_id,
            "review_id": vote_data.review_id,
            "user_id": user_id,
            "is_helpful": vote_data.is_helpful,
            "created_at": datetime.utcnow().isoformat()
        }
        
        votes.append(vote_dict)
        await self._save_votes(votes)
        
        # Update review vote counts
        reviews[review_index]['total_votes'] = reviews[review_index].get('total_votes', 0) + 1
        if vote_data.is_helpful:
            reviews[review_index]['helpful_votes'] = reviews[review_index].get('helpful_votes', 0) + 1
        
        await self._save_reviews(reviews)
        
        self._next_vote_id += 1
        
        return ReviewVote(**vote_dict)
    
    async def flag_review(self, user_id: int, flag_data: ReviewFlagCreate) -> ReviewFlag:
        """Flag a review as inappropriate."""
        flags = await self._load_flags()
        reviews = await self._load_reviews()
        
        # Check if user already flagged this review
        existing_flag = next(
            (flag for flag in flags 
             if flag['user_id'] == user_id and flag['review_id'] == flag_data.review_id),
            None
        )
        if existing_flag:
            raise ValueError("You have already flagged this review")
        
        # Check if review exists
        review_index = next((i for i, review in enumerate(reviews) if review['id'] == flag_data.review_id), None)
        if review_index is None:
            raise ValueError("Review not found")
        
        # Create flag
        flag_dict = {
            "id": self._next_flag_id,
            "review_id": flag_data.review_id,
            "user_id": user_id,
            "reason": flag_data.reason,
            "created_at": datetime.utcnow().isoformat(),
            "resolved": False
        }
        
        flags.append(flag_dict)
        await self._save_flags(flags)
        
        # Update review flag count
        reviews[review_index]['flagged_count'] = reviews[review_index].get('flagged_count', 0) + 1
        
        # Auto-flag if too many flags
        if reviews[review_index]['flagged_count'] >= 3:
            reviews[review_index]['status'] = ReviewStatus.FLAGGED
        
        await self._save_reviews(reviews)
        
        self._next_flag_id += 1
        
        return ReviewFlag(**flag_dict)
    
    async def get_review_stats(self, water_id: int) -> ReviewStats:
        """Get review statistics for a water bottle."""
        reviews = await self._load_reviews()
        
        # Filter approved reviews for this water
        water_reviews = [
            review for review in reviews 
            if review['water_id'] == water_id and review['status'] == ReviewStatus.APPROVED
        ]
        
        if not water_reviews:
            return ReviewStats(
                water_id=water_id,
                total_reviews=0,
                average_rating=0.0,
                rating_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            )
        
        # Calculate statistics
        total_reviews = len(water_reviews)
        ratings = [review['rating'] for review in water_reviews]
        average_rating = sum(ratings) / len(ratings)
        
        # Rating distribution
        rating_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for rating in ratings:
            star_rating = str(int(round(rating)))
            if star_rating in rating_distribution:
                rating_distribution[star_rating] += 1
        
        # Detailed ratings
        taste_ratings = [r['taste_rating'] for r in water_reviews if r.get('taste_rating')]
        health_ratings = [r['health_rating'] for r in water_reviews if r.get('health_rating')]
        value_ratings = [r['value_rating'] for r in water_reviews if r.get('value_rating')]
        packaging_ratings = [r['packaging_rating'] for r in water_reviews if r.get('packaging_rating')]
        
        # Recent reviews (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_reviews = [
            review for review in water_reviews
            if datetime.fromisoformat(review['created_at'].replace('Z', '+00:00')) > thirty_days_ago
        ]
        
        return ReviewStats(
            water_id=water_id,
            total_reviews=total_reviews,
            average_rating=round(average_rating, 2),
            rating_distribution=rating_distribution,
            average_taste_rating=round(sum(taste_ratings) / len(taste_ratings), 2) if taste_ratings else None,
            average_health_rating=round(sum(health_ratings) / len(health_ratings), 2) if health_ratings else None,
            average_value_rating=round(sum(value_ratings) / len(value_ratings), 2) if value_ratings else None,
            average_packaging_rating=round(sum(packaging_ratings) / len(packaging_ratings), 2) if packaging_ratings else None,
            verified_purchase_count=len([r for r in water_reviews if r.get('is_verified_purchase')]),
            recent_reviews_count=len(recent_reviews)
        )
    
    async def get_user_review_summary(self, user_id: int) -> UserReviewSummary:
        """Get review summary for a user."""
        reviews = await self._load_reviews()
        
        # Filter user's reviews
        user_reviews = [review for review in reviews if review['user_id'] == user_id]
        
        if not user_reviews:
            return UserReviewSummary(
                user_id=user_id,
                total_reviews=0,
                average_rating_given=0.0,
                helpful_votes_received=0,
                verified_purchase_reviews=0,
                recent_reviews=0
            )
        
        # Calculate statistics
        total_reviews = len(user_reviews)
        ratings = [review['rating'] for review in user_reviews]
        average_rating_given = sum(ratings) / len(ratings)
        helpful_votes_received = sum(review.get('helpful_votes', 0) for review in user_reviews)
        verified_purchase_reviews = len([r for r in user_reviews if r.get('is_verified_purchase')])
        
        # Recent reviews (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_reviews = len([
            review for review in user_reviews
            if datetime.fromisoformat(review['created_at'].replace('Z', '+00:00')) > thirty_days_ago
        ])
        
        return UserReviewSummary(
            user_id=user_id,
            total_reviews=total_reviews,
            average_rating_given=round(average_rating_given, 2),
            helpful_votes_received=helpful_votes_received,
            verified_purchase_reviews=verified_purchase_reviews,
            recent_reviews=recent_reviews
        )
    
    async def get_pending_reviews(self, skip: int = 0, limit: int = 20) -> Tuple[List[Review], int]:
        """Get pending reviews for moderation."""
        reviews = await self._load_reviews()
        
        # Filter pending reviews
        pending_reviews = [review for review in reviews if review['status'] == ReviewStatus.PENDING]
        
        # Sort by creation date (oldest first for moderation queue)
        pending_reviews.sort(key=lambda x: x.get('created_at', ''))
        
        total = len(pending_reviews)
        
        # Apply pagination
        paginated_reviews = pending_reviews[skip:skip + limit]
        
        # Populate metadata
        result_reviews = []
        for review_dict in paginated_reviews:
            review_dict = await self._populate_review_metadata(review_dict)
            result_reviews.append(Review(**review_dict))
        
        return result_reviews, total
    
    async def get_flagged_reviews(self, skip: int = 0, limit: int = 20) -> Tuple[List[Review], int]:
        """Get flagged reviews for moderation."""
        reviews = await self._load_reviews()
        
        # Filter flagged reviews
        flagged_reviews = [review for review in reviews if review['status'] == ReviewStatus.FLAGGED]
        
        # Sort by flag count (highest first)
        flagged_reviews.sort(key=lambda x: x.get('flagged_count', 0), reverse=True)
        
        total = len(flagged_reviews)
        
        # Apply pagination
        paginated_reviews = flagged_reviews[skip:skip + limit]
        
        # Populate metadata
        result_reviews = []
        for review_dict in paginated_reviews:
            review_dict = await self._populate_review_metadata(review_dict)
            result_reviews.append(Review(**review_dict))
        
        return result_reviews, total


# Global service instance
review_service = ReviewService() 