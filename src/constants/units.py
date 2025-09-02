"""
Unit conversion constants for the Speeds and Feeds Calculator.

Contains all the unit conversion factors used throughout the application.
"""

import math

# Physical Constants
PI = math.pi

# Unit Conversion Constants
INCH_TO_MM = 25.4
MM_TO_INCH = 1 / INCH_TO_MM
THOU_TO_MM = 0.0254
MM_TO_THOU = 1 / THOU_TO_MM
SFM_TO_SMM = 0.3048
SMM_TO_SFM = 1 / SFM_TO_SMM
HP_TO_KW = 0.745699872
KW_TO_HP = 1 / HP_TO_KW

# Legacy constants for compatibility with main.py
IN_TO_MM = INCH_TO_MM
MM_TO_IN = MM_TO_INCH
FT_TO_M = 0.3048
FT_TO_MM = 304.8
MM_TO_FT = 0.00328084
M_TO_FT = 3.28084