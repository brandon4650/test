"""
Icon Matcher Module
Handles matching spell icons in captured screen images
"""
import logging
import cv2
import numpy as np

logger = logging.getLogger('utils.icon_matcher')

class IconMatcher:
    """Class for matching spell icons in screen captures"""
    
    def __init__(self):
        """Initialize the icon matcher"""
        # Keep track of recent match results for stability
        self.recent_matches = []
        self.max_recent_matches = 3
        self.stability_threshold = 2  # Number of consecutive matches needed
        
    def find_best_match(self, image, templates):
        """
        Find the best matching icon template in the image
        
        Args:
            image: OpenCV image to search in (needle)
            templates: Dictionary of {name: template_image} (haystacks)
            
        Returns:
            tuple: (best_match_name, confidence) or (None, 0) if no match
        """
        if not templates:
            return None, 0
            
        best_match_name = None
        best_confidence = 0
        
        try:
            # Convert image to grayscale for template matching
            if image is None:
                logger.error("Input image is None")
                return None, 0
                
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # For each template, try to find a match
            for name, template in templates.items():
                if template is None:
                    logger.warning(f"Template '{name}' is None, skipping")
                    continue
                    
                # Convert template to grayscale
                try:
                    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                except cv2.error:
                    logger.warning(f"Failed to convert template '{name}' to grayscale, skipping")
                    continue
                    
                # Normalize images
                gray_image_norm = cv2.normalize(gray_image, None, 0, 255, cv2.NORM_MINMAX)
                gray_template_norm = cv2.normalize(gray_template, None, 0, 255, cv2.NORM_MINMAX)
                
                # Make sure images are the right size for matching
                if gray_image_norm.shape[0] < gray_template_norm.shape[0] or \
                   gray_image_norm.shape[1] < gray_template_norm.shape[1]:
                    logger.warning(
                        f"Image ({gray_image_norm.shape}) smaller than template '{name}' "
                        f"({gray_template_norm.shape}), skipping"
                    )
                    continue
                
                # If image and template are the same size, use simple comparison
                if gray_image_norm.shape == gray_template_norm.shape:
                    result = cv2.matchTemplate(gray_image_norm, gray_template_norm, cv2.TM_CCOEFF_NORMED)
                    confidence = result[0][0]
                else:
                    # Use template matching
                    result = cv2.matchTemplate(gray_image_norm, gray_template_norm, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    confidence = max_val
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match_name = name
            
            # Add to recent matches
            if best_match_name:
                self.recent_matches.append(best_match_name)
                if len(self.recent_matches) > self.max_recent_matches:
                    self.recent_matches.pop(0)
                
                # Check for stability
                if len(self.recent_matches) >= self.stability_threshold:
                    last_matches = self.recent_matches[-self.stability_threshold:]
                    if all(match == last_matches[0] for match in last_matches):
                        # Stable match
                        return best_match_name, best_confidence
                    else:
                        # Unstable match, return the most common one
                        from collections import Counter
                        most_common = Counter(self.recent_matches).most_common(1)[0][0]
                        return most_common, best_confidence
            
            return best_match_name, best_confidence
            
        except Exception as e:
            logger.error(f"Error in find_best_match: {str(e)}", exc_info=True)
            return None, 0
    
    def match_specific_icon(self, image, template, threshold=0.8):
        """
        Match a specific icon template in an image
        
        Args:
            image: OpenCV image to search in
            template: Template image to find
            threshold: Confidence threshold for a valid match
            
        Returns:
            tuple: (is_match, confidence)
        """
        try:
            # Convert both to grayscale
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Normalize images
            gray_image_norm = cv2.normalize(gray_image, None, 0, 255, cv2.NORM_MINMAX)
            gray_template_norm = cv2.normalize(gray_template, None, 0, 255, cv2.NORM_MINMAX)
            
            # Use template matching
            result = cv2.matchTemplate(gray_image_norm, gray_template_norm, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Check if the match exceeds threshold
            if max_val >= threshold:
                return True, max_val
            else:
                return False, max_val
                
        except Exception as e:
            logger.error(f"Error in match_specific_icon: {str(e)}", exc_info=True)
            return False, 0
    
    def find_all_matches(self, image, template, threshold=0.8):
        """
        Find all instances of a template in an image
        
        Args:
            image: OpenCV image to search in
            template: Template image to find
            threshold: Confidence threshold for valid matches
            
        Returns:
            list: List of (x, y, confidence) tuples for each match
        """
        try:
            # Convert both to grayscale
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Normalize images
            gray_image_norm = cv2.normalize(gray_image, None, 0, 255, cv2.NORM_MINMAX)
            gray_template_norm = cv2.normalize(gray_template, None, 0, 255, cv2.NORM_MINMAX)
            
            # Use template matching
            result = cv2.matchTemplate(gray_image_norm, gray_template_norm, cv2.TM_CCOEFF_NORMED)
            
            # Find all locations exceeding the threshold
            locations = np.where(result >= threshold)
            matches = []
            
            for pt in zip(*locations[::-1]):  # x, y
                matches.append((pt[0], pt[1], result[pt[1], pt[0]]))
                
            # Sort by confidence
            matches.sort(key=lambda x: x[2], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error in find_all_matches: {str(e)}", exc_info=True)
            return []
