# iOS Integration Guide (Video Scan)

This guide explains how to connect your iOS app using the **Video Upload** method.

## 1. Overview
The workflow is simple:
1.  **Record Video**: The App records a 5-second video of the user's face.
2.  **Upload**: The App sends this video file to the server.
3.  **Receive Results**: The Server returns the Scores & Measurements JSON.

## 2. Step-by-Step Implementation

### Step A: Record Video
*   Use `AVCaptureSession` or `UIImagePickerController` to record a video.
*   Save the video to a temporary URL (e.g., `NSTemporaryDirectory() + "scan.mov"`).
*   Ensure the video covers Front, Left, and Right angles.

### Step B: Upload to API
*   **Endpoint**: `POST /scan/upload-video`
*   **Method**: `Multipart Form Data`
*   **Code Concept**:
    1.  Create a request to `http://<YOUR_IP>:8000/api/scan/upload-video`.
    2.  Set `Content-Type` to `multipart/form-data; boundary=...`.
    3.  Attach your video file data with the field name `file`.

### Step C: Handle Response
*   The API will extract frames, analyze them, and return the JSON.
*   **Parse the JSON**:
    *   Read `measurements.front_view` for Canthal Tilt, Symmetry, etc.
    *   Read `measurements.profile_view` for Jawline, Gonial Angle.
    *   Read `scan_summary.overall_score` for the main 1-10 rating.
*   **Display**: Show these values on your results screen (e.g., "Symmetry: 9/10 - Ideal").

## 3. Configuration
*   **Base URL**: `http://<YOUR_IP>:8000/api`
*   **Permissions**: Add `NSCameraUsageDescription` & `NSMicrophoneUsageDescription` to `Info.plist`.
