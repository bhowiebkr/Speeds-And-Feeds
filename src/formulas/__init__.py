"""
Formulas package for the Speeds and Feeds Calculator.

This package contains all the mathematical formulas and calculations
used for machining parameter computation.
"""

from .basic import *
from .power import *
from .chipload import *
from .deflection import *
from .validation import *

__all__ = [
    # Basic formulas
    'calculate_rpm', 'calculate_feed_rate', 'calculate_surface_speed', 'calculate_mrr_milling',
    
    # Power formulas
    'calculate_cutting_power', 'calculate_torque',
    
    # Chipload formulas
    'chip_load_rule_of_thumb', 'calculate_diameter_based_chipload', 'is_micro_tool',
    'calculate_chip_thinning_factor', 'apply_hsm_speed_boost',
    
    # Deflection calculations
    'calculate_tool_deflection', 'calculate_cutting_force',
    
    # Validation
    'validate_machining_parameters', 'get_rigidity_warnings', 'adjust_speed_for_coating',
]