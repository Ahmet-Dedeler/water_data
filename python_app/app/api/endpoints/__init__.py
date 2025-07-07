from fastapi import APIRouter
from . import (
    users, health_goals, water, reviews, recommendations,
    search, notifications, exports, analytics, achievements, social,
    gamification
)
from . import health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(health_goals.router, prefix="/health-goals", tags=["Health Goals"])
api_router.include_router(water.router, prefix="/waters", tags=["waters"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
api_router.include_router(social.router, prefix="/social", tags=["Social"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["Gamification"]) 