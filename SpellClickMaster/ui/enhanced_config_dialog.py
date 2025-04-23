"""
Enhanced Configuration Dialog UI Module
Implements an improved dialog for configuring spell icons and keybinds with expansion/class support
"""
import logging
import cv2
import numpy as np
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QFormLayout, QDoubleSpinBox, QMessageBox,
    QLineEdit, QWidget, QSplitter
)
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon

from ui.expansion_class_manager import ExpansionClassManager

logger = logging.getLogger('ui.enhanced_config_dialog')

class EnhancedConfigurationDialog(QDialog):
    """Enhanced dialog for configuring spell icons and keybinds with expansion/class support"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        
        self.setWindowTitle("Spell Caster Configuration")
        self.setMinimumSize(900, 600)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        main_layout = QVBoxLayout(self)
        
        # Create a splitter for expansion/class manager and settings
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Create expansion/class manager
        self.exp_class_manager = ExpansionClassManager(self.config_manager)
        self.exp_class_manager.config_changed.connect(self.on_config_changed)
        
        # Tab widget for organizing settings
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.spells_tab = QWidget()
        self.settings_tab = QWidget()
        
        self.setup_spells_tab(self.spells_tab)
        self.setup_settings_tab(self.settings_tab)
        
        # Add tabs to widget
        self.tab_widget.addTab(self.spells_tab, "Spells and Keybinds")
        self.tab_widget.addTab(self.settings_tab, "Detection Settings")
        
        # Add both sides to splitter
        self.splitter.addWidget(self.exp_class_manager)
        self.splitter.addWidget(self.tab_widget)
        
        # Set initial sizes (40% for manager, 60% for settings)
        self.splitter.setSizes([400, 600])
        
        main_layout.addWidget(self.splitter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_configuration)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
    def setup_spells_tab(self, tab):
        """Set up the spells and keybinds tab"""
        layout = QHBoxLayout(tab)
        
        # Left side - Spell list and controls
        spell_group = QGroupBox("Spell Templates")
        spell_layout = QVBoxLayout()
        
        # Spell list
        self.spell_list = QListWidget()
        self.spell_list.setIconSize(QSize(48, 48))
        self.spell_list.currentItemChanged.connect(self.on_spell_selected)
        spell_layout.addWidget(self.spell_list)
        
        # Name edit control
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Spell Name:"))
        self.spell_name_edit = QLineEdit()
        self.spell_name_edit.setEnabled(False)  # Disabled until a spell is selected
        self.spell_name_edit.editingFinished.connect(self.on_spell_name_changed)
        name_layout.addWidget(self.spell_name_edit)
        spell_layout.addLayout(name_layout)
        
        # Spell controls
        spell_buttons = QHBoxLayout()
        
        self.add_spell_button = QPushButton("Add")
        self.add_spell_button.clicked.connect(self.add_spell)
        spell_buttons.addWidget(self.add_spell_button)
        
        self.update_template_button = QPushButton("Update Template")
        self.update_template_button.clicked.connect(self.update_spell_template)
        self.update_template_button.setEnabled(False)  # Disabled until a spell is selected
        spell_buttons.addWidget(self.update_template_button)
        
        self.remove_spell_button = QPushButton("Remove")
        self.remove_spell_button.clicked.connect(self.remove_spell)
        self.remove_spell_button.setEnabled(False)  # Disabled until a spell is selected
        spell_buttons.addWidget(self.remove_spell_button)
        
        self.wizard_button = QPushButton("Setup Wizard")
        self.wizard_button.clicked.connect(self.launch_setup_wizard)
        spell_buttons.addWidget(self.wizard_button)
        
        spell_layout.addLayout(spell_buttons)
        spell_group.setLayout(spell_layout)
        
        # Right side - Keybind configuration
        keybind_group = QGroupBox("Keybinds")
        keybind_layout = QVBoxLayout()
        
        # Keybind list
        self.keybind_layout = QFormLayout()
        keybind_layout.addLayout(self.keybind_layout)
        
        # Add stretch to keep the form at the top
        keybind_layout.addStretch()
        
        keybind_group.setLayout(keybind_layout)
        
        # Add both groups to the main layout
        layout.addWidget(spell_group)
        layout.addWidget(keybind_group)
        
        # Initialize
        self.populate_spell_list()
        self.populate_keybind_list()

    def update_spell_template(self):
        """Update the template for an existing spell by drawing a selection box"""
        import time
        
        current_item = self.spell_list.currentItem()
        if not current_item:
            return
            
        spell_name = current_item.data(Qt.UserRole)
        if not spell_name:
            return
            
        # Minimize dialog 
        self.hide()
        
        # Show instructions
        msg = QMessageBox()
        msg.setWindowTitle("Capture Spell Icon")
        msg.setText("A screen capture window will open.\n\n"
                    "Click and drag to select the spell icon region, then press Enter.\n"
                    "Press Escape to cancel.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        # Small delay to allow the dialog to close
        time.sleep(0.5)
        
        from screen_capture import ScreenCapture
        import cv2
        
        screen_capture = ScreenCapture()
        
        try:
            # Capture full screen
            screenshot = screen_capture.capture_full_screen()
            if screenshot is None:
                QMessageBox.warning(
                    self,
                    "Capture Failed",
                    "Failed to capture screen. Please try again."
                )
                self.show()
                return
                
            # Create window to display the screenshot
            window_name = "Select Spell Icon (Click and drag to select, then press Enter)"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            
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
            
            # Process selection if completed
            if selection['complete']:
                x, y, w, h = selection['x'], selection['y'], selection['w'], selection['h']
                
                # Ensure positive width and height
                if w < 0:
                    x += w
                    w = -w
                if h < 0:
                    y += h
                    h = -h
                
                # Extract the selected region as a template
                if x >= 0 and y >= 0 and w > 0 and h > 0:
                    template = screenshot[y:y+h, x:x+w].copy()
                    
                    # Resize template to standard size
                    template = cv2.resize(template, (64, 64))
                    
                    # Update the template
                    class_config = self.get_current_class_config()
                    if 'icon_templates' not in class_config:
                        class_config['icon_templates'] = {}
                        
                    class_config['icon_templates'][spell_name] = template
                    
                    # Save back to config
                    self.save_current_class_config(class_config)
                    
                    # Update UI
                    self.populate_spell_list()
                    
                    # Notify user
                    QMessageBox.information(
                        self,
                        "Success", 
                        f"Updated template for spell '{spell_name}'"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid Selection", 
                        "The selected area is invalid. Please try again."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Cancelled", 
                    "Template capture was cancelled."
                )
        
        finally:
            # Show dialog again
            self.show()
            self.activateWindow()
    
    def on_spell_name_changed(self):
        """Handle spell name changes"""
        new_name = self.spell_name_edit.text().strip()
        if not new_name:
            return
            
        current_item = self.spell_list.currentItem()
        if not current_item:
            return
            
        old_name = current_item.data(Qt.UserRole)
        if old_name == new_name:
            return  # No change
            
        # Get current class config
        class_config = self.get_current_class_config()
        
        # Update templates and keybinds
        icon_templates = class_config.get('icon_templates', {})
        keybinds = class_config.get('keybinds', {})
        
        # Check if the new name already exists
        if new_name in icon_templates:
            QMessageBox.warning(
                self,
                "Name Already Exists",
                f"A spell with the name '{new_name}' already exists."
            )
            # Reset the name
            self.spell_name_edit.setText(old_name)
            return
            
        # Move template and keybind to new name
        if old_name in icon_templates:
            icon_templates[new_name] = icon_templates[old_name]
            del icon_templates[old_name]
            
        if old_name in keybinds:
            keybinds[new_name] = keybinds[old_name]
            del keybinds[old_name]
            
        # Save back to config
        self.save_current_class_config(class_config)
        
        # Update UI
        self.populate_spell_list()
        self.populate_keybind_list()
        
        # Select the renamed item
        for i in range(self.spell_list.count()):
            item = self.spell_list.item(i)
            if item.data(Qt.UserRole) == new_name:
                self.spell_list.setCurrentItem(item)
                break
                
        logger.info(f"Renamed spell from '{old_name}' to '{new_name}'")
        
    def setup_settings_tab(self, tab):
        """Set up the detection settings tab"""
        import time
        layout = QVBoxLayout(tab)
        
        # Scan area group
        scan_group = QGroupBox("Scan Area")
        scan_layout = QFormLayout()
        
        # Scan area settings
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 3000)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 3000)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 1000)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 1000)
        
        scan_layout.addRow("X Position:", self.x_spin)
        scan_layout.addRow("Y Position:", self.y_spin)
        scan_layout.addRow("Width:", self.width_spin)
        scan_layout.addRow("Height:", self.height_spin)
        
        # Add button to capture coordinates from the screen
        capture_area_button = QPushButton("Capture Scan Area")
        capture_area_button.clicked.connect(self.capture_scan_area)
        scan_layout.addRow(capture_area_button)
        
        # Manual coordinate entry
        coord_layout = QHBoxLayout()
        self.coord_input = QLineEdit()
        self.coord_input.setPlaceholderText("X: 1567 Y: 1023 W: 75 H: 74")
        
        set_coords_button = QPushButton("Set")
        set_coords_button.clicked.connect(self.set_coords_from_text)
        
        coord_layout.addWidget(self.coord_input)
        coord_layout.addWidget(set_coords_button)
        
        scan_layout.addRow("Manual Coordinates:", coord_layout)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # Detection settings group
        detection_group = QGroupBox("Detection Settings")
        detection_layout = QFormLayout()
        
        # Detection settings
        self.frequency_spin = QDoubleSpinBox()
        self.frequency_spin.setRange(0.01, 1.0)
        self.frequency_spin.setSingleStep(0.01)
        self.frequency_spin.setDecimals(2)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        self.confidence_spin.setDecimals(2)
        
        self.cooldown_spin = QDoubleSpinBox()
        self.cooldown_spin.setRange(0.0, 5.0)
        self.cooldown_spin.setSingleStep(0.1)
        self.cooldown_spin.setDecimals(2)
        
        detection_layout.addRow("Detection Frequency (seconds):", self.frequency_spin)
        detection_layout.addRow("Confidence Threshold:", self.confidence_spin)
        detection_layout.addRow("Spell Cooldown (seconds):", self.cooldown_spin)
        
        detection_group.setLayout(detection_layout)
        layout.addWidget(detection_group)
        
        # Add stretch to fill empty space
        layout.addStretch()
        
        # Initialize values from config
        self.load_settings_values()
        
    def load_settings_values(self):
        """Load settings values from the current class config"""
        class_config = self.get_current_class_config()
        
        # Scan area settings
        scan_area = class_config.get('scan_area')
        if scan_area:
            self.x_spin.setValue(scan_area[0])
            self.y_spin.setValue(scan_area[1])
            self.width_spin.setValue(scan_area[2])
            self.height_spin.setValue(scan_area[3])
            
            # Show current coordinates in the text field
            self.coord_input.setText(f"X: {scan_area[0]} Y: {scan_area[1]} W: {scan_area[2]} H: {scan_area[3]}")
        else:
            # Load from global config as fallback
            global_scan_area = self.config.get('scan_area', [0, 0, 100, 100])
            self.x_spin.setValue(global_scan_area[0])
            self.y_spin.setValue(global_scan_area[1])
            self.width_spin.setValue(global_scan_area[2])
            self.height_spin.setValue(global_scan_area[3])
            
            # Show current coordinates in the text field
            self.coord_input.setText(f"X: {global_scan_area[0]} Y: {global_scan_area[1]} W: {global_scan_area[2]} H: {global_scan_area[3]}")
        
        # Load detection settings from global config (these are shared across classes)
        self.frequency_spin.setValue(self.config.get('detection_frequency', 0.1))
        self.confidence_spin.setValue(self.config.get('confidence_threshold', 0.8))
        self.cooldown_spin.setValue(self.config.get('cooldown', 0.5))
    
    def capture_scan_area(self):
        """Capture scan area coordinates from the screen"""
        import time
        import cv2
        from screen_capture import ScreenCapture
        
        # Hide the dialog
        self.hide()
        
        # Show instructions
        msg = QMessageBox()
        msg.setWindowTitle("Capture Scan Area")
        msg.setText("A screen capture window will open.\n\n"
                    "Click and drag to select the area to scan for spell icons, then press Enter.\n"
                    "Press Escape to cancel.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        # Small delay to allow the dialog to close
        time.sleep(0.5)
        
        screen_capture = ScreenCapture()
        
        try:
            # Capture full screen
            screenshot = screen_capture.capture_full_screen()
            if screenshot is None:
                QMessageBox.warning(
                    self,
                    "Capture Failed",
                    "Failed to capture screen. Please try again."
                )
                self.show()
                return
                
            # Create window to display the screenshot
            window_name = "Select Scan Area (Click and drag to select, then press Enter)"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            
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
                    
                    # Show coordinates
                    text = f"X: {x} Y: {y} W: {w} H: {h}"
                    cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
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
            
            # Process selection if completed
            if selection['complete']:
                x, y, w, h = selection['x'], selection['y'], selection['w'], selection['h']
                
                # Ensure positive width and height
                if w < 0:
                    x += w
                    w = -w
                if h < 0:
                    y += h
                    h = -h
                
                # Update the spin boxes
                if x >= 0 and y >= 0 and w > 0 and h > 0:
                    self.x_spin.setValue(x)
                    self.y_spin.setValue(y)
                    self.width_spin.setValue(w)
                    self.height_spin.setValue(h)
                    
                    # Update the coordinate input field
                    self.coord_input.setText(f"X: {x} Y: {y} W: {w} H: {h}")
                    
                    # Update class config
                    class_config = self.get_current_class_config()
                    class_config['scan_area'] = [x, y, w, h]
                    self.save_current_class_config(class_config)
                    
                    # Notify user
                    QMessageBox.information(
                        self,
                        "Success", 
                        f"Scan area coordinates set to X: {x}, Y: {y}, W: {w}, H: {h}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid Selection", 
                        "The selected area is invalid. Please try again."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Cancelled", 
                    "Scan area capture was cancelled."
                )
        
        finally:
            # Show dialog again
            self.show()
            self.activateWindow()
    
    def set_coords_from_text(self):
        """Set scan area coordinates from text input"""
        coords_text = self.coord_input.text().strip()
        
        # Try to parse the coordinates from the text
        try:
            # Extract X, Y, W, H values using a simple parsing approach
            import re
            
            # Look for patterns like "X: 1567 Y: 1023 W: 75 H: 74"
            x_match = re.search(r'X:\s*(\d+)', coords_text, re.IGNORECASE)
            y_match = re.search(r'Y:\s*(\d+)', coords_text, re.IGNORECASE)
            w_match = re.search(r'W:\s*(\d+)', coords_text, re.IGNORECASE)
            h_match = re.search(r'H:\s*(\d+)', coords_text, re.IGNORECASE)
            
            if not all([x_match, y_match, w_match, h_match]):
                raise ValueError("Could not find all required coordinates")
                
            x = int(x_match.group(1))
            y = int(y_match.group(1))
            w = int(w_match.group(1))
            h = int(h_match.group(1))
            
            # Update the spin boxes
            self.x_spin.setValue(x)
            self.y_spin.setValue(y)
            self.width_spin.setValue(w)
            self.height_spin.setValue(h)
            
            # Update class config
            class_config = self.get_current_class_config()
            class_config['scan_area'] = [x, y, w, h]
            self.save_current_class_config(class_config)
            
            # Notify user
            QMessageBox.information(
                self,
                "Success", 
                f"Scan area coordinates set to X: {x}, Y: {y}, W: {w}, H: {h}"
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Invalid Coordinates", 
                f"Failed to parse coordinates: {str(e)}\n\nExpected format: X: 1567 Y: 1023 W: 75 H: 74"
            )
            
    def populate_spell_list(self):
        """Populate the spell list with the configured templates"""
        self.spell_list.clear()
        
        # Get current class config
        class_config = self.get_current_class_config()
        icon_templates = class_config.get('icon_templates', {})
        
        for name, template in icon_templates.items():
            # Convert template to QIcon for display
            h, w = template.shape[:2]
            
            # Convert BGR to RGB
            rgb_img = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            
            # Create QImage and QPixmap
            qimg = QImage(rgb_img.data, w, h, 3 * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            # Create list item
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            item.setIcon(QIcon(pixmap))
            
            self.spell_list.addItem(item)
            
    def populate_keybind_list(self):
        """Populate the keybind list with the current keybinds"""
        # Clear existing widgets
        while self.keybind_layout.rowCount() > 0:
            self.keybind_layout.removeRow(0)
        
        # Get current class config
        class_config = self.get_current_class_config()
        keybinds = class_config.get('keybinds', {})
        
        # Add keybind fields
        for spell_name, key in keybinds.items():
            line_edit = QLineEdit(key)
            line_edit.setProperty('spell_name', spell_name)
            line_edit.textChanged.connect(lambda text, name=spell_name: self.update_keybind(name, text))
            
            self.keybind_layout.addRow(f"{spell_name}:", line_edit)

    def update_keybind(self, name, key):
        """Update a keybind for a spell"""
        if not name:
            return
            
        # Get current class config
        class_config = self.get_current_class_config()
        keybinds = class_config.get('keybinds', {})
        
        # Update the keybind
        keybinds[name] = key
        
        # Save back to config
        self.save_current_class_config(class_config)
        
        # Log update
        logger.info(f"Updated keybind for {name}: {key}")
            
    def on_spell_selected(self, current, previous):
        """Handle spell selection"""
        self.remove_spell_button.setEnabled(current is not None)
        
        if not current:
            self.spell_name_edit.setEnabled(False)
            self.spell_name_edit.setText("")
            self.update_template_button.setEnabled(False)
            return
        
        # Get spell name
        spell_name = current.data(Qt.UserRole)
        
        # Update the name edit
        self.spell_name_edit.setEnabled(True)
        self.spell_name_edit.setText(spell_name)
        
        # Enable the update template button
        self.update_template_button.setEnabled(True)
        
    def add_spell(self):
        """Add a new spell template"""
        import os
        import tkinter as tk
        from tkinter import simpledialog, messagebox
        import numpy as np
        import cv2
        
        # Create a simple dialog to get spell name and key
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Ask for the spell name
        spell_name = simpledialog.askstring("Add Spell", "Enter the spell name:")
        if not spell_name:
            root.destroy()
            return
            
        # Ask for the key to press
        key = simpledialog.askstring("Add Spell", f"Enter the key to press for {spell_name}:")
        if not key:
            root.destroy()
            return
        
        # Ask if the user wants to capture a template from the screen
        use_screen_capture = messagebox.askyesno(
            "Template Method",
            "Do you want to capture the spell icon from your screen?\n\n"
            "Yes: Capture from screen\n"
            "No: Create a colored square template"
        )
        
        if use_screen_capture:
            # Temporarily destroy the tkinter root to avoid conflicts with OpenCV
            root.destroy()
            
            # Minimize dialog 
            self.hide()
            
            # Now capture from screen
            from screen_capture import ScreenCapture
            
            screen_capture = ScreenCapture()
            
            # Create window for capture
            cv2.namedWindow("Capture Spell Icon")
            
            # Initialize capture variables
            template = None
            capturing = True
            
            def mouse_callback(event, x, y, flags, param):
                nonlocal template
                if capturing:
                    # Get screen capture
                    full_img = screen_capture.capture_full_screen()
                    if full_img is None:
                        return
                        
                    # Show a rectangle around the current position
                    img_copy = full_img.copy()
                    icon_size = 64  # Standard size for spell icons
                    
                    # Draw rectangle around the cursor position
                    start_point = (max(0, x - icon_size//2), max(0, y - icon_size//2))
                    end_point = (min(full_img.shape[1], x + icon_size//2), min(full_img.shape[0], y + icon_size//2))
                    cv2.rectangle(img_copy, start_point, end_point, (0, 255, 0), 2)
                    
                    # Add text instruction
                    cv2.putText(
                        img_copy,
                        "Position over spell icon and press Enter",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )
                    
                    # Show the image
                    cv2.imshow("Capture Spell Icon", img_copy)
                    
                    # If left button was clicked, save template
                    if event == cv2.EVENT_LBUTTONDOWN:
                        # Extract the region around the mouse as a template
                        x1, y1 = max(0, x - icon_size//2), max(0, y - icon_size//2)
                        x2, y2 = min(full_img.shape[1], x + icon_size//2), min(full_img.shape[0], y + icon_size//2)
                        
                        if x2 > x1 and y2 > y1:
                            template = full_img[y1:y2, x1:x2].copy()
                            
                            # Display the captured template
                            cv2.imshow("Captured Template", template)
            
            # Set up mouse callback
            cv2.setMouseCallback("Capture Spell Icon", mouse_callback)
            
            # Main capture loop
            while capturing:
                # Just wait for key press
                key_pressed = cv2.waitKey(100)
                
                # Enter key accepts the selection
                if key_pressed == 13 and template is not None:  # Enter key
                    capturing = False
                # Escape key cancels
                elif key_pressed == 27:  # Escape key
                    template = None
                    capturing = False
            
            # Clean up OpenCV windows
            cv2.destroyAllWindows()
            
            # Show dialog again
            self.show()
            
            # If no template was captured, create a default one
            if template is None:
                # Create a new tkinter root for messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo(
                    "Screen Capture Cancelled",
                    "Creating a default template instead."
                )
                # Fall through to default template creation
            else:
                # Resize template to standard size if needed
                if template.shape[0] != 64 or template.shape[1] != 64:
                    template = cv2.resize(template, (64, 64))
                    
                # Update current class config
                class_config = self.get_current_class_config()
                
                # Initialize icon_templates if needed
                if 'icon_templates' not in class_config:
                    class_config['icon_templates'] = {}
                
                # Initialize keybinds if needed  
                if 'keybinds' not in class_config:
                    class_config['keybinds'] = {}
                
                # Store the template and keybind
                class_config['icon_templates'][spell_name] = template
                class_config['keybinds'][spell_name] = key
                
                # Save back to config
                self.save_current_class_config(class_config)
                
                # Update UI
                self.populate_spell_list()
                self.populate_keybind_list()
                
                # Notify user
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Success", f"Added spell '{spell_name}' with key '{key}'")
                root.destroy()
                return
        
        # Default template creation (original code)
        # Create a simple template for this spell (64x64 colored square with text)
        import random
        template = np.zeros((64, 64, 3), dtype=np.uint8)
        
        # Generate a random color for this spell
        color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        
        # Fill with the color
        template[:, :] = color
        
        # Add text with the spell name
        cv2.putText(
            template,
            spell_name[:5],  # First 5 chars only to fit
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),  # Black text
            2
        )
        
        # Update current class config
        class_config = self.get_current_class_config()
        
        # Initialize icon_templates if needed
        if 'icon_templates' not in class_config:
            class_config['icon_templates'] = {}
        
        # Initialize keybinds if needed  
        if 'keybinds' not in class_config:
            class_config['keybinds'] = {}
        
        # Store the template and keybind
        class_config['icon_templates'][spell_name] = template
        class_config['keybinds'][spell_name] = key
        
        # Save back to config
        self.save_current_class_config(class_config)
        
        # Update UI
        self.populate_spell_list()
        self.populate_keybind_list()
        
        # Notify user
        if 'root' not in locals() or root is None or not root.winfo_exists():
            root = tk.Tk()
            root.withdraw()
        messagebox.showinfo("Success", f"Added spell '{spell_name}' with key '{key}'")
        root.destroy()
        
    def remove_spell(self):
        """Remove the selected spell"""
        current_item = self.spell_list.currentItem()
        if not current_item:
            return
            
        spell_name = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Remove Spell",
            f"Are you sure you want to remove the spell '{spell_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get current class config
            class_config = self.get_current_class_config()
            
            # Remove from templates
            icon_templates = class_config.get('icon_templates', {})
            if spell_name in icon_templates:
                del icon_templates[spell_name]
                
            # Remove from keybinds
            keybinds = class_config.get('keybinds', {})
            if spell_name in keybinds:
                del keybinds[spell_name]
                
            # Save back to config
            self.save_current_class_config(class_config)
            
            # Update UI
            self.populate_spell_list()
            self.populate_keybind_list()
            
    def launch_setup_wizard(self):
        """Launch the setup wizard"""
        from ui.setup_wizard import SetupWizard
        from screen_capture import ScreenCapture
        
        # Close this dialog temporarily
        self.hide()
        
        wizard = SetupWizard(self.config_manager, ScreenCapture(), self.parent())
        if wizard.exec_():
            # Reload config
            self.config = self.config_manager.load_config()
            
            # Update UI
            self.populate_spell_list()
            self.populate_keybind_list()
            self.load_settings_values()
            
        # Show this dialog again
        self.show()
        
    def get_current_class_config(self):
        """Get the configuration for the current expansion and class"""
        # Get selected expansion and class
        current_exp_id, current_class_id = self.exp_class_manager.get_current_selection()
        
        if not current_exp_id or not current_class_id:
            # No selection, return empty config
            return {}
            
        # Get config for this expansion and class
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            return {}
            
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        if current_class_id not in classes:
            return {}
            
        class_config = classes[current_class_id]
        if not isinstance(class_config, dict):
            # Initialize with empty dict if not a dict
            classes[current_class_id] = {}
            class_config = classes[current_class_id]
            
        return class_config
        
    def save_current_class_config(self, class_config):
        """Save the current class configuration"""
        # Get selected expansion and class
        current_exp_id, current_class_id = self.exp_class_manager.get_current_selection()
        
        if not current_exp_id or not current_class_id:
            # No selection, can't save
            return False
            
        # Get config for this expansion and class
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            return False
            
        exp_data = expansions[current_exp_id]
        
        if 'classes' not in exp_data:
            exp_data['classes'] = {}
            
        # Update class config
        exp_data['classes'][current_class_id] = class_config
        
        # Save full config
        return self.config_manager.save_config(self.config)
        
    def save_configuration(self):
        """Save the configuration changes"""
        # Update scan area for current class
        class_config = self.get_current_class_config()
        
        # Update scan area
        scan_area = [
            self.x_spin.value(),
            self.y_spin.value(),
            self.width_spin.value(),
            self.height_spin.value()
        ]
        class_config['scan_area'] = scan_area
        
        # Save class config
        self.save_current_class_config(class_config)
        
        # Update global settings
        self.config['detection_frequency'] = self.frequency_spin.value()
        self.config['confidence_threshold'] = self.confidence_spin.value()
        self.config['cooldown'] = self.cooldown_spin.value()
        
        # Save global configuration
        if self.config_manager.save_config(self.config):
            # Accept dialog
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
            
    def on_config_changed(self):
        """Handle configuration changes from the expansion/class manager"""
        # Reload config
        self.config = self.config_manager.load_config()
        
        # Update UI
        self.populate_spell_list()
        self.populate_keybind_list()
        self.load_settings_values()
                