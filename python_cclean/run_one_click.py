#!/usr/bin/env python3
"""
Standalone script to run the one-click cleaner.
"""

import sys
import os

# Add the cclean package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cclean'))

from cclean.one_click_cleaner import OneClickCleaner, OneClickConfig
from cclean.config import format_bytes
from cclean.logger import CCleanLogger

def main():
    """Main function to run one-click cleaner."""
    # Initialize logger
    logger = CCleanLogger.get_instance()
    logger.start_session()
    
    try:
        print("=== CClean One-Click Cleaner ===\n")
        
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
        
        if preview['total_files'] == 0:
            print("\nNo files found to clean. Your system is already clean!")
            return
        
        # Show category breakdown
        print(f"\nCategory Breakdown:")
        for category, info in preview['categories'].items():
            print(f"  {category}: {info['files']:,} files, {info['size_formatted']}")
        
        # Ask for user confirmation
        response = input("\nProceed with one-click cleanup? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\nStarting one-click cleanup...")
            results = cleaner.perform_one_click_cleanup()
            
            print(f"\n=== Cleanup Results ===")
            print(f"Files deleted: {results['total_files_deleted']:,}")
            print(f"Space freed: {format_bytes(results['total_bytes_freed'])}")
            print(f"Duration: {results['duration']:.2f} seconds")
            print(f"Success: {results['success']}")
            
            if results['errors']:
                print(f"\nErrors encountered:")
                for error in results['errors']:
                    print(f"  - {error}")
                    
            if 'backup_stats' in results:
                backup_stats = results['backup_stats']
                print(f"\nBackup Information:")
                print(f"  Files backed up: {backup_stats.get('file_count', 0)}")
                print(f"  Backup size: {format_bytes(backup_stats.get('total_size', 0))}")
        else:
            print("Cleanup cancelled.")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"One-click cleaner error: {e}")
    finally:
        logger.end_session()

if __name__ == "__main__":
    main()