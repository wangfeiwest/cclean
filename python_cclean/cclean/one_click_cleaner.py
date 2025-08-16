"""
One-Click Cleaner for CClean.
Provides intelligent, automated cleaning with backup and safety features.
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

try:
    from .config import CleanupType, CleanupResult, format_bytes
    from .backup_manager import BackupManager
    from .cleaner import CCleaner
    from .logger import CCleanLogger
    from .utils import has_admin_rights, get_free_disk_space
    from .security_checker import SecurityChecker, SecurityLevel
except ImportError:
    # If running as script, use absolute imports
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import CleanupType, CleanupResult, format_bytes
    from backup_manager import BackupManager
    from cleaner import CCleaner
    from logger import CCleanLogger
    from utils import has_admin_rights, get_free_disk_space
    from security_checker import SecurityChecker, SecurityLevel

@dataclass
class OneClickConfig:
    """Configuration for one-click cleaning."""
    enable_backup: bool = True
    backup_large_files: bool = False  # Files > 10MB
    max_backup_size: int = 500 * 1024 * 1024  # 500MB total backup limit
    enable_system_cleanup: bool = True
    enable_browser_cleanup: bool = True
    enable_temp_cleanup: bool = True
    enable_recycle_bin: bool = True
    auto_cleanup_old_backups: bool = True
    backup_retention_days: int = 7
    parallel_processing: bool = True
    max_workers: int = 4
    enable_enhanced_security: bool = True  # New security feature
    security_level_threshold: SecurityLevel = SecurityLevel.MODERATE  # Only process safe/moderate files

class OneClickCleaner:
    """
    Intelligent one-click cleaner with backup and safety features.
    Combines multiple cleanup strategies for maximum effectiveness.
    """
    
    def __init__(self, config: Optional[OneClickConfig] = None, 
                 backup_dir: Optional[str] = None,
                 logger: Optional[CCleanLogger] = None):
        """
        Initialize one-click cleaner.
        
        Args:
            config: Configuration object
            backup_dir: Directory for backups
            logger: Logger instance
        """
        self.config = config if config else OneClickConfig()
        self.logger = logger if logger else CCleanLogger.get_instance()
        
        # Initialize components
        if self.config.enable_backup:
            self.backup_manager = BackupManager(backup_dir, self.logger)
        else:
            self.backup_manager = None
            
        self.core_cleaner = CCleaner(self.logger)
        
        # Configure security settings
        if self.config.enable_enhanced_security:
            self.core_cleaner.set_security_checks(True)
            self.logger.info(f"Enhanced security enabled - threshold: {self.config.security_level_threshold.value}")
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[str, int, int], None]] = None
        self.total_steps = 0
        self.current_step = 0
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """Set progress callback for UI updates."""
        self.progress_callback = callback
    
    def _update_progress(self, message: str, increment: int = 1):
        """Update progress and call callback if set."""
        self.current_step += increment
        if self.progress_callback:
            self.progress_callback(message, self.current_step, self.total_steps)
        
        self.logger.info(f"Progress: {message} ({self.current_step}/{self.total_steps})")
    
    def _run_windows_cleanup_tools(self) -> CleanupResult:
        """Run Windows built-in cleanup tools."""
        result = CleanupResult()
        
        try:
            self._update_progress("运行Windows磁盘清理工具...")
            
            # Method 1: Try cleanmgr with sagerun
            try:
                subprocess.run(['cleanmgr', '/sagerun:1'], 
                             timeout=300, check=False, 
                             capture_output=True)
                result.success = True
                self.logger.info("Windows disk cleanup completed")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Method 2: Try basic cleanmgr
                try:
                    subprocess.run(['cleanmgr', '/d', 'C:'], 
                                 timeout=180, check=False,
                                 capture_output=True)
                    result.success = True
                except Exception:
                    result.success = False
                    result.error_message = "Windows cleanup tools unavailable"
            
        except Exception as e:
            result.success = False
            result.error_message = f"Windows cleanup failed: {e}"
        
        return result
    
    def _run_system_commands(self) -> CleanupResult:
        """Run additional system cleanup commands."""
        result = CleanupResult()
        commands_run = 0
        
        # System cleanup commands (only with admin rights)
        if has_admin_rights():
            cleanup_commands = [
                # Clear DNS cache
                ('ipconfig /flushdns', "清理DNS缓存"),
                
                # Clear event logs (carefully)
                ('wevtutil cl Application', "清理应用程序事件日志"),
                ('wevtutil cl System', "清理系统事件日志"),
                
                # Clear Windows Update cache (if service is stopped)
                ('net stop wuauserv & rd /s /q C:\\Windows\\SoftwareDistribution\\Download & net start wuauserv', 
                 "清理Windows更新缓存"),
            ]
            
            for command, description in cleanup_commands:
                try:
                    self._update_progress(description)
                    subprocess.run(command, shell=True, timeout=60, 
                                 capture_output=True, check=False)
                    commands_run += 1
                    time.sleep(1)  # Brief pause between commands
                except Exception as e:
                    self.logger.warning(f"Command failed: {command} - {e}")
        
        result.success = commands_run > 0
        result.files_deleted = commands_run
        return result
    
    def _intelligent_file_cleanup(self) -> CleanupResult:
        """Perform intelligent file cleanup with backup."""
        total_result = CleanupResult()
        
        # Define cleanup categories with priorities
        cleanup_categories = [
            (CleanupType.TEMP_FILES, "清理临时文件", 3),
            (CleanupType.BROWSER_CACHE, "清理浏览器缓存", 2), 
            (CleanupType.SYSTEM_FILES, "清理系统日志", 1),
        ]
        
        if self.config.parallel_processing:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_category = {}
                
                for cleanup_type, description, priority in cleanup_categories:
                    future = executor.submit(self._cleanup_category_with_backup, 
                                           cleanup_type, description)
                    future_to_category[future] = (cleanup_type, description)
                
                for future in as_completed(future_to_category):
                    cleanup_type, description = future_to_category[future]
                    try:
                        result = future.result()
                        
                        total_result.files_scanned += result.files_scanned
                        total_result.files_deleted += result.files_deleted
                        total_result.bytes_freed += result.bytes_freed
                        
                        if not result.success and result.error_message:
                            if total_result.error_message:
                                total_result.error_message += f"; {result.error_message}"
                            else:
                                total_result.error_message = result.error_message
                        
                        self._update_progress(f"{description}完成")
                        
                    except Exception as e:
                        self.logger.error(f"Category cleanup failed {cleanup_type}: {e}")
        else:
            # Sequential processing
            for cleanup_type, description, priority in cleanup_categories:
                result = self._cleanup_category_with_backup(cleanup_type, description)
                
                total_result.files_scanned += result.files_scanned
                total_result.files_deleted += result.files_deleted
                total_result.bytes_freed += result.bytes_freed
                
                if not result.success and result.error_message:
                    if total_result.error_message:
                        total_result.error_message += f"; {result.error_message}"
                    else:
                        total_result.error_message = result.error_message
                
                self._update_progress(f"{description}完成")
        
        return total_result
    
    def _cleanup_category_with_backup(self, cleanup_type: CleanupType, description: str) -> CleanupResult:
        """Clean up a specific category with backup support."""
        self.logger.info(f"开始{description}...")
        
        # Configure cleaner for this category
        self.core_cleaner.set_dry_run(False)
        self.core_cleaner.set_verbose(False)
        
        # Override the file processing to include backup
        if self.backup_manager:
            original_process_file = self.core_cleaner._process_single_file
            
            def process_file_with_backup(file_path, scan_only=False):
                if scan_only:
                    return original_process_file(file_path, scan_only)
                
                result = CleanupResult()
                result.files_scanned = 1
                result.bytes_freed = file_path.stat().st_size if file_path.exists() else 0
                
                # Use backup manager for safe deletion
                success, error_msg = self.backup_manager.safe_delete_with_backup(
                    file_path, cleanup_type.value
                )
                
                if success:
                    result.files_deleted = 1
                    result.success = True
                else:
                    result.success = False
                    result.error_message = error_msg
                
                return result
            
            # Temporarily replace the method
            self.core_cleaner._process_single_file = process_file_with_backup
        
        # Perform cleanup
        try:
            if cleanup_type == CleanupType.TEMP_FILES:
                result = self.core_cleaner.clean_temp_files()
            elif cleanup_type == CleanupType.BROWSER_CACHE:
                result = self.core_cleaner.clean_browser_cache()
            elif cleanup_type == CleanupType.SYSTEM_FILES:
                result = self.core_cleaner.clean_system_files()
            else:
                result = CleanupResult()
                result.success = False
                result.error_message = "Unknown cleanup type"
        except Exception as e:
            result = CleanupResult()
            result.success = False
            result.error_message = f"Cleanup failed: {e}"
        
        return result
    
    def _cleanup_recycle_bin(self) -> CleanupResult:
        """Clean up recycle bin."""
        self._update_progress("清空回收站...")
        return self.core_cleaner.clean_recycle_bin()
    
    def _perform_backup_maintenance(self):
        """Perform backup maintenance tasks."""
        if not self.backup_manager:
            return
        
        try:
            self._update_progress("维护备份文件...")
            
            # Get backup stats
            stats = self.backup_manager.get_backup_statistics()
            
            # Clean old backups if enabled and backup size is too large
            if (self.config.auto_cleanup_old_backups and 
                stats['total_size'] > self.config.max_backup_size):
                
                cleaned_count, cleaned_size = self.backup_manager.cleanup_old_backups(
                    self.config.backup_retention_days
                )
                
                self.logger.info(f"Cleaned {cleaned_count} old backups, freed {format_bytes(cleaned_size)}")
        
        except Exception as e:
            self.logger.warning(f"Backup maintenance failed: {e}")
    
    def perform_one_click_cleanup(self) -> Dict:
        """
        Perform comprehensive one-click cleanup.
        
        Returns:
            Dictionary with cleanup results and statistics
        """
        start_time = time.time()
        self.current_step = 0
        
        # Calculate total steps
        steps = []
        if self.config.enable_system_cleanup:
            steps.extend(["Windows工具", "系统命令"])
        if self.config.enable_temp_cleanup or self.config.enable_browser_cleanup:
            steps.append("文件清理")
        if self.config.enable_recycle_bin:
            steps.append("回收站")
        if self.backup_manager:
            steps.append("备份维护")
        
        self.total_steps = len(steps)
        
        results = {
            'start_time': start_time,
            'system_info': {
                'admin_rights': has_admin_rights(),
                'free_space_before': get_free_disk_space('C:')
            },
            'cleanup_results': {},
            'total_files_deleted': 0,
            'total_bytes_freed': 0,
            'success': True,
            'errors': []
        }
        
        self.logger.info("=== 开始一键清理 ===")
        
        try:
            # Step 1: Windows built-in cleanup
            if self.config.enable_system_cleanup:
                windows_result = self._run_windows_cleanup_tools()
                results['cleanup_results']['windows_tools'] = windows_result
                
                if not windows_result.success:
                    results['errors'].append(windows_result.error_message)
                
                # System commands
                system_result = self._run_system_commands()
                results['cleanup_results']['system_commands'] = system_result
                results['total_files_deleted'] += system_result.files_deleted
            
            # Step 2: Intelligent file cleanup
            if (self.config.enable_temp_cleanup or 
                self.config.enable_browser_cleanup):
                
                file_result = self._intelligent_file_cleanup()
                results['cleanup_results']['file_cleanup'] = file_result
                results['total_files_deleted'] += file_result.files_deleted
                results['total_bytes_freed'] += file_result.bytes_freed
                
                if not file_result.success and file_result.error_message:
                    results['errors'].append(file_result.error_message)
            
            # Step 3: Recycle bin
            if self.config.enable_recycle_bin:
                recycle_result = self._cleanup_recycle_bin()
                results['cleanup_results']['recycle_bin'] = recycle_result
                results['total_bytes_freed'] += recycle_result.bytes_freed
                
                if not recycle_result.success and recycle_result.error_message:
                    results['errors'].append(recycle_result.error_message)
            
            # Step 4: Backup maintenance
            if self.backup_manager:
                self._perform_backup_maintenance()
        
        except Exception as e:
            self.logger.error(f"One-click cleanup failed: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        # Final statistics
        results['duration'] = time.time() - start_time
        results['system_info']['free_space_after'] = get_free_disk_space('C:')
        results['system_info']['space_gained'] = (
            results['system_info']['free_space_after'] - 
            results['system_info']['free_space_before']
        )
        
        # Backup statistics
        if self.backup_manager:
            results['backup_stats'] = self.backup_manager.get_backup_statistics()
        
        self.logger.info("=== 一键清理完成 ===")
        self.logger.info(f"清理文件: {results['total_files_deleted']}")
        self.logger.info(f"释放空间: {format_bytes(results['total_bytes_freed'])}")
        self.logger.info(f"实际获得: {format_bytes(results['system_info']['space_gained'])}")
        
        return results
    
    def get_cleanup_preview(self) -> Dict:
        """
        Get a preview of what would be cleaned without actually cleaning.
        
        Returns:
            Dictionary with preview information
        """
        preview = {
            'categories': {},
            'total_files': 0,
            'total_size': 0,
            'backup_required': self.config.enable_backup
        }
        
        # Configure cleaner for scanning only
        self.core_cleaner.set_dry_run(True)
        
        try:
            # Scan different categories
            if self.config.enable_temp_cleanup:
                temp_result = self.core_cleaner.scan_temp_files()
                preview['categories']['temp_files'] = {
                    'files': temp_result.files_scanned,
                    'size': temp_result.bytes_freed,
                    'size_formatted': format_bytes(temp_result.bytes_freed)
                }
                preview['total_files'] += temp_result.files_scanned
                preview['total_size'] += temp_result.bytes_freed
            
            if self.config.enable_browser_cleanup:
                browser_result = self.core_cleaner.scan_browser_cache()
                preview['categories']['browser_cache'] = {
                    'files': browser_result.files_scanned,
                    'size': browser_result.bytes_freed,
                    'size_formatted': format_bytes(browser_result.bytes_freed)
                }
                preview['total_files'] += browser_result.files_scanned
                preview['total_size'] += browser_result.bytes_freed
            
            if self.config.enable_recycle_bin:
                recycle_result = self.core_cleaner.scan_recycle_bin()
                preview['categories']['recycle_bin'] = {
                    'files': recycle_result.files_scanned,
                    'size': recycle_result.bytes_freed,
                    'size_formatted': format_bytes(recycle_result.bytes_freed)
                }
                preview['total_files'] += recycle_result.files_scanned
                preview['total_size'] += recycle_result.bytes_freed
        
        except Exception as e:
            self.logger.error(f"Preview scan failed: {e}")
        
        preview['total_size_formatted'] = format_bytes(preview['total_size'])
        
        return preview


if __name__ == "__main__":
    """Example usage of OneClickCleaner."""
    try:
        from .logger import CCleanLogger
    except ImportError:
        from logger import CCleanLogger
    
    # Initialize logger
    logger = CCleanLogger.get_instance()
    logger.start_session()
    
    try:
        # Create cleaner with default configuration
        config = OneClickConfig()
        cleaner = OneClickCleaner(config=config, logger=logger)
        
        # Get preview first
        print("Getting cleanup preview...")
        preview = cleaner.get_cleanup_preview()
        
        print(f"\nPreview Results:")
        print(f"Total files: {preview['total_files']:,}")
        print(f"Total size: {preview['total_size_formatted']}")
        print(f"Backup required: {preview['backup_required']}")
        
        # Ask for user confirmation
        response = input("\nProceed with one-click cleanup? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\nStarting one-click cleanup...")
            results = cleaner.perform_one_click_cleanup()
            
            print(f"\nCleanup Results:")
            print(f"Files deleted: {results['total_files_deleted']:,}")
            print(f"Space freed: {format_bytes(results['total_bytes_freed'])}")
            print(f"Duration: {results['duration']:.2f} seconds")
            print(f"Success: {results['success']}")
            
            if results['errors']:
                print(f"Errors: {'; '.join(results['errors'])}")
        else:
            print("Cleanup cancelled.")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        logger.end_session()