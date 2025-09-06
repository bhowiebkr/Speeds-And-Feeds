"""
Results display UI box for the Speeds and Feeds Calculator.

Contains the ResultsBox widget for displaying calculated results and dashboard.
"""

from PySide6 import QtWidgets, QtCore
from ...constants.machining import MachineRigidity
from ...formulas.power import calculate_torque


class ResultsBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ResultsBox, self).__init__(parent)
        self.setTitle("📊 Results Dashboard")
        self.setObjectName("results_box")
        
        # Import dashboard widgets
        from ...components.dashboard_widgets import RangeBarWidget, GradientType
        
        # Main layout - directly use the dashboard
        mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainLayout)
        
        # Create dashboard view directly
        self._create_dashboard_view(mainLayout)
    
    def _create_dashboard_view(self, main_layout):
        """Create the graphical dashboard view."""
        from ...components.dashboard_widgets import RangeBarWidget, GradientType
        
        # All parameters use consistent gradient bars
        bars_layout = QtWidgets.QGridLayout()
        
        # RPM bar - bell curve (optimal RPM in middle based on preferred value)
        self.rpm_bar = RangeBarWidget()
        self.rpm_bar.setLabel("Spindle Speed")
        self.rpm_bar.setUnit("RPM")
        self.rpm_bar.setGradientType(GradientType.BELL_CURVE)
        
        # Feed Rate bars - bell curve (optimal feed rates in middle)
        self.feed_bar = RangeBarWidget()
        self.feed_bar.setLabel("Feed Rate")
        self.feed_bar.setUnit("mm/min")
        self.feed_bar.setGradientType(GradientType.BELL_CURVE)
        
        self.feed_imp_bar = RangeBarWidget() 
        self.feed_imp_bar.setLabel("Feed Rate")
        self.feed_imp_bar.setUnit("in/min")
        self.feed_imp_bar.setGradientType(GradientType.BELL_CURVE)
        
        # MRR bar - bell curve (optimal efficiency in middle)
        self.mrr_bar = RangeBarWidget()
        self.mrr_bar.setLabel("Material Removal Rate") 
        self.mrr_bar.setUnit("cm³/min")
        self.mrr_bar.setGradientType(GradientType.BELL_CURVE)
        
        # Power bars - ascending (higher efficiency is better, but watch limits)
        self.kw_bar = RangeBarWidget()
        self.kw_bar.setLabel("Power")
        self.kw_bar.setUnit("kW")
        self.kw_bar.setGradientType(GradientType.ASCENDING)
        self.kw_bar.setShowPercentage(True)  # Show percentage of spindle capacity
        
        self.hp_bar = RangeBarWidget()
        self.hp_bar.setLabel("Power") 
        self.hp_bar.setUnit("HP")
        self.hp_bar.setGradientType(GradientType.ASCENDING)
        self.hp_bar.setShowPercentage(True)  # Show percentage of spindle capacity
        
        # Torque bar - ascending (higher torque capability is better)
        self.torque_bar = RangeBarWidget()
        self.torque_bar.setLabel("Spindle Torque")
        self.torque_bar.setUnit("Nm")
        self.torque_bar.setGradientType(GradientType.ASCENDING)
        
        # Deflection bar - ascending (lower deflection is better, but show the actual values)
        self.deflection_bar = RangeBarWidget()
        self.deflection_bar.setLabel("Tool Deflection")
        self.deflection_bar.setUnit("mm")
        self.deflection_bar.setGradientType(GradientType.ASCENDING)  # Higher values are concerning
        
        # Advanced info display
        self.advanced_info = QtWidgets.QLabel("Select material and set parameters for advanced calculations")
        self.advanced_info.setWordWrap(True)
        self.advanced_info.setStyleSheet("color: #aaa; font-size: 10px; padding: 8px; border: 1px solid #444; background-color: #2a2a2a;")
        self.advanced_info.setMinimumHeight(80)
        
        # Add bars to grid layout - reorganized for better space usage
        bars_layout.addWidget(self.rpm_bar, 0, 0)           # RPM in single column now
        bars_layout.addWidget(self.deflection_bar, 0, 1)    # Deflection next to RPM
        bars_layout.addWidget(self.feed_bar, 1, 0)
        bars_layout.addWidget(self.feed_imp_bar, 1, 1)
        bars_layout.addWidget(self.mrr_bar, 2, 0) 
        bars_layout.addWidget(self.torque_bar, 2, 1)        # Torque next to MRR
        bars_layout.addWidget(self.kw_bar, 3, 0)
        bars_layout.addWidget(self.hp_bar, 3, 1)
        bars_layout.addWidget(self.advanced_info, 4, 0, 1, 2)  # Advanced info spans both columns
        
        main_layout.addLayout(bars_layout)
        main_layout.addStretch()
    
    
    def update_dashboard_values(self, fs, rpm_status, rpm_message, machine_limits, spindle_capacity_kw, material_info=None, warnings=None, rigidity_info=None):
        """Update dashboard widgets with new values."""
        
        if hasattr(self, 'rpm_bar'):
            # Check unit system from parent GUI
            is_metric = True
            try:
                is_metric = self.parent().tool_box.is_metric()
            except:
                is_metric = True  # Default to metric
            
            min_rpm, preferred_rpm, max_rpm = machine_limits
            
            # Update RPM bar with bell curve gradient centered on preferred RPM
            self.rpm_bar.setRange(min_rpm, max_rpm)
            self.rpm_bar.setPreferredValue(preferred_rpm)
            self.rpm_bar.setValue(fs.rpm)
            
            # Feed Rate bars - show only the appropriate one based on unit system
            optimal_feed = fs.feed if fs.feed > 0 else 1000  # Default to 1000 mm/min if zero
            
            if is_metric:
                self.feed_bar.setVisible(True)
                self.feed_imp_bar.setVisible(False)
                self.feed_bar.setIntelligentRange(fs.feed, optimal_feed, 1.2)
                self.feed_bar.setValue(fs.feed)
            else:
                self.feed_bar.setVisible(False)
                self.feed_imp_bar.setVisible(True)
                optimal_feed_imp = optimal_feed * 0.0393701
                self.feed_imp_bar.setIntelligentRange(fs.feed * 0.0393701, optimal_feed_imp, 1.2)
                self.feed_imp_bar.setValue(fs.feed * 0.0393701)
            
            # MRR bar - use intelligent range with typical MRR values
            typical_mrr = max(fs.mrr, 5.0) if fs.mrr > 0 else 15.0  # Default typical MRR
            self.mrr_bar.setIntelligentRange(fs.mrr, typical_mrr, 1.8)
            self.mrr_bar.setValue(fs.mrr)
            
            # Torque calculation and display
            torque = calculate_torque(fs.kw, fs.rpm)
            max_torque = calculate_torque(spindle_capacity_kw, min_rpm) if min_rpm > 0 else 50  # Estimate max torque
            self.torque_bar.setRange(0, max_torque)
            self.torque_bar.setPreferredValue(max_torque * 0.8)  # 80% of max torque
            self.torque_bar.setValue(torque)
            
            # Power bars - show only the appropriate one based on unit system
            if is_metric:
                self.kw_bar.setVisible(True)
                self.hp_bar.setVisible(False)
                self.kw_bar.setRange(0, spindle_capacity_kw)
                self.kw_bar.setPreferredValue(spindle_capacity_kw * 0.7)  # 70% efficiency sweet spot
                self.kw_bar.setValue(fs.kw)
            else:
                self.kw_bar.setVisible(False)
                self.hp_bar.setVisible(True)
                spindle_capacity_hp = spindle_capacity_kw * 1.34102
                self.hp_bar.setRange(0, spindle_capacity_hp)  
                self.hp_bar.setPreferredValue(spindle_capacity_hp * 0.7)  # 70% efficiency sweet spot
                self.hp_bar.setValue(fs.kw * 1.34102)
            
            # Deflection bar - show deflection values prominently
            if hasattr(fs, 'tool_deflection') and fs.tool_deflection > 0:
                # Set intelligent range based on tool diameter
                max_deflection = fs.diameter * 0.1 if fs.diameter > 0 else 0.1  # 10% of diameter max
                warning_deflection = fs.diameter * 0.05 if fs.diameter > 0 else 0.05  # 5% warning threshold
                self.deflection_bar.setRange(0, max_deflection)
                self.deflection_bar.setPreferredValue(warning_deflection)  # 5% deflection is warning level
                self.deflection_bar.setValue(fs.tool_deflection)
                self.deflection_bar.setVisible(True)
            else:
                # Hide deflection bar if no deflection data
                self.deflection_bar.setValue(0)
                self.deflection_bar.setVisible(False)
            
            # Update advanced info display
            self._update_advanced_info(fs, torque, material_info, warnings, rigidity_info, is_metric)
    
    def _update_advanced_info(self, fs, torque, material_info=None, warnings=None, rigidity_info=None, is_metric=True):
        """Update the advanced information display."""
        info_lines = []
        
        # Basic calculations with appropriate units
        info_lines.append(f"⚙️ Calculated Parameters:")
        
        if is_metric:
            feed_text = f"{fs.feed:.1f} mm/min"
            power_text = f"{fs.kw:.3f} kW"
        else:
            feed_imperial = fs.feed * 0.0393701
            power_hp = fs.kw * 1.34102
            feed_text = f"{feed_imperial:.2f} in/min"
            power_text = f"{power_hp:.3f} HP"
            
        info_lines.append(f"   RPM: {fs.rpm:.0f} | Feed: {feed_text} | MRR: {fs.mrr:.2f} cm³/min")
        info_lines.append(f"   Power: {power_text} | Torque: {torque:.2f} Nm")
        
        # 📐 Deflection Analysis (for ALL tools now) - More prominent display
        if hasattr(fs, 'tool_deflection') and fs.tool_deflection > 0:
            deflection_percent = (fs.tool_deflection / fs.diameter) * 100 if fs.diameter > 0 else 0
            info_lines.append(f"")
            info_lines.append(f"📐 DEFLECTION: {fs.tool_deflection:.4f}mm ({deflection_percent:.2f}% of {fs.diameter:.1f}mm tool)")
            info_lines.append(f"   Cutting Force: {fs.cutting_force:.1f}N | Stickout: {fs.tool_stickout:.1f}mm")
            
            # More prominent deflection status
            if deflection_percent > 5:
                info_lines.append(f"   🔴 HIGH DEFLECTION - Reduce feeds/DOC immediately")
            elif deflection_percent > 2:
                info_lines.append(f"   🟡 MODERATE DEFLECTION - Monitor surface finish")
            elif deflection_percent > 0.5:
                info_lines.append(f"   🟢 ACCEPTABLE DEFLECTION - Good for precision")
            else:
                info_lines.append(f"   🟢 EXCELLENT RIGIDITY - Minimal deflection")
        
        # 🚀 HSM Parameters (when enabled)
        if hasattr(fs, 'hsm_enabled') and fs.hsm_enabled:
            info_lines.append(f"")
            info_lines.append(f"🚀 HSM Parameters:")
            if hasattr(fs, 'chip_thinning_factor'):
                base_feed = fs.feed / fs.chip_thinning_factor if fs.chip_thinning_factor > 0 else fs.feed
                engagement_percent = (fs.woc / fs.diameter) * 100 if fs.diameter > 0 else 0
                info_lines.append(f"   Chip Thinning Factor: {fs.chip_thinning_factor:.2f}x")
                info_lines.append(f"   Compensated Feed: {fs.feed:.0f} mm/min (base: {base_feed:.0f} mm/min)")
                info_lines.append(f"   Radial Engagement: {engagement_percent:.1f}% ({fs.woc:.2f}mm of {fs.diameter:.1f}mm tool)")
        
        # Micro tool specific information
        if hasattr(fs, 'is_micro_tool') and fs.is_micro_tool:
            info_lines.append(f"")
            info_lines.append(f"🔬 Micro Tool Analysis ({fs.diameter:.1f}mm):")
            info_lines.append(f"   Effective Chipload: {fs.adjusted_mmpt:.4f}mm ({fs.adjusted_mmpt*0.0393701:.4f}\")")
        else:
            info_lines.append(f"")
            info_lines.append(f"🔧 Standard Tool ({fs.diameter:.1f}mm): Chipload {fs.adjusted_mmpt:.4f}mm ({fs.adjusted_mmpt*0.0393701:.4f}\")")
        
        # Rigidity adjustment info if available and different from original
        if rigidity_info and hasattr(fs, 'adjusted_mmpt'):
            rigidity_level, rigidity_name = rigidity_info
            if rigidity_level != MachineRigidity.VMC_INDUSTRIAL:
                # Show rigidity adjustments if parameters were modified
                original_different = (
                    abs(fs.mmpt - fs.adjusted_mmpt) > 0.001 or 
                    abs(fs.doc - fs.adjusted_doc) > 0.001 or
                    abs(fs.woc - fs.adjusted_woc) > 0.001
                )
                if original_different:
                    info_lines.append(f"🏗️ Rigidity Adjustments ({rigidity_name}):")
                    if abs(fs.mmpt - fs.adjusted_mmpt) > 0.001:
                        info_lines.append(f"   Chip Load: {fs.mmpt:.4f} → {fs.adjusted_mmpt:.4f} mm/tooth")
                    if abs(fs.doc - fs.adjusted_doc) > 0.001:
                        info_lines.append(f"   DOC: {fs.doc:.2f} → {fs.adjusted_doc:.2f} mm")
                    if abs(fs.woc - fs.adjusted_woc) > 0.001:
                        info_lines.append(f"   WOC: {fs.woc:.2f} → {fs.adjusted_woc:.2f} mm")
        
        # Material info if available
        if material_info:
            material_key, kc, sfm, smm, chip_load, name = material_info
            info_lines.append(f"📦 Material: {name}")
            info_lines.append(f"   Kc: {kc} N/mm² | Recommended Speed: {sfm} SFM ({smm:.1f} SMM)")
        
        # Warnings if any
        if warnings and len(warnings) > 0:
            info_lines.append(f"⚠️  Warnings: {warnings[0]}")
            if len(warnings) > 1:
                info_lines.append(f"    + {len(warnings)-1} more warning(s)")
        
        # Performance indicators
        if fs.kw > 0 and fs.mrr > 0:
            efficiency = fs.mrr / fs.kw  # cm³/min per kW
            info_lines.append(f"📈 Efficiency: {efficiency:.1f} cm³/min/kW")
        
        self.advanced_info.setText("\n".join(info_lines))