"""
Settings Widget for CNC ToolHub.

Provides a comprehensive settings interface with backup management
and other application configuration options.
"""

from PySide6 import QtWidgets, QtCore, QtGui
from datetime import datetime
from typing import Optional
import os

from ..utils.backup_manager import BackupManager, get_file_type_from_path


class BackupListWidget(QtWidgets.QListWidget):
    """Custom list widget for displaying backup files with enhanced formatting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        
        # Set custom styling
        self.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
        """)


class BackupSectionWidget(QtWidgets.QGroupBox):
    """Widget for backup management settings and operations."""
    
    backupCreated = QtCore.Signal(str, str)  # backup_type, filename
    backupRestored = QtCore.Signal(str, str)  # backup_type, filename
    
    def __init__(self, parent=None):
        super().__init__("Backup Management", parent)
        self.backup_manager = BackupManager()
        self.settings = QtCore.QSettings("CNC_ToolHub", "Settings")
        self.setup_ui()
        self.load_settings()
        self.refresh_backup_list()
    
    def setup_ui(self):
        """Setup the backup section UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Backup Settings
        settings_group = QtWidgets.QGroupBox("Backup Settings")
        settings_layout = QtWidgets.QFormLayout(settings_group)
        
        # Number of backups to keep
        self.max_backups_spinbox = QtWidgets.QSpinBox()
        self.max_backups_spinbox.setRange(1, 50)
        self.max_backups_spinbox.setValue(10)
        self.max_backups_spinbox.setToolTip("Maximum number of backups to keep for each file type")
        self.max_backups_spinbox.valueChanged.connect(self.save_settings)
        settings_layout.addRow("Max backups to keep:", self.max_backups_spinbox)
        
        # Auto-backup enabled
        self.auto_backup_checkbox = QtWidgets.QCheckBox()
        self.auto_backup_checkbox.setChecked(True)
        self.auto_backup_checkbox.setToolTip("Automatically create backups when files are saved")
        self.auto_backup_checkbox.stateChanged.connect(self.save_settings)
        settings_layout.addRow("Auto-backup on save:", self.auto_backup_checkbox)
        
        # Backup frequency (for future enhancement)
        self.backup_frequency_combo = QtWidgets.QComboBox()
        self.backup_frequency_combo.addItems(["On Save", "Daily", "Weekly"])
        self.backup_frequency_combo.setToolTip("How often to create automatic backups")
        self.backup_frequency_combo.currentTextChanged.connect(self.save_settings)
        settings_layout.addRow("Backup frequency:", self.backup_frequency_combo)
        
        layout.addWidget(settings_group)
        
        # Manual Backup Controls
        manual_group = QtWidgets.QGroupBox("Manual Backup")
        manual_layout = QtWidgets.QHBoxLayout(manual_group)
        
        # File type selection
        self.backup_type_combo = QtWidgets.QComboBox()
        self.backup_type_combo.addItems(["tool_library", "projects", "materials", "tool_presets"])
        manual_layout.addWidget(QtWidgets.QLabel("File type:"))
        manual_layout.addWidget(self.backup_type_combo)
        
        # Create backup button
        self.create_backup_btn = QtWidgets.QPushButton("📁 Create Backup Now")
        self.create_backup_btn.clicked.connect(self.create_manual_backup)
        self.create_backup_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #4CAF50, stop:1 #388E3C);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #66BB6A, stop:1 #4CAF50);
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #388E3C, stop:1 #2E7D32);
            }
        """)
        manual_layout.addWidget(self.create_backup_btn)
        manual_layout.addStretch()
        
        layout.addWidget(manual_group)
        
        # Backup List and Management
        list_group = QtWidgets.QGroupBox("Existing Backups")
        list_layout = QtWidgets.QVBoxLayout(list_group)
        
        # Filter controls
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Show backups for:"))
        
        self.filter_type_combo = QtWidgets.QComboBox()
        self.filter_type_combo.addItems(["All Types", "tool_library", "projects", "materials", "tool_presets"])
        self.filter_type_combo.currentTextChanged.connect(self.refresh_backup_list)
        filter_layout.addWidget(self.filter_type_combo)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("🔄")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setToolTip("Refresh backup list")
        refresh_btn.clicked.connect(self.refresh_backup_list)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        list_layout.addLayout(filter_layout)
        
        # Backup list
        self.backup_list = BackupListWidget()
        self.backup_list.setMaximumHeight(200)
        list_layout.addWidget(self.backup_list)
        
        # Backup actions
        actions_layout = QtWidgets.QHBoxLayout()
        
        self.restore_btn = QtWidgets.QPushButton("↩️ Restore Selected")
        self.restore_btn.clicked.connect(self.restore_selected_backup)
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #42A5F5, stop:1 #2196F3);
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        actions_layout.addWidget(self.restore_btn)
        
        self.delete_btn = QtWidgets.QPushButton("🗑️ Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_backup)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #f44336, stop:1 #d32f2f);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #ff5722, stop:1 #f44336);
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        actions_layout.addWidget(self.delete_btn)
        
        self.cleanup_btn = QtWidgets.QPushButton("🧹 Cleanup Old Backups")
        self.cleanup_btn.clicked.connect(self.cleanup_old_backups)
        self.cleanup_btn.setToolTip("Remove old backups based on retention settings")
        self.cleanup_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #FF9800, stop:1 #F57C00);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 #FFB74D, stop:1 #FF9800);
            }
        """)
        actions_layout.addWidget(self.cleanup_btn)
        
        actions_layout.addStretch()
        list_layout.addLayout(actions_layout)
        
        layout.addWidget(list_group)
        
        # Backup Statistics
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setStyleSheet("color: #888888; font-size: 11px; padding: 8px;")
        layout.addWidget(self.stats_label)
        
        # Connect list selection to button states
        self.backup_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()
    
    def load_settings(self):
        """Load settings from QSettings."""
        self.max_backups_spinbox.setValue(
            int(self.settings.value("backup/max_backups", 10))
        )
        self.auto_backup_checkbox.setChecked(
            self.settings.value("backup/auto_backup", True, type=bool)
        )
        frequency = self.settings.value("backup/frequency", "On Save")
        index = self.backup_frequency_combo.findText(frequency)
        if index >= 0:
            self.backup_frequency_combo.setCurrentIndex(index)
    
    def save_settings(self):
        """Save settings to QSettings."""
        self.settings.setValue("backup/max_backups", self.max_backups_spinbox.value())
        self.settings.setValue("backup/auto_backup", self.auto_backup_checkbox.isChecked())
        self.settings.setValue("backup/frequency", self.backup_frequency_combo.currentText())
        self.settings.sync()
    
    def get_data_file_path(self, backup_type: str) -> Optional[str]:
        """Get the path to the data file for the given backup type."""
        base_path = "src/components"
        
        file_mappings = {
            'tool_library': f"{base_path}/tool_library.json",
            'projects': f"{base_path}/projects.json", 
            'materials': f"{base_path}/materials.json",
            'tool_presets': f"{base_path}/tool_presets.json"
        }
        
        file_path = file_mappings.get(backup_type)
        if file_path and os.path.exists(file_path):
            return file_path
        return None
    
    def create_manual_backup(self):
        """Create a manual backup for the selected file type."""
        backup_type = self.backup_type_combo.currentText()
        file_path = self.get_data_file_path(backup_type)
        
        if not file_path:
            QtWidgets.QMessageBox.warning(
                self, "Backup Failed", 
                f"Could not find {backup_type} file to backup."
            )
            return
        
        if self.backup_manager.create_backup(file_path, backup_type):
            # Rotate backups if needed
            max_backups = self.max_backups_spinbox.value()
            deleted_count = self.backup_manager.rotate_backups(backup_type, max_backups)
            
            message = f"Backup created successfully for {backup_type}!"
            if deleted_count > 0:
                message += f"\n{deleted_count} old backups were removed."
            
            QtWidgets.QMessageBox.information(self, "Backup Created", message)
            self.backupCreated.emit(backup_type, "")
            self.refresh_backup_list()
        else:
            QtWidgets.QMessageBox.critical(
                self, "Backup Failed", 
                f"Failed to create backup for {backup_type}."
            )
    
    def refresh_backup_list(self):
        """Refresh the backup list display."""
        self.backup_list.clear()
        
        filter_type = self.filter_type_combo.currentText()
        
        if filter_type == "All Types":
            backup_types = ["tool_library", "projects", "materials", "tool_presets"]
        else:
            backup_types = [filter_type]
        
        all_backups = []
        
        for backup_type in backup_types:
            backups = self.backup_manager.list_backups(backup_type)
            for filename, backup_time, file_size in backups:
                all_backups.append((backup_type, filename, backup_time, file_size))
        
        # Sort all backups by time (newest first)
        all_backups.sort(key=lambda x: x[2], reverse=True)
        
        for backup_type, filename, backup_time, file_size in all_backups:
            item = QtWidgets.QListWidgetItem()
            
            # Format display text
            time_str = backup_time.strftime("%Y-%m-%d %H:%M:%S")
            size_str = self.backup_manager.format_file_size(file_size)
            
            item.setText(f"📁 {backup_type} - {time_str} ({size_str})")
            item.setData(QtCore.Qt.UserRole, {"type": backup_type, "filename": filename})
            
            # Add tooltip with more details
            item.setToolTip(
                f"Type: {backup_type}\n"
                f"File: {filename}\n"
                f"Date: {time_str}\n"
                f"Size: {size_str}"
            )
            
            self.backup_list.addItem(item)
        
        # Update statistics
        self.update_statistics()
    
    def update_statistics(self):
        """Update backup statistics display."""
        stats = self.backup_manager.get_backup_stats()
        
        total_backups = sum(data['count'] for data in stats.values())
        total_size = sum(data['total_size'] for data in stats.values())
        
        stats_text = f"Total backups: {total_backups} | "
        stats_text += f"Total size: {self.backup_manager.format_file_size(total_size)}"
        
        # Find most recent backup across all types
        latest_times = [data['latest_backup'] for data in stats.values() if data['latest_backup']]
        if latest_times:
            latest_overall = max(latest_times)
            stats_text += f" | Last backup: {latest_overall.strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.stats_label.setText(stats_text)
    
    def update_button_states(self):
        """Update button states based on selection."""
        has_selection = bool(self.backup_list.currentItem())
        self.restore_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def restore_selected_backup(self):
        """Restore the selected backup."""
        current_item = self.backup_list.currentItem()
        if not current_item:
            return
        
        backup_data = current_item.data(QtCore.Qt.UserRole)
        backup_type = backup_data["type"]
        filename = backup_data["filename"]
        
        # Confirm restoration
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Restore",
            f"Are you sure you want to restore this backup?\n\n"
            f"Type: {backup_type}\n"
            f"File: {filename}\n\n"
            f"This will overwrite the current {backup_type} file!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            target_path = self.get_data_file_path(backup_type)
            if not target_path:
                QtWidgets.QMessageBox.warning(
                    self, "Restore Failed",
                    f"Could not determine target path for {backup_type}"
                )
                return
            
            if self.backup_manager.restore_backup(filename, backup_type, target_path):
                QtWidgets.QMessageBox.information(
                    self, "Restore Successful",
                    f"Backup restored successfully!\n\n"
                    f"Please restart the application to load the restored data."
                )
                self.backupRestored.emit(backup_type, filename)
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Restore Failed",
                    f"Failed to restore backup for {backup_type}."
                )
    
    def delete_selected_backup(self):
        """Delete the selected backup."""
        current_item = self.backup_list.currentItem()
        if not current_item:
            return
        
        backup_data = current_item.data(QtCore.Qt.UserRole)
        backup_type = backup_data["type"]
        filename = backup_data["filename"]
        
        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete this backup?\n\n"
            f"Type: {backup_type}\n"
            f"File: {filename}\n\n"
            f"This action cannot be undone!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self.backup_manager.delete_backup(filename, backup_type):
                QtWidgets.QMessageBox.information(
                    self, "Delete Successful",
                    "Backup deleted successfully!"
                )
                self.refresh_backup_list()
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Delete Failed",
                    f"Failed to delete backup {filename}."
                )
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention settings."""
        max_backups = self.max_backups_spinbox.value()
        
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Cleanup",
            f"This will remove old backups, keeping only the newest {max_backups} "
            f"backups for each file type.\n\nAre you sure?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            total_deleted = 0
            for backup_type in ["tool_library", "projects", "materials", "tool_presets"]:
                deleted = self.backup_manager.rotate_backups(backup_type, max_backups)
                total_deleted += deleted
            
            QtWidgets.QMessageBox.information(
                self, "Cleanup Complete",
                f"Cleanup completed!\n{total_deleted} old backups were removed."
            )
            self.refresh_backup_list()


class SettingsWidget(QtWidgets.QWidget):
    """Main settings widget with multiple sections."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings widget UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Title
        title_label = QtWidgets.QLabel("⚙️ Application Settings")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px 0px;
            }
        """)
        layout.addWidget(title_label)
        
        # Backup Section
        self.backup_section = BackupSectionWidget()
        layout.addWidget(self.backup_section)
        
        # Future sections can be added here
        # General Settings Section (placeholder)
        general_group = QtWidgets.QGroupBox("General Settings")
        general_layout = QtWidgets.QFormLayout(general_group)
        
        # Placeholder for future settings
        placeholder_label = QtWidgets.QLabel("Additional settings will be added here in future versions.")
        placeholder_label.setStyleSheet("color: #888888; font-style: italic; padding: 10px;")
        general_layout.addWidget(placeholder_label)
        
        layout.addWidget(general_group)
        
        # Stretch to push everything to top
        layout.addStretch()
    
    def is_auto_backup_enabled(self) -> bool:
        """Check if auto-backup is enabled."""
        return self.backup_section.auto_backup_checkbox.isChecked()
    
    def get_max_backups(self) -> int:
        """Get the maximum number of backups to keep."""
        return self.backup_section.max_backups_spinbox.value()
    
    def create_backup_if_enabled(self, file_path: str) -> bool:
        """Create backup if auto-backup is enabled."""
        if not self.is_auto_backup_enabled():
            return True  # Not an error, just not enabled
        
        backup_type = get_file_type_from_path(file_path)
        if not backup_type:
            return True  # Unknown file type, skip
        
        success = self.backup_section.backup_manager.create_backup(file_path, backup_type)
        if success:
            # Rotate backups
            max_backups = self.get_max_backups()
            self.backup_section.backup_manager.rotate_backups(backup_type, max_backups)
        
        return success