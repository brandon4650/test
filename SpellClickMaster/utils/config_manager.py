"""
Configuration Manager Module
Handles loading, saving, and managing application configuration
"""
import os
import json
import logging
import pickle
import sys
import cv2
import numpy as np
from pathlib import Path

logger = logging.getLogger('utils.config_manager')

class ConfigManager:
    """Class for managing application configuration"""
    
    def __init__(self, config_file=None):
        """Initialize the configuration manager"""
        # Determine the application base path
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if config_file:
            self.config_file = config_file
        else:
            # Default configuration file in user's Documents folder
            documents_path = os.path.join(os.path.expanduser("~"), "Documents")
            self.config_file = os.path.join(
                documents_path,
                "SpellCaster",
                "config.json"
            )
            
        # Icon templates file (binary data)
        self.templates_file = os.path.join(
            os.path.dirname(self.config_file),
            "icon_templates.dat"
        )
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Default configuration
        self.default_config = {
            'scan_area': None,
            'detection_frequency': 0.1,  # seconds
            'confidence_threshold': 0.8,
            'cooldown': 0.5,  # seconds between actions
            'autostart': False,
            'minimize_to_tray': True,
            'keybinds': {},
            'icon_templates': {}  # Will be populated from the templates file
        }
        
        # Initialize icon templates
        self.icon_templates = {}
        
        # Load templates if they exist
        self._load_templates()
        
    def config_exists(self):
        """Check if configuration file exists"""
        return os.path.isfile(self.config_file)
        
    def load_config(self):
        """Load configuration from file"""
        if not self.config_exists():
            logger.info(f"Configuration file not found at {self.config_file}, using defaults")
            config = self.default_config.copy()
            # Add templates from separate file
            config['icon_templates'] = self.icon_templates
            return config
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Add any missing default fields
            for key, value in self.default_config.items():
                if key not in config:
                    config[key] = value
            
            # Add templates from separate file
            config['icon_templates'] = self.icon_templates
                    
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}", exc_info=True)
            config = self.default_config.copy()
            config['icon_templates'] = self.icon_templates
            return config
            
    def save_config(self, config):
        """Save configuration to file"""
        # Extract icon templates to save separately
        if 'icon_templates' in config:
            self.icon_templates = config['icon_templates']
            self._save_templates()
        
        # Filter out binary data that can't be serialized to JSON
        filtered_config = config.copy()
        
        # Remove the templates from the JSON config
        if 'icon_templates' in filtered_config:
            del filtered_config['icon_templates']
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(filtered_config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}", exc_info=True)
            return False
    
    def _save_templates(self):
        """Save icon templates to a separate binary file"""
        try:
            if self.icon_templates:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
                
                # Save templates as pickled object
                with open(self.templates_file, 'wb') as f:
                    pickle.dump(self.icon_templates, f)
                    
                logger.info(f"Templates saved to {self.templates_file}")
                return True
        except Exception as e:
            logger.error(f"Error saving templates: {str(e)}", exc_info=True)
            return False
    
    def _load_templates(self):
        """Load icon templates from a separate binary file"""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'rb') as f:
                    self.icon_templates = pickle.load(f)
                logger.info(f"Templates loaded from {self.templates_file}")
                return True
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}", exc_info=True)
            self.icon_templates = {}
            return False
            
    def save_template_image(self, name, image):
        """Save a single template image"""
        try:
            # Create the templates directory
            templates_dir = os.path.join(os.path.dirname(self.config_file), "templates")
            os.makedirs(templates_dir, exist_ok=True)
            
            # Save the image as PNG
            image_path = os.path.join(templates_dir, f"{name}.png")
            cv2.imwrite(image_path, image)
            
            # Update in-memory templates
            self.icon_templates[name] = image
            
            # Update templates file
            self._save_templates()
            
            logger.info(f"Template '{name}' saved to {image_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving template image: {str(e)}", exc_info=True)
            return False
    
    def load_template_image(self, name):
        """Load a single template image"""
        try:
            # Check if it's in memory first
            if name in self.icon_templates:
                return self.icon_templates[name]
                
            # Try to load from file
            templates_dir = os.path.join(os.path.dirname(self.config_file), "templates")
            image_path = os.path.join(templates_dir, f"{name}.png")
            
            if os.path.exists(image_path):
                image = cv2.imread(image_path)
                if image is not None:
                    # Update in-memory templates
                    self.icon_templates[name] = image
                    return image
            
            return None
        except Exception as e:
            logger.error(f"Error loading template image: {str(e)}", exc_info=True)
            return None
            
    def reset_config(self):
        """Reset configuration to defaults"""
        try:
            # Delete config file
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                logger.info(f"Configuration file {self.config_file} deleted")
                
            # Delete templates file
            if os.path.exists(self.templates_file):
                os.remove(self.templates_file)
                logger.info(f"Templates file {self.templates_file} deleted")
                
            # Delete template images
            templates_dir = os.path.join(os.path.dirname(self.config_file), "templates")
            if os.path.exists(templates_dir):
                for file in os.listdir(templates_dir):
                    if file.endswith(".png"):
                        os.remove(os.path.join(templates_dir, file))
                
                # Try to remove the directory
                try:
                    os.rmdir(templates_dir)
                except:
                    pass
                    
            # Reset in-memory templates
            self.icon_templates = {}
            
            return self.default_config.copy()
        except Exception as e:
            logger.error(f"Error resetting configuration: {str(e)}", exc_info=True)
            return self.default_config.copy()
