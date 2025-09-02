"""
Tool deflection calculations for the Speeds and Feeds Calculator.

Contains formulas for calculating tool deflection using cantilever beam theory.
"""

import math
from ..constants.machining import CARBIDE_YOUNGS_MODULUS


def calculate_tool_deflection(force_n: float, diameter_mm: float, stickout_mm: float) -> float:
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
    E = CARBIDE_YOUNGS_MODULUS  # Young's modulus (Pa)
    
    # Convert to meters
    radius_m = (diameter_mm / 2) / 1000  # Convert to meters
    stickout_m = stickout_mm / 1000
    
    # Moment of inertia for circular cross-section: I = π*r⁴/4
    moment_inertia = (math.pi * (radius_m ** 4)) / 4
    
    # Cantilever beam deflection formula
    deflection_m = (force_n * (stickout_m ** 3)) / (3 * E * moment_inertia)
    
    return deflection_m * 1000  # Convert back to mm


def calculate_cutting_force(kc: float, doc_mm: float, woc_mm: float, feed_per_tooth: float) -> float:
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


def calculate_moment_of_inertia(diameter_mm: float) -> float:
    """
    Calculate second moment of area for circular cross-section.
    
    Args:
        diameter_mm: Tool diameter in mm
        
    Returns:
        Second moment of area (mm⁴)
    """
    radius_mm = diameter_mm / 2.0
    return (math.pi * (radius_mm ** 4)) / 4.0  # I = π*r⁴/4