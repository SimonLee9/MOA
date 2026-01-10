"""
MOA Backend - FastAPI Application
Main entry point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import init_db, close_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler
    Runs on startup and shutdown
    """
    # Startup
    print("🚀 Starting MOA Backend...")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down MOA Backend...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="MOA API",
    description="""
    **MOA (Minutes Of Action)** - AI 회의 액션 매니저
    
    회의를 녹음하고, AI가 자동으로:
    - 🎙️ 음성을 텍스트로 변환 (화자 분리 포함)
    - 📝 회의 내용 요약
    - ✅ 액션 아이템 추출
    
    ## 주요 기능
    - 오디오 파일 업로드
    - AI 기반 회의 요약
    - 액션 아이템 관리
    - Human-in-the-Loop 검토
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
