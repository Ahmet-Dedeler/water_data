import logging
import uvicorn
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
from fastapi.staticfiles import StaticFiles
import os


# --- Importing from app directory ---
from app.core.logging_config import setup_logging
from app.core.config import settings
from app.api.endpoints import (
    users, water, health_goals, achievements, social,
    notifications, analytics, admin, api_keys, leaderboards,
    water_quality, coaching, health_integration, reviews, recommendations,
    search, exports, reminders, push, comments, gamification,
    drinks, calculator, health, challenges, friends, activity_feed,
    messaging, advanced_analytics, notification_system
)
from app.db.database import SessionLocal, engine, Base
from app.services.scheduler_service import SchedulerManager

# --- Pre-startup setup ---

# Set up structured logging before anything else
setup_logging()
log = logging.getLogger(__name__)

# Initialize rate limiter from settings
limiter = Limiter(key_func=lambda request: request.client.host)

# --- Lifespan Management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    log.info("Application starting up...")

    # Run database migrations
    log.info("Running database migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    log.info("Database migrations complete.")

    # Create database tables (if they don't exist)
    Base.metadata.create_all(bind=engine)
    # Start the scheduler
    await SchedulerManager.start()
    log.info("Application startup complete.")
    
    yield
    
    # --- Shutdown ---
    log.info("Application shutting down...")
    await SchedulerManager.shutdown()
    log.info("Application shutdown complete.")


# --- FastAPI App Initialization ---

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# --- Middleware Configuration ---

# Global Exception Handler - must be the first middleware added
@app.middleware("http")
async def global_exception_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        log.error("An unhandled exception occurred", exc_info=True, extra={"error": str(e)})
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please contact support."},
        )

# Add Rate Limiter state and middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- API Router Configuration ---

api_router = APIRouter(prefix=settings.API_V1_STR)

api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(water.router, prefix="/water", tags=["Water"])
api_router.include_router(water_quality.router, prefix="/water-quality", tags=["Water Quality"])
api_router.include_router(health_goals.router, prefix="/health-goals", tags=["Health Goals"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["Achievements"])
api_router.include_router(social.router, prefix="/social", tags=["Social"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(leaderboards.router, prefix="/leaderboards", tags=["Leaderboards"])
api_router.include_router(coaching.router, prefix="/coaching", tags=["Coaching"])
api_router.include_router(health_integration.router, prefix="/health-integration", tags=["Health Integration"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(push.router, prefix="/push", tags=["Push Notifications"])
api_router.include_router(comments.router, prefix="/comments", tags=["Comments"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
api_router.include_router(drinks.router, prefix="/drinks", tags=["Drinks"])
api_router.include_router(calculator.router, prefix="/calculator", tags=["Calculator"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["Challenges"])
api_router.include_router(friends.router, prefix="/friends", tags=["Friends"])
api_router.include_router(activity_feed.router, prefix="/activity-feed", tags=["Activity Feed"])
api_router.include_router(messaging.router, prefix="/messaging", tags=["Messaging"])
api_router.include_router(advanced_analytics.router, prefix="/advanced-analytics", tags=["Advanced Analytics"])

app.include_router(api_router)

# --- Root Endpoint ---

@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/v1/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Water Bottle Tracker API",
        "version": "1.0.0",
        "description": "A comprehensive water bottle health tracking system",
        "features": [
            "User management and authentication",
            "Water consumption tracking",
            "Health goals and achievements",
            "Social features and friend system",
            "Activity feed and messaging",
            "Gamification and leaderboards",
            "Health app integration",
            "Advanced analytics and insights",
            "Hydration coaching",
            "Water quality tracking",
            "Diverse drink type support",
            "Caffeine logging",
            "Personalized recommendations",
            "Export and reporting",
            "Real-time analytics",
            "AI-powered insights"
        ],
        "endpoints": {
            "users": "/api/v1/users",
            "water": "/api/v1/water",
            "achievements": "/api/v1/achievements",
            "admin": "/api/v1/admin",
            "analytics": "/api/v1/analytics",
            "api_keys": "/api/v1/api-keys",
            "calculator": "/api/v1/calculator",
            "challenges": "/api/v1/challenges",
            "coaching": "/api/v1/coaching",
            "comments": "/api/v1/comments",
            "drinks": "/api/v1/drinks",
            "exports": "/api/v1/exports",
            "gamification": "/api/v1/gamification",
            "health_goals": "/api/v1/health-goals",
            "health_integration": "/api/v1/health-integration",
            "health": "/api/v1/health",
            "leaderboards": "/api/v1/leaderboards",
            "notifications": "/api/v1/notifications",
            "push": "/api/v1/push",
            "recommendations": "/api/v1/recommendations",
            "reminders": "/api/v1/reminders",
            "reviews": "/api/v1/reviews",
            "search": "/api/v1/search",
            "social": "/api/v1/social",
            "water_quality": "/api/v1/water-quality",
            "friends": "/api/v1/friends",
            "activity_feed": "/api/v1/activity-feed",
            "messaging": "/api/v1/messaging",
            "advanced_analytics": "/api/v1/advanced-analytics"
        }
    }

# --- Main entry point for running the app ---
if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 