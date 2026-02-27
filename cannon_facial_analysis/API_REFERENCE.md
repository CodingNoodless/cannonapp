# API Reference (Video Scan)

**Base URL**: `http://<YOUR_IP>:8000/api`

## The Main Workflow

### 1. Upload Video & Get Results
**Endpoint**: `POST /scan/upload-video`
**Method**: `multipart/form-data`

*   **Input**: A single video file (e.g., `scan.mp4`, `scan.mov`) captured by the user.
    *   **Field Name**: `file`
    *   **Content-Type**: `video/mp4` or `video/quicktime`

*   **Process**:
    1.  App records a 5-second video.
    2.  App uploads this file to the endpoint.
    3.  Server extracts frames, analyzes them, and returns JSON.

*   **Output (JSON Response)**:
    ```json
    {
      "success": true,
      "scan_summary": {
        "overall_score": 8.5
      },
      "measurements": {
        "front_view": {
          "canthal_tilt_left": { "value": 6.5, "score": 9.0, "rating": "Ideal" },
          "symmetry_score": { "value": 85.0 }
        },
        "profile_view": {
          "gonial_angle": { "value": 125.0, "score": 8.0 }
        }
      },
      "ai_recommendations": {
        "summary": "Great structure...",
        "recommendations": []
      }
    }
    ```

---

## Utilities

### Health Check
**Endpoint**: `GET /health`
*   **Returns**: `{"status": "healthy"}`
