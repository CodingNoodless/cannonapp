import cv2
import numpy as np

class QualityChecker:
    def __init__(self):
        pass

    def check_quality(self, image: np.ndarray, landmarks_detected: bool, yaw: float) -> dict:
        """
        Assess frame quality.
        """
        quality_metrics = {
            "score": 0.0,
            "lighting": "good",
            "blur": "low",
            "resolution_adequate": True,
            "landmarks_detected": landmarks_detected,
            "is_usable": False
        }

        if not landmarks_detected:
            return quality_metrics

        # Resolution Check
        h, w = image.shape[:2]
        if h < 480 or w < 480:
            quality_metrics["resolution_adequate"] = False
        
        # Blur Detection (Laplacian Variance)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 50: # Threshold for blur, adjustable
             quality_metrics["blur"] = "high"
        
        # Lighting (Brightness)
        mean_brightness = np.mean(gray)
        if mean_brightness < 40:
            quality_metrics["lighting"] = "too_dark"
        elif mean_brightness > 220:
             quality_metrics["lighting"] = "too_bright"
             
        # Overall Quality Score
        # Simple heuristic
        score = 1.0
        if quality_metrics["blur"] == "high": score -= 0.4
        if quality_metrics["lighting"] != "good": score -= 0.3
        if not quality_metrics["resolution_adequate"]: score -= 0.2
        
        quality_metrics["score"] = max(0.0, score)
        quality_metrics["is_usable"] = score > 0.5
        
        return quality_metrics
