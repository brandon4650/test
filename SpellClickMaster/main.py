#!/usr/bin/env python3
"""
Spell Caster Automation Tool
Main entry point for the application
"""
import sys
import os
import logging
import platform
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from ui.main_window import MainWindow
from utils.config_manager import ConfigManager

# Determine if we are running as an executable or as a script
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Set up logging
log_path = os.path.join(application_path, 'spell_caster.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path)
    ]
)

logger = logging.getLogger('main')

def is_admin():
    """Check if the application is running with administrator privileges"""
    try:
        if platform.system() == 'Windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0  # Unix-based check for root
    except:
        return False
    
def set_predefined_scan_area():
    """Set predefined scan area from the error message coordinates"""
    import json
    import os
    import logging
    
    logger = logging.getLogger('setup')
    
    config_file = os.path.join(os.path.dirname(__file__), 'spell_caster_config.json')
    
    try:
        # Check if the file exists and is accessible
        if os.path.exists(config_file):
            # Load existing config
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Create a new config
            config = {}
        
        # Set the scan area to the coordinates from the error message
        config['scan_area'] = [1567, 1023, 75, 74]
        
        # Save the config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Predefined scan area set to X: 1567, Y: 1023, W: 75, H: 74")
        return True
    except Exception as e:
        logger.error(f"Failed to set predefined scan area: {str(e)}")
        return False

def show_error_dialog(message, details=None):
    """Show an error dialog with optional details"""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Spell Caster - Error")
    msg_box.setText(message)
    if details:
        msg_box.setDetailedText(details)
    msg_box.exec_()

def main():
    """Main application entry point"""
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Spell Caster")
        
        # Set icon from different possible locations
        icon_paths = [
            os.path.join(application_path, "assets", "app_icon.ico"),
            os.path.join(application_path, "assets", "app_icon.svg")
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                break
        
        # Initialize configuration
        config_file = os.path.join(application_path, "spell_caster_config.json")
        config_manager = ConfigManager(config_file)
        
        # Check if first run or config missing
        first_run = not config_manager.config_exists()
        
        # Check for admin rights if on Windows
        if platform.system() == 'Windows' and not is_admin():
            logger.warning("Application may need administrator privileges for full keyboard control")
            # Warning box
            QMessageBox.warning(
                None, 
                "Limited Functionality Warning", 
                "Spell Caster may need administrator privileges for full keyboard control.\n"
                "Some key combinations might not work correctly without admin rights.\n\n"
                "Consider restarting the application as administrator if you experience issues."
            )
        
        # Create and show main window
        window = MainWindow(config_manager, first_run=first_run)
        window.show()
        
        # Start application event loop
        sys.exit(app.exec_())
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Application failed to start: {str(e)}", exc_info=True)
        
        # Try to show a GUI error dialog
        try:
            show_error_dialog(
                f"The application failed to start: {str(e)}",
                error_details
            )
        except:
            # If GUI dialog fails, resort to console output
            print(f"CRITICAL ERROR: {str(e)}\n{error_details}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
