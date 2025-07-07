from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging

from app.models import BaseResponse
from app.models.review import (
    Review, ReviewCreate, ReviewUpdate, ReviewModeration,
    ReviewVote, ReviewVoteCreate, ReviewFlag, ReviewFlagCreate,
    ReviewStats, UserReviewSummary, ReviewStatus
)
from app.services.review_service import review_service
from app.core.auth import (
    get_current_active_user, get_current_moderator_user,
    get_current_user_optional
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=BaseResponse[Review], status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new review."""
    try:
        review = await review_service.create_review(current_user["user_id"], review_data)
        return BaseResponse(
            data=review,
            message="Review created successfully and submitted for moderation"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{review_id}", response_model=BaseResponse[Review])
async def get_review(review_id: int):
    """Get a specific review by ID."""
    try:
        review = await review_service.get_review_by_id(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return BaseResponse(
            data=review,
            message="Review retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{review_id}", response_model=BaseResponse[Review])
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update a review (only by the author)."""
    try:
        updated_review = await review_service.update_review(
            current_user["user_id"], 
            review_id, 
            review_update
        )
        if not updated_review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return BaseResponse(
            data=updated_review,
            message="Review updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{review_id}", response_model=BaseResponse[dict])
async def delete_review(
    review_id: int,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a review (by author or admin)."""
    try:
        is_admin = current_user.get("role") in ["admin", "moderator"]
        success = await review_service.delete_review(
            current_user["user_id"], 
            review_id, 
            is_admin=is_admin
        )
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return BaseResponse(
            data={"deleted": True},
            message="Review deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/water/{water_id}", response_model=BaseResponse[List[Review]])
async def get_reviews_for_water(
    water_id: int,
    status: Optional[ReviewStatus] = Query(ReviewStatus.APPROVED, description="Filter by review status"),
    sort_by: str = Query("created_at", description="Sort field (created_at, helpful, rating)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return")
):
    """Get reviews for a specific water bottle."""
    try:
        reviews, total = await review_service.get_reviews_for_water(
            water_id=water_id,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit
        )
        
        return BaseResponse(
            data=reviews,
            message=f"Retrieved {len(reviews)} reviews for water {water_id} (total: {total})"
        )
    except Exception as e:
        logger.error(f"Error getting reviews for water: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}", response_model=BaseResponse[List[Review]])
async def get_reviews_by_user(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return")
):
    """Get reviews written by a specific user."""
    try:
        reviews, total = await review_service.get_reviews_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        return BaseResponse(
            data=reviews,
            message=f"Retrieved {len(reviews)} reviews by user {user_id} (total: {total})"
        )
    except Exception as e:
        logger.error(f"Error getting reviews by user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/reviews", response_model=BaseResponse[List[Review]])
async def get_my_reviews(
    current_user: dict = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return")
):
    """Get current user's reviews."""
    try:
        reviews, total = await review_service.get_reviews_by_user(
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit
        )
        
        return BaseResponse(
            data=reviews,
            message=f"Retrieved {len(reviews)} of your reviews (total: {total})"
        )
    except Exception as e:
        logger.error(f"Error getting user's reviews: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{review_id}/vote", response_model=BaseResponse[ReviewVote])
async def vote_on_review(
    review_id: int,
    vote_data: ReviewVoteCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Vote on a review (helpful/not helpful)."""
    try:
        # Override review_id from URL
        vote_data.review_id = review_id
        
        vote = await review_service.vote_on_review(current_user["user_id"], vote_data)
        return BaseResponse(
            data=vote,
            message="Vote recorded successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error voting on review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{review_id}/flag", response_model=BaseResponse[ReviewFlag])
async def flag_review(
    review_id: int,
    flag_data: ReviewFlagCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Flag a review as inappropriate."""
    try:
        # Override review_id from URL
        flag_data.review_id = review_id
        
        flag = await review_service.flag_review(current_user["user_id"], flag_data)
        return BaseResponse(
            data=flag,
            message="Review flagged successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error flagging review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/water/{water_id}", response_model=BaseResponse[ReviewStats])
async def get_water_review_stats(water_id: int):
    """Get review statistics for a water bottle."""
    try:
        stats = await review_service.get_review_stats(water_id)
        return BaseResponse(
            data=stats,
            message="Review statistics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting review stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/user/{user_id}", response_model=BaseResponse[UserReviewSummary])
async def get_user_review_summary(user_id: int):
    """Get review summary for a user."""
    try:
        summary = await review_service.get_user_review_summary(user_id)
        return BaseResponse(
            data=summary,
            message="User review summary retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting user review summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/stats", response_model=BaseResponse[UserReviewSummary])
async def get_my_review_summary(current_user: dict = Depends(get_current_active_user)):
    """Get current user's review summary."""
    try:
        summary = await review_service.get_user_review_summary(current_user["user_id"])
        return BaseResponse(
            data=summary,
            message="Your review summary retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting user review summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Moderation endpoints (moderator/admin only)
@router.get("/moderation/pending", response_model=BaseResponse[List[Review]])
async def get_pending_reviews(
    moderator: dict = Depends(get_current_moderator_user),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return")
):
    """Get pending reviews for moderation."""
    try:
        reviews, total = await review_service.get_pending_reviews(skip=skip, limit=limit)
        return BaseResponse(
            data=reviews,
            message=f"Retrieved {len(reviews)} pending reviews (total: {total})"
        )
    except Exception as e:
        logger.error(f"Error getting pending reviews: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/moderation/flagged", response_model=BaseResponse[List[Review]])
async def get_flagged_reviews(
    moderator: dict = Depends(get_current_moderator_user),
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return")
):
    """Get flagged reviews for moderation."""
    try:
        reviews, total = await review_service.get_flagged_reviews(skip=skip, limit=limit)
        return BaseResponse(
            data=reviews,
            message=f"Retrieved {len(reviews)} flagged reviews (total: {total})"
        )
    except Exception as e:
        logger.error(f"Error getting flagged reviews: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{review_id}/moderate", response_model=BaseResponse[Review])
async def moderate_review(
    review_id: int,
    moderation: ReviewModeration,
    moderator: dict = Depends(get_current_moderator_user)
):
    """Moderate a review (approve/reject/flag)."""
    try:
        moderated_review = await review_service.moderate_review(review_id, moderation)
        if not moderated_review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        action_msg = {
            ReviewStatus.APPROVED: "approved",
            ReviewStatus.REJECTED: "rejected", 
            ReviewStatus.FLAGGED: "flagged"
        }.get(moderation.status, "updated")
        
        return BaseResponse(
            data=moderated_review,
            message=f"Review {action_msg} successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moderating review: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 