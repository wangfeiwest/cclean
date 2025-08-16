"""
Backup and Recovery Manager for CClean.
Implements safe backup and restore mechanisms for deleted files.
"""

import os
import json
import shutil
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import zipfile

from .config import format_bytes
from .logger import CCleanLogger

@dataclass
class BackupEntry:
    """Represents a single backed up file."""
    original_path: str
    backup_path: str
    file_size: int
    file_hash: str
    backup_time: str
    cleanup_type: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BackupEntry':
        return cls(**data)

class BackupManager:
    """
    Manages backup and recovery operations for cleaned files.
    Provides safe deletion with recovery capabilities.
    """
    
    def __init__(self, backup_dir: Optional[str] = None, logger: Optional[CCleanLogger] = None):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups (default: ./backups)
            logger: Logger instance
        """
        self.logger = logger if logger else CCleanLogger.get_instance()
        
        # Setup backup directory
        if backup_dir:
            self.backup_root = Path(backup_dir)
        else:
            self.backup_root = Path.cwd() / "backups"
        
        self.backup_root.mkdir(exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.backup_root / "backup_metadata.json"
        
        # Load existing metadata
        self.metadata: Dict[str, BackupEntry] = self._load_metadata()
        
        self.logger.info(f"Backup manager initialized: {self.backup_root}")
    
    def _load_metadata(self) -> Dict[str, BackupEntry]:
        """Load backup metadata from file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        key: BackupEntry.from_dict(value) 
                        for key, value in data.items()
                    }
        except Exception as e:
            self.logger.warning(f"Failed to load backup metadata: {e}")
        
        return {}
    
    def _save_metadata(self):
        """Save backup metadata to file."""
        try:
            data = {key: entry.to_dict() for key, entry in self.metadata.items()}
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save backup metadata: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _generate_backup_path(self, original_path: str, cleanup_type: str) -> Path:
        """Generate unique backup path for a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_file = Path(original_path)
        
        # Create type-specific directory
        type_dir = self.backup_root / cleanup_type / timestamp
        type_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        backup_name = f"{original_file.stem}_{int(time.time())}{original_file.suffix}"
        return type_dir / backup_name
    
    def backup_file(self, file_path: Path, cleanup_type: str = "manual") -> Tuple[bool, str]:
        """
        Backup a file before deletion.
        
        Args:
            file_path: Path to file to backup
            cleanup_type: Type of cleanup operation
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not file_path.exists():
                return False, "File does not exist"
            
            if not file_path.is_file():
                return False, "Path is not a file"
            
            # Calculate file info
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)
            
            # Skip very large files (>100MB) to save space
            if file_size > 100 * 1024 * 1024:
                self.logger.warning(f"Skipping backup of large file: {file_path} ({format_bytes(file_size)})")
                return True, "Large file skipped"
            
            # Generate backup path
            backup_path = self._generate_backup_path(str(file_path), cleanup_type)
            
            # Copy file to backup location
            shutil.copy2(file_path, backup_path)
            
            # Create backup entry
            entry = BackupEntry(
                original_path=str(file_path.absolute()),
                backup_path=str(backup_path.absolute()),
                file_size=file_size,
                file_hash=file_hash,
                backup_time=datetime.now().isoformat(),
                cleanup_type=cleanup_type
            )
            
            # Store in metadata
            backup_key = f"{cleanup_type}_{int(time.time())}_{file_path.name}"
            self.metadata[backup_key] = entry
            self._save_metadata()
            
            self.logger.debug(f"File backed up: {file_path} -> {backup_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Backup failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def safe_delete_with_backup(self, file_path: Path, cleanup_type: str = "manual") -> Tuple[bool, str]:
        """
        Safely delete file with automatic backup.
        
        Args:
            file_path: Path to file to delete
            cleanup_type: Type of cleanup operation
            
        Returns:
            Tuple of (success, message)
        """
        # First backup the file
        backup_success, backup_msg = self.backup_file(file_path, cleanup_type)
        
        if not backup_success and backup_msg != "Large file skipped":
            return False, f"Backup failed: {backup_msg}"
        
        # Then delete the original file
        try:
            file_path.unlink()
            self.logger.debug(f"File safely deleted: {file_path}")
            return True, ""
        except Exception as e:
            error_msg = f"Delete failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def restore_file(self, backup_key: str) -> Tuple[bool, str]:
        """
        Restore a file from backup.
        
        Args:
            backup_key: Key identifying the backup
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if backup_key not in self.metadata:
                return False, "Backup not found"
            
            entry = self.metadata[backup_key]
            backup_path = Path(entry.backup_path)
            original_path = Path(entry.original_path)
            
            if not backup_path.exists():
                return False, "Backup file not found"
            
            if original_path.exists():
                return False, "Original file already exists"
            
            # Ensure parent directory exists
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Restore file
            shutil.copy2(backup_path, original_path)
            
            # Verify restoration
            if self._calculate_file_hash(original_path) != entry.file_hash:
                original_path.unlink()  # Clean up failed restoration
                return False, "File integrity check failed"
            
            self.logger.info(f"File restored: {backup_path} -> {original_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Restore failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def list_backups(self, cleanup_type: Optional[str] = None) -> List[Dict]:
        """
        List all available backups.
        
        Args:
            cleanup_type: Filter by cleanup type (optional)
            
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for key, entry in self.metadata.items():
            if cleanup_type and entry.cleanup_type != cleanup_type:
                continue
            
            backup_info = {
                'key': key,
                'original_path': entry.original_path,
                'file_size': entry.file_size,
                'file_size_formatted': format_bytes(entry.file_size),
                'backup_time': entry.backup_time,
                'cleanup_type': entry.cleanup_type,
                'backup_exists': Path(entry.backup_path).exists()
            }
            backups.append(backup_info)
        
        # Sort by backup time (newest first)
        backups.sort(key=lambda x: x['backup_time'], reverse=True)
        return backups
    
    def delete_backup(self, backup_key: str) -> Tuple[bool, str]:
        """
        Permanently delete a backup.
        
        Args:
            backup_key: Key identifying the backup
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if backup_key not in self.metadata:
                return False, "Backup not found"
            
            entry = self.metadata[backup_key]
            backup_path = Path(entry.backup_path)
            
            # Delete backup file
            if backup_path.exists():
                backup_path.unlink()
            
            # Remove from metadata
            del self.metadata[backup_key]
            self._save_metadata()
            
            self.logger.info(f"Backup deleted: {backup_key}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Delete backup failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def cleanup_old_backups(self, days_old: int = 7) -> Tuple[int, int]:
        """
        Clean up old backups older than specified days.
        
        Args:
            days_old: Delete backups older than this many days
            
        Returns:
            Tuple of (deleted_count, total_size_freed)
        """
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        deleted_count = 0
        total_size_freed = 0
        keys_to_delete = []
        
        for key, entry in self.metadata.items():
            try:
                backup_time = datetime.fromisoformat(entry.backup_time).timestamp()
                if backup_time < cutoff_time:
                    backup_path = Path(entry.backup_path)
                    if backup_path.exists():
                        total_size_freed += backup_path.stat().st_size
                        backup_path.unlink()
                    
                    keys_to_delete.append(key)
                    deleted_count += 1
            except Exception as e:
                self.logger.warning(f"Error cleaning backup {key}: {e}")
        
        # Remove from metadata
        for key in keys_to_delete:
            del self.metadata[key]
        
        if keys_to_delete:
            self._save_metadata()
        
        self.logger.info(f"Cleaned {deleted_count} old backups, freed {format_bytes(total_size_freed)}")
        return deleted_count, total_size_freed
    
    def get_backup_statistics(self) -> Dict:
        """Get statistics about backups."""
        total_backups = len(self.metadata)
        total_size = 0
        cleanup_types = {}
        
        for entry in self.metadata.values():
            total_size += entry.file_size
            
            if entry.cleanup_type not in cleanup_types:
                cleanup_types[entry.cleanup_type] = {'count': 0, 'size': 0}
            
            cleanup_types[entry.cleanup_type]['count'] += 1
            cleanup_types[entry.cleanup_type]['size'] += entry.file_size
        
        return {
            'total_backups': total_backups,
            'total_size': total_size,
            'total_size_formatted': format_bytes(total_size),
            'backup_location': str(self.backup_root.absolute()),
            'cleanup_types': cleanup_types
        }
    
    def create_backup_archive(self, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create a compressed archive of all backups.
        
        Args:
            output_path: Path for the archive file (optional)
            
        Returns:
            Tuple of (success, archive_path_or_error)
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.backup_root.parent / f"cclean_backups_{timestamp}.zip")
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata file
                zipf.write(self.metadata_file, "backup_metadata.json")
                
                # Add all backup files
                for entry in self.metadata.values():
                    backup_path = Path(entry.backup_path)
                    if backup_path.exists():
                        # Use relative path in archive
                        relative_path = backup_path.relative_to(self.backup_root)
                        zipf.write(backup_path, str(relative_path))
            
            self.logger.info(f"Backup archive created: {output_path}")
            return True, output_path
            
        except Exception as e:
            error_msg = f"Failed to create backup archive: {e}"
            self.logger.error(error_msg)
            return False, error_msg