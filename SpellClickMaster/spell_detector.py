"""
Spell Detector Module
Handles the detection of spell icons and triggers the corresponding actions
"""
import time
import logging
import threading
import cv2
import numpy as np
from screen_capture import ScreenCapture
from keyboard_controller import KeyboardController
from utils.icon_matcher import IconMatcher
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger('spell_detector')

class SpellDetector(QObject):
    """Class for detecting spell icons and triggering keyboard actions"""
    
    status_updated = pyqtSignal(str)  # Signal for status updates
    icon_detected = pyqtSignal(str, float)  # Signal for detected icons with confidence
    screenshot_updated = pyqtSignal(object)  # Signal with current screenshot for UI
    
    def __init__(self, config_manager):
        """Initialize the spell detector with configuration"""
        super().__init__()
        self.config_manager = config_manager
        self.screen_capture = ScreenCapture()
        self.keyboard = KeyboardController()
        self.icon_matcher = IconMatcher()
        
        self.running = False
        self.paused = False
        self.detection_thread = None
        self.last_detected_icon = None
        self.last_action_time = 0
        
        # Load configuration
        config = self.config_manager.load_config()
        self.scan_area = config.get('scan_area', None)  # Region to scan for spell icons
        self.detection_frequency = config.get('detection_frequency', 0.1)  # Seconds between scans
        self.confidence_threshold = config.get('confidence_threshold', 0.8)  # Minimum match confidence
        self.cooldown = config.get('cooldown', 0.5)  # Cooldown between actions in seconds
        self.keybinds = config.get('keybinds', {})  # Map of icon names to keys
        self.icon_templates = config.get('icon_templates', {})  # Map of icon names to template regions
        
        # Performance metrics
        self.fps = 0
        self.frame_times = []
        self.max_frame_times = 10  # Number of frame times to keep for averaging
        
        # Add preset spell templates from the image
        self._add_preset_templates()
        
    def _add_preset_templates(self):
        """Add preset templates if no templates exist yet"""
        if not self.icon_templates:
            try:
                # Create default templates for N5, C1, and N1 from the image shown in the attached assets
                # These are likely to be replaced by actual templates from the user's game
                # Just providing sensible defaults for first-time users
                
                # Create basic colored squares as placeholders for spell icons
                # Blue for N5
                n5_template = np.zeros((40, 40, 3), dtype=np.uint8)
                n5_template[:, :] = (255, 0, 0)  # Blue square
                
                # Purple for C1
                c1_template = np.zeros((40, 40, 3), dtype=np.uint8)
                c1_template[:, :] = (128, 0, 128)  # Purple square
                
                # Green for N1
                n1_template = np.zeros((40, 40, 3), dtype=np.uint8)
                n1_template[:, :] = (0, 255, 0)  # Green square
                
                # Add these to the templates
                self.icon_templates['N5'] = n5_template
                self.icon_templates['C1'] = c1_template
                self.icon_templates['N1'] = n1_template
                
                # Default keybinds
                self.keybinds['N5'] = '1'
                self.keybinds['C1'] = '2'
                self.keybinds['N1'] = '3'
                
                # Save the configuration
                config = self.config_manager.load_config()
                config['icon_templates'] = self.icon_templates
                config['keybinds'] = self.keybinds
                self.config_manager.save_config(config)
                
                logger.info("Added preset spell templates for first-time use")
            except Exception as e:
                logger.error(f"Error adding preset templates: {str(e)}", exc_info=True)
        
    def start(self):
        """Start the detection process"""
        if self.running:
            logger.warning("Detection already running")
            return False
            
        if not self.scan_area:
            self.status_updated.emit("Error: Scan area not configured")
            logger.error("Scan area not configured")
            return False
            
        if not self.keybinds:
            self.status_updated.emit("Error: No keybinds configured")
            logger.error("No keybinds configured")
            return False
            
        self.running = True
        self.paused = False
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        self.status_updated.emit("Detection started")
        logger.info("Detection process started")
        return True
    
    def pause(self):
        """Pause the detection process without stopping the thread"""
        if self.running and not self.paused:
            self.paused = True
            self.status_updated.emit("Detection paused")
            logger.info("Detection process paused")
            return True
        return False
    
    def resume(self):
        """Resume the detection process if paused"""
        if self.running and self.paused:
            self.paused = False
            self.status_updated.emit("Detection resumed")
            logger.info("Detection process resumed")
            return True
        return False
        
    def stop(self):
        """Stop the detection process"""
        if not self.running:
            return
            
        self.running = False
        self.paused = False
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
            
        self.status_updated.emit("Detection stopped")
        logger.info("Detection process stopped")
        
    def update_config(self):
        """Update configuration from config manager"""
        config = self.config_manager.load_config()
        self.scan_area = config.get('scan_area')
        self.detection_frequency = config.get('detection_frequency', 0.1)
        self.confidence_threshold = config.get('confidence_threshold', 0.8)
        self.cooldown = config.get('cooldown', 0.5)
        self.keybinds = config.get('keybinds', {})
        self.icon_templates = config.get('icon_templates', {})
        logger.info("Configuration updated")
        
    def is_running(self):
        """Check if detection is running"""
        return self.running and not self.paused
    
    def is_paused(self):
        """Check if detection is paused"""
        return self.running and self.paused
        
    def _detection_loop(self):
        """Main detection loop that runs in a separate thread"""
        logger.info("Detection loop started")
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            # Get screenshot of scan area
            scan_area = self.scan_area
            if not scan_area:
                logger.warning("No scan area defined, skipping detection")
                time.sleep(1)
                continue
                
            screenshot = self.screen_capture.capture_region(scan_area)
            if screenshot is None:
                logger.warning("Failed to capture scan area")
                time.sleep(1)
                continue
                
            # Emit the screenshot for UI display if needed
            self.screenshot_updated.emit(screenshot)
            
            # Match each template against the screenshot
            detected = False
            highest_confidence = 0
            best_match = None
            
            for name, template in self.templates.items():
                logger.debug(f"Checking template: {name}")
                confidence = self._match_template(screenshot, template)
                logger.debug(f"Template {name} confidence: {confidence:.4f}")
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = name
                    
                # If confidence is above threshold, consider it a match
                if confidence > self.confidence_threshold:
                    logger.info(f"Detected '{name}' with confidence {confidence:.4f}")
                    
                    # Check if the spell is on cooldown
                    now = time.time()
                    if now - self.last_detection_time < self.cooldown:
                        logger.debug(f"Spell on cooldown, skipping action")
                        detected = True
                        continue
                        
                    # Spell detected, press the corresponding key
                    key = self.keybinds.get(name)
                    if key:
                        logger.info(f"Pressing key: {key} for spell: {name}")
                        self.keyboard_controller.press_key(key)
                        self.icon_detected.emit(name, confidence)
                        self.last_detection_time = now
                        detected = True
                        break
                    else:
                        logger.warning(f"No keybind defined for detected spell: {name}")
            
            if not detected and best_match:
                logger.debug(f"Best match was '{best_match}' with confidence {highest_confidence:.4f} (below threshold)")
            elif not detected:
                logger.debug("No matches found")
                
            # Wait before next detection
            time.sleep(self.detection_frequency)
    
    def get_performance_stats(self):
        """Get performance statistics"""
        return {
            'fps': self.fps,
            'avg_frame_time': sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0,
            'min_frame_time': min(self.frame_times) if self.frame_times else 0,
            'max_frame_time': max(self.frame_times) if self.frame_times else 0,
        }
