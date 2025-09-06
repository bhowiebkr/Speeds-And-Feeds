"""
CNC Machining Formulas and Constants

Combined module providing constants, formulas, and helper functions for CNC machining
calculations including feeds, speeds, material removal rates, and power requirements.

Based on industry-standard formulas and material properties from leading manufacturers
including Sandvik Coromant, Harvey Tool, and Kennametal.

Formulas reference: https://www.garrtool.com/resources/machining-formulas/
"""

import math
import json
import os
from typing import Dict, List, Tuple, Optional, Union

# Physical Constants
PI = math.pi

# Unit Conversion Constants
INCH_TO_MM = 25.4
MM_TO_INCH = 1 / INCH_TO_MM
THOU_TO_MM = 0.0254
MM_TO_THOU = 1 / THOU_TO_MM
SFM_TO_SMM = 0.3048
SMM_TO_SFM = 1 / SFM_TO_SMM
HP_TO_KW = 0.745699872
KW_TO_HP = 1 / HP_TO_KW

# Machining Constants
POWER_CALCULATION_FACTOR = 60000  # Factor for converting N*mm/min to kW
DEFAULT_MACHINE_EFFICIENCY = 0.8  # 80% typical machine efficiency
SAFETY_FACTOR_DEFAULT = 1.2  # 20% safety factor for calculations

# Tool Geometry Constants
CARBIDE_RAKE_ANGLE_EFFECT = 0.01  # 1% power change per degree of rake angle
COATED_TOOL_SPEED_INCREASE = 1.3  # 30% speed increase for coated tools
HSS_TO_CARBIDE_SPEED_RATIO = 0.5  # HSS runs at ~50% of carbide speeds


class MaterialProperty:
    """Container for material machining properties."""
    
    def __init__(self, name: str, kc: float, sfm: float, chip_load: float, 
                 hardness: Union[int, Tuple[int, int]] = None):
        self.name = name
        self.kc = kc  # Specific cutting force (N/mm²)
        self.sfm = sfm  # Surface speed (SFM)
        self.smm = sfm * SFM_TO_SMM  # Surface speed (m/min)
        self.chip_load = chip_load  # Feed per tooth (mm/tooth)
        self.hardness = hardness


# Standard Material Properties (typical values)
MATERIALS = {
    'aluminum_6061': MaterialProperty('6061 Aluminum', 800, 1200, 0.08, (95, 150)),
    'steel_1018': MaterialProperty('1018 Mild Steel', 2000, 100, 0.08, (120, 170)),
    'stainless_304': MaterialProperty('304 Stainless', 2600, 75, 0.05, (150, 200)),
    'cast_iron_grey': MaterialProperty('Grey Cast Iron', 1350, 120, 0.08, (150, 250)),
    'titanium_ti64': MaterialProperty('Ti-6Al-4V', 2550, 75, 0.04, (300, 400)),
    'brass_360': MaterialProperty('360 Brass', 700, 600, 0.12, (60, 120)),
    'copper_101': MaterialProperty('101 Copper', 600, 400, 0.10, (40, 80)),
}

# Machine Efficiency by Drive Type
MACHINE_EFFICIENCIES = {
    'direct_drive': 0.85,
    'belt_drive': 0.78,
    'gear_drive': 0.75,
}

# Tool Coating Speed Multipliers
COATING_MULTIPLIERS = {
    'uncoated': 1.0,
    'tin': 1.2,
    'ticn': 1.3,
    'tialn': 1.4,
    'alcrn': 1.5,
    'diamond': 2.0,
}

# Machine Rigidity Types and Adjustment Factors
class MachineRigidity:
    """Machine rigidity levels with associated adjustment factors."""
    ROUTER = 'router'
    DIY_MEDIUM = 'diy_medium'
    VMC_INDUSTRIAL = 'vmc_industrial'

# Machine Rigidity Properties
MACHINE_RIGIDITY_FACTORS = {
    MachineRigidity.ROUTER: {
        'name': 'Router/Light Duty',
        'description': 'Router-based CNC, gantry machines, light construction',
        'chipload_factor': 0.4,  # 40% of standard chipload
        'doc_factor': 0.5,       # 50% of standard depth of cut
        'woc_factor': 0.6,       # 60% of standard width of cut
        'min_rpm': 8000,         # Routers prefer higher RPM
        'steel_sfm_limit': 60,   # Limited steel cutting capability (SFM)
        'chatter_sensitivity': 0.8,  # High sensitivity to vibration
        'power_efficiency': 0.75     # Lower power transmission efficiency
    },
    MachineRigidity.DIY_MEDIUM: {
        'name': 'DIY/Medium Duty (PrintNC)',
        'description': 'PrintNC, hobby VMC, reinforced gantry machines',
        'chipload_factor': 0.5,  # 50% of standard chipload (very conservative for hobby machines)
        'doc_factor': 0.8,       # 80% of standard depth of cut
        'woc_factor': 0.85,      # 85% of standard width of cut
        'min_rpm': 1000,         # Can handle lower RPM
        'steel_sfm_limit': 85,   # Good steel cutting capability (SFM)
        'chatter_sensitivity': 0.5,  # Medium sensitivity to vibration
        'power_efficiency': 0.85     # Good power transmission efficiency
    },
    MachineRigidity.VMC_INDUSTRIAL: {
        'name': 'VMC/Industrial',
        'description': 'Commercial VMC, Tormach, Haas, industrial machines',
        'chipload_factor': 1.0,  # 100% of standard chipload
        'doc_factor': 1.0,       # 100% of standard depth of cut
        'woc_factor': 1.0,       # 100% of standard width of cut
        'min_rpm': 100,          # Can handle very low RPM
        'steel_sfm_limit': 150,  # Excellent steel cutting capability (SFM)
        'chatter_sensitivity': 0.2,  # Low sensitivity to vibration
        'power_efficiency': 0.9      # High power transmission efficiency
    }
}


def inches_to_mm(inches):
    """Convert inches to millimeters."""
    return inches * INCH_TO_MM


def mm_to_inches(mm):
    """Convert millimeters to inches."""
    return mm * MM_TO_INCH


def thou_to_mm(thou):
    """Convert thousandths of an inch to millimeters."""
    return thou * THOU_TO_MM


def mm_to_thou(mm):
    """Convert millimeters to thousandths of an inch."""
    return mm * MM_TO_THOU


def sfm_to_smm(sfm):
    """Convert Surface Feet per Minute to Surface Meters per Minute."""
    return sfm * SFM_TO_SMM


def smm_to_sfm(smm):
    """Convert Surface Meters per Minute to Surface Feet per Minute."""
    return smm * SMM_TO_SFM


def load_materials_database(json_path: str = None) -> Dict:
    """
    Load materials database from JSON file.
    
    Args:
        json_path: Path to materials.json file. If None, uses default location.
        
    Returns:
        Dictionary containing materials database
    """
    if json_path is None:
        # Default path relative to this module
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, '..', 'data', 'materials.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Materials database not found at {json_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error parsing materials database at {json_path}")
        return {}


def calculate_rpm(surface_speed: float, diameter: float, units: str = 'metric') -> float:
    """
    Calculate spindle RPM from surface speed and tool diameter.
    
    Args:
        surface_speed: Surface speed (SFM or SMM)
        diameter: Tool diameter (inches or mm)
        units: 'metric' for SMM/mm, 'imperial' for SFM/inches
        
    Returns:
        RPM (revolutions per minute)
    """
    if units == 'metric':
        # SMM to RPM: RPM = (SMM * 1000) / (π * D)
        return (surface_speed * 1000) / (PI * diameter)
    else:
        # SFM to RPM: RPM = (SFM * 12) / (π * D)
        return (surface_speed * 12) / (PI * diameter)


def calculate_feed_rate(rpm: float, flutes: int, chip_load: float) -> float:
    """
    Calculate feed rate from RPM, flute count, and chip load.
    
    Args:
        rpm: Spindle speed (RPM)
        flutes: Number of flutes/teeth
        chip_load: Feed per tooth (mm/tooth or in/tooth)
        
    Returns:
        Feed rate (mm/min or in/min)
    """
    return rpm * flutes * chip_load


def calculate_surface_speed(rpm: float, diameter: float, units: str = 'metric') -> float:
    """
    Calculate surface speed from RPM and tool diameter.
    
    Args:
        rpm: Spindle speed (RPM)
        diameter: Tool diameter (inches or mm)
        units: 'metric' for SMM, 'imperial' for SFM
        
    Returns:
        Surface speed (SMM or SFM)
    """
    if units == 'metric':
        # SMM = (RPM * π * D) / 1000
        return (rpm * PI * diameter) / 1000
    else:
        # SFM = (RPM * π * D) / 12
        return (rpm * PI * diameter) / 12


def calculate_mrr_milling(depth_of_cut: float, width_of_cut: float, 
                         feed_rate: float) -> float:
    """
    Calculate Material Removal Rate for milling operations.
    
    Args:
        depth_of_cut: Axial depth of cut (mm)
        width_of_cut: Radial width of cut (mm)
        feed_rate: Feed rate (mm/min)
        
    Returns:
        MRR in cm³/min
    """
    return (depth_of_cut * width_of_cut * feed_rate) / 1000


def calculate_cutting_power(mrr: float, kc: float, efficiency: float = 1.0) -> float:
    """
    Calculate required cutting power.
    
    Args:
        mrr: Material removal rate (cm³/min)
        kc: Specific cutting force (N/mm²)
        efficiency: Machine efficiency (0.0-1.0). Default 1.0 for theoretical power.
        
    Returns:
        Required cutting power (kW)
    """
    # Basic cutting power (theoretical)
    cutting_power = (mrr * kc) / POWER_CALCULATION_FACTOR
    
    # Account for machine efficiency if specified
    if efficiency < 1.0:
        cutting_power = cutting_power / efficiency
    
    return cutting_power


def calculate_torque(power_kw: float, rpm: float) -> float:
    """
    Calculate torque from power and RPM.
    
    Args:
        power_kw: Power in kilowatts
        rpm: Spindle speed (RPM)
        
    Returns:
        Torque in Newton-meters
    """
    if rpm == 0:
        return 0
    return (power_kw * 9549) / rpm


def chip_load_rule_of_thumb(diameter_mm: float, material_factor: float = 1.0) -> float:
    """
    Calculate chip load using rule of thumb: Diameter / 200.
    
    Args:
        diameter_mm: Tool diameter in mm
        material_factor: Multiplier for material (aluminum ~2.0, steel ~1.0, stainless ~0.5)
        
    Returns:
        Suggested chip load (mm/tooth)
    """
    return (diameter_mm / 200) * material_factor


def calculate_diameter_based_chipload(diameter_mm: float, material_type: str = 'aluminum') -> float:
    """
    Calculate chipload based on tool diameter with special handling for micro tools.
    
    This function addresses the non-linear relationship between tool diameter and 
    appropriate chipload, especially for micro tools where standard formulas break down.
    
    Args:
        diameter_mm: Tool diameter in mm
        material_type: Material being cut ('aluminum', 'steel', 'stainless')
        
    Returns:
        Recommended base chipload (mm/tooth) before any multipliers
    """
    if diameter_mm < 1.0:
        # Ultra-micro tools: fixed minimum to prevent breakage
        base_chipload = 0.005  # ~0.0002"
    elif diameter_mm < 3.0:
        # Micro tools: use percentage of diameter (1.5% conservative for aluminum)
        if material_type == 'aluminum':
            percentage = 0.015  # 1.5% of diameter
        elif material_type in ['steel', 'stainless']:
            percentage = 0.01   # 1% of diameter (more conservative)
        else:
            percentage = 0.012  # Default 1.2%
        
        base_chipload = diameter_mm * percentage
    elif diameter_mm < 6.0:
        # Small tools: linear interpolation between 3mm and 6mm
        # At 3mm: use micro formula result
        # At 6mm: use standard base (0.08mm for aluminum)
        micro_result = 3.0 * 0.015  # 0.045mm at 3mm
        standard_base = 0.08        # Standard base at 6mm
        
        # Linear interpolation
        t = (diameter_mm - 3.0) / (6.0 - 3.0)  # 0 to 1
        base_chipload = micro_result + t * (standard_base - micro_result)
    else:
        # Standard tools: use current base values
        if material_type == 'aluminum':
            base_chipload = 0.08
        elif material_type == 'steel':
            base_chipload = 0.08
        elif material_type == 'stainless':
            base_chipload = 0.05
        else:
            base_chipload = 0.08
    
    return base_chipload


def is_micro_tool(diameter_mm: float) -> bool:
    """
    Determine if a tool is considered a micro tool requiring special parameters.
    
    Args:
        diameter_mm: Tool diameter in mm
        
    Returns:
        True if tool is micro (<3mm), False otherwise
    """
    return diameter_mm < 3.0


def adjust_speed_for_coating(base_speed: float, coating: str) -> float:
    """
    Adjust cutting speed based on tool coating.
    
    Args:
        base_speed: Base cutting speed for uncoated tool
        coating: Coating type ('tin', 'ticn', 'tialn', etc.)
        
    Returns:
        Adjusted cutting speed
    """
    multiplier = COATING_MULTIPLIERS.get(coating.lower(), 1.0)
    return base_speed * multiplier


def adjust_for_machine_rigidity(parameter_value: float, parameter_type: str, 
                               rigidity_level: str, material_type: str = None) -> float:
    """
    Adjust machining parameters based on machine rigidity level.
    
    Args:
        parameter_value: Original parameter value
        parameter_type: Type of parameter ('chipload', 'doc', 'woc', 'surface_speed')
        rigidity_level: Machine rigidity level (router, diy_medium, vmc_industrial)
        material_type: Optional material type for steel-specific adjustments
        
    Returns:
        Adjusted parameter value
    """
    if rigidity_level not in MACHINE_RIGIDITY_FACTORS:
        return parameter_value
    
    rigidity_props = MACHINE_RIGIDITY_FACTORS[rigidity_level]
    
    if parameter_type == 'chipload':
        return parameter_value * rigidity_props['chipload_factor']
    elif parameter_type == 'doc':
        return parameter_value * rigidity_props['doc_factor']
    elif parameter_type == 'woc':
        return parameter_value * rigidity_props['woc_factor']
    elif parameter_type == 'surface_speed':
        # Special handling for steel on router machines
        if material_type and 'steel' in material_type.lower() and rigidity_level == MachineRigidity.ROUTER:
            # Limit steel cutting speed on routers
            steel_limit = rigidity_props['steel_sfm_limit']
            if parameter_value > steel_limit:
                return steel_limit
        return parameter_value
    
    return parameter_value


def get_rigidity_warnings(rpm: float, surface_speed: float, chipload: float,
                         rigidity_level: str, material_type: str = None, 
                         tool_diameter: float = None) -> List[str]:
    """
    Generate warnings based on machine rigidity and cutting parameters.
    
    Args:
        rpm: Calculated RPM
        surface_speed: Surface speed (SFM)
        chipload: Chip load (mm/tooth)
        rigidity_level: Machine rigidity level
        material_type: Material being cut
        tool_diameter: Tool diameter in mm (for micro tool warnings)
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if rigidity_level not in MACHINE_RIGIDITY_FACTORS:
        return warnings
    
    rigidity_props = MACHINE_RIGIDITY_FACTORS[rigidity_level]
    
    # Check minimum RPM for machine type
    if rpm < rigidity_props['min_rpm']:
        if rigidity_level == MachineRigidity.ROUTER:
            warnings.append(f"RPM too low for router spindle (min {rigidity_props['min_rpm']} recommended)")
        else:
            warnings.append(f"RPM below recommended minimum for this machine type ({rigidity_props['min_rpm']})")
    
    # Steel cutting warnings for lighter machines
    if material_type and 'steel' in material_type.lower():
        if rigidity_level == MachineRigidity.ROUTER:
            warnings.append("Router machines may struggle with steel - consider aluminum or brass alternatives")
            if surface_speed < 80:
                warnings.append("Low surface speed for steel on router - expect poor surface finish")
        elif rigidity_level == MachineRigidity.DIY_MEDIUM:
            if surface_speed > rigidity_props['steel_sfm_limit']:
                warnings.append("Steel cutting at high speed on DIY machine - watch for excessive wear")
    
    # Chatter sensitivity warnings
    if rigidity_level in [MachineRigidity.ROUTER, MachineRigidity.DIY_MEDIUM]:
        if chipload > 0.2:  # High chipload threshold (mm)
            warnings.append("High chipload may cause chatter on this machine type - reduce if vibration occurs")
    
    # Conservative chipload warnings for hobby machines
    chipload_inches = chipload * 0.0393701  # Convert mm to inches
    if rigidity_level in [MachineRigidity.ROUTER, MachineRigidity.DIY_MEDIUM]:
        if chipload_inches > 0.004:  # 0.004" threshold
            warnings.append(f"Chipload {chipload_inches:.4f}\" is aggressive for hobby machines - consider reducing to <0.003\"")
        elif chipload_inches > 0.003:  # 0.003" caution threshold
            warnings.append(f"Chipload {chipload_inches:.4f}\" is moderately aggressive - watch for tool deflection")
    
    # Micro tool specific warnings
    if tool_diameter and is_micro_tool(tool_diameter):
        warnings.append(f"🔍 Micro Tool Mode ({tool_diameter:.1f}mm) - Special considerations apply:")
        warnings.append("   • Use stub-length tools for maximum rigidity")
        warnings.append("   • Check spindle runout (<0.0003\" critical)")
        warnings.append("   • Reduce DOC to 25% of diameter maximum")
        
        if tool_diameter < 1.5:
            warnings.append("   • Consider air/mist cooling for chip evacuation")
        
        if rigidity_level in [MachineRigidity.ROUTER, MachineRigidity.DIY_MEDIUM]:
            warnings.append("   • Monitor for tool deflection - reduce feed if poor finish")
            
        if material_type and 'aluminum' in material_type.lower():
            warnings.append("   • Ensure adequate coolant to prevent chip welding")
    
    return warnings


def get_machine_rigidity_info(rigidity_level: str) -> Dict[str, any]:
    """
    Get machine rigidity information and recommended settings.
    
    Args:
        rigidity_level: Machine rigidity level
        
    Returns:
        Dictionary with rigidity information
    """
    return MACHINE_RIGIDITY_FACTORS.get(rigidity_level, MACHINE_RIGIDITY_FACTORS[MachineRigidity.VMC_INDUSTRIAL])


def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert between common machining units.
    
    Args:
        value: Value to convert
        from_unit: Source unit ('mm', 'in', 'sfm', 'smm', 'hp', 'kw')
        to_unit: Target unit
        
    Returns:
        Converted value
    """
    # Length conversions
    if from_unit == 'mm' and to_unit == 'in':
        return value * MM_TO_INCH
    elif from_unit == 'in' and to_unit == 'mm':
        return value * INCH_TO_MM
    elif from_unit == 'thou' and to_unit == 'mm':
        return value * THOU_TO_MM
    elif from_unit == 'mm' and to_unit == 'thou':
        return value * MM_TO_THOU
    
    # Speed conversions
    elif from_unit == 'sfm' and to_unit == 'smm':
        return value * SFM_TO_SMM
    elif from_unit == 'smm' and to_unit == 'sfm':
        return value * SMM_TO_SFM
    
    # Power conversions
    elif from_unit == 'hp' and to_unit == 'kw':
        return value * HP_TO_KW
    elif from_unit == 'kw' and to_unit == 'hp':
        return value * KW_TO_HP
    
    else:
        raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported")


def validate_machining_parameters(rpm: float, feed_rate: float, depth_of_cut: float,
                                width_of_cut: float, tool_diameter: float) -> List[str]:
    """
    Validate machining parameters for basic sanity checks.
    
    Args:
        rpm: Spindle speed (RPM)
        feed_rate: Feed rate (mm/min)
        depth_of_cut: Depth of cut (mm)
        width_of_cut: Width of cut (mm)
        tool_diameter: Tool diameter (mm)
        
    Returns:
        List of warning messages (empty if all OK)
    """
    warnings = []
    
    if rpm <= 0:
        warnings.append("RPM must be greater than 0")
    elif rpm > 50000:
        warnings.append("RPM extremely high (>50,000) - check calculation")
    
    if feed_rate <= 0:
        warnings.append("Feed rate must be greater than 0")
    elif feed_rate > 10000:
        warnings.append("Feed rate extremely high (>10,000 mm/min)")
    
    if depth_of_cut < 0:
        warnings.append("Depth of cut cannot be negative")
    elif depth_of_cut > tool_diameter:
        warnings.append("Depth of cut greater than tool diameter - very aggressive")
    
    if width_of_cut < 0:
        warnings.append("Width of cut cannot be negative")
    elif width_of_cut > tool_diameter:
        warnings.append("Width of cut greater than tool diameter")
    
    # Check for extremely light cuts
    if depth_of_cut > 0 and width_of_cut > 0:
        if depth_of_cut < 0.01 and width_of_cut < 0.01:
            warnings.append("Very light cut - may cause rubbing instead of cutting")
    
    return warnings


def calculate_chip_thinning_factor(woc_mm: float, tool_diameter_mm: float) -> float:
    """
    Calculate radial chip thinning factor (RCTF).
    
    Formula: RCTF = 1/√(1 - [1 - (2 × Ae/D)]²)
    
    Args:
        woc_mm: Width of cut (radial engagement) in mm
        tool_diameter_mm: Tool diameter in mm
        
    Returns:
        Chip thinning factor (1.0 = no thinning, >1.0 = compensation needed)
    """
    if tool_diameter_mm <= 0:
        return 1.0
        
    ae_ratio = woc_mm / tool_diameter_mm
    
    if ae_ratio >= 0.5:
        return 1.0  # No chip thinning at ≥50% engagement
    
    if ae_ratio <= 0.01:  # Very small engagement
        return min(2.5, 1.0 / math.sqrt(max(0.01, 1 - (1 - 2 * ae_ratio) ** 2)))
    
    # RCTF = 1/√(1 - [1 - (2 × Ae/D)]²)
    inner_term = 1 - 2 * ae_ratio
    denominator = 1 - inner_term ** 2
    
    if denominator <= 0:
        return 2.5  # Cap at 2.5x for extreme cases
    
    return min(2.5, 1.0 / math.sqrt(denominator))


def apply_hsm_speed_boost(surface_speed: float, material_type: str, hsm_enabled: bool) -> float:
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
    
    material_lower = material_type.lower() if material_type else ''
    
    for material, multiplier in hsm_multipliers.items():
        if material in material_lower:
            return surface_speed * multiplier
    
    return surface_speed * 1.15  # Default 15% increase


def get_material_property(material_key: str, property_name: str, 
                         materials_db: Dict = None) -> Optional[float]:
    """
    Get a specific property for a material from the database.
    
    Args:
        material_key: Material key (e.g., 'aluminum.6061')
        property_name: Property name (e.g., 'kc_typical', 'sfm_typical')
        materials_db: Materials database (if None, loads default)
        
    Returns:
        Property value or None if not found
    """
    if materials_db is None:
        materials_db = load_materials_database()
    
    try:
        # Navigate the nested material structure
        keys = material_key.split('.')
        current = materials_db['materials']
        
        for key in keys:
            current = current[key]
            if 'variants' in current:
                current = current['variants']
        
        return current.get(property_name)
        
    except (KeyError, TypeError):
        return None


# Physical Constants for Tool Deflection
CARBIDE_YOUNGS_MODULUS = 600e9  # Pa (600 GPa for carbide)
CARBIDE_DENSITY = 14500  # kg/m³
MINIMUM_CHIP_THICKNESS = 0.001  # mm, minimum chip thickness for micro tools

# Micro Machining Thresholds
MICRO_TOOL_THRESHOLD = 3.0  # mm
ULTRA_MICRO_THRESHOLD = 1.0  # mm


class StandardMachiningCalculator:
    """
    Calculation engine for standard machining operations (tools ≥3mm).
    
    Uses traditional machining formulas with rigidity adjustments.
    Optimized for conventional end mills and cutting operations.
    """
    
    def __init__(self):
        self.warnings = []
    
    def calculate_chipload(self, diameter_mm: float, material_type: str, flute_count: int, 
                          base_chipload: float, rigidity_level: str) -> float:
        """
        Calculate chipload for standard tools using traditional methods.
        
        Args:
            diameter_mm: Tool diameter in mm
            material_type: Material being cut
            flute_count: Number of flutes
            base_chipload: Base chipload from material database
            rigidity_level: Machine rigidity level
            
        Returns:
            Adjusted chipload (mm/tooth)
        """
        # Start with base material chipload
        chipload = base_chipload
        
        # Apply flute count multipliers for standard tools
        if flute_count == 1:
            chipload *= 1.25  # Single flute - higher chipload capability
        elif flute_count == 2:
            chipload *= 1.0   # 2-flute baseline
        elif flute_count >= 3:
            chipload *= 0.85  # Multi-flute - reduced per flute load
        
        # Apply rigidity adjustments
        chipload = adjust_for_machine_rigidity(
            chipload, 'chipload', rigidity_level, material_type
        )
        
        return chipload
    
    def calculate_tool_deflection(self, force_n: float, diameter_mm: float, stickout_mm: float) -> float:
        """
        Calculate tool deflection using cantilever beam theory for standard tools.
        
        Formula: δ = F*L³/(3*E*I)
        
        Args:
            force_n: Cutting force in Newtons
            diameter_mm: Tool diameter in mm
            stickout_mm: Tool stickout length in mm
            
        Returns:
            Tool tip deflection in mm
        """
        # Material properties for carbide
        E = CARBIDE_YOUNGS_MODULUS  # Young's modulus (Pa)
        
        # Convert to meters
        radius_m = (diameter_mm / 2) / 1000  # Convert to meters
        stickout_m = stickout_mm / 1000
        
        # Moment of inertia for circular cross-section: I = π*r⁴/4
        moment_inertia = (math.pi * (radius_m ** 4)) / 4
        
        # Cantilever beam deflection formula
        deflection_m = (force_n * (stickout_m ** 3)) / (3 * E * moment_inertia)
        
        return deflection_m * 1000  # Convert back to mm
    
    def calculate_cutting_force(self, kc: float, doc_mm: float, woc_mm: float, feed_per_tooth: float) -> float:
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

    def calculate_cutting_parameters(self, diameter: float, flute_num: int, doc: float, 
                                   woc: float, smm: float, mmpt: float, kc: float,
                                   rigidity_level: str, material_type: str, 
                                   tool_stickout: float = 15.0, hsm_enabled: bool = False,
                                   chip_thinning_enabled: bool = False) -> dict:
        """
        Calculate standard machining parameters with deflection analysis and HSM support.
        
        Returns:
            Dictionary with calculated values and warnings
        """
        self.warnings = []
        
        # Apply HSM speed boost if enabled
        if hsm_enabled:
            smm = apply_hsm_speed_boost(smm * 3.28084, material_type, hsm_enabled) * 0.3048
        
        # Apply rigidity adjustments to cutting parameters
        adjusted_doc = adjust_for_machine_rigidity(doc, 'doc', rigidity_level, material_type)
        adjusted_woc = adjust_for_machine_rigidity(woc, 'woc', rigidity_level, material_type)
        adjusted_smm = adjust_for_machine_rigidity(smm, 'surface_speed', rigidity_level, material_type)
        
        # Calculate chipload using standard method
        adjusted_mmpt = self.calculate_chipload(
            diameter, material_type, flute_num, mmpt, rigidity_level
        )
        
        # Apply chip thinning compensation if enabled
        chip_thinning_factor = 1.0
        if chip_thinning_enabled:
            chip_thinning_factor = calculate_chip_thinning_factor(adjusted_woc, diameter)
            adjusted_mmpt *= chip_thinning_factor
        
        # Standard RPM calculation
        if diameter > 0 and adjusted_smm > 0:
            rpm = calculate_rpm(adjusted_smm, diameter, 'metric')
        else:
            rpm = 0.0
        
        # Standard feed rate calculation
        if rpm > 0 and adjusted_mmpt > 0:
            feed_rate = calculate_feed_rate(rpm, flute_num, adjusted_mmpt)
        else:
            feed_rate = 0.0
        
        # Material removal rate
        if adjusted_woc > 0 and adjusted_doc > 0 and feed_rate > 0:
            mrr = calculate_mrr_milling(adjusted_doc, adjusted_woc, feed_rate)
        else:
            mrr = 0.0
        
        # Required spindle power
        if kc > 0 and mrr > 0:
            power_kw = calculate_cutting_power(mrr, kc)
        else:
            power_kw = 0.0
        
        # Calculate deflection for all tool sizes now
        cutting_force = self.calculate_cutting_force(kc, adjusted_doc, adjusted_woc, adjusted_mmpt)
        tool_deflection = self.calculate_tool_deflection(cutting_force, diameter, tool_stickout)
        
        # Get standard warnings
        param_warnings = validate_machining_parameters(rpm, feed_rate, doc, woc, diameter)
        rigidity_warnings = get_rigidity_warnings(
            rpm, adjusted_smm * 3.28084, adjusted_mmpt, rigidity_level, material_type, diameter
        )
        self.warnings = param_warnings + rigidity_warnings
        
        # Add deflection warnings
        deflection_percent = (tool_deflection / diameter) * 100 if diameter > 0 else 0
        if deflection_percent > 5:
            self.warnings.append(f"High deflection: {tool_deflection:.4f}mm ({deflection_percent:.1f}% of diameter)")
        elif deflection_percent > 1:
            self.warnings.append("Monitor surface finish - deflection may affect quality")
        
        return {
            'rpm': rpm,
            'feed_rate': feed_rate,
            'mrr': mrr,
            'power_kw': power_kw,
            'adjusted_mmpt': adjusted_mmpt,
            'adjusted_doc': adjusted_doc,
            'adjusted_woc': adjusted_woc,
            'adjusted_smm': adjusted_smm,
            'tool_deflection': tool_deflection,
            'cutting_force': cutting_force,
            'chip_thinning_factor': chip_thinning_factor,
            'warnings': self.warnings
        }


class MicroMachiningCalculator:
    """
    Advanced calculation engine for micro machining operations (tools <3mm).
    
    Implements tool deflection modeling using cantilever beam theory,
    iterative cutting force calculations, and physics-based parameters.
    """
    
    def __init__(self):
        self.warnings = []
        self.tool_stickout = 15.0  # mm, default conservative stickout
        self.max_iterations = 10
        self.convergence_tolerance = 0.001  # mm, deflection convergence
    
    def calculate_moment_of_inertia(self, diameter_mm: float) -> float:
        """
        Calculate second moment of area for circular cross-section.
        
        Args:
            diameter_mm: Tool diameter in mm
            
        Returns:
            Second moment of area (mm⁴)
        """
        radius_mm = diameter_mm / 2.0
        return (math.pi * (radius_mm ** 4)) / 4.0  # I = π*r⁴/4
    
    def calculate_cutting_force(self, kc: float, chip_area_mm2: float, 
                              diameter_mm: float) -> float:
        """
        Calculate cutting force for micro tools with corrections.
        
        Args:
            kc: Specific cutting force (N/mm²)
            chip_area_mm2: Chip cross-sectional area (mm²)
            diameter_mm: Tool diameter for size effect corrections
            
        Returns:
            Cutting force (N)
        """
        # Basic cutting force
        force = kc * chip_area_mm2
        
        # Size effect correction for micro tools
        # Smaller tools experience higher specific forces due to material strengthening
        if diameter_mm < 1.0:
            size_effect = 1.5  # 50% increase for ultra-micro tools
        elif diameter_mm < 2.0:
            size_effect = 1.3  # 30% increase for small micro tools
        else:
            size_effect = 1.1  # 10% increase for larger micro tools
        
        force *= size_effect
        
        return force
    
    def calculate_tool_deflection(self, force_n: float, diameter_mm: float, 
                                stickout_mm: float = None) -> float:
        """
        Calculate tool deflection using cantilever beam theory.
        
        Args:
            force_n: Applied force (N)
            diameter_mm: Tool diameter (mm)  
            stickout_mm: Tool stickout length (mm)
            
        Returns:
            Tool tip deflection (mm)
        """
        if stickout_mm is None:
            stickout_mm = self.tool_stickout
        
        # Convert to meters for calculation
        diameter_m = diameter_mm / 1000.0
        stickout_m = stickout_mm / 1000.0
        
        # Calculate moment of inertia
        moment_inertia = self.calculate_moment_of_inertia(diameter_mm) / (1000.0 ** 4)  # Convert to m⁴
        
        # Cantilever beam deflection: δ = F*L³/(3*E*I)
        deflection_m = (force_n * (stickout_m ** 3)) / (3.0 * CARBIDE_YOUNGS_MODULUS * moment_inertia)
        
        # Convert back to mm
        return deflection_m * 1000.0
    
    def calculate_effective_chipload(self, target_chipload: float, deflection_mm: float,
                                   feed_rate: float, rpm: float, flute_count: int) -> float:
        """
        Calculate effective chipload considering tool deflection.
        
        Tool deflection reduces the actual chip thickness by moving the tool
        away from the workpiece during cutting.
        
        Args:
            target_chipload: Intended chipload (mm/tooth)
            deflection_mm: Tool tip deflection (mm)
            feed_rate: Feed rate (mm/min)
            rpm: Spindle speed (RPM)
            flute_count: Number of flutes
            
        Returns:
            Effective chipload after deflection (mm/tooth)
        """
        if rpm <= 0 or flute_count <= 0:
            return 0.0
        
        # Calculate actual chip thickness after deflection
        # Deflection effectively reduces the chip thickness
        effective_chipload = max(target_chipload - deflection_mm, MINIMUM_CHIP_THICKNESS)
        
        return effective_chipload
    
    def calculate_micro_chipload(self, diameter_mm: float, material_type: str, 
                               flute_count: int, rigidity_level: str) -> float:
        """
        Calculate chipload for micro tools using percentage of diameter method.
        
        Args:
            diameter_mm: Tool diameter in mm
            material_type: Material being cut
            flute_count: Number of flutes
            rigidity_level: Machine rigidity level
            
        Returns:
            Micro tool chipload (mm/tooth)
        """
        if diameter_mm < ULTRA_MICRO_THRESHOLD:
            # Ultra-micro tools: fixed minimum to prevent breakage
            base_chipload = 0.005  # ~0.0002"
        else:
            # Micro tools: percentage of diameter
            if material_type and 'aluminum' in material_type.lower():
                percentage = 0.015  # 1.5% of diameter for aluminum
            elif material_type and ('steel' in material_type.lower() or 'stainless' in material_type.lower()):
                percentage = 0.01   # 1% of diameter for harder materials
            else:
                percentage = 0.012  # Default 1.2%
            
            base_chipload = diameter_mm * percentage
        
        # Apply flute multiplier (much more conservative for micro tools)
        if flute_count == 1:
            base_chipload *= 1.1  # Only 10% increase for single flute micro tools
        elif flute_count >= 3:
            base_chipload *= 0.8  # Reduce for multiple flutes
        
        # Apply rigidity adjustments
        adjusted_chipload = adjust_for_machine_rigidity(
            base_chipload, 'chipload', rigidity_level, material_type
        )
        
        return adjusted_chipload
    
    def iterative_calculation(self, diameter: float, flute_num: int, doc: float, 
                            woc: float, smm: float, kc: float, rigidity_level: str,
                            material_type: str, hsm_enabled: bool = False,
                            chip_thinning_enabled: bool = False) -> dict:
        """
        Perform iterative calculation considering tool deflection effects.
        
        The cutting force causes tool deflection, which reduces effective chipload,
        which changes cutting force. Iterate until convergence.
        
        Returns:
            Dictionary with converged values
        """
        # Apply HSM speed boost if enabled
        if hsm_enabled:
            smm = apply_hsm_speed_boost(smm * 3.28084, material_type, hsm_enabled) * 0.3048
        
        # Initial chipload calculation
        target_chipload = self.calculate_micro_chipload(
            diameter, material_type, flute_num, rigidity_level
        )
        
        # Apply rigidity adjustments to other parameters
        adjusted_doc = adjust_for_machine_rigidity(doc, 'doc', rigidity_level, material_type)
        adjusted_woc = adjust_for_machine_rigidity(woc, 'woc', rigidity_level, material_type) 
        adjusted_smm = adjust_for_machine_rigidity(smm, 'surface_speed', rigidity_level, material_type)
        
        # Apply chip thinning compensation if enabled
        chip_thinning_factor = 1.0
        if chip_thinning_enabled:
            chip_thinning_factor = calculate_chip_thinning_factor(adjusted_woc, diameter)
            target_chipload *= chip_thinning_factor
        
        # Initial calculations
        rpm = calculate_rpm(adjusted_smm, diameter, 'metric') if diameter > 0 and adjusted_smm > 0 else 0.0
        
        # Iterative convergence loop
        current_chipload = target_chipload
        previous_deflection = 0.0
        
        for iteration in range(self.max_iterations):
            # Calculate feed rate with current chipload
            feed_rate = calculate_feed_rate(rpm, flute_num, current_chipload) if rpm > 0 else 0.0
            
            # Calculate chip area (simplified for micro tools)
            chip_area = current_chipload * adjusted_doc  # mm²
            
            # Calculate cutting force
            cutting_force = self.calculate_cutting_force(kc, chip_area, diameter)
            
            # Calculate tool deflection
            deflection = self.calculate_tool_deflection(cutting_force, diameter, self.tool_stickout)
            
            # Check convergence
            if abs(deflection - previous_deflection) < self.convergence_tolerance:
                break
            
            # Calculate new effective chipload
            current_chipload = self.calculate_effective_chipload(
                target_chipload, deflection, feed_rate, rpm, flute_num
            )
            
            previous_deflection = deflection
        
        # Final calculations with converged values
        final_feed_rate = calculate_feed_rate(rpm, flute_num, current_chipload) if rpm > 0 else 0.0
        
        # Material removal rate  
        if adjusted_woc > 0 and adjusted_doc > 0 and final_feed_rate > 0:
            mrr = calculate_mrr_milling(adjusted_doc, adjusted_woc, final_feed_rate)
        else:
            mrr = 0.0
        
        # Power calculation
        if kc > 0 and mrr > 0:
            power_kw = calculate_cutting_power(mrr, kc)
        else:
            power_kw = 0.0
        
        return {
            'rpm': rpm,
            'feed_rate': final_feed_rate,
            'mrr': mrr,
            'power_kw': power_kw,
            'adjusted_mmpt': current_chipload,
            'adjusted_doc': adjusted_doc,
            'adjusted_woc': adjusted_woc,
            'adjusted_smm': adjusted_smm,
            'tool_deflection': deflection,
            'cutting_force': cutting_force,
            'chip_thinning_factor': chip_thinning_factor,
            'iterations': iteration + 1,
            'target_chipload': target_chipload
        }
    
    def calculate_cutting_parameters(self, diameter: float, flute_num: int, doc: float,
                                   woc: float, smm: float, mmpt: float, kc: float,
                                   rigidity_level: str, material_type: str,
                                   tool_stickout: float = 15.0, hsm_enabled: bool = False,
                                   chip_thinning_enabled: bool = False) -> dict:
        """
        Main calculation method for micro machining parameters.
        
        Returns:
            Dictionary with calculated values and warnings
        """
        self.warnings = []
        
        # Perform iterative calculation
        results = self.iterative_calculation(
            diameter, flute_num, doc, woc, smm, kc, rigidity_level, material_type, hsm_enabled, chip_thinning_enabled
        )
        
        # Generate micro-specific warnings
        self.warnings.extend(self._generate_micro_warnings(diameter, results, rigidity_level, material_type))
        
        # Add basic parameter warnings
        param_warnings = validate_machining_parameters(
            results['rpm'], results['feed_rate'], doc, woc, diameter
        )
        self.warnings.extend(param_warnings)
        
        # Add rigidity warnings
        rigidity_warnings = get_rigidity_warnings(
            results['rpm'], results['adjusted_smm'] * 3.28084, results['adjusted_mmpt'],
            rigidity_level, material_type, diameter
        )
        self.warnings.extend(rigidity_warnings)
        
        results['warnings'] = self.warnings
        return results
    
    def _generate_micro_warnings(self, diameter: float, results: dict, 
                               rigidity_level: str, material_type: str) -> List[str]:
        """Generate warnings specific to micro machining."""
        warnings = []
        
        deflection = results.get('tool_deflection', 0)
        cutting_force = results.get('cutting_force', 0)
        iterations = results.get('iterations', 0)
        
        # Tool deflection warnings
        deflection_percentage = (deflection / diameter) * 100 if diameter > 0 else 0
        if deflection_percentage > 5:
            warnings.append(f"⚠️ High deflection: {deflection:.4f}mm ({deflection_percentage:.1f}% of diameter)")
        elif deflection_percentage > 2:
            warnings.append(f"⚠️ Moderate deflection: {deflection:.4f}mm - monitor surface finish")
        
        # Cutting force warnings
        if cutting_force > 50:
            warnings.append(f"⚠️ High cutting force: {cutting_force:.1f}N - risk of tool breakage")
        
        # Convergence warnings
        if iterations >= self.max_iterations:
            warnings.append("⚠️ Calculation did not fully converge - results may be approximate")
        
        # Ultra-micro specific warnings
        if diameter < ULTRA_MICRO_THRESHOLD:
            warnings.append("🔬 Ultra-Micro Tool (<1mm) - Extreme care required:")
            warnings.append("   • Use minimal stickout length")
            warnings.append("   • Perfect spindle runout essential (<0.0001\")")
            warnings.append("   • Consider high-frequency spindle for better finish")
        
        # Material-specific micro warnings
        if material_type and 'steel' in material_type.lower() and diameter < 2.0:
            warnings.append("⚠️ Micro steel cutting - consider carbide coating for tool life")
        
        return warnings
    
    def set_tool_stickout(self, stickout_mm: float):
        """Set tool stickout length for deflection calculations."""
        self.tool_stickout = max(stickout_mm, 5.0)  # Minimum 5mm stickout


class FeedsAndSpeeds:
    """
    CNC machining feeds and speeds calculator using strategy pattern.
    
    Automatically selects between StandardMachiningCalculator and MicroMachiningCalculator
    based on tool diameter. Provides a unified interface for all machining calculations.
    """
    
    def __init__(self):
        # Tool parameters
        self.diameter = 0.0          # Tool diameter (mm)
        self.flute_num = 2           # Number of flutes/cutting edges
        self.tool_stickout = 15.0    # Tool stickout length for deflection calculations (mm)
        
        # Cutting parameters
        self.doc = 0.0               # Depth of cut (mm)
        self.woc = 0.0               # Width of cut (mm)
        self.smm = 0.0               # Surface speed (m/min)
        self.mmpt = 0.0              # Feed per tooth (mm/tooth)
        self.kc = 0.0                # Specific cutting force (N/mm²)
        
        # HSM and chip thinning parameters
        self.hsm_enabled = False     # High speed machining mode
        self.chip_thinning_enabled = False  # Chip thinning compensation
        
        # Machine rigidity parameters
        self.rigidity_level = MachineRigidity.VMC_INDUSTRIAL  # Default to industrial
        self.material_type = None    # Material type for rigidity-aware adjustments
        
        # Calculated results
        self.rpm = 0.0               # Spindle speed (RPM)
        self.feed = 0.0              # Feed rate (mm/min)
        self.mrr = 0.0               # Material removal rate (cm³/min)
        self.kw = 0.0                # Required spindle power (kW)
        
        # Rigidity-adjusted values
        self.adjusted_mmpt = 0.0     # Rigidity-adjusted chip load
        self.adjusted_doc = 0.0      # Rigidity-adjusted depth of cut
        self.adjusted_woc = 0.0      # Rigidity-adjusted width of cut
        self.adjusted_smm = 0.0      # Rigidity-adjusted surface speed
        
        # Micro machining specific results
        self.tool_deflection = 0.0   # Tool deflection (mm)
        self.cutting_force = 0.0     # Cutting force (N)
        self.chip_thinning_factor = 1.0  # Chip thinning compensation factor
        self.is_micro_tool = False   # True if using micro calculator
        
        # Calculator instances
        self._standard_calc = StandardMachiningCalculator()
        self._micro_calc = MicroMachiningCalculator()
    
    def validate_inputs(self):
        """Validate input parameters before calculation."""
        errors = []
        
        if not self.diameter or self.diameter <= 0:
            errors.append("Tool diameter must be greater than 0")
        if not self.flute_num or self.flute_num <= 0:
            errors.append("Number of flutes must be greater than 0")
        if self.doc < 0:
            errors.append("Depth of cut cannot be negative")
        if self.woc < 0:
            errors.append("Width of cut cannot be negative")
        if self.smm < 0:
            errors.append("Surface speed cannot be negative")
        if self.mmpt < 0:
            errors.append("Feed per tooth cannot be negative")
        if self.kc < 0:
            errors.append("Specific cutting force cannot be negative")
            
        return errors
    
    def _select_calculator(self) -> Union[StandardMachiningCalculator, MicroMachiningCalculator]:
        """
        Select appropriate calculator based on tool diameter.
        
        Returns:
            Calculator instance (StandardMachiningCalculator or MicroMachiningCalculator)
        """
        if self.diameter < MICRO_TOOL_THRESHOLD:
            self.is_micro_tool = True
            # Set tool stickout for micro calculator
            self._micro_calc.set_tool_stickout(self.tool_stickout)
            return self._micro_calc
        else:
            self.is_micro_tool = False
            return self._standard_calc
    
    def calculate(self):
        """
        Calculate machining parameters using the appropriate calculation engine.
        
        Automatically selects between standard and micro machining calculations
        based on tool diameter (<3mm uses micro calculator).
        """
        # Validate inputs first
        validation_errors = self.validate_inputs()
        if validation_errors:
            # Set results to zero if validation fails
            self._reset_results()
            return validation_errors
        
        # Select appropriate calculator
        calculator = self._select_calculator()
        
        # Perform calculation using selected engine
        results = calculator.calculate_cutting_parameters(
            self.diameter, self.flute_num, self.doc, self.woc,
            self.smm, self.mmpt, self.kc, self.rigidity_level, self.material_type,
            self.tool_stickout, self.hsm_enabled, self.chip_thinning_enabled
        )
        
        # Update instance variables with results
        self.rpm = results.get('rpm', 0.0)
        self.feed = results.get('feed_rate', 0.0)
        self.mrr = results.get('mrr', 0.0)
        self.kw = results.get('power_kw', 0.0)
        
        # Update adjusted values
        self.adjusted_mmpt = results.get('adjusted_mmpt', 0.0)
        self.adjusted_doc = results.get('adjusted_doc', 0.0)
        self.adjusted_woc = results.get('adjusted_woc', 0.0)
        self.adjusted_smm = results.get('adjusted_smm', 0.0)
        
        # Update tool deflection and cutting force (now available for all tools)
        self.tool_deflection = results.get('tool_deflection', 0.0)
        self.cutting_force = results.get('cutting_force', 0.0)
        self.chip_thinning_factor = results.get('chip_thinning_factor', 1.0)
        
        # Return warnings from calculation
        return results.get('warnings', [])
    
    def _reset_results(self):
        """Reset all calculated results to zero."""
        self.rpm = 0.0
        self.feed = 0.0
        self.mrr = 0.0
        self.kw = 0.0
        self.adjusted_mmpt = 0.0
        self.adjusted_doc = 0.0
        self.adjusted_woc = 0.0
        self.adjusted_smm = 0.0
        self.tool_deflection = 0.0
        self.cutting_force = 0.0
        self.chip_thinning_factor = 1.0
    
    def set_tool_stickout(self, stickout_mm: float):
        """
        Set tool stickout length for micro tool deflection calculations.
        
        Args:
            stickout_mm: Tool stickout length in mm
        """
        self.tool_stickout = max(stickout_mm, 5.0)  # Minimum 5mm stickout
        if hasattr(self._micro_calc, 'set_tool_stickout'):
            self._micro_calc.set_tool_stickout(self.tool_stickout)
    
    def get_results_dict(self):
        """Return calculated results as a dictionary."""
        return {
            'rpm': self.rpm,
            'feed_rate_mm_min': self.feed,
            'feed_rate_in_min': self.feed * 0.0393701,
            'mrr_cm3_min': self.mrr,
            'mrr_in3_min': self.mrr * 0.0610237,
            'power_kw': self.kw,
            'power_hp': self.kw * 1.34102
        }
    
    def print_values(self):
        """Print current input parameters and calculated results."""
        print("=== CNC Feeds and Speeds Calculator ===")
        print("\nTool Parameters:")
        print(f"  Diameter: {self.diameter:.3f} mm")
        print(f"  Flutes: {self.flute_num}")
        
        print("\nCutting Parameters:")
        print(f"  Depth of Cut: {self.doc:.3f} mm")
        print(f"  Width of Cut: {self.woc:.3f} mm")
        print(f"  Surface Speed: {self.smm:.1f} m/min")
        print(f"  Feed per Tooth: {self.mmpt:.4f} mm/tooth")
        print(f"  Specific Cutting Force: {self.kc:.0f} N/mm²")
        
        print("\nCalculated Results:")
        print(f"  RPM: {self.rpm:.0f}")
        print(f"  Feed Rate: {self.feed:.2f} mm/min ({self.feed * 0.0393701:.2f} in/min)")
        print(f"  MRR: {self.mrr:.2f} cm³/min ({self.mrr * 0.0610237:.3f} in³/min)")
        print(f"  Power: {self.kw:.2f} kW ({self.kw * 1.34102:.2f} HP)")
    
    def copy_from(self, other):
        """Copy all parameters from another FeedsAndSpeeds instance."""
        if isinstance(other, FeedsAndSpeeds):
            self.diameter = other.diameter
            self.flute_num = other.flute_num
            self.doc = other.doc
            self.woc = other.woc
            self.smm = other.smm
            self.mmpt = other.mmpt
            self.kc = other.kc
    
    def set_material_properties(self, material_key: str):
        """
        Set material properties from the MATERIALS database.
        
        Args:
            material_key: Key from MATERIALS dict (e.g., 'aluminum_6061', 'steel_1018')
        """
        if material_key in MATERIALS:
            material = MATERIALS[material_key]
            self.kc = material.kc
            self.smm = material.smm
            self.mmpt = material.chip_load
            return material.name
        else:
            available = list(MATERIALS.keys())
            raise ValueError(f"Material '{material_key}' not found. Available: {available}")
    
    def get_suggested_chip_load(self, material_factor: float = 1.0) -> float:
        """
        Get suggested chip load using rule of thumb.
        
        Args:
            material_factor: Material multiplier (aluminum ~2.0, steel ~1.0, stainless ~0.5)
            
        Returns:
            Suggested chip load (mm/tooth)
        """
        return chip_load_rule_of_thumb(self.diameter, material_factor)
    
    def calculate_torque(self) -> float:
        """
        Calculate spindle torque based on current power and RPM.
        
        Returns:
            Torque in Newton-meters
        """
        return calculate_torque(self.kw, self.rpm)


# Pre-calculated common values for quick reference
COMMON_CALCULATIONS = {
    'aluminum_6061_12mm': {
        'rpm_800sfm': calculate_rpm(244, 12, 'metric'),  # 800 SFM = 244 SMM
        'feed_rate_015cpt': lambda rpm: calculate_feed_rate(rpm, 3, 0.15),
        'description': '12mm 3-flute in 6061 aluminum at 800 SFM, 0.15 chip load'
    },
    'steel_1018_6mm': {
        'rpm_100sfm': calculate_rpm(30.5, 6, 'metric'),  # 100 SFM = 30.5 SMM
        'feed_rate_008cpt': lambda rpm: calculate_feed_rate(rpm, 2, 0.08),
        'description': '6mm 2-flute in 1018 steel at 100 SFM, 0.08 chip load'
    }
}


if __name__ == "__main__":
    # Test the enhanced module
    print("CNC Machining Formulas and Constants Module Test")
    print("=" * 50)
    
    # Test material properties
    aluminum = MATERIALS['aluminum_6061']
    steel = MATERIALS['steel_1018']
    
    print(f"\nMaterial Properties:")
    print(f"Aluminum 6061: Kc={aluminum.kc} N/mm², Speed={aluminum.sfm} SFM ({aluminum.smm:.1f} SMM), Chip Load={aluminum.chip_load} mm/tooth")
    print(f"Steel 1018: Kc={steel.kc} N/mm², Speed={steel.sfm} SFM ({steel.smm:.1f} SMM), Chip Load={steel.chip_load} mm/tooth")
    
    # Test enhanced FeedsAndSpeeds class
    calc = FeedsAndSpeeds()
    calc.diameter = 12  # 12mm tool
    calc.flute_num = 3  # 3-flute
    calc.doc = 2  # 2mm depth of cut
    calc.woc = 6  # 6mm width of cut
    
    print(f"\nTesting with 12mm 3-flute end mill:")
    
    # Test with aluminum
    material_name = calc.set_material_properties('aluminum_6061')
    print(f"\n{material_name}:")
    warnings = calc.calculate()
    print(f"  RPM: {calc.rpm:.0f}")
    print(f"  Feed Rate: {calc.feed:.1f} mm/min")
    print(f"  MRR: {calc.mrr:.2f} cm³/min")
    print(f"  Power: {calc.kw:.3f} kW ({convert_units(calc.kw, 'kw', 'hp'):.3f} HP)")
    print(f"  Torque: {calc.calculate_torque():.2f} Nm")
    if warnings:
        print(f"  Warnings: {warnings}")
    
    # Test with steel
    material_name = calc.set_material_properties('steel_1018')
    print(f"\n{material_name}:")
    warnings = calc.calculate()
    print(f"  RPM: {calc.rpm:.0f}")
    print(f"  Feed Rate: {calc.feed:.1f} mm/min")
    print(f"  MRR: {calc.mrr:.2f} cm³/min")
    print(f"  Power: {calc.kw:.3f} kW ({convert_units(calc.kw, 'kw', 'hp'):.3f} HP)")
    print(f"  Torque: {calc.calculate_torque():.2f} Nm")
    if warnings:
        print(f"  Warnings: {warnings}")
    
    # Test rule of thumb chip loads
    print(f"\nChip Load Rule of Thumb for 12mm tool:")
    print(f"  Aluminum (2x): {chip_load_rule_of_thumb(12, 2.0):.3f} mm/tooth")
    print(f"  Steel (1x): {chip_load_rule_of_thumb(12, 1.0):.3f} mm/tooth")
    print(f"  Stainless (0.5x): {chip_load_rule_of_thumb(12, 0.5):.3f} mm/tooth")
    
    # Test unit conversions
    print(f"\nUnit Conversion Tests:")
    print(f"  25.4mm = {convert_units(25.4, 'mm', 'in'):.3f} inches")
    print(f"  800 SFM = {convert_units(800, 'sfm', 'smm'):.1f} SMM")
    print(f"  5 kW = {convert_units(5, 'kw', 'hp'):.2f} HP")

