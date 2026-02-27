class RecommendationEngine:
    def __init__(self):
        # Generic suggestions for testing
        # These map feature keys to advice when the score is low.
        self.SUGGESTION_MAP = {
            "mid_lower_ratio": {
                "high": "Your lower face appears longer relative to the midface. Consider styling facial hair (if applicable) or hairstyles that add volume to the sides to balance proportions.",
                "low": "Your midface appears dominant. Styles that elongate the chin or add vertical height can help balance this."
            },
            "esr": {
                "high": "Wide-set eyes (High ESR). Glasses with a wider bridge or hairstyles with bangs can visually reduce the spacing.",
                "low": "Close-set eyes (Low ESR). Avoid heavy bangs; open up the face with pulled-back hair or lighter eyewear frames to create an illusion of width."
            },
            "midface_ratio": {
                "high": "Longer midface. Contouring the cheeks to reduce verticality or choosing glasses with taller lenses can help shorted the appearance of the midface.",
                "low": "Compact midface. You have a compact facial structure, which is generally youthful. Maintain this balance with proportionate styling."
            },
            "cheekbone_prominence": {
                "low": "Lower cheekbone definition. Facial exercises (e.g., cheek lifts) or contouring makeup can enhance cheekbone definition. Maintaining lower body fat percentages also helps."
            },
            "facial_convexity": {
                "high": "Convex profile. Good posture fits well. If looking to harmonize, hairstyles that don't add too much volume to the back can maintain balance.",
                "low": "Concave or flat profile. Hairstyles with volume at the back or beard styling can add projection to the lower face."
            },
            "nasolabial_angle": {
                "high": "Upturned nose appearance. Generally aesthetic. Ensure grooming is tidy.",
                "low": "Downturned nose appearance. Good posture helps. In some cases, specific facial exercises can help maintain nasal muscle tone."
            },
            "jaw_cheek_ratio": {
                "high": "Strong jaw width relative to cheeks. This is a masculine trait. Ensure neck posture is good to define the jawline clearly.",
                "low": "Jaw width is narrower than cheekbones. To enhance jawline definition, consider chewing exercises or overall fitness to reduce facial fullness."
            }
        }

    def generate_recommendations(self, analysis_result: dict) -> list:
        """
        Generate a list of recommendations based on the Golden Ratio analysis scores.
        """
        recommendations = []
        
        # Iterate through the analysis results
        for key, data in analysis_result.items():
            if key == "overall_harmony": continue
            
            score = data.get("score", 100)
            value = data.get("value", 0)
            ideal = data.get("ideal", 0)
            
            # Threshold for making a recommendation
            # If score is below 70 ("Needs Improvement" or low "Average"), suggest something
            if score < 75:
                direction = "high" if value > ideal else "low"
                
                # Check if we have specific advice for this metric
                if key in self.SUGGESTION_MAP:
                    advice_entry = self.SUGGESTION_MAP[key]
                    
                    # specific high/low advice or generic advice
                    if direction in advice_entry:
                        recommendations.append(f"**{key.replace('_', ' ').title()}**: {advice_entry[direction]}")
                    elif "low" in advice_entry and len(advice_entry) == 1:
                         # fluctuating value logic isn't strictly high/low, fallback to single advice
                         recommendations.append(f"**{key.replace('_', ' ').title()}**: {advice_entry['low']}")
        
        if not recommendations:
            recommendations.append("Great facial harmony! Your features align well with the reference standards. Keep up your current care routine.")
            
        return recommendations
