"""
API v1 Router
Combines all API endpoints
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.meetings import router as meetings_router
from app.api.v1.upload import router as upload_router
from app.api.v1.tus_upload import router as tus_upload_router
from app.api.v1.review import router as review_router
from app.api.v1.websocket import router as websocket_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.export import router as export_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.integrations import router as integrations_router


api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(meetings_router)
api_router.include_router(upload_router)
api_router.include_router(tus_upload_router)  # Tus resumable upload
api_router.include_router(review_router)      # Human-in-the-loop review
api_router.include_router(websocket_router)   # Real-time progress updates
api_router.include_router(metrics_router)     # Metrics and monitoring
api_router.include_router(export_router)      # Meeting export (Markdown, HTML, JSON)
api_router.include_router(notifications_router)  # In-app notifications
api_router.include_router(integrations_router)   # External integrations (Slack, etc.)
