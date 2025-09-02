"""
Base calculator class for the Speeds and Feeds Calculator.

Contains the main FeedsAndSpeeds class that provides a unified interface
for all machining calculations.
"""

from typing import Union, List
from ..constants.materials import MATERIALS
from ..constants.machining import MachineRigidity, MICRO_TOOL_THRESHOLD
from ..formulas.basic import calculate_rpm, calculate_feed_rate
from ..formulas.power import calculate_torque
from ..formulas.chipload import chip_load_rule_of_thumb


class FeedsAndSpeeds:
    """
    CNC machining feeds and speeds calculator using strategy pattern.
    
    Automatically selects between StandardMachiningCalculator and MicroMachiningCalculator
    based on tool diameter. Provides a unified interface for all machining calculations.
    """
    
    def __init__(self):
        # Tool parameters
        self.diameter = 0.0          # Tool diameter (mm)
        self.flute_num = 2           # Number of flutes/cutting edges
        self.tool_stickout = 15.0    # Tool stickout length for deflection calculations (mm)
        
        # Cutting parameters
        self.doc = 0.0               # Depth of cut (mm)
        self.woc = 0.0               # Width of cut (mm)
        self.smm = 0.0               # Surface speed (m/min)
        self.mmpt = 0.0              # Feed per tooth (mm/tooth)
        self.kc = 0.0                # Specific cutting force (N/mm²)
        
        # HSM and chip thinning parameters
        self.hsm_enabled = False     # High speed machining mode
        self.chip_thinning_enabled = False  # Chip thinning compensation
        
        # Machine rigidity parameters
        self.rigidity_level = MachineRigidity.VMC_INDUSTRIAL  # Default to industrial
        self.material_type = None    # Material type for rigidity-aware adjustments
        
        # Calculated results
        self.rpm = 0.0               # Spindle speed (RPM)
        self.feed = 0.0              # Feed rate (mm/min)
        self.mrr = 0.0               # Material removal rate (cm³/min)
        self.kw = 0.0                # Required spindle power (kW)
        
        # Rigidity-adjusted values
        self.adjusted_mmpt = 0.0     # Rigidity-adjusted chip load
        self.adjusted_doc = 0.0      # Rigidity-adjusted depth of cut
        self.adjusted_woc = 0.0      # Rigidity-adjusted width of cut
        self.adjusted_smm = 0.0      # Rigidity-adjusted surface speed
        
        # Micro machining specific results
        self.tool_deflection = 0.0   # Tool deflection (mm)
        self.cutting_force = 0.0     # Cutting force (N)
        self.chip_thinning_factor = 1.0  # Chip thinning compensation factor
        self.is_micro_tool = False   # True if using micro calculator
        
        # Calculator instances will be imported when needed to avoid circular imports
        self._standard_calc = None
        self._micro_calc = None
    
    def validate_inputs(self):
        """Validate input parameters before calculation."""
        errors = []
        
        if not self.diameter or self.diameter <= 0:
            errors.append("Tool diameter must be greater than 0")
        if not self.flute_num or self.flute_num <= 0:
            errors.append("Number of flutes must be greater than 0")
        if self.doc < 0:
            errors.append("Depth of cut cannot be negative")
        if self.woc < 0:
            errors.append("Width of cut cannot be negative")
        if self.smm < 0:
            errors.append("Surface speed cannot be negative")
        if self.mmpt < 0:
            errors.append("Feed per tooth cannot be negative")
        if self.kc < 0:
            errors.append("Specific cutting force cannot be negative")
            
        return errors
    
    def _get_calculator_instances(self):
        """Lazy load calculator instances to avoid circular imports."""
        if self._standard_calc is None:
            from .standard import StandardMachiningCalculator
            self._standard_calc = StandardMachiningCalculator()
        
        if self._micro_calc is None:
            from .micro import MicroMachiningCalculator
            self._micro_calc = MicroMachiningCalculator()
            
        return self._standard_calc, self._micro_calc
    
    def _select_calculator(self):
        """
        Select appropriate calculator based on tool diameter.
        
        Returns:
            Calculator instance (StandardMachiningCalculator or MicroMachiningCalculator)
        """
        standard_calc, micro_calc = self._get_calculator_instances()
        
        if self.diameter < MICRO_TOOL_THRESHOLD:
            self.is_micro_tool = True
            # Set tool stickout for micro calculator
            micro_calc.set_tool_stickout(self.tool_stickout)
            return micro_calc
        else:
            self.is_micro_tool = False
            return standard_calc
    
    def calculate(self):
        """
        Calculate machining parameters using the appropriate calculation engine.
        
        Automatically selects between standard and micro machining calculations
        based on tool diameter (<3mm uses micro calculator).
        """
        # Validate inputs first
        validation_errors = self.validate_inputs()
        if validation_errors:
            # Set results to zero if validation fails
            self._reset_results()
            return validation_errors
        
        # Select appropriate calculator
        calculator = self._select_calculator()
        
        # Perform calculation using selected engine
        results = calculator.calculate_cutting_parameters(
            self.diameter, self.flute_num, self.doc, self.woc,
            self.smm, self.mmpt, self.kc, self.rigidity_level, self.material_type,
            self.tool_stickout, self.hsm_enabled, self.chip_thinning_enabled
        )
        
        # Update instance variables with results
        self.rpm = results.get('rpm', 0.0)
        self.feed = results.get('feed_rate', 0.0)
        self.mrr = results.get('mrr', 0.0)
        self.kw = results.get('power_kw', 0.0)
        
        # Update adjusted values
        self.adjusted_mmpt = results.get('adjusted_mmpt', 0.0)
        self.adjusted_doc = results.get('adjusted_doc', 0.0)
        self.adjusted_woc = results.get('adjusted_woc', 0.0)
        self.adjusted_smm = results.get('adjusted_smm', 0.0)
        
        # Update tool deflection and cutting force (now available for all tools)
        self.tool_deflection = results.get('tool_deflection', 0.0)
        self.cutting_force = results.get('cutting_force', 0.0)
        self.chip_thinning_factor = results.get('chip_thinning_factor', 1.0)
        
        # Return warnings from calculation
        return results.get('warnings', [])
    
    def _reset_results(self):
        """Reset all calculated results to zero."""
        self.rpm = 0.0
        self.feed = 0.0
        self.mrr = 0.0
        self.kw = 0.0
        self.adjusted_mmpt = 0.0
        self.adjusted_doc = 0.0
        self.adjusted_woc = 0.0
        self.adjusted_smm = 0.0
        self.tool_deflection = 0.0
        self.cutting_force = 0.0
        self.chip_thinning_factor = 1.0
    
    def set_tool_stickout(self, stickout_mm: float):
        """
        Set tool stickout length for micro tool deflection calculations.
        
        Args:
            stickout_mm: Tool stickout length in mm
        """
        self.tool_stickout = max(stickout_mm, 5.0)  # Minimum 5mm stickout
        if self._micro_calc:
            self._micro_calc.set_tool_stickout(self.tool_stickout)
    
    def get_results_dict(self):
        """Return calculated results as a dictionary."""
        return {
            'rpm': self.rpm,
            'feed_rate_mm_min': self.feed,
            'feed_rate_in_min': self.feed * 0.0393701,
            'mrr_cm3_min': self.mrr,
            'mrr_in3_min': self.mrr * 0.0610237,
            'power_kw': self.kw,
            'power_hp': self.kw * 1.34102
        }
    
    def print_values(self):
        """Print current input parameters and calculated results."""
        print("=== CNC Feeds and Speeds Calculator ===")
        print("\nTool Parameters:")
        print(f"  Diameter: {self.diameter:.3f} mm")
        print(f"  Flutes: {self.flute_num}")
        
        print("\nCutting Parameters:")
        print(f"  Depth of Cut: {self.doc:.3f} mm")
        print(f"  Width of Cut: {self.woc:.3f} mm")
        print(f"  Surface Speed: {self.smm:.1f} m/min")
        print(f"  Feed per Tooth: {self.mmpt:.4f} mm/tooth")
        print(f"  Specific Cutting Force: {self.kc:.0f} N/mm²")
        
        print("\nCalculated Results:")
        print(f"  RPM: {self.rpm:.0f}")
        print(f"  Feed Rate: {self.feed:.2f} mm/min ({self.feed * 0.0393701:.2f} in/min)")
        print(f"  MRR: {self.mrr:.2f} cm³/min ({self.mrr * 0.0610237:.3f} in³/min)")
        print(f"  Power: {self.kw:.2f} kW ({self.kw * 1.34102:.2f} HP)")
    
    def copy_from(self, other):
        """Copy all parameters from another FeedsAndSpeeds instance."""
        if isinstance(other, FeedsAndSpeeds):
            self.diameter = other.diameter
            self.flute_num = other.flute_num
            self.doc = other.doc
            self.woc = other.woc
            self.smm = other.smm
            self.mmpt = other.mmpt
            self.kc = other.kc
    
    def set_material_properties(self, material_key: str):
        """
        Set material properties from the MATERIALS database.
        
        Args:
            material_key: Key from MATERIALS dict (e.g., 'aluminum_6061', 'steel_1018')
        """
        if material_key in MATERIALS:
            material = MATERIALS[material_key]
            self.kc = material.kc
            self.smm = material.smm
            self.mmpt = material.chip_load
            return material.name
        else:
            available = list(MATERIALS.keys())
            raise ValueError(f"Material '{material_key}' not found. Available: {available}")
    
    def get_suggested_chip_load(self, material_factor: float = 1.0) -> float:
        """
        Get suggested chip load using rule of thumb.
        
        Args:
            material_factor: Material multiplier (aluminum ~2.0, steel ~1.0, stainless ~0.5)
            
        Returns:
            Suggested chip load (mm/tooth)
        """
        return chip_load_rule_of_thumb(self.diameter, material_factor)
    
    def calculate_torque(self) -> float:
        """
        Calculate spindle torque based on current power and RPM.
        
        Returns:
            Torque in Newton-meters
        """
        return calculate_torque(self.kw, self.rpm)