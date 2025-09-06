"""
Calculators package for the Speeds and Feeds Calculator.

This package contains the main calculation engines for different types
of machining operations.
"""

from .base import FeedsAndSpeeds
from .standard import StandardMachiningCalculator
from .micro import MicroMachiningCalculator

__all__ = [
    'FeedsAndSpeeds',
    'StandardMachiningCalculator', 
    'MicroMachiningCalculator',
]