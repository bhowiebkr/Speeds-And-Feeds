"""
Basic machining formulas for the Speeds and Feeds Calculator.

Contains fundamental calculations for RPM, feed rates, surface speeds, and MRR.
"""

import math
from ..constants.units import PI


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