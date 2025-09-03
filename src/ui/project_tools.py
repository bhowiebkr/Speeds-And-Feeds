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


class ProjectToolWidget(QtWidgets.QWidget):
    """Custom widget for project tool items with proper sizing."""
    
    def __init__(self, tool: ToolSpecs, association: ProjectToolAssociation, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.association = association
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the project tool widget UI."""
        # Main layout with proper margins and spacing
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(4)
        
        # Top row - tool info and controls
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.setSpacing(6)
        
        # Tool info - let it expand naturally
        info_label = QtWidgets.QLabel(f"{self.tool.name} ({self.tool.diameter_mm:.3f}mm)")
        info_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        info_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        info_label.setWordWrap(True)
        
        # Quantity control
        qty_label = QtWidgets.QLabel("Qty:")
        qty_label.setStyleSheet("font-size: 10px;")
        
        self.qty_spin = QtWidgets.QSpinBox()
        self.qty_spin.setRange(1, 99)
        self.qty_spin.setValue(self.association.quantity_needed)
        self.qty_spin.setMinimumWidth(50)  # Use minimum instead of fixed
        self.qty_spin.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        
        # Notes button - remove fixed size, let it size naturally
        self.notes_btn = QtWidgets.QPushButton("📝")
        self.notes_btn.setToolTip("Edit notes for this tool")
        self.notes_btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.notes_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                padding: 4px 6px;
                min-width: 24px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        
        top_layout.addWidget(info_label, 1)  # Give it stretch priority
        top_layout.addWidget(qty_label)
        top_layout.addWidget(self.qty_spin)
        top_layout.addWidget(self.notes_btn)
        
        # Bottom row - notes preview
        self.notes_preview = QtWidgets.QLabel()
        self.notes_preview.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.notes_preview.setWordWrap(True)
        self.update_notes_preview()
        
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.notes_preview)
        
        # Set a reasonable minimum height
        self.setMinimumHeight(50)
    
    def update_notes_preview(self):
        """Update the notes preview display."""
        if self.association.notes:
            preview_text = self.association.notes[:80] + ("..." if len(self.association.notes) > 80 else "")
            self.notes_preview.setText(f"📝 {preview_text}")
            self.notes_preview.setStyleSheet("color: #888888; font-style: italic; font-size: 10px;")
        else:
            self.notes_preview.setText("No notes")
            self.notes_preview.setStyleSheet("color: #666666; font-style: italic; font-size: 10px;")
    
    def sizeHint(self):
        """Return proper size hint for this widget."""
        # Calculate based on content
        base_height = 50  # Minimum height for single line
        
        # Add height for wrapped text if tool name is long
        font_metrics = self.fontMetrics()
        info_text = f"{self.tool.name} ({self.tool.diameter_mm:.3f}mm)"
        available_width = self.width() - 150  # Account for controls
        
        if available_width > 0:
            text_rect = font_metrics.boundingRect(0, 0, available_width, 0, 
                                                QtCore.Qt.TextWordWrap, info_text)
            text_height = text_rect.height()
            if text_height > font_metrics.height():
                base_height += text_height - font_metrics.height()
        
        # Add height for notes if present
        if self.association.notes:
            notes_height = font_metrics.height()  # Notes are single line with ellipsis
            base_height += notes_height
        
        return QtCore.QSize(self.width(), base_height + 16)  # Add padding


class ProjectToolListWidget(QtWidgets.QListWidget):
    """Enhanced list widget for project tools with quantity support."""
    
    toolQuantityChanged = QtCore.Signal(str, int)  # tool_id, quantity
    toolNotesChanged = QtCore.Signal(str, str)  # tool_id, notes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        # Configure for proper sizing
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setSpacing(2)  # Small spacing between items
        
    def add_tool_association(self, tool: ToolSpecs, association: ProjectToolAssociation):
        """Add a tool association to the list."""
        # Create a plain list item without text (widget will handle display)
        item = QtWidgets.QListWidgetItem()
        item.tool = tool  # Store tool reference for context menus
        
        # Create the custom widget
        widget = ProjectToolWidget(tool, association, self)
        
        # Connect signals
        widget.qty_spin.valueChanged.connect(lambda value: self.toolQuantityChanged.emit(tool.id, value))
        widget.notes_btn.clicked.connect(lambda: self.edit_tool_notes(tool.id, association.notes))
        
        # Store references for updates
        item.widget = widget
        item.notes_preview = widget.notes_preview
        item.notes_btn = widget.notes_btn
        
        # Add to list and set proper sizing
        self.addItem(item)
        self.setItemWidget(item, widget)
        
        # Force item to use widget's size hint
        item.setSizeHint(widget.sizeHint())
        
        return item
    
    def edit_tool_notes(self, tool_id: str, current_notes: str):
        """Open dialog to edit tool notes."""
        dialog = ToolNotesDialog(tool_id, current_notes, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_notes = dialog.get_notes()
            self.toolNotesChanged.emit(tool_id, new_notes)
            
            # Update the preview for this tool
            for i in range(self.count()):
                item = self.item(i)
                if hasattr(item, 'tool') and item.tool.id == tool_id:
                    if hasattr(item, 'widget'):
                        # Update the association data
                        item.widget.association.notes = new_notes
                        # Update the preview display
                        item.widget.update_notes_preview()
                        # Recalculate size in case notes changed height
                        item.setSizeHint(item.widget.sizeHint())
                    break


class ToolNotesDialog(QtWidgets.QDialog):
    """Dialog for editing project-specific tool notes."""
    
    def __init__(self, tool_id: str, current_notes: str, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        self.current_notes = current_notes
        
        self.setWindowTitle("📝 Edit Tool Notes")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header_label = QtWidgets.QLabel(f"📝 Project Notes for Tool: {self.tool_id}")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        
        # Instructions
        instructions = QtWidgets.QLabel(
            "Add notes specific to this tool's use in this project:\n"
            "• Operations (roughing, finishing, slotting)\n" 
            "• Speeds & feeds recommendations\n"
            "• Special considerations or warnings"
        )
        instructions.setStyleSheet("color: #cccccc; font-size: 11px;")
        instructions.setWordWrap(True)
        
        # Notes text area
        self.notes_text = QtWidgets.QTextEdit()
        self.notes_text.setPlainText(self.current_notes)
        self.notes_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.notes_text.setPlaceholderText("Enter notes for this tool in this project...")
        
        # Character count
        self.char_count = QtWidgets.QLabel("0 characters")
        self.char_count.setStyleSheet("color: #888888; font-size: 10px;")
        self.update_char_count()
        self.notes_text.textChanged.connect(self.update_char_count)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        clear_btn = QtWidgets.QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_notes)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QtWidgets.QPushButton("💾 Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        # Assemble layout
        layout.addWidget(header_label)
        layout.addWidget(instructions)
        layout.addWidget(self.notes_text, 1)
        layout.addWidget(self.char_count)
        layout.addLayout(button_layout)
    
    def update_char_count(self):
        """Update character count label."""
        count = len(self.notes_text.toPlainText())
        self.char_count.setText(f"{count} characters")
    
    def clear_notes(self):
        """Clear the notes text."""
        self.notes_text.clear()
    
    def get_notes(self) -> str:
        """Get the notes text."""
        return self.notes_text.toPlainText().strip()


class ProjectToolsDialog(QtWidgets.QDialog):
    """Dialog for managing tools within a specific project."""
    
    def __init__(self, project: Project, tool_library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.project = project
        self.library = tool_library
        
        self.setWindowTitle(f"🔧 Tools for Project: {project.name}")
        self.setModal(True)
        self.resize(1200, 800)  # Larger default size
        self.setMinimumSize(1000, 600)  # Minimum size to prevent clipping
        self.setup_ui()
        self.populate_tools()
    
    def setup_ui(self):
        """Setup the main UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)  # Increased margins
        layout.setSpacing(18)  # Increased spacing
        
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
        filter_layout.setSpacing(12)  # Add proper spacing
        
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
        self.project_tools.toolNotesChanged.connect(self.update_tool_notes)
        self.project_tools.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.project_tools.customContextMenuRequested.connect(self.show_project_tool_context_menu)
        
        # Project tools actions
        project_actions = QtWidgets.QHBoxLayout()
        project_actions.setSpacing(12)  # Add proper spacing
        
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
    
    def update_tool_notes(self, tool_id: str, notes: str):
        """Update tool notes in project."""
        for tool_assoc in self.project.tools:
            if tool_assoc.tool_id == tool_id:
                tool_assoc.notes = notes
                break
    
    def show_project_tool_context_menu(self, position):
        """Show context menu for project tools."""
        item = self.project_tools.itemAt(position)
        if not item or not hasattr(item, 'tool'):
            return
        
        menu = QtWidgets.QMenu(self)
        
        # Edit notes
        edit_notes_action = menu.addAction("📝 Edit Notes")
        menu.addSeparator()
        
        # View tool details
        view_action = menu.addAction("🔍 View Details")
        
        # Open URL if available
        tool = item.tool
        if tool.url:
            open_url_action = menu.addAction("🌐 Open URL")
        
        menu.addSeparator()
        # Remove from project
        remove_action = menu.addAction("❌ Remove from Project")
        
        action = menu.exec_(self.project_tools.mapToGlobal(position))
        
        if action == edit_notes_action:
            # Find current notes for this tool
            current_notes = ""
            for tool_assoc in self.project.tools:
                if tool_assoc.tool_id == tool.id:
                    current_notes = tool_assoc.notes
                    break
            self.project_tools.edit_tool_notes(tool.id, current_notes)
        elif action == view_action:
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