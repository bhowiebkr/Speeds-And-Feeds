"""
Context menu operations mixin for navigation widget.

Provides context menus for projects, parts, and setups.
"""

from PySide6 import QtWidgets, QtCore, QtGui

from ...models.project import ProjectStatus


class ContextMenuOperationsMixin:
    """Mixin providing context menu operations for navigation widget."""
    
    def show_project_context_menu(self, position):
        """Show context menu for project combo box."""
        if self.project_combo.count() <= 1:  # Only has "Select Project..." option
            return
        
        menu = QtWidgets.QMenu(self)
        
        # Get current selection
        current_index = self.project_combo.currentIndex()
        has_project = current_index > 0 and self.current_project_id
        
        if has_project:
            project = self.project_manager.get_project(self.current_project_id)
            
            # Edit action
            edit_action = menu.addAction("✏️ Edit Project")
            edit_action.triggered.connect(self.edit_current_project)
            
            # Clone action
            clone_action = menu.addAction("📋 Clone Project")
            clone_action.triggered.connect(self.clone_current_project)
            
            menu.addSeparator()
            
            # Status actions
            status_menu = menu.addMenu("📊 Change Status")
            
            active_action = status_menu.addAction("🟢 Active")
            active_action.triggered.connect(lambda: self.change_project_status(ProjectStatus.ACTIVE))
            active_action.setEnabled(project.status != ProjectStatus.ACTIVE if project else True)
            
            completed_action = status_menu.addAction("✅ Completed")
            completed_action.triggered.connect(lambda: self.change_project_status(ProjectStatus.COMPLETED))
            completed_action.setEnabled(project.status != ProjectStatus.COMPLETED if project else True)
            
            archived_action = status_menu.addAction("📁 Archived")
            archived_action.triggered.connect(lambda: self.archive_current_project)
            archived_action.setEnabled(project.status != ProjectStatus.ARCHIVED if project else True)
            
            menu.addSeparator()
            
            # Info action
            info_action = menu.addAction("ℹ️ Project Info")
            info_action.triggered.connect(self.show_project_info)
            
            menu.addSeparator()
            
            # Delete action
            delete_action = menu.addAction("🗑️ Delete Project")
            delete_action.triggered.connect(self.delete_current_project)
            
            # Make delete action red
            delete_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        
        # New project action (always available)
        menu.addSeparator()
        new_action = menu.addAction("➕ New Project")
        new_action.triggered.connect(self.new_project)
        
        # Show menu
        global_pos = self.project_combo.mapToGlobal(position)
        menu.exec(global_pos)
    
    def show_part_context_menu(self, position):
        """Show context menu for part combo box."""
        if not self.current_project_id:
            return
        
        menu = QtWidgets.QMenu(self)
        
        # Get current selection
        current_index = self.part_combo.currentIndex()
        has_part = current_index > 0 and self.current_part_id
        
        if has_part:
            # Edit action
            edit_action = menu.addAction("✏️ Edit Part")
            edit_action.triggered.connect(self.edit_current_part)
            
            # Clone action
            clone_action = menu.addAction("📋 Clone Part")
            clone_action.triggered.connect(self.clone_current_part)
            
            menu.addSeparator()
            
            # Delete action
            delete_action = menu.addAction("🗑️ Delete Part")
            delete_action.triggered.connect(self.delete_current_part)
            
            menu.addSeparator()
        
        # New part action (available when project is selected)
        new_action = menu.addAction("➕ New Part")
        new_action.triggered.connect(self.new_part)
        
        # Show menu
        global_pos = self.part_combo.mapToGlobal(position)
        menu.exec(global_pos)
    
    def show_setup_context_menu(self, position):
        """Show context menu for setup combo box."""
        if not self.current_project_id or not self.current_part_id:
            return
        
        menu = QtWidgets.QMenu(self)
        
        # Get current selection
        current_index = self.setup_combo.currentIndex()
        has_setup = current_index > 0 and self.current_setup_id
        
        if has_setup:
            # Edit action
            edit_action = menu.addAction("✏️ Edit Setup")
            edit_action.triggered.connect(self.edit_current_setup)
            
            # Clone action
            clone_action = menu.addAction("📋 Clone Setup")
            clone_action.triggered.connect(self.clone_current_setup)
            
            menu.addSeparator()
            
            # Delete action
            delete_action = menu.addAction("🗑️ Delete Setup")
            delete_action.triggered.connect(self.delete_current_setup)
            
            menu.addSeparator()
        
        # New setup action (available when part is selected)
        new_action = menu.addAction("➕ New Setup")
        new_action.triggered.connect(self.new_setup)
        
        # Show menu
        global_pos = self.setup_combo.mapToGlobal(position)
        menu.exec(global_pos)
    
    def archive_current_project(self):
        """Archive the current project (set status to ARCHIVED)."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found.")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self,
            "Archive Project",
            f"Are you sure you want to archive the project '{project.name}'?\n\n"
            f"Archived projects are moved out of the active workflow but remain accessible.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.change_project_status(ProjectStatus.ARCHIVED)
    
    def change_project_status(self, new_status: ProjectStatus):
        """Change the status of the current project."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found.")
            return
        
        # Update status
        old_status = project.status
        project.status = new_status
        
        if self.project_manager.update_project(project):
            self.refresh_projects()
            
            # Status change messages
            status_names = {
                ProjectStatus.ACTIVE: "Active",
                ProjectStatus.COMPLETED: "Completed", 
                ProjectStatus.ARCHIVED: "Archived"
            }
            
            QtWidgets.QMessageBox.information(
                self,
                "Status Updated",
                f"Project '{project.name}' status changed from "
                f"{status_names.get(old_status, 'Unknown')} to {status_names.get(new_status, 'Unknown')}."
            )
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to update project status.")
    
    def show_project_info(self):
        """Show detailed information about the current project."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found.")
            return
        
        # Gather project statistics
        parts = self.project_manager.get_parts(self.current_project_id)
        total_setups = 0
        total_tools = 0
        
        for part in parts:
            setups = self.project_manager.get_setups(self.current_project_id, part.id)
            total_setups += len(setups)
            
            for setup in setups:
                tool_assignments = self.project_manager.get_tool_assignments(
                    self.current_project_id, part.id, setup.id
                )
                total_tools += len(tool_assignments)
        
        # Status display
        status_map = {
            ProjectStatus.ACTIVE: "🟢 Active",
            ProjectStatus.COMPLETED: "✅ Completed",
            ProjectStatus.ARCHIVED: "📁 Archived"
        }
        status_text = status_map.get(project.status, "⚪ Unknown")
        
        # Create info dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Project Info: {project.name}")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Project details
        info_text = f"""
        <h2>{project.name}</h2>
        <p><strong>Status:</strong> {status_text}</p>
        <p><strong>Description:</strong> {project.description or 'No description'}</p>
        
        <h3>Statistics</h3>
        <ul>
            <li><strong>Parts:</strong> {len(parts)}</li>
            <li><strong>Setups:</strong> {total_setups}</li>
            <li><strong>Tool Assignments:</strong> {total_tools}</li>
        </ul>
        
        <h3>Project Structure</h3>
        """
        
        if parts:
            info_text += "<ul>"
            for part in parts[:10]:  # Limit to first 10 parts
                setups = self.project_manager.get_setups(self.current_project_id, part.id)
                info_text += f"<li><strong>{part.name}</strong> ({len(setups)} setup{'s' if len(setups) != 1 else ''})</li>"
            
            if len(parts) > 10:
                info_text += f"<li><em>... and {len(parts) - 10} more parts</em></li>"
            
            info_text += "</ul>"
        else:
            info_text += "<p><em>No parts in this project</em></p>"
        
        info_label = QtWidgets.QLabel(info_text)
        info_label.setTextFormat(QtCore.Qt.RichText)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Close button
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()