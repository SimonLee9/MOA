"""
MOA Backend - FastAPI Application
Main entry point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validate_settings_on_startup
from app.core.database import init_db, close_db
from app.api.v1.router import api_router
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler
    Runs on startup and shutdown
    """
    # Startup
    logger.info("Starting MOA Backend...")

    # Validate configuration
    validate_settings_on_startup()

    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down MOA Backend...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="MOA API",
    description="""
    **MOA (Minutes Of Action)** - AI 회의 액션 매니저

    회의를 녹음하고, AI가 자동으로:
    - 음성을 텍스트로 변환 (화자 분리 포함)
    - 회의 내용 요약
    - 액션 아이템 추출

    ## 주요 기능
    - 오디오 파일 업로드
    - AI 기반 회의 요약
    - 액션 아이템 관리
    - Human-in-the-Loop 검토
    """,
    version="2.1.0",
    docs_url="/docs" if settings.debug else None,  # Disable in production
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Security headers middleware (applied first, wraps all responses)
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=settings.is_production,
)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    default_limit=100,
    default_window=60,
    enabled=not settings.debug,  # Disable in debug mode for easier testing
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Include API router
app.include_router(api_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for container orchestration
    """
    return {
        "status": "healthy",
        "service": "MOA Backend",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "service": "MOA API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
