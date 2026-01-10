"""
API v1 Router
Combines all API endpoints
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.meetings import router as meetings_router
from app.api.v1.upload import router as upload_router


api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(meetings_router)
api_router.include_router(upload_router)
