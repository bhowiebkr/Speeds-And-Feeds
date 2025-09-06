"""
Integrated Project Tool Manager Widget for CNC ToolHub.

Provides a comprehensive interface for managing projects with hierarchical
organization (Projects → Parts → Setups) and integrated tool management.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import List, Optional, Dict, Set
import uuid

from ..models.project import ProjectManager, Project, Part, Setup, ProjectStatus
from ..models.tool_library import ToolLibrary, ToolSpecs
from .project_tools import ProjectToolWidget, ProjectToolListWidget as OriginalProjectToolListWidget, ToolNotesDialog


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
        
        # Info button
        self.info_btn = QtWidgets.QPushButton("ℹ️")
        self.info_btn.setFixedSize(28, 28)
        self.info_btn.setToolTip("Show project details")
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
        self.selectionChanged.emit(
            self.current_project_id or "",
            self.current_part_id or "",
            self.current_setup_id or ""
        )
    
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
        info_lines.append(f"<b>Status:</b> {project.status.value.title()}")
        
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
        dialog = ProjectEditorDialog(None, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            project = self.project_manager.create_project(**data)
            if project:
                self.refresh_projects()
                # Select the new project
                index = self.project_combo.findData(project.id)
                if index >= 0:
                    self.project_combo.setCurrentIndex(index)
    
    def new_part(self):
        """Create a new part."""
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


class ToolBrowserListWidget(QtWidgets.QListWidget):
    """Custom list widget that provides drag functionality for tools."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.setDefaultDropAction(QtCore.Qt.CopyAction)
    
    def startDrag(self, supportedActions):
        """Start drag operation with tool ID as mime data."""
        current_item = self.currentItem()
        if current_item:
            tool_id = current_item.data(QtCore.Qt.UserRole)
            if tool_id:
                drag = QtGui.QDrag(self)
                mimeData = QtCore.QMimeData()
                mimeData.setText(tool_id)
                drag.setMimeData(mimeData)
                
                # Create drag pixmap
                pixmap = QtGui.QPixmap(200, 30)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                painter.setPen(QtCore.Qt.white)
                painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, current_item.text())
                painter.end()
                drag.setPixmap(pixmap)
                
                drag.exec_(supportedActions)


class ToolBrowserWidget(QtWidgets.QWidget):
    """Tool browser widget for selecting tools to add to projects."""
    
    toolSelected = QtCore.Signal(str)  # tool_id
    
    def __init__(self, tool_library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.tool_library = tool_library
        self.setup_ui()
        self.refresh_tools()
    
    def setup_ui(self):
        """Setup the tool browser UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header with actions
        header_layout = QtWidgets.QHBoxLayout()
        
        header_label = QtWidgets.QLabel("Available Tools")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        self.add_favorites_btn = QtWidgets.QPushButton("⭐")
        self.add_favorites_btn.setFixedSize(28, 28)
        self.add_favorites_btn.setToolTip("Add all favorites to project")
        self.add_favorites_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        header_layout.addWidget(self.add_favorites_btn)
        
        layout.addLayout(header_layout)
        
        # Search and filters
        filter_layout = QtWidgets.QHBoxLayout()
        
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search tools...")
        self.search_input.textChanged.connect(self.filter_tools)
        filter_layout.addWidget(self.search_input)
        
        self.favorites_btn = QtWidgets.QPushButton("⭐ Favorites")
        self.favorites_btn.setCheckable(True)
        self.favorites_btn.clicked.connect(self.filter_tools)
        filter_layout.addWidget(self.favorites_btn)
        
        layout.addLayout(filter_layout)
        
        # Tool list
        self.tool_list = ToolBrowserListWidget()
        self.tool_list.itemDoubleClicked.connect(self.on_tool_double_clicked)
        layout.addWidget(self.tool_list, 1)  # Give it stretch to fill available space
        
        # Add button
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        
        self.add_button = QtWidgets.QPushButton("➕ Add Selected Tool")
        self.add_button.clicked.connect(self.add_selected_tool)
        self.add_button.setFixedHeight(36)
        self.add_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #4CAF50, stop:1 #388E3C);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #66BB6A, stop:1 #4CAF50);
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #388E3C, stop:1 #2E7D32);
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        button_layout.addWidget(self.add_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def refresh_tools(self):
        """Refresh the tool list."""
        self.tool_list.clear()
        tools = self.tool_library.get_all_tools()
        
        for tool in tools:
            item = QtWidgets.QListWidgetItem()
            item.setText(f"{tool.name} ({tool.diameter_mm:.3f}mm)")
            item.setData(QtCore.Qt.UserRole, tool.id)
            item.setToolTip(f"{tool.manufacturer} - {tool.name}\\n"
                          f"Diameter: {tool.diameter_mm:.3f}mm\\n"
                          f"Flutes: {tool.flutes}\\n"
                          f"Coating: {tool.coating}")
            
            # Add favorite indicator
            favorites = self.tool_library.get_user_favorites()
            if tool.id in favorites:
                item.setText(f"⭐ {item.text()}")
            
            self.tool_list.addItem(item)
    
    def filter_tools(self):
        """Filter tools based on search and favorites."""
        search_text = self.search_input.text().lower()
        favorites_only = self.favorites_btn.isChecked()
        
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            tool_id = item.data(QtCore.Qt.UserRole)
            tool = self.tool_library.get_tool(tool_id)
            
            if not tool:
                continue
            
            visible = True
            
            # Apply search filter
            if search_text:
                text_match = (
                    search_text in tool.name.lower() or
                    search_text in tool.manufacturer.lower() or
                    search_text in tool.coating.lower()
                )
                if not text_match:
                    visible = False
            
            # Apply favorites filter
            if favorites_only:
                user_favorites = self.tool_library.get_user_favorites()
                if tool.id not in user_favorites:
                    visible = False
            
            item.setHidden(not visible)
    
    def on_tool_double_clicked(self, item):
        """Handle tool double-click."""
        tool_id = item.data(QtCore.Qt.UserRole)
        if tool_id:
            self.toolSelected.emit(tool_id)
    
    def add_selected_tool(self):
        """Add currently selected tool."""
        current_item = self.tool_list.currentItem()
        if current_item:
            tool_id = current_item.data(QtCore.Qt.UserRole)
            if tool_id:
                self.toolSelected.emit(tool_id)


class ProjectToolsDropListWidget(QtWidgets.QListWidget):
    """Custom list widget that accepts tool drops."""
    
    toolDropped = QtCore.Signal(str)  # tool_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.setDefaultDropAction(QtCore.Qt.CopyAction)
    
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop events."""
        if event.mimeData().hasText():
            tool_id = event.mimeData().text()
            self.toolDropped.emit(tool_id)
            event.acceptProposedAction()
        else:
            event.ignore()


class EnhancedProjectToolListWidget(OriginalProjectToolListWidget):
    """Enhanced project tool list widget with drag-and-drop support."""
    
    toolDropped = QtCore.Signal(str)  # tool_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Enable drop functionality
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.setDefaultDropAction(QtCore.Qt.CopyAction)
    
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop events."""
        if event.mimeData().hasText():
            tool_id = event.mimeData().text()
            self.toolDropped.emit(tool_id)
            event.acceptProposedAction()
        else:
            event.ignore()


class ProjectToolsWidget(QtWidgets.QWidget):
    """Widget for displaying and managing tools at current selection level."""
    
    toolRemoved = QtCore.Signal(str)  # tool_id
    toolsChanged = QtCore.Signal()  # Signal when tools are added/removed
    
    def __init__(self, tool_library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.tool_library = tool_library
        self.project_manager: Optional[ProjectManager] = None
        self.current_project_id: Optional[str] = None
        self.current_part_id: Optional[str] = None
        self.current_setup_id: Optional[str] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the project tools UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header with actions
        header_layout = QtWidgets.QHBoxLayout()
        
        self.header_label = QtWidgets.QLabel("Project Tools")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.header_label)
        
        header_layout.addStretch()
        
        self.copy_tools_btn = QtWidgets.QPushButton("📋")
        self.copy_tools_btn.setFixedSize(28, 28)
        self.copy_tools_btn.setToolTip("Copy tools from another project")
        self.copy_tools_btn.clicked.connect(self.copy_tools_from)
        self.copy_tools_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        header_layout.addWidget(self.copy_tools_btn)
        
        self.export_btn = QtWidgets.QPushButton("📄")
        self.export_btn.setFixedSize(28, 28)
        self.export_btn.setToolTip("Export tool list")
        self.export_btn.clicked.connect(self.export_tool_list)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Tools list - use the rich original widget with drop functionality
        self.tools_list = EnhancedProjectToolListWidget()
        self.tools_list.toolDropped.connect(self.add_tool_from_drop)
        self.tools_list.toolQuantityChanged.connect(self.update_tool_quantity_in_project)
        self.tools_list.toolNotesChanged.connect(self.update_tool_notes_in_project)
        layout.addWidget(self.tools_list, 1)  # Give it stretch to fill available space
        
        # Actions
        actions_layout = QtWidgets.QHBoxLayout()
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(0, 8, 0, 0)
        
        self.remove_btn = QtWidgets.QPushButton("🗑️ Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_tool)
        self.remove_btn.setFixedHeight(36)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #f44336, stop:1 #d32f2f);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #ff5722, stop:1 #f44336);
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #d32f2f, stop:1 #b71c1c);
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        actions_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QtWidgets.QPushButton("🧹 Clear All")
        self.clear_btn.clicked.connect(self.clear_all_tools)
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #FF9800, stop:1 #F57C00);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #FFB74D, stop:1 #FF9800);
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #F57C00, stop:1 #E65100);
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        actions_layout.addWidget(self.clear_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
    
    def set_context(self, project_manager: ProjectManager, project_id: str, part_id: str, setup_id: str):
        """Set the current context for tool display."""
        self.project_manager = project_manager
        self.current_project_id = project_id
        self.current_part_id = part_id
        self.current_setup_id = setup_id
        self.refresh_tools()
    
    def refresh_tools(self):
        """Refresh the tools list."""
        self.tools_list.clear()
        
        if not self.project_manager or not self.current_project_id:
            self.header_label.setText("Project Tools")
            return
        
        tools = self.get_current_tools()
        
        # Update header based on context
        if self.current_setup_id:
            self.header_label.setText("Setup Tools")
        elif self.current_part_id:
            self.header_label.setText("Part Tools")
        else:
            self.header_label.setText("Project Tools")
        
        # Use the rich tool widget formatting
        for tool_assoc in tools:
            tool = self.tool_library.get_tool(tool_assoc.tool_id)
            if tool:
                self.tools_list.add_tool_association(tool, tool_assoc)
    
    def get_current_tools(self):
        """Get tools for current context."""
        if self.current_setup_id:
            setup = self.project_manager.get_setup(self.current_project_id, self.current_part_id, self.current_setup_id)
            return setup.tools if setup else []
        elif self.current_part_id:
            part = self.project_manager.get_part(self.current_project_id, self.current_part_id)
            return part.tools if part else []
        else:
            project = self.project_manager.get_project(self.current_project_id)
            return project.tools if project else []
    
    def add_tool(self, tool_id: str):
        """Add a tool to current context."""
        if not self.project_manager:
            QtWidgets.QMessageBox.warning(self, "No Project Manager", "Project manager not available")
            return
        
        if not self.current_project_id:
            QtWidgets.QMessageBox.information(self, "No Project Selected", "Please select a project first")
            return
        
        # Get quantity and notes from user
        dialog = ToolAssignmentDialog(tool_id, self.tool_library, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            quantity, notes = dialog.get_data()
            
            success = self.project_manager.add_tool_to_level(
                self.current_project_id,
                self.current_part_id,
                self.current_setup_id,
                tool_id,
                quantity,
                notes
            )
            
            if success:
                self.refresh_tools()
                self.toolsChanged.emit()
            else:
                QtWidgets.QMessageBox.warning(self, "Failed", "Failed to add tool to project")
    
    def add_tool_from_drop(self, tool_id: str):
        """Add a tool from drag-and-drop operation."""
        self.add_tool(tool_id)
    
    def update_tool_quantity_in_project(self, tool_id: str, quantity: int):
        """Update tool quantity in current context."""
        if not self.project_manager:
            return
        
        tools = self.get_current_tools()
        for tool_assoc in tools:
            if tool_assoc.tool_id == tool_id:
                tool_assoc.quantity_needed = quantity
                # Save the updated data
                self.project_manager.save_projects()
                break
    
    def update_tool_notes_in_project(self, tool_id: str, notes: str):
        """Update tool notes in current context."""
        if not self.project_manager:
            return
        
        tools = self.get_current_tools()
        for tool_assoc in tools:
            if tool_assoc.tool_id == tool_id:
                tool_assoc.notes = notes
                # Save the updated data
                self.project_manager.save_projects()
                break
    
    def remove_selected_tool(self):
        """Remove selected tool."""
        current_item = self.tools_list.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select a tool to remove")
            return
        
        if not self.project_manager:
            QtWidgets.QMessageBox.warning(self, "No Project Manager", "Project manager not available")
            return
            
        # For rich widget, get tool from the widget attribute
        tool_id = None
        if hasattr(current_item, 'tool'):
            tool_id = current_item.tool.id
        elif hasattr(current_item, 'widget') and hasattr(current_item.widget, 'tool'):
            tool_id = current_item.widget.tool.id
        else:
            # Fallback to UserRole data
            tool_id = current_item.data(QtCore.Qt.UserRole)
        
        if tool_id:
            success = self.project_manager.remove_tool_from_level(
                self.current_project_id,
                self.current_part_id,
                self.current_setup_id,
                tool_id
            )
            
            if success:
                self.refresh_tools()
                self.toolRemoved.emit(tool_id)
                self.toolsChanged.emit()
            else:
                QtWidgets.QMessageBox.warning(self, "Failed", "Failed to remove tool from project")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Could not identify selected tool")
    
    def clear_all_tools(self):
        """Clear all tools from current context."""
        reply = QtWidgets.QMessageBox.question(
            self, "Clear All Tools",
            "Are you sure you want to remove all tools from this level?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            tools = self.get_current_tools()
            for tool_assoc in tools[:]:  # Copy list to avoid modification during iteration
                self.project_manager.remove_tool_from_level(
                    self.current_project_id,
                    self.current_part_id,
                    self.current_setup_id,
                    tool_assoc.tool_id
                )
            
            self.refresh_tools()
            self.toolsChanged.emit()
    
    def copy_tools_from(self):
        """Copy tools from another project/part/setup."""
        if not self.project_manager:
            return
        
        # Simple implementation for now - could be enhanced with a full dialog
        QtWidgets.QMessageBox.information(self, "Copy Tools", "Copy tools functionality would be implemented here")
    
    def export_tool_list(self):
        """Export current tool list."""
        if not self.project_manager or not self.current_project_id:
            QtWidgets.QMessageBox.information(self, "Export Tools", "No project selected")
            return
        
        tools = self.get_current_tools()
        if not tools:
            QtWidgets.QMessageBox.information(self, "Export Tools", "No tools to export")
            return
        
        # Generate tool list text
        context = "Project"
        if self.current_setup_id:
            context = "Setup"
        elif self.current_part_id:
            context = "Part"
        
        tool_list = f"Tool List for {context}\n"
        tool_list += f"Generated: {QtCore.QDateTime.currentDateTime().toString()}\n\n"
        
        for i, tool_assoc in enumerate(tools, 1):
            tool = self.tool_library.get_tool(tool_assoc.tool_id)
            if tool:
                tool_list += f"{i}. {tool.name}\n"
                tool_list += f"   Diameter: {tool.diameter_mm:.3f}mm\n"
                tool_list += f"   Quantity: {tool_assoc.quantity_needed}\n"
                if tool_assoc.notes:
                    tool_list += f"   Notes: {tool_assoc.notes}\n"
                tool_list += "\n"
        
        # Copy to clipboard
        clipboard = QtGui.QGuiApplication.clipboard()
        clipboard.setText(tool_list)
        
        QtWidgets.QMessageBox.information(self, "Export Complete", 
                                        "Tool list copied to clipboard!")


class IntegratedProjectManager(QtWidgets.QWidget):
    """Main integrated project manager widget."""
    
    def __init__(self, tool_library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.tool_library = tool_library
        self.project_manager = tool_library.project_manager
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the main UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Navigation (compact, minimal height)
        self.navigation = ProjectNavigationWidget(self.project_manager, self)
        main_layout.addWidget(self.navigation, 0)  # No stretch, natural height only
        
        # Tools section (60% height)
        tools_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # Available tools (left panel) - wrapped in styled group box
        self.available_tools_group = QtWidgets.QGroupBox("Available Tools")
        self.available_tools_group.setStyleSheet("""
            QGroupBox {
                background-color: #2a2a2a;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 12px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #2a2a2a;
                border: none;
            }
        """)
        available_tools_layout = QtWidgets.QVBoxLayout(self.available_tools_group)
        available_tools_layout.setContentsMargins(8, 15, 8, 8)
        
        self.tool_browser = ToolBrowserWidget(self.tool_library, self)
        available_tools_layout.addWidget(self.tool_browser)
        tools_splitter.addWidget(self.available_tools_group)
        
        # Project tools (right panel) - wrapped in styled group box  
        self.project_tools_group = QtWidgets.QGroupBox("Project Tools")
        self.project_tools_group.setStyleSheet("""
            QGroupBox {
                background-color: #2a2a2a;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 12px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #2a2a2a;
                border: none;
            }
        """)
        project_tools_layout = QtWidgets.QVBoxLayout(self.project_tools_group)
        project_tools_layout.setContentsMargins(8, 15, 8, 8)
        
        self.project_tools = ProjectToolsWidget(self.tool_library, self)
        project_tools_layout.addWidget(self.project_tools)
        tools_splitter.addWidget(self.project_tools_group)
        
        # Set equal sizes
        tools_splitter.setSizes([400, 400])
        main_layout.addWidget(tools_splitter, 100)  # Take ALL remaining space
    
    def connect_signals(self):
        """Connect all signals."""
        self.navigation.selectionChanged.connect(self.on_selection_changed)
        self.tool_browser.toolSelected.connect(self.project_tools.add_tool)
        self.tool_browser.add_favorites_btn.clicked.connect(self.add_all_favorites)
        self.project_tools.toolsChanged.connect(self.update_tool_counts)
        
        # Now that signals are connected, restore last selection
        self.navigation.restore_last_selection()
    
    def on_selection_changed(self, project_id: str, part_id: str, setup_id: str):
        """Handle selection change in navigation."""
        self.project_tools.set_context(
            self.project_manager,
            project_id,
            part_id,
            setup_id
        )
        self.update_tool_counts()
    
    def update_tool_counts(self):
        """Update tool counts in panel headers."""
        # Update Available Tools count
        all_tools = self.tool_library.get_all_tools()
        current_tools = self.project_tools.get_current_tools() if self.project_tools.current_project_id else []
        current_tool_ids = {t.tool_id for t in current_tools}
        available_count = len([t for t in all_tools if t.id not in current_tool_ids])
        
        self.available_tools_group.setTitle(f"Available Tools ({available_count})")
        
        # Update Project Tools count with context
        project_tool_count = len(current_tools)
        context = "Project"
        if self.project_tools.current_setup_id:
            context = "Setup"
        elif self.project_tools.current_part_id:
            context = "Part"
        
        self.project_tools_group.setTitle(f"{context} Tools ({project_tool_count})")
    
    def add_all_favorites(self):
        """Add all favorite tools to current context."""
        favorites = self.tool_library.get_user_favorites()
        if not favorites:
            QtWidgets.QMessageBox.information(self, "No Favorites", "No favorite tools found")
            return
        
        added_count = 0
        for tool_id in favorites:
            # Check if tool is already in current context
            current_tools = self.project_tools.get_current_tools()
            if not any(t.tool_id == tool_id for t in current_tools):
                self.project_tools.add_tool(tool_id)
                added_count += 1
        
        if added_count > 0:
            QtWidgets.QMessageBox.information(self, "Added Favorites", 
                                            f"Added {added_count} favorite tools!")
        else:
            QtWidgets.QMessageBox.information(self, "Already Added", 
                                            "All favorite tools are already in this context")
    


# Simple dialog classes for creating/editing entities
class ProjectEditorDialog(QtWidgets.QDialog):
    """Dialog for creating/editing projects."""
    def __init__(self, project: Optional[Project], parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_ui()
        if project:
            self.populate_fields()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        
        self.name_input = QtWidgets.QLineEdit()
        self.description_input = QtWidgets.QTextEdit()
        self.customer_input = QtWidgets.QLineEdit()
        
        form.addRow("Name:", self.name_input)
        form.addRow("Description:", self.description_input)
        form.addRow("Customer:", self.customer_input)
        
        layout.addLayout(form)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def populate_fields(self):
        if self.project:
            self.name_input.setText(self.project.name)
            self.description_input.setPlainText(self.project.description)
            self.customer_input.setText(self.project.customer_name)
    
    def get_data(self):
        return {
            'name': self.name_input.text(),
            'description': self.description_input.toPlainText(),
            'customer_name': self.customer_input.text()
        }


class PartEditorDialog(QtWidgets.QDialog):
    """Dialog for creating/editing parts."""
    def __init__(self, part: Optional[Part], parent=None):
        super().__init__(parent)
        self.part = part
        self.setup_ui()
        if part:
            self.populate_fields()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        
        self.name_input = QtWidgets.QLineEdit()
        self.description_input = QtWidgets.QTextEdit()
        self.material_input = QtWidgets.QLineEdit()
        self.drawing_input = QtWidgets.QLineEdit()
        self.quantity_input = QtWidgets.QSpinBox()
        self.quantity_input.setRange(1, 9999)
        self.quantity_input.setValue(1)
        
        form.addRow("Name:", self.name_input)
        form.addRow("Description:", self.description_input)
        form.addRow("Material:", self.material_input)
        form.addRow("Drawing #:", self.drawing_input)
        form.addRow("Quantity:", self.quantity_input)
        
        layout.addLayout(form)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def populate_fields(self):
        if self.part:
            self.name_input.setText(self.part.name)
            self.description_input.setPlainText(self.part.description)
            self.material_input.setText(self.part.material)
            self.drawing_input.setText(self.part.drawing_number)
            self.quantity_input.setValue(self.part.quantity_required)
    
    def get_data(self):
        return {
            'name': self.name_input.text(),
            'description': self.description_input.toPlainText(),
            'material': self.material_input.text(),
            'drawing_number': self.drawing_input.text(),
            'quantity_required': self.quantity_input.value()
        }


class SetupEditorDialog(QtWidgets.QDialog):
    """Dialog for creating/editing setups."""
    def __init__(self, setup: Optional[Setup], parent=None):
        super().__init__(parent)
        self.setup = setup
        self.setup_ui()
        if setup:
            self.populate_fields()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        
        self.name_input = QtWidgets.QLineEdit()
        self.description_input = QtWidgets.QTextEdit()
        self.work_offset_combo = QtWidgets.QComboBox()
        self.work_offset_combo.addItems(["G54", "G55", "G56", "G57", "G58", "G59"])
        self.operation_combo = QtWidgets.QComboBox()
        self.operation_combo.addItems(["", "Roughing", "Finishing", "Drilling", "Tapping", "Boring"])
        self.operation_combo.setEditable(True)
        
        form.addRow("Name:", self.name_input)
        form.addRow("Description:", self.description_input)
        form.addRow("Work Offset:", self.work_offset_combo)
        form.addRow("Operation:", self.operation_combo)
        
        layout.addLayout(form)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def populate_fields(self):
        if self.setup:
            self.name_input.setText(self.setup.name)
            self.description_input.setPlainText(self.setup.description)
            self.work_offset_combo.setCurrentText(self.setup.work_offset)
            self.operation_combo.setCurrentText(self.setup.operation_type)
    
    def get_data(self):
        return {
            'name': self.name_input.text(),
            'description': self.description_input.toPlainText(),
            'work_offset': self.work_offset_combo.currentText(),
            'operation_type': self.operation_combo.currentText()
        }


class ToolAssignmentDialog(QtWidgets.QDialog):
    """Dialog for assigning tools with quantity and notes."""
    def __init__(self, tool_id: str, tool_library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        self.tool_library = tool_library
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        tool = self.tool_library.get_tool(self.tool_id)
        if tool:
            tool_label = QtWidgets.QLabel(f"Adding: {tool.name} ({tool.diameter_mm:.3f}mm)")
            tool_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(tool_label)
        
        form = QtWidgets.QFormLayout()
        
        self.quantity_input = QtWidgets.QSpinBox()
        self.quantity_input.setRange(1, 99)
        self.quantity_input.setValue(1)
        
        self.notes_input = QtWidgets.QLineEdit()
        self.notes_input.setPlaceholderText("Optional notes...")
        
        form.addRow("Quantity:", self.quantity_input)
        form.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self):
        return self.quantity_input.value(), self.notes_input.text()