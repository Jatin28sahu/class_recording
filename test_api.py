"""
Test script for the Class Recording API
"""
import requests
import time
from pathlib import Path


def test_api():
    """Test the complete API workflow."""
    base_url = "http://localhost:8000"
    
    # Test 1: Root endpoint
    print("=" * 60)
    print("Test 1: Testing root endpoint...")
    print("=" * 60)
    response = requests.get(base_url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    # Test 2: Upload and process audio
    print("=" * 60)
    print("Test 2: Uploading and processing audio file...")
    print("=" * 60)
    
    # Check if test audio files exist
    test_files = ["transformer.mp3", "ai_podcast.mp3"]
    audio_file_path = None
    
    for test_file in test_files:
        if Path(test_file).exists():
            audio_file_path = test_file
            break
    
    if not audio_file_path:
        print("ERROR: No test audio file found!")
        print(f"Please ensure one of these files exists: {test_files}")
        return
    
    print(f"Using audio file: {audio_file_path}")
    
    with open(audio_file_path, "rb") as f:
        files = {"audio_file": f}
        data = {
            "class_name": "Computer Science",
            "subject": "Artificial Intelligence",
            "section": "A"
        }
        
        response = requests.post(f"{base_url}/process", files=files, data=data)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result}")
    
    if response.status_code != 200:
        print("ERROR: Failed to create job!")
        return
    
    job_id = result["job_id"]
    print(f"\nJob ID: {job_id}\n")
    
    # Test 3: Poll for job status
    print("=" * 60)
    print("Test 3: Polling job status...")
    print("=" * 60)
    
    max_attempts = 60  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f"{base_url}/status/{job_id}")
        status_data = response.json()
        
        status = status_data["status"]
        progress = status_data.get("progress", "N/A")
        
        print(f"[Attempt {attempt + 1}] Status: {status} | Progress: {progress}")
        
        if status == "completed":
            print("\n✅ Job completed successfully!\n")
            break
        elif status == "failed":
            print(f"\n❌ Job failed: {status_data.get('error')}\n")
            return
        
        time.sleep(5)
        attempt += 1
    
    if attempt >= max_attempts:
        print("\n⏱️ Timeout: Job took too long to complete\n")
        return
    
    # Test 4: Get result
    print("=" * 60)
    print("Test 4: Fetching result...")
    print("=" * 60)
    
    response = requests.get(f"{base_url}/result/{job_id}")
    result_data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Job Status: {result_data['status']}")
    
    if result_data.get("combined_md"):
        combined_md = result_data["combined_md"]
        preview_length = 500
        print(f"\nCombined Markdown Preview (first {preview_length} chars):")
        print("-" * 60)
        print(combined_md[:preview_length])
        print("...\n")
        
        # Save to file
        output_file = f"test_result_{job_id[:8]}.md"
        with open(output_file, "w") as f:
            f.write(combined_md)
        print(f"✅ Full result saved to: {output_file}\n")
    
    # Test 5: Get result as plain markdown
    print("=" * 60)
    print("Test 5: Fetching result as plain markdown...")
    print("=" * 60)
    
    response = requests.get(f"{base_url}/result/{job_id}/markdown")
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.text)} characters\n")
    
    # Test 6: List recordings
    print("=" * 60)
    print("Test 6: Listing all recordings...")
    print("=" * 60)
    
    response = requests.get(f"{base_url}/recordings")
    recordings_data = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"Total recordings: {recordings_data['total']}")
    
    if recordings_data["recordings"]:
        print("\nRecent recordings:")
        for rec in recordings_data["recordings"][:3]:
            print(f"  - ID: {rec['id']} | Class: {rec['class']} | Subject: {rec['subject']} | Date: {rec['date']}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    print(f"\nAPI Documentation: {base_url}/docs")
    print(f"ReDoc: {base_url}/redoc")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Class Recording API Test Suite")
    print("=" * 60)
    print("\nMake sure the API server is running:")
    print("  uvicorn api:app --reload --host 0.0.0.0 --port 8000")
    print("\n" + "=" * 60 + "\n")
    
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server!")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
