"""
Constants package for the Speeds and Feeds Calculator.

This package contains all the constants used throughout the application,
organized by category for better maintainability.
"""

from .units import *
from .materials import *
from .machining import *

__all__ = [
    # Unit conversion constants
    'INCH_TO_MM', 'MM_TO_INCH', 'SFM_TO_SMM', 'SMM_TO_SFM',
    'HP_TO_KW', 'KW_TO_HP', 'IN_TO_MM', 'MM_TO_IN', 'FT_TO_M', 'FT_TO_MM',
    'MM_TO_FT', 'M_TO_FT',
    
    # Material constants
    'MATERIALS', 'COATING_MULTIPLIERS', 'MaterialProperty',
    
    # Machining constants
    'POWER_CALCULATION_FACTOR', 'DEFAULT_MACHINE_EFFICIENCY', 'SAFETY_FACTOR_DEFAULT',
    'MACHINE_RIGIDITY_FACTORS', 'MachineRigidity', 'CARBIDE_YOUNGS_MODULUS',
    'MICRO_TOOL_THRESHOLD', 'ULTRA_MICRO_THRESHOLD',
]