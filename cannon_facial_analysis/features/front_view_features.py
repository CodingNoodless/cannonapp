import numpy as np
from core.feature_calculator import FeatureCalculator

class FrontViewFeatures:
    def __init__(self):
        self.calculator = FeatureCalculator()
        
        # MediaPipe Landmark Indices (approximate)
        self.LM_LEFT_EYE = [33, 160, 158, 133, 153, 144] # p1..p6
        self.LM_RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        self.LM_NOSE_TIP = 1
        self.LM_NOSE_BOTTOM = 2 # Subnasale check
        self.LM_CHIN = 152 # Menton
        self.LM_LIP_TOP = 13
        self.LM_LIP_BOTTOM = 14
        self.LM_LEFT_HEAD_SIDE = 234
        self.LM_RIGHT_HEAD_SIDE = 454
        self.LM_LEFT_EAR = 234 # Approx outer ear
        self.LM_RIGHT_EAR = 454 # Approx 
        # New landmarks
        self.LM_FOREHEAD_TOP = 10 # Glabella/Forehead
        self.LM_CHEEK_LEFT = 123
        self.LM_CHEEK_RIGHT = 352
        self.LM_JAW_LEFT = 58 
        self.LM_JAW_RIGHT = 288
        self.LM_BROW_LEFT = 105
        self.LM_BROW_RIGHT = 334 

    def calculate(self, landmarks_array, image_shape):
        """
        Calculate front view features.
        landmarks_array: np.array of shape (468, 3)
        """
        features = {}
        
        # 1. Eye Aspect Ratio (EAR)
        left_eye_pts = landmarks_array[self.LM_LEFT_EYE]
        right_eye_pts = landmarks_array[self.LM_RIGHT_EYE]
        
        features['ear_left'] = self.calculator.calculate_ear(left_eye_pts[:, :2])
        features['ear_right'] = self.calculator.calculate_ear(right_eye_pts[:, :2])
        
        # Landmarks
        glabella = landmarks_array[10]
        subnasale = landmarks_array[2]
        menton = landmarks_array[152]
        # Forehead top approximation (point 10 is glabella, 151 is forehead top)
        trichion = landmarks_array[151] 
        
        # 3. Facial Thirds
        # Upper: Trichion to Glabella
        upper_third = self.calculator.distance(trichion[:2], glabella[:2])
        # Mid: Glabella to Subnasale
        mid_third = self.calculator.distance(glabella[:2], subnasale[:2])
        # Lower: Subnasale to Menton
        lower_third = self.calculator.distance(subnasale[:2], menton[:2])
        
        features['facial_thirds'] = [upper_third, mid_third, lower_third]
        # Ratio for compatibility
        features['mid_lower_ratio'] = mid_third / (lower_third + 1e-6)
        
        # 5. Inter-Pupillary Distance (IPD)
        left_pupil = landmarks_array[468] if len(landmarks_array) > 468 else landmarks_array[473] # MP Iris
        if len(landmarks_array) <= 468:
            left_pupil = np.mean(left_eye_pts, axis=0)
            right_pupil = np.mean(right_eye_pts, axis=0)
        else:
            right_pupil = landmarks_array[473]
            
        features['ipd_pixels'] = self.calculator.distance(left_pupil[:2], right_pupil[:2])
        
        # 6. Face Width / Body
        # Bizygomatic width
        face_width = self.calculator.distance(landmarks_array[self.LM_CHEEK_LEFT][:2], landmarks_array[self.LM_CHEEK_RIGHT][:2])
        # Face Height
        face_height = self.calculator.distance(trichion[:2], menton[:2])
        
        features['face_width_height_ratio'] = face_width / (face_height + 1e-6)
        features['esr'] = features['ipd_pixels'] / (face_width + 1e-6)
        
        # 9. Midface Ratio (Pupil to Lip / Pupil to Pupil)
        lip_center = (landmarks_array[self.LM_LIP_TOP] + landmarks_array[self.LM_LIP_BOTTOM]) / 2
        midface_height = self.calculator.distance((left_pupil[:2] + right_pupil[:2])/2, lip_center[:2])
        features['midface_ratio'] = midface_height / (features['ipd_pixels'] + 1e-6)
        
        # 11. Nose Width Ratio
        nose_left = landmarks_array[102] # Approx nostril
        nose_right = landmarks_array[331]
        nose_width = self.calculator.distance(nose_left[:2], nose_right[:2])
        features['nose_width_ratio'] = nose_width / (face_width + 1e-6)
        
        # 16. Cheekbone Prominence & Bigonial Width
        jaw_width = self.calculator.distance(landmarks_array[self.LM_JAW_LEFT][:2], landmarks_array[self.LM_JAW_RIGHT][:2])
        features['bigonial_width_pixels'] = jaw_width
        features['cheekbone_prominence'] = face_width / (jaw_width + 1e-6)
        features['jaw_cheek_ratio'] = jaw_width / (face_width + 1e-6) # Inverse
        
        # Brow Height (Pupil to Brow)
        l_brow = landmarks_array[self.LM_BROW_LEFT]
        r_brow = landmarks_array[self.LM_BROW_RIGHT]
        brow_h_l = self.calculator.distance(left_pupil[:2], l_brow[:2])
        brow_h_r = self.calculator.distance(right_pupil[:2], r_brow[:2])
        features['brow_height_pixels'] = (brow_h_l + brow_h_r) / 2
        
        # Jaw Frontal Angle
        # Vector Left Gonion -> Menton
        v_jaw_l = menton[:2] - landmarks_array[self.LM_JAW_LEFT][:2]
        angle_jaw_l = np.degrees(np.arctan2(v_jaw_l[1], v_jaw_l[0]))
        features['jaw_frontal_angle'] = abs(angle_jaw_l) # simplified slope
        
        # Chin to Philtrum Ratio
        # Philtrum = Subnasale (2) to Upper Lip (0)
        lip_top = landmarks_array[0] # Cupid's bow
        philtrum_len = self.calculator.distance(subnasale[:2], lip_top[:2])
        chin_height = self.calculator.distance(landmarks_array[17][:2], menton[:2])
        features['chin_philtrum_ratio'] = chin_height / (philtrum_len + 1e-6)
        
        # Facial Symmetry
        # Simplified: Compare distances from center line (Nose bridge)
        sym_score = 0
        pairs = [
            (self.LM_CHEEK_LEFT, self.LM_CHEEK_RIGHT),
            (self.LM_JAW_LEFT, self.LM_JAW_RIGHT),
            (self.LM_LEFT_EYE[3], self.LM_RIGHT_EYE[3]) # Eye corners
        ]
        total_diff_pct = 0
        # Center X approx as avg of Glabella and Menton X
        center_x = (landmarks_array[10][0] + landmarks_array[152][0]) / 2
        
        for p1, p2 in pairs:
             d1 = abs(landmarks_array[p1][0] - center_x)
             d2 = abs(landmarks_array[p2][0] - center_x)
             if d1 + d2 > 0:
                 total_diff_pct += abs(d1 - d2) / ((d1+d2)/2)
        
        features['symmetry_score'] = 100 * (1.0 - (total_diff_pct / len(pairs)))

        # ---------------- NEW FEATURES FOR DETAILED ANALYSIS ----------------

        # Canthal Tilt (Angle between inner and outer eye corners)
        l_inner = landmarks_array[133]
        l_outer = landmarks_array[33]
        dy_l = l_inner[1] - l_outer[1]
        dx_l = l_outer[0] - l_inner[0]
        features['canthal_tilt_left'] = np.degrees(np.arctan2(dy_l, dx_l))

        r_inner = landmarks_array[362]
        r_outer = landmarks_array[263]
        dy_r = r_inner[1] - r_outer[1]
        dx_r = r_outer[0] - r_inner[0] 
        features['canthal_tilt_right'] = np.degrees(np.arctan2(dy_r, dx_r))

        # Nose Length (Nasion 168 to Subnasale 2)
        nasion = landmarks_array[168]
        features['nose_length_pixels'] = self.calculator.distance(nasion[:2], landmarks_array[self.LM_NOSE_BOTTOM][:2])

        # Philtrum Length 
        features['philtrum_length_pixels'] = philtrum_len

        return features
