import cv2
import numpy as np
from mediapipe.tasks.python.vision.face_landmarker import FaceLandmarksConnections
from typing import Optional, Any, List

class Visualizer:
    def __init__(self):
        # Custom mesh style — cyan/electric blue tessellation
        self.mesh_color = (0, 255, 255)  # Cyan in BGR (for OpenCV)
        self.mesh_thickness = 1
        
        # Contour style — bright green for eyes, lips, face oval
        self.contour_color = (128, 255, 0) # Bright green in BGR
        self.contour_thickness = 1

    def _draw_connections(self, image: np.ndarray, landmarks: List[Any], connections: Any, color: tuple, thickness: int):
        h, w = image.shape[:2]
        for connection in connections:
            start_idx = connection.start
            end_idx = connection.end
            
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]
            
            pt1 = (int(p1.x * w), int(p1.y * h))
            pt2 = (int(p2.x * w), int(p2.y * h))
            
            cv2.line(image, pt1, pt2, color, thickness, cv2.LINE_AA)

    def draw_mesh(self, image: np.ndarray, landmarks) -> np.ndarray:
        """
        Draws the face mesh tessellation and contours on the image.
        Args:
            image: RGB image (numpy array)
            landmarks: List of MediaPipe normalized landmarks
            
        Returns:
            Image with mesh drawn (RGB)
        """
        # OpenCV uses BGR, but input image is RGB
        # We will work in BGR for drawing and convert back if needed, 
        # but since we want to return the same format, we just draw on it.
        # Note: cv2.line uses colors in the format of the input image.
        # If image is RGB, (r, g, b).
        
        annotated_image = image.copy()
        
        # RGB colors for drawing on RGB image
        mesh_color_rgb = (255, 255, 0)
        contour_color_rgb = (0, 255, 128)
        
        # Draw tessellation (the "mesh" look)
        self._draw_connections(
            annotated_image, 
            landmarks, 
            FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION, 
            mesh_color_rgb, 
            self.mesh_thickness
        )
        
        # Draw contours (eyes, lips, face oval)
        self._draw_connections(
            annotated_image, 
            landmarks, 
            FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS, 
            contour_color_rgb, 
            self.contour_thickness
        )
        
        return annotated_image

    def draw_pose_info(self, image: np.ndarray, yaw: float, pitch: float, roll: float) -> np.ndarray:
        """
        Draws head pose angles on the image.
        """
        annotated_image = image.copy()
        
        text = f"Y: {int(yaw)} P: {int(pitch)} R: {int(roll)}"
        # Cyan color for text
        cv2.putText(annotated_image, text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
                    
        return annotated_image

# Singleton instance
visualizer = Visualizer()
