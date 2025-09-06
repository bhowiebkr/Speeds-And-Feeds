"""
Material selection UI box for the Speeds and Feeds Calculator.

Contains the MaterialBox widget for material and coating selection.
"""

from PySide6 import QtWidgets, QtCore
from ...components.widgets import MaterialCombo, CoatingCombo
from ...constants.units import MM_TO_IN
from ...constants.materials import MATERIALS
from ...constants.machining import MACHINE_RIGIDITY_FACTORS, MachineRigidity
from ...formulas.chipload import chip_load_rule_of_thumb, adjust_speed_for_coating


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
                    material = MATERIALS[material_key]
                    
                    # Apply preset multipliers
                    adjusted_sfm = material.sfm * preset["surface_speed_multiplier"]
                    adjusted_smm = adjusted_sfm * 0.3048
                    adjusted_chip_load = material.chip_load * preset["chip_load_multiplier"]
                    
                    self.on_material_selected(material_key, material.kc, adjusted_sfm, adjusted_smm, adjusted_chip_load, material.name)
                elif material_key == "steel_1018":
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