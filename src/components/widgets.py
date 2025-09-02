from PySide6 import QtWidgets, QtCore, QtGui
from typing import Dict, Optional, Tuple
import sys
import os

# Import the enhanced formulas module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.formulas import MATERIALS, load_materials_database, COATING_MULTIPLIERS


class IntInput(QtWidgets.QLineEdit):
    def __init__(self, val=None):
        super(IntInput, self).__init__(None)
        self.setValidator(QtGui.QIntValidator())

        if val:
            self.setText(str(val))


class DoubleInput(QtWidgets.QLineEdit):
    def __init__(self, val=None):
        super(DoubleInput, self).__init__(None)
        self.setValidator(QtGui.QDoubleValidator())

        if val:
            self.setText(str(val))


class MaterialCombo(QtWidgets.QComboBox):
    """
    Dropdown for material selection with hardness (HB) and K-factor data.
    
    Emits materialSelected signal with (material_key, kc, sfm, smm, chip_load, name) tuple.
    """
    
    materialSelected = QtCore.Signal(str, float, float, float, float, str)  # key, kc, sfm, smm, chip_load, name
    
    def __init__(self, parent=None):
        super(MaterialCombo, self).__init__(parent)
        self.materials_data = {}
        self.setup_materials()
        self.currentTextChanged.connect(self.on_selection_changed)
    
    def setup_materials(self):
        """Load materials from both MATERIALS dict and JSON database."""
        self.clear()
        self.materials_data.clear()
        
        # Add "Select Material" placeholder
        self.addItem("Select Material...")
        self.materials_data[""] = None
        
        # Load from MATERIALS dict (enhanced formulas.py)
        aluminum_items = []
        steel_items = []
        
        for key, material in MATERIALS.items():
            if 'aluminum' in key.lower():
                display_text = f"{material.name} - {material.sfm} SFM, Kc={material.kc}"
                aluminum_items.append((display_text, key, material))
            elif 'steel' in key.lower():
                display_text = f"{material.name} - {material.sfm} SFM, Kc={material.kc}"
                steel_items.append((display_text, key, material))
            else:
                display_text = f"{material.name} - {material.sfm} SFM, Kc={material.kc}"
                self.addItem(display_text)
                self.materials_data[display_text] = (key, material)
        
        # Add aluminum section
        if aluminum_items:
            self.insertSeparator(self.count())
            for display_text, key, material in sorted(aluminum_items):
                self.addItem(f"🔹 {display_text}")
                self.materials_data[f"🔹 {display_text}"] = (key, material)
        
        # Add steel section  
        if steel_items:
            self.insertSeparator(self.count())
            for display_text, key, material in sorted(steel_items):
                self.addItem(f"🔸 {display_text}")
                self.materials_data[f"🔸 {display_text}"] = (key, material)
        
        # Try to load additional materials from JSON database
        json_materials = load_materials_database()
        if json_materials and 'materials' in json_materials:
            self._load_json_materials(json_materials['materials'])
    
    def _load_json_materials(self, materials_db: Dict):
        """Load materials from JSON database."""
        try:
            # Load aluminum variants
            if 'aluminum' in materials_db:
                aluminum_section = materials_db['aluminum']
                if 'variants' in aluminum_section:
                    for variant_key, variant_data in aluminum_section['variants'].items():
                        if variant_key not in ['6061']:  # Skip if already loaded from MATERIALS dict
                            name = variant_data.get('name', f'Aluminum {variant_key}')
                            sfm = variant_data.get('sfm_typical', variant_data.get('sfm_range', [0, 0])[0])
                            kc = variant_data.get('kc_typical', variant_data.get('kc_range', [0, 0])[0])
                            chip_load = variant_data.get('chip_load_typical', 0.1)
                            
                            if sfm > 0 and kc > 0:
                                display_text = f"🔹 {name} - {sfm} SFM, Kc={kc}"
                                self.addItem(display_text)
                                
                                # Create a mock material object
                                from types import SimpleNamespace
                                material = SimpleNamespace()
                                material.name = name
                                material.kc = kc
                                material.sfm = sfm  
                                material.smm = sfm * 0.3048
                                material.chip_load = chip_load
                                
                                self.materials_data[display_text] = (f"aluminum_{variant_key}", material)
            
            # Load steel variants
            if 'steel' in materials_db:
                steel_section = materials_db['steel']
                if 'variants' in steel_section:
                    for variant_key, variant_data in steel_section['variants'].items():
                        if variant_key not in ['1018']:  # Skip if already loaded from MATERIALS dict
                            name = variant_data.get('name', f'Steel {variant_key}')
                            sfm = variant_data.get('sfm_typical', variant_data.get('sfm_range', [0, 0])[0])
                            kc = variant_data.get('kc_typical', variant_data.get('kc_range', [0, 0])[0])
                            chip_load = variant_data.get('chip_load_typical', 0.06)
                            
                            if sfm > 0 and kc > 0:
                                display_text = f"🔸 {name} - {sfm} SFM, Kc={kc}"
                                self.addItem(display_text)
                                
                                # Create a mock material object
                                from types import SimpleNamespace
                                material = SimpleNamespace()
                                material.name = name
                                material.kc = kc
                                material.sfm = sfm
                                material.smm = sfm * 0.3048
                                material.chip_load = chip_load
                                
                                self.materials_data[display_text] = (f"steel_{variant_key}", material)
        
        except Exception as e:
            print(f"Error loading JSON materials: {e}")
    
    def on_selection_changed(self):
        """Handle material selection change."""
        current_text = self.currentText()
        
        if current_text in self.materials_data and self.materials_data[current_text] is not None:
            key, material = self.materials_data[current_text]
            self.materialSelected.emit(
                key, 
                material.kc, 
                material.sfm,
                material.smm,
                material.chip_load, 
                material.name
            )
    
    def get_current_material(self) -> Optional[Tuple[str, object]]:
        """Get the currently selected material data."""
        current_text = self.currentText()
        if current_text in self.materials_data and self.materials_data[current_text] is not None:
            return self.materials_data[current_text]
        return None


class CoatingCombo(QtWidgets.QComboBox):
    """
    Dropdown for tool coating selection.
    
    Emits coatingSelected signal with (coating_key, multiplier) tuple.
    """
    
    coatingSelected = QtCore.Signal(str, float)  # coating_key, multiplier
    
    def __init__(self, parent=None):
        super(CoatingCombo, self).__init__(parent)
        self.setup_coatings()
        self.currentTextChanged.connect(self.on_selection_changed)
    
    def setup_coatings(self):
        """Load coating options from COATING_MULTIPLIERS."""
        self.clear()
        
        coating_names = {
            'uncoated': 'Uncoated HSS/Carbide',
            'tin': 'TiN (Gold) - General Purpose', 
            'ticn': 'TiCN (Blue/Purple) - Hard Materials',
            'tialn': 'TiAlN (Purple/Black) - High Speed',
            'alcrn': 'AlCrN (Dark) - High Performance',
            'diamond': 'Diamond Coated - Non-Ferrous'
        }
        
        for key, multiplier in COATING_MULTIPLIERS.items():
            display_name = coating_names.get(key, key.upper())
            speed_increase = int((multiplier - 1.0) * 100)
            if speed_increase > 0:
                display_text = f"{display_name} (+{speed_increase}% speed)"
            else:
                display_text = display_name
            
            self.addItem(display_text)
            self.setItemData(self.count() - 1, (key, multiplier))
        
        # Set default to uncoated
        self.setCurrentIndex(0)
    
    def on_selection_changed(self):
        """Handle coating selection change."""
        current_index = self.currentIndex()
        if current_index >= 0:
            data = self.itemData(current_index)
            if data:
                key, multiplier = data
                self.coatingSelected.emit(key, multiplier)
    
    def get_current_coating(self) -> Tuple[str, float]:
        """Get the currently selected coating data."""
        current_index = self.currentIndex()
        if current_index >= 0:
            data = self.itemData(current_index)
            if data:
                return data
        return ('uncoated', 1.0)