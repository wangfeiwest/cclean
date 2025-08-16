"""
Main entry point for CClean Python version.
Handles command-line interface, user interaction, and program flow.
"""

import sys
import argparse
import signal
import os
from typing import Optional

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

from .config import CleanupType, VERSION, APP_NAME, format_bytes
from .cleaner import CCleaner
from .logger import CCleanLogger
from .utils import has_admin_rights, request_admin_rights, get_free_disk_space

# Global cleaner instance for signal handling
_cleaner: Optional[CCleaner] = None

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    print("\n\nReceived interrupt signal. Stopping cleanup operations...")
    if _cleaner:
        _cleaner.stop()
    sys.exit(0)

def print_header():
    """Print application header with styling."""
    if HAS_COLORAMA:
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.GREEN}{APP_NAME}")
        print(f"{Fore.YELLOW}Version {VERSION}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    else:
        print(f"\n{'='*70}")
        print(f"{APP_NAME}")
        print(f"Version {VERSION}")
        print(f"{'='*70}\n")

def print_system_info():
    """Print system information."""
    admin_status = "✓ Yes" if has_admin_rights() else "✗ No (Limited functionality)"
    if HAS_COLORAMA:
        admin_color = Fore.GREEN if has_admin_rights() else Fore.YELLOW
        print(f"Administrator Rights: {admin_color}{admin_status}{Style.RESET_ALL}")
    else:
        print(f"Administrator Rights: {admin_status}")
    
    try:
        free_space = get_free_disk_space("C:")
        print(f"C: Drive Free Space: {format_bytes(free_space)}")
    except Exception:
        print("C: Drive Free Space: Unable to determine")
    
    print()

def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default response if user just presses Enter
    
    Returns:
        True if user confirms, False otherwise
    """
    suffix = " [Y/n]: " if default else " [y/N]: "
    
    while True:
        try:
            response = input(message + suffix).strip().lower()
            
            if not response:
                return default
            elif response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return False

def display_scan_results(result, cleanup_type_name: str):
    """Display scan results to user."""
    if HAS_COLORAMA:
        print(f"\n{Fore.CYAN}Scan Results - {cleanup_type_name}:{Style.RESET_ALL}")
        print(f"  Files Found: {Fore.YELLOW}{result.files_scanned:,}{Style.RESET_ALL}")
        print(f"  Space to Free: {Fore.GREEN}{format_bytes(result.bytes_freed)}{Style.RESET_ALL}")
    else:
        print(f"\nScan Results - {cleanup_type_name}:")
        print(f"  Files Found: {result.files_scanned:,}")
        print(f"  Space to Free: {format_bytes(result.bytes_freed)}")
    
    if not result.success and result.error_message:
        if HAS_COLORAMA:
            print(f"  {Fore.RED}Warnings: {result.error_message}{Style.RESET_ALL}")
        else:
            print(f"  Warnings: {result.error_message}")

def display_cleanup_results(result, cleanup_type_name: str, dry_run: bool = False):
    """Display cleanup results to user."""
    action = "Dry Run Results" if dry_run else "Cleanup Results"
    
    if HAS_COLORAMA:
        print(f"\n{Fore.CYAN}{action} - {cleanup_type_name}:{Style.RESET_ALL}")
        print(f"  Files Processed: {Fore.YELLOW}{result.files_deleted:,}/{result.files_scanned:,}{Style.RESET_ALL}")
        print(f"  Space Freed: {Fore.GREEN}{format_bytes(result.bytes_freed)}{Style.RESET_ALL}")
    else:
        print(f"\n{action} - {cleanup_type_name}:")
        print(f"  Files Processed: {result.files_deleted:,}/{result.files_scanned:,}")
        print(f"  Space Freed: {format_bytes(result.bytes_freed)}")
    
    if not result.success and result.error_message:
        if HAS_COLORAMA:
            print(f"  {Fore.RED}Errors: {result.error_message}{Style.RESET_ALL}")
        else:
            print(f"  Errors: {result.error_message}")

def progress_callback(message: str, current: int, total: int):
    """Progress callback for cleaner operations."""
    if total > 0:
        percentage = (current / total) * 100
        print(f"\r{message} ({current}/{total}, {percentage:.1f}%)", end='', flush=True)
        if current == total:
            print()  # New line when complete
    else:
        print(f"\r{message}", end='', flush=True)

def interactive_cleanup(cleaner: CCleaner, cleanup_type: CleanupType, dry_run: bool = False) -> bool:
    """
    Perform interactive cleanup with user confirmation.
    
    Args:
        cleaner: CCleaner instance
        cleanup_type: Type of cleanup to perform
        dry_run: Whether this is a dry run
    
    Returns:
        True if cleanup was successful, False otherwise
    """
    type_names = {
        CleanupType.TEMP_FILES: "Temporary Files",
        CleanupType.BROWSER_CACHE: "Browser Cache",
        CleanupType.SYSTEM_FILES: "System Files", 
        CleanupType.DEVELOPMENT_FILES: "Development Tools Cache",
        CleanupType.MEDIA_FILES: "Media & Download Temps",
        CleanupType.GAMING_FILES: "Gaming Platform Cache",
        CleanupType.SYSTEM_OPTIMIZATION: "System Optimization Files",
        CleanupType.RECYCLE_BIN: "Recycle Bin",
        CleanupType.ALL: "All Categories"
    }
    
    type_name = type_names.get(cleanup_type, "Unknown")
    
    # First, perform a scan
    print(f"Scanning {type_name.lower()}...")
    
    if cleanup_type == CleanupType.ALL:
        scan_result = cleaner.perform_full_scan()
    elif cleanup_type == CleanupType.TEMP_FILES:
        scan_result = cleaner.scan_temp_files()
    elif cleanup_type == CleanupType.BROWSER_CACHE:
        scan_result = cleaner.scan_browser_cache()
    elif cleanup_type == CleanupType.SYSTEM_FILES:
        scan_result = cleaner.scan_system_files()
    elif cleanup_type == CleanupType.DEVELOPMENT_FILES:
        scan_result = cleaner.scan_development_files()
    elif cleanup_type == CleanupType.MEDIA_FILES:
        scan_result = cleaner.scan_media_files()
    elif cleanup_type == CleanupType.GAMING_FILES:
        scan_result = cleaner.scan_gaming_files()
    elif cleanup_type == CleanupType.SYSTEM_OPTIMIZATION:
        scan_result = cleaner.scan_system_optimization()
    elif cleanup_type == CleanupType.RECYCLE_BIN:
        scan_result = cleaner.scan_recycle_bin()
    else:
        print("Unknown cleanup type")
        return False
    
    display_scan_results(scan_result, type_name)
    
    if scan_result.files_scanned == 0:
        print("No files found to clean.")
        return True
    
    # Ask for confirmation unless it's a dry run
    if not dry_run:
        if not confirm_action(f"Proceed with {type_name.lower()} cleanup?"):
            print("Cleanup cancelled by user.")
            return True
    
    # Perform cleanup
    action = "dry run" if dry_run else "cleanup"
    print(f"\nStarting {type_name.lower()} {action}...")
    
    if cleanup_type == CleanupType.ALL:
        cleanup_result = cleaner.perform_full_cleanup()
    elif cleanup_type == CleanupType.TEMP_FILES:
        cleanup_result = cleaner.clean_temp_files()
    elif cleanup_type == CleanupType.BROWSER_CACHE:
        cleanup_result = cleaner.clean_browser_cache()
    elif cleanup_type == CleanupType.SYSTEM_FILES:
        cleanup_result = cleaner.clean_system_files()
    elif cleanup_type == CleanupType.DEVELOPMENT_FILES:
        cleanup_result = cleaner.clean_development_files()
    elif cleanup_type == CleanupType.MEDIA_FILES:
        cleanup_result = cleaner.clean_media_files()
    elif cleanup_type == CleanupType.GAMING_FILES:
        cleanup_result = cleaner.clean_gaming_files()
    elif cleanup_type == CleanupType.SYSTEM_OPTIMIZATION:
        cleanup_result = cleaner.clean_system_optimization()
    elif cleanup_type == CleanupType.RECYCLE_BIN:
        cleanup_result = cleaner.clean_recycle_bin()
    else:
        return False
    
    display_cleanup_results(cleanup_result, type_name, dry_run)
    
    return cleanup_result.success

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='cclean-py',
        description='Windows C Drive Cleaner Tool - Python Version',
        epilog="""
Examples:
  cclean-py --scan                    # Scan all categories
  cclean-py --temp --dry-run          # Dry run temp file cleanup
  cclean-py --all --verbose           # Clean all with verbose output
  cclean-py --browser --quiet         # Clean browser cache quietly
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        '-s', '--scan',
        action='store_true',
        help='Scan for files without deleting (default action)'
    )
    action_group.add_argument(
        '-c', '--clean', 
        action='store_true',
        help='Clean files after confirmation'
    )
    
    # Category arguments
    category_group = parser.add_mutually_exclusive_group()
    category_group.add_argument(
        '-t', '--temp',
        action='store_true',
        help='Only process temporary files'
    )
    category_group.add_argument(
        '-b', '--browser',
        action='store_true', 
        help='Only process browser cache'
    )
    category_group.add_argument(
        '-r', '--recycle',
        action='store_true',
        help='Only empty recycle bin'
    )
    category_group.add_argument(
        '-y', '--system',
        action='store_true',
        help='Only process system files'
    )
    category_group.add_argument(
        '--dev', '--development',
        action='store_true',
        help='Only process development tools cache'
    )
    category_group.add_argument(
        '-m', '--media',
        action='store_true',
        help='Only process media and download temp files'
    )
    category_group.add_argument(
        '-g', '--gaming',
        action='store_true',
        help='Only process gaming platform cache'
    )
    category_group.add_argument(
        '-o', '--optimize', '--optimization',
        action='store_true',
        help='Only process system optimization files'
    )
    category_group.add_argument(
        '-a', '--all',
        action='store_true',
        help='Process all categories (default)'
    )
    
    # Mode arguments
    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='Show what would be deleted without deleting'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress console output (log file only)'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bars and animations'
    )
    
    # Configuration arguments
    parser.add_argument(
        '-l', '--log',
        metavar='FILE',
        default='cclean.log',
        help='Specify log file (default: cclean.log)'
    )
    parser.add_argument(
        '--force-admin',
        action='store_true',
        help='Request administrator privileges if not already elevated'
    )
    
    # Information arguments
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} v{VERSION}'
    )
    
    return parser

def main():
    """Main entry point."""
    global _cleaner
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if args.quiet and args.verbose:
        parser.error("Cannot use both --quiet and --verbose options")
    
    # Determine cleanup type
    cleanup_type = CleanupType.ALL  # default
    if args.temp:
        cleanup_type = CleanupType.TEMP_FILES
    elif args.browser:
        cleanup_type = CleanupType.BROWSER_CACHE
    elif args.system:
        cleanup_type = CleanupType.SYSTEM_FILES
    elif args.dev:
        cleanup_type = CleanupType.DEVELOPMENT_FILES
    elif args.media:
        cleanup_type = CleanupType.MEDIA_FILES
    elif args.gaming:
        cleanup_type = CleanupType.GAMING_FILES
    elif args.optimize:
        cleanup_type = CleanupType.SYSTEM_OPTIMIZATION
    elif args.recycle:
        cleanup_type = CleanupType.RECYCLE_BIN
    
    # Determine action (default is scan)
    scan_only = not args.clean
    
    # Request admin rights if needed
    if args.force_admin and not has_admin_rights():
        print("Requesting administrator privileges...")
        request_admin_rights()
        return
    
    # Print header unless quiet
    if not args.quiet:
        print_header()
        print_system_info()
        
        if not has_admin_rights():
            if HAS_COLORAMA:
                print(f"{Fore.YELLOW}Warning: Running without administrator privileges.")
                print(f"Some system files may not be accessible.{Style.RESET_ALL}\n")
            else:
                print("Warning: Running without administrator privileges.")
                print("Some system files may not be accessible.\n")
    
    # Initialize logger
    logger = CCleanLogger.get_instance(args.log, not args.quiet)
    logger.start_session()
    
    if args.verbose:
        logger.set_console_level('DEBUG')
    
    try:
        # Initialize cleaner
        _cleaner = CCleaner(logger)
        _cleaner.set_dry_run(args.dry_run)
        _cleaner.set_verbose(args.verbose)
        
        # Set up progress display - Enhanced progress is now default
        if not args.no_progress and not args.quiet:
            if args.verbose:
                # Use simple callback for verbose mode to avoid conflicts
                _cleaner.set_progress_callback(progress_callback)
                _cleaner.set_enhanced_progress(False)
            else:
                # Enhanced progress display is now the default
                _cleaner.set_enhanced_progress(True)
        
        # Perform the requested operation
        success = True
        
        if scan_only:
            # Scan mode
            type_names = {
                CleanupType.TEMP_FILES: "Temporary Files",
                CleanupType.BROWSER_CACHE: "Browser Cache",
                CleanupType.SYSTEM_FILES: "System Files",
                CleanupType.DEVELOPMENT_FILES: "Development Tools Cache",
                CleanupType.MEDIA_FILES: "Media & Download Temps",
                CleanupType.GAMING_FILES: "Gaming Platform Cache",
                CleanupType.SYSTEM_OPTIMIZATION: "System Optimization Files",
                CleanupType.RECYCLE_BIN: "Recycle Bin", 
                CleanupType.ALL: "All Categories"
            }
            
            type_name = type_names.get(cleanup_type, "Unknown")
            
            if not args.quiet:
                print(f"Scanning {type_name.lower()}...")
            
            if cleanup_type == CleanupType.ALL:
                result = _cleaner.perform_full_scan()
            elif cleanup_type == CleanupType.TEMP_FILES:
                result = _cleaner.scan_temp_files()
            elif cleanup_type == CleanupType.BROWSER_CACHE:
                result = _cleaner.scan_browser_cache()
            elif cleanup_type == CleanupType.SYSTEM_FILES:
                result = _cleaner.scan_system_files()
            elif cleanup_type == CleanupType.DEVELOPMENT_FILES:
                result = _cleaner.scan_development_files()
            elif cleanup_type == CleanupType.MEDIA_FILES:
                result = _cleaner.scan_media_files()
            elif cleanup_type == CleanupType.GAMING_FILES:
                result = _cleaner.scan_gaming_files()
            elif cleanup_type == CleanupType.SYSTEM_OPTIMIZATION:
                result = _cleaner.scan_system_optimization()
            elif cleanup_type == CleanupType.RECYCLE_BIN:
                result = _cleaner.scan_recycle_bin()
            
            if not args.quiet:
                display_scan_results(result, type_name)
            
            success = result.success
        
        else:
            # Clean mode
            success = interactive_cleanup(_cleaner, cleanup_type, args.dry_run)
        
        # Final status
        if not args.quiet:
            if success:
                if HAS_COLORAMA:
                    print(f"\n{Fore.GREEN}Operation completed successfully!{Style.RESET_ALL}")
                else:
                    print("\nOperation completed successfully!")
            else:
                if HAS_COLORAMA:
                    print(f"\n{Fore.RED}Operation completed with errors. Check log for details.{Style.RESET_ALL}")
                else:
                    print("\nOperation completed with errors. Check log for details.")
        
        logger.end_session()
        return 0 if success else 1
    
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nOperation cancelled by user.")
        logger.info("Operation cancelled by user")
        logger.end_session()
        return 130  # Standard exit code for SIGINT
    
    except Exception as e:
        error_msg = f"Fatal error: {e}"
        if not args.quiet:
            if HAS_COLORAMA:
                print(f"\n{Fore.RED}{error_msg}{Style.RESET_ALL}")
            else:
                print(f"\n{error_msg}")
        
        logger.critical(error_msg)
        logger.end_session()
        return 1

if __name__ == '__main__':
    sys.exit(main())