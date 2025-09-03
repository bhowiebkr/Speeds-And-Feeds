"""
Project Manager Widget for the Speeds and Feeds Calculator.

Provides a comprehensive interface for managing projects and organizing
tools into project-based collections.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import List, Optional
from datetime import datetime

from ..models.project import ProjectManager, Project, ProjectStatus
from ..models.tool_library import ToolLibrary
from .project_tools import ProjectToolsDialog


class ProjectListWidget(QtWidgets.QTableWidget):
    """Custom table widget for displaying projects."""
    
    projectSelected = QtCore.Signal(Project)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        """Setup the project table."""
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Name", "Customer", "Status", "Tools", "Modified"
        ])
        
        # Set column widths
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # Name
        header.resizeSection(1, 150)  # Customer
        header.resizeSection(2, 80)   # Status
        header.resizeSection(3, 60)   # Tools
        
        # Configure table
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Connect selection
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def populate_projects(self, projects: List[Project]):
        """Populate table with project data."""
        self.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            # Name
            name_item = QtWidgets.QTableWidgetItem(project.name)
            name_item.setData(QtCore.Qt.UserRole, project)
            self.setItem(row, 0, name_item)
            
            # Customer
            customer_item = QtWidgets.QTableWidgetItem(project.customer_name)
            self.setItem(row, 1, customer_item)
            
            # Status
            status_item = QtWidgets.QTableWidgetItem(project.status.value.title())
            status_color = self.get_status_color(project.status)
            status_item.setBackground(QtGui.QColor(status_color))
            self.setItem(row, 2, status_item)
            
            # Tool count
            tool_count_item = QtWidgets.QTableWidgetItem(str(project.get_tool_count()))
            tool_count_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, 3, tool_count_item)
            
            # Modified date
            try:
                modified_date = datetime.fromisoformat(project.date_modified)
                date_str = modified_date.strftime("%m/%d/%Y")
            except:
                date_str = "Unknown"
            modified_item = QtWidgets.QTableWidgetItem(date_str)
            self.setItem(row, 4, modified_item)
    
    def get_status_color(self, status: ProjectStatus) -> str:
        """Get color for project status."""
        colors = {
            ProjectStatus.ACTIVE: "#4CAF50",      # Green
            ProjectStatus.COMPLETED: "#2196F3",   # Blue  
            ProjectStatus.ARCHIVED: "#666666"     # Gray
        }
        return colors.get(status, "#ffffff")
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_items = self.selectedItems()
        if selected_items:
            project = selected_items[0].data(QtCore.Qt.UserRole)
            if project:
                self.projectSelected.emit(project)
    
    def get_selected_project(self) -> Optional[Project]:
        """Get currently selected project."""
        selected_items = self.selectedItems()
        if selected_items:
            return selected_items[0].data(QtCore.Qt.UserRole)
        return None


class ProjectEditorDialog(QtWidgets.QDialog):
    """Dialog for creating/editing projects."""
    
    def __init__(self, project: Optional[Project] = None, parent=None):
        super().__init__(parent)
        self.project = project
        self.is_edit_mode = project is not None
        
        self.setWindowTitle("Edit Project" if self.is_edit_mode else "New Project")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def setup_ui(self):
        """Setup the editor UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form layout
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(10)
        
        # Project fields
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter project name")
        
        self.customer_input = QtWidgets.QLineEdit()
        self.customer_input.setPlaceholderText("Enter customer name (optional)")
        
        self.description_input = QtWidgets.QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Enter project description (optional)")
        
        self.status_combo = QtWidgets.QComboBox()
        for status in ProjectStatus:
            self.status_combo.addItem(status.value.title(), status)
        
        self.notes_input = QtWidgets.QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Additional notes (optional)")
        
        # Add to form
        form.addRow("Project Name*:", self.name_input)
        form.addRow("Customer:", self.customer_input)
        form.addRow("Description:", self.description_input)
        form.addRow("Status:", self.status_combo)
        form.addRow("Notes:", self.notes_input)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Save Project")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # Assemble layout
        layout.addLayout(form)
        layout.addLayout(button_layout)
    
    def populate_fields(self):
        """Populate fields with existing project data."""
        if not self.project:
            return
        
        self.name_input.setText(self.project.name)
        self.customer_input.setText(self.project.customer_name)
        self.description_input.setPlainText(self.project.description)
        self.notes_input.setPlainText(self.project.notes)
        
        # Set status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.project.status:
                self.status_combo.setCurrentIndex(i)
                break
    
    def get_project_data(self) -> dict:
        """Get project data from form."""
        return {
            'name': self.name_input.text().strip(),
            'customer_name': self.customer_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'status': self.status_combo.currentData(),
            'notes': self.notes_input.toPlainText().strip()
        }
    
    def accept(self):
        """Validate and accept the dialog."""
        if not self.name_input.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation Error", 
                                        "Project name is required.")
            return
        
        super().accept()


class ProjectManagerDialog(QtWidgets.QDialog):
    """Main project management dialog."""
    
    projectsModified = QtCore.Signal()
    
    def __init__(self, tool_library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.tool_library = tool_library
        self.project_manager = tool_library.project_manager
        self.current_project: Optional[Project] = None
        
        self.setWindowTitle("📁 Project Manager")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.refresh_projects()
    
    def setup_ui(self):
        """Setup the main UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header
        header_layout = QtWidgets.QHBoxLayout()
        
        title_label = QtWidgets.QLabel("📁 Project Manager")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        
        # Action buttons
        self.new_project_btn = QtWidgets.QPushButton("➕ New Project")
        self.new_project_btn.clicked.connect(self.new_project)
        
        self.edit_project_btn = QtWidgets.QPushButton("✏️ Edit")
        self.edit_project_btn.setEnabled(False)
        self.edit_project_btn.clicked.connect(self.edit_project)
        
        self.clone_project_btn = QtWidgets.QPushButton("📋 Clone")
        self.clone_project_btn.setEnabled(False)
        self.clone_project_btn.clicked.connect(self.clone_project)
        
        self.delete_project_btn = QtWidgets.QPushButton("🗑️ Delete")
        self.delete_project_btn.setEnabled(False)
        self.delete_project_btn.clicked.connect(self.delete_project)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.new_project_btn)
        header_layout.addWidget(self.edit_project_btn)
        header_layout.addWidget(self.clone_project_btn)
        header_layout.addWidget(self.delete_project_btn)
        
        # Search and filters
        search_layout = QtWidgets.QHBoxLayout()
        
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search projects...")
        self.search_input.textChanged.connect(self.filter_projects)
        
        self.status_filter = QtWidgets.QComboBox()
        self.status_filter.addItem("All Statuses", None)
        for status in ProjectStatus:
            self.status_filter.addItem(status.value.title(), status)
        self.status_filter.currentTextChanged.connect(self.filter_projects)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(QtWidgets.QLabel("Status:"))
        search_layout.addWidget(self.status_filter)
        search_layout.addStretch()
        
        # Project list
        self.project_list = ProjectListWidget()
        self.project_list.projectSelected.connect(self.on_project_selected)
        
        # Project details panel
        details_group = QtWidgets.QGroupBox("Project Details")
        details_layout = QtWidgets.QVBoxLayout(details_group)
        
        self.details_label = QtWidgets.QLabel("Select a project to view details")
        self.details_label.setAlignment(QtCore.Qt.AlignCenter)
        self.details_label.setStyleSheet("color: #888888; font-style: italic;")
        details_layout.addWidget(self.details_label)
        
        # Action buttons for selected project
        project_actions_layout = QtWidgets.QHBoxLayout()
        
        self.manage_tools_btn = QtWidgets.QPushButton("🔧 Manage Tools")
        self.manage_tools_btn.setEnabled(False)
        self.manage_tools_btn.clicked.connect(self.manage_project_tools)
        
        self.archive_btn = QtWidgets.QPushButton("📦 Archive")
        self.archive_btn.setEnabled(False)
        self.archive_btn.clicked.connect(self.archive_project)
        
        project_actions_layout.addWidget(self.manage_tools_btn)
        project_actions_layout.addWidget(self.archive_btn)
        project_actions_layout.addStretch()
        
        # Dialog buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        # Assemble layout
        layout.addLayout(header_layout)
        layout.addLayout(search_layout)
        layout.addWidget(self.project_list, 1)  # Take most space
        layout.addWidget(details_group)
        layout.addLayout(project_actions_layout)
        layout.addLayout(button_layout)
    
    def refresh_projects(self):
        """Refresh the project list."""
        projects = self.project_manager.get_all_projects()
        self.project_list.populate_projects(projects)
    
    def filter_projects(self):
        """Filter projects based on search and status."""
        search_query = self.search_input.text().strip()
        status_filter = self.status_filter.currentData()
        
        # Get all projects
        all_projects = self.project_manager.get_all_projects()
        
        # Apply filters
        filtered_projects = all_projects
        
        # Search filter
        if search_query:
            filtered_projects = self.project_manager.search_projects(search_query)
        
        # Status filter
        if status_filter:
            filtered_projects = [p for p in filtered_projects if p.status == status_filter]
        
        self.project_list.populate_projects(filtered_projects)
    
    def on_project_selected(self, project: Project):
        """Handle project selection."""
        self.current_project = project
        
        # Enable buttons
        self.edit_project_btn.setEnabled(True)
        self.clone_project_btn.setEnabled(True)
        self.delete_project_btn.setEnabled(True)
        self.manage_tools_btn.setEnabled(True)
        self.archive_btn.setEnabled(project.status != ProjectStatus.ARCHIVED)
        
        # Update details
        self.update_project_details(project)
    
    def update_project_details(self, project: Project):
        """Update the project details panel."""
        details = f"""
        <b>Name:</b> {project.name}<br>
        <b>Customer:</b> {project.customer_name or 'Not specified'}<br>
        <b>Status:</b> {project.status.value.title()}<br>
        <b>Tools:</b> {project.get_tool_count()}<br>
        <b>Created:</b> {self.format_date(project.date_created)}<br>
        <b>Modified:</b> {self.format_date(project.date_modified)}<br>
        """
        
        if project.description:
            details += f"<b>Description:</b> {project.description}<br>"
        
        if project.notes:
            details += f"<b>Notes:</b> {project.notes}"
        
        self.details_label.setText(details)
        self.details_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.details_label.setStyleSheet("color: #ffffff;")
    
    def format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%m/%d/%Y %I:%M %p")
        except:
            return "Unknown"
    
    def new_project(self):
        """Create a new project."""
        dialog = ProjectEditorDialog(parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            project_data = dialog.get_project_data()
            project = self.project_manager.create_project(**project_data)
            if project:
                self.refresh_projects()
                self.projectsModified.emit()
                QtWidgets.QMessageBox.information(self, "Success", 
                                                f"Project '{project.name}' created successfully!")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to create project.")
    
    def edit_project(self):
        """Edit the selected project."""
        if not self.current_project:
            return
        
        dialog = ProjectEditorDialog(self.current_project, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            project_data = dialog.get_project_data()
            
            # Update project
            for key, value in project_data.items():
                setattr(self.current_project, key, value)
            
            if self.project_manager.update_project(self.current_project):
                self.refresh_projects()
                self.update_project_details(self.current_project)
                self.projectsModified.emit()
                QtWidgets.QMessageBox.information(self, "Success", "Project updated successfully!")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to update project.")
    
    def clone_project(self):
        """Clone the selected project."""
        if not self.current_project:
            return
        
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Clone Project", 
            f"Enter name for cloned project:",
            text=f"{self.current_project.name} (Copy)"
        )
        
        if ok and name.strip():
            cloned_project = self.project_manager.clone_project(self.current_project.id, name.strip())
            if cloned_project:
                self.refresh_projects()
                self.projectsModified.emit()
                QtWidgets.QMessageBox.information(self, "Success", 
                                                f"Project cloned as '{name.strip()}'!")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to clone project.")
    
    def delete_project(self):
        """Delete the selected project."""
        if not self.current_project:
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Project",
            f"Are you sure you want to delete project '{self.current_project.name}'?\n"
            f"This will remove the project and all its tool associations.\n\n"
            f"This action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.delete_project(self.current_project.id):
                self.refresh_projects()
                self.projectsModified.emit()
                self.current_project = None
                self.details_label.setText("Select a project to view details")
                self.details_label.setAlignment(QtCore.Qt.AlignCenter)
                self.details_label.setStyleSheet("color: #888888; font-style: italic;")
                
                # Disable buttons
                self.edit_project_btn.setEnabled(False)
                self.clone_project_btn.setEnabled(False)
                self.delete_project_btn.setEnabled(False)
                self.manage_tools_btn.setEnabled(False)
                self.archive_btn.setEnabled(False)
                
                QtWidgets.QMessageBox.information(self, "Success", "Project deleted successfully!")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to delete project.")
    
    def archive_project(self):
        """Archive the selected project."""
        if not self.current_project:
            return
        
        if self.project_manager.archive_project(self.current_project.id):
            self.current_project.status = ProjectStatus.ARCHIVED
            self.refresh_projects()
            self.update_project_details(self.current_project)
            self.archive_btn.setEnabled(False)
            self.projectsModified.emit()
            QtWidgets.QMessageBox.information(self, "Success", "Project archived successfully!")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Failed to archive project.")
    
    def manage_project_tools(self):
        """Open project tool management interface."""
        if not self.current_project:
            return
        
        dialog = ProjectToolsDialog(self.current_project, self.tool_library, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Refresh project list to show updated tool counts
            self.refresh_projects()
            if self.current_project:
                self.update_project_details(self.current_project)