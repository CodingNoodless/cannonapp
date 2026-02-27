from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from ..models import ScanRequest, ScanResponse, RealtimeRequest, RealtimeResponse
from core.face_detector import FaceDetector
from core.angle_classifier import AngleClassifier
from core.quality_checker import QualityChecker
from core.feature_calculator import FeatureCalculator
from core.image_preprocessor import ImagePreprocessor, preprocessor
from core.visualizer import visualizer
from features.front_view_features import FrontViewFeatures
from features.profile_features import ProfileFeatures
from features.composite_features import CompositeFeatures
from core.llm_analyzer import LLMAnalyzer
from core.golden_ratio import GoldenRatioAnalyzer
import base64
import numpy as np
import cv2
import traceback
import tempfile
import os
import shutil

router = APIRouter()

# Dependency Injection (Simple singleton pattern for now)
face_detector = FaceDetector()
angle_classifier = AngleClassifier()
quality_checker = QualityChecker()
# internal feature calculators
front_features = FrontViewFeatures()
profile_features = ProfileFeatures()
composite_features = CompositeFeatures()
llm_analyzer = LLMAnalyzer()
golden_ratio_analyzer = GoldenRatioAnalyzer()

def decode_image(base64_string: str) -> np.ndarray:
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        image_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Image decode failed")
        # Convert BGR to RGB
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

def aggregate_measurements(measurements_list: list[dict]) -> dict:
    """
    Aggregate multiple feature measurements using weighted median.
    Weight is based on image quality (sharpness score).
    
    Args:
        measurements_list: List of feature dictionaries with _quality_score
        
    Returns:
        Aggregated features dictionary
    """
    if not measurements_list:
        return {}
    
    if len(measurements_list) == 1:
        return measurements_list[0]
    
    # Collect all feature keys (excluding internal keys)
    all_keys = set()
    for m in measurements_list:
        all_keys.update(k for k in m.keys() if not k.startswith('_'))
    
    aggregated = {}
    
    for key in all_keys:
        values = []
        weights = []
        
        for m in measurements_list:
            if key in m and m[key] is not None:
                val = m[key]
                # Handle numeric types only
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    values.append(val)
                    # Use quality score as weight (default 100)
                    weights.append(m.get('_quality_score', 100))
                elif isinstance(val, list):
                    # For list values, just take the first valid one
                    if key not in aggregated:
                        aggregated[key] = val
        
        if values:
            # Calculate weighted median
            if len(values) >= 3:
                # Remove outliers (values outside 1.5 IQR)
                arr = np.array(values)
                q1, q3 = np.percentile(arr, [25, 75])
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                filtered_values = [v for v in values if lower_bound <= v <= upper_bound]
                if filtered_values:
                    aggregated[key] = float(np.median(filtered_values))
                else:
                    aggregated[key] = float(np.median(values))
            else:
                # With few values, just use median directly
                aggregated[key] = float(np.median(values))
    
    return aggregated

async def process_analysis_pipeline(images: list[np.ndarray], include_visuals: bool = False) -> ScanResponse:
    """
    Shared pipeline for processing a sequence of frames (from JSON or Video).
    Features multi-frame averaging and lighting normalization for improved accuracy.
    """
    frames_by_angle = {"front": 0, "left_profile": 0, "right_profile": 0}
    
    # Store processed data for second pass
    processed_frames = []
    
    # Multi-frame measurement collection for averaging
    front_measurements_collection = []  # List of feature dicts
    profile_measurements_collection = []
    
    best_front_frame_features = {}
    best_profile_frame_features = {} 
    visualization_image_b64 = None 
    
    # Pass 1: Preprocess, Detect Landmarks & Classify Angles
    detected_ipd_pixels = 0.0
    all_ipd_values = []
    
    for img in images:
        try:
            # Check image quality and preprocess if needed
            quality = preprocessor.calculate_image_quality(img)
            
            if quality["needs_preprocessing"]:
                # Apply lighting normalization for problematic images
                img_processed = preprocessor.preprocess(
                    img, 
                    apply_clahe=True, 
                    apply_exposure=True,
                    apply_denoise=False,  # Skip for speed
                    apply_sharpen=False
                )
            else:
                img_processed = img
            
            landmarks = face_detector.process_image(img_processed)
            if not landmarks:
                continue

            lm_array = face_detector.get_landmarks_as_array(landmarks, img_processed.shape)
            yaw, pitch, roll = angle_classifier.estimate_head_pose(lm_array, img_processed.shape)
            angle = angle_classifier.classify_angle(yaw, pitch, roll)
            
            frame_data = {
                "img": img_processed,
                "landmarks": lm_array,
                "angle": angle,
                "yaw": yaw,
                "quality": quality
            }
            
            # Generate visualization if requested (from the first good front frame)
            if include_visuals and visualization_image_b64 is None:
                viz_img = visualizer.draw_mesh(img_processed, landmarks)
                viz_img = visualizer.draw_pose_info(viz_img, yaw, pitch, roll)
                
                # Convert to base64
                _, buffer = cv2.imencode('.jpg', cv2.cvtColor(viz_img, cv2.COLOR_RGB2BGR))
                visualization_image_b64 = base64.b64encode(buffer).decode('utf-8')

            processed_frames.append(frame_data)
            frames_by_angle[angle] = frames_by_angle.get(angle, 0) + 1
            
            # Collect front-view features for averaging
            if angle in ["front", "three_quarter_left", "three_quarter_right"]:
                feats = front_features.calculate(lm_array, img_processed.shape)
                feats["_yaw"] = yaw
                feats["_quality_score"] = quality["sharpness"]  # Use sharpness as quality weight
                
                front_measurements_collection.append(feats)
                
                if 'ipd_pixels' in feats and feats['ipd_pixels'] > 0:
                    all_ipd_values.append(feats['ipd_pixels'])

        except Exception as e:
            print(f"Pipeline pass 1 error: {e}")
            continue

    # Calculate median IPD from all measurements (more robust than single frame)
    if all_ipd_values:
        detected_ipd_pixels = float(np.median(all_ipd_values))

    # Pass 2: Multi-Frame Averaging & Profile Collection
    # Calculate scale based on best IPD found
    calibration_scale = 0.0
    if detected_ipd_pixels > 0:
        calibration_scale = 63.0 / detected_ipd_pixels # 63mm standard IPD
    
    # Aggregate front-view features using weighted median (quality-weighted)
    if front_measurements_collection:
        best_front_frame_features = aggregate_measurements(front_measurements_collection)
    
    # Collect and aggregate profile measurements
    for frame in processed_frames:
        try:
            angle = frame["angle"]
            lm_array = frame["landmarks"]
            
            if angle in ["left_profile", "right_profile"]:
                feats = profile_features.calculate(lm_array, angle, calibration_scale=calibration_scale)
                feats["_quality_score"] = frame.get("quality", {}).get("sharpness", 100)
                profile_measurements_collection.append(feats)
                
        except Exception as e:
            print(f"Pipeline pass 2 error: {e}")
            continue
    
    # Aggregate profile features
    if profile_measurements_collection:
        best_profile_frame_features = aggregate_measurements(profile_measurements_collection)

    # Define Ideal Ranges (approximate standards)
    IDEAL_RANGES = {
        "ipd_mm": "60-65mm",
        "canthal_tilt_left": "5-10°",
        "canthal_tilt_right": "5-10°",
        "nose_width_ratio": "0.25-0.30",
        "nose_length_mm": "45-50mm",
        "philtrum_length_mm": "11-15mm",
        "ear_left": "0.25-0.30",
        "ear_right": "0.25-0.30",
        "jaw_cheek_ratio": "0.75-0.85",
        "esr": "0.45-0.47",
        "midface_ratio": "0.95-1.05",
        "nasolabial_angle": "90-110°",
        "mentolabial_angle": "120-130°",
        "facial_convexity": "165-175°" 
    }

    # Format measurements and perform conversions
    measurements_out = {}
    
    pixels_per_mm = 0.0
    if detected_ipd_pixels > 0:
        pixels_per_mm = detected_ipd_pixels / 63.0
    
    # Process Front View
    measurements_out["front_view"] = {}
    for k, v in best_front_frame_features.items():
        if k.startswith("_"): continue # Skip internal keys
        
        # Handle non-scalar values (lists, etc)
        if isinstance(v, list) or isinstance(v, tuple):
             # For facial_thirds, we might want to expose specific sub-values or skip
             if k == "facial_thirds":
                 # map to separate keys? 
                 measurements_out["front_view"]["facial_third_upper_px"] = {"value": float(v[0]), "unit": "px", "ideal": "N/A"}
                 measurements_out["front_view"]["facial_third_mid_px"] = {"value": float(v[1]), "unit": "px", "ideal": "N/A"}
                 measurements_out["front_view"]["facial_third_lower_px"] = {"value": float(v[2]), "unit": "px", "ideal": "N/A"}
                 if pixels_per_mm > 0:
                      measurements_out["front_view"]["facial_third_upper_mm"] = {"value": float(v[0]/pixels_per_mm), "unit": "mm", "ideal": "N/A"}
                      measurements_out["front_view"]["facial_third_mid_mm"] = {"value": float(v[1]/pixels_per_mm), "unit": "mm", "ideal": "N/A"}
                      measurements_out["front_view"]["facial_third_lower_mm"] = {"value": float(v[2]/pixels_per_mm), "unit": "mm", "ideal": "N/A"}
             continue
             
        val = float(v)
        unit = "ratio"
        key_out = k
        
        # Unit inference
        if "tilt" in k or "angle" in k or "slope" in k or "convexity" in k: 
            unit = "degrees"
        
        if "pixels" in k:
            # Convert to mm
            if pixels_per_mm > 0:
                val_mm = val / pixels_per_mm
                key_out = k.replace("pixels", "mm")
                measurements_out["front_view"][key_out] = {
                    "value": val_mm, 
                    "unit": "mm", 
                    "ideal": IDEAL_RANGES.get(key_out, "N/A")
                }
            continue 
        
        measurements_out["front_view"][key_out] = {
            "value": val, 
            "unit": unit,
            "ideal": IDEAL_RANGES.get(key_out, "N/A")
        }

    # Manual IPD entry for display
    if pixels_per_mm > 0:
        measurements_out["front_view"]["ipd_mm"] = {"value": 63.0, "unit": "mm", "ideal": "60-65mm"}

    # Process Profile View
    measurements_out["profile_view"] = {}
    for k, v in best_profile_frame_features.items():
        measurements_out["profile_view"][k] = {
            "value": float(v), 
            "unit": "degrees",
            "ideal": IDEAL_RANGES.get(k, "N/A")
        }

    # Run Advanced Analysis
    analysis_input = {}
    for cat in measurements_out.values():
        for k, data in cat.items():
            analysis_input[k] = data["value"]
            
    golden_ratio_result = golden_ratio_analyzer.analyze(analysis_input)
    
    # Merge scores back into measurements_out
    scores = golden_ratio_result.get("scores", {})
    for category in ["front_view", "profile_view"]:
        if category in measurements_out:
            for key, data in measurements_out[category].items():
                if key in scores:
                    measurements_out[category][key]["score"] = scores[key]["score"]
                    measurements_out[category][key]["rating"] = scores[key]["rating"]
    
    # Get AI Recommendations
    ai_result = None
    if analysis_input:
        ai_result = llm_analyzer.generate_recommendations(analysis_input, golden_ratio_result)
    
    return ScanResponse(
        success=True,
        scan_summary={
            "total_frames": len(images),
            "frames_by_angle": frames_by_angle,
            "overall_score": golden_ratio_result.get("average_score", 0)
        },
        measurements=measurements_out,
        golden_ratio_analysis=golden_ratio_result,
        ai_recommendations=ai_result,
        quality_metrics={"status": "processed"},
        processed_image=visualization_image_b64
    )

@router.post("/scan/analyze-realtime", response_model=RealtimeResponse)
async def analyze_realtime(request: RealtimeRequest):
    img = decode_image(request.image)
    landmarks = face_detector.process_image(img)
    
    landmarks_detected = landmarks is not None
    yaw, pitch, roll = 0.0, 0.0, 0.0
    angle_label = "unknown"
    
    if landmarks_detected:
        lm_array = face_detector.get_landmarks_as_array(landmarks, img.shape)
        yaw, pitch, roll = angle_classifier.estimate_head_pose(lm_array, img.shape)
        angle_label = angle_classifier.classify_angle(yaw, pitch, roll)

    quality = quality_checker.check_quality(img, landmarks_detected, yaw)
    processed_image_b64 = None
    if request.include_visuals and landmarks_detected:
         viz_img = visualizer.draw_mesh(img, landmarks)
         viz_img = visualizer.draw_pose_info(viz_img, yaw, pitch, roll)
         _, buffer = cv2.imencode('.jpg', cv2.cvtColor(viz_img, cv2.COLOR_RGB2BGR))
         processed_image_b64 = base64.b64encode(buffer).decode('utf-8')
    feedback = {
        "message": "Face not detected" if not landmarks_detected else f"Angle: {angle_label}",
        "current_yaw": yaw
    }

    return RealtimeResponse(
        success=True,
        detected_angle=angle_label,
        angle_confidence=1.0 if landmarks_detected else 0.0,
        quality_score=quality["score"],
        feedback=feedback,
        landmarks_detected=landmarks_detected,
        processed_image=processed_image_b64
    )

@router.post("/scan/analyze", response_model=ScanResponse)
async def analyze_scan(request: ScanRequest):
    # Decode all frames first
    images = []
    for frame in request.frames:
        try:
            img = decode_image(frame.image)
            images.append(img)
        except:
            continue
    
    return await process_analysis_pipeline(images, include_visuals=request.include_visuals)

@router.post("/scan/upload-video", response_model=ScanResponse)
async def analyze_video(file: UploadFile = File(...)):
    # Save temp file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Read video
        cap = cv2.VideoCapture(temp_path)
        images = []
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Sample every 5th frame to reduce load (assuming 30fps, gets 6fps)
            if frame_count % 5 == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                images.append(rgb_frame)
            
            frame_count += 1
            
        cap.release()
        
        if not images:
            raise HTTPException(status_code=400, detail="Could not extract frames from video")
            
        return await process_analysis_pipeline(images, include_visuals=False)

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
