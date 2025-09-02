import sys
import os
import logging

from PySide6 import QtWidgets, QtCore, QtGui

from src.components.widgets import IntInput, DoubleInput, MaterialCombo, CoatingCombo


from src.formulas import FeedsAndSpeeds, chip_load_rule_of_thumb, adjust_speed_for_coating, validate_machining_parameters, MachineRigidity, MACHINE_RIGIDITY_FACTORS

IN_TO_MM = 25.4
MM_TO_IN = 0.0393701
FT_TO_M = 0.3048
FT_TO_MM = 304.8
MM_TO_FT = 0.00328084
M_TO_FT = 3.28084


class ToolBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ToolBox, self).__init__(parent)
        self.setTitle("🔧 Tool Info")
        self.setObjectName("tool_box")
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(10)  # Slightly increased for better spacing
        form.setHorizontalSpacing(10)
        self.setLayout(form)
        
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
        
        # Add to layout
        form.addRow("Units", unit_widget)
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


class MaterialBox(QtWidgets.QGroupBox):
    """Material selection and tool coating options."""
    
    # Signal emitted when material properties change
    materialChanged = QtCore.Signal(str, float, float, float, float, str)  # key, kc, sfm, smm, chip_load, name
    coatingChanged = QtCore.Signal(str, float)  # coating_key, multiplier
    
    def __init__(self, parent=None):
        super(MaterialBox, self).__init__(parent)
        self.setTitle("📦 Material & Tool")
        self.setObjectName("material_box")
        
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(10)  # Increased for better spacing
        form.setHorizontalSpacing(10)
        self.setLayout(form)
        
        # Material selection
        self.materialCombo = MaterialCombo()
        self.materialCombo.setToolTip("Select workpiece material to auto-populate optimal cutting parameters")
        
        # Tool coating selection
        self.coatingCombo = CoatingCombo()
        self.coatingCombo.setToolTip("Select tool coating to adjust cutting speeds automatically")
        
        # Material info display (read-only)
        self.materialInfo = QtWidgets.QLabel("Select a material for recommendations")
        self.materialInfo.setWordWrap(True)
        self.materialInfo.setMinimumHeight(40)  # Ensure minimum height for multi-line text
        self.materialInfo.setAlignment(QtCore.Qt.AlignTop)
        self.materialInfo.setStyleSheet("color: #888; font-size: 11px; padding: 5px; border: 1px solid #ddd; border-radius: 3px; background-color: #f9f9f9;")
        
        # Suggest parameters button
        self.suggestButton = QtWidgets.QPushButton("💡 Suggest Parameters")
        self.suggestButton.setToolTip("Use rule-of-thumb calculations to suggest optimal parameters")
        self.suggestButton.clicked.connect(self.suggest_parameters)
        
        # Presets dropdown
        self.presetsCombo = QtWidgets.QComboBox()
        self.presetsCombo.addItem("Select Preset...")
        self.presetsCombo.addItem("🔹 Aluminum Roughing (1-Flute) - Maximum MRR")
        self.presetsCombo.addItem("🔹 Aluminum Roughing (2-Flute) - Balanced")
        self.presetsCombo.addItem("🔹 Aluminum Finishing - High Quality")
        self.presetsCombo.addItem("🔸 Steel Roughing - Conservative")
        self.presetsCombo.addItem("🔸 Steel Finishing - Precision")
        self.presetsCombo.setToolTip("Quick presets for common operations")
        self.presetsCombo.currentTextChanged.connect(self.apply_preset)
        
        # Add to form
        form.addRow("Material", self.materialCombo)
        form.addRow("Tool Coating", self.coatingCombo)
        form.addRow("Quick Presets", self.presetsCombo)
        form.addRow("", self.materialInfo)  # Empty label for info display
        form.addRow("", self.suggestButton)
        
        # Connect signals
        self.materialCombo.materialSelected.connect(self.on_material_selected)
        self.coatingCombo.coatingSelected.connect(self.on_coating_selected)
        
        # Store current selections
        self.current_material = None
        self.current_coating = ('uncoated', 1.0)
    
    def on_material_selected(self, material_key: str, kc: float, sfm: float, smm: float, chip_load: float, name: str):
        """Handle material selection."""
        self.current_material = (material_key, kc, sfm, smm, chip_load, name)
        
        # Update info display
        info_text = f"{name}\n"
        info_text += f"Surface Speed: {sfm} SFM ({smm:.1f} SMM)\n"
        info_text += f"Specific Cutting Force: {kc} N/mm²\n"
        info_text += f"Recommended Chip Load: {chip_load} mm/tooth"
        self.materialInfo.setText(info_text)
        
        # Apply coating multiplier if not uncoated
        if self.current_coating[1] != 1.0:
            adjusted_sfm = adjust_speed_for_coating(sfm, self.current_coating[0])
            adjusted_smm = adjusted_sfm * 0.3048
        else:
            adjusted_sfm = sfm
            adjusted_smm = smm
        
        # Emit signal with adjusted values
        self.materialChanged.emit(material_key, kc, adjusted_sfm, adjusted_smm, chip_load, name)
    
    def on_coating_selected(self, coating_key: str, multiplier: float):
        """Handle coating selection."""
        self.current_coating = (coating_key, multiplier)
        
        # If material is selected, re-emit with adjusted speeds
        if self.current_material:
            material_key, kc, base_sfm, base_smm, chip_load, name = self.current_material
            adjusted_sfm = adjust_speed_for_coating(base_sfm, coating_key)
            adjusted_smm = adjusted_sfm * 0.3048
            
            # Update info display
            speed_change = int((multiplier - 1.0) * 100)
            if speed_change > 0:
                speed_text = f" (+{speed_change}% for coating)"
            else:
                speed_text = ""
                
            info_text = f"{name}{speed_text}\n"
            info_text += f"Surface Speed: {adjusted_sfm:.0f} SFM ({adjusted_smm:.1f} SMM)\n"
            info_text += f"Specific Cutting Force: {kc} N/mm²\n"
            info_text += f"Recommended Chip Load: {chip_load} mm/tooth"
            self.materialInfo.setText(info_text)
            
            # Emit adjusted values
            self.materialChanged.emit(material_key, kc, adjusted_sfm, adjusted_smm, chip_load, name)
        
        # Emit coating change
        self.coatingChanged.emit(coating_key, multiplier)
    
    def suggest_parameters(self):
        """Suggest parameters using rule-of-thumb calculations."""
        # Get tool diameter from parent
        try:
            # Find the main GUI window to access tool_box
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'tool_box'):
                main_window = main_window.parent()
            
            if not main_window or not hasattr(main_window, 'tool_box'):
                raise AttributeError("Cannot find tool_box in parent hierarchy")
                
            tool_diameter = main_window.tool_box.toolDiameter.value()
            
            if self.current_material:
                material_key, kc, sfm, smm, chip_load, name = self.current_material
                
                # Get current flute count to provide context-aware suggestions
                current_flutes = main_window.tool_box.fluteNum.value()
                
                # Use rule of thumb for chip load based on material AND flute count
                if 'aluminum' in material_key.lower():
                    if current_flutes == 1:
                        # Single flute aluminum - much higher chip loads possible
                        suggested_chip_load = chip_load_rule_of_thumb(tool_diameter, 3.0)  # 3x for single flute aluminum
                        flute_advice = "Single-flute: Excellent for roughing, maximum MRR"
                    elif current_flutes == 2:
                        suggested_chip_load = chip_load_rule_of_thumb(tool_diameter, 2.0)  # 2x for 2-flute aluminum
                        flute_advice = "2-flute: Good balance of finish and MRR"
                    else:
                        suggested_chip_load = chip_load_rule_of_thumb(tool_diameter, 1.5)  # 1.5x for 3+ flute aluminum
                        flute_advice = "Multi-flute: Best for finishing operations"
                elif 'steel' in material_key.lower():
                    suggested_chip_load = chip_load_rule_of_thumb(tool_diameter, 1.0)  # 1x for steel  
                    flute_advice = "Steel: Conservative chip loads recommended"
                elif 'stainless' in material_key.lower():
                    suggested_chip_load = chip_load_rule_of_thumb(tool_diameter, 0.5)  # 0.5x for stainless
                    flute_advice = "Stainless: Very conservative to avoid work hardening"
                else:
                    suggested_chip_load = chip_load_rule_of_thumb(tool_diameter, 1.0)  # Default
                    flute_advice = "General recommendation"
                
                # Show suggestion in a message box
                msg = QtWidgets.QMessageBox(self)
                msg.setWindowTitle("Parameter Suggestions")
                msg.setIcon(QtWidgets.QMessageBox.Information)
                
                suggestion_text = f"For {name} with {tool_diameter}mm {current_flutes}-flute tool:\n\n"
                suggestion_text += f"Recommended Chip Load:\n"
                suggestion_text += f"  Rule of Thumb: {suggested_chip_load:.4f} mm/tooth\n"
                suggestion_text += f"  Material Default: {chip_load:.4f} mm/tooth\n"
                suggestion_text += f"  {flute_advice}\n\n"
                suggestion_text += f"Surface Speed: {sfm} SFM ({smm:.1f} SMM)\n"
                suggestion_text += f"Specific Cutting Force: {kc} N/mm²\n\n"
                if 'aluminum' in material_key.lower() and current_flutes > 1:
                    suggestion_text += f"💡 Consider 1-flute for maximum roughing MRR\n\n"
                suggestion_text += "Apply these suggestions?"
                
                msg.setText(suggestion_text)
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                
                if msg.exec() == QtWidgets.QMessageBox.Yes:
                    # Apply suggestions to GUI
                    main_window.cutting_box.Kc.setValue(kc)
                    
                    # Set values based on current unit system
                    main_window.cutting_box.surface_speed.blockSignals(True)
                    main_window.cutting_box.feed_per_tooth.blockSignals(True)
                    
                    if main_window.tool_box.is_metric():
                        main_window.cutting_box.surface_speed.setValue(smm)
                        main_window.cutting_box.feed_per_tooth.setValue(suggested_chip_load)
                    else:
                        main_window.cutting_box.surface_speed.setValue(sfm)
                        main_window.cutting_box.feed_per_tooth.setValue(suggested_chip_load * MM_TO_IN)
                    
                    main_window.cutting_box.surface_speed.blockSignals(False)
                    main_window.cutting_box.feed_per_tooth.blockSignals(False)
            
            else:
                # No material selected
                QtWidgets.QMessageBox.information(
                    self, 
                    "Select Material", 
                    "Please select a material first to get parameter suggestions."
                )
        
        except AttributeError:
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Unable to access tool parameters. Make sure tool diameter is set."
            )
    
    def apply_preset(self, preset_name: str):
        """Apply material-aware preset configurations."""
        if not preset_name or preset_name.startswith("Select"):
            return
            
        try:
            # Find the main GUI window to access tool_box
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'tool_box'):
                main_window = main_window.parent()
            
            if not main_window or not hasattr(main_window, 'tool_box'):
                raise AttributeError("Cannot find tool_box in parent hierarchy")
                
            tool_diameter = main_window.tool_box.toolDiameter.value()
            
            # Get machine rigidity for adjusting presets
            machine_rigidity = main_window.machine_box.get_selected_rigidity()
            rigidity_factors = MACHINE_RIGIDITY_FACTORS.get(machine_rigidity, MACHINE_RIGIDITY_FACTORS[MachineRigidity.VMC_INDUSTRIAL])
            
            # Define preset configurations (adjusted for machine rigidity)
            presets = {
                "🔹 Aluminum Roughing (1-Flute) - Maximum MRR": {
                    "material": "aluminum_6061",
                    "operation": "roughing",
                    "doc": min(tool_diameter * 0.6 * rigidity_factors['doc_factor'], 4.0),  # Adjusted for rigidity
                    "woc": min(tool_diameter * 1.0 * rigidity_factors['woc_factor'], 12.0),  # Adjusted for rigidity
                    "surface_speed_multiplier": 1.1,  # Higher speed for single flute
                    "chip_load_multiplier": 1.25 * rigidity_factors['chipload_factor'],  # Adjusted for rigidity (conservative single flute)
                    "flutes": 1  # Single flute for maximum MRR
                },
                "🔹 Aluminum Roughing (2-Flute) - Balanced": {
                    "material": "aluminum_6061",
                    "operation": "roughing",
                    "doc": min(tool_diameter * 0.4 * rigidity_factors['doc_factor'], 3.0),  # Adjusted for rigidity
                    "woc": min(tool_diameter * 0.8 * rigidity_factors['woc_factor'], 8.0),  # Adjusted for rigidity
                    "surface_speed_multiplier": 1.0,
                    "chip_load_multiplier": 1.3 * rigidity_factors['chipload_factor'],  # Adjusted for rigidity
                    "flutes": 2  # 2-flute for balanced approach
                },
                "🔹 Aluminum Finishing - High Quality": {
                    "material": "aluminum_6061", 
                    "operation": "finishing",
                    "doc": min(tool_diameter * 0.1 * rigidity_factors['doc_factor'], 0.5),  # Adjusted for rigidity
                    "woc": min(tool_diameter * 0.4 * rigidity_factors['woc_factor'], 2.0),  # Adjusted for rigidity
                    "surface_speed_multiplier": 1.2,  # Higher speed for finish
                    "chip_load_multiplier": 0.7 * rigidity_factors['chipload_factor'],  # Adjusted for rigidity
                    "flutes": 4  # 4-flute for finishing
                },
                "🔸 Steel Roughing - Conservative": {
                    "material": "steel_1018",
                    "operation": "roughing", 
                    "doc": min(tool_diameter * 0.3 * rigidity_factors['doc_factor'], 2.0),  # Adjusted for rigidity
                    "woc": min(tool_diameter * 0.6 * rigidity_factors['woc_factor'], 4.0),  # Adjusted for rigidity
                    "surface_speed_multiplier": 0.9 if machine_rigidity != MachineRigidity.ROUTER else 0.7,  # Extra conservative for router+steel
                    "chip_load_multiplier": 1.2 * rigidity_factors['chipload_factor'],  # Adjusted for rigidity
                    "flutes": 2  # 2-flute for roughing
                },
                "🔸 Steel Finishing - Precision": {
                    "material": "steel_1018",
                    "operation": "finishing",
                    "doc": min(tool_diameter * 0.05 * rigidity_factors['doc_factor'], 0.25),  # Adjusted for rigidity
                    "woc": min(tool_diameter * 0.25 * rigidity_factors['woc_factor'], 1.0),  # Adjusted for rigidity
                    "surface_speed_multiplier": 1.0 if machine_rigidity != MachineRigidity.ROUTER else 0.6,  # Much more conservative for router+steel
                    "chip_load_multiplier": 0.8 * rigidity_factors['chipload_factor'],  # Adjusted for rigidity
                    "flutes": 4  # 4-flute for finishing
                }
            }
            
            if preset_name in presets:
                preset = presets[preset_name]
                
                # First set material
                material_key = preset["material"]
                self.materialCombo.blockSignals(True)
                for i in range(self.materialCombo.count()):
                    if material_key in self.materialCombo.itemText(i).lower():
                        self.materialCombo.setCurrentIndex(i)
                        break
                self.materialCombo.blockSignals(False)
                
                # Trigger material selection manually with preset adjustments
                if material_key == "aluminum_6061":
                    from src.formulas import MATERIALS
                    material = MATERIALS[material_key]
                    
                    # Apply preset multipliers
                    adjusted_sfm = material.sfm * preset["surface_speed_multiplier"]
                    adjusted_smm = adjusted_sfm * 0.3048
                    adjusted_chip_load = material.chip_load * preset["chip_load_multiplier"]
                    
                    self.on_material_selected(material_key, material.kc, adjusted_sfm, adjusted_smm, adjusted_chip_load, material.name)
                elif material_key == "steel_1018":
                    from src.formulas import MATERIALS
                    material = MATERIALS[material_key]
                    
                    # Apply preset multipliers
                    adjusted_sfm = material.sfm * preset["surface_speed_multiplier"]
                    adjusted_smm = adjusted_sfm * 0.3048
                    adjusted_chip_load = material.chip_load * preset["chip_load_multiplier"]
                    
                    self.on_material_selected(material_key, material.kc, adjusted_sfm, adjusted_smm, adjusted_chip_load, material.name)
                
                # Apply preset parameters
                if hasattr(main_window, 'cutting_box'):
                    cutting_box = main_window.cutting_box
                    
                    # Set depth and width of cut
                    cutting_box.DOC.setValue(preset["doc"])
                    cutting_box.WOC.setValue(preset["woc"])
                    
                    # Adjust flute count if tool box has it
                    if hasattr(main_window, 'tool_box'):
                        main_window.tool_box.fluteNum.setValue(preset["flutes"])
                
                # Show confirmation with rigidity info
                rigidity_name = rigidity_factors['name']
                reduction_info = ""
                if machine_rigidity != MachineRigidity.VMC_INDUSTRIAL:
                    chip_reduction = int((1 - rigidity_factors['chipload_factor']) * 100)
                    doc_reduction = int((1 - rigidity_factors['doc_factor']) * 100)
                    reduction_info = f"\n⚠️  Adjusted for {rigidity_name}:\n   Chipload: -{chip_reduction}%, DOC: -{doc_reduction}%"
                
                QtWidgets.QMessageBox.information(
                    self,
                    "Preset Applied",
                    f"Applied {preset['operation']} preset for {preset['material'].replace('_', ' ').title()}:\n\n"
                    f"Depth of Cut: {preset['doc']:.2f}mm\n"
                    f"Width of Cut: {preset['woc']:.2f}mm\n"
                    f"Flutes: {preset['flutes']}\n\n"
                    f"Material parameters have been auto-populated."
                    f"{reduction_info}"
                )
                
                # Reset combo to prevent reapplication
                self.presetsCombo.setCurrentIndex(0)
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Preset Error", 
                f"Error applying preset: {str(e)}\nMake sure tool diameter is set."
            )


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


class MachineBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(MachineBox, self).__init__(parent)
        self.setTitle("🏭 Machine Specs")
        self.setObjectName("machine_box")
        form = QtWidgets.QFormLayout()
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(10)
        self.setLayout(form)

        # Widgets with enhanced styling
        self.minRPM = QtWidgets.QSpinBox()
        self.minRPM.setRange(0, 100000)
        self.minRPM.setSuffix(" RPM")
        self.minRPM.setValue(6000)
        self.minRPM.setToolTip("Minimum spindle speed of your machine")
        
        self.preferredRPM = QtWidgets.QSpinBox()
        self.preferredRPM.setRange(0, 100000)
        self.preferredRPM.setSuffix(" RPM")
        self.preferredRPM.setValue(22000)
        self.preferredRPM.setToolTip("Your preferred spindle speed for optimal performance")
        
        self.maxRPM = QtWidgets.QSpinBox()
        self.maxRPM.setRange(0, 100000)
        self.maxRPM.setSuffix(" RPM")
        self.maxRPM.setValue(24000)
        self.maxRPM.setToolTip("Maximum spindle speed of your machine")
        
        # Add spindle power capacity
        self.spindlePower = QtWidgets.QDoubleSpinBox()
        self.spindlePower.setRange(0.1, 50.0)
        self.spindlePower.setValue(2.2)  # Default to user's 2.2kW spindle
        self.spindlePower.setSuffix(" kW")
        self.spindlePower.setDecimals(1)
        self.spindlePower.setToolTip("Maximum power capacity of your spindle motor")
        
        # Add machine rigidity dropdown
        self.rigidityCombo = QtWidgets.QComboBox()
        self.rigidityCombo.addItem("Select Machine Type...")
        
        # Populate with rigidity options
        for rigidity_key, rigidity_data in MACHINE_RIGIDITY_FACTORS.items():
            self.rigidityCombo.addItem(rigidity_data['name'], rigidity_key)
        
        # Set default to DIY/Medium (PrintNC)
        self.rigidityCombo.setCurrentText(MACHINE_RIGIDITY_FACTORS[MachineRigidity.DIY_MEDIUM]['name'])
        self.rigidityCombo.setToolTip("Machine rigidity affects cutting parameters and recommendations")
        
        # Connect signal for rigidity changes
        self.rigidityCombo.currentTextChanged.connect(self.on_rigidity_changed)
        
        # Machine info display
        self.machineInfo = QtWidgets.QLabel()
        self.machineInfo.setWordWrap(True)
        self.machineInfo.setStyleSheet("color: #888; font-size: 10px; padding: 5px; border: 1px solid #444; background-color: #2a2a2a;")
        self.machineInfo.setMinimumHeight(60)
        
        # Initialize machine info display
        self.on_rigidity_changed()

        form.addRow("Min (RPM)", self.minRPM)
        form.addRow("⭐ Preferred (RPM)", self.preferredRPM)
        form.addRow("Max (RPM)", self.maxRPM)
        form.addRow("🔌 Spindle Power", self.spindlePower)
        form.addRow("🏗️ Machine Rigidity", self.rigidityCombo)
        form.addRow("", self.machineInfo)
    
    def on_rigidity_changed(self):
        """Handle machine rigidity selection change."""
        current_text = self.rigidityCombo.currentText()
        if current_text == "Select Machine Type...":
            self.machineInfo.setText("Select your machine type for optimized cutting parameters")
            return
        
        # Find the rigidity key for the selected text
        selected_rigidity = None
        for rigidity_key, rigidity_data in MACHINE_RIGIDITY_FACTORS.items():
            if rigidity_data['name'] == current_text:
                selected_rigidity = rigidity_key
                break
        
        if selected_rigidity:
            rigidity_data = MACHINE_RIGIDITY_FACTORS[selected_rigidity]
            
            # Update machine info display
            info_text = f"{rigidity_data['description']}\n"
            info_text += f"Chipload Reduction: {int((1-rigidity_data['chipload_factor'])*100)}%\n"
            info_text += f"DOC/WOC Reduction: {int((1-rigidity_data['doc_factor'])*100)}%/{int((1-rigidity_data['woc_factor'])*100)}%\n"
            info_text += f"Min RPM: {rigidity_data['min_rpm']} | Steel Limit: {rigidity_data['steel_sfm_limit']} SFM"
            
            self.machineInfo.setText(info_text)
            
            # Auto-adjust RPM recommendations based on machine type
            if selected_rigidity == MachineRigidity.ROUTER:
                # Router recommendations
                self.minRPM.setValue(8000)
                self.preferredRPM.setValue(18000)
                self.maxRPM.setValue(24000)
            elif selected_rigidity == MachineRigidity.DIY_MEDIUM:
                # DIY/PrintNC recommendations  
                self.minRPM.setValue(1000)
                self.preferredRPM.setValue(12000)
                self.maxRPM.setValue(24000)
            elif selected_rigidity == MachineRigidity.VMC_INDUSTRIAL:
                # Industrial VMC recommendations
                self.minRPM.setValue(100)
                self.preferredRPM.setValue(3000)
                self.maxRPM.setValue(12000)
    
    def get_selected_rigidity(self):
        """Get the currently selected machine rigidity level."""
        current_text = self.rigidityCombo.currentText()
        
        # Find the rigidity key for the selected text
        for rigidity_key, rigidity_data in MACHINE_RIGIDITY_FACTORS.items():
            if rigidity_data['name'] == current_text:
                return rigidity_key
        
        # Default to DIY/Medium if nothing selected
        return MachineRigidity.DIY_MEDIUM


class ResultsBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ResultsBox, self).__init__(parent)
        self.setTitle("📊 Results Dashboard")
        self.setObjectName("results_box")
        
        # Import dashboard widgets
        from .components.dashboard_widgets import RangeBarWidget, RPMGaugeWidget, StatusIndicatorWidget
        
        # Main layout - directly use the dashboard
        mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainLayout)
        
        # Create dashboard view directly
        self._create_dashboard_view(mainLayout)
    
    def _create_dashboard_view(self, main_layout):
        """Create the graphical dashboard view."""
        from .components.dashboard_widgets import RangeBarWidget, GradientType
        
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
        from src.formulas import calculate_torque
        
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


class GUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        self.settings = None

        self.setWindowTitle(
            "⚙️ Speeds & Feeds Calculator v2.0 - Enhanced with HSM"
        )
        self.setMinimumSize(1000, 1100)  # Set to match successful large size test
        self.resize(1200, 1100)
        settings = QtCore.QSettings("speeds-and-feeds-calc", "SpeedsAndFeedsCalculator")

        try:
            self.restoreGeometry(settings.value("geometry"))

        except Exception as e:
            logging.warning(
                "Unable to load settings. First time opening the tool?\n" + str(e)
            )

        # Layouts with improved spacing
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        sections_layout = QtWidgets.QHBoxLayout()
        sections_layout.setSpacing(15)

        self.setCentralWidget(main_widget)
        main_widget.setLayout(main_layout)
        form = QtWidgets.QFormLayout()

        self.tool_box = ToolBox(self)
        self.material_box = MaterialBox(self)
        self.cutting_box = CuttingBox(self)
        self.machine_box = MachineBox(self)

        self.results_box = ResultsBox()

        # Add Widgets
        main_layout.addLayout(form)
        main_layout.addLayout(sections_layout)
        sections_layout.addWidget(self.tool_box)
        sections_layout.addWidget(self.material_box)
        sections_layout.addWidget(self.cutting_box)
        sections_layout.addWidget(self.machine_box)
        main_layout.addWidget(self.results_box)

        # Logic - Use valueChanged for real-time updates
        self.tool_box.fluteNum.valueChanged.connect(self.update)
        self.cutting_box.DOC.valueChanged.connect(self.update)
        self.cutting_box.WOC.valueChanged.connect(self.update)
        self.cutting_box.surface_speed.valueChanged.connect(self.update)
        self.cutting_box.feed_per_tooth.valueChanged.connect(self.update)
        self.cutting_box.Kc.valueChanged.connect(self.update)
        self.tool_box.toolDiameter.valueChanged.connect(self.toolDiameterChanged)
        
        # Connect unit switching - connect to both handlers
        self.tool_box.unit_group.buttonClicked.connect(self.tool_box.on_unit_changed)
        self.tool_box.unit_group.buttonClicked.connect(self.on_unit_changed)
        
        # Material box signals
        self.material_box.materialChanged.connect(self.on_material_changed)
        self.material_box.coatingChanged.connect(self.update)  # Update calculations when coating changes
        
        # Machine box signals
        self.machine_box.rigidityCombo.currentTextChanged.connect(self.update)  # Update when rigidity changes

        self.cutting_box.init()
        self.update()

    def toolDiameterChanged(self):
        self.cutting_box.init()
        self.update()
    
    def on_material_changed(self, material_key: str, kc: float, sfm: float, smm: float, chip_load: float, name: str):
        """Handle material selection and auto-populate cutting parameters."""
        # Auto-populate material-specific parameters
        self.cutting_box.Kc.setValue(kc)
        
        # Set surface speed (convert based on current units)
        self.cutting_box.surface_speed.blockSignals(True)
        if self.tool_box.is_metric():
            self.cutting_box.surface_speed.setValue(smm)
        else:
            self.cutting_box.surface_speed.setValue(sfm)
        self.cutting_box.surface_speed.blockSignals(False)
        
        # Set feed per tooth (convert based on current units)
        self.cutting_box.feed_per_tooth.blockSignals(True)
        if self.tool_box.is_metric():
            self.cutting_box.feed_per_tooth.setValue(chip_load)
        else:
            self.cutting_box.feed_per_tooth.setValue(chip_load * MM_TO_IN)
        self.cutting_box.feed_per_tooth.blockSignals(False)
        
        # Set material context for UI adaptation
        self.cutting_box.set_material_context(material_key)
        
        # Update the calculations
        self.update()
    
    def on_unit_changed(self):
        """Handle unit system change"""
        # Update tool box units (this will be called automatically by the signal)
        # But we need to make sure the ToolBox handles its own conversion
        
        # Update cutting box units
        self.cutting_box.update_units()
        
        # Update calculations
        self.update()

    def closeEvent(self, event):
        self.settings = QtCore.QSettings(
            "speeds-and-feeds-calc", "SpeedsAndFeedsCalculator"
        )
        self.settings.setValue("geometry", self.saveGeometry())
        QtWidgets.QWidget.closeEvent(self, event)

    def get_rpm_status(self, rpm):
        """Determine RPM status based on machine limits and preferred RPM"""
        min_rpm = self.machine_box.minRPM.value()
        preferred_rpm = self.machine_box.preferredRPM.value()
        max_rpm = self.machine_box.maxRPM.value()
        
        # Check if outside machine limits (danger)
        if rpm < min_rpm:
            return "danger", f"below minimum ({min_rpm:,} RPM)"
        elif rpm > max_rpm:
            return "danger", f"above maximum ({max_rpm:,} RPM)"
        
        # Check if close to preferred RPM (good)
        preferred_tolerance = preferred_rpm * 0.1  # 10% tolerance around preferred
        if abs(rpm - preferred_rpm) <= preferred_tolerance:
            return "good", f"near preferred ({preferred_rpm:,} RPM)"
        
        # Check if approaching limits (warning)
        elif rpm > max_rpm * 0.9:  # Within 90% of max
            return "warning", "approaching maximum"
        elif rpm < min_rpm * 1.1:  # Within 110% of min
            return "warning", "near minimum"
        else:
            return "info", "within safe range"
    

    def update(self):
        fs = FeedsAndSpeeds()

        # Tool
        fs.diameter = self.tool_box.get_diameter_mm()
        fs.flute_num = self.tool_box.fluteNum.value()
        # fs.flute_len = self.tool_box.fluteLen.value()
        # fs.lead_angle = self.tool_box.leadAngle.value()

        # Cutting
        fs.doc = self.cutting_box.get_doc_mm()
        fs.woc = self.cutting_box.get_woc_mm()
        fs.smm = self.cutting_box.get_surface_speed_sfm() * FT_TO_M  # Convert SFM to SMM
        fs.mmpt = self.cutting_box.get_feed_per_tooth_mm()
        fs.kc = self.cutting_box.Kc.value()
        
        # HSM and chip thinning parameters
        fs.hsm_enabled = self.cutting_box.is_hsm_enabled()
        fs.chip_thinning_enabled = self.cutting_box.is_chip_thinning_enabled()
        fs.tool_stickout = self.cutting_box.get_tool_stickout_mm()
        
        # Machine rigidity
        fs.rigidity_level = self.machine_box.get_selected_rigidity()
        
        # Material type for rigidity-aware adjustments
        if hasattr(self.material_box, 'current_material') and self.material_box.current_material:
            material_key, _, _, _, _, _ = self.material_box.current_material
            fs.material_type = material_key

        # fs.print_values()

        # Do the formulas (now includes rigidity adjustments and warnings)
        calculation_warnings = fs.calculate()
        
        # Get additional validation warnings
        validation_warnings = validate_machining_parameters(fs.rpm, fs.feed, fs.doc, fs.woc, fs.diameter)
        all_warnings = calculation_warnings + validation_warnings
        
        # Get RPM status for color coding  
        rpm_status, rpm_message = self.get_rpm_status(fs.rpm)
        
        # Update dashboard widgets
        machine_limits = (
            self.machine_box.minRPM.value(),
            self.machine_box.preferredRPM.value(), 
            self.machine_box.maxRPM.value()
        )
        spindle_capacity = self.machine_box.spindlePower.value()
        
        # Get current material info if available
        material_info = None
        if hasattr(self.material_box, 'current_material') and self.material_box.current_material:
            material_info = self.material_box.current_material
        
        # Pass rigidity info to results display
        rigidity_level = fs.rigidity_level
        rigidity_name = MACHINE_RIGIDITY_FACTORS[rigidity_level]['name']
        rigidity_info = (rigidity_level, rigidity_name)
        
        self.results_box.update_dashboard_values(fs, rpm_status, rpm_message, machine_limits, spindle_capacity, material_info, all_warnings, rigidity_info)
        
        # Update material box with warnings if any
        if all_warnings:
            warning_text = "⚠️ Warnings:\n" + "\n".join(all_warnings[:3])  # Show first 3 warnings
            self.material_box.materialInfo.setStyleSheet("color: #ff8c00; font-size: 11px; padding: 5px;")
            if hasattr(self.material_box, 'current_material') and self.material_box.current_material:
                # Preserve material info and add warnings
                material_key, kc, sfm, smm, chip_load, name = self.material_box.current_material
                current_info = self.material_box.materialInfo.text()
                if not current_info.startswith("⚠️"):
                    self.material_box.materialInfo.setText(current_info + "\n\n" + warning_text)
        else:
            # Reset to normal color if no warnings
            self.material_box.materialInfo.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")


def load_stylesheet():
    """Load the dark theme stylesheet"""
    stylesheet_path = os.path.join(os.path.dirname(__file__), 'dark_theme.qss')
    try:
        with open(stylesheet_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"Stylesheet file not found: {stylesheet_path}")
        return ""

def start():
    app = QtWidgets.QApplication(sys.argv)
    
    # Apply dark theme stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    gui = GUI()
    gui.show()
    app.exec()
    sys.exit()
