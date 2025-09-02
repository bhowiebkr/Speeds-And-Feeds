"""
Tool configuration UI box for the Speeds and Feeds Calculator.

Contains the ToolBox widget for tool diameter, flute count, and unit selection.
"""

from PySide6 import QtWidgets, QtCore
from ...constants.units import IN_TO_MM, MM_TO_IN
from ...models.tool_library import ToolLibrary, ToolSpecs
from ..tool_library_widget import ToolLibraryWidget


class ToolBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ToolBox, self).__init__(parent)
        self.setTitle("🔧 Tool Info")
        self.setObjectName("tool_box")
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(10)  # Slightly increased for better spacing
        form.setHorizontalSpacing(10)
        self.setLayout(form)
        
        # Initialize tool library
        self.tool_library = ToolLibrary()
        self.current_tool: ToolSpecs = None
        
        # Unit system selection
        self.unit_group = QtWidgets.QButtonGroup(self)
        self.metric_radio = QtWidgets.QRadioButton("Metric (mm)")
        self.imperial_radio = QtWidgets.QRadioButton("Imperial (inches)")
        self.metric_radio.setChecked(True)  # Default to metric
        
        self.unit_group.addButton(self.metric_radio, 0)
        self.unit_group.addButton(self.imperial_radio, 1)
        
        # Create horizontal layout for unit selection
        unit_layout = QtWidgets.QHBoxLayout()
        unit_layout.addWidget(self.metric_radio)
        unit_layout.addWidget(self.imperial_radio)
        unit_widget = QtWidgets.QWidget()
        unit_widget.setLayout(unit_layout)
        
        # Single diameter input that changes units
        self.toolDiameter = QtWidgets.QDoubleSpinBox()
        self.fluteNum = QtWidgets.QSpinBox()
        
        # Set initial ranges and defaults for metric
        self.toolDiameter.setRange(0.1, 200.0)
        self.toolDiameter.setSuffix(" mm")
        self.toolDiameter.setValue(12.0)
        self.toolDiameter.setDecimals(3)
        self.toolDiameter.setToolTip("Tool diameter")
        
        self.fluteNum.setRange(1, 10)
        self.fluteNum.setValue(2)
        self.fluteNum.setToolTip("Number of cutting flutes on the tool")
        
        # Tool library integration
        tool_library_layout = QtWidgets.QHBoxLayout()
        
        # Tool selection button
        self.tool_library_btn = QtWidgets.QPushButton("📚 Tool Library")
        self.tool_library_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:pressed { background-color: #005a9e; }
        """)
        self.tool_library_btn.clicked.connect(self.open_tool_library)
        
        # Current tool info display
        self.current_tool_label = QtWidgets.QLabel("Manual Entry")
        self.current_tool_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        
        tool_library_layout.addWidget(self.tool_library_btn)
        tool_library_layout.addWidget(self.current_tool_label)
        tool_library_layout.addStretch()
        
        tool_library_widget = QtWidgets.QWidget()
        tool_library_widget.setLayout(tool_library_layout)
        
        # Add to layout
        form.addRow("Units", unit_widget)
        form.addRow("Tool Selection", tool_library_widget)
        form.addRow("Tool Diameter", self.toolDiameter)
        form.addRow("Number of flutes (#)", self.fluteNum)
        
        # Connect signals
        self.unit_group.buttonClicked.connect(self.on_unit_changed)
        
        # Store current value in metric for conversions
        self._metric_value = 12.0
        
    def on_unit_changed(self):
        """Handle unit system change"""
        current_value = self.toolDiameter.value()
        current_suffix = self.toolDiameter.suffix()
        
        if self.metric_radio.isChecked():
            # Switch to metric
            if current_suffix == '"':  # Currently imperial
                # Convert current imperial value to metric
                converted_value = current_value * IN_TO_MM
            else:
                converted_value = current_value  # Already metric
                
            self.toolDiameter.blockSignals(True)
            self.toolDiameter.setRange(0.1, 200.0)
            self.toolDiameter.setSuffix(" mm")
            self.toolDiameter.setDecimals(3)
            self.toolDiameter.setSingleStep(0.1)
            self.toolDiameter.setValue(converted_value)
            self.toolDiameter.blockSignals(False)
        else:
            # Switch to imperial
            if current_suffix == " mm":  # Currently metric
                # Convert current metric value to imperial
                converted_value = current_value * MM_TO_IN
            else:
                converted_value = current_value  # Already imperial
                
            self.toolDiameter.blockSignals(True)
            self.toolDiameter.setRange(0.001, 8.0)
            self.toolDiameter.setSuffix('"')
            self.toolDiameter.setDecimals(4)
            self.toolDiameter.setSingleStep(0.001)
            self.toolDiameter.setValue(converted_value)
            self.toolDiameter.blockSignals(False)
    
    def get_diameter_mm(self):
        """Get diameter in millimeters regardless of display units"""
        if self.metric_radio.isChecked():
            return self.toolDiameter.value()
        else:
            return self.toolDiameter.value() * IN_TO_MM
    
    def is_metric(self):
        """Return True if metric units are selected"""
        return self.metric_radio.isChecked()
    
    def open_tool_library(self):
        """Open the tool library dialog."""
        dialog = ToolLibraryWidget(self.tool_library, self)
        dialog.toolSelected.connect(self.on_tool_selected)
        dialog.exec_()
    
    def on_tool_selected(self, tool: ToolSpecs):
        """Handle tool selection from library."""
        self.current_tool = tool
        
        # Update tool diameter (convert to current units)
        diameter_mm = tool.diameter_mm
        
        self.toolDiameter.blockSignals(True)
        if self.is_metric():
            self.toolDiameter.setValue(diameter_mm)
        else:
            self.toolDiameter.setValue(diameter_mm * MM_TO_IN)
        self.toolDiameter.blockSignals(False)
        
        # Update flute count
        self.fluteNum.blockSignals(True)
        self.fluteNum.setValue(tool.flutes)
        self.fluteNum.blockSignals(False)
        
        # Update current tool display
        tool_info = f"{tool.manufacturer} {tool.name[:30]}{'...' if len(tool.name) > 30 else ''}"
        self.current_tool_label.setText(tool_info)
        self.current_tool_label.setStyleSheet("color: #0078d4; font-size: 11px; font-weight: bold;")
        
        # Set tooltip with full tool information
        tooltip = f"""
        <b>{tool.manufacturer} {tool.name}</b><br>
        Part Number: {tool.part_number}<br>
        Diameter: {tool.diameter_mm:.3f}mm ({tool.diameter_inch:.4f}")<br>
        Flutes: {tool.flutes}<br>
        Material: {tool.material}<br>
        Coating: {tool.coating}<br>
        Length of Cut: {tool.length_of_cut_mm}mm<br>
        Overall Length: {tool.overall_length_mm}mm<br>
        """
        if tool.notes:
            tooltip += f"<br>Notes: {tool.notes[:100]}{'...' if len(tool.notes) > 100 else ''}"
        
        self.current_tool_label.setToolTip(tooltip)
        
        # Notify parent that tool changed (trigger recalculation)
        if hasattr(self.parent(), 'toolDiameterChanged'):
            self.parent().toolDiameterChanged()
    
    def get_current_tool(self) -> ToolSpecs:
        """Get currently selected tool from library."""
        return self.current_tool
    
    def clear_tool_selection(self):
        """Clear current tool selection and return to manual entry."""
        self.current_tool = None
        self.current_tool_label.setText("Manual Entry")
        self.current_tool_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        self.current_tool_label.setToolTip("")
    
    def get_tool_info_for_calculations(self) -> dict:
        """Get tool information formatted for calculations."""
        if self.current_tool:
            return {
                'from_library': True,
                'tool_id': self.current_tool.id,
                'manufacturer': self.current_tool.manufacturer,
                'name': self.current_tool.name,
                'part_number': self.current_tool.part_number,
                'diameter_mm': self.current_tool.diameter_mm,
                'flutes': self.current_tool.flutes,
                'material': self.current_tool.material,
                'coating': self.current_tool.coating,
                'manufacturer_speeds': self.current_tool.manufacturer_speeds,
                'manufacturer_feeds': self.current_tool.manufacturer_feeds
            }
        else:
            return {
                'from_library': False,
                'diameter_mm': self.get_diameter_mm(),
                'flutes': self.fluteNum.value()
            }