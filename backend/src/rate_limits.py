from functools import wraps
from typing import Any, Callable, Dict

from django.http import HttpRequest, HttpResponse
from django_ratelimit import ALL, UNSAFE
from django_ratelimit.decorators import ratelimit

# Rate limiting settings for different types of endpoints
RATE_LIMIT_CONFIG = {
    # Authentication - strict limits
    "auth": {
        "rate": "5/m",  # 5 attempts per minute
        "method": ALL,
        "block": True,
    },
    # API endpoints for authenticated users
    "api_authenticated": {
        "rate": "100/m",  # 100 requests per minute
        "method": ALL,
        "block": True,
    },
    # API endpoints for unauthenticated users
    "api_anonymous": {
        "rate": "20/m",  # 20 requests per minute
        "method": ALL,
        "block": True,
    },
    # Game endpoints - stricter limits
    "game": {
        "rate": "30/m",  # 30 requests per minute
        "method": ALL,
        "block": True,
    },
    # Admin endpoints - very strict limits
    "admin": {
        "rate": "10/m",  # 10 requests per minute
        "method": ALL,
        "block": True,
    },
    # File uploads - strict limits
    "file_upload": {
        "rate": "5/m",  # 5 uploads per minute
        "method": UNSAFE,
        "block": True,
    },
    # WebSocket connections
    "websocket": {
        "rate": "60/m",  # 60 connections per minute
        "method": ALL,
        "block": True,
    },
}


def get_rate_limit_config(endpoint_type: str) -> Dict[str, Any]:
    """Get rate limiting configuration for endpoint type."""
    return RATE_LIMIT_CONFIG.get(endpoint_type, RATE_LIMIT_CONFIG["api_authenticated"])


# Decorators for rate limiting - applied to view methods
def rate_limit_auth_method(view_method: Callable) -> Callable:
    """Rate limiting for authentication methods."""
    return ratelimit(key="ip", rate="5/m", method=ALL, block=True)(view_method)


def rate_limit_api_method(view_method: Callable) -> Callable:
    """Rate limiting for API endpoint methods (ViewSet support)."""
    rl_decorator = ratelimit(key="user_or_ip", rate="5/m", method=ALL, block=True)

    @wraps(view_method)
    def wrapped(self, request: object, *args, **kwargs):
        return rl_decorator(lambda req, *a, **kw: view_method(self, req, *a, **kw))(
            request, *args, **kwargs
        )

    return wrapped


def rate_limit_game_method(view_method: Callable) -> Callable:
    """Rate limiting for game endpoint methods."""
    rl_decorator = ratelimit(key="user_or_ip", rate="100/m", method=ALL, block=True)

    @wraps(view_method)
    def wrapped(self, request: object, *args, **kwargs):
        return rl_decorator(lambda req, *a, **kw: view_method(self, req, *a, **kw))(
            request, *args, **kwargs
        )

    return wrapped


def rate_limit_admin_method(view_method: Callable) -> Callable:
    """Rate limiting for admin endpoint methods."""
    rl_decorator = ratelimit(key="user", rate="100/m", method=ALL, block=True)

    @wraps(view_method)
    def wrapped(self, request: object, *args, **kwargs):
        return rl_decorator(lambda req, *a, **kw: view_method(self, req, *a, **kw))(
            request, *args, **kwargs
        )

    return wrapped


def rate_limit_file_upload_method(view_method: Callable) -> Callable:
    """Rate limiting for file upload methods."""
    rl_decorator = ratelimit(key="user", rate="5/m", method=UNSAFE, block=True)(
        view_method
    )

    @wraps(view_method)
    def wrapped(self, request: object, *args, **kwargs):
        return rl_decorator(lambda req, *a, **kw: view_method(self, req, *a, **kw))(
            request, *args, **kwargs
        )

    return wrapped


# Decorators for functions (e.g., api_view)
def rate_limit_auth(
    view_func: Callable[[HttpRequest], HttpResponse]
) -> Callable[[HttpRequest], HttpResponse]:
    """Rate limiting for authentication."""
    return ratelimit(key="ip", rate="5/m", method=ALL, block=True)(view_func)


def get_user_identifier(request: HttpRequest) -> str:
    """Get unique identifier for user (user ID or IP address)."""
    if request.user.is_authenticated:
        return f"user_{request.user.id}"
    else:
        # Get IP address from request
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        return f"ip_{ip}"


def check_rate_limit(request: HttpRequest, endpoint_type: str) -> bool:
    """
    Check if request is within rate limit for given endpoint type.
    
    This is a simplified implementation that always returns True.
    In production, you would integrate with a proper rate limiting backend.
    """
    # For now, always allow the request
    # In a real implementation, you would check against Redis/Memcached
    # and return False if the limit is exceeded
    return True
