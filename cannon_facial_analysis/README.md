
# Facial Analysis Backend System

A comprehensive Python-based system for analyzing facial features from multi-angle face scans (Front, Left Profile, Right Profile). This system computes 25-30 key facial metrics used in aesthetics and looksmaxxing applications.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Measurement Methodology](#measurement-methodology)

## Features

- **Multi-Angle Scanning**: Automatically detects and classifies Front, Left Profile, and Right Profile frames.
- **Real-time Feedback**: Provides instant angle detection and quality scoring during scanning.
- **Robust Metrics**: Calculates 25+ facial features including:
    - **Front**: Eye Aspect Ratio (EAR), Canthal Tilt, Midface Ratio, Eye Separation Ratio, Jaw/Cheek Ratio.
    - **Profile**: Facial Convexity, Nasolabial Angle, Mentolabial Angle, Jaw Projection.
    - **Composite**: Symmetry scores and facial harmony.
- **Quality Control**: Filters frames based on lighting, blur, and face detection confidence.

## Project Structure

```
facial-analysis-backend/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # Pydantic data models
│   └── api/
│       └── routes.py        # API endpoints
├── core/
│   ├── face_detector.py     # MediaPipe FaceMesh wrapper
│   ├── angle_classifier.py  # Head pose estimation & classification
│   ├── quality_checker.py   # Blur/Brightness detection
│   └── feature_calculator.py# Geometry utils (angles, distances)
├── features/
│   ├── front_view_features.py
│   ├── profile_features.py
│   └── composite_features.py
├── static/                  # Frontend for testing
│   ├── index.html
│   └── js/
│       └── app.js
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## Installation

1.  **Prerequisites**: Python 3.9+
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On MacOS/Linux
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Start the Server
Run the FastAPI server using uvicorn:
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

### 2. Test with Frontend
Open `http://127.0.0.1:8000` in your browser.
-   Allow camera access.
-   Click **"Start Analysis Scan"**.
-   Rotate different angles carefully for 5 seconds.
-   View the results table.

## API Documentation

### `POST /api/scan/analyze-realtime`
Procsses a single frame for feedback.
-   **Input**: `{"image": "base64...", "timestamp": 123}`
-   **Output**: Angle classification ("front", "left_profile"), quality score.

### `POST /api/scan/analyze`
Processes a complete sequence of frames.
-   **Input**: `{"frames": [{"image": "...", "timestamp": ...}], "config": {}}`
-   **Output**: Full JSON report of all measurements.

## Measurement Methodology

All measurements are calculated using **MediaPipe Face Mesh (468 landmarks)**.

### Front View Examples
-   **Eye Aspect Ratio (EAR)**: Ratio of eye height to eye width.
-   **Midface Ratio**: (Pupil-to-Lip Distance) / Inter-Pupillary Distance.
-   **Eye Separation Ratio**: Inter-Pupillary Distance / Face Width (Bizygomatic).
-   **Jaw/Cheek Ratio**: Bigonial Width / Bizygomatic Width.

### Profile View Examples
-   **Facial Convexity**: Angle formed by Glabella -> Subnasale -> Pogonion (Chin). Measures profile flatness.
-   **Nasolabial Angle**: Angle formed by Nose Tip -> Subnasale -> Upper Lip.
-   **Mentolabial Angle**: Angle formed by Lower Lip -> Sublabiale -> Pogonion.


## Accuracy & Limitations

### Perspective Distortion (The "Selfie Effect")
**Yes, distance matters.** Phone cameras (especially front-facing ones) use wide-angle lenses. If you hold the camera too close (< 12 inches), features in the center of the face (nose/midface) will appear larger than they are, and features on the edges (ears/jaw) will appear smaller.

**Best Practice:**
-   Hold the camera at **arm's length** (approx. 20-24 inches or 50-60cm).
-   Ensure good lighting (avoid deep shadows).
-   Keep your head level (neutral pitch).

### Algorithms
-   **Ratios**: Most measurements are ratios (e.g., `Nose Width / Face Width`). These are generally robust to distance *if* perspective distortion is minimized.
-   **Angles**: Highly sensitive to your head's rotation relative to the camera. The "Real-time Feedback" helps guide you to the correct profile angle.
