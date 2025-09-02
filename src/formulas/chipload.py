"""
Chip load calculations and adjustments for the Speeds and Feeds Calculator.

Contains formulas for calculating appropriate chip loads for different tools and materials.
"""

import math
from ..constants.machining import MICRO_TOOL_THRESHOLD, ULTRA_MICRO_THRESHOLD
from ..constants.materials import COATING_MULTIPLIERS


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
    return diameter_mm < MICRO_TOOL_THRESHOLD


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