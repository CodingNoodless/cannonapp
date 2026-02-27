import requests
import base64
import json

# Create a dummy white image base64
dummy_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="

url = "http://127.0.0.1:8003/api/scan/analyze"
payload = {
    "frames": [
        {"image": dummy_image, "timestamp": 1234567890}
    ],
    "config": {}
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text[:500]}")
except Exception as e:
    print(f"Request failed: {e}")
