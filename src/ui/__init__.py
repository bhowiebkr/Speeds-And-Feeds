"""
UI package for the Speeds and Feeds Calculator.

This package contains all the user interface components.
"""

from .boxes import *
from .styles import load_stylesheet

__all__ = [
    'ToolBox', 'MaterialBox', 'CuttingBox', 'MachineBox', 'ResultsBox',
    'load_stylesheet',
]