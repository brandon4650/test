"""
Image Enhancer Module
Provides specialized image enhancement functions for improved spell icon detection
"""
import cv2
import numpy as np
import logging

# Set up logging
logger = logging.getLogger('utils.image_enhancer')

class ImageEnhancer:
    """
    Class for enhancing images to improve spell detection accuracy using OpenCV
    """
    
    def __init__(self):
        """Initialize the image enhancer"""
        # Preprocessing chains for different game types
        self.enhancement_presets = {
            'default': ['denoise', 'normalize', 'sharpen'],
            'bright_ui': ['denoise', 'contrast', 'sharpen'],
            'dark_ui': ['denoise', 'brighten', 'contrast', 'sharpen'],
            'high_detail': ['denoise', 'normalize', 'edge_enhance'],
            'colored_icons': ['saturation', 'contrast']
        }
    
    def enhance(self, image, methods=None, preset=None):
        """
        Enhance an image using specified methods or a preset
        
        Args:
            image: OpenCV image to enhance
            methods: List of enhancement methods to apply in order
            preset: Name of a preset enhancement chain
            
        Returns:
            enhanced_image: The enhanced OpenCV image
        """
        if image is None:
            logger.error("Cannot enhance None image")
            return None
            
        # Use preset if specified, otherwise use methods
        if preset and preset in self.enhancement_presets:
            methods = self.enhancement_presets[preset]
        elif not methods:
            methods = self.enhancement_presets['default']
            
        enhanced = image.copy()
        
        for method in methods:
            try:
                if method == 'denoise':
                    enhanced = self.denoise(enhanced)
                elif method == 'normalize':
                    enhanced = self.normalize(enhanced)
                elif method == 'sharpen':
                    enhanced = self.sharpen(enhanced)
                elif method == 'contrast':
                    enhanced = self.enhance_contrast(enhanced)
                elif method == 'brighten':
                    enhanced = self.brighten(enhanced)
                elif method == 'edge_enhance':
                    enhanced = self.edge_enhance(enhanced)
                elif method == 'saturation':
                    enhanced = self.enhance_saturation(enhanced)
            except Exception as e:
                logger.warning(f"Error applying {method}: {str(e)}")
                
        return enhanced
    
    def denoise(self, image, strength=7):
        """Apply denoising to reduce noise in the image"""
        # Use different denoising algorithms based on image type
        if len(image.shape) == 3:  # Color image
            return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
        else:  # Grayscale image
            return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
    
    def normalize(self, image):
        """Normalize the image histogram"""
        if len(image.shape) == 3:  # Color image
            # Convert to LAB color space for better normalization
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            
            # Merge channels and convert back to BGR
            merged = cv2.merge([cl, a, b])
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        else:  # Grayscale image
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)
    
    def sharpen(self, image, strength=1.5):
        """Sharpen the image to enhance edges and details"""
        # Define kernel for sharpening
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        
        # Apply kernel for standard sharpening
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Blend with original image for subtle effect
        if strength != 1.0:
            return cv2.addWeighted(image, 1 - strength, sharpened, strength, 0)
        return sharpened
    
    def enhance_contrast(self, image, clip_limit=3.0, alpha=1.5, beta=15):
        """Enhance contrast using multiple techniques"""
        if len(image.shape) == 3:  # Color image
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel with higher clip limit
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            
            # Apply additional contrast to L channel
            cl = cv2.convertScaleAbs(cl, alpha=alpha, beta=beta)
            
            # Merge channels and convert back to BGR
            merged = cv2.merge([cl, a, b])
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        else:  # Grayscale image
            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            cl = clahe.apply(image)
            
            # Apply additional contrast
            return cv2.convertScaleAbs(cl, alpha=alpha, beta=beta)
    
    def brighten(self, image, beta=30):
        """Brighten the image"""
        return cv2.convertScaleAbs(image, alpha=1.0, beta=beta)
    
    def edge_enhance(self, image, k=7, sigma=1.5):
        """Enhance edges using unsharp masking"""
        # Gaussian blur
        blurred = cv2.GaussianBlur(image, (k, k), sigma)
        # Unsharp masking: original + (original - blurred)
        return cv2.addWeighted(image, 1.5, blurred, -0.5, 0)
    
    def enhance_saturation(self, image, saturation_scale=1.5):
        """Enhance color saturation of the image"""
        if len(image.shape) != 3:  # Not a color image
            return image
            
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype("float32")
        h, s, v = cv2.split(hsv)
        
        # Scale the saturation channel
        s = s * saturation_scale
        s = np.clip(s, 0, 255)
        
        # Merge the channels and convert back to BGR
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)
    
    def binarize(self, image, adaptive=True, block_size=11, c=2):
        """Convert image to binary (black and white)"""
        # Convert to grayscale if color image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        if adaptive:
            # Adaptive thresholding works better for varying lighting conditions
            return cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, block_size, c
            )
        else:
            # Otsu's thresholding automatically finds the optimal threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
    
    def extract_dominant_colors(self, image, k=3):
        """
        Extract the dominant colors in the image
        
        Args:
            image: OpenCV image
            k: Number of dominant colors to extract
            
        Returns:
            list: List of (B,G,R) color tuples
        """
        if len(image.shape) != 3:  # Not a color image
            return [(0, 0, 0)]
            
        # Reshape the image to be a list of pixels
        pixels = image.reshape((-1, 3))
        pixels = np.float32(pixels)
        
        # Define criteria and apply K-means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert centers to uint8 and return
        centers = np.uint8(centers)
        
        # Count occurrences of each label to determine dominant colors
        unique_labels, counts = np.unique(labels, return_counts=True)
        
        # Sort by frequency
        sorted_indices = np.argsort(counts)[::-1]
        sorted_centers = centers[sorted_indices]
        
        # Convert to list of tuples
        return [tuple(map(int, color)) for color in sorted_centers]
    
    def create_color_mask(self, image, target_color, tolerance=30):
        """
        Create a mask for areas of the image matching a specific color
        
        Args:
            image: OpenCV image
            target_color: (B,G,R) color to match
            tolerance: Color distance tolerance
            
        Returns:
            mask: Binary mask where matching pixels are white
        """
        if len(image.shape) != 3:  # Not a color image
            return None
            
        # Create an array of the target color
        target = np.uint8([[target_color]])
        
        # Convert image and target to HSV
        hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv_target = cv2.cvtColor(target, cv2.COLOR_BGR2HSV)
        
        # Extract the hue
        target_hue = hsv_target[0, 0, 0]
        
        # Create range for the mask
        lower_bound = np.array([max(0, target_hue - tolerance), 50, 50])
        upper_bound = np.array([min(179, target_hue + tolerance), 255, 255])
        
        # Create mask
        return cv2.inRange(hsv_img, lower_bound, upper_bound)
    
    def detect_edges(self, image, low_threshold=50, high_threshold=150):
        """
        Detect edges in the image using Canny edge detection
        
        Args:
            image: OpenCV image
            low_threshold: Lower threshold for edge detection
            high_threshold: Higher threshold for edge detection
            
        Returns:
            edges: Binary image containing detected edges
        """
        # Convert to grayscale if color image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply slight blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect edges
        return cv2.Canny(blurred, low_threshold, high_threshold)
    
    def detect_features(self, image, method='sift', max_features=50):
        """
        Detect key features in the image
        
        Args:
            image: OpenCV image
            method: Feature detection method ('sift', 'orb', or 'fast')
            max_features: Maximum number of features to detect
            
        Returns:
            tuple: (keypoints, descriptors)
        """
        # Convert to grayscale if color image
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        if method == 'sift':
            # SIFT detector
            try:
                sift = cv2.SIFT_create(nfeatures=max_features)
            except AttributeError:
                # Fall back for older OpenCV versions
                sift = cv2.xfeatures2d.SIFT_create(nfeatures=max_features)
            return sift.detectAndCompute(gray, None)
            
        elif method == 'orb':
            # ORB detector
            orb = cv2.ORB_create(nfeatures=max_features)
            return orb.detectAndCompute(gray, None)
            
        elif method == 'fast':
            # FAST detector
            fast = cv2.FastFeatureDetector_create()
            keypoints = fast.detect(gray, None)
            return keypoints, None
            
        return None, None