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
class Project:
    """Project data structure for organizing tool collections."""
    id: str
    name: str
    description: str = ""
    customer_name: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
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
        """Get set of all tool IDs in this project."""
        return {tool_assoc.tool_id for tool_assoc in self.tools}
    
    def get_tool_count(self) -> int:
        """Get total number of tools in this project."""
        return len(self.tools)


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
        components_dir = os.path.join(os.path.dirname(__file__), "..", "components")
        return os.path.join(components_dir, "projects.json")
    
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