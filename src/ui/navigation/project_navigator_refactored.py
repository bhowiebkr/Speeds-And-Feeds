"""
Refactored project navigation widget combining all operation mixins.

This is the main navigation widget that combines:
- Base navigation functionality
- Edit operations
- Delete operations  
- Clone operations
- Context menu operations
"""

from PySide6 import QtWidgets, QtCore
from typing import Optional

from ...models.project import ProjectManager
from .base_navigator import BaseNavigationWidget
from .edit_operations import EditOperationsMixin
from .delete_operations import DeleteOperationsMixin
from .clone_operations import CloneOperationsMixin
from .context_menu_operations import ContextMenuOperationsMixin


class ProjectNavigationWidget(
    BaseNavigationWidget,
    EditOperationsMixin,
    DeleteOperationsMixin,
    CloneOperationsMixin,
    ContextMenuOperationsMixin
):
    """Navigation widget with cascading ComboBoxes for Project/Part/Setup selection.
    
    Combines all navigation functionality through multiple mixins:
    - BaseNavigationWidget: Core combo box handling and UI
    - EditOperationsMixin: Edit/create operations for projects, parts, setups
    - DeleteOperationsMixin: Delete operations with confirmation dialogs
    - CloneOperationsMixin: Deep cloning operations preserving relationships
    - ContextMenuOperationsMixin: Right-click context menus with actions
    
    Features:
    - Cascading selection (Project → Part → Setup)
    - Edit/delete buttons with smart state management
    - Context menus with comprehensive actions
    - Keyboard shortcuts (F2=edit, Delete=delete, Ctrl+D=clone, Ctrl+N=new project)
    - Project status management with visual indicators
    - Deep cloning that preserves all relationships
    - Settings persistence for last selection
    - Confirmation dialogs for destructive operations
    """
    
    def __init__(self, project_manager: ProjectManager, parent=None):
        # Initialize base class (which will call __init__ on all mixins through MRO)
        super().__init__(project_manager, parent)
        
        # Restore last selection after everything is set up
        QtCore.QTimer.singleShot(100, self.restore_last_selection)
    
    def get_current_selection(self) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Get the current project, part, and setup IDs."""
        return self.current_project_id, self.current_part_id, self.current_setup_id
    
    def set_selection(self, project_id: Optional[str] = None, 
                     part_id: Optional[str] = None, 
                     setup_id: Optional[str] = None):
        """Set the current selection programmatically."""
        # Set project selection
        if project_id:
            for i in range(1, self.project_combo.count()):  # Skip "Select Project..." at index 0
                if self.project_combo.itemData(i) == project_id:
                    self.project_combo.setCurrentIndex(i)
                    break
        
        # Set part selection (after project is set)
        if part_id and self.current_project_id == project_id:
            for i in range(1, self.part_combo.count()):  # Skip "Select Part..." at index 0
                if self.part_combo.itemData(i) == part_id:
                    self.part_combo.setCurrentIndex(i)
                    break
        
        # Set setup selection (after part is set)
        if setup_id and self.current_part_id == part_id:
            for i in range(1, self.setup_combo.count()):  # Skip "Select Setup..." at index 0
                if self.setup_combo.itemData(i) == setup_id:
                    self.setup_combo.setCurrentIndex(i)
                    break
    
    def clear_selection(self):
        """Clear all selections."""
        self.project_combo.setCurrentIndex(0)  # "Select Project..."
        # This will trigger cascading clears through the signal handlers