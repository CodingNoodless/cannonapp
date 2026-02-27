"""
Image Preprocessor Module
Provides lighting normalization and image enhancement for better landmark detection.
"""
import cv2
import numpy as np

class ImagePreprocessor:
    """
    Preprocesses images to improve facial landmark detection accuracy.
    Handles lighting normalization, exposure correction, and noise reduction.
    """
    
    def __init__(self, 
                 clahe_clip_limit: float = 2.0,
                 clahe_tile_size: tuple = (8, 8),
                 enable_denoising: bool = True):
        """
        Args:
            clahe_clip_limit: Contrast limit for CLAHE (higher = more contrast)
            clahe_tile_size: Tile grid size for CLAHE
            enable_denoising: Whether to apply noise reduction
        """
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_size = clahe_tile_size
        self.enable_denoising = enable_denoising
        
        # Create CLAHE object
        self.clahe = cv2.createCLAHE(
            clipLimit=clahe_clip_limit,
            tileGridSize=clahe_tile_size
        )
    
    def normalize_lighting(self, image: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        to normalize lighting across the image.
        
        Args:
            image: Input image in RGB format
            
        Returns:
            Lighting-normalized image in RGB format
        """
        # Convert to LAB color space (L = lightness)
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        
        # Split channels
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Apply CLAHE to L channel only
        l_normalized = self.clahe.apply(l_channel)
        
        # Merge channels back
        lab_normalized = cv2.merge([l_normalized, a_channel, b_channel])
        
        # Convert back to RGB
        return cv2.cvtColor(lab_normalized, cv2.COLOR_LAB2RGB)
    
    def correct_exposure(self, image: np.ndarray, target_brightness: int = 127) -> np.ndarray:
        """
        Adjust image exposure to a target average brightness.
        
        Args:
            image: Input image in RGB format
            target_brightness: Target average brightness (0-255)
            
        Returns:
            Exposure-corrected image
        """
        # Calculate current average brightness
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        current_brightness = np.mean(gray)
        
        # Avoid division by zero
        if current_brightness < 1:
            current_brightness = 1
            
        # Calculate adjustment ratio
        ratio = target_brightness / current_brightness
        
        # Clamp ratio to reasonable bounds (0.5x to 2x adjustment)
        ratio = np.clip(ratio, 0.5, 2.0)
        
        # Apply adjustment
        adjusted = cv2.convertScaleAbs(image, alpha=ratio, beta=0)
        
        return adjusted
    
    def reduce_noise(self, image: np.ndarray, strength: int = 7) -> np.ndarray:
        """
        Apply fast denoising to reduce image noise.
        
        Args:
            image: Input image in RGB format
            strength: Denoising strength (higher = smoother but less detail)
            
        Returns:
            Denoised image
        """
        return cv2.fastNlMeansDenoisingColored(
            image, 
            None, 
            h=strength,
            hColor=strength,
            templateWindowSize=7,
            searchWindowSize=21
        )
    
    def enhance_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Subtly enhance edges to improve landmark detection on low-contrast faces.
        
        Args:
            image: Input image in RGB format
            
        Returns:
            Edge-enhanced image
        """
        # Apply unsharp masking
        gaussian = cv2.GaussianBlur(image, (0, 0), 2.0)
        sharpened = cv2.addWeighted(image, 1.3, gaussian, -0.3, 0)
        
        return sharpened
    
    def preprocess(self, image: np.ndarray, 
                   apply_clahe: bool = True,
                   apply_exposure: bool = True,
                   apply_denoise: bool = False,
                   apply_sharpen: bool = False) -> np.ndarray:
        """
        Full preprocessing pipeline.
        
        Args:
            image: Input image in RGB format
            apply_clahe: Whether to apply CLAHE lighting normalization
            apply_exposure: Whether to correct exposure
            apply_denoise: Whether to apply denoising (slower)
            apply_sharpen: Whether to enhance edges
            
        Returns:
            Preprocessed image ready for landmark detection
        """
        result = image.copy()
        
        # Step 1: Exposure correction (do first to get image in reasonable range)
        if apply_exposure:
            result = self.correct_exposure(result)
        
        # Step 2: CLAHE for local contrast enhancement
        if apply_clahe:
            result = self.normalize_lighting(result)
        
        # Step 3: Denoising (optional, slower)
        if apply_denoise and self.enable_denoising:
            result = self.reduce_noise(result)
        
        # Step 4: Edge enhancement (optional)
        if apply_sharpen:
            result = self.enhance_edges(result)
        
        return result
    
    def calculate_image_quality(self, image: np.ndarray) -> dict:
        """
        Calculate quality metrics for the image.
        
        Returns:
            Dictionary with brightness, contrast, and sharpness scores
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Brightness (0-255)
        brightness = np.mean(gray)
        
        # Contrast (standard deviation of pixel values)
        contrast = np.std(gray)
        
        # Sharpness (Laplacian variance - higher = sharper)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # Quality flags
        is_too_dark = brightness < 50
        is_too_bright = brightness > 200
        is_low_contrast = contrast < 30
        is_blurry = sharpness < 100
        
        return {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "sharpness": float(sharpness),
            "is_too_dark": is_too_dark,
            "is_too_bright": is_too_bright,
            "is_low_contrast": is_low_contrast,
            "is_blurry": is_blurry,
            "needs_preprocessing": is_too_dark or is_too_bright or is_low_contrast
        }


# Singleton instance for easy import
preprocessor = ImagePreprocessor()
