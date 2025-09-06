"""
Project management data models for the Speeds and Feeds Calculator.

Provides data structures for organizing tools into project-based collections
and tracking tool assignments across multiple projects.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum


class ProjectStatus(Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class ProjectToolAssociation:
    """Association between a project and a tool with project-specific metadata."""
    tool_id: str
    quantity_needed: int = 1
    notes: str = ""
    date_added: str = ""
    
    def __post_init__(self):
        if not self.date_added:
            self.date_added = datetime.now().isoformat()


@dataclass
class Setup:
    """Setup data structure for organizing tools by machining setup."""
    id: str
    name: str
    part_id: str
    description: str = ""
    work_offset: str = "G54"  # G54-G59
    fixture_notes: str = ""
    machine_config: str = ""
    operation_type: str = ""  # roughing, finishing, drilling, etc.
    date_created: str = ""
    date_modified: str = ""
    notes: str = ""
    tools: List[ProjectToolAssociation] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        
        if not self.date_created:
            self.date_created = datetime.now().isoformat()
        
        if not self.date_modified:
            self.date_modified = self.date_created
    
    def add_tool(self, tool_id: str, quantity: int = 1, notes: str = "") -> bool:
        """Add a tool to this setup."""
        # Check if tool already exists
        for tool_assoc in self.tools:
            if tool_assoc.tool_id == tool_id:
                # Update existing association
                tool_assoc.quantity_needed = quantity
                tool_assoc.notes = notes
                self.date_modified = datetime.now().isoformat()
                return True
        
        # Add new association
        self.tools.append(ProjectToolAssociation(
            tool_id=tool_id,
            quantity_needed=quantity,
            notes=notes
        ))
        self.date_modified = datetime.now().isoformat()
        return True
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from this setup."""
        for i, tool_assoc in enumerate(self.tools):
            if tool_assoc.tool_id == tool_id:
                self.tools.pop(i)
                self.date_modified = datetime.now().isoformat()
                return True
        return False
    
    def has_tool(self, tool_id: str) -> bool:
        """Check if setup contains a specific tool."""
        return any(tool_assoc.tool_id == tool_id for tool_assoc in self.tools)
    
    def get_tool_ids(self) -> Set[str]:
        """Get set of all tool IDs in this setup."""
        return {tool_assoc.tool_id for tool_assoc in self.tools}
    
    def get_tool_count(self) -> int:
        """Get total number of tools in this setup."""
        return len(self.tools)


@dataclass
class Part:
    """Part data structure for organizing setups within a project."""
    id: str
    name: str
    project_id: str
    description: str = ""
    material: str = ""
    drawing_number: str = ""
    quantity_required: int = 1
    date_created: str = ""
    date_modified: str = ""
    notes: str = ""
    setups: List[Setup] = None
    tools: List[ProjectToolAssociation] = None  # Part-level tools
    
    def __post_init__(self):
        if self.setups is None:
            self.setups = []
        
        if self.tools is None:
            self.tools = []
        
        if not self.date_created:
            self.date_created = datetime.now().isoformat()
        
        if not self.date_modified:
            self.date_modified = self.date_created
    
    def add_setup(self, setup: Setup) -> bool:
        """Add a setup to this part."""
        setup.part_id = self.id
        self.setups.append(setup)
        self.date_modified = datetime.now().isoformat()
        return True
    
    def remove_setup(self, setup_id: str) -> bool:
        """Remove a setup from this part."""
        for i, setup in enumerate(self.setups):
            if setup.id == setup_id:
                self.setups.pop(i)
                self.date_modified = datetime.now().isoformat()
                return True
        return False
    
    def get_setup(self, setup_id: str) -> Optional[Setup]:
        """Get a setup by ID."""
        for setup in self.setups:
            if setup.id == setup_id:
                return setup
        return None
    
    def add_tool(self, tool_id: str, quantity: int = 1, notes: str = "") -> bool:
        """Add a tool to this part (part-level tool)."""
        # Check if tool already exists
        for tool_assoc in self.tools:
            if tool_assoc.tool_id == tool_id:
                # Update existing association
                tool_assoc.quantity_needed = quantity
                tool_assoc.notes = notes
                self.date_modified = datetime.now().isoformat()
                return True
        
        # Add new association
        self.tools.append(ProjectToolAssociation(
            tool_id=tool_id,
            quantity_needed=quantity,
            notes=notes
        ))
        self.date_modified = datetime.now().isoformat()
        return True
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from this part."""
        for i, tool_assoc in enumerate(self.tools):
            if tool_assoc.tool_id == tool_id:
                self.tools.pop(i)
                self.date_modified = datetime.now().isoformat()
                return True
        return False
    
    def get_all_tool_ids(self) -> Set[str]:
        """Get all tool IDs from this part and all its setups."""
        all_tool_ids = set()
        
        # Add part-level tools
        all_tool_ids.update(tool_assoc.tool_id for tool_assoc in self.tools)
        
        # Add setup-level tools
        for setup in self.setups:
            all_tool_ids.update(setup.get_tool_ids())
        
        return all_tool_ids
    
    def get_setup_count(self) -> int:
        """Get total number of setups in this part."""
        return len(self.setups)


@dataclass
class Project:
    """Project data structure for organizing tool collections with hierarchical parts and setups."""
    id: str
    name: str
    description: str = ""
    customer_name: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    date_created: str = ""
    date_modified: str = ""
    notes: str = ""
    parts: List[Part] = None
    tools: List[ProjectToolAssociation] = None  # Project-level tools (shared across parts)
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        
        if self.parts is None:
            self.parts = []
        
        if not self.date_created:
            self.date_created = datetime.now().isoformat()
        
        if not self.date_modified:
            self.date_modified = self.date_created
            
        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = ProjectStatus(self.status)
    
    def add_tool(self, tool_id: str, quantity: int = 1, notes: str = "") -> bool:
        """Add a tool to this project."""
        # Check if tool already exists
        for tool_assoc in self.tools:
            if tool_assoc.tool_id == tool_id:
                # Update existing association
                tool_assoc.quantity_needed = quantity
                tool_assoc.notes = notes
                self.date_modified = datetime.now().isoformat()
                return True
        
        # Add new association
        self.tools.append(ProjectToolAssociation(
            tool_id=tool_id,
            quantity_needed=quantity,
            notes=notes
        ))
        self.date_modified = datetime.now().isoformat()
        return True
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from this project."""
        for i, tool_assoc in enumerate(self.tools):
            if tool_assoc.tool_id == tool_id:
                self.tools.pop(i)
                self.date_modified = datetime.now().isoformat()
                return True
        return False
    
    def has_tool(self, tool_id: str) -> bool:
        """Check if project contains a specific tool."""
        return any(tool_assoc.tool_id == tool_id for tool_assoc in self.tools)
    
    def get_tool_ids(self) -> Set[str]:
        """Get set of all tool IDs in this project (project-level only)."""
        return {tool_assoc.tool_id for tool_assoc in self.tools}
    
    def get_all_tool_ids(self) -> Set[str]:
        """Get all tool IDs from project, parts, and setups."""
        all_tool_ids = set()
        
        # Add project-level tools
        all_tool_ids.update(self.get_tool_ids())
        
        # Add tools from all parts
        for part in self.parts:
            all_tool_ids.update(part.get_all_tool_ids())
        
        return all_tool_ids
    
    def get_tool_count(self) -> int:
        """Get total number of project-level tools."""
        return len(self.tools)
    
    def get_total_tool_count(self) -> int:
        """Get total number of tools across project, parts, and setups."""
        return len(self.get_all_tool_ids())
    
    def add_part(self, part: Part) -> bool:
        """Add a part to this project."""
        part.project_id = self.id
        self.parts.append(part)
        self.date_modified = datetime.now().isoformat()
        return True
    
    def remove_part(self, part_id: str) -> bool:
        """Remove a part from this project."""
        for i, part in enumerate(self.parts):
            if part.id == part_id:
                self.parts.pop(i)
                self.date_modified = datetime.now().isoformat()
                return True
        return False
    
    def get_part(self, part_id: str) -> Optional[Part]:
        """Get a part by ID."""
        for part in self.parts:
            if part.id == part_id:
                return part
        return None
    
    def get_part_count(self) -> int:
        """Get total number of parts in this project."""
        return len(self.parts)
    
    def get_setup_count(self) -> int:
        """Get total number of setups across all parts."""
        return sum(part.get_setup_count() for part in self.parts)


class ProjectManager:
    """
    Project management class with persistence and CRUD operations.
    
    Provides comprehensive project management including:
    - Project CRUD operations
    - Tool assignment management  
    - Project templates and cloning
    - JSON persistence
    """
    
    def __init__(self, projects_file: str = None):
        self.projects_file = projects_file or self._get_default_projects_path()
        self.projects: Dict[str, Project] = {}
        self.load_projects()
    
    def _get_default_projects_path(self) -> str:
        """Get default path for projects file."""
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        return os.path.join(data_dir, "projects.json")
    
    def load_projects(self) -> bool:
        """Load projects from JSON file."""
        try:
            if not os.path.exists(self.projects_file):
                self._create_default_projects()
                return True
            
            with open(self.projects_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.projects = {}
            for project_id, project_data in data.items():
                # Convert tool associations
                if 'tools' in project_data:
                    project_data['tools'] = [
                        ProjectToolAssociation(**tool_data) 
                        for tool_data in project_data['tools']
                    ]
                
                # Convert parts and their setups
                if 'parts' in project_data:
                    parts = []
                    for part_data in project_data['parts']:
                        # Convert part-level tools
                        if 'tools' in part_data:
                            part_data['tools'] = [
                                ProjectToolAssociation(**tool_data)
                                for tool_data in part_data['tools']
                            ]
                        
                        # Convert setups
                        if 'setups' in part_data:
                            setups = []
                            for setup_data in part_data['setups']:
                                # Convert setup-level tools
                                if 'tools' in setup_data:
                                    setup_data['tools'] = [
                                        ProjectToolAssociation(**tool_data)
                                        for tool_data in setup_data['tools']
                                    ]
                                setups.append(Setup(**setup_data))
                            part_data['setups'] = setups
                        
                        parts.append(Part(**part_data))
                    project_data['parts'] = parts
                
                project = Project(**project_data)
                self.projects[project.id] = project
            
            return True
            
        except Exception as e:
            print(f"Error loading projects: {e}")
            self._create_default_projects()
            return False
    
    def save_projects(self) -> bool:
        """Save projects to JSON file."""
        try:
            # Create backup before saving (if auto-backup is enabled)
            self._create_backup_if_enabled()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.projects_file), exist_ok=True)
            
            # Convert to serializable format
            data = {}
            for project_id, project in self.projects.items():
                project_dict = asdict(project)
                # Convert status enum to string
                project_dict['status'] = project.status.value
                data[project_id] = project_dict
            
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving projects: {e}")
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
            if not os.path.exists(self.projects_file):
                return True  # No existing file to backup
            
            backup_manager = BackupManager()
            backup_type = get_file_type_from_path(self.projects_file)
            
            if backup_type and backup_manager.create_backup(self.projects_file, backup_type):
                # Rotate backups based on settings
                max_backups = int(settings.value("backup/max_backups", 10))
                backup_manager.rotate_backups(backup_type, max_backups)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def _create_default_projects(self):
        """Create default empty projects structure."""
        self.projects = {}
        self.save_projects()
    
    def create_project(self, name: str, description: str = "", 
                      customer_name: str = "") -> Optional[Project]:
        """Create a new project."""
        # Generate unique ID
        project_id = f"proj_{len(self.projects) + 1:03d}"
        while project_id in self.projects:
            project_id = f"proj_{len(self.projects) + 2:03d}"
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            customer_name=customer_name
        )
        
        self.projects[project_id] = project
        self.save_projects()
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        return list(self.projects.values())
    
    def get_projects_by_status(self, status: ProjectStatus) -> List[Project]:
        """Get projects filtered by status."""
        return [p for p in self.projects.values() if p.status == status]
    
    def get_active_projects(self) -> List[Project]:
        """Get all active projects."""
        return self.get_projects_by_status(ProjectStatus.ACTIVE)
    
    def update_project(self, project: Project) -> bool:
        """Update an existing project."""
        if project.id in self.projects:
            project.date_modified = datetime.now().isoformat()
            self.projects[project.id] = project
            return self.save_projects()
        return False
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self.projects:
            del self.projects[project_id]
            return self.save_projects()
        return False
    
    def archive_project(self, project_id: str) -> bool:
        """Archive a project (set status to archived)."""
        project = self.get_project(project_id)
        if project:
            project.status = ProjectStatus.ARCHIVED
            return self.update_project(project)
        return False
    
    def clone_project(self, source_project_id: str, new_name: str) -> Optional[Project]:
        """Clone an existing project with a new name."""
        source_project = self.get_project(source_project_id)
        if not source_project:
            return None
        
        # Create new project
        new_project = self.create_project(
            name=new_name,
            description=f"Cloned from: {source_project.name}",
            customer_name=source_project.customer_name
        )
        
        if new_project:
            # Copy all tool associations
            for tool_assoc in source_project.tools:
                new_project.add_tool(
                    tool_id=tool_assoc.tool_id,
                    quantity=tool_assoc.quantity_needed,
                    notes=tool_assoc.notes
                )
            
            self.save_projects()
        
        return new_project
    
    def get_projects_using_tool(self, tool_id: str) -> List[Project]:
        """Get all projects that use a specific tool."""
        return [p for p in self.projects.values() if p.has_tool(tool_id)]
    
    def search_projects(self, query: str) -> List[Project]:
        """Search projects by name, description, or customer."""
        query_lower = query.lower()
        results = []
        
        for project in self.projects.values():
            if (query_lower in project.name.lower() or
                query_lower in project.description.lower() or
                query_lower in project.customer_name.lower()):
                results.append(project)
        
        return results
    
    # Part management methods
    def create_part(self, project_id: str, name: str, **kwargs) -> Optional[Part]:
        """Create a new part in a project."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        part_id = f"part_{len(project.parts) + 1:03d}"
        part = Part(
            id=part_id,
            name=name,
            project_id=project_id,
            **kwargs
        )
        
        project.add_part(part)
        self.save_projects()
        return part
    
    def delete_part(self, project_id: str, part_id: str) -> bool:
        """Delete a part from a project."""
        project = self.get_project(project_id)
        if not project:
            return False
        
        if project.remove_part(part_id):
            self.save_projects()
            return True
        return False
    
    def get_part(self, project_id: str, part_id: str) -> Optional[Part]:
        """Get a specific part."""
        project = self.get_project(project_id)
        if not project:
            return None
        return project.get_part(part_id)
    
    def update_part(self, project_id: str, part: Part) -> bool:
        """Update a part."""
        project = self.get_project(project_id)
        if not project:
            return False
        
        for i, existing_part in enumerate(project.parts):
            if existing_part.id == part.id:
                project.parts[i] = part
                project.date_modified = datetime.now().isoformat()
                self.save_projects()
                return True
        return False
    
    # Setup management methods
    def create_setup(self, project_id: str, part_id: str, name: str, **kwargs) -> Optional[Setup]:
        """Create a new setup in a part."""
        part = self.get_part(project_id, part_id)
        if not part:
            return None
        
        setup_id = f"setup_{len(part.setups) + 1:03d}"
        setup = Setup(
            id=setup_id,
            name=name,
            part_id=part_id,
            **kwargs
        )
        
        part.add_setup(setup)
        self.save_projects()
        return setup
    
    def delete_setup(self, project_id: str, part_id: str, setup_id: str) -> bool:
        """Delete a setup from a part."""
        part = self.get_part(project_id, part_id)
        if not part:
            return False
        
        if part.remove_setup(setup_id):
            self.save_projects()
            return True
        return False
    
    def get_setup(self, project_id: str, part_id: str, setup_id: str) -> Optional[Setup]:
        """Get a specific setup."""
        part = self.get_part(project_id, part_id)
        if not part:
            return None
        return part.get_setup(setup_id)
    
    def update_setup(self, project_id: str, part_id: str, setup: Setup) -> bool:
        """Update a setup."""
        part = self.get_part(project_id, part_id)
        if not part:
            return False
        
        for i, existing_setup in enumerate(part.setups):
            if existing_setup.id == setup.id:
                part.setups[i] = setup
                part.date_modified = datetime.now().isoformat()
                self.save_projects()
                return True
        return False
    
    # Helper methods for tool assignment at different levels
    def add_tool_to_level(self, project_id: str, part_id: str, setup_id: str, tool_id: str, quantity: int = 1, notes: str = "") -> bool:
        """Add tool at the appropriate level (project, part, or setup)."""
        if setup_id:
            # Add to setup level
            setup = self.get_setup(project_id, part_id, setup_id)
            if setup and setup.add_tool(tool_id, quantity, notes):
                self.save_projects()
                return True
        elif part_id:
            # Add to part level
            part = self.get_part(project_id, part_id)
            if part and part.add_tool(tool_id, quantity, notes):
                self.save_projects()
                return True
        else:
            # Add to project level
            project = self.get_project(project_id)
            if project and project.add_tool(tool_id, quantity, notes):
                self.save_projects()
                return True
        
        return False
    
    def remove_tool_from_level(self, project_id: str, part_id: str, setup_id: str, tool_id: str) -> bool:
        """Remove tool from the appropriate level."""
        if setup_id:
            # Remove from setup level
            setup = self.get_setup(project_id, part_id, setup_id)
            if setup and setup.remove_tool(tool_id):
                self.save_projects()
                return True
        elif part_id:
            # Remove from part level
            part = self.get_part(project_id, part_id)
            if part and part.remove_tool(tool_id):
                self.save_projects()
                return True
        else:
            # Remove from project level
            project = self.get_project(project_id)
            if project and project.remove_tool(tool_id):
                self.save_projects()
                return True
        
        return False