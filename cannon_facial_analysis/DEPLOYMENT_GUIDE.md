# Deployment Guide

This guide explains how to host your Facial Analysis Backend on the cloud so your iOS app can use it from anywhere (not just your local Wi-Fi).

## Recommended Option: Railway (Easiest)
Railway is excellent for Python/FastAPI apps.

### Prerequisites
1.  **GitHub Account**: Push this code to a GitHub repository.
2.  **Railway Account**: Sign up at [railway.app](https://railway.app/).

### Steps
1.  **Create New Project**:
    *   Click "New Project" -> "Deploy from GitHub repo".
    *   Select your `facial-analysis-backend` repository.

2.  **Configure Build**:
    *   Railway usually auto-detects `requirements.txt`.
    *   If asked, the **Start Command** should be:
        ```bash
        uvicorn app.main:app --host 0.0.0.0 --port $PORT
        ```

3.  **Environment Variables**:
    *   Go to the "Variables" tab.
    *   Add `GROQ_API_KEY`: Paste your API Key here.

4.  **Deploy**:
    *   Click "Deploy". Wait a few minutes.
    *   Railway will give you a public URL (e.g., `https://my-face-app.up.railway.app`).

5.  **Update iOS App**:
    *   Replace your local IP (`http://192.168.x.x:8000`) with this new `https` URL in your Swift code.

---

## Option 2: Render (Free Tier Available)
Render is another great option.

1.  **Sign up** at [render.com](https://render.com/).
2.  **New Web Service** -> Connect GitHub.
3.  **Settings**:
    *   **Runtime**: Python 3
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4.  **Env Vars**: Add `GROQ_API_KEY`.

---

## Important Checks
*   **OpenCV Dependencies**: Sometimes cloud scanners struggle with `opencv-python`. If the build fails, change `opencv-python` in `requirements.txt` to `opencv-python-headless`.
*   **MediaPipe**: Requires GL libraries on some minimal Linux images. Railway/Render usually handle this well, but if you see import errors, you may need a `Aptfile` (for Heroku/Render) installing `libgl1`.
