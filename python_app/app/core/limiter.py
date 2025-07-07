from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Default rate limit for all endpoints
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"]) 