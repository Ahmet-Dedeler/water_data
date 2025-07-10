from fastapi import APIRouter

from app.api.endpoints import (
    achievements, admin, analytics, api_keys, calculator, challenges,
    coaching, comments, drinks, exports, gamification, health_goals,
    health, notifications, push, recommendations, reminders, reviews,
    search, social, users, water
)

router = APIRouter()

router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
router.include_router(calculator.router, prefix="/calculator", tags=["calculator"])
router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
router.include_router(coaching.router, prefix="/coaching", tags=["coaching"])
router.include_router(comments.router, prefix="/comments", tags=["comments"])
router.include_router(drinks.router, prefix="/drinks", tags=["drinks"])
router.include_router(exports.router, prefix="/exports", tags=["exports"])
router.include_router(gamification.router, prefix="/gamification", tags=["gamification"])
router.include_router(health_goals.router, prefix="/health-goals", tags=["health-goals"])
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
router.include_router(push.router, prefix="/push", tags=["push"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(social.router, prefix="/social", tags=["social"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(water.router, prefix="/water", tags=["water"]) 