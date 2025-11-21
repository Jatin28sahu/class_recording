# Class Recording API Documentation

FastAPI-based service for processing class audio recordings and generating comprehensive study materials.

## Features

- ✅ **Audio Transcription**: Converts audio/video to text using Whisper
- ✅ **AI-Powered Study Materials**: Generates notes, misconceptions, practice questions, and resources
- ✅ **Multi-Model Support**: Uses both OpenAI (GPT-4, GPT-5) and Gemini models
- ✅ **Async Job Processing**: Long-running pipeline with job_id tracking
- ✅ **SQLite Database**: Persistent storage of all recordings
- ✅ **RESTful API**: Easy integration with any client

## Installation

```bash
pip install -r requirements.txt
```

## Starting the Server

```bash
# Development mode with auto-reload
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python api.py
```

Server will be available at: `http://localhost:8000`

## API Endpoints

### 1. Root Endpoint
```
GET /
```
Returns API information and available endpoints.

### 2. Process Audio File
```
POST /process
```

Upload and process an audio file.

**Request (multipart/form-data):**
- `audio_file` (file, required): Audio file to process
- `class` (string, required): Class name
- `subject` (string, required): Subject name
- `section` (string, optional): Section

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Job created successfully. Record ID: 1"
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/process" \
  -F "audio_file=@/path/to/audio.mp3" \
  -F "class=Mathematics" \
  -F "subject=Calculus" \
  -F "section=A"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/process"
files = {"audio_file": open("audio.mp3", "rb")}
data = {
    "class": "Mathematics",
    "subject": "Calculus",
    "section": "A"  # optional
}

response = requests.post(url, files=files, data=data)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")
```

### 3. Check Job Status
```
GET /status/{job_id}
```

Check the current status of a processing job.

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "progress": "Generating study materials...",
  "error": null
}
```

**Possible statuses:**
- `pending`: Job is queued
- `processing`: Job is currently being processed
- `completed`: Job finished successfully
- `failed`: Job encountered an error

**Example:**
```bash
curl "http://localhost:8000/status/123e4567-e89b-12d3-a456-426614174000"
```

### 4. Get Job Result
```
GET /result/{job_id}
```

Get the processed result (combined markdown).

**Response (completed):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "combined_md": "# Class Tutor – Combined Output\n\n..."
}
```

**Example:**
```bash
curl "http://localhost:8000/result/123e4567-e89b-12d3-a456-426614174000"
```

### 5. Get Result as Markdown
```
GET /result/{job_id}/markdown
```

Get the result as plain text markdown (useful for direct download).

**Example:**
```bash
curl "http://localhost:8000/result/123e4567-e89b-12d3-a456-426614174000/markdown" -o result.md
```

### 6. List All Recordings
```
GET /recordings?limit=100&offset=0
```

Get a paginated list of all recordings.

**Query Parameters:**
- `limit` (int, default: 100): Maximum records to return
- `offset` (int, default: 0): Number of records to skip

**Response:**
```json
{
  "recordings": [
    {
      "id": 1,
      "date": "2025-11-21",
      "class": "Mathematics",
      "section": "A",
      "subject": "Calculus",
      "audio_filename": "123e4567-e89b-12d3-a456-426614174000.mp3",
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "created_at": "2025-11-21 17:45:00"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### 7. Get Specific Recording
```
GET /recordings/{record_id}
```

Get details of a specific recording by database ID.

## Database Schema

```sql
CREATE TABLE recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    class TEXT NOT NULL,
    section TEXT,
    subject TEXT NOT NULL,
    audio_filename TEXT NOT NULL,
    combined_md TEXT,
    job_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Processing Pipeline

1. **Audio Upload**: File is saved to `uploads/` directory
2. **Database Entry**: Record created in SQLite database
3. **Background Job**: Processing starts asynchronously
4. **Transcription**: Audio converted to text using Whisper
5. **AI Processing**: LangGraph pipeline generates study materials:
   - Node 1A: Structured class notes (GPT-4)
   - Node 1B: Misconception detection (GPT-4-mini)
   - Node 2: Practice questions (GPT-4-mini)
   - Node 3: Resources & real-life applications (GPT-5)
   - Node 4: Study plan & actions (Gemini-1.5-flash)
6. **Result Storage**: Combined markdown saved to database

## Model Configuration

The system uses a multi-model approach:

- **NODE_1A** (Notes): `gpt-4o` (OpenAI)
- **NODE_1B** (Misconceptions): `gpt-4o-mini` (OpenAI)
- **NODE_2** (Practice): `gpt-4o-mini` (OpenAI)
- **NODE_3** (Resources): `gpt-5` (OpenAI)
- **NODE_4** (Actions): `gemini-1.5-flash` (Google Gemini)

## Complete Workflow Example

```python
import requests
import time

# 1. Upload and process audio
url = "http://localhost:8000/process"
files = {"audio_file": open("lecture.mp3", "rb")}
data = {
    "class": "Physics",
    "subject": "Quantum Mechanics",
    "section": "B"
}

response = requests.post(url, files=files, data=data)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# 2. Poll for status
while True:
    status_response = requests.get(f"http://localhost:8000/status/{job_id}")
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status == "completed":
        break
    elif status == "failed":
        print("Job failed:", status_response.json().get("error"))
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again

# 3. Get the result
result_response = requests.get(f"http://localhost:8000/result/{job_id}")
combined_md = result_response.json()["combined_md"]

# Save to file
with open("study_materials.md", "w") as f:
    f.write(combined_md)

print("Study materials saved to study_materials.md")
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Job or resource not found
- `500 Internal Server Error`: Server error during processing

Error responses include a detail message:
```json
{
  "detail": "Error description here"
}
```

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## File Structure

```
/workspaces/class_recording/
├── api.py                    # FastAPI application
├── database.py               # SQLite operations
├── models.py                 # Pydantic models
├── worker.py                 # Background job processor
├── class_test_graph.py       # LangGraph pipeline
├── audio_to_transcribe_whisper.py  # Transcription
├── recordings.db             # SQLite database
├── uploads/                  # Uploaded audio files
└── requirements.txt          # Python dependencies
```

## Environment Variables

Required environment variables (set in `.env`):

```
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
DEEPGRAM_API_KEY=your_deepgram_key
LANGCHAIN_API_KEY=your_langchain_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=SMART_CLASS_NOTES
```

## Notes

- The `uploads/` directory and `recordings.db` file are created automatically
- Audio files are stored with UUID-based filenames for uniqueness
- All LLM calls are tracked in LangSmith for monitoring
- The system supports various audio formats (mp3, wav, m4a, etc.)
- Processing time depends on audio length and model availability

## Troubleshooting

**Job stays in "pending" status:**
- Check server logs for errors
- Verify API keys are set correctly
- Ensure models are accessible

**"Job not found" error:**
- Verify the job_id is correct
- Jobs are stored in-memory and will be lost on server restart

**Database errors:**
- Ensure write permissions in the project directory
- Check if `recordings.db` is locked by another process
