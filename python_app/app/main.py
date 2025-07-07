from app.api.endpoints import (
    users, utils, auth, admin, water, analytics, social, reminders,
    profiles, achievements, friends, notifications, challenges, coaching,
    health, calculator, drinks
)
from app.db.database import engine, Base
from app.utils.scheduler import scheduler

app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(achievements.router, prefix="/api/v1/achievements", tags=["achievements"])
app.include_router(friends.router, prefix="/api/v1/friends", tags=["friends"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(challenges.router, prefix="/api/v1/challenges", tags=["challenges"])
app.include_router(coaching.router, prefix="/api/v1/coaching", tags=["coaching"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(calculator.router, prefix="/api/v1/calculator", tags=["calculator"])
app.include_router(drinks.router, prefix="/api/v1/drinks", tags=["drinks"])

# Simple route for testing
@app.get("/")
def read_root():
    return {"message": "Welcome to the Water Bottles API!"} 