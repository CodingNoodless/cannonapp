import math

class GoldenRatioAnalyzer:
    def __init__(self):
        self.GOLDEN_RATIO = 1.618
        
        # Scoring Standards: {feature_key: {'ideal': float, 'sigma': float}}
        # Sigma determines the "width" of the bell curve (tolerance).
        # Score = 100 * exp( - (x - ideal)^2 / (2 * sigma^2) )
        self.SCORING_STANDARDS = {
            # Front View
            "midface_ratio": {"ideal": 1.0, "sigma": 0.08},
            "canthal_tilt_left": {"ideal": 7.0, "sigma": 3.0}, # Positive tilt 5-10 is good
            "canthal_tilt_right": {"ideal": 7.0, "sigma": 3.0},
            "ipd_mm": {"ideal": 63.0, "sigma": 5.0},
            "esr": {"ideal": 0.46, "sigma": 0.04}, # Approx 46% - 48%
            "jaw_cheek_ratio": {"ideal": 0.80, "sigma": 0.08},
            "nose_width_ratio": {"ideal": 0.25, "sigma": 0.04},
            
            # New Front View Standards
            "face_width_height_ratio": {"ideal": 0.80, "sigma": 0.05},
            "symmetry_score": {"ideal": 100.0, "sigma": 5.0},
            "chin_philtrum_ratio": {"ideal": 2.5, "sigma": 0.4},
            "mid_lower_ratio": {"ideal": 1.0, "sigma": 0.1},
            "cheekbone_prominence": {"ideal": 1.15, "sigma": 0.1},

            # Profile View
            "facial_convexity": {"ideal": 170.0, "sigma": 5.0},
            "nasolabial_angle": {"ideal": 100.0, "sigma": 8.0}, # 90-110
            "mentolabial_angle": {"ideal": 125.0, "sigma": 10.0},
            
            # New Profile View Standards
            "gonial_angle": {"ideal": 125.0, "sigma": 8.0},
            "nose_tip_angle": {"ideal": 85.0, "sigma": 8.0},
            "forehead_slope": {"ideal": 10.0, "sigma": 5.0}, # Slight forward slope
        }

    def calculate_gaussian_score(self, value: float, ideal: float, sigma: float) -> float:
        """
        Calculate score (0-10) based on Gaussian bell curve.
        """
        if sigma <= 0: return 0.0
        exponent = -((value - ideal) ** 2) / (2 * sigma ** 2)
        return 10.0 * math.exp(exponent)

    def analyze(self, measurements: dict) -> dict:
        """
        Compare measurements against ideals and generate scores.
        measurements: dict of feature_name -> value (float)
        """
        analysis = {
            "scores": {},
            "total_score": 0,
            "average_score": 0
        }
        
        total_score_sum = 0
        count = 0

        for key, value in measurements.items():
            standard = self.SCORING_STANDARDS.get(key)
            if standard:
                score = self.calculate_gaussian_score(value, standard['ideal'], standard['sigma'])
                
                # Assign rating text (scaled for 0-10)
                rating = "Average"
                if score >= 9.0: rating = "Ideal"
                elif score >= 8.0: rating = "Excellent"
                elif score >= 7.0: rating = "Good"
                elif score >= 5.0: rating = "Average"
                else: rating = "Needs Improvement"
                
                analysis["scores"][key] = {
                    "value": value,
                    "ideal": standard['ideal'],
                    "score": round(score, 1),
                    "rating": rating
                }
                
                total_score_sum += score
                count += 1
        
        if count > 0:
            analysis["total_score"] = round(total_score_sum, 1) 
            analysis["average_score"] = round(total_score_sum / count, 1)

        return analysis
