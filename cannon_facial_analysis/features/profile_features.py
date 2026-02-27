import numpy as np
from core.feature_calculator import FeatureCalculator

class ProfileFeatures:
    def __init__(self):
        self.calculator = FeatureCalculator()
        
        # Landmark indices
        self.LM_GLABELLA = 10
        self.LM_NASION = 168
        self.LM_NOSE_TIP = 1
        self.LM_SUBNASALE = 2
        self.LM_LIP_UPPER = 13
        self.LM_LIP_LOWER = 14
        self.LM_CHIN = 152 # Menton/Pogonion
        self.LM_CHIN_INDENT = 17 # Sublabiale
        
        # Gonion (approximate on mesh boundary)
        self.LM_GONION_LEFT = 132
        self.LM_GONION_RIGHT = 361
        self.LM_EAR_LEFT = 234
        self.LM_EAR_RIGHT = 454
        self.LM_FOREHEAD_TOP = 151 

    def calculate(self, landmarks_array, side: str, calibration_scale: float = 0.0):
        """
        Calculate profile features.
        side: 'left' or 'right'
        calibration_scale: mm per pixel
        """
        features = {}
        
        glabella = landmarks_array[self.LM_GLABELLA]
        nasion = landmarks_array[self.LM_NASION]
        subnasale = landmarks_array[self.LM_SUBNASALE]
        tip = landmarks_array[self.LM_NOSE_TIP]
        upper_lip = landmarks_array[self.LM_LIP_UPPER]
        lower_lip = landmarks_array[self.LM_LIP_LOWER]
        pogonion = landmarks_array[self.LM_CHIN]
        chin_indent = landmarks_array[self.LM_CHIN_INDENT]
        
        # 19. Facial Convexity (Glabella - Subnasale - Pogonion)
        features['facial_convexity'] = self.calculator.calculate_angle(
            glabella[:2], subnasale[:2], pogonion[:2]
        )
        
        # 20. Nasolabial Angle
        features['nasolabial_angle'] = self.calculator.calculate_angle(
            tip[:2], subnasale[:2], upper_lip[:2]
        )
        
        # 21. Mentolabial Angle
        features['mentolabial_angle'] = self.calculator.calculate_angle(
            lower_lip[:2], chin_indent[:2], pogonion[:2]
        )
        
        # ---------------- NEW FEATURES ----------------
        
        # Midface Projection
        # Depth of Subnasale vs Glabella-Pogonion line
        # Not perfect 3D depth, but in profile 2D, it represents forward growth relative to vertical plane
        midface_proj_px = self.calculator.point_line_distance(subnasale, glabella, pogonion)
        features['midface_projection_mm'] = midface_proj_px * calibration_scale
        
        # Chin Projection
        # Depth of Pogonion vs Nasion vertical line
        # Vertical line at Nasion: (Nasion.x, Nasion.y) to (Nasion.x, Nasion.y + 100)
        # Assumes image is upright.
        nasion_vertical_end = np.array([nasion[0], nasion[1] + 100])
        chin_proj_px = self.calculator.point_line_distance(pogonion, nasion, nasion_vertical_end)
        # Direction: check if Chin X is ahead of Nasion X (dependent on side)
        # If left profile, "ahead" means smaller X? No, usually Left Profile means facing Left. 
        # Facing Left -> Nose X < Ear X. Forward is negative X?
        # Let's just return magnitude.
        features['chin_projection_mm'] = chin_proj_px * calibration_scale
        
        # Nose Projection (Tip to Subnasale distance - or Tip to Facial Plane)
        # Simple definition: Distance from Tip to Subnasale (base)
        nose_proj_px = self.calculator.distance(tip[:2], subnasale[:2])
        features['nose_projection_mm'] = nose_proj_px * calibration_scale
        
        # Nose Tip Angle
        # Angle between Bridge (Nasion-Tip) and Columella (Subnasale-Tip) ??
        # Or usually Nasofacial angle? 
        # Let's use Nasal Tip Angle: Nasion - Tip - Subnasale? No.
        # User requested "Nose Tip Angle". Often Nasion-Pronasale-Subnasale.
        features['nose_tip_angle'] = self.calculator.calculate_angle(
            nasion[:2], tip[:2], subnasale[:2]
        )
        
        # Lip Projection (E-Line)
        # E-Line: Tip to Pogonion.
        # Distance of Upper/Lower lip to this line.
        upper_lip_dist = self.calculator.point_line_distance(upper_lip, tip, pogonion)
        lower_lip_dist = self.calculator.point_line_distance(lower_lip, tip, pogonion)
        features['eline_upper_lip_mm'] = upper_lip_dist * calibration_scale
        features['eline_lower_lip_mm'] = lower_lip_dist * calibration_scale
        
        # Forehead Slope
        # Angle of Glabella - Trichion(151) vs Vertical
        forehead_top = landmarks_array[self.LM_FOREHEAD_TOP]
        # Vertical vector
        vertical_vec = np.array([0, -1]) # Up
        forehead_vec = forehead_top[:2] - glabella[:2]
        # Angle
        cosine = np.dot(forehead_vec, vertical_vec) / (np.linalg.norm(forehead_vec) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
        features['forehead_slope'] = angle
        
        # Gonial Angle (Jaw Angle)
        # Need Gonion.
        if side == 'left' or side == 'left_profile':
            gonion = landmarks_array[self.LM_GONION_LEFT]
            ear = landmarks_array[self.LM_EAR_LEFT]
        else:
            gonion = landmarks_array[self.LM_GONION_RIGHT]
            ear = landmarks_array[self.LM_EAR_RIGHT]
            
        # Angle: Articulare (Ear approx) - Gonion - Menton
        features['gonial_angle'] = self.calculator.calculate_angle(
            ear[:2], gonion[:2], pogonion[:2]
        )
        
        # Jawline Angle (Ramus inclination?)
        # User requested "Jawline angle" separate from Gonial angle.
        # Usually Gonion to Menton vs Horizontal.
        v_jaw = pogonion[:2] - gonion[:2]
        angle_jaw = np.degrees(np.arctan2(v_jaw[1], v_jaw[0]))
        # Normalize to 0-180 or deviation from horizontal
        features['jawline_angle'] = abs(angle_jaw) 
        
        return features
