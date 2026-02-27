import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os
from typing import List, Tuple, Optional, Any

class FaceDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        # Path to the model file
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "face_landmarker.task")
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_tracking_confidence
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def process_image(self, image: np.ndarray) -> Optional[Any]:
        """
        Process an image and return face landmarks.
        Image should be in RGB format.
        """
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        results = self.detector.detect(mp_image)
        
        if not results.face_landmarks:
            return None
        
        # Return the first face detected
        return results.face_landmarks[0]

    def get_landmarks_as_array(self, landmarks, image_shape) -> np.ndarray:
        """
        Convert landmarks to a numpy array of (x, y, z) coordinates.
        Note: New API returns normalized landmarks directly.
        """
        h, w = image_shape[:2]
        landmark_array = np.array([
            [lm.x * w, lm.y * h, lm.z * w] 
            for lm in landmarks
        ])
        return landmark_array
