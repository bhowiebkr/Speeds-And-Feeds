"""
Utilities package for the Speeds and Feeds Calculator.

This package contains utility functions used throughout the application.
"""

from .conversions import *
from .rigidity import *

__all__ = [
    'convert_units', 'inches_to_mm', 'mm_to_inches', 'sfm_to_smm', 'smm_to_sfm',
    'adjust_for_machine_rigidity', 'get_machine_rigidity_info',
]