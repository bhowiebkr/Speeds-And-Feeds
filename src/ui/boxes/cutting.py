"""
Cutting parameters UI box for the Speeds and Feeds Calculator.

Contains the CuttingBox widget for depth/width of cut, surface speeds, and feed rates.
"""

from PySide6 import QtWidgets, QtCore
from ...constants.units import IN_TO_MM, MM_TO_IN, FT_TO_M, M_TO_FT


class CuttingBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(CuttingBox, self).__init__(parent)
        self.setTitle("⚙️ Cutting Operation")
        self.setObjectName("cutting_box")
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(35)  # Further increased spacing to prevent overlap (>34px widget height)
        form.setHorizontalSpacing(10)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.setLayout(form)
        self.setMinimumHeight(550)  # Further increased to accommodate larger spacing
        self.paused = False

        # Single input widgets that adapt to unit system
        self.DOC = QtWidgets.QDoubleSpinBox()
        self.DOC_percent = QtWidgets.QDoubleSpinBox()
        self.WOC = QtWidgets.QDoubleSpinBox()
        self.WOC_percent = QtWidgets.QDoubleSpinBox()
        self.surface_speed = QtWidgets.QDoubleSpinBox()
        self.feed_per_tooth = QtWidgets.QDoubleSpinBox()
        self.Kc = QtWidgets.QDoubleSpinBox()  # Specific cutting force
        
        # Configure widgets with defaults for metric
        self.DOC.setRange(0.001, 50.0)
        self.DOC.setValue(0.5)
        self.DOC.setSuffix(" mm")
        self.DOC.setDecimals(3)
        self.DOC.setMinimumHeight(28)  # Standard spinbox height
        self.DOC.setToolTip("Axial depth of cut")
        
        self.DOC_percent.setRange(0.1, 200.0)
        self.DOC_percent.setValue(4.2)  # 0.5mm / 12mm * 100
        self.DOC_percent.setSuffix(" %")
        self.DOC_percent.setDecimals(1)
        self.DOC_percent.setMinimumHeight(28)  # Standard spinbox height
        self.DOC_percent.setToolTip("Depth of cut as percentage of tool diameter")
        
        self.WOC.setRange(0.001, 100.0)
        self.WOC.setValue(6.0)
        self.WOC.setSuffix(" mm")
        self.WOC.setDecimals(3)
        self.WOC.setMinimumHeight(28)  # Standard spinbox height
        self.WOC.setToolTip("Radial width of cut")
        
        self.WOC_percent.setRange(1, 100)
        self.WOC_percent.setValue(50.0)  # 6mm / 12mm * 100
        self.WOC_percent.setSuffix(" %")
        self.WOC_percent.setDecimals(1)
        self.WOC_percent.setMinimumHeight(28)  # Standard spinbox height
        self.WOC_percent.setToolTip("Width of cut as percentage of tool diameter")
        
        self.surface_speed.setRange(10, 5000)
        self.surface_speed.setValue(400)
        self.surface_speed.setSuffix(" SFM")
        self.surface_speed.setDecimals(0)
        self.surface_speed.setMinimumHeight(28)  # Standard spinbox height
        self.surface_speed.setToolTip("Surface cutting speed")
        
        self.feed_per_tooth.setRange(0.0001, 1.0)
        self.feed_per_tooth.setValue(0.0020)
        self.feed_per_tooth.setSuffix('"')
        self.feed_per_tooth.setDecimals(4)
        self.feed_per_tooth.setMinimumHeight(28)  # Standard spinbox height
        self.feed_per_tooth.setToolTip("Feed per tooth (chipload)")
        
        # Configure Kc (Specific Cutting Force) - always in N/mm²
        self.Kc.setMinimum(500.0)
        self.Kc.setMaximum(4000.0)
        self.Kc.setValue(800.0)  # Default for aluminum
        self.Kc.setSuffix(" N/mm²")
        self.Kc.setMinimumHeight(28)  # Standard spinbox height
        self.Kc.setToolTip("Specific Cutting Force - Material dependent:\nAluminum: 700-900\nMild Steel: 1800-2200\nStainless: 2400-2800\nCast Iron: 1200-1500")

        # Add spacers
        spacer1 = QtWidgets.QWidget()
        spacer1.setFixedHeight(12)  # Increased spacer height
        spacer2 = QtWidgets.QWidget()
        spacer2.setFixedHeight(12)  # Increased spacer height

        # Add to layout
        form.addRow("Depth Of Cut", self.DOC)
        form.addRow("DOC (%)", self.DOC_percent)
        form.addRow(spacer1)
        form.addRow("Width Of Cut", self.WOC)
        form.addRow("WOC (%)", self.WOC_percent)
        form.addRow(spacer2)
        form.addRow("Surface Speed", self.surface_speed)
        form.addRow("Feed per Tooth", self.feed_per_tooth)
        form.addRow("⚡ Specific Cutting Force", self.Kc)

        # Add spacer for HSM controls
        spacer3 = QtWidgets.QWidget()
        spacer3.setFixedHeight(12)
        form.addRow(spacer3)

        # HSM and Chip Thinning controls
        self.hsm_enabled = QtWidgets.QCheckBox("Enable HSM (High Speed Machining)")
        self.hsm_enabled.setToolTip("Enable high speed machining mode with chip thinning compensation")
        
        self.chip_thinning_enabled = QtWidgets.QCheckBox("Apply Chip Thinning Compensation")
        self.chip_thinning_enabled.setEnabled(False)  # Auto-controlled by HSM
        self.chip_thinning_enabled.setToolTip("Automatically compensates feed rates for radial engagement < 50%")
        
        # Tool stickout for deflection calculations
        self.tool_stickout = QtWidgets.QDoubleSpinBox()
        self.tool_stickout.setRange(5.0, 100.0)
        self.tool_stickout.setValue(15.0)  # Conservative default
        self.tool_stickout.setSuffix(" mm")
        self.tool_stickout.setDecimals(1)
        self.tool_stickout.setMinimumHeight(28)
        self.tool_stickout.setToolTip("Tool stickout length for deflection calculations on all tool sizes")

        form.addRow(self.hsm_enabled)
        form.addRow(self.chip_thinning_enabled)
        form.addRow("Tool Stickout", self.tool_stickout)

        # Connect signals for percentage calculations
        self.DOC.valueChanged.connect(self.update_doc_percent)
        self.DOC_percent.valueChanged.connect(self.update_doc_from_percent)
        self.WOC.valueChanged.connect(self.update_woc_percent)
        self.WOC_percent.valueChanged.connect(self.update_woc_from_percent)
        
        # Connect HSM signals
        self.hsm_enabled.stateChanged.connect(self.on_hsm_changed)
        self.chip_thinning_enabled.stateChanged.connect(lambda: self.parent().parent().update() if self.parent() and self.parent().parent() else None)
        self.tool_stickout.valueChanged.connect(lambda: self.parent().parent().update() if self.parent() and self.parent().parent() else None)

    def init(self):
        """Initialize the cutting box with default values"""
        self.update_doc_percent()
        self.update_woc_percent()
    
    def update_doc_percent(self):
        """Update DOC percentage from absolute value"""
        try:
            diameter = self.parent().parent().tool_box.get_diameter_mm()
            if diameter > 0:
                self.DOC_percent.blockSignals(True)
                doc_mm = self.get_doc_mm()
                percentage = (doc_mm / diameter) * 100
                self.DOC_percent.setValue(percentage)
                self.DOC_percent.blockSignals(False)
        except:
            pass  # Ignore errors during initialization
    
    def update_doc_from_percent(self):
        """Update DOC absolute value from percentage"""
        try:
            diameter = self.parent().parent().tool_box.get_diameter_mm()
            if diameter > 0:
                self.DOC.blockSignals(True)
                percentage = self.DOC_percent.value()
                doc_mm = diameter * percentage / 100
                if self.is_metric():
                    self.DOC.setValue(doc_mm)
                else:
                    self.DOC.setValue(doc_mm * MM_TO_IN)
                self.DOC.blockSignals(False)
        except:
            pass
    
    def update_woc_percent(self):
        """Update WOC percentage from absolute value"""
        try:
            diameter = self.parent().parent().tool_box.get_diameter_mm()
            if diameter > 0:
                self.WOC_percent.blockSignals(True)
                woc_mm = self.get_woc_mm()
                percentage = (woc_mm / diameter) * 100
                self.WOC_percent.setValue(min(percentage, 100))  # Cap at 100%
                self.WOC_percent.blockSignals(False)
        except:
            pass
    
    def update_woc_from_percent(self):
        """Update WOC absolute value from percentage"""
        try:
            diameter = self.parent().parent().tool_box.get_diameter_mm()
            if diameter > 0:
                self.WOC.blockSignals(True)
                percentage = self.WOC_percent.value()
                woc_mm = diameter * percentage / 100
                if self.is_metric():
                    self.WOC.setValue(woc_mm)
                else:
                    self.WOC.setValue(woc_mm * MM_TO_IN)
                self.WOC.blockSignals(False)
        except:
            pass
    
    def update_units(self):
        """Update all widgets to match the selected unit system"""
        is_metric = self.is_metric()
        
        # Read current displayed values BEFORE unit change
        current_doc = self.DOC.value()
        current_woc = self.WOC.value()
        current_surface_speed = self.surface_speed.value()
        current_feed = self.feed_per_tooth.value()
        
        # Determine current unit state from suffix
        doc_is_currently_metric = self.DOC.suffix() == " mm"
        surface_is_currently_metric = self.surface_speed.suffix() == " SMM"
        feed_is_currently_metric = self.feed_per_tooth.suffix() == " mm"
        
        # Update DOC
        self.DOC.blockSignals(True)
        if is_metric:
            # Convert to metric if needed
            if not doc_is_currently_metric:  # Currently imperial
                converted_doc = current_doc * IN_TO_MM
            else:
                converted_doc = current_doc
            
            self.DOC.setRange(0.001, 50.0)
            self.DOC.setSuffix(" mm")
            self.DOC.setDecimals(3)
            self.DOC.setSingleStep(0.1)
            self.DOC.setValue(converted_doc)
        else:
            # Convert to imperial if needed
            if doc_is_currently_metric:  # Currently metric
                converted_doc = current_doc * MM_TO_IN
            else:
                converted_doc = current_doc
                
            self.DOC.setRange(0.00004, 2.0)
            self.DOC.setSuffix('"')
            self.DOC.setDecimals(4)
            self.DOC.setSingleStep(0.001)
            self.DOC.setValue(converted_doc)
        self.DOC.blockSignals(False)
        
        # Update WOC
        self.WOC.blockSignals(True)
        if is_metric:
            # Convert to metric if needed
            if not doc_is_currently_metric:  # Use same logic as DOC for consistency
                converted_woc = current_woc * IN_TO_MM
            else:
                converted_woc = current_woc
                
            self.WOC.setRange(0.001, 100.0)
            self.WOC.setSuffix(" mm")
            self.WOC.setDecimals(3)
            self.WOC.setSingleStep(0.1)
            self.WOC.setValue(converted_woc)
        else:
            # Convert to imperial if needed
            if doc_is_currently_metric:  # Use same logic as DOC for consistency
                converted_woc = current_woc * MM_TO_IN
            else:
                converted_woc = current_woc
                
            self.WOC.setRange(0.00004, 4.0)
            self.WOC.setSuffix('"')
            self.WOC.setDecimals(4)
            self.WOC.setSingleStep(0.001)
            self.WOC.setValue(converted_woc)
        self.WOC.blockSignals(False)
        
        # Update surface speed
        self.surface_speed.blockSignals(True)
        if is_metric:
            # Convert to SMM if needed
            if not surface_is_currently_metric:  # Currently SFM
                converted_speed = current_surface_speed * FT_TO_M
            else:
                converted_speed = current_surface_speed
                
            self.surface_speed.setRange(3, 1500)
            self.surface_speed.setSuffix(" SMM")
            self.surface_speed.setDecimals(0)
            self.surface_speed.setValue(converted_speed)
        else:
            # Convert to SFM if needed
            if surface_is_currently_metric:  # Currently SMM
                converted_speed = current_surface_speed * M_TO_FT
            else:
                converted_speed = current_surface_speed
                
            self.surface_speed.setRange(10, 5000)
            self.surface_speed.setSuffix(" SFM")
            self.surface_speed.setDecimals(0)
            self.surface_speed.setValue(converted_speed)
        self.surface_speed.blockSignals(False)
        
        # Update feed per tooth
        self.feed_per_tooth.blockSignals(True)
        if is_metric:
            # Convert to mm if needed
            if not feed_is_currently_metric:  # Currently inches
                converted_feed = current_feed * IN_TO_MM
            else:
                converted_feed = current_feed
                
            self.feed_per_tooth.setRange(0.001, 25.0)
            self.feed_per_tooth.setSuffix(" mm")
            self.feed_per_tooth.setDecimals(4)
            self.feed_per_tooth.setSingleStep(0.001)
            self.feed_per_tooth.setValue(converted_feed)
        else:
            # Convert to inches if needed
            if feed_is_currently_metric:  # Currently mm
                converted_feed = current_feed * MM_TO_IN
            else:
                converted_feed = current_feed
                
            self.feed_per_tooth.setRange(0.00004, 1.0)
            self.feed_per_tooth.setSuffix('"')
            self.feed_per_tooth.setDecimals(4)
            self.feed_per_tooth.setSingleStep(0.0001)
            self.feed_per_tooth.setValue(converted_feed)
        self.feed_per_tooth.blockSignals(False)
    
    def is_metric(self):
        """Check if parent ToolBox is in metric mode"""
        try:
            return self.parent().parent().tool_box.is_metric()
        except:
            return True  # Default to metric
    
    def get_doc_mm(self):
        """Get depth of cut in mm regardless of display units"""
        if self.is_metric():
            return self.DOC.value()
        else:
            return self.DOC.value() * IN_TO_MM
    
    def get_woc_mm(self):
        """Get width of cut in mm regardless of display units"""
        if self.is_metric():
            return self.WOC.value()
        else:
            return self.WOC.value() * IN_TO_MM
    
    def get_surface_speed_sfm(self):
        """Get surface speed in SFM regardless of display units"""
        if self.is_metric():
            return self.surface_speed.value() * M_TO_FT
        else:
            return self.surface_speed.value()
    
    def get_feed_per_tooth_mm(self):
        """Get feed per tooth in mm regardless of display units"""
        if self.is_metric():
            return self.feed_per_tooth.value()
        else:
            return self.feed_per_tooth.value() * IN_TO_MM
    
    def on_hsm_changed(self):
        """Handle HSM mode toggle"""
        if self.hsm_enabled.isChecked():
            # HSM enabled - auto-enable chip thinning
            self.chip_thinning_enabled.setChecked(True)
            self.chip_thinning_enabled.setEnabled(False)  # Auto-controlled
        else:
            # HSM disabled - allow manual chip thinning control
            self.chip_thinning_enabled.setEnabled(True)
        
        # Trigger update if parent exists
        try:
            self.parent().parent().update()
        except:
            pass
    
    def is_hsm_enabled(self):
        """Check if HSM mode is enabled"""
        return self.hsm_enabled.isChecked()
    
    def is_chip_thinning_enabled(self):
        """Check if chip thinning compensation is enabled"""
        return self.chip_thinning_enabled.isChecked()
    
    def get_tool_stickout_mm(self):
        """Get tool stickout in mm"""
        return self.tool_stickout.value()

    def set_material_context(self, material_key: str):
        """Adjust UI emphasis based on material type."""        
        # Create tooltips based on material
        if 'aluminum' in material_key.lower():
            # For aluminum, surface speed is less critical - many speeds work
            self.surface_speed.setToolTip("Surface speed for aluminum (less critical - wide range works)")
            
            # Make chip load more prominent for aluminum
            self.feed_per_tooth.setToolTip("⭐ CRITICAL: Chip load for aluminum - affects surface finish significantly")
            
        elif 'steel' in material_key.lower():
            # For steel, surface speed is more critical for tool life
            self.surface_speed.setToolTip("⭐ CRITICAL: Surface speed for steel - directly affects tool life")
            
            # Chip load important but not as variable
            self.feed_per_tooth.setToolTip("Chip load for steel - important for proper chip evacuation")
        
        else:
            # Default tooltips
            self.surface_speed.setToolTip("Surface cutting speed")
            self.feed_per_tooth.setToolTip("Feed per tooth (chipload)")