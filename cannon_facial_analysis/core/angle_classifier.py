import numpy as np
import cv2

class AngleClassifier:
    def __init__(self, is_front_camera: bool = True):
        """
        Args:
            is_front_camera: If True, assumes image is mirrored (selfie camera).
                             Yaw signs will be adjusted accordingly.
        """
        self.is_front_camera = is_front_camera

    def estimate_head_pose(self, landmarks_3d: np.ndarray, image_shape: tuple) -> tuple:
        """
        Estimate head pose (yaw, pitch, roll) from 3D landmarks.
        Returns yaw, pitch, roll in degrees.
        """
        h, w = image_shape[:2]
        
        # 3D model points (generic 3D face model)
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left Mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ])

        # Camera internals (approximate)
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array(
            [[focal_length, 0, center[0]],
             [0, focal_length, center[1]],
             [0, 0, 1]], dtype="double"
        )
        dist_coeffs = np.zeros((4, 1))

        # 2D image points from landmarks
        image_points = np.array([
            landmarks_3d[1][:2],    # Nose tip
            landmarks_3d[152][:2],  # Chin
            landmarks_3d[33][:2],   # Left eye left corner
            landmarks_3d[263][:2],  # Right eye right corner
            landmarks_3d[61][:2],   # Left mouth corner
            landmarks_3d[291][:2]   # Right mouth corner
        ], dtype="double")

        (success, rotation_vector, translation_vector) = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        pose_mat = cv2.hconcat((rotation_matrix, translation_vector))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
        
        pitch = euler_angles[0][0]
        yaw = euler_angles[1][0]
        roll = euler_angles[2][0]
        
        # Adjust for front camera mirroring
        if self.is_front_camera:
            yaw = -yaw  # Invert yaw for mirrored image
        
        return yaw, pitch, roll

    def classify_angle(self, yaw: float, pitch: float, roll: float) -> str:
        """
        Classify the face angle based on yaw.
        
        Returns:
            "front": Face is roughly facing the camera (|yaw| < 20°)
            "left_profile": Face is turned showing LEFT side to camera (yaw < -30°)
            "right_profile": Face is turned showing RIGHT side to camera (yaw > 30°)
            "three_quarter_left": Transitional angle (yaw between -20° and -30°)
            "three_quarter_right": Transitional angle (yaw between 20° and 30°)
        """
        abs_yaw = abs(yaw)
        
        # Lenient front detection (allows up to 20 degrees)
        if abs_yaw < 20:
            return "front"
        
        # Three-quarter views (transitional, still usable for some features)
        if 20 <= abs_yaw < 35:
            if yaw > 0:
                return "three_quarter_right"
            else:
                return "three_quarter_left"
        
        # Full profile views (35+ degrees)
        if yaw >= 35:
            return "right_profile"  # Showing right side to camera
        elif yaw <= -35:
            return "left_profile"   # Showing left side to camera
        
        return "front"  # Fallback
