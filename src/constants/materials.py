"""
Material properties and constants for the Speeds and Feeds Calculator.

Contains material definitions and coating multipliers.
"""

from typing import Union, Tuple
from .units import SFM_TO_SMM


class MaterialProperty:
    """Container for material machining properties."""
    
    def __init__(self, name: str, kc: float, sfm: float, chip_load: float, 
                 hardness: Union[int, Tuple[int, int]] = None):
        self.name = name
        self.kc = kc  # Specific cutting force (N/mm²)
        self.sfm = sfm  # Surface speed (SFM)
        self.smm = sfm * SFM_TO_SMM  # Surface speed (m/min)
        self.chip_load = chip_load  # Feed per tooth (mm/tooth)
        self.hardness = hardness


# Standard Material Properties (typical values)
MATERIALS = {
    'aluminum_6061': MaterialProperty('6061 Aluminum', 800, 1200, 0.08, (95, 150)),
    'steel_1018': MaterialProperty('1018 Mild Steel', 2000, 100, 0.08, (120, 170)),
    'stainless_304': MaterialProperty('304 Stainless', 2600, 75, 0.05, (150, 200)),
    'cast_iron_grey': MaterialProperty('Grey Cast Iron', 1350, 120, 0.08, (150, 250)),
    'titanium_ti64': MaterialProperty('Ti-6Al-4V', 2550, 75, 0.04, (300, 400)),
    'brass_360': MaterialProperty('360 Brass', 700, 600, 0.12, (60, 120)),
    'copper_101': MaterialProperty('101 Copper', 600, 400, 0.10, (40, 80)),
}

# Tool Coating Speed Multipliers
COATING_MULTIPLIERS = {
    'uncoated': 1.0,
    'tin': 1.2,
    'ticn': 1.3,
    'tialn': 1.4,
    'alcrn': 1.5,
    'diamond': 2.0,
}