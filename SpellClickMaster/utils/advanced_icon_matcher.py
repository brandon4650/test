"""
Advanced Icon Matcher Module
Provides enhanced spell icon detection using OpenCV with multiple detection methods
"""
import cv2
import numpy as np
import logging
from collections import namedtuple

# Set up logging
logger = logging.getLogger('utils.advanced_icon_matcher')

# Define a result structure
MatchResult = namedtuple('MatchResult', ['name', 'confidence', 'location', 'method'])

class AdvancedIconMatcher:
    """
    Advanced class for matching spell icons using multiple OpenCV techniques
    for improved accuracy and performance
    """
    
    # Define available matching methods
    METHODS = {
        'template': cv2.TM_CCOEFF_NORMED,  # Template matching
        'sift': 'SIFT',                    # Scale-Invariant Feature Transform
        'orb': 'ORB',                      # Oriented FAST and Rotated BRIEF
        'histogram': 'HISTOGRAM',          # Color histogram comparison
    }
    
    def __init__(self, default_methods=None):
        """
        Initialize the advanced icon matcher
        
        Args:
            default_methods (list): List of method names to use by default
                                    e.g., ['template', 'sift']
        """
        self.default_methods = default_methods or ['template']
        
        # Initialize feature detectors
        self.sift = None
        self.orb = None
        
        # Track performance stats
        self.stats = {
            'template_matches': 0,
            'sift_matches': 0,
            'orb_matches': 0,
            'histogram_matches': 0,
            'failed_matches': 0,
            'total_calls': 0
        }
    
    def _initialize_detectors(self):
        """Initialize feature detectors on first use to save memory"""
        if 'sift' in self.default_methods and self.sift is None:
            try:
                self.sift = cv2.SIFT_create()
            except AttributeError:
                # Fall back to older OpenCV versions
                self.sift = cv2.xfeatures2d.SIFT_create()
            logger.info("SIFT detector initialized")
            
        if 'orb' in self.default_methods and self.orb is None:
            self.orb = cv2.ORB_create()
            logger.info("ORB detector initialized")
    
    def find_best_match(self, image, templates, methods=None, threshold=0.7):
        """
        Find the best matching icon template in the image using multiple methods
        
        Args:
            image: OpenCV image to search in
            templates: Dictionary of {name: template_image}
            methods: List of methods to use (defaults to self.default_methods)
            threshold: Confidence threshold for a valid match
            
        Returns:
            MatchResult: Named tuple with best match info or None if no match
        """
        if image is None or not templates:
            return None
            
        methods = methods or self.default_methods
        self.stats['total_calls'] += 1
        
        # Make sure needed detectors are initialized
        if any(m in ('sift', 'orb') for m in methods):
            self._initialize_detectors()
        
        best_match = None
        best_confidence = threshold  # Start with threshold as minimum confidence
        
        # Try each template with each method
        for name, template in templates.items():
            # Skip invalid templates
            if template is None or template.size == 0:
                continue
                
            # Try different matching methods
            for method in methods:
                result = None
                
                if method == 'template':
                    result = self._match_template(image, template, name)
                elif method == 'sift' and self.sift is not None:
                    result = self._match_sift(image, template, name)
                elif method == 'orb' and self.orb is not None:
                    result = self._match_orb(image, template, name)
                elif method == 'histogram':
                    result = self._match_histogram(image, template, name)
                
                # Update best match if we found a better one
                if result and result.confidence > best_confidence:
                    best_match = result
                    best_confidence = result.confidence
        
        # Update stats
        if best_match:
            method_stat = f"{best_match.method}_matches"
            if method_stat in self.stats:
                self.stats[method_stat] += 1
        else:
            self.stats['failed_matches'] += 1
            
        return best_match
    
    def _match_template(self, image, template, name):
        """Match using standard template matching"""
        # Ensure template is smaller than the image
        if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
            return None
            
        # Convert both to grayscale if they're color images
        if len(image.shape) == 3:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            img_gray = image
            
        if len(template.shape) == 3:
            tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            tpl_gray = template
            
        # Run template matching
        result = cv2.matchTemplate(img_gray, tpl_gray, self.METHODS['template'])
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Get the location of the best match
        top_left = max_loc
        confidence = max_val
        
        return MatchResult(name, confidence, top_left, 'template')
    
    def _match_sift(self, image, template, name):
        """Match using SIFT features"""
        # Convert both to grayscale if they're color images
        if len(image.shape) == 3:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            img_gray = image
            
        if len(template.shape) == 3:
            tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            tpl_gray = template
        
        # Find keypoints and descriptors
        kp1, des1 = self.sift.detectAndCompute(img_gray, None)
        kp2, des2 = self.sift.detectAndCompute(tpl_gray, None)
        
        # If not enough keypoints, return no match
        if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
            return None
        
        # Create BFMatcher with default params
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des2, des1, k=2)
        
        # Apply ratio test
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        
        # Calculate confidence based on number of good matches
        match_ratio = len(good_matches) / max(1, len(kp2))
        
        # If we have enough good matches, find location
        if len(good_matches) >= 4:
            # Extract locations of matched keypoints
            src_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            
            # Find homography
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            # Get the corners of the template
            h, w = tpl_gray.shape
            corners = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
            
            # Transform the corners through the homography
            transformed_corners = cv2.perspectiveTransform(corners, H)
            
            # Get the top left corner
            top_left = tuple(map(int, transformed_corners[0][0]))
            
            return MatchResult(name, match_ratio, top_left, 'sift')
        
        return None
    
    def _match_orb(self, image, template, name):
        """Match using ORB features"""
        # Convert both to grayscale if they're color images
        if len(image.shape) == 3:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            img_gray = image
            
        if len(template.shape) == 3:
            tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            tpl_gray = template
        
        # Find keypoints and descriptors
        kp1, des1 = self.orb.detectAndCompute(img_gray, None)
        kp2, des2 = self.orb.detectAndCompute(tpl_gray, None)
        
        # If not enough keypoints, return no match
        if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
            return None
        
        # Create BFMatcher
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des2, des1)
        
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Take only good matches (lower distance)
        good_matches = matches[:int(len(matches) * 0.75)]
        
        # Calculate confidence based on number of good matches
        match_ratio = len(good_matches) / max(1, len(kp2))
        
        # If we have enough good matches, find location
        if len(good_matches) >= 4:
            # Extract locations of matched keypoints
            src_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            
            # Find homography
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            # Get the corners of the template
            h, w = tpl_gray.shape
            corners = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
            
            # Transform the corners through the homography
            transformed_corners = cv2.perspectiveTransform(corners, H)
            
            # Get the top left corner
            top_left = tuple(map(int, transformed_corners[0][0]))
            
            return MatchResult(name, match_ratio, top_left, 'orb')
        
        return None
    
    def _match_histogram(self, image, template, name):
        """Match using color histogram comparison"""
        # Convert to HSV for better color matching
        if len(image.shape) == 3:
            img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        else:
            # If grayscale, can't do histogram matching properly
            return None
            
        if len(template.shape) == 3:
            tpl_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
        else:
            # If grayscale, can't do histogram matching properly
            return None
        
        # Calculate template histogram
        h_bins = 50
        s_bins = 60
        histSize = [h_bins, s_bins]
        h_ranges = [0, 180]
        s_ranges = [0, 256]
        ranges = h_ranges + s_ranges
        channels = [0, 1]  # Use H and S channels
        
        tpl_hist = cv2.calcHist([tpl_hsv], channels, None, histSize, ranges, accumulate=False)
        cv2.normalize(tpl_hist, tpl_hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        
        # Sliding window over the image
        best_score = -1
        best_loc = None
        window_size = template.shape[:2]
        
        # Limit number of windows to check for performance
        step_size = max(1, min(window_size) // 4)
        
        for y in range(0, image.shape[0] - window_size[0], step_size):
            for x in range(0, image.shape[1] - window_size[1], step_size):
                # Extract window
                window = img_hsv[y:y+window_size[0], x:x+window_size[1]]
                
                # Calculate window histogram
                window_hist = cv2.calcHist([window], channels, None, histSize, ranges, accumulate=False)
                cv2.normalize(window_hist, window_hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
                
                # Compare histograms
                score = cv2.compareHist(tpl_hist, window_hist, cv2.HISTCMP_CORREL)
                
                if score > best_score:
                    best_score = score
                    best_loc = (x, y)
        
        if best_score > 0.7:  # Threshold for histogram matching
            return MatchResult(name, best_score, best_loc, 'histogram')
        
        return None
    
    def match_specific_icon(self, image, template, methods=None, threshold=0.7):
        """
        Match a specific icon template in an image using multiple methods
        
        Args:
            image: OpenCV image to search in
            template: Template image to find
            methods: List of methods to use (defaults to self.default_methods)
            threshold: Confidence threshold for a valid match
            
        Returns:
            tuple: (is_match, confidence, location)
        """
        methods = methods or self.default_methods
        
        # Create a temporary template dictionary
        templates = {'specific': template}
        
        # Find best match
        match = self.find_best_match(image, templates, methods, threshold)
        
        if match and match.confidence >= threshold:
            return True, match.confidence, match.location
        else:
            return False, 0, None
    
    def find_all_matches(self, image, template, method='template', threshold=0.7, max_results=10):
        """
        Find all instances of a template in an image
        
        Args:
            image: OpenCV image to search in
            template: Template image to find
            method: Method to use for matching ('template' recommended for this)
            threshold: Confidence threshold for valid matches
            max_results: Maximum number of results to return
            
        Returns:
            list: List of (x, y, confidence) tuples for each match
        """
        if image is None or template is None:
            return []
            
        if method != 'template':
            logger.warning("Only template matching supported for multiple matches. Using template method.")
        
        # Ensure template is smaller than the image
        if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
            return []
            
        # Convert both to grayscale if they're color images
        if len(image.shape) == 3:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            img_gray = image
            
        if len(template.shape) == 3:
            tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            tpl_gray = template
            
        # Run template matching
        result = cv2.matchTemplate(img_gray, tpl_gray, self.METHODS['template'])
        
        # Get locations where result is above threshold
        locations = np.where(result >= threshold)
        matches = []
        
        # Convert to list of (x, y, confidence) tuples
        for pt in zip(*locations[::-1]):  # Swap columns and rows to get x,y order
            confidence = result[pt[1], pt[0]]
            matches.append((pt[0], pt[1], float(confidence)))
        
        # Sort matches by confidence (highest first)
        matches.sort(key=lambda x: x[2], reverse=True)
        
        # Apply non-maximum suppression to remove overlapping matches
        final_matches = []
        template_width, template_height = tpl_gray.shape[1], tpl_gray.shape[0]
        
        for match in matches:
            if len(final_matches) >= max_results:
                break
                
            # Check if this match overlaps with any existing match
            is_overlapping = False
            for existing in final_matches:
                # Calculate overlap
                overlap_x = max(0, min(match[0] + template_width, existing[0] + template_width) - max(match[0], existing[0]))
                overlap_y = max(0, min(match[1] + template_height, existing[1] + template_height) - max(match[1], existing[1]))
                overlap_area = overlap_x * overlap_y
                template_area = template_width * template_height
                
                # If overlap is significant, skip this match
                if overlap_area > 0.5 * template_area:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                final_matches.append(match)
        
        return final_matches
    
    def preprocess_image(self, image, operations=None):
        """
        Preprocess an image to improve matching
        
        Args:
            image: OpenCV image to preprocess
            operations: List of preprocessing operations to apply
                Options: 'gray', 'blur', 'clahe', 'sharpen', 'threshold'
                
        Returns:
            processed_image: The processed OpenCV image
        """
        if image is None:
            return None
            
        operations = operations or ['gray']
        processed = image.copy()
        
        for op in operations:
            if op == 'gray' and len(processed.shape) == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            
            elif op == 'blur':
                ksize = 3  # Kernel size can be adjusted
                processed = cv2.GaussianBlur(processed, (ksize, ksize), 0)
            
            elif op == 'clahe':
                # Convert to LAB for CLAHE if it's a color image
                if len(processed.shape) == 3:
                    lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    l = clahe.apply(l)
                    lab = cv2.merge((l, a, b))
                    processed = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                else:
                    # For grayscale
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    processed = clahe.apply(processed)
            
            elif op == 'sharpen':
                kernel = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]])
                processed = cv2.filter2D(processed, -1, kernel)
            
            elif op == 'threshold' and len(processed.shape) == 2:
                # Only for grayscale images
                _, processed = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return processed
    
    def get_stats(self):
        """Get statistics about the matcher's performance"""
        return self.stats
    
    def reset_stats(self):
        """Reset all statistics"""
        for key in self.stats:
            self.stats[key] = 0