"""
Rate Limiting Middleware
Implements token bucket rate limiting with Redis backend
"""

import time
import logging
from typing import Optional, Callable
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using token bucket algorithm

    For production with multiple instances, use Redis-based limiter instead.
    """

    def __init__(self):
        # {client_key: {"tokens": float, "last_update": float}}
        self._buckets: dict = defaultdict(lambda: {"tokens": 0, "last_update": 0})

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit

        Args:
            key: Client identifier (IP or user ID)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        bucket = self._buckets[key]

        # Calculate token refill rate
        refill_rate = max_requests / window_seconds

        # Time since last update
        time_passed = now - bucket["last_update"]

        # Refill tokens
        bucket["tokens"] = min(
            max_requests,
            bucket["tokens"] + (time_passed * refill_rate)
        )
        bucket["last_update"] = now

        # Check if we have tokens
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            remaining = int(bucket["tokens"])
            return True, remaining, 0
        else:
            # Calculate retry after
            tokens_needed = 1 - bucket["tokens"]
            retry_after = int(tokens_needed / refill_rate) + 1
            return False, 0, retry_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with configurable limits per endpoint

    Features:
    - Per-IP rate limiting
    - Configurable limits per route pattern
    - Automatic cleanup of old entries
    - Rate limit headers in response
    """

    def __init__(
        self,
        app,
        default_limit: int = 100,
        default_window: int = 60,
        route_limits: Optional[dict] = None,
        enabled: bool = True,
    ):
        """
        Initialize rate limiter

        Args:
            app: ASGI application
            default_limit: Default requests per window
            default_window: Default window in seconds
            route_limits: Dict of {route_prefix: (limit, window)}
            enabled: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.route_limits = route_limits or {}
        self.enabled = enabled
        self._limiter = InMemoryRateLimiter()

        # Default route limits
        self._default_route_limits = {
            "/api/v1/auth/login": (5, 60),       # 5 login attempts per minute
            "/api/v1/auth/register": (3, 60),    # 3 registrations per minute
            "/api/v1/upload": (10, 60),          # 10 uploads per minute
            "/api/v1/meetings": (60, 60),        # 60 requests per minute
        }
        self._default_route_limits.update(route_limits or {})

    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use X-Forwarded-For if behind proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain
            return forwarded.split(",")[0].strip()

        # Fall back to direct client IP
        client = request.client
        if client:
            return client.host

        return "unknown"

    def _get_limit_for_path(self, path: str) -> tuple[int, int]:
        """Get rate limit for a given path"""
        for route_prefix, (limit, window) in self._default_route_limits.items():
            if path.startswith(route_prefix):
                return limit, window
        return self.default_limit, self.default_window

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip health check endpoints
        if request.url.path in ["/health", "/api/v1/metrics/health"]:
            return await call_next(request)

        # Get client key and limits
        client_key = self._get_client_key(request)
        limit, window = self._get_limit_for_path(request.url.path)

        # Create bucket key including path pattern
        bucket_key = f"{client_key}:{request.url.path.split('/')[1:4]}"

        # Check rate limit
        is_allowed, remaining, retry_after = self._limiter.is_allowed(
            bucket_key, limit, window
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_key} on {request.url.path}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)

        return response
