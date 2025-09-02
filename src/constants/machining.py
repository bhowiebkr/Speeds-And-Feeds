"""
Machining constants and machine rigidity definitions for the Speeds and Feeds Calculator.

Contains machining calculation constants, machine types, and rigidity factors.
"""

# Machining Constants
POWER_CALCULATION_FACTOR = 60000  # Factor for converting N*mm/min to kW
DEFAULT_MACHINE_EFFICIENCY = 0.8  # 80% typical machine efficiency
SAFETY_FACTOR_DEFAULT = 1.2  # 20% safety factor for calculations

# Tool Geometry Constants
CARBIDE_RAKE_ANGLE_EFFECT = 0.01  # 1% power change per degree of rake angle
COATED_TOOL_SPEED_INCREASE = 1.3  # 30% speed increase for coated tools
HSS_TO_CARBIDE_SPEED_RATIO = 0.5  # HSS runs at ~50% of carbide speeds

# Machine Efficiency by Drive Type
MACHINE_EFFICIENCIES = {
    'direct_drive': 0.85,
    'belt_drive': 0.78,
    'gear_drive': 0.75,
}

# Physical Constants for Tool Deflection
CARBIDE_YOUNGS_MODULUS = 600e9  # Pa (600 GPa for carbide)
CARBIDE_DENSITY = 14500  # kg/m³
MINIMUM_CHIP_THICKNESS = 0.001  # mm, minimum chip thickness for micro tools

# Micro Machining Thresholds
MICRO_TOOL_THRESHOLD = 3.0  # mm
ULTRA_MICRO_THRESHOLD = 1.0  # mm


class MachineRigidity:
    """Machine rigidity levels with associated adjustment factors."""
    ROUTER = 'router'
    DIY_MEDIUM = 'diy_medium'
    VMC_INDUSTRIAL = 'vmc_industrial'


# Machine Rigidity Properties
MACHINE_RIGIDITY_FACTORS = {
    MachineRigidity.ROUTER: {
        'name': 'Router/Light Duty',
        'description': 'Router-based CNC, gantry machines, light construction',
        'chipload_factor': 0.4,  # 40% of standard chipload
        'doc_factor': 0.5,       # 50% of standard depth of cut
        'woc_factor': 0.6,       # 60% of standard width of cut
        'min_rpm': 8000,         # Routers prefer higher RPM
        'steel_sfm_limit': 60,   # Limited steel cutting capability (SFM)
        'chatter_sensitivity': 0.8,  # High sensitivity to vibration
        'power_efficiency': 0.75     # Lower power transmission efficiency
    },
    MachineRigidity.DIY_MEDIUM: {
        'name': 'DIY/Medium Duty (PrintNC)',
        'description': 'PrintNC, hobby VMC, reinforced gantry machines',
        'chipload_factor': 0.5,  # 50% of standard chipload (very conservative for hobby machines)
        'doc_factor': 0.8,       # 80% of standard depth of cut
        'woc_factor': 0.85,      # 85% of standard width of cut
        'min_rpm': 1000,         # Can handle lower RPM
        'steel_sfm_limit': 85,   # Good steel cutting capability (SFM)
        'chatter_sensitivity': 0.5,  # Medium sensitivity to vibration
        'power_efficiency': 0.85     # Good power transmission efficiency
    },
    MachineRigidity.VMC_INDUSTRIAL: {
        'name': 'VMC/Industrial',
        'description': 'Commercial VMC, Tormach, Haas, industrial machines',
        'chipload_factor': 1.0,  # 100% of standard chipload
        'doc_factor': 1.0,       # 100% of standard depth of cut
        'woc_factor': 1.0,       # 100% of standard width of cut
        'min_rpm': 100,          # Can handle very low RPM
        'steel_sfm_limit': 150,  # Excellent steel cutting capability (SFM)
        'chatter_sensitivity': 0.2,  # Low sensitivity to vibration
        'power_efficiency': 0.9      # High power transmission efficiency
    }
}