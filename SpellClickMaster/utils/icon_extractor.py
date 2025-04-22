"""
Icon Extractor Module
Analyzes game screenshots to automatically extract and identify spell icons
"""
import os
import cv2
import numpy as np
import logging
from collections import namedtuple

# Set up logging
logger = logging.getLogger('utils.icon_extractor')

# A structure to store icon metadata
IconInfo = namedtuple('IconInfo', ['image', 'position', 'size', 'confidence', 'name'])

class IconExtractor:
    """
    Class for extracting spell icons from game screenshots using advanced OpenCV techniques
    """
    
    def __init__(self, min_size=20, max_size=100):
        """
        Initialize the icon extractor
        
        Args:
            min_size: Minimum size of icons to detect
            max_size: Maximum size of icons to detect
        """
        self.min_size = min_size
        self.max_size = max_size
        
        # Track previously extracted icons for stability
        self.previous_extractions = []
        self.max_history = 3
    
    def analyze_screenshot(self, image, method='contour'):
        """
        Analyze a screenshot to identify potential spell icons
        
        Args:
            image: OpenCV image to analyze
            method: Method to use for icon extraction 
                    ('contour', 'features', 'grid', or 'color')
            
        Returns:
            list: List of IconInfo objects for extracted icons
        """
        if image is None:
            logger.error("Cannot analyze None image")
            return []
            
        try:
            if method == 'contour':
                return self._extract_by_contours(image)
            elif method == 'features':
                return self._extract_by_features(image)
            elif method == 'grid':
                return self._extract_by_grid(image)
            elif method == 'color':
                return self._extract_by_color(image)
            else:
                logger.warning(f"Unknown extraction method: {method}, using contour")
                return self._extract_by_contours(image)
        except Exception as e:
            logger.error(f"Error extracting icons: {str(e)}", exc_info=True)
            return []
    
    def _extract_by_contours(self, image):
        """Extract icons by finding contours around distinct objects"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Process contours to find potential icons
        icons = []
        for i, contour in enumerate(contours):
            # Calculate contour area
            area = cv2.contourArea(contour)
            
            # Skip if too small or too large
            if area < self.min_size * self.min_size or area > self.max_size * self.max_size:
                continue
                
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Skip non-square-ish shapes (most icons are approximately square)
            aspect_ratio = float(w) / h
            if aspect_ratio < 0.7 or aspect_ratio > 1.3:
                continue
                
            # Extract icon
            icon_image = image[y:y+h, x:x+w]
            
            # Add to list with dummy confidence score and auto-generated name
            icons.append(IconInfo(
                image=icon_image,
                position=(x, y),
                size=(w, h),
                confidence=0.8,  # Dummy score
                name=f"icon_{i}"
            ))
        
        # Sort by position (left to right)
        icons.sort(key=lambda icon: icon.position[0])
        
        return icons
    
    def _extract_by_features(self, image):
        """Extract icons by finding feature-rich areas"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect SIFT features
        try:
            sift = cv2.SIFT_create()
        except AttributeError:
            # Fall back for older OpenCV versions
            sift = cv2.xfeatures2d.SIFT_create()
            
        keypoints, _ = sift.detectAndCompute(gray, None)
        
        # If we don't have any keypoints, fall back to contour method
        if not keypoints:
            logger.info("No features detected, falling back to contour method")
            return self._extract_by_contours(image)
        
        # Cluster keypoints to find dense regions (potential icons)
        keypoint_positions = np.array([kp.pt for kp in keypoints])
        
        # If we don't have enough keypoints for k-means, fall back
        if len(keypoint_positions) < 5:
            logger.info("Not enough keypoints for clustering, falling back to contour method")
            return self._extract_by_contours(image)
        
        # Use DBSCAN for clustering
        from sklearn.cluster import DBSCAN
        clustering = DBSCAN(eps=30, min_samples=3).fit(keypoint_positions)
        
        # Get cluster labels
        labels = clustering.labels_
        
        # Organize keypoints by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:  # Skip noise points
                continue
                
            if label not in clusters:
                clusters[label] = []
                
            clusters[label].append(keypoint_positions[i])
        
        icons = []
        for i, points in clusters.items():
            points = np.array(points)
            
            # Get min and max x, y for the cluster
            min_x, min_y = np.min(points, axis=0)
            max_x, max_y = np.max(points, axis=0)
            
            # Add padding
            padding = 5
            min_x = max(0, int(min_x) - padding)
            min_y = max(0, int(min_y) - padding)
            max_x = min(image.shape[1], int(max_x) + padding)
            max_y = min(image.shape[0], int(max_y) + padding)
            
            # Calculate width and height
            width = max_x - min_x
            height = max_y - min_y
            
            # Skip if too small or too large
            if width < self.min_size or height < self.min_size or width > self.max_size or height > self.max_size:
                continue
                
            # Extract icon
            icon_image = image[min_y:max_y, min_x:max_x]
            
            # Add to list
            icons.append(IconInfo(
                image=icon_image,
                position=(min_x, min_y),
                size=(width, height),
                confidence=0.7,  # Dummy score
                name=f"icon_{i}"
            ))
        
        # Sort by position (left to right)
        icons.sort(key=lambda icon: icon.position[0])
        
        return icons
    
    def _extract_by_grid(self, image, grid_size=None):
        """Extract icons by dividing the image into a grid and analyzing each cell"""
        # Determine grid size based on image dimensions if not provided
        if grid_size is None:
            # Estimate a reasonable grid based on the image size and expected icon size
            avg_size = (self.min_size + self.max_size) // 2
            rows = max(1, image.shape[0] // avg_size)
            cols = max(1, image.shape[1] // avg_size)
            grid_size = (rows, cols)
        
        # Calculate cell size
        cell_height = image.shape[0] // grid_size[0]
        cell_width = image.shape[1] // grid_size[1]
        
        icons = []
        for r in range(grid_size[0]):
            for c in range(grid_size[1]):
                # Calculate cell boundaries
                top = r * cell_height
                left = c * cell_width
                bottom = min(image.shape[0], (r + 1) * cell_height)
                right = min(image.shape[1], (c + 1) * cell_width)
                
                # Extract cell
                cell = image[top:bottom, left:right]
                
                # Check if this cell might contain an icon
                if self._is_potential_icon(cell):
                    # Add to list
                    icons.append(IconInfo(
                        image=cell,
                        position=(left, top),
                        size=(right-left, bottom-top),
                        confidence=0.6,  # Lower confidence for grid method
                        name=f"icon_r{r}c{c}"
                    ))
        
        return icons
    
    def _extract_by_color(self, image):
        """Extract icons by finding distinctive color regions"""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Find the most saturated regions (spell icons often have vibrant colors)
        _, saturation, _ = cv2.split(hsv)
        
        # Threshold the saturation channel
        _, binary = cv2.threshold(saturation, 100, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        icons = []
        for i, contour in enumerate(contours):
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Skip if too small or too large
            if w < self.min_size or h < self.min_size or w > self.max_size or h > self.max_size:
                continue
                
            # Skip non-square-ish shapes
            aspect_ratio = float(w) / h
            if aspect_ratio < 0.7 or aspect_ratio > 1.3:
                continue
                
            # Extract icon
            icon_image = image[y:y+h, x:x+w]
            
            # Add to list
            icons.append(IconInfo(
                image=icon_image,
                position=(x, y),
                size=(w, h),
                confidence=0.7,  # Dummy score
                name=f"icon_{i}"
            ))
        
        # Sort by position (left to right)
        icons.sort(key=lambda icon: icon.position[0])
        
        return icons
    
    def _is_potential_icon(self, image):
        """Determine if an image patch might contain an icon"""
        # Icons typically have:
        # 1. A good mix of colors (not just a flat color)
        # 2. Some edges/details
        # 3. Square-ish shape
        
        # Check shape
        aspect_ratio = float(image.shape[1]) / image.shape[0]
        if aspect_ratio < 0.7 or aspect_ratio > 1.3:
            return False
            
        # Check for edges
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_percentage = np.count_nonzero(edges) / (image.shape[0] * image.shape[1])
        
        # Icons typically have some edges but not too many
        if edge_percentage < 0.05 or edge_percentage > 0.5:
            return False
            
        # Check color variance (icons are typically not a flat color)
        color_std = np.std(image)
        if color_std < 15:  # Arbitrary threshold, may need tuning
            return False
            
        return True
    
    def extract_icons_from_screenshot(self, image, method='combined', max_icons=5):
        """
        Extract the most likely spell icons from a screenshot
        
        Args:
            image: OpenCV image
            method: Extraction method or 'combined' to try multiple methods
            max_icons: Maximum number of icons to extract
            
        Returns:
            list: List of IconInfo objects for extracted icons
        """
        if method == 'combined':
            # Try multiple methods and combine results
            methods = ['contour', 'features', 'color']
            all_icons = []
            
            for m in methods:
                try:
                    icons = self.analyze_screenshot(image, method=m)
                    all_icons.extend(icons)
                except Exception as e:
                    logger.warning(f"Error with method {m}: {str(e)}")
                    
            # If we have no icons, try grid method as fallback
            if not all_icons:
                try:
                    all_icons = self.analyze_screenshot(image, method='grid')
                except Exception as e:
                    logger.warning(f"Error with grid method: {str(e)}")
            
            # Filter and remove duplicates
            unique_icons = self._filter_duplicate_icons(all_icons)
            
            # Sort by x-position (left to right)
            unique_icons.sort(key=lambda icon: icon.position[0])
            
            # Rename icons based on position
            renamed_icons = []
            for i, icon in enumerate(unique_icons[:max_icons]):
                # Names based on position: leftmost = N5, second = C1, third = N1, etc.
                # (using the naming convention from the screenshots)
                if i == 0:
                    name = "N5"
                elif i == 1:
                    name = "C1"
                elif i == 2:
                    name = "N1"
                else:
                    name = f"Spell{i+1}"
                    
                renamed_icons.append(IconInfo(
                    icon.image, icon.position, icon.size, icon.confidence, name
                ))
                
            return renamed_icons
        else:
            # Use specified method
            icons = self.analyze_screenshot(image, method=method)
            
            # Sort by x-position (left to right)
            icons.sort(key=lambda icon: icon.position[0])
            
            # Limit number of icons
            icons = icons[:max_icons]
            
            # Rename icons based on position
            renamed_icons = []
            for i, icon in enumerate(icons):
                if i == 0:
                    name = "N5"
                elif i == 1:
                    name = "C1"
                elif i == 2:
                    name = "N1"
                else:
                    name = f"Spell{i+1}"
                    
                renamed_icons.append(IconInfo(
                    icon.image, icon.position, icon.size, icon.confidence, name
                ))
                
            return renamed_icons
    
    def _filter_duplicate_icons(self, icons, overlap_threshold=0.5):
        """Filter out duplicate icon detections"""
        if not icons:
            return []
            
        unique_icons = []
        
        for icon in icons:
            # Check if this icon overlaps significantly with any icon we've already added
            is_duplicate = False
            for existing in unique_icons:
                # Calculate intersection rectangle
                x1 = max(icon.position[0], existing.position[0])
                y1 = max(icon.position[1], existing.position[1])
                x2 = min(icon.position[0] + icon.size[0], existing.position[0] + existing.size[0])
                y2 = min(icon.position[1] + icon.size[1], existing.position[1] + existing.size[1])
                
                # Check if there is an intersection
                if x1 < x2 and y1 < y2:
                    # Calculate area of intersection
                    intersection_area = (x2 - x1) * (y2 - y1)
                    
                    # Calculate areas of both icons
                    icon_area = icon.size[0] * icon.size[1]
                    existing_area = existing.size[0] * existing.size[1]
                    
                    # Calculate overlap ratio
                    overlap = intersection_area / min(icon_area, existing_area)
                    
                    if overlap > overlap_threshold:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_icons.append(icon)
                
        return unique_icons
    
    def save_extracted_icons(self, icons, output_dir):
        """
        Save extracted icons to disk
        
        Args:
            icons: List of IconInfo objects
            output_dir: Directory to save icons to
            
        Returns:
            list: List of paths to saved icon files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        saved_paths = []
        for icon in icons:
            # Create a filename
            filename = f"{icon.name}.png"
            filepath = os.path.join(output_dir, filename)
            
            # Save the image
            cv2.imwrite(filepath, icon.image)
            saved_paths.append(filepath)
            
        return saved_paths