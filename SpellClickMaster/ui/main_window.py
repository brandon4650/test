"""
Main Window UI Module
Implements the primary application window
"""
import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QCheckBox,
    QSlider, QComboBox, QStatusBar, QAction, QMenu,
    QSystemTrayIcon, QMessageBox, QShortcut
)
from PyQt5.QtCore import Qt, QSettings, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QKeySequence

from spell_detector import SpellDetector
from screen_capture import ScreenCapture
from ui.setup_wizard import SetupWizard
from ui.configuration_dialog import ConfigurationDialog

logger = logging.getLogger('ui.main_window')

class MainWindow(QMainWindow):
    """Main application window class"""
    
    def __init__(self, config_manager, first_run=False):
        """Initialize the main window"""
        super().__init__()
        
        self.config_manager = config_manager
        self.screen_capture = ScreenCapture()
        self.spell_detector = SpellDetector(config_manager)
        
        # Connect signals
        self.spell_detector.status_updated.connect(self.update_status)
        self.spell_detector.icon_detected.connect(self.on_icon_detected)
        
        # Set up UI
        self.setWindowTitle("Spell Caster")
        self.setMinimumSize(400, 300)
        self.setup_ui()
        
        # Load settings
        self.load_window_settings()
        
        # Set up system tray
        self.setup_system_tray()
        
        # Global hotkeys
        self.setup_hotkeys()
        
        # Show setup wizard on first run
        if first_run:
            QTimer.singleShot(100, self.show_setup_wizard)
            
    def setup_ui(self):
        """Set up the user interface"""
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Status Group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.detected_icon_label = QLabel("No spell detected")
        self.detected_icon_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.detected_icon_label)
        
        main_layout.addWidget(status_group)
        
        # Controls Group
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.start_button = QPushButton("Start Casting")
        self.start_button.clicked.connect(self.start_detection)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_detection)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        main_layout.addWidget(controls_group)
        
        # Settings Group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Detection frequency slider
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Detection Speed:"))
        self.frequency_slider = QSlider(Qt.Horizontal)
        self.frequency_slider.setMinimum(1)
        self.frequency_slider.setMaximum(20)
        self.frequency_slider.setValue(10)
        self.frequency_slider.setTickPosition(QSlider.TicksBelow)
        self.frequency_slider.setTickInterval(1)
        self.frequency_slider.valueChanged.connect(self.update_detection_frequency)
        freq_layout.addWidget(self.frequency_slider)
        self.freq_value_label = QLabel("100ms")
        freq_layout.addWidget(self.freq_value_label)
        settings_layout.addLayout(freq_layout)
        
        # Confidence threshold slider
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Match Confidence:"))
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(50)
        self.confidence_slider.setMaximum(95)
        self.confidence_slider.setValue(80)
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.setTickInterval(5)
        self.confidence_slider.valueChanged.connect(self.update_confidence_threshold)
        conf_layout.addWidget(self.confidence_slider)
        self.conf_value_label = QLabel("80%")
        conf_layout.addWidget(self.conf_value_label)
        settings_layout.addLayout(conf_layout)
        
        # Auto-start checkbox
        self.autostart_checkbox = QCheckBox("Start on application launch")
        config = self.config_manager.load_config()
        self.autostart_checkbox.setChecked(config.get('autostart', False))
        self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
        settings_layout.addWidget(self.autostart_checkbox)
        
        # Minimize to tray checkbox
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_checkbox.setChecked(config.get('minimize_to_tray', True))
        self.minimize_to_tray_checkbox.stateChanged.connect(self.toggle_minimize_to_tray)
        settings_layout.addWidget(self.minimize_to_tray_checkbox)
        
        main_layout.addWidget(settings_group)
        
        # Configuration buttons
        config_layout = QHBoxLayout()
        
        self.setup_button = QPushButton("Setup Wizard")
        self.setup_button.clicked.connect(self.show_setup_wizard)
        config_layout.addWidget(self.setup_button)
        
        self.config_button = QPushButton("Configure Spells")
        self.config_button.clicked.connect(self.show_configuration_dialog)
        config_layout.addWidget(self.config_button)
        
        main_layout.addLayout(config_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create menus
        self.create_menus()
        
        # Apply initial settings
        config = self.config_manager.load_config()
        self.frequency_slider.setValue(int(1/config.get('detection_frequency', 0.1) * 10))
        self.confidence_slider.setValue(int(config.get('confidence_threshold', 0.8) * 100))
        self.update_detection_frequency(self.frequency_slider.value())
        self.update_confidence_threshold(self.confidence_slider.value())
        
        # Auto-start if configured
        if config.get('autostart', False):
            QTimer.singleShot(1000, self.start_detection)
        
    def create_menus(self):
        """Create application menu bars"""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        start_action = QAction("&Start Casting", self)
        start_action.setShortcut("Ctrl+S")
        start_action.triggered.connect(self.start_detection)
        file_menu.addAction(start_action)
        
        stop_action = QAction("S&top Casting", self)
        stop_action.setShortcut("Ctrl+T")
        stop_action.triggered.connect(self.stop_detection)
        file_menu.addAction(stop_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = self.menuBar().addMenu("&Settings")
        
        config_action = QAction("&Configure Spells", self)
        config_action.triggered.connect(self.show_configuration_dialog)
        settings_menu.addAction(config_action)
        
        wizard_action = QAction("Setup &Wizard", self)
        wizard_action.triggered.connect(self.show_setup_wizard)
        settings_menu.addAction(wizard_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def setup_system_tray(self):
        """Set up system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(QIcon("assets/app_icon.svg"), self)
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        toggle_action = QAction("Start Casting", self)
        toggle_action.triggered.connect(self.toggle_detection)
        self.tray_toggle_action = toggle_action
        tray_menu.addAction(toggle_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
    def setup_hotkeys(self):
        """Set up global keyboard shortcuts"""
        # Start/stop shortcut (F10)
        self.toggle_shortcut = QShortcut(QKeySequence("F10"), self)
        self.toggle_shortcut.activated.connect(self.toggle_detection)
        
        # Show/hide shortcut (F11)
        self.visibility_shortcut = QShortcut(QKeySequence("F11"), self)
        self.visibility_shortcut.activated.connect(self.toggle_visibility)
        
    def load_window_settings(self):
        """Load window position and size settings"""
        settings = QSettings("SpellCaster", "SpellCaster")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Center the window on the screen by default
            screen_geometry = self.screen().availableGeometry()
            self.move(
                (screen_geometry.width() - self.width()) // 2,
                (screen_geometry.height() - self.height()) // 2
            )
            
    def save_window_settings(self):
        """Save window position and size settings"""
        settings = QSettings("SpellCaster", "SpellCaster")
        settings.setValue("geometry", self.saveGeometry())
        
    @pyqtSlot()
    def start_detection(self):
        """Start the spell detection process"""
        if self.spell_detector.start():
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.setup_button.setEnabled(False)
            self.config_button.setEnabled(False)
            
            # Update tray icon menu
            self.tray_toggle_action.setText("Stop Casting")
            
            self.status_bar.showMessage("Spell detection active")
            
    @pyqtSlot()
    def stop_detection(self):
        """Stop the spell detection process"""
        self.spell_detector.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.setup_button.setEnabled(True)
        self.config_button.setEnabled(True)
        
        # Update tray icon menu
        self.tray_toggle_action.setText("Start Casting")
        
        self.status_bar.showMessage("Spell detection stopped")
        
    @pyqtSlot()
    def toggle_detection(self):
        """Toggle the spell detection on/off"""
        if self.spell_detector.running:
            self.stop_detection()
        else:
            self.start_detection()
            
    @pyqtSlot()
    def toggle_visibility(self):
        """Toggle the visibility of the application window"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            
    @pyqtSlot(str)
    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        self.status_bar.showMessage(status)
        
    @pyqtSlot(str, float)
    def on_icon_detected(self, icon_name, confidence):
        """Handle icon detection event"""
        self.detected_icon_label.setText(f"Detected: {icon_name} ({confidence:.2f})")
        
    @pyqtSlot(int)
    def update_detection_frequency(self, value):
        """Update detection frequency based on slider value"""
        # Convert slider value to detection frequency (in seconds)
        # 1-20 scale maps to 500ms-50ms (0.5s-0.05s)
        frequency = 0.5 - (value - 1) * (0.45 / 19)
        
        # Update config
        config = self.config_manager.load_config()
        config['detection_frequency'] = frequency
        self.config_manager.save_config(config)
        
        # Update spell detector
        self.spell_detector.update_config()
        
        # Update label
        self.freq_value_label.setText(f"{int(frequency * 1000)}ms")
        
    @pyqtSlot(int)
    def update_confidence_threshold(self, value):
        """Update confidence threshold based on slider value"""
        # Convert slider value to confidence threshold (0.5-0.95)
        threshold = value / 100
        
        # Update config
        config = self.config_manager.load_config()
        config['confidence_threshold'] = threshold
        self.config_manager.save_config(config)
        
        # Update spell detector
        self.spell_detector.update_config()
        
        # Update label
        self.conf_value_label.setText(f"{value}%")
        
    @pyqtSlot(int)
    def toggle_autostart(self, state):
        """Toggle auto-start setting"""
        config = self.config_manager.load_config()
        config['autostart'] = state == Qt.Checked
        self.config_manager.save_config(config)
        
    @pyqtSlot(int)
    def toggle_minimize_to_tray(self, state):
        """Toggle minimize to tray setting"""
        config = self.config_manager.load_config()
        config['minimize_to_tray'] = state == Qt.Checked
        self.config_manager.save_config(config)
        
    def show_setup_wizard(self):
        """Show the setup wizard dialog"""
        wizard = SetupWizard(self.config_manager, self.screen_capture, parent=self)
        if wizard.exec_():
            # Reload configuration after wizard completes
            self.spell_detector.update_config()
            
    def show_configuration_dialog(self):
        """Show the spell configuration dialog"""
        dialog = ConfigurationDialog(self.config_manager, parent=self)
        if dialog.exec_():
            # Reload configuration after dialog completes
            self.spell_detector.update_config()
            
    def show_about_dialog(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About Spell Caster",
            "<h2>Spell Caster</h2>"
            "<p>Version 1.0</p>"
            "<p>An application to automate spell casting in games by detecting on-screen spell icons.</p>"
            "<p>© 2023 Spell Caster Project</p>"
        )
        
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:  # Left click
            self.toggle_visibility()
            
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_window_settings()
        
        config = self.config_manager.load_config()
        if config.get('minimize_to_tray', True) and not self.spell_detector.running:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Spell Caster",
                "Application minimized to system tray. Click the icon to restore.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            if self.spell_detector.running:
                reply = QMessageBox.question(
                    self,
                    "Exit Confirmation",
                    "Spell detection is currently running. Are you sure you want to exit?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                    
                # Stop detection before exiting
                self.spell_detector.stop()
                
            self.close_application()
            
    def close_application(self):
        """Close the application properly"""
        # Stop detection if running
        if self.spell_detector.running:
            self.spell_detector.stop()
            
        # Save settings
        self.save_window_settings()
        
        # Hide tray icon
        self.tray_icon.hide()
        
        # Quit application
        QApplication.quit()
