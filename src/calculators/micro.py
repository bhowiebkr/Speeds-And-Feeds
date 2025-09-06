"""
Micro machining calculator for the Speeds and Feeds Calculator.

Contains the advanced calculation engine for micro machining operations (tools <3mm).
Implements tool deflection modeling using cantilever beam theory and iterative calculations.
"""

import math
from typing import List
from ..constants.units import FT_TO_M, M_TO_FT
from ..constants.machining import CARBIDE_YOUNGS_MODULUS, MINIMUM_CHIP_THICKNESS, ULTRA_MICRO_THRESHOLD
from ..formulas.basic import calculate_rpm, calculate_feed_rate, calculate_mrr_milling
from ..formulas.power import calculate_cutting_power
from ..formulas.chipload import apply_hsm_speed_boost, calculate_chip_thinning_factor
from ..formulas.deflection import calculate_moment_of_inertia
from ..formulas.validation import validate_machining_parameters, get_rigidity_warnings
from ..utils.rigidity import adjust_for_machine_rigidity


class MicroMachiningCalculator:
    """
    Advanced calculation engine for micro machining operations (tools <3mm).
    
    Implements tool deflection modeling using cantilever beam theory,
    iterative cutting force calculations, and physics-based parameters.
    """
    
    def __init__(self):
        self.warnings = []
        self.tool_stickout = 15.0  # mm, default conservative stickout
        self.max_iterations = 10
        self.convergence_tolerance = 0.001  # mm, deflection convergence
    
    def calculate_cutting_force(self, kc: float, chip_area_mm2: float, 
                              diameter_mm: float) -> float:
        """
        Calculate cutting force for micro tools with corrections.
        
        Args:
            kc: Specific cutting force (N/mm²)
            chip_area_mm2: Chip cross-sectional area (mm²)
            diameter_mm: Tool diameter for size effect corrections
            
        Returns:
            Cutting force (N)
        """
        # Basic cutting force
        force = kc * chip_area_mm2
        
        # Size effect correction for micro tools
        # Smaller tools experience higher specific forces due to material strengthening
        if diameter_mm < 1.0:
            size_effect = 1.5  # 50% increase for ultra-micro tools
        elif diameter_mm < 2.0:
            size_effect = 1.3  # 30% increase for small micro tools
        else:
            size_effect = 1.1  # 10% increase for larger micro tools
        
        force *= size_effect
        
        return force
    
    def calculate_tool_deflection(self, force_n: float, diameter_mm: float, 
                                stickout_mm: float = None) -> float:
        """
        Calculate tool deflection using cantilever beam theory.
        
        Args:
            force_n: Applied force (N)
            diameter_mm: Tool diameter (mm)  
            stickout_mm: Tool stickout length (mm)
            
        Returns:
            Tool tip deflection (mm)
        """
        if stickout_mm is None:
            stickout_mm = self.tool_stickout
        
        # Convert to meters for calculation
        diameter_m = diameter_mm / 1000.0
        stickout_m = stickout_mm / 1000.0
        
        # Calculate moment of inertia
        moment_inertia = calculate_moment_of_inertia(diameter_mm) / (1000.0 ** 4)  # Convert to m⁴
        
        # Cantilever beam deflection: δ = F*L³/(3*E*I)
        deflection_m = (force_n * (stickout_m ** 3)) / (3.0 * CARBIDE_YOUNGS_MODULUS * moment_inertia)
        
        # Convert back to mm
        return deflection_m * 1000.0
    
    def calculate_effective_chipload(self, target_chipload: float, deflection_mm: float,
                                   feed_rate: float, rpm: float, flute_count: int) -> float:
        """
        Calculate effective chipload considering tool deflection.
        
        Tool deflection reduces the actual chip thickness by moving the tool
        away from the workpiece during cutting.
        
        Args:
            target_chipload: Intended chipload (mm/tooth)
            deflection_mm: Tool tip deflection (mm)
            feed_rate: Feed rate (mm/min)
            rpm: Spindle speed (RPM)
            flute_count: Number of flutes
            
        Returns:
            Effective chipload after deflection (mm/tooth)
        """
        if rpm <= 0 or flute_count <= 0:
            return 0.0
        
        # Calculate actual chip thickness after deflection
        # Deflection effectively reduces the chip thickness
        effective_chipload = max(target_chipload - deflection_mm, MINIMUM_CHIP_THICKNESS)
        
        return effective_chipload
    
    def calculate_micro_chipload(self, diameter_mm: float, material_type: str, 
                               flute_count: int, rigidity_level: str) -> float:
        """
        Calculate chipload for micro tools using percentage of diameter method.
        
        Args:
            diameter_mm: Tool diameter in mm
            material_type: Material being cut
            flute_count: Number of flutes
            rigidity_level: Machine rigidity level
            
        Returns:
            Micro tool chipload (mm/tooth)
        """
        if diameter_mm < ULTRA_MICRO_THRESHOLD:
            # Ultra-micro tools: fixed minimum to prevent breakage
            base_chipload = 0.005  # ~0.0002"
        else:
            # Micro tools: percentage of diameter
            if material_type and 'aluminum' in material_type.lower():
                percentage = 0.015  # 1.5% of diameter for aluminum
            elif material_type and ('steel' in material_type.lower() or 'stainless' in material_type.lower()):
                percentage = 0.01   # 1% of diameter for harder materials
            else:
                percentage = 0.012  # Default 1.2%
            
            base_chipload = diameter_mm * percentage
        
        # Apply flute multiplier (much more conservative for micro tools)
        if flute_count == 1:
            base_chipload *= 1.1  # Only 10% increase for single flute micro tools
        elif flute_count >= 3:
            base_chipload *= 0.8  # Reduce for multiple flutes
        
        # Apply rigidity adjustments
        adjusted_chipload = adjust_for_machine_rigidity(
            base_chipload, 'chipload', rigidity_level, material_type
        )
        
        return adjusted_chipload
    
    def iterative_calculation(self, diameter: float, flute_num: int, doc: float, 
                            woc: float, smm: float, kc: float, rigidity_level: str,
                            material_type: str, hsm_enabled: bool = False,
                            chip_thinning_enabled: bool = False) -> dict:
        """
        Perform iterative calculation considering tool deflection effects.
        
        The cutting force causes tool deflection, which reduces effective chipload,
        which changes cutting force. Iterate until convergence.
        
        Returns:
            Dictionary with converged values
        """
        # Apply HSM speed boost if enabled
        if hsm_enabled:
            smm = apply_hsm_speed_boost(smm * M_TO_FT, material_type, hsm_enabled) * FT_TO_M
        
        # Initial chipload calculation
        target_chipload = self.calculate_micro_chipload(
            diameter, material_type, flute_num, rigidity_level
        )
        
        # Apply rigidity adjustments to other parameters
        adjusted_doc = adjust_for_machine_rigidity(doc, 'doc', rigidity_level, material_type)
        adjusted_woc = adjust_for_machine_rigidity(woc, 'woc', rigidity_level, material_type) 
        adjusted_smm = adjust_for_machine_rigidity(smm, 'surface_speed', rigidity_level, material_type)
        
        # Apply chip thinning compensation if enabled
        chip_thinning_factor = 1.0
        if chip_thinning_enabled:
            chip_thinning_factor = calculate_chip_thinning_factor(adjusted_woc, diameter)
            target_chipload *= chip_thinning_factor
        
        # Initial calculations
        rpm = calculate_rpm(adjusted_smm, diameter, 'metric') if diameter > 0 and adjusted_smm > 0 else 0.0
        
        # Iterative convergence loop
        current_chipload = target_chipload
        previous_deflection = 0.0
        
        for iteration in range(self.max_iterations):
            # Calculate feed rate with current chipload
            feed_rate = calculate_feed_rate(rpm, flute_num, current_chipload) if rpm > 0 else 0.0
            
            # Calculate chip area (simplified for micro tools)
            chip_area = current_chipload * adjusted_doc  # mm²
            
            # Calculate cutting force
            cutting_force = self.calculate_cutting_force(kc, chip_area, diameter)
            
            # Calculate tool deflection
            deflection = self.calculate_tool_deflection(cutting_force, diameter, self.tool_stickout)
            
            # Check convergence
            if abs(deflection - previous_deflection) < self.convergence_tolerance:
                break
            
            # Calculate new effective chipload
            current_chipload = self.calculate_effective_chipload(
                target_chipload, deflection, feed_rate, rpm, flute_num
            )
            
            previous_deflection = deflection
        
        # Final calculations with converged values
        final_feed_rate = calculate_feed_rate(rpm, flute_num, current_chipload) if rpm > 0 else 0.0
        
        # Material removal rate  
        if adjusted_woc > 0 and adjusted_doc > 0 and final_feed_rate > 0:
            mrr = calculate_mrr_milling(adjusted_doc, adjusted_woc, final_feed_rate)
        else:
            mrr = 0.0
        
        # Power calculation
        if kc > 0 and mrr > 0:
            power_kw = calculate_cutting_power(mrr, kc)
        else:
            power_kw = 0.0
        
        return {
            'rpm': rpm,
            'feed_rate': final_feed_rate,
            'mrr': mrr,
            'power_kw': power_kw,
            'adjusted_mmpt': current_chipload,
            'adjusted_doc': adjusted_doc,
            'adjusted_woc': adjusted_woc,
            'adjusted_smm': adjusted_smm,
            'tool_deflection': deflection,
            'cutting_force': cutting_force,
            'chip_thinning_factor': chip_thinning_factor,
            'iterations': iteration + 1,
            'target_chipload': target_chipload
        }
    
    def calculate_cutting_parameters(self, diameter: float, flute_num: int, doc: float,
                                   woc: float, smm: float, mmpt: float, kc: float,
                                   rigidity_level: str, material_type: str,
                                   tool_stickout: float = 15.0, hsm_enabled: bool = False,
                                   chip_thinning_enabled: bool = False) -> dict:
        """
        Main calculation method for micro machining parameters.
        
        Returns:
            Dictionary with calculated values and warnings
        """
        self.warnings = []
        self.tool_stickout = tool_stickout
        
        # Perform iterative calculation
        results = self.iterative_calculation(
            diameter, flute_num, doc, woc, smm, kc, rigidity_level, material_type, hsm_enabled, chip_thinning_enabled
        )
        
        # Generate micro-specific warnings
        self.warnings.extend(self._generate_micro_warnings(diameter, results, rigidity_level, material_type))
        
        # Add basic parameter warnings
        param_warnings = validate_machining_parameters(
            results['rpm'], results['feed_rate'], doc, woc, diameter
        )
        self.warnings.extend(param_warnings)
        
        # Add rigidity warnings
        rigidity_warnings = get_rigidity_warnings(
            results['rpm'], results['adjusted_smm'] * M_TO_FT, results['adjusted_mmpt'],
            rigidity_level, material_type, diameter
        )
        self.warnings.extend(rigidity_warnings)
        
        results['warnings'] = self.warnings
        return results
    
    def _generate_micro_warnings(self, diameter: float, results: dict, 
                               rigidity_level: str, material_type: str) -> List[str]:
        """Generate warnings specific to micro machining."""
        warnings = []
        
        deflection = results.get('tool_deflection', 0)
        cutting_force = results.get('cutting_force', 0)
        iterations = results.get('iterations', 0)
        
        # Tool deflection warnings
        deflection_percentage = (deflection / diameter) * 100 if diameter > 0 else 0
        if deflection_percentage > 5:
            warnings.append(f"⚠️ High deflection: {deflection:.4f}mm ({deflection_percentage:.1f}% of diameter)")
        elif deflection_percentage > 2:
            warnings.append(f"⚠️ Moderate deflection: {deflection:.4f}mm - monitor surface finish")
        
        # Cutting force warnings
        if cutting_force > 50:
            warnings.append(f"⚠️ High cutting force: {cutting_force:.1f}N - risk of tool breakage")
        
        # Convergence warnings
        if iterations >= self.max_iterations:
            warnings.append("⚠️ Calculation did not fully converge - results may be approximate")
        
        # Ultra-micro specific warnings
        if diameter < ULTRA_MICRO_THRESHOLD:
            warnings.append("🔬 Ultra-Micro Tool (<1mm) - Extreme care required:")
            warnings.append("   • Use minimal stickout length")
            warnings.append("   • Perfect spindle runout essential (<0.0001\")")
            warnings.append("   • Consider high-frequency spindle for better finish")
        
        # Material-specific micro warnings
        if material_type and 'steel' in material_type.lower() and diameter < 2.0:
            warnings.append("⚠️ Micro steel cutting - consider carbide coating for tool life")
        
        return warnings
    
    def set_tool_stickout(self, stickout_mm: float):
        """Set tool stickout length for deflection calculations."""
        self.tool_stickout = max(stickout_mm, 5.0)  # Minimum 5mm stickout