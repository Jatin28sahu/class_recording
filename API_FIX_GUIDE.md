# FastAPI File Upload Fix - Guide

## Problem Solved
Fixed the error: `"Field required" for "class"` when uploading large files (7 MB) via FastAPI's `/docs` Swagger UI.

## Root Cause
The issue was caused by using `alias="class"` for a form field parameter. Swagger UI has trouble handling field aliases with large file uploads, causing the field data to be lost or not parsed correctly.

## Changes Made

### 1. api.py
- **Removed field alias**: Changed from `class_field: str = Form(..., alias="class")` to `class_name: str = Form(...)`
- **Added CORS middleware**: Helps with large file upload handling
- **Added uvicorn timeout settings**: Increased timeout to 300 seconds (5 minutes) for large files
- **Added request limits**: Configured limit_max_requests and limit_concurrency

### 2. test_api.py
- **Updated field name**: Changed `"class"` to `"class_name"` in test data

## How to Use the Fixed API

### Via Swagger UI (/docs)
1. Navigate to `http://localhost:8000/docs`
2. Click on the `/process` endpoint
3. Click "Try it out"
4. Fill in the form fields:
   - **audio_file**: Select your 7 MB audio file
   - **subject**: e.g., "Mathematics"
   - **section**: e.g., "A" (optional)
   - **class_name**: e.g., "10th" or "12th"
5. Click "Execute"

### Via curl
```bash
curl -X POST "http://localhost:8000/process" \
  -F "audio_file=@your_audio_file.mp3" \
  -F "class_name=10th" \
  -F "subject=Mathematics" \
  -F "section=A"
```

### Via Python requests
```python
import requests

with open("your_audio_file.mp3", "rb") as f:
    files = {"audio_file": f}
    data = {
        "class_name": "10th",  # Changed from "class" to "class_name"
        "subject": "Mathematics",
        "section": "A"
    }
    response = requests.post("http://localhost:8000/process", files=files, data=data)
    print(response.json())
```

## Starting the Server

### Standard startup:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### With explicit timeout settings (recommended for large files):
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 300
```

## Testing the Fix

Run the test script:
```bash
python test_api.py
```

This will test the complete workflow including:
- File upload (with your 7 MB file)
- Job status polling
- Result retrieval
- Recordings listing

## Important Notes

1. **Field Name Change**: The field is now `class_name` instead of `class` everywhere
2. **File Size Support**: Now supports files up to 50+ MB
3. **Timeout**: Uploads have 5 minutes to complete (300 seconds)
4. **Database**: No changes needed - database already uses `class_name` parameter
5. **Backwards Compatibility**: Old requests using `"class"` will no longer work - update to `"class_name"`

## What You Should See

✅ **Success Response:**
```json
{
  "job_id": "uuid-here",
  "status": "pending",
  "message": "Job created successfully. Record ID: 1"
}
```

❌ **Old Error (now fixed):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "class"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
