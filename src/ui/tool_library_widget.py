"""
Tool Library Widget for the Speeds and Feeds Calculator.

A modern, feature-rich tool library interface with search, filtering, 
favorites, and comprehensive tool management capabilities.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from typing import List, Optional
import os
import json

from decimal import Decimal
from ..models.tool_library import ToolLibrary, ToolSpecs, MM_TO_INCH_DECIMAL, INCH_TO_MM_DECIMAL
from ..models.project import Project
from ..constants.units import MM_TO_IN, IN_TO_MM
from ..utils.fractions import parse_fractional_input, decimal_to_fraction_string, get_common_imperial_fractions, FractionalInputError
from .project_manager import ProjectManagerDialog


class ToolCard(QtWidgets.QFrame):
    """Individual tool card widget with modern styling."""
    
    toolSelected = QtCore.Signal(ToolSpecs)
    toolFavorited = QtCore.Signal(str, bool)
    toolDeleted = QtCore.Signal(str)
    toolEdited = QtCore.Signal(ToolSpecs)
    
    def __init__(self, tool: ToolSpecs, is_favorite: bool = False, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.is_favorite = is_favorite
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the tool card UI."""
        self.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Raised)
        self.setLineWidth(1)
        self.setMinimumSize(280, 180)  # Use minimum instead of fixed
        self.setMaximumWidth(320)      # Set max width to prevent over-stretching
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        # Set dark theme compatible styling
        self.setStyleSheet("""
            ToolCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #3c3c3c, stop:1 #2a2a2a);
                border: 1px solid #555555;
                border-radius: 8px;
                color: #ffffff;
            }
            ToolCard:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #4a4a4a, stop:1 #383838);
                border: 2px solid #0078d4;
            }
        """)
        
        # Main layout with better spacing
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)  # Increased margins
        layout.setSpacing(8)  # Increased spacing
        
        # Header with manufacturer and favorite button
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setSpacing(8)  # Add spacing between header elements
        
        # Manufacturer and series
        manufacturer_label = QtWidgets.QLabel(f"{self.tool.manufacturer}")
        manufacturer_label.setStyleSheet("font-weight: bold; color: #0078d4; font-size: 11px;")
        
        # Favorite button - using QLabel instead of QPushButton
        self.favorite_btn = QtWidgets.QLabel()
        self.favorite_btn.setMinimumSize(24, 24)  # Use minimum instead of fixed
        self.favorite_btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.favorite_btn.setAlignment(QtCore.Qt.AlignCenter)
        self.favorite_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.update_favorite_icon()
        self.favorite_btn.setToolTip("Add to Favorites" if not self.is_favorite else "Remove from Favorites")
        
        header_layout.addWidget(manufacturer_label)
        header_layout.addStretch()
        header_layout.addWidget(self.favorite_btn)
        
        # Tool name
        name_label = QtWidgets.QLabel(self.tool.name)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        name_label.setMaximumHeight(30)
        
        # Specifications layout
        specs_layout = QtWidgets.QGridLayout()
        specs_layout.setSpacing(4)
        
        # Diameter
        diameter_label = QtWidgets.QLabel("Diameter:")
        diameter_label.setStyleSheet("font-size: 10px; color: #cccccc;")
        diameter_value = QtWidgets.QLabel(f"{float(self.tool.diameter_mm):.3f}mm ({float(self.tool.diameter_inch):.4f}\")")
        diameter_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #ffffff;")
        
        # Flutes
        flutes_label = QtWidgets.QLabel("Flutes:")
        flutes_label.setStyleSheet("font-size: 10px; color: #cccccc;")
        flutes_value = QtWidgets.QLabel(str(self.tool.flutes))
        flutes_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #ffffff;")
        
        # Coating
        coating_label = QtWidgets.QLabel("Coating:")
        coating_label.setStyleSheet("font-size: 10px; color: #cccccc;")
        coating_value = QtWidgets.QLabel(self.tool.coating.upper())
        coating_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #2196F3;")
        
        # Material
        material_label = QtWidgets.QLabel("Material:")
        material_label.setStyleSheet("font-size: 10px; color: #cccccc;")
        material_value = QtWidgets.QLabel(self.tool.material.upper())
        material_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #ffffff;")
        
        specs_layout.addWidget(diameter_label, 0, 0)
        specs_layout.addWidget(diameter_value, 0, 1)
        specs_layout.addWidget(flutes_label, 1, 0)
        specs_layout.addWidget(flutes_value, 1, 1)
        specs_layout.addWidget(coating_label, 2, 0)
        specs_layout.addWidget(coating_value, 2, 1)
        specs_layout.addWidget(material_label, 3, 0)
        specs_layout.addWidget(material_value, 3, 1)
        
        # Part number and price
        part_price_layout = QtWidgets.QHBoxLayout()
        part_number = QtWidgets.QLabel(f"P/N: {self.tool.part_number}")
        part_number.setStyleSheet("font-size: 9px; color: #aaaaaa; font-family: monospace;")
        
        if self.tool.price > 0:
            price_label = QtWidgets.QLabel(f"${self.tool.price:.2f}")
            price_label.setStyleSheet("font-size: 10px; color: #4CAF50; font-weight: bold;")
            part_price_layout.addWidget(price_label)
        
        part_price_layout.addWidget(part_number)
        part_price_layout.addStretch()
        
        # Project indicators
        projects_using_tool = self.parent().library.get_projects_using_tool(self.tool.id) if hasattr(self.parent(), 'library') else []
        if projects_using_tool:
            project_layout = QtWidgets.QHBoxLayout()
            project_layout.setSpacing(2)
            for project in projects_using_tool[:2]:  # Show max 2 projects
                project_label = QtWidgets.QLabel(f"📁 {project.name}")
                project_label.setStyleSheet("""
                    background-color: #9C27B0; 
                    color: #ffffff; 
                    border-radius: 3px; 
                    padding: 2px 6px; 
                    font-size: 9px;
                """)
                project_layout.addWidget(project_label)
            if len(projects_using_tool) > 2:
                more_label = QtWidgets.QLabel(f"+{len(projects_using_tool) - 2}")
                more_label.setStyleSheet("""
                    background-color: #666666; 
                    color: #ffffff; 
                    border-radius: 3px; 
                    padding: 2px 6px; 
                    font-size: 9px;
                """)
                project_layout.addWidget(more_label)
            project_layout.addStretch()
        
        # Tags
        if self.tool.tags:
            tags_layout = QtWidgets.QHBoxLayout()
            tags_layout.setSpacing(2)
            for tag in self.tool.tags[:3]:  # Show max 3 tags
                tag_label = QtWidgets.QLabel(tag)
                tag_label.setStyleSheet("""
                    background-color: #404040; 
                    color: #2196F3; 
                    border: 1px solid #2196F3;
                    border-radius: 3px; 
                    padding: 2px 6px; 
                    font-size: 9px;
                """)
                tags_layout.addWidget(tag_label)
            tags_layout.addStretch()
        
        # Assemble layout
        layout.addLayout(header_layout)
        layout.addWidget(name_label)
        layout.addLayout(specs_layout)
        layout.addLayout(part_price_layout)
        if projects_using_tool:
            layout.addLayout(project_layout)
        if self.tool.tags:
            layout.addLayout(tags_layout)
        layout.addStretch()
        
        # Tool type indicator
        type_indicator = QtWidgets.QLabel()
        type_color = self.get_type_color(self.tool.type)
        type_indicator.setStyleSheet(f"background-color: {type_color}; border-radius: 2px;")
        type_indicator.setFixedHeight(4)
        layout.addWidget(type_indicator)
        
    def get_type_color(self, tool_type: str) -> str:
        """Get color for tool type indicator."""
        type_colors = {
            "square_endmill": "#4CAF50",
            "ball_endmill": "#2196F3", 
            "corner_radius_endmill": "#FF9800",
            "roughing_endmill": "#F44336",
            "drill": "#9C27B0",
            "spot_drill": "#795548",
            "chamfer_mill": "#607D8B",
            "thread_mill": "#E91E63"
        }
        return type_colors.get(tool_type, "#666666")
        
    def update_favorite_icon(self):
        """Update favorite button icon and styling based on state."""
        if self.is_favorite:
            # Favorited state - using QLabel with star
            self.favorite_btn.setText("★")
            self.favorite_btn.setStyleSheet("""
                QLabel {
                    background: #ffd700;
                    border: 2px solid #333333;
                    color: #000000;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 12px;
                }
            """)
        else:
            # Non-favorited state - empty star
            self.favorite_btn.setText("☆")
            self.favorite_btn.setStyleSheet("""
                QLabel {
                    background: transparent;
                    border: 2px solid #666666;
                    color: #888888;
                    font-size: 16px;
                    font-weight: normal;
                    border-radius: 12px;
                }
            """)
    
    def toggle_favorite(self):
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
        self.update_favorite_icon()
        self.favorite_btn.setToolTip("Add to Favorites" if not self.is_favorite else "Remove from Favorites")
        self.toolFavorited.emit(self.tool.id, self.is_favorite)
    
    def mousePressEvent(self, event):
        """Handle mouse click events."""
        if event.button() == QtCore.Qt.LeftButton:
            # Check if click was on the favorite button
            favorite_btn_geometry = self.favorite_btn.geometry()
            if favorite_btn_geometry.contains(event.pos()):
                self.toggle_favorite()
                event.accept()
                return
            # Otherwise, handle tool selection
            self.toolSelected.emit(self.tool)
        super().mousePressEvent(event)
        
    def contextMenuEvent(self, event):
        """Show context menu for tool actions."""
        menu = QtWidgets.QMenu(self)
        
        edit_action = menu.addAction("✏️ Edit Tool")
        delete_action = menu.addAction("🗑️ Delete Tool")
        
        action = menu.exec_(event.globalPos())
        
        if action == edit_action:
            self.toolEdited.emit(self.tool)
        elif action == delete_action:
            self.toolDeleted.emit(self.tool.id)


class ToolLibraryWidget(QtWidgets.QWidget):
    """Main tool library widget with modern interface."""
    
    toolSelected = QtCore.Signal(str)  # Changed to emit tool_id string instead of ToolSpecs
    
    def __init__(self, library: ToolLibrary = None, parent=None, embed_mode=False):
        super().__init__(parent)
        self.library = library or ToolLibrary()
        self.current_tools: List[ToolSpecs] = []
        self.tool_cards: List[ToolCard] = []
        self._refreshing = False  # Flag to prevent filtering during refresh
        self.embed_mode = embed_mode
        
        if not embed_mode:
            # Only set window properties when used as a dialog
            self.setWindowTitle("🔧 Tool Library")
            self.setModal(True)
            self.resize(1200, 800)
        self.setup_ui()
        self.refresh_tools()
        
    def setup_ui(self):
        """Setup the main UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header with title and actions
        header_layout = QtWidgets.QHBoxLayout()
        
        title_label = QtWidgets.QLabel("🔧 Tool Library")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        
        # Action buttons
        self.add_tool_btn = QtWidgets.QPushButton("➕ Add Tool")
        self.add_tool_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:pressed { background-color: #005a9e; }
        """)
        self.add_tool_btn.clicked.connect(self.add_new_tool)
        
        self.import_btn = QtWidgets.QPushButton("📁 Import")
        self.import_btn.clicked.connect(self.import_tools)
        
        self.export_btn = QtWidgets.QPushButton("💾 Export")  
        self.export_btn.clicked.connect(self.export_tools)
        
        
        self.help_btn = QtWidgets.QPushButton("❓ Guide")
        self.help_btn.clicked.connect(self.show_tool_guide)
        
        self.projects_btn = QtWidgets.QPushButton("📁 Projects")
        self.projects_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:pressed { background-color: #6A1B9A; }
        """)
        self.projects_btn.clicked.connect(self.show_project_manager)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.projects_btn)
        header_layout.addWidget(self.add_tool_btn)
        header_layout.addWidget(self.import_btn)
        header_layout.addWidget(self.export_btn)
        header_layout.addWidget(self.help_btn)
        
        # Search and filters
        search_layout = QtWidgets.QHBoxLayout()
        
        # Search box
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search tools by name, part number, or description...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e1e1e1;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #0078d4; }
        """)
        self.search_input.textChanged.connect(self.filter_tools)
        
        # Clear search button
        self.clear_search_btn = QtWidgets.QPushButton("✖")
        self.clear_search_btn.setMinimumSize(30, 30)  # Use minimum instead of fixed
        self.clear_search_btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.clear_search_btn.clicked.connect(self.clear_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_btn)
        
        # Filters layout
        filters_layout = QtWidgets.QHBoxLayout()
        
        # Quick filter buttons
        self.favorites_btn = QtWidgets.QPushButton("⭐ Favorites")
        self.favorites_btn.setCheckable(True)
        self.favorites_btn.clicked.connect(self.filter_tools)
        
        self.recent_btn = QtWidgets.QPushButton("🕒 Recent")
        self.recent_btn.setCheckable(True)
        self.recent_btn.clicked.connect(self.filter_tools)
        
        # Manufacturer filter
        self.manufacturer_combo = QtWidgets.QComboBox()
        self.manufacturer_combo.addItem("All Manufacturers")
        self.manufacturer_combo.addItems(self.library.manufacturers)
        self.manufacturer_combo.currentTextChanged.connect(self.filter_tools)
        
        # Tool type filter
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItem("All Types")
        self.type_combo.addItems([t.replace('_', ' ').title() for t in self.library.tool_types])
        self.type_combo.currentTextChanged.connect(self.filter_tools)
        
        # Diameter range
        diameter_label = QtWidgets.QLabel("Ø:")
        self.diameter_min = QtWidgets.QDoubleSpinBox()
        self.diameter_min.setRange(0.0, 1000.0)
        self.diameter_min.setSuffix("mm")
        self.diameter_min.setSpecialValueText("Min")
        self.diameter_min.valueChanged.connect(self.filter_tools)
        
        self.diameter_max = QtWidgets.QDoubleSpinBox()
        self.diameter_max.setRange(0.0, 1000.0)
        self.diameter_max.setValue(1000.0)
        self.diameter_max.setSuffix("mm")
        self.diameter_max.setSpecialValueText("Max")
        self.diameter_max.valueChanged.connect(self.filter_tools)
        
        # Project filter
        self.project_combo = QtWidgets.QComboBox()
        self.project_combo.addItem("All Tools", None)
        self.project_combo.addItem("No Project", "no_project")
        self.refresh_project_filter()
        self.project_combo.currentIndexChanged.connect(self.filter_tools)
        
        filters_layout.addWidget(self.favorites_btn)
        filters_layout.addWidget(self.recent_btn)
        filters_layout.addWidget(QtWidgets.QLabel("Project:"))
        filters_layout.addWidget(self.project_combo)
        filters_layout.addWidget(QtWidgets.QLabel("Manufacturer:"))
        filters_layout.addWidget(self.manufacturer_combo)
        filters_layout.addWidget(QtWidgets.QLabel("Type:"))
        filters_layout.addWidget(self.type_combo)
        filters_layout.addWidget(diameter_label)
        filters_layout.addWidget(self.diameter_min)
        filters_layout.addWidget(QtWidgets.QLabel("to"))
        filters_layout.addWidget(self.diameter_max)
        filters_layout.addStretch()
        
        # Tools display area
        self.tools_scroll = QtWidgets.QScrollArea()
        self.tools_scroll.setWidgetResizable(True)
        self.tools_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tools_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tools_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        
        self.tools_container = QtWidgets.QWidget()
        self.tools_container.setStyleSheet("background-color: #2b2b2b;")
        self.tools_layout = QtWidgets.QGridLayout(self.tools_container)
        self.tools_layout.setSpacing(10)
        
        self.tools_scroll.setWidget(self.tools_container)
        
        # Status bar
        self.status_label = QtWidgets.QLabel("0 tools loaded")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        
        # Buttons layout (different for embed vs dialog mode)
        button_layout = QtWidgets.QHBoxLayout()
        
        if not self.embed_mode:
            # Dialog mode: show select/cancel buttons
            self.select_button = QtWidgets.QPushButton("Select Tool")
            self.select_button.setEnabled(False)
            self.cancel_button = QtWidgets.QPushButton("Cancel")
            
            self.select_button.clicked.connect(self.select_current_tool)
            self.cancel_button.clicked.connect(self.close_widget)
            
            button_layout.addWidget(self.status_label)
            button_layout.addStretch()
            button_layout.addWidget(self.select_button)
            button_layout.addWidget(self.cancel_button)
        else:
            # Embed mode: just show status
            button_layout.addWidget(self.status_label)
            button_layout.addStretch()
        
        # Assemble main layout
        layout.addLayout(header_layout)
        layout.addLayout(search_layout)
        layout.addLayout(filters_layout)
        layout.addWidget(self.tools_scroll)
        layout.addLayout(button_layout)
        
        # Track selected tool
        self.selected_tool: Optional[ToolSpecs] = None
        
    def refresh_tools(self):
        """Refresh the tools display."""
        self.current_tools = self.library.get_all_tools()
        self.refresh_project_filter()
        self.filter_tools()
    
    def refresh_project_filter(self):
        """Refresh the project filter dropdown."""
        current_selection = self.project_combo.currentData()
        
        # Set flag to prevent filtering during refresh
        self._refreshing = True
        
        # Clear and repopulate
        self.project_combo.clear()
        self.project_combo.addItem("All Tools", None)
        self.project_combo.addItem("No Project", "no_project")
        
        # Add active projects
        active_projects = self.library.project_manager.get_active_projects()
        for project in active_projects:
            self.project_combo.addItem(f"📁 {project.name}", project.id)
        
        # Restore selection if possible
        if current_selection:
            index = self.project_combo.findData(current_selection)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
        
        # Clear flag
        self._refreshing = False
        
    def filter_tools(self):
        """Apply filters and update display."""
        # Skip filtering if we're in the middle of refreshing
        if self._refreshing:
            return
            
        # Get filter values
        search_query = self.search_input.text().strip()
        manufacturer = self.manufacturer_combo.currentText()
        if manufacturer == "All Manufacturers":
            manufacturer = ""
        
        tool_type = self.type_combo.currentText().lower().replace(' ', '_')
        if tool_type == "all_types":
            tool_type = ""
        
        diameter_min = self.diameter_min.value()
        diameter_max = self.diameter_max.value()
        project_filter = self.project_combo.currentData()
        
        # Start with base tool search
        filtered_tools = self.library.search_tools(
            query=search_query,
            manufacturer=manufacturer,
            tool_type=tool_type,
            diameter_min=diameter_min,
            diameter_max=diameter_max
        )
        
        # Apply project filter
        if project_filter == "no_project":
            # Show tools not assigned to any project
            all_project_tool_ids = set()
            for project in self.library.project_manager.get_all_projects():
                all_project_tool_ids.update(project.get_tool_ids())
            filtered_tools = [t for t in filtered_tools if t.id not in all_project_tool_ids]
        elif project_filter:
            # Show tools assigned to specific project
            project_tools = self.library.get_project_tools(project_filter)
            project_tool_ids = {t.id for t in project_tools}
            filtered_tools = [t for t in filtered_tools if t.id in project_tool_ids]
        
        # Apply quick filters
        if self.favorites_btn.isChecked():
            favorites = self.library.get_user_favorites()
            filtered_tools = [t for t in filtered_tools if t.id in favorites]
            
        if self.recent_btn.isChecked():
            recent = self.library.get_recently_used()
            filtered_tools = [t for t in filtered_tools if t.id in recent]
        
        self.display_tools(filtered_tools)
        
    def display_tools(self, tools: List[ToolSpecs]):
        """Display tools in grid layout."""
        # Clear existing cards
        for card in self.tool_cards:
            card.deleteLater()
        self.tool_cards.clear()
        
        # Add new cards
        favorites = self.library.get_user_favorites()
        cols = 4  # Tools per row
        
        for i, tool in enumerate(tools):
            row = i // cols
            col = i % cols
            
            is_favorite = tool.id in favorites
            card = ToolCard(tool, is_favorite)
            
            # Connect signals
            card.toolSelected.connect(self.on_tool_selected)
            card.toolFavorited.connect(self.on_tool_favorited)
            card.toolDeleted.connect(self.on_tool_deleted)
            card.toolEdited.connect(self.on_tool_edited)
            
            self.tools_layout.addWidget(card, row, col)
            self.tool_cards.append(card)
        
        # Update status
        self.status_label.setText(f"{len(tools)} tool(s) displayed")
        
    def on_tool_selected(self, tool: ToolSpecs):
        """Handle tool selection."""
        self.selected_tool = tool
        
        if not self.embed_mode:
            self.select_button.setEnabled(True)
        else:
            # In embed mode, emit signal immediately on selection
            self.toolSelected.emit(tool.id)
        
        # Mark as recently used
        self.library.mark_as_used(tool.id)
        
        # Highlight selected card - only change the perimeter border
        for card in self.tool_cards:
            if card.tool.id == tool.id:
                card.setStyleSheet("""
                    ToolCard {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #3c3c3c, stop:1 #2a2a2a);
                        border: 3px solid #0078d4;
                        border-radius: 8px;
                        color: #ffffff;
                    }
                    ToolCard:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #4a4a4a, stop:1 #383838);
                        border: 3px solid #2196F3;
                    }
                """)
            else:
                # Reset to default dark styling
                card.setStyleSheet("""
                    ToolCard {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #3c3c3c, stop:1 #2a2a2a);
                        border: 1px solid #555555;
                        border-radius: 8px;
                        color: #ffffff;
                    }
                    ToolCard:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                   stop:0 #4a4a4a, stop:1 #383838);
                        border: 2px solid #0078d4;
                    }
                """)
    
    def on_tool_favorited(self, tool_id: str, is_favorite: bool):
        """Handle favorite toggle."""
        if is_favorite:
            self.library.add_to_favorites(tool_id)
        else:
            self.library.remove_from_favorites(tool_id)
    
    def on_tool_deleted(self, tool_id: str):
        """Handle tool deletion."""
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Tool", 
            f"Are you sure you want to delete this tool?\nThis action cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.library.remove_tool(tool_id):
                self.refresh_tools()
                QtWidgets.QMessageBox.information(self, "Success", "Tool deleted successfully.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to delete tool.")
    
    def on_tool_edited(self, tool: ToolSpecs):
        """Handle tool editing."""
        dialog = ToolEditorDialog(tool, self.library, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh_tools()
    
    def select_current_tool(self):
        """Select the current tool and close dialog/emit signal."""
        if self.selected_tool:
            self.toolSelected.emit(self.selected_tool.id)  # Emit tool ID instead of ToolSpecs object
            if not self.embed_mode:
                self.close_widget()
    
    def close_widget(self):
        """Close the widget (handle both dialog and embed modes)."""
        if self.embed_mode:
            # In embed mode, just clear selection or do nothing
            pass
        else:
            # In dialog mode, close the dialog
            self.close()
    
    def clear_search(self):
        """Clear search and filters."""
        self.search_input.clear()
        self.manufacturer_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.diameter_min.setValue(0.0)
        self.diameter_max.setValue(1000.0)
        self.favorites_btn.setChecked(False)
        self.recent_btn.setChecked(False)
        self.filter_tools()
    
    def add_new_tool(self):
        """Add a new tool."""
        dialog = ToolEditorDialog(None, self.library, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh_tools()
    
    def import_tools(self):
        """Import tools from file."""
        QtWidgets.QMessageBox.information(self, "Import Tools", "CSV import functionality coming soon!")
    
    def export_tools(self):
        """Export tools to file."""
        QtWidgets.QMessageBox.information(self, "Export Tools", "CSV export functionality coming soon!")
    
    
    def show_tool_guide(self):
        """Show tool selection guide."""
        if not self.embed_mode:
            dialog = ToolGuideDialog(self)
            dialog.exec_()
    
    def show_project_manager(self):
        """Show project manager dialog."""
        if not self.embed_mode:
            dialog = ProjectManagerDialog(self.library, self)
            dialog.projectsModified.connect(self.refresh_project_filter)
            dialog.exec_()


class ToolEditorDialog(QtWidgets.QDialog):
    """Dialog for editing/creating tools."""
    
    def __init__(self, tool: Optional[ToolSpecs], library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.library = library
        self.is_edit_mode = tool is not None
        
        self.setWindowTitle("✏️ Edit Tool" if self.is_edit_mode else "➕ Add New Tool")
        self.setModal(True)
        self.resize(500, 600)
        self.setup_ui()
        
        if self.is_edit_mode:
            self.populate_fields()
    
    def setup_ui(self):
        """Setup editor UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form layout
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(15)
        
        # Basic info
        self.id_input = QtWidgets.QLineEdit()
        self.manufacturer_combo = QtWidgets.QComboBox()
        self.manufacturer_combo.setEditable(True)
        self.manufacturer_combo.addItems(self.library.manufacturers)
        
        self.series_input = QtWidgets.QLineEdit()
        self.name_input = QtWidgets.QLineEdit()
        
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems([t.replace('_', ' ').title() for t in self.library.tool_types])
        
        # Dimensions with unit selection and fractional input support
        diameter_layout = QtWidgets.QVBoxLayout()
        
        # Input row with text input, dropdown, and unit selector
        input_row = QtWidgets.QHBoxLayout()
        
        # Fractional/decimal input field
        self.diameter_input = QtWidgets.QLineEdit()
        self.diameter_input.setPlaceholderText("1/4 or 0.25")
        self.diameter_input.textChanged.connect(self.on_diameter_text_changed)
        input_row.addWidget(self.diameter_input, 2)
        
        # Common fractions dropdown
        self.fraction_combo = QtWidgets.QComboBox()
        self.fraction_combo.addItem("Common Fractions...")
        common_fractions = get_common_imperial_fractions()
        for display_str, decimal_val in common_fractions:
            if decimal_val <= Decimal('2.0'):  # Limit to reasonable tool sizes
                self.fraction_combo.addItem(f"{display_str} ({float(decimal_val):.4f})", display_str)
        self.fraction_combo.currentTextChanged.connect(self.on_fraction_selected)
        input_row.addWidget(self.fraction_combo, 1)
        
        # Unit selector
        self.unit_combo = QtWidgets.QComboBox()
        self.unit_combo.addItems(["mm", "inch"])
        self.unit_combo.currentTextChanged.connect(self.on_unit_changed)
        input_row.addWidget(self.unit_combo, 0)
        
        diameter_layout.addLayout(input_row)
        
        # Preview/validation label
        self.diameter_preview = QtWidgets.QLabel("")
        self.diameter_preview.setStyleSheet("color: #666666; font-size: 10px; font-style: italic;")
        diameter_layout.addWidget(self.diameter_preview)
        
        self.flutes_input = QtWidgets.QSpinBox()
        self.flutes_input.setRange(1, 20)
        
        self.length_of_cut_input = QtWidgets.QDoubleSpinBox()
        self.length_of_cut_input.setRange(0.1, 1000.0)
        self.length_of_cut_input.setDecimals(2)
        self.length_of_cut_input.setSuffix(" mm")
        
        self.overall_length_input = QtWidgets.QDoubleSpinBox()
        self.overall_length_input.setRange(1.0, 1000.0)
        self.overall_length_input.setDecimals(2)
        self.overall_length_input.setSuffix(" mm")
        
        # Material and coating
        self.coating_combo = QtWidgets.QComboBox()
        self.coating_combo.setEditable(True)
        self.coating_combo.addItems(self.library.coatings)
        
        self.material_combo = QtWidgets.QComboBox()
        self.material_combo.setEditable(True)
        self.material_combo.addItems(self.library.materials)
        
        # Part info
        self.part_number_input = QtWidgets.QLineEdit()
        self.price_input = QtWidgets.QDoubleSpinBox()
        self.price_input.setRange(0.0, 10000.0)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        
        # Notes and tags
        self.notes_input = QtWidgets.QTextEdit()
        self.notes_input.setMaximumHeight(80)
        
        self.tags_input = QtWidgets.QLineEdit()
        self.tags_input.setPlaceholderText("comma, separated, tags")
        
        # URL field with button
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("https://manufacturer.com/tool-page")
        
        url_layout = QtWidgets.QHBoxLayout()
        self.open_url_btn = QtWidgets.QPushButton("🌐 Open")
        self.open_url_btn.setMinimumWidth(80)  # Use minimum instead of fixed
        self.open_url_btn.clicked.connect(self.open_url)
        self.open_url_btn.setEnabled(False)
        
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.open_url_btn)
        
        # Enable/disable button based on URL content
        self.url_input.textChanged.connect(self.on_url_changed)
        
        # Add to form
        form.addRow("Tool ID*:", self.id_input)
        form.addRow("Manufacturer*:", self.manufacturer_combo)
        form.addRow("Series:", self.series_input)
        form.addRow("Name*:", self.name_input)
        form.addRow("Type*:", self.type_combo)
        form.addRow("Diameter*:", diameter_layout)
        form.addRow("Number of Flutes*:", self.flutes_input)
        form.addRow("Length of Cut:", self.length_of_cut_input)
        form.addRow("Overall Length:", self.overall_length_input)
        form.addRow("Coating:", self.coating_combo)
        form.addRow("Material*:", self.material_combo)
        form.addRow("Part Number:", self.part_number_input)
        form.addRow("Price:", self.price_input)
        form.addRow("URL:", url_layout)
        form.addRow("Notes:", self.notes_input)
        form.addRow("Tags:", self.tags_input)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("💾 Save Tool")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.save_tool)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # Assemble layout
        layout.addLayout(form)
        layout.addLayout(button_layout)
        
        # Initialize unit tracking
        self.original_unit = "mm"  # Default to mm
        self.updating_diameter = False  # Flag to prevent recursive updates
        
        # Initialize preview
        self.update_diameter_preview()
        
    def populate_fields(self):
        """Populate fields with existing tool data."""
        if not self.tool:
            return
            
        self.id_input.setText(self.tool.id)
        self.id_input.setEnabled(False)  # Don't allow ID changes
        
        self.manufacturer_combo.setCurrentText(self.tool.manufacturer)
        self.series_input.setText(self.tool.series)
        self.name_input.setText(self.tool.name)
        
        # Find type index
        type_text = self.tool.type.replace('_', ' ').title()
        type_index = self.type_combo.findText(type_text)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        # Set diameter and unit based on tool's original unit
        original_unit = getattr(self.tool, 'original_unit', 'mm')
        original_diameter = getattr(self.tool, 'original_diameter', self.tool.diameter_mm)
        
        self.original_unit = original_unit
        self.unit_combo.setCurrentText(original_unit)
        
        # If we have the original diameter, use that, otherwise use the stored value in the correct unit
        if original_diameter > Decimal('0'):
            diameter_to_show = original_diameter
        else:
            # Fallback: use diameter_mm if original unit is mm, or convert if inch
            if original_unit == "mm":
                diameter_to_show = self.tool.diameter_mm
            else:
                diameter_to_show = self.tool.diameter_inch
        
        # Try to display as fraction for imperial units, otherwise decimal
        if original_unit == "inch":
            fraction_str = decimal_to_fraction_string(diameter_to_show)
            if fraction_str:
                self.diameter_input.setText(fraction_str)
            else:
                self.diameter_input.setText(f"{float(diameter_to_show):.4f}")
        else:
            self.diameter_input.setText(f"{float(diameter_to_show):.3f}")
        self.flutes_input.setValue(self.tool.flutes)
        self.length_of_cut_input.setValue(self.tool.length_of_cut_mm)
        self.overall_length_input.setValue(self.tool.overall_length_mm)
        
        self.coating_combo.setCurrentText(self.tool.coating)
        self.material_combo.setCurrentText(self.tool.material)
        
        self.part_number_input.setText(self.tool.part_number)
        self.price_input.setValue(self.tool.price)
        self.url_input.setText(getattr(self.tool, 'url', ''))
        self.notes_input.setPlainText(self.tool.notes)
        self.tags_input.setText(", ".join(self.tool.tags))
    
    def on_unit_changed(self):
        """Handle unit change - convert diameter value using high-precision Decimal."""
        if self.updating_diameter:
            return
        
        self.updating_diameter = True
        current_text = self.diameter_input.text()
        current_unit = self.unit_combo.currentText()
        
        try:
            # Parse current value
            current_value = parse_fractional_input(current_text)
            
            # Convert value when switching units using precise Decimal arithmetic
            if current_unit == "mm" and self.original_unit == "inch":
                # Convert from inch to mm
                converted_value = current_value * INCH_TO_MM_DECIMAL
                self.diameter_input.setText(f"{float(converted_value):.3f}")
            elif current_unit == "inch" and self.original_unit == "mm":
                # Convert from mm to inch  
                converted_value = current_value * MM_TO_INCH_DECIMAL
                
                # Try to show as fraction for imperial
                fraction_str = decimal_to_fraction_string(converted_value)
                if fraction_str:
                    self.diameter_input.setText(fraction_str)
                else:
                    self.diameter_input.setText(f"{float(converted_value):.4f}")
            
            self.original_unit = current_unit
        except FractionalInputError:
            # If current input is invalid, just update unit tracking
            self.original_unit = current_unit
        
        self.updating_diameter = False
        self.update_diameter_preview()
    
    def on_diameter_text_changed(self):
        """Handle diameter text input change - update preview."""
        self.update_diameter_preview()
    
    def on_fraction_selected(self):
        """Handle selection from common fractions dropdown."""
        if self.fraction_combo.currentIndex() > 0:  # Skip "Common Fractions..." item
            fraction_str = self.fraction_combo.currentData()
            if fraction_str:
                self.diameter_input.setText(fraction_str)
                self.fraction_combo.setCurrentIndex(0)  # Reset dropdown
    
    def update_diameter_preview(self):
        """Update the diameter preview/validation label."""
        current_text = self.diameter_input.text().strip()
        current_unit = self.unit_combo.currentText()
        
        if not current_text:
            self.diameter_preview.setText("")
            return
        
        try:
            # Parse the input
            decimal_value = parse_fractional_input(current_text)
            
            # Show different formats based on current unit
            if current_unit == "inch":
                # For imperial, show both fractional and decimal
                fraction_str = decimal_to_fraction_string(decimal_value)
                mm_value = decimal_value * INCH_TO_MM_DECIMAL
                
                if fraction_str and fraction_str != current_text:
                    preview = f"= {fraction_str}\" ({float(decimal_value):.4f}\") = {float(mm_value):.3f}mm"
                else:
                    preview = f"= {float(decimal_value):.4f}\" = {float(mm_value):.3f}mm"
            else:
                # For metric, show decimal and imperial equivalent
                inch_value = decimal_value * MM_TO_INCH_DECIMAL
                fraction_str = decimal_to_fraction_string(inch_value)
                
                if fraction_str:
                    preview = f"= {float(decimal_value):.3f}mm = {fraction_str}\" ({float(inch_value):.4f}\")"
                else:
                    preview = f"= {float(decimal_value):.3f}mm = {float(inch_value):.4f}\""
            
            self.diameter_preview.setText(preview)
            self.diameter_preview.setStyleSheet("color: #666666; font-size: 10px; font-style: italic;")
            
        except FractionalInputError:
            self.diameter_preview.setText("Invalid input - use format like 1/4, 0.25, or 1 1/2")
            self.diameter_preview.setStyleSheet("color: #cc0000; font-size: 10px; font-style: italic;")
    
    def on_url_changed(self):
        """Enable/disable open button based on URL validity."""
        url = self.url_input.text().strip()
        is_valid = url and (url.startswith('http://') or url.startswith('https://'))
        self.open_url_btn.setEnabled(is_valid)
    
    def open_url(self):
        """Open the URL in the default browser."""
        import webbrowser
        url = self.url_input.text().strip()
        if url:
            try:
                webbrowser.open(url)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to open URL: {str(e)}")
    
    def save_tool(self):
        """Save the tool."""
        # Validate required fields
        diameter_valid = False
        try:
            diameter_value = parse_fractional_input(self.diameter_input.text())
            diameter_valid = diameter_value > 0
        except FractionalInputError:
            diameter_valid = False
        
        if not all([
            self.id_input.text().strip(),
            self.manufacturer_combo.currentText().strip(),
            self.name_input.text().strip(),
            diameter_valid,
            self.flutes_input.value() > 0
        ]):
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Please fill in all required fields (marked with *).")
            return
        
        # Check for ID conflicts (only for new tools)
        if not self.is_edit_mode:
            existing_tool = self.library.get_tool(self.id_input.text().strip())
            if existing_tool:
                QtWidgets.QMessageBox.warning(self, "ID Conflict", "A tool with this ID already exists. Please choose a different ID.")
                return
        
        # Create tool specs with unit tracking using high-precision Decimal
        tool_type = self.type_combo.currentText().lower().replace(' ', '_')
        original_diameter = parse_fractional_input(self.diameter_input.text())
        original_unit = self.unit_combo.currentText()
        tags = [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()]
        
        # Calculate both mm and inch values using precise Decimal arithmetic
        if original_unit == "mm":
            diameter_mm = original_diameter
            diameter_inch = ToolSpecs.mm_to_inch(original_diameter)
        else:  # inch
            diameter_mm = ToolSpecs.inch_to_mm(original_diameter)
            diameter_inch = original_diameter
        
        tool = ToolSpecs(
            id=self.id_input.text().strip(),
            manufacturer=self.manufacturer_combo.currentText().strip(),
            series=self.series_input.text().strip(),
            name=self.name_input.text().strip(),
            type=tool_type,
            diameter_mm=diameter_mm,
            diameter_inch=diameter_inch,
            flutes=self.flutes_input.value(),
            length_of_cut_mm=self.length_of_cut_input.value(),
            overall_length_mm=self.overall_length_input.value(),
            shank_diameter_mm=diameter_mm,  # Default to same as cutting diameter
            coating=self.coating_combo.currentText().strip(),
            material=self.material_combo.currentText().strip(),
            manufacturer_speeds={},  # TODO: Add speed input fields
            manufacturer_feeds={},   # TODO: Add feed input fields
            notes=self.notes_input.toPlainText().strip(),
            part_number=self.part_number_input.text().strip(),
            price=self.price_input.value(),
            url=self.url_input.text().strip(),
            tags=tags,
            # Unit tracking to prevent rounding errors
            original_unit=original_unit,
            original_diameter=original_diameter
        )
        
        # Save tool
        if self.is_edit_mode:
            success = self.library.update_tool(tool)
        else:
            success = self.library.add_tool(tool)
        
        if success:
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Save Error", "Failed to save tool. Please try again.")


class QuickStartDialog(QtWidgets.QDialog):
    """Dialog for quick start tool presets."""
    
    toolsAdded = QtCore.Signal()
    
    def __init__(self, library: ToolLibrary, parent=None):
        super().__init__(parent)
        self.library = library
        
        self.setWindowTitle("🎯 Quick Start Tool Kits")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup quick start UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_label = QtWidgets.QLabel("🎯 Quick Start Tool Kits")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c2c2c;")
        
        # Description
        desc_label = QtWidgets.QLabel(
            "Get started quickly with curated tool kits for common machining applications. "
            "These presets include recommended tools with optimized parameters."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px 0;")
        
        # Kits layout
        kits_layout = QtWidgets.QGridLayout()
        kits_layout.setSpacing(15)
        
        # Hobby Kit
        hobby_kit = self.create_kit_widget(
            "🏠 Hobby Starter Kit", 
            "Perfect for hobbyists and makers\n• 1/8\" and 1/4\" end mills\n• HSS construction\n• Budget-friendly",
            "#17a2b8",
            self.add_hobby_kit
        )
        
        # Professional Aluminum Kit
        aluminum_kit = self.create_kit_widget(
            "✈️ Aluminum Pro Kit", 
            "Optimized for aluminum machining\n• 3-flute design\n• TiAlN coating\n• High-speed capable",
            "#28a745",
            self.add_aluminum_kit
        )
        
        # Micro Precision Kit
        micro_kit = self.create_kit_widget(
            "🔬 Micro Precision Kit", 
            "Ultra-precision micro machining\n• Sub-millimeter tools\n• DLC coating\n• Electronics/Medical",
            "#dc3545",
            self.add_micro_kit
        )
        
        # Steel Kit
        steel_kit = self.create_kit_widget(
            "🏭 Steel Machining Kit", 
            "Heavy-duty steel machining\n• Coated carbide tools\n• Industrial grade\n• High durability",
            "#6f42c1",
            self.add_steel_kit
        )
        
        kits_layout.addWidget(hobby_kit, 0, 0)
        kits_layout.addWidget(aluminum_kit, 0, 1)
        kits_layout.addWidget(micro_kit, 1, 0)
        kits_layout.addWidget(steel_kit, 1, 1)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        # Assemble layout
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(kits_layout)
        layout.addStretch()
        layout.addLayout(button_layout)
    
    def create_kit_widget(self, title: str, description: str, color: str, callback):
        """Create a kit widget."""
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(QtWidgets.QFrame.Box)
        widget.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
                background-color: white;
            }}
            QFrame:hover {{
                background-color: #f8f9fa;
                border-width: 3px;
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Title
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        
        # Description
        desc_label = QtWidgets.QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        
        # Add button
        add_btn = QtWidgets.QPushButton("➕ Add Kit")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        add_btn.clicked.connect(callback)
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(add_btn)
        
        return widget
    
    def add_hobby_kit(self):
        """Add hobby starter kit tools."""
        tools = [
            self.create_tool_from_preset("hobby_001", "Generic", "Hobby Kit", 
                "2-Flute Square End Mill - 1/8\"", "square_endmill", 3.175, 0.125, 2,
                12.0, 38.1, "uncoated", "HSS", "HOBBY-125", 8.99, 
                ["hobby", "starter", "budget", "versatile"]),
            self.create_tool_from_preset("hobby_002", "Generic", "Hobby Kit",
                "2-Flute Square End Mill - 1/4\"", "square_endmill", 6.35, 0.25, 2,
                19.05, 50.8, "uncoated", "HSS", "HOBBY-250", 12.99,
                ["hobby", "starter", "budget", "general_purpose"])
        ]
        self.add_tools_to_library(tools, "Hobby Starter Kit")
    
    def add_aluminum_kit(self):
        """Add aluminum machining kit tools."""
        tools = [
            self.create_tool_from_preset("pro_alu_001", "Professional Tools", "Aluminum Series",
                "3-Flute Aluminum End Mill - 6mm", "square_endmill", 6.0, 0.2362, 3,
                18.0, 60.0, "TiAlN", "carbide", "PRO-ALU-6MM", 35.99,
                ["professional", "aluminum", "coated", "3_flute"])
        ]
        self.add_tools_to_library(tools, "Aluminum Pro Kit")
    
    def add_micro_kit(self):
        """Add micro precision kit tools."""
        tools = [
            self.create_tool_from_preset("micro_001", "Precision Tools", "Micro Series",
                "Micro End Mill - 0.5mm", "square_endmill", 0.5, 0.0197, 2,
                1.5, 38.1, "DLC", "carbide", "MICRO-05MM", 89.99,
                ["micro", "precision", "electronics", "medical"])
        ]
        self.add_tools_to_library(tools, "Micro Precision Kit")
    
    def add_steel_kit(self):
        """Add steel machining kit tools."""
        tools = [
            self.create_tool_from_preset("steel_001", "Industrial Tools", "Steel Series",
                "4-Flute Steel End Mill - 8mm", "square_endmill", 8.0, 0.3150, 4,
                22.0, 75.0, "TiAlN", "carbide", "STEEL-8MM", 42.50,
                ["industrial", "steel", "coated", "4_flute"])
        ]
        self.add_tools_to_library(tools, "Steel Machining Kit")
    
    def create_tool_from_preset(self, tool_id: str, manufacturer: str, series: str,
                               name: str, tool_type: str, diameter_mm: float, diameter_inch: float,
                               flutes: int, length_of_cut: float, overall_length: float,
                               coating: str, material: str, part_number: str, price: float,
                               tags: list) -> ToolSpecs:
        """Create a ToolSpecs object from preset parameters."""
        return ToolSpecs(
            id=tool_id,
            manufacturer=manufacturer,
            series=series,
            name=name,
            type=tool_type,
            diameter_mm=diameter_mm,
            diameter_inch=diameter_inch,
            flutes=flutes,
            length_of_cut_mm=length_of_cut,
            overall_length_mm=overall_length,
            shank_diameter_mm=diameter_mm,
            coating=coating,
            material=material,
            manufacturer_speeds={},
            manufacturer_feeds={},
            notes=f"Part of {series} - optimized for specific applications",
            part_number=part_number,
            price=price,
            url="",
            tags=tags
        )
    
    def add_tools_to_library(self, tools: List[ToolSpecs], kit_name: str):
        """Add tools to the library."""
        added_count = 0
        
        for tool in tools:
            # Check if tool already exists
            if not self.library.get_tool(tool.id):
                if self.library.add_tool(tool):
                    added_count += 1
        
        if added_count > 0:
            QtWidgets.QMessageBox.information(
                self, "Kit Added", 
                f"Successfully added {added_count} tool(s) from {kit_name}!"
            )
            self.toolsAdded.emit()
        else:
            QtWidgets.QMessageBox.information(
                self, "Kit Already Exists", 
                f"All tools from {kit_name} are already in your library."
            )


class ToolGuideDialog(QtWidgets.QDialog):
    """Dialog showing tool selection guidance."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("❓ Tool Selection Guide")
        self.setModal(True)
        self.resize(900, 700)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup guide UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Tab widget for different guides
        tabs = QtWidgets.QTabWidget()
        
        # Material Guide
        material_tab = self.create_material_guide()
        tabs.addTab(material_tab, "📋 Material Guide")
        
        # Application Guide
        application_tab = self.create_application_guide()
        tabs.addTab(application_tab, "🔧 Application Guide")
        
        # Coating Guide
        coating_tab = self.create_coating_guide()
        tabs.addTab(coating_tab, "🎨 Coating Guide")
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addWidget(tabs)
        layout.addLayout(button_layout)
    
    def create_material_guide(self):
        """Create material selection guide."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Material-Specific Tool Recommendations</h2>
        
        <h3>🔷 Aluminum Alloys</h3>
        <ul>
        <li><b>Recommended Coatings:</b> Uncoated, TiAlN, ZrN</li>
        <li><b>Avoid:</b> TiN (can cause aluminum buildup)</li>
        <li><b>Flutes:</b> 2-3 for roughing, 3-6 for finishing</li>
        <li><b>Notes:</b> Sharp tools essential. Use good chip evacuation.</li>
        </ul>
        
        <h3>⚙️ Steel Alloys</h3>
        <ul>
        <li><b>Recommended Coatings:</b> TiN, TiAlN, AlCrN</li>
        <li><b>Flutes:</b> 2-3 for roughing, 4-6 for finishing</li>
        <li><b>Notes:</b> Higher flute count for better surface finish.</li>
        </ul>
        
        <h3>🔧 Stainless Steel</h3>
        <ul>
        <li><b>Recommended Coatings:</b> TiAlN, AlCrN, DLC</li>
        <li><b>Avoid:</b> Uncoated tools</li>
        <li><b>Flutes:</b> 2-3 for roughing, 4 for finishing</li>
        <li><b>Notes:</b> Work hardens rapidly. Maintain consistent feeds.</li>
        </ul>
        
        <h3>🚀 Titanium</h3>
        <ul>
        <li><b>Recommended Coatings:</b> TiAlN, AlCrN</li>
        <li><b>Avoid:</b> TiN, uncoated</li>
        <li><b>Flutes:</b> 2 for roughing, 3-4 for finishing</li>
        <li><b>Notes:</b> Very challenging. Low speeds, high feeds, flood coolant.</li>
        </ul>
        """)
        
        layout.addWidget(text)
        return widget
    
    def create_application_guide(self):
        """Create application guide."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Application-Specific Tool Selection</h2>
        
        <h3>🏗️ Roughing Operations</h3>
        <ul>
        <li><b>Tool Types:</b> Roughing end mills, Square end mills</li>
        <li><b>Flutes:</b> 2-3 (better chip evacuation)</li>
        <li><b>Strategy:</b> Maximize material removal rate</li>
        </ul>
        
        <h3>✨ Finishing Operations</h3>
        <ul>
        <li><b>Tool Types:</b> Square end mills, Ball end mills</li>
        <li><b>Flutes:</b> 4-6 (better surface finish)</li>
        <li><b>Strategy:</b> Optimize for surface quality</li>
        </ul>
        
        <h3>🎯 3D Profiling</h3>
        <ul>
        <li><b>Tool Types:</b> Ball end mills, Corner radius end mills</li>
        <li><b>Flutes:</b> 2-4</li>
        <li><b>Strategy:</b> Consider tool deflection for deep features</li>
        </ul>
        
        <h3>📦 Slotting & Pocketing</h3>
        <ul>
        <li><b>Tool Types:</b> Square end mills, Corner radius</li>
        <li><b>Flutes:</b> 2-3 for slots, 3-4 for pockets</li>
        <li><b>Strategy:</b> Adaptive toolpaths recommended</li>
        </ul>
        
        <h3>🔬 Micro Machining</h3>
        <ul>
        <li><b>Tool Types:</b> Micro end mills, Micro drills</li>
        <li><b>Flutes:</b> 2 (typically)</li>
        <li><b>Strategy:</b> Very high speeds, light cuts, rigid setup</li>
        </ul>
        """)
        
        layout.addWidget(text)
        return widget
    
    def create_coating_guide(self):
        """Create coating guide."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        text.setHtml("""
        <h2>Tool Coating Selection Guide</h2>
        
        <h3>⚪ Uncoated</h3>
        <ul>
        <li><b>Best for:</b> Aluminum, Wood, Plastics</li>
        <li><b>Benefits:</b> Sharp cutting edge, Low cost, Easy to resharpen</li>
        <li><b>Limitations:</b> Lower tool life, Limited speed capability</li>
        </ul>
        
        <h3>🟡 TiN (Titanium Nitride)</h3>
        <ul>
        <li><b>Best for:</b> Steel, Cast iron</li>
        <li><b>Benefits:</b> Good wear resistance, Improved lubricity</li>
        <li><b>Avoid:</b> Aluminum (can cause buildup)</li>
        </ul>
        
        <h3>🟠 TiAlN (Titanium Aluminum Nitride)</h3>
        <ul>
        <li><b>Best for:</b> Steel, Stainless steel, Aluminum, Titanium</li>
        <li><b>Benefits:</b> High temperature resistance, Excellent wear resistance</li>
        <li><b>Notes:</b> Most versatile coating</li>
        </ul>
        
        <h3>🔵 AlCrN (Aluminum Chromium Nitride)</h3>
        <ul>
        <li><b>Best for:</b> Stainless steel, Titanium, Hardened steel</li>
        <li><b>Benefits:</b> Excellent for difficult materials, High temperature stability</li>
        <li><b>Avoid:</b> Aluminum (can cause buildup)</li>
        </ul>
        
        <h3>⚫ DLC (Diamond-Like Carbon)</h3>
        <ul>
        <li><b>Best for:</b> Non-ferrous metals, Composites, Precision work</li>
        <li><b>Benefits:</b> Very low friction, Excellent for precision</li>
        <li><b>Limitations:</b> Temperature sensitive, Very expensive</li>
        </ul>
        """)
        
        layout.addWidget(text)
        return widget