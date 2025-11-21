"""
FastAPI application for class recording processing
"""
import uuid
import shutil
from pathlib import Path
from typing import Optional, Annotated
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from models import (
    JobResponse,
    JobStatusResponse,
    JobResultResponse,
    RecordingResponse,
    RecordingsListResponse
)
from database import (
    insert_recording,
    get_recording_by_job_id,
    get_all_recordings,
    get_recording_by_id
)
from worker import start_job, get_job_status


# Initialize FastAPI app
app = FastAPI(
    title="Class Recording API",
    description="API for processing class audio recordings and generating study materials",
    version="1.0.0"
)

# Add CORS middleware to handle large file uploads
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Class Recording API",
        "version": "1.0.0",
        "endpoints": {
            "POST /process": "Upload and process audio file",
            "GET /status/{job_id}": "Check job status",
            "GET /result/{job_id}": "Get processing result",
            "GET /recordings": "List all recordings"
        }
    }


@app.post("/process", response_model=JobResponse)
async def process_audio(
    audio_file: UploadFile = File(..., description="Audio file to process"),
    subject: str = Form(..., description="Subject name"),
    section: Optional[str] = Form(None, description="Section (optional)"),
    class_name: str = Form(..., description="Class/Grade (e.g., 10th, 12th)")
):
    """
    Upload and process an audio file.
    
    This endpoint:
    1. Saves the uploaded audio file
    2. Creates a database entry
    3. Starts a background job for processing
    4. Returns job_id for tracking
    
    The processing includes:
    - Audio transcription
    - Study notes generation
    - Misconceptions detection
    - Practice questions creation
    - Resource recommendations
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file with job_id in filename
        file_extension = Path(audio_file.filename).suffix
        audio_filename = f"{job_id}{file_extension}"
        audio_path = UPLOADS_DIR / audio_filename
        
        # Save file to disk
        with audio_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        # Insert record into database
        record_id = insert_recording(
            class_name=class_name,
            subject=subject,
            audio_filename=audio_filename,
            job_id=job_id,
            section=section
        )
        
        # Start background processing job
        start_job(
            job_id=job_id,
            audio_path=str(audio_path)
        )
        
        return JobResponse(
            job_id=job_id,
            status="pending",
            message=f"Job created successfully. Record ID: {record_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    """
    Check the status of a processing job.
    
    Possible statuses:
    - pending: Job is queued
    - processing: Job is currently being processed
    - completed: Job finished successfully
    - failed: Job encountered an error
    - not_found: Job ID doesn't exist
    """
    job_status = get_job_status(job_id)
    
    if job_status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job_id,
        status=job_status["status"],
        progress=job_status.get("progress"),
        error=job_status.get("error")
    )


@app.get("/result/{job_id}", response_model=JobResultResponse)
def get_result(job_id: str):
    """
    Get the result of a completed job.
    
    Returns:
    - combined_md: The generated study materials in Markdown format
    - status: Current job status
    - error: Error message if job failed
    """
    # Check job status
    job_status = get_job_status(job_id)
    
    if job_status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_status["status"] == "failed":
        return JobResultResponse(
            job_id=job_id,
            status="failed",
            error=job_status.get("error")
        )
    
    if job_status["status"] in ["pending", "processing"]:
        return JobResultResponse(
            job_id=job_id,
            status=job_status["status"],
            combined_md=None
        )
    
    # Job completed - get from database
    recording = get_recording_by_job_id(job_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found in database")
    
    return JobResultResponse(
        job_id=job_id,
        status="completed",
        combined_md=recording.get("combined_md")
    )


@app.get("/result/{job_id}/markdown", response_class=PlainTextResponse)
def get_result_markdown(job_id: str):
    """
    Get the result as plain markdown text (useful for direct download).
    """
    job_status = get_job_status(job_id)
    
    if job_status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job_status['status']}"
        )
    
    recording = get_recording_by_job_id(job_id)
    
    if not recording or not recording.get("combined_md"):
        raise HTTPException(status_code=404, detail="Result not found")
    
    return recording["combined_md"]


@app.get("/recordings", response_model=RecordingsListResponse)
def list_recordings(limit: int = 100, offset: int = 0):
    """
    List all recordings with pagination.
    
    Args:
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
    """
    recordings = get_all_recordings(limit=limit, offset=offset)
    
    # Convert to response model
    recording_responses = [
        RecordingResponse(
            id=rec["id"],
            date=rec["date"],
            class_name=rec["class"],
            section=rec["section"],
            subject=rec["subject"],
            audio_filename=rec["audio_filename"],
            job_id=rec["job_id"],
            created_at=rec["created_at"]
        )
        for rec in recordings
    ]
    
    return RecordingsListResponse(
        recordings=recording_responses,
        total=len(recording_responses),
        limit=limit,
        offset=offset
    )


@app.get("/recordings/{record_id}")
def get_recording(record_id: int):
    """
    Get a specific recording by ID.
    """
    recording = get_recording_by_id(record_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return recording


if __name__ == "__main__":
    import uvicorn
    # Increase timeout and request size limits for large file uploads
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=300,  # 5 minutes
        limit_max_requests=1000,
        limit_concurrency=100
    )
