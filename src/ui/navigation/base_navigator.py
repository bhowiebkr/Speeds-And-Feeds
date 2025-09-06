"""
Base navigation widget with core combo box functionality.

Provides the foundational UI and selection logic for project navigation.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional

from ...models.project import ProjectManager, ProjectStatus


class BaseNavigationWidget(QtWidgets.QWidget):
    """Base navigation widget with cascading ComboBoxes for Project/Part/Setup selection."""
    
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
        self.setup_shortcuts()
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
        
        # Edit/Delete buttons for projects
        self.edit_project_btn = QtWidgets.QPushButton("✏️")
        self.edit_project_btn.clicked.connect(self.edit_current_project)
        self.edit_project_btn.setEnabled(False)
        self.edit_project_btn.setFixedSize(24, 24)
        self.edit_project_btn.setToolTip("Edit project")
        layout.addWidget(self.edit_project_btn)
        
        self.delete_project_btn = QtWidgets.QPushButton("🗑️")
        self.delete_project_btn.clicked.connect(self.delete_current_project)
        self.delete_project_btn.setEnabled(False)
        self.delete_project_btn.setFixedSize(24, 24)
        self.delete_project_btn.setToolTip("Delete project")
        layout.addWidget(self.delete_project_btn)
        
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
        
        # Edit/Delete buttons for parts
        self.edit_part_btn = QtWidgets.QPushButton("✏️")
        self.edit_part_btn.clicked.connect(self.edit_current_part)
        self.edit_part_btn.setEnabled(False)
        self.edit_part_btn.setFixedSize(24, 24)
        self.edit_part_btn.setToolTip("Edit part")
        layout.addWidget(self.edit_part_btn)
        
        self.delete_part_btn = QtWidgets.QPushButton("🗑️")
        self.delete_part_btn.clicked.connect(self.delete_current_part)
        self.delete_part_btn.setEnabled(False)
        self.delete_part_btn.setFixedSize(24, 24)
        self.delete_part_btn.setToolTip("Delete part")
        layout.addWidget(self.delete_part_btn)
        
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
        layout.addWidget(self.new_setup_btn)
        
        # Edit/Delete buttons for setups
        self.edit_setup_btn = QtWidgets.QPushButton("✏️")
        self.edit_setup_btn.clicked.connect(self.edit_current_setup)
        self.edit_setup_btn.setEnabled(False)
        self.edit_setup_btn.setFixedSize(24, 24)
        self.edit_setup_btn.setToolTip("Edit setup")
        layout.addWidget(self.edit_setup_btn)
        
        self.delete_setup_btn = QtWidgets.QPushButton("🗑️")
        self.delete_setup_btn.clicked.connect(self.delete_current_setup)
        self.delete_setup_btn.setEnabled(False)
        self.delete_setup_btn.setFixedSize(24, 24)
        self.delete_setup_btn.setToolTip("Delete setup")
        layout.addWidget(self.delete_setup_btn)
        
        # Add spacer to push everything to the left
        layout.addStretch()
    
    def refresh_projects(self):
        """Refresh the project combo box."""
        self.project_combo.blockSignals(True)
        current_text = self.project_combo.currentText()
        self.project_combo.clear()
        
        # Add default option
        self.project_combo.addItem("Select Project...")
        
        projects = self.project_manager.get_all_projects()
        for project in projects:
            status_prefix = self._get_status_prefix(project.status)
            self.project_combo.addItem(f"{status_prefix} {project.name}", project.id)
        
        # Restore selection if possible
        index = self.project_combo.findText(current_text)
        if index >= 0:
            self.project_combo.setCurrentIndex(index)
        
        self.project_combo.blockSignals(False)
        self.on_project_changed()
    
    def refresh_parts(self):
        """Refresh the part combo box based on selected project."""
        self.part_combo.blockSignals(True)
        current_text = self.part_combo.currentText()
        self.part_combo.clear()
        
        # Add default option
        self.part_combo.addItem("Select Part...")
        
        if self.current_project_id:
            parts = self.project_manager.get_parts(self.current_project_id)
            for part in parts:
                self.part_combo.addItem(part.name, part.id)
            
            # Restore selection if possible
            index = self.part_combo.findText(current_text)
            if index >= 0:
                self.part_combo.setCurrentIndex(index)
        
        self.part_combo.blockSignals(False)
        self.on_part_changed()
    
    def refresh_setups(self):
        """Refresh the setup combo box based on selected part."""
        self.setup_combo.blockSignals(True)
        current_text = self.setup_combo.currentText()
        self.setup_combo.clear()
        
        # Add default option
        self.setup_combo.addItem("Select Setup...")
        
        if self.current_project_id and self.current_part_id:
            setups = self.project_manager.get_setups(self.current_project_id, self.current_part_id)
            for setup in setups:
                self.setup_combo.addItem(setup.name, setup.id)
            
            # Restore selection if possible
            index = self.setup_combo.findText(current_text)
            if index >= 0:
                self.setup_combo.setCurrentIndex(index)
        
        self.setup_combo.blockSignals(False)
        self.on_setup_changed()
    
    def on_project_changed(self):
        """Handle project selection change."""
        current_index = self.project_combo.currentIndex()
        if current_index > 0:  # Skip "Select Project..." option
            self.current_project_id = self.project_combo.itemData(current_index)
        else:
            self.current_project_id = None
        
        self.refresh_parts()
        self.update_button_states()
        self.emit_selection_changed()
    
    def on_part_changed(self):
        """Handle part selection change."""
        current_index = self.part_combo.currentIndex()
        if current_index > 0:  # Skip "Select Part..." option
            self.current_part_id = self.part_combo.itemData(current_index)
        else:
            self.current_part_id = None
        
        self.refresh_setups()
        self.update_button_states()
        self.emit_selection_changed()
    
    def on_setup_changed(self):
        """Handle setup selection change."""
        current_index = self.setup_combo.currentIndex()
        if current_index > 0:  # Skip "Select Setup..." option
            self.current_setup_id = self.setup_combo.itemData(current_index)
        else:
            self.current_setup_id = None
        
        self.update_button_states()
        self.emit_selection_changed()
    
    def emit_selection_changed(self):
        """Emit selection changed signal with current IDs."""
        project_id = self.current_project_id or ""
        part_id = self.current_part_id or ""
        setup_id = self.current_setup_id or ""
        
        self.selectionChanged.emit(project_id, part_id, setup_id)
        self.save_current_selection()
    
    def update_button_states(self):
        """Update the enabled state of edit/delete buttons based on current selection."""
        # Project buttons
        has_project = self.current_project_id is not None
        self.edit_project_btn.setEnabled(has_project)
        self.delete_project_btn.setEnabled(has_project)
        self.new_part_btn.setEnabled(has_project)
        
        # Part buttons
        has_part = self.current_part_id is not None
        self.edit_part_btn.setEnabled(has_part)
        self.delete_part_btn.setEnabled(has_part)
        self.new_setup_btn.setEnabled(has_part)
        
        # Setup buttons
        has_setup = self.current_setup_id is not None
        self.edit_setup_btn.setEnabled(has_setup)
        self.delete_setup_btn.setEnabled(has_setup)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # F2 for edit
        edit_shortcut = QtGui.QShortcut(QtGui.QKeySequence("F2"), self)
        edit_shortcut.activated.connect(self.edit_current_item)
        
        # Delete key for delete
        delete_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self.delete_current_item)
        
        # Ctrl+D for duplicate/clone
        clone_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+D"), self)
        clone_shortcut.activated.connect(self.clone_current_item)
        
        # Ctrl+N for new project
        new_project_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+N"), self)
        new_project_shortcut.activated.connect(self.new_project)
    
    def save_current_selection(self):
        """Save the current selection to settings."""
        self.settings.setValue("current_project_id", self.current_project_id or "")
        self.settings.setValue("current_part_id", self.current_part_id or "")
        self.settings.setValue("current_setup_id", self.current_setup_id or "")
    
    def restore_last_selection(self):
        """Restore the last saved selection from settings."""
        saved_project_id = self.settings.value("current_project_id", "")
        saved_part_id = self.settings.value("current_part_id", "")
        saved_setup_id = self.settings.value("current_setup_id", "")
        
        # Restore project selection
        if saved_project_id:
            for i in range(1, self.project_combo.count()):  # Skip "Select Project..." at index 0
                if self.project_combo.itemData(i) == saved_project_id:
                    self.project_combo.setCurrentIndex(i)
                    break
        
        # Restore part selection (after project is set)
        if saved_part_id and self.current_project_id == saved_project_id:
            for i in range(1, self.part_combo.count()):  # Skip "Select Part..." at index 0
                if self.part_combo.itemData(i) == saved_part_id:
                    self.part_combo.setCurrentIndex(i)
                    break
        
        # Restore setup selection (after part is set)
        if saved_setup_id and self.current_part_id == saved_part_id:
            for i in range(1, self.setup_combo.count()):  # Skip "Select Setup..." at index 0
                if self.setup_combo.itemData(i) == saved_setup_id:
                    self.setup_combo.setCurrentIndex(i)
                    break
    
    def _get_status_prefix(self, status: ProjectStatus) -> str:
        """Get the status prefix emoji for display."""
        status_map = {
            ProjectStatus.ACTIVE: "🟢",
            ProjectStatus.COMPLETED: "✅",
            ProjectStatus.ARCHIVED: "📁"
        }
        return status_map.get(status, "⚪")
    
    # These methods will be implemented by mixins or overridden in subclasses
    def show_project_context_menu(self, position):
        """Show context menu for project combo box."""
        pass
    
    def show_part_context_menu(self, position):
        """Show context menu for part combo box."""
        pass
    
    def show_setup_context_menu(self, position):
        """Show context menu for setup combo box."""
        pass
    
    def edit_current_item(self):
        """Edit the currently selected item."""
        pass
    
    def delete_current_item(self):
        """Delete the currently selected item."""
        pass
    
    def clone_current_item(self):
        """Clone the currently selected item."""
        pass
    
    def edit_current_project(self):
        """Edit the current project."""
        pass
    
    def edit_current_part(self):
        """Edit the current part."""
        pass
    
    def edit_current_setup(self):
        """Edit the current setup."""
        pass
    
    def delete_current_project(self):
        """Delete the current project."""
        pass
    
    def delete_current_part(self):
        """Delete the current part."""
        pass
    
    def delete_current_setup(self):
        """Delete the current setup."""
        pass
    
    def new_project(self):
        """Create a new project."""
        pass
    
    def new_part(self):
        """Create a new part."""
        pass
    
    def new_setup(self):
        """Create a new setup."""
        pass