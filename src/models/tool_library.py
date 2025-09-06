"""
Tool Library data model for the Speeds and Feeds Calculator.

Provides data structures and persistence for managing a comprehensive tool library.
"""

import json
import os
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from PySide6 import QtCore
from .project import ProjectManager, Project

# Set decimal precision for tool measurements (high precision for manufacturing)
getcontext().prec = 28

# Exact conversion constants using Decimal for precision
MM_TO_INCH_DECIMAL = Decimal('0.0393700787401574803149606299213')
INCH_TO_MM_DECIMAL = Decimal('25.4')  # Exactly 25.4 by definition


class DecimalJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


@dataclass
class ToolSpecs:
    """Tool specifications data structure with high-precision Decimal measurements."""
    id: str
    manufacturer: str
    series: str
    name: str
    type: str
    diameter_mm: Decimal
    diameter_inch: Decimal
    flutes: int
    length_of_cut_mm: float
    overall_length_mm: float
    shank_diameter_mm: float
    coating: str
    material: str
    manufacturer_speeds: Dict[str, float]
    manufacturer_feeds: Dict[str, float]
    notes: str = ""
    part_number: str = ""
    price: float = 0.0
    url: str = ""
    tags: List[str] = None
    # Unit tracking with high-precision Decimal to avoid rounding errors
    original_unit: str = "mm"  # "mm" or "inch" - the unit this tool was originally created in
    original_diameter: Decimal = Decimal('0.0')  # The original diameter value in the original unit
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        
        # Ensure diameter fields are Decimal objects
        if not isinstance(self.diameter_mm, Decimal):
            self.diameter_mm = Decimal(str(self.diameter_mm))
        if not isinstance(self.diameter_inch, Decimal):
            self.diameter_inch = Decimal(str(self.diameter_inch))
        if not isinstance(self.original_diameter, Decimal):
            self.original_diameter = Decimal(str(self.original_diameter))
    
    @classmethod
    def mm_to_inch(cls, mm_value: Union[Decimal, float, str]) -> Decimal:
        """Convert mm to inches with high precision."""
        return Decimal(str(mm_value)) * MM_TO_INCH_DECIMAL
    
    @classmethod
    def inch_to_mm(cls, inch_value: Union[Decimal, float, str]) -> Decimal:
        """Convert inches to mm with high precision."""
        return Decimal(str(inch_value)) * INCH_TO_MM_DECIMAL
    
    def get_diameter_in_unit(self, unit: str) -> Decimal:
        """Get diameter in specified unit with original precision."""
        if self.original_unit == unit:
            return self.original_diameter
        elif unit == "mm":
            return self.diameter_mm
        else:  # inch
            return self.diameter_inch
    
    def to_dict_serializable(self) -> dict:
        """Convert to dictionary with Decimal values as strings for JSON serialization."""
        # Manually create dict to handle Decimal conversion properly
        data = {
            'id': self.id,
            'manufacturer': self.manufacturer,
            'series': self.series,
            'name': self.name,
            'type': self.type,
            'diameter_mm': str(self.diameter_mm),
            'diameter_inch': str(self.diameter_inch),
            'flutes': self.flutes,
            'length_of_cut_mm': self.length_of_cut_mm,
            'overall_length_mm': self.overall_length_mm,
            'shank_diameter_mm': self.shank_diameter_mm,
            'coating': self.coating,
            'material': self.material,
            'manufacturer_speeds': self.manufacturer_speeds,
            'manufacturer_feeds': self.manufacturer_feeds,
            'notes': self.notes,
            'part_number': self.part_number,
            'price': self.price,
            'url': self.url,
            'tags': self.tags,
            'original_unit': self.original_unit,
            'original_diameter': str(self.original_diameter)
        }
        return data


class ToolLibrary:
    """
    Tool Library manager with persistence and search capabilities.
    
    Provides comprehensive tool management including:
    - Tool CRUD operations
    - Search and filtering
    - Manufacturer presets
    - JSON persistence
    - Integration with Qt settings
    """
    
    def __init__(self, library_file: str = None):
        self.library_file = library_file or self._get_default_library_path()
        self.tools: Dict[str, ToolSpecs] = {}
        self.manufacturers: List[str] = []
        self.tool_types: List[str] = []
        self.coatings: List[str] = []
        self.materials: List[str] = []
        
        # Load existing library
        self.load_library()
        
        # Qt settings for user preferences
        self.settings = QtCore.QSettings("cnc-toolhub", "ToolLibrary")
        
        # Initialize project manager
        self.project_manager = ProjectManager()
        
    def _get_default_library_path(self) -> str:
        """Get default path for tool library file."""
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        return os.path.join(data_dir, "tool_library.json")
    
    def load_library(self) -> bool:
        """Load tool library from JSON file."""
        try:
            if not os.path.exists(self.library_file):
                self._create_default_library()
                return True
                
            with open(self.library_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load metadata
            self.manufacturers = data.get('manufacturers', [])
            self.tool_types = data.get('tool_types', [])
            self.coatings = data.get('coatings', [])
            self.materials = data.get('materials', [])
            
            # Load tools
            self.tools = {}
            tools_data = data.get('tools', {})
            
            for category, manufacturers in tools_data.items():
                for manufacturer, tools in manufacturers.items():
                    for tool_id, tool_data in tools.items():
                        # Add backward compatibility for new unit fields
                        if 'original_unit' not in tool_data:
                            tool_data['original_unit'] = 'mm'  # Default to mm for existing tools
                        if 'original_diameter' not in tool_data:
                            tool_data['original_diameter'] = tool_data.get('diameter_mm', 0.0)
                        
                        # Convert string values to Decimal for diameter fields
                        if isinstance(tool_data.get('diameter_mm'), str):
                            tool_data['diameter_mm'] = Decimal(tool_data['diameter_mm'])
                        elif 'diameter_mm' in tool_data:
                            tool_data['diameter_mm'] = Decimal(str(tool_data['diameter_mm']))
                        
                        if isinstance(tool_data.get('diameter_inch'), str):
                            tool_data['diameter_inch'] = Decimal(tool_data['diameter_inch'])
                        elif 'diameter_inch' in tool_data:
                            tool_data['diameter_inch'] = Decimal(str(tool_data['diameter_inch']))
                        
                        if isinstance(tool_data.get('original_diameter'), str):
                            tool_data['original_diameter'] = Decimal(tool_data['original_diameter'])
                        elif 'original_diameter' in tool_data:
                            tool_data['original_diameter'] = Decimal(str(tool_data['original_diameter']))
                        
                        tool_spec = ToolSpecs(**tool_data)
                        self.tools[tool_spec.id] = tool_spec
            
            return True
            
        except Exception as e:
            print(f"Error loading tool library: {e}")
            self._create_default_library()
            return False
    
    def save_library(self) -> bool:
        """Save tool library to JSON file."""
        try:
            # Create backup before saving (if auto-backup is enabled)
            self._create_backup_if_enabled()
            
            # Organize tools by category and manufacturer
            tools_data = {}
            
            for tool in self.tools.values():
                # Determine category from tool type
                if 'drill' in tool.type:
                    category = 'drills'
                elif 'endmill' in tool.type or 'mill' in tool.type:
                    category = 'endmills'
                else:
                    category = 'other_tools'
                
                if category not in tools_data:
                    tools_data[category] = {}
                
                # Use manufacturer key (lowercase with underscores)
                manufacturer_key = tool.manufacturer.lower().replace(' ', '_').replace('-', '_')
                if manufacturer_key not in tools_data[category]:
                    tools_data[category][manufacturer_key] = {}
                
                tools_data[category][manufacturer_key][tool.id] = tool.to_dict_serializable()
            
            # Create complete data structure
            data = {
                'tools': tools_data,
                'manufacturers': self.manufacturers,
                'tool_types': self.tool_types,
                'coatings': self.coatings,
                'materials': self.materials,
                'metadata': {
                    'version': '1.0',
                    'created': '2024-09-02',
                    'description': 'Tool library for CNC machining applications'
                }
            }
            
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, cls=DecimalJSONEncoder)
            
            return True
            
        except Exception as e:
            print(f"Error saving tool library: {e}")
            return False
    
    def _create_backup_if_enabled(self) -> bool:
        """Create backup if auto-backup is enabled."""
        try:
            # Import here to avoid circular imports
            from ..utils.backup_manager import BackupManager, get_file_type_from_path
            from PySide6 import QtCore
            
            settings = QtCore.QSettings("CNC_ToolHub", "Settings")
            auto_backup_enabled = settings.value("backup/auto_backup", True, type=bool)
            
            if not auto_backup_enabled:
                return True  # Not enabled, no error
            
            # Only create backup if file exists
            if not os.path.exists(self.library_file):
                return True  # No existing file to backup
            
            backup_manager = BackupManager()
            backup_type = get_file_type_from_path(self.library_file)
            
            if backup_type and backup_manager.create_backup(self.library_file, backup_type):
                # Rotate backups based on settings
                max_backups = int(settings.value("backup/max_backups", 10))
                backup_manager.rotate_backups(backup_type, max_backups)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _create_default_library(self):
        """Create default tool library with basic presets."""
        self.manufacturers = ["Harvey Tool", "Mitsubishi", "Kennametal", "Guhring", "Custom"]
        self.tool_types = ["square_endmill", "ball_endmill", "drill", "spot_drill", "custom"]
        self.coatings = ["uncoated", "TiN", "TiAlN", "AlCrN", "DLC", "custom"]
        self.materials = ["HSS", "carbide", "ceramic", "custom"]
        self.tools = {}
    
    def add_tool(self, tool: ToolSpecs) -> bool:
        """Add a new tool to the library."""
        try:
            self.tools[tool.id] = tool
            
            # Update metadata lists if needed
            if tool.manufacturer not in self.manufacturers:
                self.manufacturers.append(tool.manufacturer)
            if tool.type not in self.tool_types:
                self.tool_types.append(tool.type)
            if tool.coating not in self.coatings:
                self.coatings.append(tool.coating)
            if tool.material not in self.materials:
                self.materials.append(tool.material)
            
            return self.save_library()
            
        except Exception as e:
            print(f"Error adding tool: {e}")
            return False
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from the library."""
        try:
            if tool_id in self.tools:
                del self.tools[tool_id]
                return self.save_library()
            return False
            
        except Exception as e:
            print(f"Error removing tool: {e}")
            return False
    
    def update_tool(self, tool: ToolSpecs) -> bool:
        """Update an existing tool in the library."""
        try:
            if tool.id in self.tools:
                self.tools[tool.id] = tool
                return self.save_library()
            return False
            
        except Exception as e:
            print(f"Error updating tool: {e}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[ToolSpecs]:
        """Get a specific tool by ID."""
        return self.tools.get(tool_id)
    
    def get_all_tools(self) -> List[ToolSpecs]:
        """Get all tools as a list."""
        return list(self.tools.values())
    
    def search_tools(self, 
                    query: str = "", 
                    manufacturer: str = "", 
                    tool_type: str = "", 
                    coating: str = "",
                    material: str = "",
                    diameter_min: float = 0.0,
                    diameter_max: float = 1000.0,
                    tags: List[str] = None) -> List[ToolSpecs]:
        """Search tools with multiple filters."""
        results = []
        
        for tool in self.tools.values():
            # Text search in name, part number, and notes
            if query and query.lower() not in (
                tool.name.lower() + " " + 
                tool.part_number.lower() + " " + 
                tool.notes.lower() + " " + 
                " ".join(tool.tags).lower()
            ):
                continue
            
            # Filter by manufacturer
            if manufacturer and tool.manufacturer != manufacturer:
                continue
            
            # Filter by tool type
            if tool_type and tool.type != tool_type:
                continue
            
            # Filter by coating
            if coating and tool.coating != coating:
                continue
            
            # Filter by material
            if material and tool.material != material:
                continue
            
            # Filter by diameter range
            if not (diameter_min <= float(tool.diameter_mm) <= diameter_max):
                continue
            
            # Filter by tags
            if tags:
                if not any(tag in tool.tags for tag in tags):
                    continue
            
            results.append(tool)
        
        # Sort by diameter, then by name
        return sorted(results, key=lambda t: (float(t.diameter_mm), t.name))
    
    def get_tools_by_manufacturer(self, manufacturer: str) -> List[ToolSpecs]:
        """Get all tools from a specific manufacturer."""
        return [tool for tool in self.tools.values() if tool.manufacturer == manufacturer]
    
    def get_tools_by_type(self, tool_type: str) -> List[ToolSpecs]:
        """Get all tools of a specific type."""
        return [tool for tool in self.tools.values() if tool.type == tool_type]
    
    def get_tools_by_diameter_range(self, min_mm: float, max_mm: float) -> List[ToolSpecs]:
        """Get tools within a diameter range."""
        return [tool for tool in self.tools.values() 
                if min_mm <= float(tool.diameter_mm) <= max_mm]
    
    def import_from_csv(self, csv_file: str) -> bool:
        """Import tools from CSV file."""
        # TODO: Implement CSV import functionality
        pass
    
    def export_to_csv(self, csv_file: str, tools: List[ToolSpecs] = None) -> bool:
        """Export tools to CSV file."""
        # TODO: Implement CSV export functionality  
        pass
    
    def get_user_favorites(self) -> List[str]:
        """Get user's favorite tool IDs from settings."""
        favorites = self.settings.value("favorites", [])
        if isinstance(favorites, str):
            return [favorites]  # Handle single favorite
        return favorites or []
    
    def add_to_favorites(self, tool_id: str):
        """Add tool to user favorites."""
        favorites = self.get_user_favorites()
        if tool_id not in favorites:
            favorites.append(tool_id)
            self.settings.setValue("favorites", favorites)
    
    def remove_from_favorites(self, tool_id: str):
        """Remove tool from user favorites."""
        favorites = self.get_user_favorites()
        if tool_id in favorites:
            favorites.remove(tool_id)
            self.settings.setValue("favorites", favorites)
    
    def get_recently_used(self, limit: int = 10) -> List[str]:
        """Get recently used tool IDs."""
        recent = self.settings.value("recent_tools", [])
        if isinstance(recent, str):
            return [recent][:limit]
        return (recent or [])[:limit]
    
    def mark_as_used(self, tool_id: str):
        """Mark tool as recently used."""
        recent = self.get_recently_used()
        if tool_id in recent:
            recent.remove(tool_id)
        recent.insert(0, tool_id)
        self.settings.setValue("recent_tools", recent[:20])  # Keep max 20
    
    # Project-related methods
    
    def get_project_tools(self, project_id: str) -> List[ToolSpecs]:
        """Get all tools assigned to a specific project."""
        project = self.project_manager.get_project(project_id)
        if not project:
            return []
        
        project_tools = []
        for tool_assoc in project.tools:
            tool = self.get_tool(tool_assoc.tool_id)
            if tool:
                project_tools.append(tool)
        
        return project_tools
    
    def get_tools_by_project(self, project_ids: List[str]) -> List[ToolSpecs]:
        """Get tools that belong to any of the specified projects."""
        if not project_ids:
            return []
        
        tool_ids = set()
        for project_id in project_ids:
            project = self.project_manager.get_project(project_id)
            if project:
                tool_ids.update(project.get_tool_ids())
        
        return [self.get_tool(tool_id) for tool_id in tool_ids if self.get_tool(tool_id)]
    
    def get_projects_using_tool(self, tool_id: str) -> List[Project]:
        """Get all projects that use a specific tool."""
        return self.project_manager.get_projects_using_tool(tool_id)
    
    def add_tool_to_project(self, project_id: str, tool_id: str, quantity: int = 1, notes: str = "") -> bool:
        """Add a tool to a project."""
        project = self.project_manager.get_project(project_id)
        if project and self.get_tool(tool_id):
            return project.add_tool(tool_id, quantity, notes) and self.project_manager.save_projects()
        return False
    
    def remove_tool_from_project(self, project_id: str, tool_id: str) -> bool:
        """Remove a tool from a project."""
        project = self.project_manager.get_project(project_id)
        if project:
            return project.remove_tool(tool_id) and self.project_manager.save_projects()
        return False