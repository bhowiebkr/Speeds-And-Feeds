# https://www.garrtool.com/resources/machining-formulas/

import math


def inches_to_mm(inches):
    """Convert inches to millimeters."""
    return inches * 25.4


def mm_to_inches(mm):
    """Convert millimeters to inches."""
    return mm / 25.4


def thou_to_mm(thou):
    """Convert thousandths of an inch to millimeters."""
    return thou * 0.0254


def mm_to_thou(mm):
    """Convert millimeters to thousandths of an inch."""
    return mm / 0.0254


def sfm_to_smm(sfm):
    """Convert Surface Feet per Minute to Surface Meters per Minute."""
    return sfm * 0.3048


def smm_to_sfm(smm):
    """Convert Surface Meters per Minute to Surface Feet per Minute."""
    return smm / 0.3048




class FeedsAndSpeeds:
    """
    CNC machining feeds and speeds calculator.
    
    Calculates optimal cutting parameters including RPM, feed rate, 
    material removal rate (MRR), and required spindle power based on 
    tool geometry, cutting parameters, and material properties.
    """
    
    def __init__(self):
        # Tool parameters
        self.diameter = 0.0          # Tool diameter (mm)
        self.flute_num = 2           # Number of flutes/cutting edges
        
        # Cutting parameters
        self.doc = 0.0               # Depth of cut (mm)
        self.woc = 0.0               # Width of cut (mm)
        self.smm = 0.0               # Surface speed (m/min)
        self.mmpt = 0.0              # Feed per tooth (mm/tooth)
        self.kc = 0.0                # Specific cutting force (N/mm²)
        
        # Calculated results
        self.rpm = 0.0               # Spindle speed (RPM)
        self.feed = 0.0              # Feed rate (mm/min)
        self.mrr = 0.0               # Material removal rate (cm³/min)
        self.kw = 0.0                # Required spindle power (kW)
    
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
    
    def calculate(self):
        """
        Calculate machining parameters using standard formulas.
        
        Formulas used:
        - RPM = (Surface Speed × 1000) / (π × Diameter)
        - Feed Rate = Flutes × Feed per Tooth × RPM
        - MRR = Width of Cut × Depth of Cut × Feed Rate / 1000
        - Power = (MRR × Specific Cutting Force) / 60000
        """
        # Validate inputs first
        validation_errors = self.validate_inputs()
        if validation_errors:
            # Set results to zero if validation fails
            self.rpm = 0.0
            self.feed = 0.0
            self.mrr = 0.0
            self.kw = 0.0
            return validation_errors
        
        # Calculate RPM from surface speed
        if self.diameter > 0 and self.smm > 0:
            self.rpm = (self.smm * 1000) / (self.diameter * math.pi)
        else:
            self.rpm = 0.0
        
        # Calculate feed rate
        if self.rpm > 0 and self.mmpt > 0:
            self.feed = self.flute_num * self.mmpt * self.rpm
        else:
            self.feed = 0.0
        
        # Calculate material removal rate (MRR)
        if self.woc > 0 and self.doc > 0 and self.feed > 0:
            self.mrr = (self.woc * self.doc * self.feed) / 1000  # cm³/min
        else:
            self.mrr = 0.0
        
        # Calculate required spindle power
        if self.kc > 0 and self.mrr > 0:
            # Power (kW) = (MRR (cm³/min) × Kc (N/mm²)) / 60000
            # Factor of 60000 converts from N·mm/min to kW
            self.kw = (self.mrr * self.kc) / 60000
        else:
            self.kw = 0.0
        
        return []  # No errors
    
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

