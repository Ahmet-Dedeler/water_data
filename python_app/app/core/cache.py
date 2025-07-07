from functools import lru_cache, wraps
from datetime import datetime, timedelta

def timed_lru_cache(seconds: int, maxsize: int = 128):
    """
    A time-aware LRU cache decorator.

    Args:
        seconds (int): The cache lifetime in seconds.
        maxsize (int): The maximum size of the LRU cache.
    """
    def wrapper_cache(func):
        # Apply the LRU cache to the function
        func = lru_cache(maxsize=maxsize)(func)
        
        # Add a lifetime to the cache
        lifetime = timedelta(seconds=seconds)
        expiration = datetime.utcnow() + lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            nonlocal expiration
            
            # Reset cache if it has expired
            if datetime.utcnow() >= expiration:
                func.cache_clear()
                expiration = datetime.utcnow() + lifetime

            return func(*args, **kwargs)

        # Copy over the cache_clear and cache_info methods
        wrapped_func.cache_clear = func.cache_clear
        wrapped_func.cache_info = func.cache_info
        
        return wrapped_func

    return wrapper_cache 