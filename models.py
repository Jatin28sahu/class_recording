"""
Pydantic models for FastAPI request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProcessRequest(BaseModel):
    """Request model for processing audio files"""
    class_name: str = Field(..., alias="class", description="Class name")
    subject: str = Field(..., description="Subject name")
    section: Optional[str] = Field(None, description="Section (optional)")

    class Config:
        populate_by_name = True


class JobResponse(BaseModel):
    """Response model for job creation"""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status check"""
    job_id: str
    status: str
    progress: Optional[str] = None
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    """Response model for completed job result"""
    job_id: str
    status: str
    combined_md: Optional[str] = None
    error: Optional[str] = None


class RecordingResponse(BaseModel):
    """Response model for a single recording"""
    id: int
    date: str
    class_name: str = Field(..., alias="class")
    section: Optional[str]
    subject: str
    audio_filename: str
    job_id: str
    created_at: str

    class Config:
        populate_by_name = True


class RecordingsListResponse(BaseModel):
    """Response model for list of recordings"""
    recordings: list[RecordingResponse]
    total: int
    limit: int
    offset: int
