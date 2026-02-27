import requests
import base64
import json
import time
import os

# CONFIGURATION
# ----------------
# If running on the SAME machine, use localhost
BASE_URL = "http://127.0.0.1:8000" 
# If testing from another device, use your IP: http://192.168.1.X:8000

def get_base64_image(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def test_scan_api():
    print(f"Testing API at: {BASE_URL}/api/scan/analyze")
    
    # 1. Load a test image (using a placeholder or one if it exists)
    # We will try to find an image in the current dir or subdirs
    test_image_path = "test_face.jpg"
    
    # Create a dummy image if none exists (just to test 400 bad request or connection)
    # But ideally we want a real test. Let's assume user has one or we use a zero-byte one 
    # to just check connectivity.
    
    # Better: Search for a png/jpg in the project to use
    found_images = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg'))]
    if found_images:
        test_image_path = found_images[0]
        print(f"Using test image: {test_image_path}")
        b64_img = get_base64_image(test_image_path)
    else:
        print("No local image found. Generating a dummy packet.")
        b64_img = "dummy_base64_string"

    # 2. Construct Payload (Simulating 5 frames)
    frames = []
    for i in range(5):
        frames.append({
            "image": b64_img,
            "timestamp": time.time() + (i * 0.1)
        })

    payload = {
        "frames": frames,
        "config": {}
    }

    # 3. Send Request
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/scan/analyze", json=payload)
        duration = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Time Taken: {duration:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API Success!")
            print(f"Overall Score: {data['scan_summary'].get('overall_score')}")
            print(f"Measurements Count: {len(data['measurements'].get('front_view', {}))}")
        else:
            print("\n❌ API Error:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Failed. Is the server running?")
        print("Run: uvicorn facial-analysis-backend.app.main:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    test_scan_api()
