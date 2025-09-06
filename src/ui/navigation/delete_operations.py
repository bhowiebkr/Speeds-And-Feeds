"""
Delete operations mixin for navigation widget.

Provides delete functionality for projects, parts, and setups.
"""

from PySide6 import QtWidgets, QtCore


class DeleteOperationsMixin:
    """Mixin providing delete operations for navigation widget."""
    
    def delete_current_item(self):
        """Delete the currently selected item based on what's selected."""
        if self.current_setup_id:
            self.delete_current_setup()
        elif self.current_part_id:
            self.delete_current_part()
        elif self.current_project_id:
            self.delete_current_project()
        else:
            QtWidgets.QMessageBox.information(self, "Delete Item", "Please select an item to delete.")
    
    def delete_current_project(self):
        """Delete the current project with confirmation."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found.")
            return
        
        # Count parts and setups for warning
        parts = self.project_manager.get_parts(self.current_project_id)
        total_setups = 0
        for part in parts:
            setups = self.project_manager.get_setups(self.current_project_id, part.id)
            total_setups += len(setups)
        
        # Create warning message
        warning_parts = []
        if len(parts) > 0:
            warning_parts.append(f"{len(parts)} part{'s' if len(parts) != 1 else ''}")
        if total_setups > 0:
            warning_parts.append(f"{total_setups} setup{'s' if total_setups != 1 else ''}")
        
        if warning_parts:
            warning_text = f"This project contains {' and '.join(warning_parts)}. "
        else:
            warning_text = ""
        
        # Show confirmation dialog
        reply = QtWidgets.QMessageBox.warning(
            self,
            "Delete Project",
            f"Are you sure you want to delete the project '{project.name}'?\n\n"
            f"{warning_text}All associated data will be permanently lost.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.delete_project(self.current_project_id):
                self.current_project_id = None
                self.current_part_id = None
                self.current_setup_id = None
                self.refresh_projects()
                QtWidgets.QMessageBox.information(self, "Success", f"Project '{project.name}' deleted successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to delete project.")
    
    def delete_current_part(self):
        """Delete the current part with confirmation."""
        if not self.current_project_id or not self.current_part_id:
            return
        
        part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
        if not part:
            QtWidgets.QMessageBox.warning(self, "Error", "Part not found.")
            return
        
        # Count setups for warning
        setups = self.project_manager.get_setups(self.current_project_id, self.current_part_id)
        
        # Create warning message
        if len(setups) > 0:
            warning_text = f"This part contains {len(setups)} setup{'s' if len(setups) != 1 else ''}. "
        else:
            warning_text = ""
        
        # Show confirmation dialog
        reply = QtWidgets.QMessageBox.warning(
            self,
            "Delete Part",
            f"Are you sure you want to delete the part '{part.name}'?\n\n"
            f"{warning_text}All associated data will be permanently lost.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.delete_part(self.current_project_id, self.current_part_id):
                self.current_part_id = None
                self.current_setup_id = None
                self.refresh_parts()
                QtWidgets.QMessageBox.information(self, "Success", f"Part '{part.name}' deleted successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to delete part.")
    
    def delete_current_setup(self):
        """Delete the current setup with confirmation."""
        if not self.current_project_id or not self.current_part_id or not self.current_setup_id:
            return
        
        setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
        if not setup:
            QtWidgets.QMessageBox.warning(self, "Error", "Setup not found.")
            return
        
        # Count assigned tools for warning
        tool_assignments = self.project_manager.get_tool_assignments(
            self.current_project_id, self.current_part_id, self.current_setup_id
        )
        
        # Create warning message
        if len(tool_assignments) > 0:
            warning_text = f"This setup has {len(tool_assignments)} tool assignment{'s' if len(tool_assignments) != 1 else ''}. "
        else:
            warning_text = ""
        
        # Show confirmation dialog
        reply = QtWidgets.QMessageBox.warning(
            self,
            "Delete Setup",
            f"Are you sure you want to delete the setup '{setup.name}'?\n\n"
            f"{warning_text}All associated data will be permanently lost.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.project_manager.delete_setup(self.current_project_id, self.current_part_id, self.current_setup_id):
                self.current_setup_id = None
                self.refresh_setups()
                QtWidgets.QMessageBox.information(self, "Success", f"Setup '{setup.name}' deleted successfully.")
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to delete setup.")