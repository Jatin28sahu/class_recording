"""
Background worker for processing audio files
"""
import threading
import traceback
from pathlib import Path
from typing import Dict, Any
from audio_to_transcribe_whisper import transcribe_audio_to_text
from class_test_graph import run_tutor_pipeline
from database import update_combined_md


# In-memory job storage
jobs: Dict[str, Dict[str, Any]] = {}
job_lock = threading.Lock()


def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get the current status of a job."""
    with job_lock:
        return jobs.get(job_id, {"status": "not_found"})


def process_audio_job(
    job_id: str,
    audio_path: str,
    student_level: str = "college",
    student_goal: str = "score well in final exam and actually understand the concepts"
):
    """
    Process an audio file through the complete pipeline.
    
    Steps:
    1. Transcribe audio using Whisper
    2. Run tutor pipeline to generate notes
    3. Update database with results
    4. Update job status
    """
    try:
        # Update status to processing
        with job_lock:
            jobs[job_id]["status"] = "processing"
            jobs[job_id]["progress"] = "Starting transcription..."
        
        # Convert path to Path object
        audio_file = Path(audio_path)
        
        # Step 1: Transcribe audio
        with job_lock:
            jobs[job_id]["progress"] = "Transcribing audio..."
        
        out_wav = audio_file.with_suffix(".converted.wav")
        save_json = audio_file.with_suffix(".deepgram.json")
        
        transcript = transcribe_audio_to_text(
            str(audio_file),
            out_wav=str(out_wav),
            save_json=str(save_json),
            language="auto",
            diarize=False,
        )
        
        # Step 2: Run tutor pipeline
        with job_lock:
            jobs[job_id]["progress"] = "Generating study materials..."
        
        result = run_tutor_pipeline(
            transcript=transcript,
            student_level=student_level,
            student_goal=student_goal,
        )
        
        combined_md = result["combined_markdown"]
        
        # Step 3: Update database
        with job_lock:
            jobs[job_id]["progress"] = "Saving results..."
        
        update_combined_md(job_id, combined_md)
        
        # Step 4: Update job status to completed
        with job_lock:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = "Processing complete"
            jobs[job_id]["result"] = combined_md
        
    except Exception as e:
        # Handle errors
        error_msg = f"Error processing job: {str(e)}"
        error_trace = traceback.format_exc()
        
        with job_lock:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = error_msg
            jobs[job_id]["error_trace"] = error_trace
        
        print(f"Job {job_id} failed:")
        print(error_trace)


def start_job(
    job_id: str,
    audio_path: str,
    student_level: str = "college",
    student_goal: str = "score well in final exam and actually understand the concepts"
):
    """
    Start a background job to process an audio file.
    
    Args:
        job_id: Unique identifier for the job
        audio_path: Path to the audio file
        student_level: Student level (default: "college")
        student_goal: Student's goal (default: exam preparation)
    """
    # Initialize job status
    with job_lock:
        jobs[job_id] = {
            "status": "pending",
            "progress": "Job queued",
            "error": None,
            "result": None
        }
    
    # Start processing in a background thread
    thread = threading.Thread(
        target=process_audio_job,
        args=(job_id, audio_path, student_level, student_goal),
        daemon=True
    )
    thread.start()
