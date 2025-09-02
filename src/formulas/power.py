"""
Power and torque calculations for the Speeds and Feeds Calculator.

Contains formulas for calculating cutting power and spindle torque.
"""

from ..constants.machining import POWER_CALCULATION_FACTOR


def calculate_cutting_power(mrr: float, kc: float, efficiency: float = 1.0) -> float:
    """
    Calculate required cutting power.
    
    Args:
        mrr: Material removal rate (cm³/min)
        kc: Specific cutting force (N/mm²)
        efficiency: Machine efficiency (0.0-1.0). Default 1.0 for theoretical power.
        
    Returns:
        Required cutting power (kW)
    """
    # Basic cutting power (theoretical)
    cutting_power = (mrr * kc) / POWER_CALCULATION_FACTOR
    
    # Account for machine efficiency if specified
    if efficiency < 1.0:
        cutting_power = cutting_power / efficiency
    
    return cutting_power


def calculate_torque(power_kw: float, rpm: float) -> float:
    """
    Calculate torque from power and RPM.
    
    Args:
        power_kw: Power in kilowatts
        rpm: Spindle speed (RPM)
        
    Returns:
        Torque in Newton-meters
    """
    if rpm == 0:
        return 0
    return (power_kw * 9549) / rpm