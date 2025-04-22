"""
Game-Specific Setup Page
Handles game-specific configuration for the Spell Caster application
"""
import cv2
import numpy as np
import logging
from PyQt5.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

logger = logging.getLogger('ui.game_specific_page')

class GameSpecificPage(QWizardPage):
    """Page with game-specific configuration options"""
    
    def __init__(self, config_manager):
        super().__init__()
        
        self.config_manager = config_manager
        
        self.setTitle("Game-Specific Settings")
        self.setSubTitle("Configure settings specific to your game")
        
        layout = QVBoxLayout()
        
        # Game instructions
        instructions = QLabel(
            "<p>Based on the provided image, we've detected you're playing a game with spell icons "
            "that appear on the left side of your screen. The application will monitor this area "
            "and press the corresponding keybind when a spell icon is detected.</p>"
            "<p>The leftmost icon (N5 in the screenshot) is the one that needs to be cast first.</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Image reference
        image_group = QGroupBox("Reference Image")
        image_layout = QVBoxLayout()
        
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(image_label)
        
        # Create a reference image showing the three spell icons with the leftmost one highlighted
        reference_img = np.zeros((100, 300, 3), dtype=np.uint8)
        reference_img[:, :] = (50, 50, 50)  # Dark gray background
        
        # Left icon (highlighted)
        cv2.rectangle(reference_img, (20, 20), (80, 80), (0, 0, 255), 2)  # Red border
        cv2.putText(reference_img, "N5", (40, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Middle icon
        cv2.rectangle(reference_img, (120, 20), (180, 80), (255, 255, 255), 1)  # White border
        cv2.putText(reference_img, "C1", (140, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Right icon
        cv2.rectangle(reference_img, (220, 20), (280, 80), (255, 255, 255), 1)  # White border
        cv2.putText(reference_img, "N1", (240, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Convert to QImage and display
        h, w, ch = reference_img.shape
        reference_img_rgb = cv2.cvtColor(reference_img, cv2.COLOR_BGR2RGB)
        qimg = QImage(reference_img_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        image_label.setPixmap(pixmap)
        
        # Add arrow pointing to the leftmost icon
        arrow_label = QLabel("← This icon will be detected and its keybind will be pressed")
        arrow_label.setStyleSheet("color: red; font-weight: bold;")
        image_layout.addWidget(arrow_label)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # Game-specific settings
        settings_group = QGroupBox("Game Settings")
        settings_layout = QVBoxLayout()
        
        # Game Type
        game_layout = QHBoxLayout()
        game_layout.addWidget(QLabel("Game Type:"))
        self.game_combo = QComboBox()
        self.game_combo.addItems(["World of Warcraft", "Final Fantasy XIV", "Other MMO", "Custom"])
        game_layout.addWidget(self.game_combo)
        settings_layout.addLayout(game_layout)
        
        # Game Resolution
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Game Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "2560x1440", "3840x2160", "Custom"])
        resolution_layout.addWidget(self.resolution_combo)
        settings_layout.addLayout(resolution_layout)
        
        # Key Press Duration
        key_duration_layout = QHBoxLayout()
        key_duration_layout.addWidget(QLabel("Key Press Duration (ms):"))
        self.key_duration_spin = QSpinBox()
        self.key_duration_spin.setRange(10, 500)
        self.key_duration_spin.setValue(100)
        self.key_duration_spin.setSingleStep(10)
        key_duration_layout.addWidget(self.key_duration_spin)
        settings_layout.addLayout(key_duration_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Load existing configuration if available
        config = self.config_manager.load_config()
        if 'game_type' in config:
            index = self.game_combo.findText(config['game_type'])
            if index >= 0:
                self.game_combo.setCurrentIndex(index)
                
        if 'game_resolution' in config:
            index = self.resolution_combo.findText(config['game_resolution'])
            if index >= 0:
                self.resolution_combo.setCurrentIndex(index)
                
        if 'key_press_duration' in config:
            self.key_duration_spin.setValue(int(config['key_press_duration'] * 1000))  # Convert to ms
    
    def validatePage(self):
        """Save game-specific settings before proceeding"""
        try:
            # Load config
            config = self.config_manager.load_config()
            
            # Save game settings
            config['game_type'] = self.game_combo.currentText()
            config['game_resolution'] = self.resolution_combo.currentText()
            config['key_press_duration'] = self.key_duration_spin.value() / 1000.0  # Convert to seconds
            
            # Save config
            self.config_manager.save_config(config)
            
            return True
        except Exception as e:
            logger.error(f"Error saving game settings: {str(e)}", exc_info=True)
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Failed to save game settings: {str(e)}"
            )
            return False