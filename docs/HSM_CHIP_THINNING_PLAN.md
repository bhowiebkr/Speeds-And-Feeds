# HSM and Chip Thinning Enhancement Plan

## Overview
This plan outlines the implementation of High Speed Machining (HSM) features, chip thinning compensation, and comprehensive deflection calculations for all tool sizes in the Speeds & Feeds Calculator.

## Features to Implement

### 1. **Add HSM and Chip Thinning Controls to CuttingBox** (`src/main.py`)

Add new UI controls to the cutting parameters section:

- **"Enable HSM (High Speed Machining)"** checkbox
  - When checked, enables chip thinning calculations
  - Allows higher surface speeds (20-30% boost)
  - Optimizes for shallow cuts and high feed rates

- **"Apply Chip Thinning Compensation"** checkbox
  - Auto-checks when HSM is enabled
  - Can be manually controlled for non-HSM applications
  - Compensates feed rates based on radial engagement

- **"Tool Stickout"** spinbox
  - Default: 15mm (conservative)
  - Range: 5mm to 100mm
  - Used for deflection calculations on all tool sizes

**Placement**: After the Kc (Specific Cutting Force) input in the CuttingBox layout.

---

### 2. **Implement Chip Thinning Calculations** (`src/formulas.py`)

#### New Function: Chip Thinning Factor Calculation

```python
def calculate_chip_thinning_factor(woc_mm, tool_diameter_mm):
    """
    Calculate radial chip thinning factor (RCTF).
    
    Formula: RCTF = 1/√(1 - [1 - (2 × Ae/D)]²)
    
    Args:
        woc_mm: Width of cut (radial engagement) in mm
        tool_diameter_mm: Tool diameter in mm
        
    Returns:
        Chip thinning factor (1.0 = no thinning, >1.0 = compensation needed)
    """
    ae_ratio = woc_mm / tool_diameter_mm
    
    if ae_ratio >= 0.5:
        return 1.0  # No chip thinning at ≥50% engagement
    
    # RCTF = 1/√(1 - [1 - (2 × Ae/D)]²)
    return 1.0 / math.sqrt(1 - (1 - 2 * ae_ratio) ** 2)
```

#### Expected Chip Thinning Values
- **50% WOC**: 1.00x (no compensation needed)
- **35% WOC**: 1.05x (5% feed increase)
- **20% WOC**: 1.25x (25% feed increase)
- **10% WOC**: 1.70x (70% feed increase)
- **5% WOC**: 2.30x (130% feed increase)

#### Modifications to FeedsAndSpeeds Class

- Add parameters:
  - `hsm_enabled: bool = False`
  - `chip_thinning_enabled: bool = False`
  - `tool_stickout: float = 15.0`

- Apply chip thinning factor to feed rate calculations
- Store chip thinning factor in results for display

---

### 3. **Add Deflection Calculations for Standard Tools** (`src/formulas.py`)

#### Extend StandardMachiningCalculator

Currently, deflection calculations are only performed for micro tools (<3mm). This enhancement extends deflection calculations to **all tool sizes**.

```python
def calculate_tool_deflection(self, force_n, diameter_mm, stickout_mm):
    """
    Calculate tool deflection using cantilever beam theory.
    
    Formula: δ = F*L³/(3*E*I)
    
    Args:
        force_n: Cutting force in Newtons
        diameter_mm: Tool diameter in mm
        stickout_mm: Tool stickout length in mm
        
    Returns:
        Tool tip deflection in mm
    """
    # Material properties for carbide
    E = 600e9  # Young's modulus (Pa)
    
    # Moment of inertia for circular cross-section: I = π*r⁴/4
    radius_m = (diameter_mm / 2) / 1000  # Convert to meters
    moment_inertia = (math.pi * (radius_m ** 4)) / 4
    
    # Cantilever beam deflection formula
    stickout_m = stickout_mm / 1000
    deflection_m = (force_n * (stickout_m ** 3)) / (3 * E * moment_inertia)
    
    return deflection_m * 1000  # Convert back to mm
```

#### Cutting Force Calculation

```python
def calculate_cutting_force(self, kc, doc_mm, woc_mm, feed_per_tooth):
    """
    Calculate cutting force for standard tools.
    
    Args:
        kc: Specific cutting force (N/mm²)
        doc_mm: Depth of cut (mm)
        woc_mm: Width of cut (mm)
        feed_per_tooth: Feed per tooth (mm)
        
    Returns:
        Cutting force in Newtons
    """
    # Chip area = DOC × feed per tooth
    chip_area = doc_mm * feed_per_tooth
    
    # Force = Kc × chip_area (simplified for standard tools)
    return kc * chip_area
```

---

### 4. **Update Results Display** (`src/main.py`)

#### Enhanced Advanced Info Display

Modify `_update_advanced_info()` to show comprehensive information:

```python
def _update_advanced_info(self, fs, torque, material_info=None, warnings=None, rigidity_info=None, is_metric=True):
    """Enhanced advanced information display with deflection and HSM data."""
    
    # Existing basic calculations...
    
    # 📐 Deflection Analysis (for ALL tools now)
    if hasattr(fs, 'tool_deflection') and fs.tool_deflection > 0:
        deflection_percent = (fs.tool_deflection / fs.diameter) * 100
        info_lines.append(f"")
        info_lines.append(f"📐 Deflection Analysis:")
        info_lines.append(f"   Tool Deflection: {fs.tool_deflection:.4f}mm ({deflection_percent:.2f}% of diameter)")
        info_lines.append(f"   Cutting Force: {fs.cutting_force:.1f}N")
        info_lines.append(f"   Tool Stickout: {fs.tool_stickout:.1f}mm")
        
        # Deflection warnings
        if deflection_percent > 5:
            info_lines.append(f"   ⚠️ HIGH DEFLECTION - Reduce feeds/DOC")
        elif deflection_percent > 1:
            info_lines.append(f"   ⚠️ Monitor surface finish")
    
    # 🚀 HSM Parameters (when enabled)
    if hasattr(fs, 'hsm_enabled') and fs.hsm_enabled:
        info_lines.append(f"")
        info_lines.append(f"🚀 HSM Parameters:")
        if hasattr(fs, 'chip_thinning_factor'):
            base_feed = fs.feed / fs.chip_thinning_factor
            engagement_percent = (fs.woc / fs.diameter) * 100
            info_lines.append(f"   Chip Thinning Factor: {fs.chip_thinning_factor:.2f}x")
            info_lines.append(f"   Compensated Feed: {fs.feed:.0f} mm/min (base: {base_feed:.0f} mm/min)")
            info_lines.append(f"   Radial Engagement: {engagement_percent:.1f}% ({fs.woc:.2f}mm of {fs.diameter:.1f}mm tool)")
```

---

### 5. **HSM Speed Optimization** (`src/formulas.py`)

When HSM mode is enabled, allow higher surface speeds due to reduced heat buildup:

```python
def apply_hsm_speed_boost(surface_speed, material_type, hsm_enabled):
    """
    Apply HSM speed boost for reduced heat engagement.
    
    Args:
        surface_speed: Base surface speed
        material_type: Material being cut
        hsm_enabled: Whether HSM mode is active
        
    Returns:
        Adjusted surface speed
    """
    if not hsm_enabled:
        return surface_speed
    
    # HSM speed multipliers by material
    hsm_multipliers = {
        'aluminum': 1.25,    # 25% increase
        'steel': 1.15,       # 15% increase
        'stainless': 1.10,   # 10% increase
        'titanium': 1.05,    # 5% increase (conservative)
        'cast_iron': 1.20    # 20% increase
    }
    
    for material, multiplier in hsm_multipliers.items():
        if material in material_type.lower():
            return surface_speed * multiplier
    
    return surface_speed * 1.15  # Default 15% increase
```

---

### 6. **UI Layout Updates**

#### CuttingBox Additions

Add the new controls to the CuttingBox layout:

```python
# After Kc spinbox...

# HSM and Chip Thinning controls
self.hsm_enabled = QtWidgets.QCheckBox("Enable HSM (High Speed Machining)")
self.chip_thinning_enabled = QtWidgets.QCheckBox("Apply Chip Thinning Compensation")
self.chip_thinning_enabled.setEnabled(False)  # Auto-controlled by HSM

# Tool stickout for deflection calculations
self.tool_stickout = QtWidgets.QDoubleSpinBox()
self.tool_stickout.setRange(5.0, 100.0)
self.tool_stickout.setValue(15.0)  # Conservative default
self.tool_stickout.setSuffix(" mm")
self.tool_stickout.setToolTip("Tool stickout length for deflection calculations")

# Add to layout
form.addRow(spacer3)  # New spacer
form.addRow(self.hsm_enabled)
form.addRow(self.chip_thinning_enabled)
form.addRow("Tool Stickout", self.tool_stickout)

# Signal connections
self.hsm_enabled.stateChanged.connect(self.on_hsm_changed)
self.chip_thinning_enabled.stateChanged.connect(parent().update)
self.tool_stickout.valueChanged.connect(parent().update)
```

---

### 7. **Testing and Validation**

#### Test Cases for Chip Thinning

| WOC % | Expected Factor | Expected Benefit |
|-------|----------------|------------------|
| 50%   | 1.00x          | No compensation  |
| 35%   | 1.05x          | 5% productivity  |
| 20%   | 1.25x          | 25% productivity |
| 10%   | 1.70x          | 70% productivity |
| 5%    | 2.30x          | 130% productivity|

#### Deflection Validation

Test deflection calculations with known values:
- 6mm carbide end mill, 20mm stickout, 100N force
- Expected deflection: ~0.047mm (0.78% of diameter)

#### UI Testing

- [ ] HSM checkbox enables chip thinning automatically
- [ ] Chip thinning compensation updates feed rates in real-time
- [ ] Tool stickout changes update deflection calculations
- [ ] Results display shows all new parameters correctly
- [ ] Unit switching works with new parameters

---

### 8. **Implementation Benefits**

#### Productivity Gains
- **Up to 2.3x feed rate** increase at 5% radial engagement
- **20-30% higher surface speeds** in HSM mode
- **Optimized toolpaths** for modern CAM strategies

#### Tool Life Improvements
- **Better chip evacuation** with proper chip thickness
- **Reduced heat buildup** from shorter engagement time
- **Prevent rubbing** through automatic feed compensation

#### User Awareness
- **Deflection visibility** for all tool sizes
- **Real-time feedback** on cutting conditions
- **Informed decision making** with comprehensive data

---

### 9. **Future Enhancements**

- **Axial chip thinning** for variable DOC operations
- **Approach angle compensation** for chamfer mills and ball nose tools
- **Trochoidal milling parameters** for optimal chip evacuation
- **CAM integration** suggestions based on calculated parameters

---

*This plan implements industry-standard HSM and chip thinning formulas used by professional machining software, ensuring accurate and reliable calculations for modern CNC operations.*