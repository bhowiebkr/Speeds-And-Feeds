"""
Clone operations mixin for navigation widget.

Provides clone/duplicate functionality for projects, parts, and setups.
"""

from PySide6 import QtWidgets, QtCore
import copy
from typing import Optional

from ...models.project import ProjectStatus


class CloneOperationsMixin:
    """Mixin providing clone operations for navigation widget."""
    
    def clone_current_item(self):
        """Clone the currently selected item based on what's selected."""
        if self.current_setup_id:
            self.clone_current_setup()
        elif self.current_part_id:
            self.clone_current_part()
        elif self.current_project_id:
            self.clone_current_project()
        else:
            QtWidgets.QMessageBox.information(self, "Clone Item", "Please select an item to clone.")
    
    def clone_current_project(self):
        """Clone the current project with all its parts and setups."""
        if not self.current_project_id:
            return
        
        project = self.project_manager.get_project(self.current_project_id)
        if not project:
            QtWidgets.QMessageBox.warning(self, "Error", "Project not found.")
            return
        
        # Get new name from user
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Clone Project",
            f"Enter name for the cloned project:",
            text=f"{project.name} - Copy"
        )
        
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # Check if name already exists
        existing_projects = self.project_manager.get_all_projects()
        if any(p.name.lower() == new_name.lower() for p in existing_projects):
            QtWidgets.QMessageBox.warning(
                self,
                "Name Conflict",
                f"A project named '{new_name}' already exists. Please choose a different name."
            )
            return
        
        try:
            # Clone the project
            new_project_id = self._clone_project_deep(self.current_project_id, new_name)
            
            if new_project_id:
                self.refresh_projects()
                
                # Select the new project
                for i in range(1, self.project_combo.count()):  # Skip "Select Project..." at index 0
                    if self.project_combo.itemData(i) == new_project_id:
                        self.project_combo.setCurrentIndex(i)
                        break
                
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"Project '{new_name}' cloned successfully with all parts and setups."
                )
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to clone project.")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to clone project: {str(e)}")
    
    def clone_current_part(self):
        """Clone the current part with all its setups."""
        if not self.current_project_id or not self.current_part_id:
            return
        
        part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
        if not part:
            QtWidgets.QMessageBox.warning(self, "Error", "Part not found.")
            return
        
        # Get new name from user
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Clone Part",
            f"Enter name for the cloned part:",
            text=f"{part.name} - Copy"
        )
        
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # Check if name already exists in this project
        existing_parts = self.project_manager.get_parts(self.current_project_id)
        if any(p.name.lower() == new_name.lower() for p in existing_parts):
            QtWidgets.QMessageBox.warning(
                self,
                "Name Conflict",
                f"A part named '{new_name}' already exists in this project. Please choose a different name."
            )
            return
        
        try:
            # Clone the part
            new_part_id = self._clone_part_deep(self.current_project_id, self.current_part_id, new_name)
            
            if new_part_id:
                self.refresh_parts()
                
                # Select the new part
                for i in range(1, self.part_combo.count()):  # Skip "Select Part..." at index 0
                    if self.part_combo.itemData(i) == new_part_id:
                        self.part_combo.setCurrentIndex(i)
                        break
                
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"Part '{new_name}' cloned successfully with all setups."
                )
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to clone part.")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to clone part: {str(e)}")
    
    def clone_current_setup(self):
        """Clone the current setup with all its tool assignments."""
        if not self.current_project_id or not self.current_part_id or not self.current_setup_id:
            return
        
        setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
        if not setup:
            QtWidgets.QMessageBox.warning(self, "Error", "Setup not found.")
            return
        
        # Get new name from user
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Clone Setup",
            f"Enter name for the cloned setup:",
            text=f"{setup.name} - Copy"
        )
        
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # Check if name already exists in this part
        existing_setups = self.project_manager.get_setups(self.current_project_id, self.current_part_id)
        if any(s.name.lower() == new_name.lower() for s in existing_setups):
            QtWidgets.QMessageBox.warning(
                self,
                "Name Conflict",
                f"A setup named '{new_name}' already exists in this part. Please choose a different name."
            )
            return
        
        try:
            # Clone the setup
            new_setup_id = self._clone_setup_deep(
                self.current_project_id,
                self.current_part_id,
                self.current_setup_id,
                new_name
            )
            
            if new_setup_id:
                self.refresh_setups()
                
                # Select the new setup
                for i in range(1, self.setup_combo.count()):  # Skip "Select Setup..." at index 0
                    if self.setup_combo.itemData(i) == new_setup_id:
                        self.setup_combo.setCurrentIndex(i)
                        break
                
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"Setup '{new_name}' cloned successfully with all tool assignments."
                )
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Failed to clone setup.")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to clone setup: {str(e)}")
    
    def _clone_project_deep(self, project_id: str, new_name: str) -> Optional[str]:
        """Clone a project with all its parts and setups."""
        # Get the original project
        project = self.project_manager.get_project(project_id)
        if not project:
            return None
        
        # Create new project
        new_project_id = self.project_manager.create_project(
            new_name,
            project.description,
            ProjectStatus.ACTIVE  # New cloned projects are active by default
        )
        
        if not new_project_id:
            return None
        
        # Clone all parts and their setups
        parts = self.project_manager.get_parts(project_id)
        for part in parts:
            self._clone_part_deep(new_project_id, part.id, part.name, original_project_id=project_id)
        
        return new_project_id
    
    def _clone_part_deep(self, project_id: str, part_id: str, new_name: str, original_project_id: Optional[str] = None) -> Optional[str]:
        """Clone a part with all its setups."""
        # Use original_project_id if provided (for cross-project cloning), otherwise use project_id
        source_project_id = original_project_id or project_id
        
        # Get the original part
        part = self.project_manager.get_part(source_project_id, part_id)
        if not part:
            return None
        
        # Create new part
        new_part_id = self.project_manager.create_part(
            project_id,
            new_name,
            part.description,
            part.material
        )
        
        if not new_part_id:
            return None
        
        # Clone all setups
        setups = self.project_manager.get_setups(source_project_id, part_id)
        for setup in setups:
            self._clone_setup_deep(
                project_id,
                new_part_id,
                setup.id,
                setup.name,
                original_project_id=source_project_id,
                original_part_id=part_id
            )
        
        return new_part_id
    
    def _clone_setup_deep(self, project_id: str, part_id: str, setup_id: str, new_name: str,
                         original_project_id: Optional[str] = None, original_part_id: Optional[str] = None) -> Optional[str]:
        """Clone a setup with all its tool assignments."""
        # Use original IDs if provided (for cross-project/part cloning), otherwise use current IDs
        source_project_id = original_project_id or project_id
        source_part_id = original_part_id or part_id
        
        # Get the original setup
        setup = self.project_manager.get_setup(source_project_id, source_part_id, setup_id)
        if not setup:
            return None
        
        # Create new setup
        new_setup_id = self.project_manager.create_setup(
            project_id,
            part_id,
            new_name,
            setup.description,
            setup.operation_type
        )
        
        if not new_setup_id:
            return None
        
        # Clone all tool assignments
        tool_assignments = self.project_manager.get_tool_assignments(source_project_id, source_part_id, setup_id)
        for assignment in tool_assignments:
            # Create a copy of the assignment for the new setup
            new_assignment = copy.deepcopy(assignment)
            new_assignment.setup_id = new_setup_id
            
            # Add the cloned assignment to the new setup
            self.project_manager.assign_tool_to_setup(
                project_id,
                part_id,
                new_setup_id,
                assignment.tool_id,
                new_assignment.notes
            )
        
        return new_setup_id