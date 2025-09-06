"""
Project navigation widget with cascading ComboBoxes for Project/Part/Setup selection.

Provides navigation controls with edit, delete, and clone functionality.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional

from ...models.project import ProjectManager, ProjectStatus


class ProjectNavigationWidget(QtWidgets.QWidget):
    """Navigation widget with cascading ComboBoxes for Project/Part/Setup selection."""
    
    selectionChanged = QtCore.Signal(str, str, str)  # project_id, part_id, setup_id
    
    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.current_project_id: Optional[str] = None
        self.current_part_id: Optional[str] = None
        self.current_setup_id: Optional[str] = None
        
        # Settings for persistence
        self.settings = QtCore.QSettings("CNC_ToolHub", "ProjectNavigation")
        
        self.setup_ui()
        self.refresh_projects()
    
    def setup_ui(self):
        """Setup the navigation UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Set maximum height to keep navigation compact
        self.setMaximumHeight(60)
        
        # Project selection with icon
        project_label = QtWidgets.QLabel("📁")
        project_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(project_label)
        
        self.project_combo = QtWidgets.QComboBox()
        self.project_combo.setMinimumWidth(180)
        self.project_combo.currentTextChanged.connect(self.on_project_changed)
        self.project_combo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.project_combo.customContextMenuRequested.connect(self.show_project_context_menu)
        layout.addWidget(self.project_combo)
        
        # Separator
        separator1 = QtWidgets.QLabel("|")
        separator1.setStyleSheet("color: #666666; font-size: 16px; font-weight: bold;")
        layout.addWidget(separator1)
        
        # Part selection with icon and add button
        part_label = QtWidgets.QLabel("🔧")
        part_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(part_label)
        
        self.part_combo = QtWidgets.QComboBox()
        self.part_combo.setMinimumWidth(140)
        self.part_combo.currentTextChanged.connect(self.on_part_changed)
        self.part_combo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.part_combo.customContextMenuRequested.connect(self.show_part_context_menu)
        layout.addWidget(self.part_combo)
        
        self.new_part_btn = QtWidgets.QPushButton("+")
        self.new_part_btn.clicked.connect(self.new_part)
        self.new_part_btn.setEnabled(False)
        self.new_part_btn.setFixedSize(24, 24)
        self.new_part_btn.setToolTip("Add new part")
        self.new_part_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #666666; }
        """)
        layout.addWidget(self.new_part_btn)
        
        # Separator
        separator2 = QtWidgets.QLabel("|")
        separator2.setStyleSheet("color: #666666; font-size: 16px; font-weight: bold;")
        layout.addWidget(separator2)
        
        # Setup selection with icon and add button
        setup_label = QtWidgets.QLabel("⚙️")
        setup_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(setup_label)
        
        self.setup_combo = QtWidgets.QComboBox()
        self.setup_combo.setMinimumWidth(140)
        self.setup_combo.currentTextChanged.connect(self.on_setup_changed)
        self.setup_combo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setup_combo.customContextMenuRequested.connect(self.show_setup_context_menu)
        layout.addWidget(self.setup_combo)
        
        self.new_setup_btn = QtWidgets.QPushButton("+")
        self.new_setup_btn.clicked.connect(self.new_setup)
        self.new_setup_btn.setEnabled(False)
        self.new_setup_btn.setFixedSize(24, 24)
        self.new_setup_btn.setToolTip("Add new setup")
        self.new_setup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #666666; }
        """)
        layout.addWidget(self.new_setup_btn)
        
        # Separator
        separator3 = QtWidgets.QLabel("|")
        separator3.setStyleSheet("color: #666666; font-size: 16px; font-weight: bold;")
        layout.addWidget(separator3)
        
        # Edit button
        self.edit_btn = QtWidgets.QPushButton("✏️")
        self.edit_btn.setFixedSize(28, 28)
        self.edit_btn.setToolTip("Edit selected item (F2)")
        self.edit_btn.clicked.connect(self.edit_current_item)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #666666; }
        """)
        layout.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QtWidgets.QPushButton("🗑️")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setToolTip("Delete selected item (Del)")
        self.delete_btn.clicked.connect(self.delete_current_item)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #666666; }
        """)
        layout.addWidget(self.delete_btn)

        # Info button
        self.info_btn = QtWidgets.QPushButton("ℹ️")
        self.info_btn.setFixedSize(28, 28)
        self.info_btn.setToolTip("Show project details (F1 / Ctrl+I)")
        self.info_btn.clicked.connect(self.show_project_info)
        self.info_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #777777; }
        """)
        layout.addWidget(self.info_btn)
        
        # New Project button (moved to end)
        self.new_project_btn = QtWidgets.QPushButton("📁 New Project")
        self.new_project_btn.setToolTip("Create new project (Ctrl+N)")
        self.new_project_btn.clicked.connect(self.new_project)
        self.new_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        layout.addWidget(self.new_project_btn)
        
        layout.addStretch()
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
    
    def refresh_projects(self):
        """Refresh project list."""
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self.project_combo.addItem("Select Project...", None)
        
        projects = self.project_manager.get_all_projects()
        for project in projects:
            self.project_combo.addItem(project.name, project.id)
        
        self.project_combo.blockSignals(False)
        self.refresh_parts()
    
    def refresh_parts(self):
        """Refresh parts list based on current project."""
        self.part_combo.blockSignals(True)
        self.part_combo.clear()
        self.part_combo.addItem("All Parts", None)
        
        if self.current_project_id:
            project = self.project_manager.get_project(self.current_project_id)
            if project:
                for part in project.parts:
                    self.part_combo.addItem(part.name, part.id)
                self.new_part_btn.setEnabled(True)
            else:
                self.new_part_btn.setEnabled(False)
        else:
            self.new_part_btn.setEnabled(False)
        
        self.part_combo.blockSignals(False)
        self.refresh_setups()
    
    def refresh_setups(self):
        """Refresh setups list based on current part."""
        self.setup_combo.blockSignals(True)
        self.setup_combo.clear()
        self.setup_combo.addItem("All Setups", None)
        
        if self.current_project_id and self.current_part_id:
            part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
            if part:
                for setup in part.setups:
                    self.setup_combo.addItem(setup.name, setup.id)
                self.new_setup_btn.setEnabled(True)
            else:
                self.new_setup_btn.setEnabled(False)
        else:
            self.new_setup_btn.setEnabled(False)
        
        self.setup_combo.blockSignals(False)
    
    def on_project_changed(self):
        """Handle project selection change."""
        current_data = self.project_combo.currentData()
        self.current_project_id = current_data
        self.current_part_id = None
        self.current_setup_id = None
        self.refresh_parts()
        self.emit_selection_changed()
    
    def on_part_changed(self):
        """Handle part selection change."""
        current_data = self.part_combo.currentData()
        self.current_part_id = current_data
        self.current_setup_id = None
        self.refresh_setups()
        self.emit_selection_changed()
    
    def on_setup_changed(self):
        """Handle setup selection change."""
        current_data = self.setup_combo.currentData()
        self.current_setup_id = current_data
        self.emit_selection_changed()
    
    def emit_selection_changed(self):
        """Emit selection changed signal."""
        self.save_current_selection()
        self.update_button_states()
        self.selectionChanged.emit(
            self.current_project_id or "",
            self.current_part_id or "",
            self.current_setup_id or ""
        )
    
    def update_button_states(self):
        """Update enabled state of edit/delete buttons based on current selection."""
        has_project = bool(self.current_project_id)
        has_part = bool(self.current_part_id) 
        has_setup = bool(self.current_setup_id)
        
        # Enable edit/delete if any item is selected
        can_edit_delete = has_project
        self.edit_btn.setEnabled(can_edit_delete)
        self.delete_btn.setEnabled(can_edit_delete)
        
        # Update tooltips based on selection
        if has_setup:
            self.edit_btn.setToolTip("Edit current setup (F2)")
            self.delete_btn.setToolTip("Delete current setup (Del)")
        elif has_part:
            self.edit_btn.setToolTip("Edit current part (F2)")
            self.delete_btn.setToolTip("Delete current part (Del)")
        elif has_project:
            self.edit_btn.setToolTip("Edit current project (F2)")
            self.delete_btn.setToolTip("Delete current project (Del)")
        else:
            self.edit_btn.setToolTip("Edit selected item (F2)")
            self.delete_btn.setToolTip("Delete selected item (Del)")
    
    def edit_current_item(self):
        """Edit the currently selected item."""
        if self.current_setup_id:
            self.edit_current_setup()
        elif self.current_part_id:
            self.edit_current_part()
        elif self.current_project_id:
            self.edit_current_project()
    
    def delete_current_item(self):
        """Delete the currently selected item."""
        if self.current_setup_id:
            self.delete_current_setup()
        elif self.current_part_id:
            self.delete_current_part()
        elif self.current_project_id:
            self.delete_current_project()
    
    def edit_current_project(self):
        """Edit the current project."""
        from ..dialogs.project_dialogs import ProjectEditorDialog
        
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found")
            return
        
        dialog = ProjectEditorDialog(project, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            project.name = data['name']
            project.description = data['description']
            project.customer_name = data['customer_name']
            project.status = data['status']
            
            if self.project_manager.update_project(project):
                self.refresh_projects()
                # Re-select the project to maintain selection
                index = self.project_combo.findData(project.id)
                if index >= 0:
                    self.project_combo.setCurrentIndex(index)
                QtWidgets.QMessageBox.information(self, "Success", "Project updated successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to update project")
    
    def edit_current_part(self):
        """Edit the current part."""
        from ..dialogs.project_dialogs import PartEditorDialog
        
        if not self.current_project_id or not self.current_part_id:
            return
        
        part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
        if not part:
            QtWidgets.QMessageBox.warning(self, "Error", "Part not found")
            return
        
        dialog = PartEditorDialog(part, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            part.name = data['name']
            part.description = data['description']
            part.material = data['material']
            part.drawing_number = data['drawing_number']
            part.quantity_required = data['quantity_required']
            
            if self.project_manager.update_part(self.current_project_id, part):
                self.refresh_parts()
                # Re-select the part to maintain selection
                index = self.part_combo.findData(part.id)
                if index >= 0:
                    self.part_combo.setCurrentIndex(index)
                QtWidgets.QMessageBox.information(self, "Success", "Part updated successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to update part")
    
    def edit_current_setup(self):
        """Edit the current setup."""
        from ..dialogs.project_dialogs import SetupEditorDialog
        
        if not self.current_project_id or not self.current_part_id or not self.current_setup_id:
            return
        
        setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
        if not setup:
            QtWidgets.QMessageBox.warning(self, "Error", "Setup not found")
            return
        
        dialog = SetupEditorDialog(setup, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            setup.name = data['name']
            setup.description = data['description']
            setup.work_offset = data['work_offset']
            setup.operation_type = data['operation_type']
            
            if self.project_manager.update_setup(self.current_project_id, self.current_part_id, setup):
                self.refresh_setups()
                # Re-select the setup to maintain selection
                index = self.setup_combo.findData(setup.id)
                if index >= 0:
                    self.setup_combo.setCurrentIndex(index)
                QtWidgets.QMessageBox.information(self, "Success", "Setup updated successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to update setup")
    
    def delete_current_project(self):
        """Delete the current project."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found")
            return
        
        # Show detailed confirmation dialog
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Project",
            f"Are you sure you want to delete project '{project.name}'?\n\n"
            f"This will also delete:\n"
            f"• {project.get_part_count()} parts\n"
            f"• {project.get_setup_count()} setups\n"
            f"• {project.get_total_tool_count()} tool assignments\n\n"
            f"This action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.delete_project(self.current_project_id):
                self.current_project_id = None
                self.current_part_id = None
                self.current_setup_id = None
                self.refresh_projects()
                QtWidgets.QMessageBox.information(self, "Success", "Project deleted successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to delete project")
    
    def delete_current_part(self):
        """Delete the current part."""
        if not self.current_project_id or not self.current_part_id:
            return
        
        part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
        if not part:
            QtWidgets.QMessageBox.warning(self, "Error", "Part not found")
            return
        
        # Show detailed confirmation dialog
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Part",
            f"Are you sure you want to delete part '{part.name}'?\n\n"
            f"This will also delete:\n"
            f"• {part.get_setup_count()} setups\n"
            f"• All tool assignments for this part\n\n"
            f"This action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.delete_part(self.current_project_id, self.current_part_id):
                self.current_part_id = None
                self.current_setup_id = None
                self.refresh_parts()
                QtWidgets.QMessageBox.information(self, "Success", "Part deleted successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to delete part")
    
    def delete_current_setup(self):
        """Delete the current setup."""
        if not self.current_project_id or not self.current_part_id or not self.current_setup_id:
            return
        
        setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
        if not setup:
            QtWidgets.QMessageBox.warning(self, "Error", "Setup not found")
            return
        
        # Show detailed confirmation dialog
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Setup",
            f"Are you sure you want to delete setup '{setup.name}'?\n\n"
            f"This will also delete all tool assignments for this setup.\n\n"
            f"This action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.delete_setup(self.current_project_id, self.current_part_id, self.current_setup_id):
                self.current_setup_id = None
                self.refresh_setups()
                QtWidgets.QMessageBox.information(self, "Success", "Setup deleted successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to delete setup")
    
    def show_project_context_menu(self, position):
        """Show context menu for project combo box."""
        if not self.current_project_id:
            return
        
        menu = QtWidgets.QMenu(self)
        
        edit_action = menu.addAction("✏️ Edit Project")
        edit_action.triggered.connect(self.edit_current_project)
        
        clone_action = menu.addAction("📋 Duplicate Project")
        clone_action.triggered.connect(self.clone_current_project)
        
        menu.addSeparator()
        
        # Status submenu
        status_menu = menu.addMenu("📊 Change Status")
        
        active_action = status_menu.addAction("🟢 Active")
        active_action.triggered.connect(lambda: self.change_project_status(ProjectStatus.ACTIVE))
        
        completed_action = status_menu.addAction("🔵 Completed") 
        completed_action.triggered.connect(lambda: self.change_project_status(ProjectStatus.COMPLETED))
        
        archived_action = status_menu.addAction("🟡 Archived")
        archived_action.triggered.connect(lambda: self.change_project_status(ProjectStatus.ARCHIVED))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete Project")
        delete_action.triggered.connect(self.delete_current_project)
        
        menu.exec_(self.project_combo.mapToGlobal(position))
    
    def show_part_context_menu(self, position):
        """Show context menu for part combo box."""
        if not self.current_part_id:
            return
        
        menu = QtWidgets.QMenu(self)
        
        edit_action = menu.addAction("✏️ Edit Part")
        edit_action.triggered.connect(self.edit_current_part)
        
        clone_action = menu.addAction("📋 Duplicate Part")
        clone_action.triggered.connect(self.clone_current_part)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete Part")
        delete_action.triggered.connect(self.delete_current_part)
        
        menu.exec_(self.part_combo.mapToGlobal(position))
    
    def show_setup_context_menu(self, position):
        """Show context menu for setup combo box."""
        if not self.current_setup_id:
            return
        
        menu = QtWidgets.QMenu(self)
        
        edit_action = menu.addAction("✏️ Edit Setup")
        edit_action.triggered.connect(self.edit_current_setup)
        
        clone_action = menu.addAction("📋 Duplicate Setup")
        clone_action.triggered.connect(self.clone_current_setup)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete Setup")
        delete_action.triggered.connect(self.delete_current_setup)
        
        menu.exec_(self.setup_combo.mapToGlobal(position))
    
    def clone_current_project(self):
        """Clone the current project."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found")
            return
        
        # Get new name from user
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Clone Project", 
            f"Enter name for cloned project:",
            text=f"{project.name} - Copy"
        )
        
        if ok and new_name.strip():
            cloned_project = self.project_manager.clone_project(self.current_project_id, new_name.strip())
            if cloned_project:
                self.refresh_projects()
                # Select the new project
                index = self.project_combo.findData(cloned_project.id)
                if index >= 0:
                    self.project_combo.setCurrentIndex(index)
                QtWidgets.QMessageBox.information(self, "Success", "Project cloned successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to clone project")
    
    def clone_current_part(self):
        """Clone the current part."""
        if not self.current_project_id or not self.current_part_id:
            return
        
        part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
        if not part:
            QtWidgets.QMessageBox.warning(self, "Error", "Part not found")
            return
        
        # Get new name from user
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Clone Part", 
            f"Enter name for cloned part:",
            text=f"{part.name} - Copy"
        )
        
        if ok and new_name.strip():
            # Create new part with same data
            new_part = self.project_manager.create_part(
                self.current_project_id,
                name=new_name.strip(),
                description=part.description,
                material=part.material,
                drawing_number=part.drawing_number,
                quantity_required=part.quantity_required
            )
            
            if new_part:
                # Copy tools
                for tool_assoc in part.tools:
                    new_part.add_tool(tool_assoc.tool_id, tool_assoc.quantity_needed, tool_assoc.notes)
                
                # Copy setups
                for setup in part.setups:
                    new_setup = self.project_manager.create_setup(
                        self.current_project_id,
                        new_part.id,
                        name=setup.name + " - Copy",
                        description=setup.description,
                        work_offset=setup.work_offset,
                        operation_type=setup.operation_type
                    )
                    
                    if new_setup:
                        # Copy setup tools
                        for tool_assoc in setup.tools:
                            new_setup.add_tool(tool_assoc.tool_id, tool_assoc.quantity_needed, tool_assoc.notes)
                
                self.project_manager.save_projects()
                self.refresh_parts()
                # Select the new part
                index = self.part_combo.findData(new_part.id)
                if index >= 0:
                    self.part_combo.setCurrentIndex(index)
                QtWidgets.QMessageBox.information(self, "Success", "Part cloned successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to clone part")
    
    def clone_current_setup(self):
        """Clone the current setup."""
        if not self.current_project_id or not self.current_part_id or not self.current_setup_id:
            return
        
        setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
        if not setup:
            QtWidgets.QMessageBox.warning(self, "Error", "Setup not found")
            return
        
        # Get new name from user
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Clone Setup", 
            f"Enter name for cloned setup:",
            text=f"{setup.name} - Copy"
        )
        
        if ok and new_name.strip():
            # Create new setup with same data
            new_setup = self.project_manager.create_setup(
                self.current_project_id,
                self.current_part_id,
                name=new_name.strip(),
                description=setup.description,
                work_offset=setup.work_offset,
                operation_type=setup.operation_type
            )
            
            if new_setup:
                # Copy tools
                for tool_assoc in setup.tools:
                    new_setup.add_tool(tool_assoc.tool_id, tool_assoc.quantity_needed, tool_assoc.notes)
                
                self.project_manager.save_projects()
                self.refresh_setups()
                # Select the new setup
                index = self.setup_combo.findData(new_setup.id)
                if index >= 0:
                    self.setup_combo.setCurrentIndex(index)
                QtWidgets.QMessageBox.information(self, "Success", "Setup cloned successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to clone setup")
    
    def archive_current_project(self):
        """Archive the current project."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Archive Project",
            f"Archive project '{project.name}'?\n\n"
            f"Archived projects are hidden from the active project list.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.archive_project(self.current_project_id):
                self.current_project_id = None
                self.current_part_id = None
                self.current_setup_id = None
                self.refresh_projects()
                QtWidgets.QMessageBox.information(self, "Success", "Project archived successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to archive project")
    
    def change_project_status(self, new_status: ProjectStatus):
        """Change the status of the current project."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found")
            return
        
        if project.status == new_status:
            QtWidgets.QMessageBox.information(self, "No Change", f"Project is already {new_status.value}")
            return
        
        project.status = new_status
        if self.project_manager.update_project(project):
            status_name = new_status.value.title()
            QtWidgets.QMessageBox.information(self, "Success", f"Project status changed to {status_name}")
            
            # If project was archived, it might disappear from active list
            if new_status == ProjectStatus.ARCHIVED:
                self.current_project_id = None
                self.current_part_id = None  
                self.current_setup_id = None
                self.refresh_projects()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Failed to change project status")
    
    def show_project_info(self):
        """Show project info in a popup dialog."""
        if not self.current_project_id:
            QtWidgets.QMessageBox.information(self, "Project Info", "No project selected")
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.information(self, "Project Info", "Project not found")
            return
        
        info_lines = [f"<h3>📁 {project.name}</h3>"]
        info_lines.append(f"<b>Customer:</b> {project.customer_name or 'Not specified'}")
        
        # Add status with color coding
        status_text = project.status.value.title()
        if project.status == ProjectStatus.ACTIVE:
            status_color = "#4CAF50"  # Green
        elif project.status == ProjectStatus.COMPLETED:
            status_color = "#2196F3"  # Blue
        else:  # ARCHIVED
            status_color = "#FF9800"  # Orange
        
        info_lines.append(f"<b>Status:</b> <span style='color: {status_color};'>{status_text}</span>")
        
        if project.description:
            info_lines.append(f"<b>Description:</b> {project.description}")
        
        if self.current_part_id:
            part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
            if part:
                info_lines.append(f"<hr><h4>🔧 Part: {part.name}</h4>")
                if part.material:
                    info_lines.append(f"<b>Material:</b> {part.material}")
                if part.drawing_number:
                    info_lines.append(f"<b>Drawing #:</b> {part.drawing_number}")
                info_lines.append(f"<b>Quantity:</b> {part.quantity_required}")
                
                if self.current_setup_id:
                    setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
                    if setup:
                        info_lines.append(f"<hr><h4>⚙️ Setup: {setup.name}</h4>")
                        info_lines.append(f"<b>Work Offset:</b> {setup.work_offset}")
                        if setup.operation_type:
                            info_lines.append(f"<b>Operation:</b> {setup.operation_type}")
                        if setup.description:
                            info_lines.append(f"<b>Description:</b> {setup.description}")
                else:
                    info_lines.append(f"<b>Setups:</b> {part.get_setup_count()}")
        else:
            info_lines.append(f"<b>Parts:</b> {project.get_part_count()}")
            info_lines.append(f"<b>Total Tools:</b> {project.get_total_tool_count()}")
        
        if project.notes:
            info_lines.append(f"<hr><b>Notes:</b><br>{project.notes}")
        
        QtWidgets.QMessageBox.information(self, "Project Information", "<br>".join(info_lines))
    
    def new_project(self):
        """Create a new project."""
        from ..dialogs.project_dialogs import ProjectEditorDialog
        
        dialog = ProjectEditorDialog(None, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            project = self.project_manager.create_project(
                name=data['name'],
                description=data['description'],
                customer_name=data['customer_name']
            )
            if project:
                # Set the status after creation
                project.status = data['status']
                self.project_manager.update_project(project)
                self.refresh_projects()
                # Select the new project
                index = self.project_combo.findData(project.id)
                if index >= 0:
                    self.project_combo.setCurrentIndex(index)
    
    def new_part(self):
        """Create a new part."""
        from ..dialogs.project_dialogs import PartEditorDialog
        
        if not self.current_project_id:
            return
        
        dialog = PartEditorDialog(None, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            part = self.project_manager.create_part(self.current_project_id, **data)
            if part:
                self.refresh_parts()
                # Select the new part
                index = self.part_combo.findData(part.id)
                if index >= 0:
                    self.part_combo.setCurrentIndex(index)
    
    def new_setup(self):
        """Create a new setup."""
        from ..dialogs.project_dialogs import SetupEditorDialog
        
        if not self.current_project_id or not self.current_part_id:
            return
        
        dialog = SetupEditorDialog(None, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            setup = self.project_manager.create_setup(self.current_project_id, self.current_part_id, **data)
            if setup:
                self.refresh_setups()
                # Select the new setup
                index = self.setup_combo.findData(setup.id)
                if index >= 0:
                    self.setup_combo.setCurrentIndex(index)
    
    def save_current_selection(self):
        """Save current selection to settings."""
        self.settings.setValue("last_project_id", self.current_project_id or "")
        self.settings.setValue("last_part_id", self.current_part_id or "")
        self.settings.setValue("last_setup_id", self.current_setup_id or "")
    
    def restore_last_selection(self):
        """Restore last selection from settings."""
        last_project_id = self.settings.value("last_project_id", "")
        last_part_id = self.settings.value("last_part_id", "")
        last_setup_id = self.settings.value("last_setup_id", "")
        
        # Try to restore project selection
        if last_project_id:
            project_index = self.project_combo.findData(last_project_id)
            if project_index >= 0:
                self.project_combo.blockSignals(True)
                self.project_combo.setCurrentIndex(project_index)
                self.project_combo.blockSignals(False)
                self.current_project_id = last_project_id
                self.refresh_parts()
                
                # Try to restore part selection
                if last_part_id:
                    part_index = self.part_combo.findData(last_part_id)
                    if part_index >= 0:
                        self.part_combo.blockSignals(True)
                        self.part_combo.setCurrentIndex(part_index)
                        self.part_combo.blockSignals(False)
                        self.current_part_id = last_part_id
                        self.refresh_setups()
                        
                        # Try to restore setup selection
                        if last_setup_id:
                            setup_index = self.setup_combo.findData(last_setup_id)
                            if setup_index >= 0:
                                self.setup_combo.blockSignals(True)
                                self.setup_combo.setCurrentIndex(setup_index)
                                self.setup_combo.blockSignals(False)
                                self.current_setup_id = last_setup_id
                
                # Emit the final selection change
                self.emit_selection_changed()
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts for common operations."""
        # F2 for edit
        edit_shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F2), self)
        edit_shortcut.activated.connect(self.edit_current_item)
        
        # Delete key for delete
        delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self)
        delete_shortcut.activated.connect(self.delete_current_item)
        
        # Ctrl+D for duplicate/clone
        clone_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+D"), self)
        clone_shortcut.activated.connect(self.clone_current_item)
        
        # Ctrl+N for new project
        new_project_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        new_project_shortcut.activated.connect(self.new_project)
        
        # Ctrl+Shift+P for new part
        new_part_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+P"), self)
        new_part_shortcut.activated.connect(self.new_part)
        
        # Ctrl+Shift+S for new setup
        new_setup_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+S"), self)
        new_setup_shortcut.activated.connect(self.new_setup)
        
        # F1 or Ctrl+I for info
        info_shortcut1 = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F1), self)
        info_shortcut1.activated.connect(self.show_project_info)
        
        info_shortcut2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+I"), self)
        info_shortcut2.activated.connect(self.show_project_info)
    
    def clone_current_item(self):
        """Clone the currently selected item based on what's selected."""
        if self.current_setup_id:
            self.clone_current_setup()
        elif self.current_part_id:
            self.clone_current_part()
        elif self.current_project_id:
            self.clone_current_project()