"""
Edit operations mixin for navigation widget.

Provides edit functionality for projects, parts, and setups.
"""

from PySide6 import QtWidgets, QtCore
from typing import Optional

from ...models.project import ProjectStatus


class EditOperationsMixin:
    """Mixin providing edit operations for navigation widget."""
    
    def edit_current_item(self):
        """Edit the currently selected item based on what's selected."""
        if self.current_setup_id:
            self.edit_current_setup()
        elif self.current_part_id:
            self.edit_current_part()
        elif self.current_project_id:
            self.edit_current_project()
        else:
            QtWidgets.QMessageBox.information(self, "Edit Item", "Please select an item to edit.")
    
    def edit_current_project(self):
        """Edit the current project."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found.")
            return
        
        dialog = ProjectEditDialog(project, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            # Update project with new values
            project.name = dialog.name_edit.text().strip()
            project.description = dialog.description_edit.toPlainText().strip()
            project.status = dialog.status_combo.currentData()
            
            # Save changes
            if self.project_manager.update_project(project):
                self.refresh_projects()
                QtWidgets.QMessageBox.information(self, "Success", "Project updated successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to update project.")
    
    def edit_current_part(self):
        """Edit the current part."""
        if not self.current_project_id or not self.current_part_id:
            return
        
        part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
        if not part:
            QtWidgets.QMessageBox.warning(self, "Error", "Part not found.")
            return
        
        dialog = PartEditDialog(part, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            # Update part with new values
            part.name = dialog.name_edit.text().strip()
            part.description = dialog.description_edit.toPlainText().strip()
            part.material = dialog.material_edit.text().strip()
            
            # Save changes
            if self.project_manager.update_part(self.current_project_id, part):
                self.refresh_parts()
                QtWidgets.QMessageBox.information(self, "Success", "Part updated successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to update part.")
    
    def edit_current_setup(self):
        """Edit the current setup."""
        if not self.current_project_id or not self.current_part_id or not self.current_setup_id:
            return
        
        setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
        if not setup:
            QtWidgets.QMessageBox.warning(self, "Error", "Setup not found.")
            return
        
        dialog = SetupEditDialog(setup, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            # Update setup with new values
            setup.name = dialog.name_edit.text().strip()
            setup.description = dialog.description_edit.toPlainText().strip()
            setup.operation_type = dialog.operation_edit.text().strip()
            
            # Save changes
            if self.project_manager.update_setup(self.current_project_id, self.current_part_id, setup):
                self.refresh_setups()
                QtWidgets.QMessageBox.information(self, "Success", "Setup updated successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to update setup.")
    
    def new_project(self):
        """Create a new project."""
        dialog = ProjectEditDialog(None, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            name = dialog.name_edit.text().strip()
            description = dialog.description_edit.toPlainText().strip()
            status = dialog.status_combo.currentData()
            
            if not name:
                QtWidgets.QMessageBox.warning(self, "Error", "Project name cannot be empty.")
                return
            
            # Create new project
            project_id = self.project_manager.create_project(name, description, status)
            if project_id:
                self.refresh_projects()
                
                # Select the new project
                for i in range(1, self.project_combo.count()):  # Skip "Select Project..." at index 0
                    if self.project_combo.itemData(i) == project_id:
                        self.project_combo.setCurrentIndex(i)
                        break
                
                QtWidgets.QMessageBox.information(self, "Success", f"Project '{name}' created successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to create project.")
    
    def new_part(self):
        """Create a new part."""
        if not self.current_project_id:
            QtWidgets.QMessageBox.information(self, "New Part", "Please select a project first.")
            return
        
        dialog = PartEditDialog(None, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            name = dialog.name_edit.text().strip()
            description = dialog.description_edit.toPlainText().strip()
            material = dialog.material_edit.text().strip()
            
            if not name:
                QtWidgets.QMessageBox.warning(self, "Error", "Part name cannot be empty.")
                return
            
            # Create new part
            part_id = self.project_manager.create_part(self.current_project_id, name, description, material)
            if part_id:
                self.refresh_parts()
                
                # Select the new part
                for i in range(1, self.part_combo.count()):  # Skip "Select Part..." at index 0
                    if self.part_combo.itemData(i) == part_id:
                        self.part_combo.setCurrentIndex(i)
                        break
                
                QtWidgets.QMessageBox.information(self, "Success", f"Part '{name}' created successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to create part.")
    
    def new_setup(self):
        """Create a new setup."""
        if not self.current_project_id or not self.current_part_id:
            QtWidgets.QMessageBox.information(self, "New Setup", "Please select a project and part first.")
            return
        
        dialog = SetupEditDialog(None, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            name = dialog.name_edit.text().strip()
            description = dialog.description_edit.toPlainText().strip()
            operation_type = dialog.operation_edit.text().strip()
            
            if not name:
                QtWidgets.QMessageBox.warning(self, "Error", "Setup name cannot be empty.")
                return
            
            # Create new setup
            setup_id = self.project_manager.create_setup(self.current_project_id, self.current_part_id, name, description, operation_type)
            if setup_id:
                self.refresh_setups()
                
                # Select the new setup
                for i in range(1, self.setup_combo.count()):  # Skip "Select Setup..." at index 0
                    if self.setup_combo.itemData(i) == setup_id:
                        self.setup_combo.setCurrentIndex(i)
                        break
                
                QtWidgets.QMessageBox.information(self, "Success", f"Setup '{name}' created successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to create setup.")


class ProjectEditDialog(QtWidgets.QDialog):
    """Dialog for editing project properties."""
    
    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        self.project = project
        
        self.setWindowTitle("Edit Project" if project else "New Project")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.setup_ui()
        
        if project:
            self.load_project_data()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Name field
        name_label = QtWidgets.QLabel("Project Name:")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name...")
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        
        # Description field
        desc_label = QtWidgets.QLabel("Description:")
        self.description_edit = QtWidgets.QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter project description...")
        layout.addWidget(desc_label)
        layout.addWidget(self.description_edit)
        
        # Status field
        status_label = QtWidgets.QLabel("Status:")
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItem("🟢 Active", ProjectStatus.ACTIVE)
        self.status_combo.addItem("✅ Completed", ProjectStatus.COMPLETED)
        self.status_combo.addItem("📁 Archived", ProjectStatus.ARCHIVED)
        layout.addWidget(status_label)
        layout.addWidget(self.status_combo)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_project_data(self):
        """Load project data into the form."""
        if self.project:
            self.name_edit.setText(self.project.name)
            self.description_edit.setPlainText(self.project.description or "")
            
            # Set status combo
            for i in range(self.status_combo.count()):
                if self.status_combo.itemData(i) == self.project.status:
                    self.status_combo.setCurrentIndex(i)
                    break


class PartEditDialog(QtWidgets.QDialog):
    """Dialog for editing part properties."""
    
    def __init__(self, part=None, parent=None):
        super().__init__(parent)
        self.part = part
        
        self.setWindowTitle("Edit Part" if part else "New Part")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.setup_ui()
        
        if part:
            self.load_part_data()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Name field
        name_label = QtWidgets.QLabel("Part Name:")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Enter part name...")
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        
        # Material field
        material_label = QtWidgets.QLabel("Material:")
        self.material_edit = QtWidgets.QLineEdit()
        self.material_edit.setPlaceholderText("Enter material (e.g., Aluminum 6061)...")
        layout.addWidget(material_label)
        layout.addWidget(self.material_edit)
        
        # Description field
        desc_label = QtWidgets.QLabel("Description:")
        self.description_edit = QtWidgets.QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter part description...")
        layout.addWidget(desc_label)
        layout.addWidget(self.description_edit)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_part_data(self):
        """Load part data into the form."""
        if self.part:
            self.name_edit.setText(self.part.name)
            self.material_edit.setText(self.part.material or "")
            self.description_edit.setPlainText(self.part.description or "")


class SetupEditDialog(QtWidgets.QDialog):
    """Dialog for editing setup properties."""
    
    def __init__(self, setup=None, parent=None):
        super().__init__(parent)
        self.setup = setup
        
        self.setWindowTitle("Edit Setup" if setup else "New Setup")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.setup_ui()
        
        if setup:
            self.load_setup_data()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Name field
        name_label = QtWidgets.QLabel("Setup Name:")
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Enter setup name...")
        layout.addWidget(name_label)
        layout.addWidget(self.name_edit)
        
        # Operation type field
        operation_label = QtWidgets.QLabel("Operation Type:")
        self.operation_edit = QtWidgets.QLineEdit()
        self.operation_edit.setPlaceholderText("Enter operation type (e.g., Roughing, Finishing)...")
        layout.addWidget(operation_label)
        layout.addWidget(self.operation_edit)
        
        # Description field
        desc_label = QtWidgets.QLabel("Description:")
        self.description_edit = QtWidgets.QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter setup description...")
        layout.addWidget(desc_label)
        layout.addWidget(self.description_edit)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def load_setup_data(self):
        """Load setup data into the form."""
        if self.setup:
            self.name_edit.setText(self.setup.name)
            self.operation_edit.setText(self.setup.operation_type or "")
            self.description_edit.setPlainText(self.setup.description or "")