import numpy as np
import scipy.spatial.distance as dist

class FeatureCalculator:
    def __init__(self):
        pass

    def distance(self, p1, p2):
        """Euclidean distance between two points."""
        return dist.euclidean(p1, p2)

    def get_pixels_per_mm(self, iris_diameter_pixels: float, reference_iris_mm: float = 11.7) -> float:
        """
        Calculate pixels per millimeter based on iris diameter.
        Average human iris diameter is approx 11.7mm.
        """
        if iris_diameter_pixels <= 0: return 0.0
        return iris_diameter_pixels / reference_iris_mm

    def convert_to_mm(self, value_pixels: float, pixels_per_mm: float) -> float:
        """Convert pixel value to millimeters."""
        if pixels_per_mm <= 0: return 0.0
        return value_pixels / pixels_per_mm

    def calculate_ear(self, eye_points):
        """
        Calculate Eye Aspect Ratio (EAR).
        eye_points: list of 6 (x, y) points corresponding to the eye.
        """
        # Vertical distances
        A = dist.euclidean(eye_points[1], eye_points[5])
        B = dist.euclidean(eye_points[2], eye_points[4])
        # Horizontal distance
        C = dist.euclidean(eye_points[0], eye_points[3])
        
        ear = (A + B) / (2.0 * C)
        return ear

    def calculate_angle(self, p1, p2, p3):
        """
        Calculate angle at p2 given points p1, p2, p3.
        """
        a = np.array(p1)
        b = np.array(p2)
        c = np.array(p3)
        
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)

    def point_line_distance(self, point, line_start, line_end):
        """
        Calculate perpendicular distance from point to the line defined by line_start and line_end.
        """
        p = np.array(point[:2])
        l1 = np.array(line_start[:2])
        l2 = np.array(line_end[:2])
        
        if np.array_equal(l1, l2):
            return np.linalg.norm(p - l1)
            
        return np.abs(np.cross(l2-l1, l1-p)) / np.linalg.norm(l2-l1)
