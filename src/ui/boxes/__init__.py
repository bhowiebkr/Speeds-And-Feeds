"""
UI boxes package for the Speeds and Feeds Calculator.

This package contains all the grouped UI components (boxes/sections).
"""

from .tool import ToolBox
from .material import MaterialBox
from .cutting import CuttingBox
from .machine import MachineBox
from .results import ResultsBox

__all__ = [
    'ToolBox',
    'MaterialBox', 
    'CuttingBox',
    'MachineBox',
    'ResultsBox',
]