"""
Parameter validation and warnings for the Speeds and Feeds Calculator.

Contains functions for validating machining parameters and generating warnings.
"""

import json
import os
from typing import List, Optional, Dict
from ..constants.machining import MACHINE_RIGIDITY_FACTORS, MachineRigidity
from .chipload import is_micro_tool


def validate_machining_parameters(rpm: float, feed_rate: float, depth_of_cut: float,
                                width_of_cut: float, tool_diameter: float) -> List[str]:
    """
    Validate machining parameters for basic sanity checks.
    
    Args:
        rpm: Spindle speed (RPM)
        feed_rate: Feed rate (mm/min)
        depth_of_cut: Depth of cut (mm)
        width_of_cut: Width of cut (mm)
        tool_diameter: Tool diameter (mm)
        
    Returns:
        List of warning messages (empty if all OK)
    """
    warnings = []
    
    if rpm <= 0:
        warnings.append("RPM must be greater than 0")
    elif rpm > 50000:
        warnings.append("RPM extremely high (>50,000) - check calculation")
    
    if feed_rate <= 0:
        warnings.append("Feed rate must be greater than 0")
    elif feed_rate > 10000:
        warnings.append("Feed rate extremely high (>10,000 mm/min)")
    
    if depth_of_cut < 0:
        warnings.append("Depth of cut cannot be negative")
    elif depth_of_cut > tool_diameter:
        warnings.append("Depth of cut greater than tool diameter - very aggressive")
    
    if width_of_cut < 0:
        warnings.append("Width of cut cannot be negative")
    elif width_of_cut > tool_diameter:
        warnings.append("Width of cut greater than tool diameter")
    
    # Check for extremely light cuts
    if depth_of_cut > 0 and width_of_cut > 0:
        if depth_of_cut < 0.01 and width_of_cut < 0.01:
            warnings.append("Very light cut - may cause rubbing instead of cutting")
    
    return warnings


def get_rigidity_warnings(rpm: float, surface_speed: float, chipload: float,
                         rigidity_level: str, material_type: str = None, 
                         tool_diameter: float = None) -> List[str]:
    """
    Generate warnings based on machine rigidity and cutting parameters.
    
    Args:
        rpm: Calculated RPM
        surface_speed: Surface speed (SFM)
        chipload: Chip load (mm/tooth)
        rigidity_level: Machine rigidity level
        material_type: Material being cut
        tool_diameter: Tool diameter in mm (for micro tool warnings)
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    if rigidity_level not in MACHINE_RIGIDITY_FACTORS:
        return warnings
    
    rigidity_props = MACHINE_RIGIDITY_FACTORS[rigidity_level]
    
    # Check minimum RPM for machine type
    if rpm < rigidity_props['min_rpm']:
        if rigidity_level == MachineRigidity.ROUTER:
            warnings.append(f"RPM too low for router spindle (min {rigidity_props['min_rpm']} recommended)")
        else:
            warnings.append(f"RPM below recommended minimum for this machine type ({rigidity_props['min_rpm']})")
    
    # Steel cutting warnings for lighter machines
    if material_type and 'steel' in material_type.lower():
        if rigidity_level == MachineRigidity.ROUTER:
            warnings.append("Router machines may struggle with steel - consider aluminum or brass alternatives")
            if surface_speed < 80:
                warnings.append("Low surface speed for steel on router - expect poor surface finish")
        elif rigidity_level == MachineRigidity.DIY_MEDIUM:
            if surface_speed > rigidity_props['steel_sfm_limit']:
                warnings.append("Steel cutting at high speed on DIY machine - watch for excessive wear")
    
    # Chatter sensitivity warnings
    if rigidity_level in [MachineRigidity.ROUTER, MachineRigidity.DIY_MEDIUM]:
        if chipload > 0.2:  # High chipload threshold (mm)
            warnings.append("High chipload may cause chatter on this machine type - reduce if vibration occurs")
    
    # Conservative chipload warnings for hobby machines
    chipload_inches = chipload * 0.0393701  # Convert mm to inches
    if rigidity_level in [MachineRigidity.ROUTER, MachineRigidity.DIY_MEDIUM]:
        if chipload_inches > 0.004:  # 0.004" threshold
            warnings.append(f"Chipload {chipload_inches:.4f}\" is aggressive for hobby machines - consider reducing to <0.003\"")
        elif chipload_inches > 0.003:  # 0.003" caution threshold
            warnings.append(f"Chipload {chipload_inches:.4f}\" is moderately aggressive - watch for tool deflection")
    
    # Micro tool specific warnings
    if tool_diameter and is_micro_tool(tool_diameter):
        warnings.append(f"🔍 Micro Tool Mode ({tool_diameter:.1f}mm) - Special considerations apply:")
        warnings.append("   • Use stub-length tools for maximum rigidity")
        warnings.append("   • Check spindle runout (<0.0003\" critical)")
        warnings.append("   • Reduce DOC to 25% of diameter maximum")
        
        if tool_diameter < 1.5:
            warnings.append("   • Consider air/mist cooling for chip evacuation")
        
        if rigidity_level in [MachineRigidity.ROUTER, MachineRigidity.DIY_MEDIUM]:
            warnings.append("   • Monitor for tool deflection - reduce feed if poor finish")
            
        if material_type and 'aluminum' in material_type.lower():
            warnings.append("   • Ensure adequate coolant to prevent chip welding")
    
    return warnings


def load_materials_database(json_path: str = None) -> Dict:
    """
    Load materials database from JSON file.
    
    Args:
        json_path: Path to materials.json file. If None, uses default location.
        
    Returns:
        Dictionary containing materials database
    """
    if json_path is None:
        # Default path relative to this module
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, 'components', 'materials.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Materials database not found at {json_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error parsing materials database at {json_path}")
        return {}


def get_material_property(material_key: str, property_name: str, 
                         materials_db: Dict = None) -> Optional[float]:
    """
    Get a specific property for a material from the database.
    
    Args:
        material_key: Material key (e.g., 'aluminum.6061')
        property_name: Property name (e.g., 'kc_typical', 'sfm_typical')
        materials_db: Materials database (if None, loads default)
        
    Returns:
        Property value or None if not found
    """
    if materials_db is None:
        materials_db = load_materials_database()
    
    try:
        # Navigate the nested material structure
        keys = material_key.split('.')
        current = materials_db['materials']
        
        for key in keys:
            current = current[key]
            if 'variants' in current:
                current = current['variants']
        
        return current.get(property_name)
        
    except (KeyError, TypeError):
        return None