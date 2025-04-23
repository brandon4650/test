"""
Expansion and Class Manager UI Module
Implements UI components for managing multiple WoW expansions and classes
"""
import logging
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QPushButton, QGroupBox, QTabWidget, QMessageBox,
    QListWidget, QListWidgetItem, QDialog, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon

logger = logging.getLogger('ui.expansion_class_manager')

class ExpansionDialog(QDialog):
    """Dialog for adding or editing an expansion"""
    
    def __init__(self, parent=None, expansion_data=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add/Edit Expansion")
        self.setMinimumWidth(300)
        
        self.expansion_data = expansion_data or {}
        
        layout = QVBoxLayout(self)
        
        # Form for expansion details
        form_layout = QFormLayout()
        
        # Expansion ID field
        self.id_edit = QLineEdit()
        if 'id' in self.expansion_data:
            self.id_edit.setText(self.expansion_data['id'])
            self.id_edit.setEnabled(False)  # Don't allow editing existing ID
        form_layout.addRow("Expansion ID:", self.id_edit)
        
        # Expansion name field
        self.name_edit = QLineEdit()
        if 'name' in self.expansion_data:
            self.name_edit.setText(self.expansion_data['name'])
        form_layout.addRow("Expansion Name:", self.name_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def get_expansion_data(self):
        """Get the entered expansion data"""
        return {
            'id': self.id_edit.text().strip(),
            'name': self.name_edit.text().strip()
        }
        
    @classmethod
    def get_expansion(cls, parent=None, expansion_data=None):
        """Static method to create and show the dialog"""
        dialog = cls(parent, expansion_data)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return dialog.get_expansion_data()
        return None


class ClassDialog(QDialog):
    """Dialog for adding or editing a class"""
    
    def __init__(self, parent=None, class_data=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add/Edit Class")
        self.setMinimumWidth(300)
        
        self.class_data = class_data or {}
        
        layout = QVBoxLayout(self)
        
        # Form for class details
        form_layout = QFormLayout()
        
        # Class ID field
        self.id_edit = QLineEdit()
        if 'id' in self.class_data:
            self.id_edit.setText(self.class_data['id'])
            self.id_edit.setEnabled(False)  # Don't allow editing existing ID
        form_layout.addRow("Class ID:", self.id_edit)
        
        # Class name field
        self.name_edit = QLineEdit()
        if 'name' in self.class_data:
            self.name_edit.setText(self.class_data['name'])
        form_layout.addRow("Class Name:", self.name_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def get_class_data(self):
        """Get the entered class data"""
        return {
            'id': self.id_edit.text().strip(),
            'name': self.name_edit.text().strip()
        }
        
    @classmethod
    def get_class(cls, parent=None, class_data=None):
        """Static method to create and show the dialog"""
        dialog = cls(parent, class_data)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return dialog.get_class_data()
        return None


class ExpansionClassManager(QWidget):
    """Widget for managing expansions and classes in the SpellCaster application"""
    
    # Signal emitted when expansion or class changes
    config_changed = pyqtSignal()
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.config = self.config_manager.load_config()
        
        # Ensure expansions structure exists
        if 'expansions' not in self.config:
            self.config['expansions'] = {}
            
        # Ensure current selections exist
        if 'current_expansion' not in self.config:
            self.config['current_expansion'] = None
            
        if 'current_class' not in self.config:
            self.config['current_class'] = None
            
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout(self)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.setup_selector_tab()
        self.setup_expansion_tab()
        self.setup_class_tab()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.selector_tab, "Current Selection")
        self.tab_widget.addTab(self.expansion_tab, "Manage Expansions")
        
        # For class tab, get current expansion name if available
        current_exp_id = self.config.get('current_expansion')
        tab_title = "Manage Classes"
        
        if current_exp_id and current_exp_id in self.config.get('expansions', {}):
            exp_data = self.config['expansions'][current_exp_id]
            exp_name = exp_data.get('name', current_exp_id)
            tab_title = f"Manage Classes ({exp_name})"
            
        self.tab_widget.addTab(self.class_tab, tab_title)
        
        layout.addWidget(self.tab_widget)
        
    def setup_selector_tab(self):
        """Set up the expansion/class selector tab"""
        self.selector_tab = QWidget()
        layout = QVBoxLayout(self.selector_tab)
        
        # Group box for selection
        group_box = QGroupBox("Current Configuration")
        group_layout = QVBoxLayout()
        
        # Expansion selector
        exp_layout = QHBoxLayout()
        exp_layout.addWidget(QLabel("Expansion:"))
        
        self.expansion_combo = QComboBox()
        self.expansion_combo.currentIndexChanged.connect(self.on_expansion_changed)
        exp_layout.addWidget(self.expansion_combo)
        
        group_layout.addLayout(exp_layout)
        
        # Class selector
        class_layout = QHBoxLayout()
        class_layout.addWidget(QLabel("Class:"))
        
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_class_changed)
        class_layout.addWidget(self.class_combo)
        
        group_layout.addLayout(class_layout)
        
        # Current settings info
        self.settings_label = QLabel("No configuration selected")
        group_layout.addWidget(self.settings_label)
        
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        
        # Apply button
        self.apply_button = QPushButton("Apply Selection")
        self.apply_button.clicked.connect(self.apply_selection)
        layout.addWidget(self.apply_button)
        
        # Populate selectors
        self.populate_expansion_combo()
        
    def setup_expansion_tab(self):
        """Set up the expansion management tab"""
        self.expansion_tab = QWidget()
        layout = QVBoxLayout(self.expansion_tab)
        
        # Expansion list
        self.expansion_list = QListWidget()
        self.expansion_list.currentItemChanged.connect(self.on_expansion_item_selected)
        layout.addWidget(self.expansion_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_expansion_button = QPushButton("Add Expansion")
        self.add_expansion_button.clicked.connect(self.add_expansion)
        button_layout.addWidget(self.add_expansion_button)
        
        self.edit_expansion_button = QPushButton("Edit Expansion")
        self.edit_expansion_button.clicked.connect(self.edit_expansion)
        self.edit_expansion_button.setEnabled(False)
        button_layout.addWidget(self.edit_expansion_button)
        
        self.remove_expansion_button = QPushButton("Remove Expansion")
        self.remove_expansion_button.clicked.connect(self.remove_expansion)
        self.remove_expansion_button.setEnabled(False)
        button_layout.addWidget(self.remove_expansion_button)
        
        layout.addLayout(button_layout)
        
        # Populate expansion list
        self.populate_expansion_list()
        
    def setup_class_tab(self):
        """Set up the class management tab"""
        self.class_tab = QWidget()
        layout = QVBoxLayout(self.class_tab)
        
        # Class list
        self.class_list = QListWidget()
        self.class_list.currentItemChanged.connect(self.on_class_item_selected)
        layout.addWidget(self.class_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_class_button = QPushButton("Add Class")
        self.add_class_button.clicked.connect(self.add_class)
        button_layout.addWidget(self.add_class_button)
        
        self.edit_class_button = QPushButton("Edit Class")
        self.edit_class_button.clicked.connect(self.edit_class)
        self.edit_class_button.setEnabled(False)
        button_layout.addWidget(self.edit_class_button)
        
        self.remove_class_button = QPushButton("Remove Class")
        self.remove_class_button.clicked.connect(self.remove_class)
        self.remove_class_button.setEnabled(False)
        button_layout.addWidget(self.remove_class_button)
        
        layout.addLayout(button_layout)
        
        # Populate class list
        self.populate_class_list()
        
    def populate_expansion_combo(self):
        """Populate the expansion combo box"""
        self.expansion_combo.blockSignals(True)
        self.expansion_combo.clear()
        
        expansions = self.config.get('expansions', {})
        
        # Add placeholder if no expansions
        if not expansions:
            self.expansion_combo.addItem("No expansions available")
            self.expansion_combo.setEnabled(False)
        else:
            self.expansion_combo.setEnabled(True)
            
            # Add items
            current_expansion = self.config.get('current_expansion')
            current_index = 0
            
            for i, (exp_id, exp_data) in enumerate(expansions.items()):
                exp_name = exp_data.get('name', exp_id)
                self.expansion_combo.addItem(exp_name, exp_id)
                
                if exp_id == current_expansion:
                    current_index = i
                    
            # Set current index
            if current_expansion and current_index < self.expansion_combo.count():
                self.expansion_combo.setCurrentIndex(current_index)
                
        self.expansion_combo.blockSignals(False)
        
        # Update class combo
        self.populate_class_combo()
        
    def populate_class_combo(self):
        """Populate the class combo box based on current expansion"""
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        
        current_exp_index = self.expansion_combo.currentIndex()
        
        if current_exp_index < 0 or not self.expansion_combo.isEnabled():
            self.class_combo.addItem("No classes available")
            self.class_combo.setEnabled(False)
            self.class_combo.blockSignals(False)
            return
            
        current_exp_id = self.expansion_combo.currentData()
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            self.class_combo.addItem("No classes available")
            self.class_combo.setEnabled(False)
            self.class_combo.blockSignals(False)
            return
            
        # Get classes for this expansion
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        # Add placeholder if no classes
        if not classes:
            self.class_combo.addItem("No classes available")
            self.class_combo.setEnabled(False)
        else:
            self.class_combo.setEnabled(True)
            
            # Add items
            current_class = self.config.get('current_class')
            current_index = 0
            
            for i, (class_id, class_data) in enumerate(classes.items()):
                class_name = class_data.get('name', class_id) if isinstance(class_data, dict) else class_id
                self.class_combo.addItem(class_name, class_id)
                
                if class_id == current_class:
                    current_index = i
                    
            # Set current index
            if current_class and current_index < self.class_combo.count():
                self.class_combo.setCurrentIndex(current_index)
                
        self.class_combo.blockSignals(False)
        
        # Update settings info
        self.update_settings_info()
        
    def populate_expansion_list(self):
        """Populate the expansion list widget"""
        self.expansion_list.clear()
        
        expansions = self.config.get('expansions', {})
        
        for exp_id, exp_data in expansions.items():
            exp_name = exp_data.get('name', exp_id)
            item = QListWidgetItem(f"{exp_name} ({exp_id})")
            item.setData(Qt.UserRole, exp_id)
            self.expansion_list.addItem(item)
            
    def populate_class_list(self):
        """Populate the class list widget with classes from the current expansion"""
        self.class_list.clear()
        
        # Get current expansion
        current_exp_id = self.expansion_combo.currentData()
        
        if not current_exp_id or not self.expansion_combo.isEnabled():
            return
            
        # Get classes for this expansion
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            return
            
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
            
        # Add to list
        for class_id, class_data in classes.items():
            class_name = class_data.get('name', class_id) if isinstance(class_data, dict) else class_id
            item = QListWidgetItem(f"{class_name} ({class_id})")
            item.setData(Qt.UserRole, class_id)
            self.class_list.addItem(item)
            
    def update_settings_info(self):
        """Update the settings info label"""
        current_exp_id = self.expansion_combo.currentData()
        current_class_id = self.class_combo.currentData()
        
        if not current_exp_id or not current_class_id or not self.class_combo.isEnabled():
            self.settings_label.setText("No configuration selected")
            return
            
        # Get expansion and class data
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            self.settings_label.setText("Invalid expansion selected")
            return
            
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        if current_class_id not in classes:
            self.settings_label.setText("Invalid class selected")
            return
            
        class_data = classes[current_class_id]
        
        # Build info text
        if isinstance(class_data, dict):
            # Count keybinds and templates
            keybind_count = len(class_data.get('keybinds', {}))
            has_scan_area = 'scan_area' in class_data and class_data['scan_area']
            
            info_text = (
                f"<b>Expansion:</b> {exp_data.get('name', current_exp_id)}<br>"
                f"<b>Class:</b> {class_data.get('name', current_class_id)}<br>"
                f"<b>Keybinds:</b> {keybind_count}<br>"
                f"<b>Scan Area:</b> {'Configured' if has_scan_area else 'Not Configured'}"
            )
        else:
            info_text = "Class data invalid or not fully configured"
            
        self.settings_label.setText(info_text)
        
    def on_expansion_changed(self, index):
        """Handle expansion selection change"""
        if index < 0 or not self.expansion_combo.isEnabled():
            return
            
        # Update class combo for the selected expansion
        self.populate_class_combo()
        
        # Update class list for the selected expansion
        self.populate_class_list()
        
        # Update tab title
        current_exp_id = self.expansion_combo.currentData()
        current_exp_name = self.expansion_combo.currentText()
        self.tab_widget.setTabText(2, f"Manage Classes ({current_exp_name})")
        
    def on_class_changed(self, index):
        """Handle class selection change"""
        if index < 0 or not self.class_combo.isEnabled():
            return
            
        # Update settings info
        self.update_settings_info()
        
    def apply_selection(self):
        """Apply the current expansion and class selection"""
        current_exp_id = self.expansion_combo.currentData()
        current_class_id = self.class_combo.currentData()
        
        if not current_exp_id or not current_class_id or not self.class_combo.isEnabled():
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select a valid expansion and class."
            )
            return
            
        # Check if selection exists
        expansions = self.config.get('expansions', {})
        if current_exp_id not in expansions:
            QMessageBox.warning(
                self,
                "Invalid Expansion",
                "The selected expansion is not valid."
            )
            return
            
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        if current_class_id not in classes:
            QMessageBox.warning(
                self,
                "Invalid Class",
                "The selected class is not valid for this expansion."
            )
            return
            
        # Update configuration
        self.config['current_expansion'] = current_exp_id
        self.config['current_class'] = current_class_id
        
        # Save configuration
        if self.config_manager.save_config(self.config):
            QMessageBox.information(
                self,
                "Selection Applied",
                f"Now using {exp_data.get('name', current_exp_id)} - "
                f"{classes[current_class_id].get('name', current_class_id) if isinstance(classes[current_class_id], dict) else current_class_id}"
            )
            
            # Emit config changed signal
            self.config_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
            
    def on_expansion_item_selected(self, current, previous):
        """Handle expansion item selection in the list"""
        self.edit_expansion_button.setEnabled(current is not None)
        self.remove_expansion_button.setEnabled(current is not None)
        
    def on_class_item_selected(self, current, previous):
        """Handle class item selection in the list"""
        self.edit_class_button.setEnabled(current is not None)
        self.remove_class_button.setEnabled(current is not None)
        
        # If a class is selected, check if it has templates
        if current is not None:
            class_id = current.data(Qt.UserRole)
            
            # Get current expansion
            current_exp_id = self.expansion_combo.currentData()
            
            if current_exp_id and current_exp_id in self.config.get('expansions', {}):
                # Update current class in config temporarily
                self.config['current_class'] = class_id
                
                # Check if this class has templates
                self.check_class_templates()
        
    def add_expansion(self):
        """Add a new expansion"""
        # Get expansion data from dialog
        expansion_data = ExpansionDialog.get_expansion(self)
        
        if not expansion_data:
            return
            
        # Validate expansion ID
        exp_id = expansion_data['id']
        if not exp_id:
            QMessageBox.warning(
                self,
                "Invalid ID",
                "Expansion ID cannot be empty."
            )
            return
            
        # Check if ID already exists
        if exp_id in self.config.get('expansions', {}):
            QMessageBox.warning(
                self,
                "Duplicate ID",
                f"An expansion with ID '{exp_id}' already exists."
            )
            return
            
        # Add to configuration
        if 'expansions' not in self.config:
            self.config['expansions'] = {}
            
        self.config['expansions'][exp_id] = {
            'name': expansion_data['name'],
            'classes': {}
        }
        
        # Save configuration
        if self.config_manager.save_config(self.config):
            # Update UI
            self.populate_expansion_list()
            self.populate_expansion_combo()
            
            QMessageBox.information(
                self,
                "Expansion Added",
                f"Expansion '{expansion_data['name']}' added successfully."
            )
            
            # Emit config changed signal
            self.config_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
            
    def edit_expansion(self):
        """Edit the selected expansion"""
        current_item = self.expansion_list.currentItem()
        if not current_item:
            return
            
        exp_id = current_item.data(Qt.UserRole)
        expansions = self.config.get('expansions', {})
        
        if exp_id not in expansions:
            QMessageBox.warning(
                self,
                "Invalid Expansion",
                "The selected expansion is not valid."
            )
            return
            
        # Get current data
        exp_data = expansions[exp_id]
        
        # Prepare data for dialog
        dialog_data = {
            'id': exp_id,
            'name': exp_data.get('name', exp_id)
        }
        
        # Get updated data from dialog
        updated_data = ExpansionDialog.get_expansion(self, dialog_data)
        
        if not updated_data:
            return
            
        # Update configuration
        self.config['expansions'][exp_id]['name'] = updated_data['name']
        
        # Save configuration
        if self.config_manager.save_config(self.config):
            # Update UI
            self.populate_expansion_list()
            self.populate_expansion_combo()
            
            QMessageBox.information(
                self,
                "Expansion Updated",
                f"Expansion '{updated_data['name']}' updated successfully."
            )
            
            # Emit config changed signal
            self.config_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
            
    def remove_expansion(self):
        """Remove the selected expansion"""
        current_item = self.expansion_list.currentItem()
        if not current_item:
            return
            
        exp_id = current_item.data(Qt.UserRole)
        expansions = self.config.get('expansions', {})
        
        if exp_id not in expansions:
            QMessageBox.warning(
                self,
                "Invalid Expansion",
                "The selected expansion is not valid."
            )
            return
            
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete expansion '{expansions[exp_id].get('name', exp_id)}'?\n"
            "This will delete all class configurations for this expansion.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Check if this is the current expansion
        if self.config.get('current_expansion') == exp_id:
            self.config['current_expansion'] = None
            self.config['current_class'] = None
            
        # Remove from configuration
        del self.config['expansions'][exp_id]
        
        # Save configuration
        if self.config_manager.save_config(self.config):
            # Update UI
            self.populate_expansion_list()
            self.populate_expansion_combo()
            
            QMessageBox.information(
                self,
                "Expansion Removed",
                "Expansion removed successfully."
            )
            
            # Emit config changed signal
            self.config_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
            
    def add_class(self):
        """Add a new class to the current expansion"""
        # Get current expansion
        current_exp_id = self.expansion_combo.currentData()
        
        if not current_exp_id or not self.expansion_combo.isEnabled():
            QMessageBox.warning(
                self,
                "No Expansion Selected",
                "Please select an expansion first."
            )
            return
            
        # Check if expansion exists
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            QMessageBox.warning(
                self,
                "Invalid Expansion",
                "The selected expansion is not valid."
            )
            return
            
        # Get class data from dialog
        class_data = ClassDialog.get_class(self)
        
        if not class_data:
            return
            
        # Validate class ID
        class_id = class_data['id']
        if not class_id:
            QMessageBox.warning(
                self,
                "Invalid ID",
                "Class ID cannot be empty."
            )
            return
            
        # Get current expansion data
        exp_data = expansions[current_exp_id]
        
        if 'classes' not in exp_data:
            exp_data['classes'] = {}
            
        # Check if class already exists
        if class_id in exp_data['classes']:
            QMessageBox.warning(
                self,
                "Class Exists",
                f"Class '{class_id}' already exists in expansion '{current_exp_id}'."
            )
            return
            
        # Default template for the class
        exp_data['classes'][class_id] = {
            'name': class_data['name'],
            'scan_area': None,
            'keybinds': {}
        }
        
        # Save configuration
        if self.config_manager.save_config(self.config):
            # Update UI
            self.populate_class_list()
            self.populate_class_combo()
            
            QMessageBox.information(
                self,
                "Class Added",
                f"Class '{class_data['name']}' added successfully to expansion '{exp_data.get('name', current_exp_id)}'."
            )
            
            # Emit config changed signal
            self.config_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
            
    def edit_class(self):
        """Edit the selected class in the current expansion"""
        current_item = self.class_list.currentItem()
        if not current_item:
            return
            
        class_id = current_item.data(Qt.UserRole)
        
        # Get current expansion
        current_exp_id = self.expansion_combo.currentData()
        
        if not current_exp_id or not self.expansion_combo.isEnabled():
            QMessageBox.warning(
                self,
                "No Expansion Selected",
                "Please select an expansion first."
            )
            return
            
        # Check if expansion exists
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            QMessageBox.warning(
                self,
                "Invalid Expansion",
                "The selected expansion is not valid."
            )
            return
            
        # Get current expansion data
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        if class_id not in classes:
            QMessageBox.warning(
                self,
                "Invalid Class",
                f"Class '{class_id}' not found in expansion '{current_exp_id}'."
            )
            return
            
        # Get class data
        class_data = classes[class_id]
        
        # Prepare data for dialog
        dialog_data = {
            'id': class_id,
            'name': class_data.get('name', class_id) if isinstance(class_data, dict) else class_id
        }
        
        # Get updated data from dialog
        updated_data = ClassDialog.get_class(self, dialog_data)
        
        if not updated_data:
            return
            
        # Update class data
        if isinstance(class_data, dict):
            class_data['name'] = updated_data['name']
        else:
            # Replace with proper structure
            classes[class_id] = {
                'name': updated_data['name'],
                'scan_area': None,
                'keybinds': {}
            }
            
        # Save configuration
        if self.config_manager.save_config(self.config):
            # Update UI
            self.populate_class_list()
            self.populate_class_combo()
            
            QMessageBox.information(
                self,
                "Class Updated",
                f"Class '{updated_data['name']}' updated successfully."
            )
            
            # Emit config changed signal
            self.config_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
            
    def remove_class(self):
        """Remove the selected class from the current expansion"""
        current_item = self.class_list.currentItem()
        if not current_item:
            return
            
        class_id = current_item.data(Qt.UserRole)
        
        # Get current expansion
        current_exp_id = self.expansion_combo.currentData()
        
        if not current_exp_id or not self.expansion_combo.isEnabled():
            QMessageBox.warning(
                self,
                "No Expansion Selected",
                "Please select an expansion first."
            )
            return
            
        # Check if expansion exists
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            QMessageBox.warning(
                self,
                "Invalid Expansion",
                "The selected expansion is not valid."
            )
            return
            
        # Get current expansion data
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        if class_id not in classes:
            QMessageBox.warning(
                self,
                "Invalid Class",
                f"Class '{class_id}' not found in expansion '{current_exp_id}'."
            )
            return
            
        # Get class name
        class_data = classes[class_id]
        class_name = class_data.get('name', class_id) if isinstance(class_data, dict) else class_id
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete class '{class_name}' from expansion '{exp_data.get('name', current_exp_id)}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Check if this is the current class
        if self.config.get('current_expansion') == current_exp_id and self.config.get('current_class') == class_id:
            self.config['current_class'] = None
            
        # Remove class
        del classes[class_id]
        
        # Save configuration
        if self.config_manager.save_config(self.config):
            # Update UI
            self.populate_class_list()
            self.populate_class_combo()
            
            QMessageBox.information(
                self,
                "Class Removed",
                f"Class '{class_name}' removed successfully from expansion '{exp_data.get('name', current_exp_id)}'."
            )
            
            # Emit config changed signal
            self.config_changed.emit()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )
    
    def get_current_selection(self):
        """Get the current expansion and class selection"""
        current_exp_id = self.expansion_combo.currentData()
        current_class_id = self.class_combo.currentData()
        
        return current_exp_id, current_class_id
    
    """
    Improvements to ExpansionClassManager to handle classes without spell templates
    """
    
    # Add this method to ExpansionClassManager class in expansion_class_manager.py
    def check_class_templates(self):
        """Check if the current class has spell templates and offer to create them if not"""
        # Get current expansion and class
        current_exp_id, current_class_id = self.get_current_selection()
        
        if not current_exp_id or not current_class_id:
            return
            
        # Get class config
        expansions = self.config.get('expansions', {})
        
        if current_exp_id not in expansions:
            return
            
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        if current_class_id not in classes:
            return
            
        class_config = classes[current_class_id]
        if not isinstance(class_config, dict):
            # Initialize with empty dict if not a dict
            classes[current_class_id] = {}
            class_config = classes[current_class_id]
        
        # Check if this class has spell templates
        has_templates = False
        if 'icon_templates' in class_config and class_config['icon_templates']:
            has_templates = True
            
        # If no templates, ask if user wants to create them
        if not has_templates:
            # Check if we're already in a configuration dialog
            from ui.enhanced_config_dialog import EnhancedConfigurationDialog
            top_level_parent = self
            while top_level_parent.parent():
                top_level_parent = top_level_parent.parent()
                
            if isinstance(top_level_parent, EnhancedConfigurationDialog):
                # We're already in the config dialog, just switch to the spells tab
                top_level_parent.tab_widget.setCurrentIndex(0)
                return
                
            # Otherwise, show the prompt
            from PyQt5.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self,
                "No Spell Templates",
                f"The class '{class_config.get('name', current_class_id)}' doesn't have any spell templates yet. "
                "Would you like to configure spell templates for this class now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.open_spell_configuration()

    
        
    # Add this method to ExpansionClassManager class as well
    def open_spell_configuration(self):
        """Open the configuration dialog focused on spell templates for the current class"""
        # Get parent window
        top_level_parent = self
        while top_level_parent.parent():
            top_level_parent = top_level_parent.parent()
        
        # If we're already in a configuration dialog, just switch to the spells tab
        from ui.enhanced_config_dialog import EnhancedConfigurationDialog
        if isinstance(top_level_parent, EnhancedConfigurationDialog):
            # Switch to the spells tab
            top_level_parent.tab_widget.setCurrentIndex(0)  # Switch to the spells tab
            return
            
        # Otherwise, open a new dialog
        from PyQt5.QtWidgets import QApplication
        main_window = QApplication.activeWindow()
        
        dialog = EnhancedConfigurationDialog(self.config_manager, parent=main_window)
        dialog.tab_widget.setCurrentIndex(0)  # Switch to the spells tab
        dialog.exec_()
    # Then modify the apply_selection method to check for templates after applying the selection
    def apply_selection(self):
        """Apply the current expansion and class selection"""
        current_exp_id = self.expansion_combo.currentData()
        current_class_id = self.class_combo.currentData()
        
        if not current_exp_id or not current_class_id or not self.class_combo.isEnabled():
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select a valid expansion and class."
            )
            return
            
        # Check if selection exists
        expansions = self.config.get('expansions', {})
        if current_exp_id not in expansions:
            QMessageBox.warning(
                self,
                "Invalid Expansion",
                "The selected expansion is not valid."
            )
            return
            
        exp_data = expansions[current_exp_id]
        classes = exp_data.get('classes', {})
        
        if current_class_id not in classes:
            QMessageBox.warning(
                self,
                "Invalid Class",
                "The selected class is not valid for this expansion."
            )
            return
            
        # Update configuration
        self.config['current_expansion'] = current_exp_id
        self.config['current_class'] = current_class_id
        
        # Save configuration
        if self.config_manager.save_config(self.config):
            QMessageBox.information(
                self,
                "Selection Applied",
                f"Now using {exp_data.get('name', current_exp_id)} - "
                f"{classes[current_class_id].get('name', current_class_id) if isinstance(classes[current_class_id], dict) else current_class_id}"
            )
            
            # Emit config changed signal
            self.config_changed.emit()
            
            # Check for templates
            self.check_class_templates()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )