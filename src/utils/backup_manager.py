"""
Backup Manager for CNC ToolHub JSON files.

Handles automatic and manual backups of critical data files including
tool library, projects, materials, and other configuration files.
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class BackupManager:
    """Manages backups of JSON data files with rotation and restoration."""
    
    def __init__(self, base_path: str = None):
        """Initialize backup manager with base directory."""
        if base_path is None:
            # Default to backups folder in current directory
            self.base_path = Path.cwd() / "backups"
        else:
            self.base_path = Path(base_path)
        
        # Ensure backup directories exist
        self.backup_dirs = {
            'tool_library': self.base_path / 'tool_library',
            'projects': self.base_path / 'projects',
            'materials': self.base_path / 'materials'
        }
        
        # Create all backup directories
        for backup_dir in self.backup_dirs.values():
            backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, file_path: str, backup_type: str) -> bool:
        """
        Create a timestamped backup of the specified file.
        
        Args:
            file_path: Path to the file to backup
            backup_type: Type of backup ('tool_library', 'projects', 'materials')
        
        Returns:
            True if backup was successful, False otherwise
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                print(f"Source file not found: {file_path}")
                return False
            
            if backup_type not in self.backup_dirs:
                print(f"Unknown backup type: {backup_type}")
                return False
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            backup_filename = f"{backup_type}_{timestamp}.json"
            backup_path = self.backup_dirs[backup_type] / backup_filename
            
            # Copy the file
            shutil.copy2(source_path, backup_path)
            
            print(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def list_backups(self, backup_type: str) -> List[Tuple[str, datetime, int]]:
        """
        List all backups for a given type.
        
        Args:
            backup_type: Type of backup to list
        
        Returns:
            List of tuples (filename, datetime, file_size)
        """
        try:
            if backup_type not in self.backup_dirs:
                return []
            
            backup_dir = self.backup_dirs[backup_type]
            backups = []
            
            for backup_file in backup_dir.glob(f"{backup_type}_*.json"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = backup_file.stem.replace(f"{backup_type}_", "")
                    backup_time = datetime.strptime(timestamp_str, "%Y_%m_%d_%H%M%S")
                    file_size = backup_file.stat().st_size
                    
                    backups.append((backup_file.name, backup_time, file_size))
                except ValueError:
                    # Skip files that don't match expected format
                    continue
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            return backups
            
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def restore_backup(self, backup_filename: str, backup_type: str, target_path: str) -> bool:
        """
        Restore a backup to the target location.
        
        Args:
            backup_filename: Name of the backup file
            backup_type: Type of backup
            target_path: Where to restore the backup
        
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            if backup_type not in self.backup_dirs:
                print(f"Unknown backup type: {backup_type}")
                return False
            
            backup_path = self.backup_dirs[backup_type] / backup_filename
            if not backup_path.exists():
                print(f"Backup file not found: {backup_path}")
                return False
            
            # Create target directory if it doesn't exist
            target_path_obj = Path(target_path)
            target_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy backup to target location
            shutil.copy2(backup_path, target_path)
            
            print(f"Backup restored from {backup_path} to {target_path}")
            return True
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def delete_backup(self, backup_filename: str, backup_type: str) -> bool:
        """
        Delete a specific backup file.
        
        Args:
            backup_filename: Name of the backup file
            backup_type: Type of backup
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if backup_type not in self.backup_dirs:
                print(f"Unknown backup type: {backup_type}")
                return False
            
            backup_path = self.backup_dirs[backup_type] / backup_filename
            if backup_path.exists():
                backup_path.unlink()
                print(f"Backup deleted: {backup_path}")
                return True
            else:
                print(f"Backup file not found: {backup_path}")
                return False
                
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False
    
    def rotate_backups(self, backup_type: str, max_backups: int) -> int:
        """
        Delete old backups to maintain the specified maximum count.
        
        Args:
            backup_type: Type of backup to rotate
            max_backups: Maximum number of backups to keep
        
        Returns:
            Number of backups deleted
        """
        try:
            if backup_type not in self.backup_dirs:
                print(f"Unknown backup type: {backup_type}")
                return 0
            
            backups = self.list_backups(backup_type)
            
            if len(backups) <= max_backups:
                return 0  # No rotation needed
            
            # Delete oldest backups
            deleted_count = 0
            backups_to_delete = backups[max_backups:]  # Keep newest max_backups
            
            for backup_filename, _, _ in backups_to_delete:
                if self.delete_backup(backup_filename, backup_type):
                    deleted_count += 1
            
            print(f"Rotated {deleted_count} old backups for {backup_type}")
            return deleted_count
            
        except Exception as e:
            print(f"Error rotating backups: {e}")
            return 0
    
    def get_backup_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all backup types.
        
        Returns:
            Dictionary with backup statistics for each type
        """
        stats = {}
        
        for backup_type in self.backup_dirs.keys():
            backups = self.list_backups(backup_type)
            
            if backups:
                total_size = sum(size for _, _, size in backups)
                latest_backup = backups[0][1]  # Most recent backup time
                oldest_backup = backups[-1][1]  # Oldest backup time
            else:
                total_size = 0
                latest_backup = None
                oldest_backup = None
            
            stats[backup_type] = {
                'count': len(backups),
                'total_size': total_size,
                'latest_backup': latest_backup,
                'oldest_backup': oldest_backup
            }
        
        return stats
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def cleanup_empty_directories(self):
        """Remove empty backup directories."""
        try:
            for backup_dir in self.backup_dirs.values():
                if backup_dir.exists() and not any(backup_dir.iterdir()):
                    backup_dir.rmdir()
                    print(f"Removed empty directory: {backup_dir}")
        except Exception as e:
            print(f"Error cleaning up directories: {e}")


def get_file_type_from_path(file_path: str) -> Optional[str]:
    """
    Determine backup type from file path.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Backup type string or None if not recognized
    """
    path_obj = Path(file_path)
    filename = path_obj.name.lower()
    
    if 'tool_library' in filename:
        return 'tool_library'
    elif 'projects' in filename:
        return 'projects'
    elif 'materials' in filename:
        return 'materials'
    
    return None