"""
File Upload API endpoint
Handles audio file uploads to MinIO/S3
"""

from uuid import UUID
import io

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import boto3
from botocore.exceptions import ClientError

from app.core.database import get_db
from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.models.meeting import Meeting, MeetingStatus
from app.schemas.meeting import UploadResponse


router = APIRouter(prefix="/meetings", tags=["Upload"])


# Allowed audio formats
ALLOWED_EXTENSIONS = {".m4a", ".mp3", ".wav", ".webm", ".ogg", ".flac", ".aac"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


def get_s3_client():
    """Create S3/MinIO client"""
    return boto3.client(
        "s3",
        endpoint_url=f"{'https' if settings.minio_use_ssl else 'http'}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


def ensure_bucket_exists(s3_client):
    """Ensure the storage bucket exists"""
    try:
        s3_client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        # Bucket doesn't exist, create it
        s3_client.create_bucket(Bucket=settings.minio_bucket)


@router.post("/{meeting_id}/upload", response_model=UploadResponse)
async def upload_audio(
    meeting_id: UUID,
    file: UploadFile = File(..., description="Audio file to upload"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload audio file for a meeting
    
    Supported formats: m4a, mp3, wav, webm, ogg, flac, aac
    Max size: 500MB
    """
    # Verify meeting exists and belongs to user
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if already has audio
    if meeting.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting already has an audio file. Delete the meeting and create a new one."
        )
    
    # Validate file extension
    filename = file.filename or "audio"
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )
    
    # Generate S3 key
    s3_key = f"meetings/{current_user.id}/{meeting_id}/audio{extension}"
    
    try:
        # Upload to S3/MinIO
        s3_client = get_s3_client()
        ensure_bucket_exists(s3_client)
        
        s3_client.upload_fileobj(
            io.BytesIO(content),
            settings.minio_bucket,
            s3_key,
            ExtraArgs={
                "ContentType": file.content_type or "audio/mpeg",
            }
        )
        
        # Generate URL
        audio_url = f"{'https' if settings.minio_use_ssl else 'http'}://{settings.minio_endpoint}/{settings.minio_bucket}/{s3_key}"
        
        # Update meeting
        meeting.audio_file_url = audio_url
        meeting.status = MeetingStatus.UPLOADED
        
        await db.commit()
        await db.refresh(meeting)
        
        return UploadResponse(
            meeting_id=meeting.id,
            audio_file_url=audio_url,
            audio_duration=None,  # Would need audio processing to get duration
            status=meeting.status,
            message="Upload successful. Ready for processing."
        )
        
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/{meeting_id}/process", response_model=dict)
async def start_processing(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start AI processing for a meeting
    
    This triggers the AI pipeline:
    1. Speech-to-Text (STT)
    2. Summary generation
    3. Action item extraction
    """
    # Verify meeting exists and belongs to user
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if audio file exists
    if not meeting.audio_file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file uploaded. Please upload an audio file first."
        )
    
    # Check if already processing or completed
    if meeting.status == MeetingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting is already being processed"
        )
    
    if meeting.status == MeetingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has already been processed"
        )
    
    # Update status to processing
    meeting.status = MeetingStatus.PROCESSING
    await db.commit()
    
    # TODO: Trigger Celery task for AI processing
    # from app.tasks.ai_tasks import process_meeting
    # process_meeting.delay(str(meeting_id))
    
    return {
        "meeting_id": str(meeting_id),
        "status": "processing",
        "message": "AI processing started. Check status endpoint for progress."
    }
