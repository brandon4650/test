"""
Configuration Dialog UI Module
Implements a dialog for configuring spell icons and keybinds
"""
import logging
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QFormLayout, QDoubleSpinBox, QMessageBox,
    QLineEdit, QWidget
)
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon
logger = logging.getLogger('ui.configuration_dialog')
class ConfigurationDialog(QDialog):
    """Dialog for configuring spell icons and keybinds"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        
        self.setWindowTitle("Spell Caster Configuration")
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        main_layout = QVBoxLayout()
        
        # Tab widget for organizing settings
        self.tab_widget = QTabWidget()
        
        # Create tabs
        spells_tab = QWidget()
        settings_tab = QWidget()
        
        self.setup_spells_tab(spells_tab)
        self.setup_settings_tab(settings_tab)
        
        # Add tabs to widget
        self.tab_widget.addTab(spells_tab, "Spells and Keybinds")
        self.tab_widget.addTab(settings_tab, "Detection Settings")
        
        main_layout.addWidget(self.tab_widget)
        
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
        
        self.setLayout(main_layout)
        
    def setup_spells_tab(self, tab):
        """Set up the spells and keybinds tab"""
        layout = QHBoxLayout()
        
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
        
        self.remove_spell_button = QPushButton("Remove")
        self.remove_spell_button.clicked.connect(self.remove_spell)
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
        
        tab.setLayout(layout)
        
        # Initialize
        self.populate_spell_list()
        self.populate_keybind_list()

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
            
        # Update templates and keybinds
        icon_templates = self.config.get('icon_templates', {})
        keybinds = self.config.get('keybinds', {})
        
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
            
        # Update config
        self.config['icon_templates'] = icon_templates
        self.config['keybinds'] = keybinds
        
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
        layout = QVBoxLayout()
        
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
        
        tab.setLayout(layout)
        
        # Initialize values from config
        scan_area = self.config.get('scan_area', (0, 0, 100, 100))
        self.x_spin.setValue(scan_area[0])
        self.y_spin.setValue(scan_area[1])
        self.width_spin.setValue(scan_area[2])
        self.height_spin.setValue(scan_area[3])
        
        self.frequency_spin.setValue(self.config.get('detection_frequency', 0.1))
        self.confidence_spin.setValue(self.config.get('confidence_threshold', 0.8))
        self.cooldown_spin.setValue(self.config.get('cooldown', 0.5))
        
    def populate_spell_list(self):
        """Populate the spell list with the configured templates"""
        self.spell_list.clear()
        
        icon_templates = self.config.get('icon_templates', {})
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
        
        # Add keybind fields
        keybinds = self.config.get('keybinds', {})
        for spell_name, key in keybinds.items():
            line_edit = QLineEdit(key)
            line_edit.setProperty('spell_name', spell_name)
            line_edit.textChanged.connect(lambda text, name=spell_name: self.update_keybind(name, text))
            
            self.keybind_layout.addRow(f"{spell_name}:", line_edit)

    def update_keybind(self, name, key):
        """Update a keybind for a spell"""
        if not name:
            return
            
        # Update the keybind in the config (but don't save yet)
        keybinds = self.config.get('keybinds', {})
        keybinds[name] = key
        self.config['keybinds'] = keybinds
        
        # Log update
        logger.info(f"Updated keybind for {name}: {key}")
            
    def on_spell_selected(self, current, previous):
        """Handle spell selection"""
        if not current:
            self.spell_name_edit.setEnabled(False)
            self.spell_name_edit.setText("")
            return
        
        # Get spell name
        spell_name = current.data(Qt.UserRole)
        
        # Update the name edit
        self.spell_name_edit.setEnabled(True)
        self.spell_name_edit.setText(spell_name)
        
        # TODO: Preview the selected spell template
        
    def on_keybind_changed(self, text):
        """Handle keybind changes"""
        sender = self.sender()
        spell_name = sender.property('spell_name')
        
        if not spell_name:
            return
            
        # Update the keybind in the config (but don't save yet)
        keybinds = self.config.get('keybinds', {})
        keybinds[spell_name] = text
        self.config['keybinds'] = keybinds
        
        # Update the keybind list
        self.populate_keybind_list()
        
    def add_spell(self):
        """Add a new spell template"""
        import os
        import tkinter as tk
        from tkinter import simpledialog, messagebox
        
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
        
        # Store the template
        icon_templates = self.config.get('icon_templates', {})
        icon_templates[spell_name] = template
        
        # Store the keybind
        keybinds = self.config.get('keybinds', {})
        keybinds[spell_name] = key
        
        # Update config
        self.config['icon_templates'] = icon_templates
        self.config['keybinds'] = keybinds
        
        # Update UI
        self.populate_spell_list()
        self.populate_keybind_list()
        
        # Notify user
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
            # Remove from templates
            icon_templates = self.config.get('icon_templates', {})
            if spell_name in icon_templates:
                del icon_templates[spell_name]
                
            # Remove from keybinds
            keybinds = self.config.get('keybinds', {})
            if spell_name in keybinds:
                del keybinds[spell_name]
                
            # Update config (but don't save yet)
            self.config['icon_templates'] = icon_templates
            self.config['keybinds'] = keybinds
            
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
            
            # Update settings
            scan_area = self.config.get('scan_area', (0, 0, 100, 100))
            self.x_spin.setValue(scan_area[0])
            self.y_spin.setValue(scan_area[1])
            self.width_spin.setValue(scan_area[2])
            self.height_spin.setValue(scan_area[3])
            
            self.frequency_spin.setValue(self.config.get('detection_frequency', 0.1))
            self.confidence_spin.setValue(self.config.get('confidence_threshold', 0.8))
            self.cooldown_spin.setValue(self.config.get('cooldown', 0.5))
            
        # Show this dialog again
        self.show()
        
    def save_configuration(self):
        """Save the configuration changes"""
        # Update scan area
        scan_area = (
            self.x_spin.value(),
            self.y_spin.value(),
            self.width_spin.value(),
            self.height_spin.value()
        )
        self.config['scan_area'] = scan_area
        
        # Update detection settings
        self.config['detection_frequency'] = self.frequency_spin.value()
        self.config['confidence_threshold'] = self.confidence_spin.value()
        self.config['cooldown'] = self.cooldown_spin.value()
        
        # Save configuration
        self.config_manager.save_config(self.config)
        
        # Accept dialog
        self.accept()