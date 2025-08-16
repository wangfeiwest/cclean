"""
Enhanced progress display module for CClean Python version.
Provides real-time progress bars, file processing statistics, and speed indicators.
"""

import time
import threading
from typing import Optional, Callable
from dataclasses import dataclass

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

@dataclass
class ProgressStats:
    """Statistics for progress tracking."""
    total_files: int = 0
    processed_files: int = 0
    total_bytes: int = 0
    processed_bytes: int = 0
    files_per_second: float = 0.0
    bytes_per_second: float = 0.0
    start_time: float = 0.0
    last_update_time: float = 0.0

class EnhancedProgressDisplay:
    """Enhanced progress display with real-time statistics."""
    
    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and HAS_COLORAMA
        self.stats = ProgressStats()
        self.current_operation = ""
        self.progress_bar: Optional[tqdm] = None
        self.lock = threading.Lock()
        self.last_message = ""
        self._initialized = True
        self._shutdown = False
        
    def start_operation(self, operation_name: str, total_items: int = 0):
        """Start a new operation with progress tracking."""
        with self.lock:
            self.current_operation = operation_name
            self.stats = ProgressStats(
                total_files=total_items,
                start_time=time.time(),
                last_update_time=time.time()
            )
            
            if HAS_TQDM and total_items > 0:
                self.progress_bar = tqdm(
                    total=total_items,
                    desc=self._format_operation_name(operation_name),
                    unit="files",
                    unit_scale=True,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
                )
            else:
                self._print_start_message(operation_name, total_items)
    
    def update_progress(self, processed_files: int = 0, processed_bytes: int = 0, 
                       current_file: str = "", message: str = ""):
        """Update progress with current statistics."""
        if self._shutdown or not self._initialized:
            return
            
        try:
            with self.lock:
                current_time = time.time()
                time_diff = current_time - self.stats.last_update_time
                
                # More conservative throttling to prevent spam and hanging
                if time_diff < 0.2:  # Update at most 5 times per second
                    return
            
            # Update statistics
            if processed_files > 0:
                self.stats.processed_files += processed_files
            if processed_bytes > 0:
                self.stats.processed_bytes += processed_bytes
            
            # Calculate rates
            elapsed_time = current_time - self.stats.start_time
            if elapsed_time > 0:
                self.stats.files_per_second = self.stats.processed_files / elapsed_time
                self.stats.bytes_per_second = self.stats.processed_bytes / elapsed_time
            
            self.stats.last_update_time = current_time
            
            # Update display
            if self.progress_bar and processed_files > 0:
                self.progress_bar.update(processed_files)
                if current_file:
                    # Show current file in description (truncated)
                    short_file = self._truncate_filename(current_file)
                    self.progress_bar.set_description(f"{self._format_operation_name(self.current_operation)} - {short_file}")
            elif not HAS_TQDM:
                self._print_progress_line(current_file, message)
        except Exception:
            # Ignore progress display errors to prevent crashes
            pass
    
    def set_total(self, total_files: int, total_bytes: int = 0):
        """Set or update the total number of items."""
        with self.lock:
            self.stats.total_files = total_files
            self.stats.total_bytes = total_bytes
            
            if self.progress_bar:
                self.progress_bar.total = total_files
    
    def finish_operation(self, success: bool = True, final_message: str = ""):
        """Finish the current operation and show summary."""
        with self.lock:
            if self.progress_bar:
                self.progress_bar.close()
                self.progress_bar = None
            
            # Show final summary
            self._print_summary(success, final_message)
    
    def _format_operation_name(self, name: str) -> str:
        """Format operation name with colors if available."""
        if self.use_colors:
            return f"{Fore.CYAN}{name}{Style.RESET_ALL}"
        return name
    
    def _truncate_filename(self, filename: str, max_length: int = 40) -> str:
        """Truncate filename for display."""
        if len(filename) <= max_length:
            return filename
        return "..." + filename[-(max_length-3):]
    
    def _print_start_message(self, operation: str, total_items: int):
        """Print operation start message."""
        if self.use_colors:
            print(f"\n{Fore.YELLOW}🔄 Starting {operation}...{Style.RESET_ALL}")
        else:
            print(f"\n🔄 Starting {operation}...")
        
        if total_items > 0:
            print(f"   📁 Total items to process: {total_items:,}")
    
    def _print_progress_line(self, current_file: str = "", message: str = ""):
        """Print progress line for systems without tqdm."""
        if self.stats.total_files > 0:
            percentage = (self.stats.processed_files / self.stats.total_files) * 100
            progress_bar = self._create_text_progress_bar(percentage)
            
            status_line = f"\r{progress_bar} {self.stats.processed_files}/{self.stats.total_files} "
            status_line += f"({percentage:.1f}%) - {self.stats.files_per_second:.1f} files/s"
            
            if current_file:
                short_file = self._truncate_filename(current_file, 30)
                status_line += f" - {short_file}"
            elif message and message != self.last_message:
                status_line += f" - {message}"
                self.last_message = message
        else:
            status_line = f"\r⏳ {self.current_operation}: {self.stats.processed_files:,} files processed"
            if self.stats.files_per_second > 0:
                status_line += f" ({self.stats.files_per_second:.1f} files/s)"
        
        print(status_line, end='', flush=True)
    
    def _create_text_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Create a text-based progress bar."""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        
        if self.use_colors:
            return f"{Fore.GREEN}[{bar}]{Style.RESET_ALL}"
        return f"[{bar}]"
    
    def _print_summary(self, success: bool, final_message: str):
        """Print operation summary."""
        print()  # New line after progress
        
        elapsed_time = time.time() - self.stats.start_time
        
        if self.use_colors:
            status_icon = f"{Fore.GREEN}✅" if success else f"{Fore.RED}❌"
            print(f"{status_icon} {self.current_operation} completed{Style.RESET_ALL}")
        else:
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {self.current_operation} completed")
        
        # Statistics summary
        print(f"   📊 Files processed: {self.stats.processed_files:,}")
        if self.stats.processed_bytes > 0:
            print(f"   💾 Data processed: {self._format_bytes(self.stats.processed_bytes)}")
        print(f"   ⏱️  Time elapsed: {elapsed_time:.2f} seconds")
        
        if elapsed_time > 0 and self.stats.processed_files > 0:
            print(f"   🚀 Average speed: {self.stats.files_per_second:.1f} files/s")
            if self.stats.processed_bytes > 0:
                print(f"   📈 Throughput: {self._format_bytes(self.stats.bytes_per_second)}/s")
        
        if final_message:
            print(f"   ℹ️  {final_message}")
        
        print()
    
    def _format_bytes(self, bytes_value: float) -> str:
        """Format bytes into human readable format."""
        if bytes_value == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(bytes_value)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"

class SimpleProgressCallback:
    """Simple progress callback that works with the existing progress callback system."""
    
    def __init__(self, display: EnhancedProgressDisplay):
        self.display = display
        self.current_operation = ""
        self.last_current = 0
        self.operation_started = False
    
    def __call__(self, message: str, current: int, total: int):
        """Progress callback function with loop prevention."""
        # Avoid recursive calls
        if hasattr(self, '_in_callback') and self._in_callback:
            return
        
        try:
            self._in_callback = True
            
            # Detect new operations
            if message != self.current_operation:
                if self.operation_started:  # Finish previous operation
                    self.display.finish_operation(True)
                
                self.current_operation = message
                self.operation_started = True
                self.display.start_operation(message, total)
                self.last_current = 0
            
            # Update progress - limit updates to avoid spam
            if total > 0:
                self.display.set_total(total)
            
            # Calculate increment
            increment = current - self.last_current if current > self.last_current else 0
            if increment > 0:
                self.last_current = current
                self.display.update_progress(processed_files=increment, message=message)
            
            # Finish if complete
            if current >= total > 0 and self.operation_started:
                self.display.finish_operation(True)
                self.current_operation = ""
                self.operation_started = False
                
        finally:
            self._in_callback = False