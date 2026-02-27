import cv2
import asyncio
import sys
import os
import json

# Add current path to sys.path to ensure imports work
sys.path.append(os.getcwd())

from app.api.routes import process_analysis_pipeline

async def test_pipeline():
    # Load the real image uploaded by user
    img_path = "/Users/sarvagyapuri/.gemini/antigravity/brain/2563083a-bad9-402c-b8c0-1a7bc5ecf1a8/uploaded_media_1769251204127.jpg"
    
    if not os.path.exists(img_path):
        print(f"Error: Image not found at {img_path}")
        return

    img = cv2.imread(img_path)
    if img is None:
        print("Error: Could not read image.")
        return
        
    # Convert BGR to RGB (pipeline expects RGB)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    print("Running pipeline on image...")
    try:
        # Run pipeline
        result = await process_analysis_pipeline([rgb_img])
        
        if result.success:
            print(f"Summary: {result.scan_summary}")
            print("\n✅ Pipeline processing successful!")
            
            print("\n--- Front View Features Detected ---")
            front = result.measurements.get("front_view", {})
            for k, v in front.items():
                print(f"{k}: {v['value']:.2f} {v['unit']}")
                
            print("\n--- Profile View Features Detected ---")
            profile = result.measurements.get("profile_view", {})
            if not profile:
                print("(No profile angle detected in this single image, which is expected if it's a front photo)")
            else:
                for k, v in profile.items():
                    print(f"{k}: {v['value']:.2f} {v['unit']}")
            
            # Specific checks for new features
            new_features = [
                "face_width_height_ratio", "facial_third_mid_mm", "canthal_tilt_left", 
                "jaw_frontal_angle", "symmetry_score"
            ]
            
            print("\n--- Verification of New Features ---")
            missing = []
            for feat in new_features:
                found = False
                for k in front.keys():
                    if feat in k: 
                        found = True
                        break
                if found:
                    print(f"✅ {feat} is present.")
                else:
                    missing.append(feat)
                    
            if missing:
                print(f"❌ Missing features: {missing}")
            else:
                print("All key new features verified present.")
                
        else:
            print("Pipeline returned success=False")
            
    except Exception as e:
        print(f"❌ Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()

    # DEBUG: Check raw angles
    print("\n--- DEBUG: Raw Angle Check ---")
    from core.face_detector import FaceDetector
    from core.angle_classifier import AngleClassifier
    
    print(f"Image Shape: {rgb_img.shape}")
    
    # Try more lenient detection
    fd = FaceDetector(min_detection_confidence=0.3)
    ac = AngleClassifier()
    
    lms = fd.process_image(rgb_img)
    if lms:
        lm_array = fd.get_landmarks_as_array(lms, rgb_img.shape)
        yaw, pitch, roll = ac.estimate_head_pose(lm_array, rgb_img.shape)
        label = ac.classify_angle(yaw, pitch, roll)
        print(f"Raw Yaw: {yaw:.2f}, Pitch: {pitch:.2f}, Roll: {roll:.2f}")
        print(f"Classified Label: '{label}'")
        
        # Calculate features manually here to prove they work if pipeline failed due to strictness
        from features.front_view_features import FrontViewFeatures
        fv = FrontViewFeatures()
        feats = fv.calculate(lm_array, rgb_img.shape)
        print("\n--- Manual Feature Calculation Check ---")
        print(f"Face W/H Ratio: {feats.get('face_width_height_ratio')}")
        print(f"Canthal Tilt Left: {feats.get('canthal_tilt_left')}")
    else:
        print("FaceDetector failed even with 0.3 confidence.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
