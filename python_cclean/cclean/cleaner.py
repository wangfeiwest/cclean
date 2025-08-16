"""
Core cleanup engine for CClean Python version.
Handles scanning and cleaning operations for different file categories.
"""

import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from .config import CleanupType, CleanupResult, get_all_cleanup_paths, format_bytes
from .utils import (
    find_files, find_files_fast, get_file_size, safe_delete_file, safe_delete_directory,
    empty_recycle_bin, get_recycle_bin_size, is_file_in_use,
    cleanup_empty_directories, path_exists, is_safe_to_delete,
    batch_check_paths, get_large_files_first, prioritize_cleanup_paths, get_file_priority_score,
    get_development_cache_paths, get_development_priority_score, is_safe_development_file,
    get_system_optimization_priority_score, is_dangerous_system_path, get_optimization_mode_paths,
    get_system_health_status, _path_matches_category
)
from .logger import CCleanLogger
from .security_checker import SecurityChecker, SecurityLevel
from .progress import EnhancedProgressDisplay, SimpleProgressCallback

class CCleaner:
    """
    Core cleanup engine that handles scanning and cleaning operations.
    """
    
    def __init__(self, logger: Optional[CCleanLogger] = None):
        """
        Initialize the cleaner.
        
        Args:
            logger: Optional logger instance, creates new one if not provided
        """
        self.logger = logger if logger else CCleanLogger.get_instance()
        self.dry_run = False
        self.verbose = False
        self.progress_callback: Optional[Callable[[str, int, int], None]] = None
        self._stop_requested = False
        self._lock = threading.Lock()
        
        # Initialize security checker
        self.security_checker = SecurityChecker(self.logger)
        self.enable_security_checks = True
        
        # Initialize enhanced progress display (enabled by default)
        self.progress_display = EnhancedProgressDisplay()
        self.use_enhanced_progress = True  # Default to enabled with safety protections
        
        # Track failed deletions for user feedback
        self.failed_deletions = []
    
    def set_dry_run(self, enabled: bool):
        """Enable or disable dry run mode."""
        self.dry_run = enabled
        if enabled:
            self.logger.info("Dry run mode enabled - no files will be deleted")
    
    def set_verbose(self, enabled: bool):
        """Enable or disable verbose logging."""
        self.verbose = enabled
    
    def set_security_checks(self, enabled: bool):
        """Enable or disable enhanced security checks."""
        self.enable_security_checks = enabled
        if enabled:
            self.logger.info("Enhanced security checks enabled")
        else:
            self.logger.info("Enhanced security checks disabled")
    
    def set_progress_callback(self, callback: Optional[Callable[[str, int, int], None]]):
        """
        Set progress callback function.
        
        Args:
            callback: Function that receives (message, current, total) parameters
        """
        self.progress_callback = callback
    
    def set_enhanced_progress(self, enabled: bool):
        """Enable or disable enhanced progress display."""
        self.use_enhanced_progress = enabled
        if enabled and not self.progress_callback:
            # Set up default enhanced progress callback
            self.progress_callback = SimpleProgressCallback(self.progress_display)
    
    def stop(self):
        """Request the cleaner to stop current operation."""
        self._stop_requested = True
        self.logger.info("Stop requested - will finish current operations and exit")
    
    def _track_failed_deletion(self, file_path: Path, error_msg: str):
        """Track a failed file deletion for user feedback."""
        self.failed_deletions.append({
            'path': str(file_path),
            'error': error_msg,
            'time': time.time()
        })
        
        # Limit the number of tracked failures to avoid memory issues
        if len(self.failed_deletions) > 100:
            self.failed_deletions = self.failed_deletions[-50:]  # Keep only last 50
    
    def get_failed_deletions_summary(self) -> Dict[str, int]:
        """Get a summary of failed deletions by error type."""
        summary = {}
        for failure in self.failed_deletions:
            error_type = failure['error'].split(':')[0]  # Get error type
            summary[error_type] = summary.get(error_type, 0) + 1
        return summary
    
    def clear_failed_deletions(self):
        """Clear the failed deletions list."""
        self.failed_deletions = []
    
    def _update_progress(self, message: str, current: int, total: int):
        """Update progress through callback and logging."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        
        if self.verbose:
            self.logger.log_progress(message, current, total)
    
    def scan_temp_files(self) -> CleanupResult:
        """Scan temporary files and calculate potential space savings."""
        self.logger.info("Starting optimized temporary files scan...")
        return self._process_paths_optimized(CleanupType.TEMP_FILES, scan_only=True)
    
    def clean_temp_files(self) -> CleanupResult:
        """Clean temporary files."""
        self.logger.info("Starting optimized temporary files cleanup...")
        return self._process_paths_optimized(CleanupType.TEMP_FILES, scan_only=False)
    
    def scan_browser_cache(self) -> CleanupResult:
        """Scan browser cache files and calculate potential space savings."""
        self.logger.info("Starting optimized browser cache scan...")
        return self._process_paths_optimized(CleanupType.BROWSER_CACHE, scan_only=True)
    
    def clean_browser_cache(self) -> CleanupResult:
        """Clean browser cache files."""
        self.logger.info("Starting optimized browser cache cleanup...")
        return self._process_paths_optimized(CleanupType.BROWSER_CACHE, scan_only=False)
    
    def scan_system_files(self) -> CleanupResult:
        """Scan system files and calculate potential space savings."""
        self.logger.info("Starting optimized system files scan...")
        return self._process_paths_optimized(CleanupType.SYSTEM_FILES, scan_only=True)
    
    def clean_system_files(self) -> CleanupResult:
        """Clean system files."""
        self.logger.info("Starting optimized system files cleanup...")
        return self._process_paths_optimized(CleanupType.SYSTEM_FILES, scan_only=False)
    
    def scan_recycle_bin(self) -> CleanupResult:
        """Scan recycle bin and calculate potential space savings."""
        self.logger.info("Scanning recycle bin...")
        
        result = CleanupResult()
        try:
            recycle_size = get_recycle_bin_size()
            result.files_scanned = 1 if recycle_size > 0 else 0
            result.bytes_freed = recycle_size
            result.success = True
            
            self.logger.info(f"Recycle bin contains {format_bytes(recycle_size)} of files")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Failed to scan recycle bin: {e}"
            self.logger.error(result.error_message)
        
        return result
    
    def clean_recycle_bin(self) -> CleanupResult:
        """Empty the recycle bin."""
        self.logger.info("Emptying recycle bin...")
        
        result = CleanupResult()
        try:
            # Get size before cleaning
            recycle_size = get_recycle_bin_size()
            
            if recycle_size == 0:
                self.logger.info("Recycle bin is already empty")
                result.success = True
                return result
            
            self._update_progress("Emptying recycle bin...", 0, 1)
            
            success, error_msg = empty_recycle_bin(self.dry_run)
            
            if success:
                result.files_scanned = 1
                result.files_deleted = 1 if not self.dry_run else 0
                result.bytes_freed = recycle_size
                result.success = True
                
                action = "Would empty" if self.dry_run else "Emptied"
                self.logger.info(f"{action} recycle bin - {format_bytes(recycle_size)} freed")
            else:
                result.success = False
                result.error_message = error_msg
                self.logger.error(f"Failed to empty recycle bin: {error_msg}")
            
            self._update_progress("Recycle bin cleanup completed", 1, 1)
            
        except Exception as e:
            result.success = False
            result.error_message = f"Unexpected error: {e}"
            self.logger.error(result.error_message)
        
        return result

    def scan_development_files(self) -> CleanupResult:
        """Scan development tool cache files and calculate potential space savings."""
        self.logger.info("Starting optimized development files scan...")
        return self._process_development_paths(scan_only=True)

    def clean_development_files(self) -> CleanupResult:
        """Clean development tool cache files."""
        self.logger.info("Starting optimized development files cleanup...")
        return self._process_development_paths(scan_only=False)

    def scan_media_files(self) -> CleanupResult:
        """Scan media and download temp files and calculate potential space savings."""
        self.logger.info("Starting media files scan...")
        return self._process_paths(CleanupType.MEDIA_FILES, scan_only=True)

    def clean_media_files(self) -> CleanupResult:
        """Clean media and download temp files."""
        self.logger.info("Starting media files cleanup...")
        return self._process_paths(CleanupType.MEDIA_FILES, scan_only=False)

    def scan_gaming_files(self) -> CleanupResult:
        """Scan gaming platform cache files and calculate potential space savings."""
        self.logger.info("Starting gaming files scan...")
        return self._process_paths(CleanupType.GAMING_FILES, scan_only=True)

    def clean_gaming_files(self) -> CleanupResult:
        """Clean gaming platform cache files."""
        self.logger.info("Starting gaming files cleanup...")
        return self._process_paths(CleanupType.GAMING_FILES, scan_only=False)

    def scan_system_optimization(self) -> CleanupResult:
        """Scan system optimization files and calculate potential space savings."""
        self.logger.info("Starting enhanced system optimization scan...")
        return self._process_system_optimization_enhanced(scan_only=True)

    def clean_system_optimization(self) -> CleanupResult:
        """Clean system optimization files with enhanced algorithms."""
        self.logger.info("Starting enhanced system optimization cleanup...")
        return self._process_system_optimization_enhanced(scan_only=False)
    
    def perform_full_scan(self) -> CleanupResult:
        """Perform a complete system scan of all categories."""
        self.logger.info("Starting full system scan...")
        
        total_result = CleanupResult()
        scan_results = {}
        
        # Scan all categories
        categories = [
            (CleanupType.TEMP_FILES, self.scan_temp_files),
            (CleanupType.BROWSER_CACHE, self.scan_browser_cache),
            (CleanupType.SYSTEM_FILES, self.scan_system_files),
            (CleanupType.DEVELOPMENT_FILES, self.scan_development_files),
            (CleanupType.MEDIA_FILES, self.scan_media_files),
            (CleanupType.GAMING_FILES, self.scan_gaming_files),
            (CleanupType.SYSTEM_OPTIMIZATION, self.scan_system_optimization),
            (CleanupType.RECYCLE_BIN, self.scan_recycle_bin)
        ]
        
        for i, (category, scan_func) in enumerate(categories):
            if self._stop_requested:
                break
                
            self._update_progress(f"Scanning {category.value.replace('_', ' ')}...", i, len(categories))
            
            result = scan_func()
            scan_results[category] = result
            
            # Aggregate results
            total_result.files_scanned += result.files_scanned
            total_result.bytes_freed += result.bytes_freed
            
            if not result.success:
                if total_result.error_message:
                    total_result.error_message += f"; {result.error_message}"
                else:
                    total_result.error_message = result.error_message
                total_result.success = False
        
        self._update_progress("Full scan completed", len(categories), len(categories))
        
        # Log summary
        self.logger.info(f"Full scan completed: {total_result.files_scanned:,} files found, "
                        f"{format_bytes(total_result.bytes_freed)} can be freed")
        
        return total_result
    
    def perform_full_cleanup(self) -> CleanupResult:
        """Perform a complete system cleanup of all categories."""
        self.logger.info("Starting full system cleanup...")
        
        total_result = CleanupResult()
        cleanup_results = {}
        
        # Clean all categories
        categories = [
            (CleanupType.TEMP_FILES, self.clean_temp_files),
            (CleanupType.BROWSER_CACHE, self.clean_browser_cache),
            (CleanupType.SYSTEM_FILES, self.clean_system_files),
            (CleanupType.DEVELOPMENT_FILES, self.clean_development_files),
            (CleanupType.MEDIA_FILES, self.clean_media_files),
            (CleanupType.GAMING_FILES, self.clean_gaming_files),
            (CleanupType.SYSTEM_OPTIMIZATION, self.clean_system_optimization),
            (CleanupType.RECYCLE_BIN, self.clean_recycle_bin)
        ]
        
        for i, (category, clean_func) in enumerate(categories):
            if self._stop_requested:
                break
                
            self._update_progress(f"Cleaning {category.value.replace('_', ' ')}...", i, len(categories))
            
            result = clean_func()
            cleanup_results[category] = result
            
            # Aggregate results
            total_result.files_scanned += result.files_scanned
            total_result.files_deleted += result.files_deleted
            total_result.bytes_freed += result.bytes_freed
            
            if not result.success:
                if total_result.error_message:
                    total_result.error_message += f"; {result.error_message}"
                else:
                    total_result.error_message = result.error_message
                total_result.success = False
        
        self._update_progress("Full cleanup completed", len(categories), len(categories))
        
        # Log summary
        self.logger.info(f"Full cleanup completed: {total_result.files_deleted:,}/{total_result.files_scanned:,} "
                        f"files processed, {format_bytes(total_result.bytes_freed)} freed")
        
        # Write summary report
        self.logger.write_summary_report(cleanup_results)
        
        return total_result
    
    def _process_paths_optimized(self, cleanup_type: CleanupType, scan_only: bool = True) -> CleanupResult:
        """
        优化的路径处理方法，提高系统文件清理性能。
        
        Args:
            cleanup_type: Type of cleanup to perform
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult with operation results
        """
        paths = get_all_cleanup_paths(cleanup_type)
        if not paths:
            return CleanupResult(success=False, error_message="No paths defined for cleanup type")
        
        # 预先过滤存在的路径，避免重复检查
        existing_paths = batch_check_paths(paths)
        if not existing_paths:
            return CleanupResult(success=True)
        
        # 按优先级排序路径
        prioritized_paths = prioritize_cleanup_paths(existing_paths)
        
        total_result = CleanupResult()
        operation_name = f"{'Scanning' if scan_only else 'Cleaning'} {cleanup_type.value.replace('_', ' ').title()}"
        
        # 提高并发数和优化批次大小
        max_workers = min(16, len(prioritized_paths), os.cpu_count() * 2)
        batch_size = 200  # 增大批次
        
        # 启动进度显示
        if self.use_enhanced_progress:
            self.progress_display.start_operation(operation_name, len(prioritized_paths))
        
        try:
            # 并行处理所有路径
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有路径处理任务
                future_to_path = {
                    executor.submit(self._process_single_path_fast, path, scan_only): path 
                    for path in prioritized_paths
                }
                
                processed_paths = 0
                
                # 收集结果，设置超时
                for future in as_completed(future_to_path, timeout=300):  # 5分钟总超时
                    if self._stop_requested:
                        break
                    
                    path = future_to_path[future]
                    try:
                        path_result = future.result(timeout=30)  # 单个路径30秒超时
                        
                        # 聚合结果
                        total_result.files_scanned += path_result.files_scanned
                        total_result.files_deleted += path_result.files_deleted
                        total_result.bytes_freed += path_result.bytes_freed
                        
                        if not path_result.success and path_result.error_message:
                            if total_result.error_message:
                                total_result.error_message += f"; {path_result.error_message}"
                            else:
                                total_result.error_message = path_result.error_message
                            total_result.success = False
                        
                        processed_paths += 1
                        
                        # 更新进度
                        if self.use_enhanced_progress:
                            self.progress_display.update_progress(processed_paths, len(prioritized_paths))
                            
                    except TimeoutError:
                        self.logger.warning(f"Path processing timed out: {path}")
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing path {path}: {e}")
        
        finally:
            if self.use_enhanced_progress:
                success_msg = f"{total_result.files_scanned:,} files processed"
                if total_result.bytes_freed > 0:
                    success_msg += f", {format_bytes(total_result.bytes_freed)} found"
                self.progress_display.finish_operation(True, success_msg)
        
        # 记录结果
        if scan_only:
            self.logger.log_scan_result(cleanup_type, total_result)
        else:
            self.logger.log_cleanup_result(cleanup_type, total_result)
        
        return total_result

    def _process_paths(self, cleanup_type: CleanupType, scan_only: bool = True) -> CleanupResult:
        """
        Process paths for a specific cleanup type with enhanced progress display.
        
        Args:
            cleanup_type: Type of cleanup to perform
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult with operation results
        """
        paths = get_all_cleanup_paths(cleanup_type)
        if not paths:
            return CleanupResult(success=False, error_message="No paths defined for cleanup type")
        
        total_result = CleanupResult()
        operation_name = f"{'Scanning' if scan_only else 'Cleaning'} {cleanup_type.value.replace('_', ' ').title()}"
        
        # Start enhanced progress display
        if self.use_enhanced_progress:
            self.progress_display.start_operation(operation_name, len(paths))
        
        # Use progress bar if available and enhanced progress is disabled
        progress_bar = None
        if HAS_TQDM and not self.verbose and not self.use_enhanced_progress:
            progress_bar = tqdm(
                total=len(paths),
                desc=operation_name,
                unit="path"
            )
        
        try:
            # Quick estimation of total files without blocking
            if self.use_enhanced_progress:
                self.progress_display.start_operation(operation_name, len(paths))
                # Skip file counting to avoid blocking - let progress update dynamically
            
            # Process paths
            for i, path in enumerate(paths):
                if self._stop_requested:
                    break
                
                # Update progress
                if progress_bar:
                    progress_bar.update(1)
                elif not self.use_enhanced_progress:
                    self._update_progress(f"Processing path {i+1}/{len(paths)}: {path}", i+1, len(paths))
                else:
                    # Enhanced progress is updated in _process_single_path
                    pass
                
                # Process single path
                path_result = self._process_single_path(path, scan_only)
                
                # Aggregate results
                total_result.files_scanned += path_result.files_scanned
                total_result.files_deleted += path_result.files_deleted
                total_result.bytes_freed += path_result.bytes_freed
                
                if not path_result.success and path_result.error_message:
                    if total_result.error_message:
                        total_result.error_message += f"; {path_result.error_message}"
                    else:
                        total_result.error_message = path_result.error_message
                    total_result.success = False
        
        finally:
            if progress_bar:
                progress_bar.close()
            elif self.use_enhanced_progress:
                success_msg = f"{total_result.files_scanned:,} files processed"
                if total_result.bytes_freed > 0:
                    success_msg += f", {format_bytes(total_result.bytes_freed)} found"
                self.progress_display.finish_operation(True, success_msg)
        
        # Log results
        if scan_only:
            self.logger.log_scan_result(cleanup_type, total_result)
        else:
            self.logger.log_cleanup_result(cleanup_type, total_result)
        
        return total_result
    
    def _process_development_paths(self, scan_only: bool = True) -> CleanupResult:
        """
        开发工具专用的优化路径处理方法。
        
        Args:
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult with operation results
        """
        base_paths = get_all_cleanup_paths(CleanupType.DEVELOPMENT_FILES)
        if not base_paths:
            return CleanupResult(success=False, error_message="No development paths defined")
        
        # 智能扫描开发项目并获取动态路径
        self.logger.info("智能扫描开发项目...")
        all_paths = get_development_cache_paths(base_paths)
        
        # 预过滤存在的路径
        existing_paths = batch_check_paths(all_paths)
        if not existing_paths:
            return CleanupResult(success=True)
        
        # 按开发工具优先级排序
        prioritized_paths = prioritize_cleanup_paths(existing_paths)
        
        total_result = CleanupResult()
        operation_name = f"{'Scanning' if scan_only else 'Cleaning'} Development Files"
        
        # 开发工具优化：更高并发数
        max_workers = min(20, len(prioritized_paths), os.cpu_count() * 4)
        
        if self.use_enhanced_progress:
            self.progress_display.start_operation(operation_name, len(prioritized_paths))
        
        try:
            # 并行处理所有开发路径
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_path = {
                    executor.submit(self._process_single_development_path, path, scan_only): path 
                    for path in prioritized_paths
                }
                
                processed_paths = 0
                
                # 收集结果
                for future in as_completed(future_to_path, timeout=600):  # 10分钟超时
                    if self._stop_requested:
                        break
                    
                    path = future_to_path[future]
                    try:
                        path_result = future.result(timeout=60)  # 单个路径1分钟超时
                        
                        total_result.files_scanned += path_result.files_scanned
                        total_result.files_deleted += path_result.files_deleted
                        total_result.bytes_freed += path_result.bytes_freed
                        
                        if not path_result.success and path_result.error_message:
                            if total_result.error_message:
                                total_result.error_message += f"; {path_result.error_message}"
                            else:
                                total_result.error_message = path_result.error_message
                            total_result.success = False
                        
                        processed_paths += 1
                        
                        if self.use_enhanced_progress:
                            self.progress_display.update_progress(processed_paths, len(prioritized_paths))
                            
                    except TimeoutError:
                        self.logger.warning(f"Development path processing timed out: {path}")
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing development path {path}: {e}")
        
        finally:
            if self.use_enhanced_progress:
                success_msg = f"{total_result.files_scanned:,} development files processed"
                if total_result.bytes_freed > 0:
                    success_msg += f", {format_bytes(total_result.bytes_freed)} found"
                self.progress_display.finish_operation(True, success_msg)
        
        # 记录结果
        if scan_only:
            self.logger.log_scan_result(CleanupType.DEVELOPMENT_FILES, total_result)
        else:
            self.logger.log_cleanup_result(CleanupType.DEVELOPMENT_FILES, total_result)
        
        return total_result

    def _process_single_development_path(self, path: str, scan_only: bool = True) -> CleanupResult:
        """
        处理单个开发工具路径的优化方法。
        
        Args:
            path: Path to process
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult for this path
        """
        result = CleanupResult()
        
        try:
            if not path_exists(path):
                return result
            
            # 使用开发工具优化的文件查找
            max_files_per_path = 50000  # 开发工具可能有大量文件
            files = list(find_files_fast(path, max_files=max_files_per_path, max_depth=6))
            
            if not files:
                return result
            
            # 开发工具专用批处理：更大批次和更高并发
            batch_size = 500
            max_workers = min(16, len(files), os.cpu_count() * 4)
            
            file_batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_batch = {
                    executor.submit(self._process_development_file_batch, batch, scan_only): batch 
                    for batch in file_batches
                }
                
                for future in as_completed(future_to_batch, timeout=120):  # 2分钟超时
                    if self._stop_requested:
                        break
                    
                    try:
                        batch_result = future.result(timeout=60)
                        
                        result.files_scanned += batch_result.files_scanned
                        result.files_deleted += batch_result.files_deleted
                        result.bytes_freed += batch_result.bytes_freed
                        
                        if not batch_result.success and batch_result.error_message:
                            if result.error_message:
                                result.error_message += f"; {batch_result.error_message}"
                            else:
                                result.error_message = batch_result.error_message
                            result.success = False
                            
                    except TimeoutError:
                        self.logger.warning(f"Development batch processing timed out for path: {path}")
                        
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing development path {path}: {e}"
            self.logger.error(result.error_message)
        
        return result

    def _process_development_file_batch(self, file_paths: list, scan_only: bool = True) -> CleanupResult:
        """
        开发工具专用的文件批处理方法。
        
        Args:
            file_paths: List of file paths to process
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult for the entire batch
        """
        result = CleanupResult()
        
        # 预处理：使用开发工具专用优先级算法
        valid_files = []
        
        for file_path in file_paths:
            try:
                # 开发工具安全检查
                if not is_safe_development_file(file_path):
                    continue
                
                size = get_file_size(file_path)
                if size > 0:
                    priority_score = get_development_priority_score(file_path)
                    valid_files.append((priority_score, file_path, size))
            except (OSError, PermissionError):
                continue
        
        if not valid_files:
            return result
        
        # 按开发工具优先级排序
        valid_files.sort(reverse=True)
        
        processed_count = 0
        for priority_score, file_path, file_size in valid_files:
            if self._stop_requested:
                break
            
            try:
                result.files_scanned += 1
                result.bytes_freed += file_size
                
                if not scan_only:
                    success, error_msg = safe_delete_file(file_path, self.dry_run)
                    if success:
                        result.files_deleted += 1
                        if self.verbose:
                            self.logger.log_file_operation("deleted", str(file_path), True)
                    else:
                        self._track_failed_deletion(file_path, error_msg)
                        if self.verbose:
                            self.logger.debug(f"Failed to delete development file: {file_path} ({error_msg})")
                
                processed_count += 1
                
                # 减少进度更新频率（开发文件通常很多）
                if processed_count % 100 == 0 and self.progress_callback:
                    progress_msg = f"Processing development files... ({result.files_scanned} processed)"
                    self.progress_callback(progress_msg, processed_count, len(valid_files))
                    
            except Exception as e:
                if self.verbose:
                    self.logger.error(f"Error processing development file {file_path}: {e}")
        
        return result

    def _process_single_path_fast(self, path: str, scan_only: bool = True) -> CleanupResult:
        """
        优化的单路径处理方法，使用快速扫描算法。
        
        Args:
            path: Path to process
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult for this path
        """
        result = CleanupResult()
        
        try:
            if not path_exists(path):
                return result
            
            # 使用优化的文件查找算法
            max_files_per_path = 20000  # 增加限制
            
            # 对于系统文件，优先处理大文件以提高效率
            if "System" in path or "Windows" in path:
                files = list(get_large_files_first(path, min_size=1024*100))  # 100KB以上的文件
                if len(files) < 100:  # 如果大文件不多，再扫描所有文件
                    additional_files = list(find_files_fast(path, max_files=max_files_per_path-len(files), max_depth=3))
                    files.extend(additional_files)
            else:
                files = list(find_files_fast(path, max_files=max_files_per_path, max_depth=4))
            
            if not files:
                return result
            
            # 增大批次和线程数
            batch_size = 300
            max_workers = min(12, len(files), os.cpu_count() * 3)
            
            # 将文件分批处理
            file_batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有批次
                future_to_batch = {
                    executor.submit(self._process_file_batch_fast, batch, scan_only): batch 
                    for batch in file_batches
                }
                
                # 收集结果
                for future in as_completed(future_to_batch, timeout=60):  # 1分钟超时
                    if self._stop_requested:
                        break
                    
                    try:
                        batch_result = future.result(timeout=30)
                        
                        result.files_scanned += batch_result.files_scanned
                        result.files_deleted += batch_result.files_deleted
                        result.bytes_freed += batch_result.bytes_freed
                        
                        if not batch_result.success and batch_result.error_message:
                            if result.error_message:
                                result.error_message += f"; {batch_result.error_message}"
                            else:
                                result.error_message = batch_result.error_message
                            result.success = False
                            
                    except TimeoutError:
                        self.logger.warning(f"Batch processing timed out for path: {path}")
                        
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing path {path}: {e}"
            self.logger.error(result.error_message)
        
        return result

    def _process_single_path(self, path: str, scan_only: bool = True) -> CleanupResult:
        """
        Process a single path (directory or file pattern).
        
        Args:
            path: Path to process
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult for this path
        """
        result = CleanupResult()
        
        try:
            if not path_exists(path):
                self.logger.debug(f"Path does not exist: {path}")
                return result
            
            self.logger.debug(f"Processing path: {path}")
            
            # Find files in the path with reasonable limits
            max_files_per_path = 10000  # Limit to prevent hanging
            files = list(find_files(path, max_files=max_files_per_path))
            
            if not files:
                self.logger.debug(f"No files found in: {path}")
                return result
            
            # Process files in batches for better performance
            batch_size = 100  # Process files in batches
            max_workers = min(8, len(files), 16)  # Increase thread count but cap it
            
            # Split files into batches
            file_batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
            
            batch_timeout = 60.0  # 60 seconds per batch
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit batch processing tasks
                future_to_batch = {
                    executor.submit(self._process_file_batch, batch, scan_only): batch 
                    for batch in file_batches
                }
                
                # Collect results from batches with timeout
                for future in as_completed(future_to_batch, timeout=batch_timeout * len(file_batches)):
                    if self._stop_requested:
                        break
                    
                    batch = future_to_batch[future]
                    try:
                        # Get result with timeout
                        batch_result = future.result(timeout=batch_timeout)
                        
                        result.files_scanned += batch_result.files_scanned
                        result.files_deleted += batch_result.files_deleted
                        result.bytes_freed += batch_result.bytes_freed
                        
                        if not batch_result.success and batch_result.error_message:
                            if result.error_message:
                                result.error_message += f"; {batch_result.error_message}"
                            else:
                                result.error_message = batch_result.error_message
                            result.success = False
                            
                    except TimeoutError:
                        self.logger.warning(f"Batch processing timed out after {batch_timeout} seconds")
                        result.success = False
                    except Exception as e:
                        self.logger.error(f"Error processing batch: {e}")
                        result.success = False
            
            # Clean up empty directories after file deletion
            if not scan_only and not self.dry_run and result.files_deleted > 0:
                try:
                    empty_dirs_removed = cleanup_empty_directories(path, self.dry_run)
                    if empty_dirs_removed > 0:
                        self.logger.debug(f"Removed {empty_dirs_removed} empty directories")
                except Exception as e:
                    self.logger.warning(f"Failed to clean empty directories: {e}")
        
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing path {path}: {e}"
            self.logger.error(result.error_message)
        
        return result

    def _process_file_batch_fast(self, file_paths: list, scan_only: bool = True) -> CleanupResult:
        """
        优化的文件批处理方法，提高处理效率。
        
        Args:
            file_paths: List of file paths to process
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult for the entire batch
        """
        result = CleanupResult()
        batch_size = len(file_paths)
        
        # 预处理：快速过滤文件，避免重复安全检查
        valid_files = []
        total_size = 0
        
        for file_path in file_paths:
            try:
                # 快速大小检查
                size = get_file_size(file_path)
                if size > 0:  # 只处理非空文件
                    valid_files.append((file_path, size))
                    total_size += size
            except (OSError, PermissionError):
                continue
        
        if not valid_files:
            return result
        
        # 按优先级分数排序，结合大小和类型
        valid_files_with_score = []
        for file_path, file_size in valid_files:
            priority_score = get_file_priority_score(file_path)
            total_score = priority_score + (file_size // (1024 * 1024))  # 添加大小权重
            valid_files_with_score.append((total_score, file_path, file_size))
        
        # 按总分排序
        valid_files_with_score.sort(reverse=True)
        valid_files = [(path, size) for _, path, size in valid_files_with_score]
        
        processed_count = 0
        for file_path, file_size in valid_files:
            if self._stop_requested:
                break
            
            try:
                # 快速安全检查（简化版）
                if self.enable_security_checks:
                    if not self._quick_safety_check(file_path):
                        continue
                
                result.files_scanned += 1
                result.bytes_freed += file_size
                
                if not scan_only:
                    # 实际删除文件
                    success, error_msg = safe_delete_file(file_path, self.dry_run)
                    if success:
                        result.files_deleted += 1
                        if self.verbose:
                            self.logger.log_file_operation("deleted", str(file_path), True)
                    else:
                        self._track_failed_deletion(file_path, error_msg)
                        if self.verbose:
                            self.logger.debug(f"Failed to delete: {file_path} ({error_msg})")
                
                processed_count += 1
                
                # 减少进度更新频率
                if processed_count % 50 == 0 and self.progress_callback:
                    progress_msg = f"Processing files... ({result.files_scanned} processed)"
                    self.progress_callback(progress_msg, processed_count, len(valid_files))
                    
            except Exception as e:
                if self.verbose:
                    self.logger.error(f"Error processing file {file_path}: {e}")
        
        return result

    def _quick_safety_check(self, file_path: Path) -> bool:
        """快速安全检查，避免复杂的安全扫描。"""
        try:
            file_str = str(file_path).lower()
            
            # 跳过系统关键文件
            dangerous_patterns = [
                'system32', 'syswow64', 'drivers', 'boot', 'recovery',
                'windows\\system', 'program files', 'programdata',
                '.exe', '.dll', '.sys', '.ini', '.cfg'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in file_str:
                    return False
            
            return True
            
        except Exception:
            return False

    def _process_file_batch(self, file_paths: list, scan_only: bool = True) -> CleanupResult:
        """
        Process a batch of files efficiently with progress updates.
        
        Args:
            file_paths: List of file paths to process
            scan_only: If True, only scan files without deleting
        
        Returns:
            CleanupResult for the entire batch
        """
        result = CleanupResult()
        batch_size = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            if self._stop_requested:
                break
                
            try:
                file_result = self._process_single_file(file_path, scan_only)
                
                result.files_scanned += file_result.files_scanned
                result.files_deleted += file_result.files_deleted
                result.bytes_freed += file_result.bytes_freed
                
                # Update progress for enhanced display
                if self.use_enhanced_progress and hasattr(self.progress_display, 'update_progress'):
                    self.progress_display.update_progress(
                        processed_files=file_result.files_scanned,
                        processed_bytes=file_result.bytes_freed,
                        current_file=str(file_path.name) if hasattr(file_path, 'name') else str(file_path)
                    )
                
                # Update progress callback every 20 files or at the end (less frequent)
                if self.progress_callback and (i % 20 == 0 or i == batch_size - 1):
                    progress_msg = f"Processing files... ({result.files_scanned} processed)"
                    self.progress_callback(progress_msg, i + 1, batch_size)
                
                if not file_result.success and file_result.error_message:
                    if result.error_message:
                        result.error_message += f"; {file_result.error_message}"
                    else:
                        result.error_message = file_result.error_message
                    result.success = False
                    
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                result.success = False
        
        return result
    
    def _process_single_file(self, file_path: Path, scan_only: bool = True) -> CleanupResult:
        """
        Process a single file (scan or delete) with enhanced security filtering.
        
        Args:
            file_path: Path to the file
            scan_only: If True, only scan file without deleting
        
        Returns:
            CleanupResult for this file
        """
        result = CleanupResult()
        
        try:
            # Enhanced security checks
            if self.enable_security_checks:
                security_result = self.security_checker.check_file_security(file_path)
                
                if security_result.security_level == SecurityLevel.CRITICAL:
                    if self.verbose:
                        self.logger.debug(f"Skipped (critical): {file_path} - {security_result.risk_factors}")
                    return result
                elif security_result.security_level == SecurityLevel.HIGH_RISK:
                    if self.verbose:
                        self.logger.debug(f"Skipped (high risk): {file_path} - {security_result.risk_factors}")
                    return result
                elif not security_result.is_safe:
                    if self.verbose:
                        self.logger.debug(f"Skipped (unsafe): {file_path} - {security_result.risk_factors}")
                    return result
                
                # Log security level for moderate files
                if security_result.security_level == SecurityLevel.MODERATE and self.verbose:
                    self.logger.debug(f"Processing with caution: {file_path} - Level: {security_result.security_level.value}")
            else:
                # Fallback to basic safety check
                if not is_safe_to_delete(file_path):
                    if self.verbose:
                        self.logger.debug(f"Skipped (not safe): {file_path}")
                    return result
            
            # Get file size
            file_size = get_file_size(file_path)
            if file_size == 0:
                return result  # Skip empty files
            
            result.files_scanned = 1
            result.bytes_freed = file_size
            
            if scan_only:
                # Just scanning - log if verbose
                if self.verbose:
                    self.logger.log_file_operation("scan", str(file_path), True)
                result.success = True
            else:
                # Actually delete the file
                success, error_msg = safe_delete_file(file_path, self.dry_run)
                
                if success:
                    result.files_deleted = 1
                    result.success = True
                    
                    action = "would delete" if self.dry_run else "deleted"
                    self.logger.log_file_operation(action, str(file_path), True)
                else:
                    # Track failed deletions for user feedback
                    self._track_failed_deletion(file_path, error_msg)
                    
                    # Only log serious errors (not common permission/usage issues)
                    if "Permission denied" not in error_msg and "appears to be in active use" not in error_msg and "Insufficient permissions" not in error_msg:
                        result.success = False
                        result.error_message = error_msg
                        self.logger.log_file_operation("delete", str(file_path), False, error_msg)
                    else:
                        # For common permission/usage errors, just skip silently
                        if self.verbose:
                            self.logger.debug(f"Skipped: {file_path} ({error_msg})")
                        result.files_scanned = 0  # Don't count as scanned
                        result.bytes_freed = 0   # Don't count bytes
        
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing file {file_path}: {e}"
            self.logger.error(result.error_message)
        
        return result

    def _process_system_optimization_enhanced(self, scan_only: bool = True, optimization_mode: str = 'standard') -> CleanupResult:
        """
        增强的系统优化清理方法。
        
        Args:
            scan_only: If True, only scan files without deleting
            optimization_mode: 优化模式 ('conservative', 'standard', 'aggressive', 'expert')
        
        Returns:
            CleanupResult with comprehensive system optimization results
        """
        from .config import CleanupType, SYSTEM_OPTIMIZATION_CONFIG
        
        total_result = CleanupResult()
        operation_name = f"{'Scanning' if scan_only else 'Cleaning'} System Optimization"
        
        try:
            self.logger.info(f"Starting enhanced system optimization with mode: {optimization_mode}")
            
            # 获取优化模式对应的路径
            base_paths = get_optimization_mode_paths(optimization_mode)
            if not base_paths:
                self.logger.warning("No system optimization paths found for the selected mode")
                return total_result
            
            # 预过滤存在的路径
            existing_paths = batch_check_paths(base_paths)
            if not existing_paths:
                self.logger.info("No system optimization paths found to process")
                return total_result
            
            self.logger.info(f"Found {len(existing_paths)} system optimization paths to process")
            
            if self.use_enhanced_progress:
                self.progress_display.start_operation(operation_name, len(existing_paths))
            
            # 系统优化：中等并发数（系统文件需要更谨慎处理）
            max_workers = min(12, len(existing_paths), os.cpu_count() * 2)
            
            # 按优化类别分组处理
            optimization_categories = SYSTEM_OPTIMIZATION_CONFIG['optimization_priorities']
            
            processed_paths = 0
            
            # 按优先级顺序处理各类别
            for priority in ['critical', 'high', 'medium', 'low']:
                if priority not in optimization_categories:
                    continue
                
                self.logger.info(f"Processing {priority} priority system optimization files...")
                
                # 过滤属于当前优先级的路径
                priority_paths = []
                for path in existing_paths:
                    if self._path_belongs_to_priority(path, priority, optimization_categories[priority]):
                        priority_paths.append(path)
                
                if not priority_paths:
                    continue
                
                # 并行处理当前优先级的路径
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_path = {
                        executor.submit(self._process_single_system_optimization_path, path, scan_only, priority): path 
                        for path in priority_paths
                    }
                    
                    for future in as_completed(future_to_path, timeout=900):  # 15分钟超时
                        if self._stop_requested:
                            break
                        
                        path = future_to_path[future]
                        try:
                            path_result = future.result(timeout=180)  # 单个路径3分钟超时
                            
                            total_result.files_scanned += path_result.files_scanned
                            total_result.files_deleted += path_result.files_deleted
                            total_result.bytes_freed += path_result.bytes_freed
                            
                            if not path_result.success and path_result.error_message:
                                if total_result.error_message:
                                    total_result.error_message += f"; {path_result.error_message}"
                                else:
                                    total_result.error_message = path_result.error_message
                                total_result.success = False
                            
                            processed_paths += 1
                            
                            if self.use_enhanced_progress:
                                self.progress_display.update_progress(processed_paths, len(existing_paths))
                                
                        except TimeoutError:
                            self.logger.warning(f"System optimization path processing timed out: {path}")
                            
                        except Exception as e:
                            self.logger.warning(f"Error processing system optimization path {path}: {e}")
            
            # 检查系统健康状态
            if not scan_only:
                try:
                    health_status = get_system_health_status()
                    if health_status:
                        self.logger.info(f"System health check completed: {health_status}")
                except Exception as e:
                    self.logger.warning(f"System health check failed: {e}")
        
        finally:
            if self.use_enhanced_progress:
                success_msg = f"{total_result.files_scanned:,} system optimization files processed"
                if total_result.bytes_freed > 0:
                    success_msg += f", {format_bytes(total_result.bytes_freed)} found"
                self.progress_display.finish_operation(True, success_msg)
        
        # 记录结果
        if scan_only:
            self.logger.log_scan_result(CleanupType.SYSTEM_OPTIMIZATION, total_result)
        else:
            self.logger.log_cleanup_result(CleanupType.SYSTEM_OPTIMIZATION, total_result)
        
        return total_result

    def _path_belongs_to_priority(self, path: str, priority: str, categories: list) -> bool:
        """检查路径是否属于指定优先级类别。"""
        
        path_lower = path.lower()
        for category in categories:
            if _path_matches_category(path_lower, category):
                return True
        return False

    def _process_single_system_optimization_path(self, path: str, scan_only: bool = True, priority: str = 'medium') -> CleanupResult:
        """
        处理单个系统优化路径。
        
        Args:
            path: Path to process
            scan_only: If True, only scan files without deleting
            priority: 优先级级别
        
        Returns:
            CleanupResult for this path
        """
        result = CleanupResult()
        
        try:
            if not path_exists(path):
                return result
            
            # 使用系统优化的文件查找（限制深度和数量）
            max_files_per_path = 30000  # 系统文件通常数量有限
            max_depth = 4 if priority in ['critical', 'high'] else 3
            
            files = list(find_files_fast(path, max_files=max_files_per_path, max_depth=max_depth))
            
            if not files:
                return result
            
            # 过滤和评分系统优化文件
            valid_files = []
            
            for file_path in files:
                if self._stop_requested:
                    break
                
                try:
                    # 安全检查：跳过危险的系统路径
                    if is_dangerous_system_path(file_path):
                        continue
                    
                    # 计算系统优化专用优先级
                    priority_score = get_system_optimization_priority_score(file_path)
                    
                    # 根据优先级级别调整分数阈值
                    score_threshold = {
                        'critical': 200,
                        'high': 150,
                        'medium': 100,
                        'low': 50
                    }.get(priority, 100)
                    
                    if priority_score >= score_threshold:
                        file_size = get_file_size(file_path)
                        if file_size > 0:
                            valid_files.append((priority_score, file_path, file_size))
                
                except (OSError, PermissionError):
                    continue
            
            if not valid_files:
                return result
            
            # 按系统优化优先级排序
            valid_files.sort(reverse=True)
            
            # 系统优化专用批处理：较小批次以确保安全
            batch_size = 200
            max_workers = min(8, len(valid_files), os.cpu_count() * 2)
            
            file_batches = [valid_files[i:i + batch_size] for i in range(0, len(valid_files), batch_size)]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_batch = {
                    executor.submit(self._process_system_optimization_file_batch, batch, scan_only, priority): batch 
                    for batch in file_batches
                }
                
                for future in as_completed(future_to_batch, timeout=180):  # 3分钟超时
                    if self._stop_requested:
                        break
                    
                    try:
                        batch_result = future.result(timeout=120)
                        
                        result.files_scanned += batch_result.files_scanned
                        result.files_deleted += batch_result.files_deleted
                        result.bytes_freed += batch_result.bytes_freed
                        
                        if not batch_result.success and batch_result.error_message:
                            if result.error_message:
                                result.error_message += f"; {batch_result.error_message}"
                            else:
                                result.error_message = batch_result.error_message
                            result.success = False
                            
                    except TimeoutError:
                        self.logger.warning(f"System optimization batch processing timed out for path: {path}")
                        
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing system optimization path {path}: {e}"
            self.logger.error(result.error_message)
        
        return result

    def _process_system_optimization_file_batch(self, file_data: list, scan_only: bool = True, priority: str = 'medium') -> CleanupResult:
        """
        系统优化专用的文件批处理方法。
        
        Args:
            file_data: List of tuples (priority_score, file_path, file_size)
            scan_only: If True, only scan files without deleting
            priority: 优先级级别
        
        Returns:
            CleanupResult for this batch
        """
        result = CleanupResult()
        
        if not file_data:
            return result
        
        processed_count = 0
        for priority_score, file_path, file_size in file_data:
            if self._stop_requested:
                break
            
            try:
                # 再次进行危险路径检查
                if is_dangerous_system_path(file_path):
                    continue
                
                result.files_scanned += 1
                result.bytes_freed += file_size
                
                if not scan_only:
                    success, error_msg = safe_delete_file(file_path, self.dry_run)
                    if success:
                        result.files_deleted += 1
                        if self.verbose:
                            self.logger.log_file_operation("deleted", str(file_path), True)
                    else:
                        self._track_failed_deletion(file_path, error_msg)
                        if self.verbose:
                            self.logger.debug(f"Failed to delete system optimization file: {file_path} ({error_msg})")
                
                processed_count += 1
                
                # 减少进度更新频率
                if processed_count % 50 == 0 and self.progress_callback:
                    progress_msg = f"Processing {priority} priority system files... ({result.files_scanned} processed)"
                    self.progress_callback(progress_msg, processed_count, len(file_data))
                    
            except Exception as e:
                if self.verbose:
                    self.logger.error(f"Error processing system optimization file {file_path}: {e}")
        
        return result