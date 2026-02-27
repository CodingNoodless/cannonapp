const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('start-btn');
const connectBtn = document.getElementById('connect-btn');
const feedbackText = document.getElementById('feedback-text');
const angleText = document.getElementById('angle-text');
const resultsDiv = document.getElementById('results');
const metricsContainer = document.getElementById('metrics-container');
const errorMsg = document.getElementById('error-msg');

let isScanning = false;
let scanFrames = [];
let scanStartTime = 0;
const SCAN_DURATION = 5000; // 5 seconds

function showError(msg) {
    errorMsg.innerText = msg;
    errorMsg.style.display = 'block';
    console.error(msg);
}

// Camera Setup
async function setupCamera() {
    errorMsg.style.display = 'none';
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Camera API not supported in this browser. Please use Chrome/Firefox/Safari.");
        }

        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        });

        video.srcObject = stream;

        // Wait for video to be ready
        await new Promise((resolve) => {
            video.onloadedmetadata = () => {
                resolve();
            };
        });

        await video.play();

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        connectBtn.style.display = 'none';
        startBtn.disabled = false;
        feedbackText.innerText = "Camera Connected. Ready to Scan.";

        requestAnimationFrame(processFrame);

    } catch (err) {
        showError("Camera Error: " + err.message + ". Please ensure camera permissions are allowed.");
    }
}

// Connect Button
connectBtn.addEventListener('click', setupCamera);

// Processing Loop (Realtime)
let meshOverlayImg = null; // Cached mesh image for smooth rendering
let isProcessingFrame = false; // Prevent overlapping requests

async function processFrame() {
    if (!video.videoWidth) {
        requestAnimationFrame(processFrame);
        return;
    }

    // Draw the live video
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Overlay the mesh image if available
    if (meshOverlayImg && meshOverlayImg.complete) {
        ctx.globalAlpha = 0.7;
        ctx.drawImage(meshOverlayImg, 0, 0, canvas.width, canvas.height);
        ctx.globalAlpha = 1.0;
    }

    const imageData = canvas.toDataURL('image/jpeg', 0.8);

    // If scanning, collect frames
    if (isScanning) {
        if (Date.now() - scanStartTime < SCAN_DURATION) {
            scanFrames.push({
                image: imageData,
                timestamp: Date.now() / 1000
            });
            feedbackText.innerText = `Scanning... ${(5 - (Date.now() - scanStartTime) / 1000).toFixed(1)}s`;
        } else {
            finishScan();
        }
    }

    // Send for realtime analysis (always, with mesh visuals)
    if (!isProcessingFrame && Math.random() < 0.3) {
        isProcessingFrame = true;
        try {
            const response = await fetch('/api/scan/analyze-realtime', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: imageData,
                    include_visuals: true,
                    timestamp: Date.now() / 1000
                })
            });
            const data = await response.json();

            if (data.success) {
                angleText.innerText = `Angle: ${data.detected_angle} (Q: ${data.quality_score.toFixed(2)})`;
                if (!isScanning) feedbackText.innerText = data.feedback.message;

                // Update mesh overlay image
                if (data.processed_image) {
                    const img = new Image();
                    img.onload = () => { meshOverlayImg = img; };
                    img.src = 'data:image/jpeg;base64,' + data.processed_image;
                } else {
                    meshOverlayImg = null;
                }
            }
        } catch (e) {
            console.error("Realtime API error", e);
        }
        isProcessingFrame = false;
    }

    requestAnimationFrame(processFrame);
}

// Start Scan
startBtn.addEventListener('click', () => {
    isScanning = true;
    scanFrames = [];
    scanStartTime = Date.now();
    startBtn.disabled = true;
    resultsDiv.style.display = 'none';
});

async function finishScan() {
    isScanning = false;
    feedbackText.innerText = "Analyzing... (This may take a few seconds)";

    try {
        const response = await fetch('/api/scan/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                frames: scanFrames,
                include_visuals: true,
                config: {}
            })
        });
        const data = await response.json();

        displayResults(data);
        feedbackText.innerText = "Scan Complete";
        startBtn.disabled = false;
    } catch (e) {
        showError("Analysis error: " + e.message);
        feedbackText.innerText = "Error analyzing scan";
        startBtn.disabled = false;
    }
}

function displayResults(data) {
    resultsDiv.style.display = 'block';
    metricsContainer.innerHTML = '';

    // -1. Visual Mesh Overlay
    if (data.processed_image) {
        const imgContainer = document.createElement('div');
        imgContainer.style.textAlign = 'center';
        imgContainer.style.marginBottom = '20px';
        imgContainer.innerHTML = `
            <h3 style="color: #444; margin-bottom: 10px;">Analysis Overlay</h3>
            <img src="data:image/jpeg;base64,${data.processed_image}" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        `;
        metricsContainer.appendChild(imgContainer);
    }

    // 0. Overall Score
    if (data.scan_summary && data.scan_summary.overall_score) {
        const scoreDiv = document.createElement('div');
        scoreDiv.style.textAlign = 'center';
        scoreDiv.style.marginBottom = '20px';
        scoreDiv.innerHTML = `
            <div style="font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px;">Facial Harmony Score</div>
            <div style="font-size: 48px; font-weight: 800; color: #333;">
                ${data.scan_summary.overall_score}
                <span style="font-size: 20px; color: #999; font-weight: 400;">/ 10</span>
            </div>
        `;
        metricsContainer.appendChild(scoreDiv);
    }

    // 1. Basic Measurements
    const views = ['front_view', 'profile_view'];
    views.forEach(view => {
        if (data.measurements[view]) {
            const section = document.createElement('div');
            // Clean title: "front_view" -> "Front Analysis"
            const title = view === 'front_view' ? 'Front Analysis' : 'Profile Analysis';
            section.innerHTML = `<h3 style="margin-top: 20px; margin-bottom: 10px; color: #444;">${title}</h3>`;

            Object.entries(data.measurements[view]).forEach(([key, val]) => {
                const row = document.createElement('div');
                row.className = 'metric-card';

                // Format Name: "canthal_tilt_left" -> "Canthal Tilt (Left)"
                let name = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                name = name.replace("mm", "").trim(); // Remove redundant mm in name if key had it

                let idealText = val.ideal && val.ideal !== "N/A" ? `Ideal: ${val.ideal}` : "";

                // Scoring Badge
                let scoreBadge = '';
                if (val.score !== undefined) {
                    let color = '#dc3545'; // Red
                    if (val.score >= 8.5) color = '#28a745'; // Green
                    else if (val.score >= 7.0) color = '#ffc107'; // Yellow
                    else if (val.score >= 5.0) color = '#fd7e14'; // Orange

                    scoreBadge = `<div style="
                        font-size: 11px; 
                        background: ${color}; 
                        color: white; 
                        padding: 2px 6px; 
                        border-radius: 10px; 
                        display: inline-block;
                        margin-bottom: 4px;
                        font-weight: bold;
                    ">${val.score}/10 - ${val.rating}</div>`;
                }

                row.innerHTML = `
                    <div class="metric-info">
                        <div class="metric-label">${name}</div>
                        ${scoreBadge}
                        ${idealText ? `<div class="metric-ideal">${idealText}</div>` : ''}
                    </div>
                    <div class="metric-right">
                        <span class="metric-value">${val.value.toFixed(1)}</span>
                        <span class="metric-unit">${val.unit}</span>
                    </div>
                `;
                section.appendChild(row);
            });
            metricsContainer.appendChild(section);
        }
    });

    // 2. AI Recommendations
    if (data.ai_recommendations && data.ai_recommendations.recommendations) {
        const aiSection = document.createElement('div');
        aiSection.innerHTML = `<h3 style="color: #007bff; margin-top: 20px;">🤖 AI Recommendations</h3>`;

        // Summary
        if (data.ai_recommendations.summary) {
            const summary = document.createElement('p');
            summary.style.fontStyle = 'italic';
            summary.innerText = data.ai_recommendations.summary;
            aiSection.appendChild(summary);
        }

        // Recommendations List
        data.ai_recommendations.recommendations.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'metric-card';
            card.style.borderLeft = '4px solid #007bff';
            card.innerHTML = `
                <h4>${rec.title || 'Recommendation'}</h4>
                <p>${rec.description || rec}</p>
             `;
            aiSection.appendChild(card);
        });

        metricsContainer.appendChild(aiSection);
    } else if (data.ai_recommendations && data.ai_recommendations.error) {
        const errorSec = document.createElement('div');
        errorSec.innerHTML = `<p style="color:orange">AI Note: ${data.ai_recommendations.error}</p>`;
        metricsContainer.appendChild(errorSec);
    }
}
