"""
Security middleware and utility stack for VoteWise.

Provides rate limiting, security headers, request logging, and CORS.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings

logger = logging.getLogger("votewise.middleware")


class RateLimitMiddleware:
    """Token bucket rate limiter per IP address."""

    def __init__(self, app, rpm: int = 60, burst: int = 20):
        self.app = app
        self.rpm = rpm
        self.burst = burst
        self._buckets: dict[str, list] = defaultdict(lambda: [burst, time.monotonic()])

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or settings.app_env == "testing":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"

        tokens, last_time = self._buckets[client_ip]
        now = time.monotonic()
        elapsed = now - last_time
        tokens = min(self.burst, tokens + elapsed * (self.rpm / 60))

        if tokens < 1:
            response = JSONResponse(
                status_code=429,
                content={"error": "rate_limit_exceeded", "message": "Too many requests"},
            )
            await response(scope, receive, send)
            return

        self._buckets[client_ip] = [tokens - 1, now]
        await self.app(scope, receive, send)


def register_middleware(app: FastAPI) -> None:
    """Register all middleware in correct order."""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        rpm=settings.rate_limit_rpm,
        burst=settings.rate_limit_burst,
    )

    # Security headers + request logging
    @app.middleware("http")
    async def security_and_logging(request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Request-ID"] = request_id
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )

        elapsed = round((time.monotonic() - start) * 1000, 2)
        response.headers["X-Response-Time"] = f"{elapsed}ms"

        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms) [{request_id}]"
        )
        return response
