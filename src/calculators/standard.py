"""
Standard machining calculator for the Speeds and Feeds Calculator.

Contains the calculation engine for standard machining operations (tools ≥3mm).
Uses traditional machining formulas with rigidity adjustments.
"""

from typing import List
from ..constants.units import FT_TO_M, M_TO_FT
from ..formulas.basic import calculate_rpm, calculate_feed_rate, calculate_mrr_milling
from ..formulas.power import calculate_cutting_power
from ..formulas.chipload import apply_hsm_speed_boost, calculate_chip_thinning_factor
from ..formulas.deflection import calculate_tool_deflection, calculate_cutting_force
from ..formulas.validation import validate_machining_parameters, get_rigidity_warnings
from ..utils.rigidity import adjust_for_machine_rigidity


class StandardMachiningCalculator:
    """
    Calculation engine for standard machining operations (tools ≥3mm).
    
    Uses traditional machining formulas with rigidity adjustments.
    Optimized for conventional end mills and cutting operations.
    """
    
    def __init__(self):
        self.warnings = []
    
    def calculate_chipload(self, diameter_mm: float, material_type: str, flute_count: int, 
                          base_chipload: float, rigidity_level: str) -> float:
        """
        Calculate chipload for standard tools using traditional methods.
        
        Args:
            diameter_mm: Tool diameter in mm
            material_type: Material being cut
            flute_count: Number of flutes
            base_chipload: Base chipload from material database
            rigidity_level: Machine rigidity level
            
        Returns:
            Adjusted chipload (mm/tooth)
        """
        # Start with base material chipload
        chipload = base_chipload
        
        # Apply flute count multipliers for standard tools
        if flute_count == 1:
            chipload *= 1.25  # Single flute - higher chipload capability
        elif flute_count == 2:
            chipload *= 1.0   # 2-flute baseline
        elif flute_count >= 3:
            chipload *= 0.85  # Multi-flute - reduced per flute load
        
        # Apply rigidity adjustments
        chipload = adjust_for_machine_rigidity(
            chipload, 'chipload', rigidity_level, material_type
        )
        
        return chipload

    def calculate_cutting_parameters(self, diameter: float, flute_num: int, doc: float, 
                                   woc: float, smm: float, mmpt: float, kc: float,
                                   rigidity_level: str, material_type: str, 
                                   tool_stickout: float = 15.0, hsm_enabled: bool = False,
                                   chip_thinning_enabled: bool = False) -> dict:
        """
        Calculate standard machining parameters with deflection analysis and HSM support.
        
        Returns:
            Dictionary with calculated values and warnings
        """
        self.warnings = []
        
        # Apply HSM speed boost if enabled
        if hsm_enabled:
            smm = apply_hsm_speed_boost(smm * M_TO_FT, material_type, hsm_enabled) * FT_TO_M
        
        # Apply rigidity adjustments to cutting parameters
        adjusted_doc = adjust_for_machine_rigidity(doc, 'doc', rigidity_level, material_type)
        adjusted_woc = adjust_for_machine_rigidity(woc, 'woc', rigidity_level, material_type)
        adjusted_smm = adjust_for_machine_rigidity(smm, 'surface_speed', rigidity_level, material_type)
        
        # Calculate chipload using standard method
        adjusted_mmpt = self.calculate_chipload(
            diameter, material_type, flute_num, mmpt, rigidity_level
        )
        
        # Apply chip thinning compensation if enabled
        chip_thinning_factor = 1.0
        if chip_thinning_enabled:
            chip_thinning_factor = calculate_chip_thinning_factor(adjusted_woc, diameter)
            adjusted_mmpt *= chip_thinning_factor
        
        # Standard RPM calculation
        if diameter > 0 and adjusted_smm > 0:
            rpm = calculate_rpm(adjusted_smm, diameter, 'metric')
        else:
            rpm = 0.0
        
        # Standard feed rate calculation
        if rpm > 0 and adjusted_mmpt > 0:
            feed_rate = calculate_feed_rate(rpm, flute_num, adjusted_mmpt)
        else:
            feed_rate = 0.0
        
        # Material removal rate
        if adjusted_woc > 0 and adjusted_doc > 0 and feed_rate > 0:
            mrr = calculate_mrr_milling(adjusted_doc, adjusted_woc, feed_rate)
        else:
            mrr = 0.0
        
        # Required spindle power
        if kc > 0 and mrr > 0:
            power_kw = calculate_cutting_power(mrr, kc)
        else:
            power_kw = 0.0
        
        # Calculate deflection for all tool sizes now
        cutting_force = calculate_cutting_force(kc, adjusted_doc, adjusted_woc, adjusted_mmpt)
        tool_deflection = calculate_tool_deflection(cutting_force, diameter, tool_stickout)
        
        # Get standard warnings
        param_warnings = validate_machining_parameters(rpm, feed_rate, doc, woc, diameter)
        rigidity_warnings = get_rigidity_warnings(
            rpm, adjusted_smm * M_TO_FT, adjusted_mmpt, rigidity_level, material_type, diameter
        )
        self.warnings = param_warnings + rigidity_warnings
        
        # Add deflection warnings
        deflection_percent = (tool_deflection / diameter) * 100 if diameter > 0 else 0
        if deflection_percent > 5:
            self.warnings.append(f"High deflection: {tool_deflection:.4f}mm ({deflection_percent:.1f}% of diameter)")
        elif deflection_percent > 1:
            self.warnings.append("Monitor surface finish - deflection may affect quality")
        
        return {
            'rpm': rpm,
            'feed_rate': feed_rate,
            'mrr': mrr,
            'power_kw': power_kw,
            'adjusted_mmpt': adjusted_mmpt,
            'adjusted_doc': adjusted_doc,
            'adjusted_woc': adjusted_woc,
            'adjusted_smm': adjusted_smm,
            'tool_deflection': tool_deflection,
            'cutting_force': cutting_force,
            'chip_thinning_factor': chip_thinning_factor,
            'warnings': self.warnings
        }