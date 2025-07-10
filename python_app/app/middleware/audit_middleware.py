import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.services.security_system_service import SecuritySystemService
from app.schemas.security_system import AuditLogCreate
from app.models.security_system import EventType, ActionStatus
from app.core.config import settings

# This is a simplified way to get a DB session in middleware.
# In a complex app, you might use a context variable or another pattern.
async_engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # We only want to log certain events automatically.
        # More specific events should be logged within the endpoints themselves.
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and response.status_code < 400:
            # In a real app, you would get the user ID from the request state or token
            user_id = request.state.user.id if hasattr(request.state, "user") else None

            details = {
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "process_time_ms": int(process_time * 1000)
            }
            
            # This is a generic event type. Specific endpoints should log more descriptive events.
            event_type = EventType.USER_ACTION # This should be more specific in a real app
            
            log_entry = AuditLogCreate(
                user_id=user_id,
                event_type=event_type,
                status=ActionStatus.SUCCESS,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", "unknown"),
                details=details
            )
            
            # Create a new DB session just for this middleware task
            async with AsyncSessionLocal() as db:
                security_service = SecuritySystemService(db)
                await security_service.log_audit_event(log_entry)

        return response 