"""
Project Tool Management Widget for the Speeds and Feeds Calculator.

Provides interface for assigning and managing tools within specific projects,
with drag-and-drop functionality and bulk operations.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import List, Optional, Set
import webbrowser

from ..models.project import Project, ProjectToolAssociation
from ..models.tool_library import ToolLibrary, ToolSpecs


class ToolListItem(QtWidgets.QListWidgetItem):
    """Custom list item for tools with additional data."""
    
    def __init__(self, tool: ToolSpecs, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.setText(f"{tool.name} ({tool.diameter_mm:.3f}mm)")
        self.setToolTip(f"{tool.manufacturer} - {tool.name}\n"
                       f"Diameter: {tool.diameter_mm:.3f}mm ({tool.diameter_inch:.4f}\")\n"
                       f"Flutes: {tool.flutes}\n"
                       f"Coating: {tool.coating}")
        
        # Add visual indicators
        if tool.price > 0:
            self.setText(f"{tool.name} ({tool.diameter_mm:.3f}mm) - ${tool.price:.2f}")


class ProjectToolListWidget(QtWidgets.QListWidget):
    """Enhanced list widget for project tools with quantity support."""
    
    toolQuantityChanged = QtCore.Signal(str, int)  # tool_id, quantity
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
    def add_tool_association(self, tool: ToolSpecs, association: ProjectToolAssociation):
        """Add a tool association to the list."""
        item = ToolListItem(tool)
        
        # Create widget for quantity control
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Tool info
        info_label = QtWidgets.QLabel(f"{tool.name} ({tool.diameter_mm:.3f}mm)")
        info_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        
        # Quantity control
        qty_label = QtWidgets.QLabel("Qty:")
        qty_spin = QtWidgets.QSpinBox()
        qty_spin.setRange(1, 99)
        qty_spin.setValue(association.quantity_needed)
        qty_spin.setFixedWidth(60)
        qty_spin.valueChanged.connect(lambda value: self.toolQuantityChanged.emit(tool.id, value))
        
        layout.addWidget(info_label)
        layout.addWidget(qty_label)
        layout.addWidget(qty_spin)
        
        self.addItem(item)
        self.setItemWidget(item, widget)
        
        return item


class ProjectToolsDialog(QtWidgets.QDialog):
    """Dialog for managing tools within a specific project."""
    
    def __init__(self, project: Project, tool_library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.project = project
        self.library = tool_library
        
        self.setWindowTitle(f"🔧 Tools for Project: {project.name}")
        self.setModal(True)
        self.resize(1000, 700)
        self.setup_ui()
        self.populate_tools()
    
    def setup_ui(self):
        """Setup the main UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header
        header_layout = QtWidgets.QHBoxLayout()
        
        title_label = QtWidgets.QLabel(f"🔧 Tools for: {self.project.name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        
        # Project info
        info_label = QtWidgets.QLabel(f"Customer: {self.project.customer_name or 'Not specified'}")
        info_label.setStyleSheet("font-size: 12px; color: #cccccc;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(info_label)
        
        # Main content - two column layout
        main_layout = QtWidgets.QHBoxLayout()
        
        # Left side - Available tools
        left_panel = QtWidgets.QGroupBox("Available Tools")
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        
        # Search for available tools
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search available tools...")
        self.search_input.textChanged.connect(self.filter_available_tools)
        
        # Filter controls
        filter_layout = QtWidgets.QHBoxLayout()
        
        self.favorites_only = QtWidgets.QCheckBox("Favorites Only")
        self.favorites_only.stateChanged.connect(self.filter_available_tools)
        
        self.manufacturer_filter = QtWidgets.QComboBox()
        self.manufacturer_filter.addItem("All Manufacturers")
        self.manufacturer_filter.addItems(self.library.manufacturers)
        self.manufacturer_filter.currentTextChanged.connect(self.filter_available_tools)
        
        filter_layout.addWidget(self.favorites_only)
        filter_layout.addWidget(QtWidgets.QLabel("Mfg:"))
        filter_layout.addWidget(self.manufacturer_filter)
        filter_layout.addStretch()
        
        # Available tools list
        self.available_tools = QtWidgets.QListWidget()
        self.available_tools.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.available_tools.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.available_tools.itemDoubleClicked.connect(self.add_selected_tools)
        
        # Add selected tools button
        add_tools_btn = QtWidgets.QPushButton("➡️ Add Selected Tools")
        add_tools_btn.clicked.connect(self.add_selected_tools)
        
        left_layout.addWidget(self.search_input)
        left_layout.addLayout(filter_layout)
        left_layout.addWidget(self.available_tools, 1)
        left_layout.addWidget(add_tools_btn)
        
        # Right side - Project tools
        right_panel = QtWidgets.QGroupBox(f"Project Tools ({self.project.get_tool_count()})")
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # Project tools list
        self.project_tools = ProjectToolListWidget()
        self.project_tools.toolQuantityChanged.connect(self.update_tool_quantity)
        self.project_tools.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.project_tools.customContextMenuRequested.connect(self.show_project_tool_context_menu)
        
        # Project tools actions
        project_actions = QtWidgets.QHBoxLayout()
        
        remove_tools_btn = QtWidgets.QPushButton("❌ Remove Selected")
        remove_tools_btn.clicked.connect(self.remove_selected_tools)
        
        self.export_list_btn = QtWidgets.QPushButton("📋 Export List")
        self.export_list_btn.clicked.connect(self.export_tool_list)
        
        project_actions.addWidget(remove_tools_btn)
        project_actions.addWidget(self.export_list_btn)
        project_actions.addStretch()
        
        right_layout.addWidget(self.project_tools, 1)
        right_layout.addLayout(project_actions)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # Quick actions
        quick_actions = QtWidgets.QGroupBox("Quick Actions")
        quick_layout = QtWidgets.QHBoxLayout(quick_actions)
        
        add_favorites_btn = QtWidgets.QPushButton("⭐ Add All Favorites")
        add_favorites_btn.clicked.connect(self.add_all_favorites)
        
        copy_from_project_btn = QtWidgets.QPushButton("📋 Copy from Project...")
        copy_from_project_btn.clicked.connect(self.copy_from_project)
        
        clear_all_btn = QtWidgets.QPushButton("🗑️ Clear All Tools")
        clear_all_btn.clicked.connect(self.clear_all_tools)
        
        quick_layout.addWidget(add_favorites_btn)
        quick_layout.addWidget(copy_from_project_btn)
        quick_layout.addWidget(clear_all_btn)
        quick_layout.addStretch()
        
        # Dialog buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        save_btn = QtWidgets.QPushButton("💾 Save Changes")
        save_btn.clicked.connect(self.save_changes)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(close_btn)
        
        # Assemble main layout
        layout.addLayout(header_layout)
        layout.addLayout(main_layout, 1)
        layout.addWidget(quick_actions)
        layout.addLayout(button_layout)
    
    def populate_tools(self):
        """Populate the tool lists."""
        self.populate_available_tools()
        self.populate_project_tools()
    
    def populate_available_tools(self):
        """Populate available tools list."""
        all_tools = self.library.get_all_tools()
        project_tool_ids = self.project.get_tool_ids()
        
        # Show tools not already in project
        available_tools = [t for t in all_tools if t.id not in project_tool_ids]
        
        self.available_tools.clear()
        for tool in sorted(available_tools, key=lambda x: x.name):
            item = ToolListItem(tool)
            self.available_tools.addItem(item)
    
    def populate_project_tools(self):
        """Populate project tools list."""
        self.project_tools.clear()
        
        for tool_assoc in self.project.tools:
            tool = self.library.get_tool(tool_assoc.tool_id)
            if tool:
                self.project_tools.add_tool_association(tool, tool_assoc)
    
    def filter_available_tools(self):
        """Filter available tools based on search criteria."""
        search_text = self.search_input.text().lower()
        favorites_only = self.favorites_only.isChecked()
        manufacturer = self.manufacturer_filter.currentText()
        
        favorites = self.library.get_user_favorites() if favorites_only else []
        
        for i in range(self.available_tools.count()):
            item = self.available_tools.item(i)
            tool = item.tool
            
            # Check search text
            text_match = (search_text in tool.name.lower() or 
                         search_text in tool.manufacturer.lower() or
                         search_text in tool.part_number.lower())
            
            # Check favorites
            favorites_match = not favorites_only or tool.id in favorites
            
            # Check manufacturer
            manufacturer_match = (manufacturer == "All Manufacturers" or 
                                tool.manufacturer == manufacturer)
            
            # Show/hide item
            item.setHidden(not (text_match and favorites_match and manufacturer_match))
    
    def add_selected_tools(self):
        """Add selected tools to the project."""
        selected_items = self.available_tools.selectedItems()
        
        for item in selected_items:
            tool = item.tool
            # Add to project
            self.project.add_tool(tool.id, quantity=1, notes="")
            
        # Refresh lists
        self.populate_tools()
        self.update_project_count()
    
    def remove_selected_tools(self):
        """Remove selected tools from the project."""
        selected_items = self.project_tools.selectedItems()
        
        for item in selected_items:
            if hasattr(item, 'tool'):
                self.project.remove_tool(item.tool.id)
        
        # Refresh lists  
        self.populate_tools()
        self.update_project_count()
    
    def update_tool_quantity(self, tool_id: str, quantity: int):
        """Update tool quantity in project."""
        for tool_assoc in self.project.tools:
            if tool_assoc.tool_id == tool_id:
                tool_assoc.quantity_needed = quantity
                break
    
    def show_project_tool_context_menu(self, position):
        """Show context menu for project tools."""
        item = self.project_tools.itemAt(position)
        if not item or not hasattr(item, 'tool'):
            return
        
        menu = QtWidgets.QMenu(self)
        
        # View tool details
        view_action = menu.addAction("🔍 View Details")
        
        # Open URL if available
        tool = item.tool
        if tool.url:
            open_url_action = menu.addAction("🌐 Open URL")
        
        # Remove from project
        remove_action = menu.addAction("❌ Remove from Project")
        
        action = menu.exec_(self.project_tools.mapToGlobal(position))
        
        if action == view_action:
            self.show_tool_details(tool)
        elif tool.url and action == open_url_action:
            webbrowser.open(tool.url)
        elif action == remove_action:
            self.project.remove_tool(tool.id)
            self.populate_tools()
            self.update_project_count()
    
    def show_tool_details(self, tool: ToolSpecs):
        """Show detailed tool information."""
        details = f"""
        <h3>{tool.name}</h3>
        <b>Manufacturer:</b> {tool.manufacturer}<br>
        <b>Part Number:</b> {tool.part_number}<br>
        <b>Diameter:</b> {tool.diameter_mm:.3f}mm ({tool.diameter_inch:.4f}\")<br>
        <b>Flutes:</b> {tool.flutes}<br>
        <b>Coating:</b> {tool.coating}<br>
        <b>Material:</b> {tool.material}<br>
        """
        
        if tool.price > 0:
            details += f"<b>Price:</b> ${tool.price:.2f}<br>"
        
        if tool.notes:
            details += f"<br><b>Notes:</b> {tool.notes}"
        
        QtWidgets.QMessageBox.information(self, "Tool Details", details)
    
    def add_all_favorites(self):
        """Add all favorite tools to the project."""
        favorites = self.library.get_user_favorites()
        
        added_count = 0
        for tool_id in favorites:
            if not self.project.has_tool(tool_id):
                self.project.add_tool(tool_id, quantity=1, notes="")
                added_count += 1
        
        if added_count > 0:
            self.populate_tools()
            self.update_project_count()
            QtWidgets.QMessageBox.information(self, "Success", 
                                            f"Added {added_count} favorite tools to project!")
        else:
            QtWidgets.QMessageBox.information(self, "Info", 
                                            "All favorite tools are already in this project.")
    
    def copy_from_project(self):
        """Copy tools from another project."""
        projects = [p for p in self.library.project_manager.get_all_projects() 
                   if p.id != self.project.id and p.get_tool_count() > 0]
        
        if not projects:
            QtWidgets.QMessageBox.information(self, "No Projects", 
                                            "No other projects with tools found.")
            return
        
        project_names = [f"{p.name} ({p.get_tool_count()} tools)" for p in projects]
        
        selected, ok = QtWidgets.QInputDialog.getItem(
            self, "Copy from Project", 
            "Select project to copy tools from:",
            project_names, 0, False
        )
        
        if ok:
            selected_index = project_names.index(selected)
            source_project = projects[selected_index]
            
            # Copy tools
            added_count = 0
            for tool_assoc in source_project.tools:
                if not self.project.has_tool(tool_assoc.tool_id):
                    self.project.add_tool(
                        tool_assoc.tool_id, 
                        quantity=tool_assoc.quantity_needed,
                        notes=tool_assoc.notes
                    )
                    added_count += 1
            
            if added_count > 0:
                self.populate_tools()
                self.update_project_count()
                QtWidgets.QMessageBox.information(self, "Success", 
                                                f"Copied {added_count} tools from '{source_project.name}'!")
            else:
                QtWidgets.QMessageBox.information(self, "Info", 
                                                "All tools from that project are already in this project.")
    
    def clear_all_tools(self):
        """Clear all tools from the project."""
        if self.project.get_tool_count() == 0:
            QtWidgets.QMessageBox.information(self, "Info", "Project has no tools to clear.")
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Clear All Tools",
            f"Are you sure you want to remove all {self.project.get_tool_count()} tools from this project?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.project.tools.clear()
            self.populate_tools()
            self.update_project_count()
    
    def export_tool_list(self):
        """Export project tool list."""
        if self.project.get_tool_count() == 0:
            QtWidgets.QMessageBox.information(self, "Info", "No tools to export.")
            return
        
        # Generate tool list text
        tool_list = f"Tool List for Project: {self.project.name}\n"
        tool_list += f"Customer: {self.project.customer_name or 'Not specified'}\n"
        tool_list += f"Generated: {QtCore.QDateTime.currentDateTime().toString()}\n\n"
        
        for i, tool_assoc in enumerate(self.project.tools, 1):
            tool = self.library.get_tool(tool_assoc.tool_id)
            if tool:
                tool_list += f"{i}. {tool.name}\n"
                tool_list += f"   Manufacturer: {tool.manufacturer}\n"
                tool_list += f"   Part Number: {tool.part_number}\n"
                tool_list += f"   Diameter: {tool.diameter_mm:.3f}mm ({tool.diameter_inch:.4f}\")\n"
                tool_list += f"   Quantity: {tool_assoc.quantity_needed}\n"
                if tool_assoc.notes:
                    tool_list += f"   Notes: {tool_assoc.notes}\n"
                tool_list += "\n"
        
        # Copy to clipboard
        clipboard = QtGui.QGuiApplication.clipboard()
        clipboard.setText(tool_list)
        
        QtWidgets.QMessageBox.information(self, "Export Complete", 
                                        "Tool list copied to clipboard!")
    
    def update_project_count(self):
        """Update project tool count in UI."""
        # This would update the group box title, but we need a reference
        # For now, just refresh the parent if needed
        pass
    
    def save_changes(self):
        """Save changes to the project."""
        if self.library.project_manager.save_projects():
            QtWidgets.QMessageBox.information(self, "Success", 
                                            "Project tools saved successfully!")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", 
                                        "Failed to save project changes.")