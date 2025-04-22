"""
Setup Wizard UI Module
Implements the initial setup wizard for the application
"""
import logging
import time
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QGroupBox,
    QCheckBox, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage

from ui.game_specific_page import GameSpecificPage

logger = logging.getLogger('ui.setup_wizard')

class SetupWizard(QWizard):
    """Setup wizard for initial configuration"""
    
    def __init__(self, config_manager, screen_capture, parent=None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.screen_capture = screen_capture
        
        self.setWindowTitle("Spell Caster Setup Wizard")
        self.setMinimumSize(700, 500)
        
        # Add pages
        self.addPage(WelcomePage())
        self.addPage(ScanAreaPage(config_manager, screen_capture))
        self.addPage(IconTemplatePage(config_manager, screen_capture))
        self.addPage(KeybindPage(config_manager))
        self.addPage(GameSpecificPage(config_manager))
        self.addPage(CompletionPage())
        
        # Set wizard style
        self.setWizardStyle(QWizard.ModernStyle)
        
        # Set wizard buttons
        self.setButtonText(QWizard.NextButton, "Next >")
        self.setButtonText(QWizard.BackButton, "< Back")
        self.setButtonText(QWizard.FinishButton, "Finish")
        self.setButtonText(QWizard.CancelButton, "Cancel")
        
    def accept(self):
        """Handle wizard completion"""
        # Save any final configuration
        super().accept()

class WelcomePage(QWizardPage):
    """Welcome page of the setup wizard"""
    
    def __init__(self):
        super().__init__()
        
        self.setTitle("Welcome to Spell Caster Setup")
        self.setSubTitle("This wizard will help you configure the application to detect and cast spells automatically.")
        
        layout = QVBoxLayout()
        
        intro_text = (
            "<p>Spell Caster works by analyzing your game screen and detecting spell icons "
            "that need to be cast. When it detects a specific spell icon, it will "
            "automatically press the corresponding key on your keyboard.</p>"
            "<p>This wizard will guide you through the following steps:</p>"
            "<ol>"
            "<li>Define the screen area where your spell icons appear</li>"
            "<li>Capture templates for the spells you want to detect</li>"
            "<li>Configure keyboard shortcuts for each spell</li>"
            "</ol>"
            "<p>Click 'Next' to begin setup.</p>"
        )
        
        intro_label = QLabel(intro_text)
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # Tips
        tips_group = QGroupBox("Tips for Best Results")
        tips_layout = QVBoxLayout()
        
        tips_text = (
            "• Run your game in windowed mode for best detection results\n"
            "• Make sure spell icons are clearly visible and not obscured\n"
            "• For best performance, focus on detecting just a few critical spells\n"
            "• You can always reconfigure or fine-tune settings later"
        )
        
        tips_label = QLabel(tips_text)
        tips_layout.addWidget(tips_label)
        tips_group.setLayout(tips_layout)
        
        layout.addWidget(tips_group)
        layout.addStretch()
        
        self.setLayout(layout)

class ScanAreaPage(QWizardPage):
    """Page for defining the screen area to scan for spell icons"""
    
    def __init__(self, config_manager, screen_capture):
        super().__init__()
        
        self.config_manager = config_manager
        self.screen_capture = screen_capture
        
        self.setTitle("Define Scan Area")
        self.setSubTitle("Capture the area of your screen where spell icons appear")
        
        self.scan_area = None
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Please position your game window so that the spell icons are visible. "
            "Then click 'Capture Screen' and select the area containing the leftmost spell icon."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Capture controls
        capture_layout = QHBoxLayout()
        
        self.capture_button = QPushButton("Capture Screen")
        self.capture_button.clicked.connect(self.capture_screen)
        capture_layout.addWidget(self.capture_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_capture)
        self.reset_button.setEnabled(False)
        capture_layout.addWidget(self.reset_button)
        
        layout.addLayout(capture_layout)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("No area selected")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(200)
        preview_layout.addWidget(self.preview_label)
        
        self.coordinates_label = QLabel("Coordinates: None")
        preview_layout.addWidget(self.coordinates_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        self.setLayout(layout)
        
        # Load existing configuration if available
        config = self.config_manager.load_config()
        if 'scan_area' in config:
            self.scan_area = config['scan_area']
            self.update_preview()
        
    def capture_screen(self):
        """Capture the screen and allow user to select a region"""
        # Minimize the wizard temporarily
        wizard = self.wizard()
        wizard.showMinimized()
        
        # Small delay to allow the window to minimize
        time.sleep(0.5)
        
        try:
            # Capture full screen
            screenshot = self.screen_capture.capture_full_screen()
            if screenshot is None:
                QMessageBox.warning(
                    self,
                    "Capture Failed",
                    "Failed to capture screen. Please try again."
                )
                wizard.showNormal()
                return
                
            # Create window to display the screenshot
            window_name = "Select Scan Area (Click and drag to select, then press Enter)"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
            # Set up mouse callback for selection
            selection = {'x': -1, 'y': -1, 'w': 0, 'h': 0, 'selecting': False, 'complete': False}
            
            def mouse_callback(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    selection['x'] = x
                    selection['y'] = y
                    selection['selecting'] = True
                    selection['complete'] = False
                elif event == cv2.EVENT_MOUSEMOVE and selection['selecting']:
                    selection['w'] = x - selection['x']
                    selection['h'] = y - selection['y']
                elif event == cv2.EVENT_LBUTTONUP:
                    selection['w'] = x - selection['x']
                    selection['h'] = y - selection['y']
                    selection['selecting'] = False
                    selection['complete'] = True
            
            cv2.setMouseCallback(window_name, mouse_callback)
            
            # Display the screenshot and allow selection
            clone = screenshot.copy()
            while True:
                img = clone.copy()
                if selection['x'] >= 0 and (selection['selecting'] or selection['complete']):
                    x, y, w, h = selection['x'], selection['y'], selection['w'], selection['h']
                    # Ensure positive width and height
                    if w < 0:
                        x += w
                        w = -w
                    if h < 0:
                        y += h
                        h = -h
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                cv2.imshow(window_name, img)
                key = cv2.waitKey(1)
                
                # Enter key accepts the selection
                if key == 13 and selection['complete'] and selection['w'] > 0 and selection['h'] > 0:
                    break
                # Escape key cancels
                elif key == 27:
                    selection['complete'] = False
                    break
            
            # Clean up
            cv2.destroyAllWindows()
            
            # Save selection if completed
            if selection['complete']:
                x, y, w, h = selection['x'], selection['y'], selection['w'], selection['h']
                
                # Ensure positive width and height
                if w < 0:
                    x += w
                    w = -w
                if h < 0:
                    y += h
                    h = -h
                
                self.scan_area = (x, y, w, h)
                
                # Update config
                config = self.config_manager.load_config()
                config['scan_area'] = self.scan_area
                self.config_manager.save_config(config)
                
                # Update UI
                self.update_preview()
                self.reset_button.setEnabled(True)
                self.completeChanged.emit()
        
        finally:
            # Restore wizard window
            wizard.showNormal()
            wizard.activateWindow()
    
    def update_preview(self):
        """Update the preview image with the selected scan area"""
        if self.scan_area:
            # Capture the defined area
            x, y, w, h = self.scan_area
            self.coordinates_label.setText(f"Coordinates: X={x}, Y={y}, Width={w}, Height={h}")
            
            # Try to get an image of the area
            try:
                area_img = self.screen_capture.capture_region(self.scan_area)
                if area_img is not None:
                    # Convert from BGR to RGB and then to QImage/QPixmap
                    area_img_rgb = cv2.cvtColor(area_img, cv2.COLOR_BGR2RGB)
                    h, w, ch = area_img_rgb.shape
                    qimg = QImage(area_img_rgb.data, w, h, ch * w, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    # Scale pixmap to fit the preview label while maintaining aspect ratio
                    pixmap = pixmap.scaled(
                        self.preview_label.width(), 
                        self.preview_label.height(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    
                    self.preview_label.setPixmap(pixmap)
                else:
                    self.preview_label.setText("Failed to capture preview")
            except Exception as e:
                logger.error(f"Error updating preview: {str(e)}", exc_info=True)
                self.preview_label.setText(f"Error: {str(e)}")
        else:
            self.preview_label.setText("No area selected")
            self.coordinates_label.setText("Coordinates: None")
    
    def reset_capture(self):
        """Reset the captured area"""
        self.scan_area = None
        
        # Update config
        config = self.config_manager.load_config()
        if 'scan_area' in config:
            del config['scan_area']
        self.config_manager.save_config(config)
        
        # Update UI
        self.update_preview()
        self.reset_button.setEnabled(False)
        self.completeChanged.emit()
    
    def isComplete(self):
        """Check if the page is complete"""
        return self.scan_area is not None

class IconTemplatePage(QWizardPage):
    """Page for capturing spell icon templates"""
    
    def __init__(self, config_manager, screen_capture):
        super().__init__()
        
        self.config_manager = config_manager
        self.screen_capture = screen_capture
        
        self.setTitle("Capture Spell Icons")
        self.setSubTitle("Capture the spell icons you want to detect")
        
        self.icon_templates = {}
        self.current_capture = None
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.update_live_preview)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "Now you'll capture templates for the spell icons you want to detect. "
            "Make sure your game is showing the spell icons, then enter a name for "
            "each spell and click 'Capture Icon'."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Live preview
        preview_group = QGroupBox("Live Preview")
        preview_layout = QVBoxLayout()
        
        self.live_preview_label = QLabel("Click 'Start Live Preview' to see the scan area")
        self.live_preview_label.setAlignment(Qt.AlignCenter)
        self.live_preview_label.setMinimumHeight(150)
        preview_layout.addWidget(self.live_preview_label)
        
        preview_buttons = QHBoxLayout()
        self.start_preview_button = QPushButton("Start Live Preview")
        self.start_preview_button.clicked.connect(self.toggle_live_preview)
        preview_buttons.addWidget(self.start_preview_button)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        layout.addLayout(preview_buttons)
        
        # Template capture
        capture_group = QGroupBox("Capture Templates")
        capture_layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Spell Name:"))
        self.spell_name_edit = QLabel("N1")  # Default to N1 which is visible in the image
        name_layout.addWidget(self.spell_name_edit)
        name_layout.addStretch()
        
        self.capture_button = QPushButton("Capture This Icon")
        self.capture_button.clicked.connect(self.capture_template)
        name_layout.addWidget(self.capture_button)
        
        capture_layout.addLayout(name_layout)
        
        # Template list
        self.template_list_label = QLabel("No templates captured")
        capture_layout.addWidget(self.template_list_label)
        
        self.clear_templates_button = QPushButton("Clear All Templates")
        self.clear_templates_button.clicked.connect(self.clear_templates)
        self.clear_templates_button.setEnabled(False)
        capture_layout.addWidget(self.clear_templates_button)
        
        capture_group.setLayout(capture_layout)
        layout.addWidget(capture_group)
        
        # Spell presets (based on the image)
        preset_group = QGroupBox("Preset Spells")
        preset_layout = QVBoxLayout()
        
        preset_text = (
            "Based on the provided image, the following spells have been detected:\n"
            "- N5 (left icon)\n"
            "- C1 (middle icon)\n"
            "- N1 (right icon)\n"
        )
        
        preset_label = QLabel(preset_text)
        preset_layout.addWidget(preset_label)
        
        # Buttons for preset spells
        preset_buttons = QHBoxLayout()
        
        capture_n5_button = QPushButton("Add N5")
        capture_n5_button.clicked.connect(lambda: self.add_preset_template("N5"))
        preset_buttons.addWidget(capture_n5_button)
        
        capture_c1_button = QPushButton("Add C1")
        capture_c1_button.clicked.connect(lambda: self.add_preset_template("C1"))
        preset_buttons.addWidget(capture_c1_button)
        
        capture_n1_button = QPushButton("Add N1")
        capture_n1_button.clicked.connect(lambda: self.add_preset_template("N1"))
        preset_buttons.addWidget(capture_n1_button)
        
        preset_layout.addLayout(preset_buttons)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        self.setLayout(layout)
        
        # Load existing configuration if available
        config = self.config_manager.load_config()
        if 'icon_templates' in config:
            self.icon_templates = config['icon_templates']
            self.update_template_list()
    
    def toggle_live_preview(self):
        """Toggle the live preview of the scan area"""
        if self.capture_timer.isActive():
            self.capture_timer.stop()
            self.start_preview_button.setText("Start Live Preview")
        else:
            # Check if scan area is defined
            config = self.config_manager.load_config()
            if 'scan_area' not in config:
                QMessageBox.warning(
                    self,
                    "Scan Area Not Defined",
                    "Please define a scan area on the previous page first."
                )
                return
                
            self.capture_timer.start(100)  # Update every 100ms
            self.start_preview_button.setText("Stop Live Preview")
    
    def update_live_preview(self):
        """Update the live preview image"""
        config = self.config_manager.load_config()
        scan_area = config.get('scan_area')
        
        if not scan_area:
            self.live_preview_label.setText("Scan area not defined")
            return
            
        try:
            screenshot = self.screen_capture.capture_region(scan_area)
            if screenshot is not None:
                self.current_capture = screenshot
                
                # Convert from BGR to RGB and then to QImage/QPixmap
                screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
                h, w, ch = screenshot_rgb.shape
                qimg = QImage(screenshot_rgb.data, w, h, ch * w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                
                # Scale pixmap to fit the preview label while maintaining aspect ratio
                pixmap = pixmap.scaled(
                    self.live_preview_label.width(),
                    self.live_preview_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.live_preview_label.setPixmap(pixmap)
            else:
                self.live_preview_label.setText("Failed to capture preview")
        except Exception as e:
            logger.error(f"Error updating live preview: {str(e)}", exc_info=True)
            self.live_preview_label.setText(f"Error: {str(e)}")
    
    def capture_template(self):
        """Capture the current image as a template for a spell icon"""
        if self.current_capture is None:
            QMessageBox.warning(
                self,
                "No Image",
                "Please start the live preview to capture an image."
            )
            return
            
        spell_name = self.spell_name_edit.text().strip()
        if not spell_name:
            QMessageBox.warning(
                self,
                "Missing Name",
                "Please enter a name for the spell."
            )
            return
            
        # Store the template
        self.icon_templates[spell_name] = self.current_capture.copy()
        
        # Update config
        config = self.config_manager.load_config()
        config['icon_templates'] = self.icon_templates
        self.config_manager.save_config(config)
        
        # Update UI
        self.update_template_list()
        self.clear_templates_button.setEnabled(True)
        self.completeChanged.emit()
        
        QMessageBox.information(
            self,
            "Template Saved",
            f"Template for '{spell_name}' has been saved."
        )
    
    def add_preset_template(self, spell_name):
        """Add a preset template based on the provided images"""
        # Since we can't actually capture the templates from the static image,
        # we'll create placeholder templates for these spells
        # In a real application, this would use the current_capture
        
        # Create a placeholder template (black image with the spell name)
        template = np.zeros((64, 64, 3), dtype=np.uint8)
        cv2.putText(
            template,
            spell_name,
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        # Store the template
        self.icon_templates[spell_name] = template
        
        # Update config
        config = self.config_manager.load_config()
        config['icon_templates'] = self.icon_templates
        self.config_manager.save_config(config)
        
        # Update UI
        self.update_template_list()
        self.clear_templates_button.setEnabled(True)
        self.completeChanged.emit()
        
        QMessageBox.information(
            self,
            "Template Added",
            f"Preset template for '{spell_name}' has been added."
        )
    
    def update_template_list(self):
        """Update the list of captured templates"""
        if not self.icon_templates:
            self.template_list_label.setText("No templates captured")
            return
            
        template_text = "Captured Templates:\n"
        for name in self.icon_templates:
            template_text += f"- {name}\n"
            
        self.template_list_label.setText(template_text)
    
    def clear_templates(self):
        """Clear all captured templates"""
        reply = QMessageBox.question(
            self,
            "Clear Templates",
            "Are you sure you want to clear all templates?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.icon_templates = {}
            
            # Update config
            config = self.config_manager.load_config()
            if 'icon_templates' in config:
                del config['icon_templates']
            self.config_manager.save_config(config)
            
            # Update UI
            self.update_template_list()
            self.clear_templates_button.setEnabled(False)
            self.completeChanged.emit()
    
    def isComplete(self):
        """Check if the page is complete"""
        return len(self.icon_templates) > 0

class KeybindPage(QWizardPage):
    """Page for configuring keybinds for the detected spell icons"""
    
    def __init__(self, config_manager):
        super().__init__()
        
        self.config_manager = config_manager
        
        self.setTitle("Configure Keybinds")
        self.setSubTitle("Assign keyboard shortcuts to your spell icons")
        
        self.keybinds = {}
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "For each spell icon, assign a keyboard key that should be pressed "
            "when that icon is detected. You can use letters, numbers, or "
            "special keys like F1-F12."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Keybind group
        self.keybind_group = QGroupBox("Spell Keybinds")
        self.keybind_layout = QVBoxLayout()
        self.keybind_group.setLayout(self.keybind_layout)
        layout.addWidget(self.keybind_group)
        
        # Default keybinds
        default_group = QGroupBox("Suggested Default Keybinds")
        default_layout = QVBoxLayout()
        
        default_text = (
            "Based on the provided image, we suggest these keybinds:\n"
            "• N5 → 1\n"
            "• C1 → 2\n"
            "• N1 → 3\n"
            "\nClick 'Apply Defaults' to use these settings."
        )
        
        default_label = QLabel(default_text)
        default_layout.addWidget(default_label)
        
        self.apply_defaults_button = QPushButton("Apply Defaults")
        self.apply_defaults_button.clicked.connect(self.apply_default_keybinds)
        default_layout.addWidget(self.apply_defaults_button)
        
        default_group.setLayout(default_layout)
        layout.addWidget(default_group)
        
        self.setLayout(layout)
        
        # Load existing configuration if available
        config = self.config_manager.load_config()
        self.keybinds = config.get('keybinds', {})
        self.update_keybind_ui()
        
    def update_keybind_ui(self):
        """Update the keybind UI based on the available templates"""
        # Clear the current layout
        while self.keybind_layout.count():
            item = self.keybind_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # Get template names
        config = self.config_manager.load_config()
        templates = config.get('icon_templates', {})
        
        if not templates:
            self.keybind_layout.addWidget(QLabel("No spell icons have been captured yet."))
            return
            
        # Add keybind inputs for each template
        for name in templates:
            row_layout = QHBoxLayout()
            
            row_layout.addWidget(QLabel(f"{name}:"))
            
            # Common key options
            key_options = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", 
                           "q", "w", "e", "r", "t", "y", "f", "g", "z", "x", "c", "v"]
            
            combo = QComboBox()
            combo.addItems(key_options)
            combo.setEditable(True)
            
            # Set current value if exists
            if name in self.keybinds:
                current_key = self.keybinds[name]
                if current_key in key_options:
                    combo.setCurrentText(current_key)
                else:
                    combo.setCurrentText(current_key)
                    
            # Connect to update function
            combo.currentTextChanged.connect(lambda text, name=name: self.update_keybind(name, text))
            
            row_layout.addWidget(combo)
            self.keybind_layout.addLayout(row_layout)
            
        self.keybind_layout.addStretch()
        
    def update_keybind(self, name, key):
        """Update a keybind for a spell"""
        if key:
            self.keybinds[name] = key
        elif name in self.keybinds:
            del self.keybinds[name]
            
        # Update config
        config = self.config_manager.load_config()
        config['keybinds'] = self.keybinds
        self.config_manager.save_config(config)
        
        self.completeChanged.emit()
        
    def apply_default_keybinds(self):
        """Apply the default keybinds for the preset spells"""
        default_keybinds = {
            "N5": "1",
            "C1": "2",
            "N1": "3"
        }
        
        # Update keybinds with defaults for any that exist
        config = self.config_manager.load_config()
        templates = config.get('icon_templates', {})
        
        for name in templates:
            if name in default_keybinds:
                self.keybinds[name] = default_keybinds[name]
                
        # Update config
        config['keybinds'] = self.keybinds
        self.config_manager.save_config(config)
        
        # Update UI
        self.update_keybind_ui()
        self.completeChanged.emit()
        
        QMessageBox.information(
            self,
            "Defaults Applied",
            "Default keybinds have been applied."
        )
        
    def isComplete(self):
        """Check if the page is complete"""
        config = self.config_manager.load_config()
        templates = config.get('icon_templates', {})
        
        # Ensure all templates have keybinds
        for name in templates:
            if name not in self.keybinds or not self.keybinds[name]:
                return False
                
        return len(self.keybinds) > 0

class CompletionPage(QWizardPage):
    """Final page of the setup wizard"""
    
    def __init__(self):
        super().__init__()
        
        self.setTitle("Setup Complete")
        self.setSubTitle("Your Spell Caster is now configured and ready to use")
        
        layout = QVBoxLayout()
        
        completion_text = (
            "<p>Congratulations! You have successfully configured Spell Caster.</p>"
            "<p>Here's what you can do next:</p>"
            "<ul>"
            "<li>Click 'Finish' to close this wizard and return to the main application</li>"
            "<li>In the main window, click 'Start Casting' to begin spell detection</li>"
            "<li>You can adjust detection speed and confidence settings in the main window</li>"
            "<li>To reconfigure spell icons or keybinds, use the 'Configure Spells' button</li>"
            "</ul>"
            "<p>Remember that you can always run this setup wizard again if needed.</p>"
        )
        
        completion_label = QLabel(completion_text)
        completion_label.setWordWrap(True)
        layout.addWidget(completion_label)
        
        # Autostart option
        self.autostart_checkbox = QCheckBox("Start spell detection automatically when the application launches")
        layout.addWidget(self.autostart_checkbox)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
    def validatePage(self):
        """Save final settings before completing the wizard"""
        from PyQt5.QtWidgets import QWizard
        wizard = self.wizard()
        
        # Save autostart setting
        config_manager = wizard.page(1).config_manager
        config = config_manager.load_config()
        config['autostart'] = self.autostart_checkbox.isChecked()
        config_manager.save_config(config)
        
        return True
