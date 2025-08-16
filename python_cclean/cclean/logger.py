"""
Logging system for CClean Python version.
Provides comprehensive logging with file rotation, console output, and cleanup reporting.
"""

import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO
from logging.handlers import RotatingFileHandler

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

from .config import CleanupType, CleanupResult, DEFAULT_LOG_FILE, MAX_LOG_SIZE, format_bytes
from .utils import get_current_timestamp

class ColorFormatter(logging.Formatter):
    """Custom formatter with color support."""
    
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT
    } if HAS_COLORAMA else {}
    
    def format(self, record):
        if HAS_COLORAMA and record.levelno in self.COLORS:
            # Add color to the level name
            record.levelname = f"{self.COLORS[record.levelno]}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

class CCleanLogger:
    """
    Centralized logging system for CClean with file and console output.
    """
    
    _instance: Optional['CCleanLogger'] = None
    
    def __init__(self, log_file: str = DEFAULT_LOG_FILE, console_output: bool = True):
        """
        Initialize the logger.
        
        Args:
            log_file: Path to the log file
            console_output: Whether to output to console
        """
        self.log_file = log_file
        self.console_output = console_output
        self.session_start_time = time.time()
        self._setup_logging()
    
    @classmethod
    def get_instance(cls, log_file: str = DEFAULT_LOG_FILE, console_output: bool = True) -> 'CCleanLogger':
        """Get singleton instance of the logger."""
        if cls._instance is None:
            cls._instance = cls(log_file, console_output)
        return cls._instance
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create main logger
        self.logger = logging.getLogger('cclean')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler with rotation
        try:
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=MAX_LOG_SIZE,
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}")
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = ColorFormatter(
                '[%(levelname)s] %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)
    
    def start_session(self):
        """Log session start information."""
        self.session_start_time = time.time()
        
        separator = "=" * 60
        self.info(separator)
        self.info("CClean Python Session Started")
        self.info(f"Timestamp: {get_current_timestamp()}")
        self.info(f"Log File: {os.path.abspath(self.log_file)}")
        
        # System information
        import platform
        from .utils import has_admin_rights, get_free_disk_space
        
        self.info(f"Platform: {platform.platform()}")
        self.info(f"Python Version: {platform.python_version()}")
        self.info(f"Admin Rights: {'Yes' if has_admin_rights() else 'No'}")
        
        try:
            free_space = get_free_disk_space("C:")
            self.info(f"C: Drive Free Space: {format_bytes(free_space)}")
        except Exception:
            self.info("C: Drive Free Space: Unable to determine")
        
        self.info(separator)
    
    def end_session(self):
        """Log session end information."""
        session_duration = time.time() - self.session_start_time
        
        separator = "=" * 60
        self.info(separator)
        self.info("CClean Python Session Ended")
        self.info(f"Duration: {session_duration:.2f} seconds")
        self.info(f"Timestamp: {get_current_timestamp()}")
        self.info(separator)
    
    def log_cleanup_result(self, cleanup_type: CleanupType, result: CleanupResult):
        """
        Log the results of a cleanup operation.
        
        Args:
            cleanup_type: Type of cleanup that was performed
            result: Results of the cleanup operation
        """
        type_names = {
            CleanupType.TEMP_FILES: "Temporary Files",
            CleanupType.BROWSER_CACHE: "Browser Cache",
            CleanupType.SYSTEM_FILES: "System Files",
            CleanupType.RECYCLE_BIN: "Recycle Bin",
            CleanupType.ALL: "All Categories"
        }
        
        type_name = type_names.get(cleanup_type, "Unknown")
        
        if result.success:
            message = (f"{type_name} cleanup completed: "
                      f"{result.files_deleted}/{result.files_scanned} files processed, "
                      f"{format_bytes(result.bytes_freed)} freed")
            self.info(message)
        else:
            message = (f"{type_name} cleanup failed: {result.error_message}")
            self.error(message)
        
        # Detailed breakdown if available
        if result.files_scanned > 0:
            success_rate = (result.files_deleted / result.files_scanned) * 100
            self.debug(f"{type_name} success rate: {success_rate:.1f}%")
    
    def log_scan_result(self, cleanup_type: CleanupType, result: CleanupResult):
        """
        Log the results of a scan operation.
        
        Args:
            cleanup_type: Type of cleanup that was scanned
            result: Results of the scan operation
        """
        type_names = {
            CleanupType.TEMP_FILES: "Temporary Files",
            CleanupType.BROWSER_CACHE: "Browser Cache", 
            CleanupType.SYSTEM_FILES: "System Files",
            CleanupType.RECYCLE_BIN: "Recycle Bin",
            CleanupType.ALL: "All Categories"
        }
        
        type_name = type_names.get(cleanup_type, "Unknown")
        
        if result.success:
            message = (f"{type_name} scan completed: "
                      f"{result.files_scanned} files found, "
                      f"{format_bytes(result.bytes_freed)} can be freed")
            self.info(message)
        else:
            message = f"{type_name} scan failed: {result.error_message}"
            self.error(message)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, error: str = ""):
        """
        Log individual file operations.
        
        Args:
            operation: Type of operation (scan, delete, skip)
            file_path: Path to the file
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        if success:
            self.debug(f"{operation.upper()}: {file_path}")
        else:
            self.warning(f"{operation.upper()} FAILED: {file_path} - {error}")
    
    def log_progress(self, message: str, current: int, total: int):
        """
        Log progress information.
        
        Args:
            message: Progress message
            current: Current progress
            total: Total items
        """
        if total > 0:
            percentage = (current / total) * 100
            self.debug(f"PROGRESS: {message} ({current}/{total}, {percentage:.1f}%)")
        else:
            self.debug(f"PROGRESS: {message}")
    
    def set_console_level(self, level: str):
        """
        Set the console logging level.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        log_level = level_map.get(level.upper(), logging.INFO)
        
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(log_level)
    
    def enable_console_output(self, enabled: bool):
        """
        Enable or disable console output.
        
        Args:
            enabled: Whether to enable console output
        """
        self.console_output = enabled
        
        # Remove existing console handlers
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                self.logger.removeHandler(handler)
        
        # Add console handler if enabled
        if enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = ColorFormatter('[%(levelname)s] %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def write_summary_report(self, results: dict, output_file: Optional[str] = None):
        """
        Write a summary report of all cleanup operations.
        
        Args:
            results: Dictionary of cleanup results by type
            output_file: Optional file to write report to
        """
        timestamp = get_current_timestamp()
        
        report_lines = [
            "CClean Python - Cleanup Summary Report",
            f"Generated: {timestamp}",
            "=" * 50,
            ""
        ]
        
        total_files_scanned = 0
        total_files_deleted = 0
        total_bytes_freed = 0
        
        for cleanup_type, result in results.items():
            if isinstance(cleanup_type, CleanupType):
                type_name = cleanup_type.value.replace('_', ' ').title()
                report_lines.extend([
                    f"{type_name}:",
                    f"  Files Scanned: {result.files_scanned:,}",
                    f"  Files Deleted: {result.files_deleted:,}",
                    f"  Bytes Freed: {format_bytes(result.bytes_freed)}",
                    f"  Status: {'Success' if result.success else 'Failed'}",
                    ""
                ])
                
                if result.success:
                    total_files_scanned += result.files_scanned
                    total_files_deleted += result.files_deleted
                    total_bytes_freed += result.bytes_freed
        
        report_lines.extend([
            "Summary Totals:",
            f"  Total Files Scanned: {total_files_scanned:,}",
            f"  Total Files Deleted: {total_files_deleted:,}",
            f"  Total Space Freed: {format_bytes(total_bytes_freed)}",
            ""
        ])
        
        report_text = "\n".join(report_lines)
        
        # Write to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                self.info(f"Summary report written to: {output_file}")
            except Exception as e:
                self.error(f"Failed to write summary report: {e}")
        
        # Log to main logger
        self.info("Cleanup Summary Report:")
        for line in report_lines[3:]:  # Skip header and separator
            if line:
                self.info(line)

# Convenience functions for global logger instance
def get_logger() -> CCleanLogger:
    """Get the global logger instance."""
    return CCleanLogger.get_instance()

def debug(message: str):
    """Log debug message using global logger."""
    get_logger().debug(message)

def info(message: str):
    """Log info message using global logger."""
    get_logger().info(message)

def warning(message: str):
    """Log warning message using global logger."""
    get_logger().warning(message)

def error(message: str):
    """Log error message using global logger."""
    get_logger().error(message)

def critical(message: str):
    """Log critical message using global logger."""
    get_logger().critical(message)