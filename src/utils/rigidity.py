"""
Machine rigidity utilities for the Speeds and Feeds Calculator.

Contains functions for adjusting machining parameters based on machine rigidity.
"""

from typing import Dict, Any
from ..constants.machining import MACHINE_RIGIDITY_FACTORS, MachineRigidity


def adjust_for_machine_rigidity(parameter_value: float, parameter_type: str, 
                               rigidity_level: str, material_type: str = None) -> float:
    """
    Adjust machining parameters based on machine rigidity level.
    
    Args:
        parameter_value: Original parameter value
        parameter_type: Type of parameter ('chipload', 'doc', 'woc', 'surface_speed')
        rigidity_level: Machine rigidity level (router, diy_medium, vmc_industrial)
        material_type: Optional material type for steel-specific adjustments
        
    Returns:
        Adjusted parameter value
    """
    if rigidity_level not in MACHINE_RIGIDITY_FACTORS:
        return parameter_value
    
    rigidity_props = MACHINE_RIGIDITY_FACTORS[rigidity_level]
    
    if parameter_type == 'chipload':
        return parameter_value * rigidity_props['chipload_factor']
    elif parameter_type == 'doc':
        return parameter_value * rigidity_props['doc_factor']
    elif parameter_type == 'woc':
        return parameter_value * rigidity_props['woc_factor']
    elif parameter_type == 'surface_speed':
        # Special handling for steel on router machines
        if material_type and 'steel' in material_type.lower() and rigidity_level == MachineRigidity.ROUTER:
            # Limit steel cutting speed on routers
            steel_limit = rigidity_props['steel_sfm_limit']
            if parameter_value > steel_limit:
                return steel_limit
        return parameter_value
    
    return parameter_value


def get_machine_rigidity_info(rigidity_level: str) -> Dict[str, Any]:
    """
    Get machine rigidity information and recommended settings.
    
    Args:
        rigidity_level: Machine rigidity level
        
    Returns:
        Dictionary with rigidity information
    """
    return MACHINE_RIGIDITY_FACTORS.get(rigidity_level, MACHINE_RIGIDITY_FACTORS[MachineRigidity.VMC_INDUSTRIAL])