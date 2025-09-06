"""
Unit conversion utilities for the Speeds and Feeds Calculator.

Contains functions for converting between different units used in machining.
"""

from ..constants.units import *


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