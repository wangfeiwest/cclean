"""
CClean - Windows C Drive Cleaner Tool (Python Version)

A comprehensive Windows C drive cleanup tool that helps free up disk space
by removing temporary files, browser cache, system logs, and emptying recycle bin.
"""

__version__ = "1.0.0"
__author__ = "CClean Development Team"

from .cleaner import CCleaner
from .config import CleanupType, CleanupResult
from .logger import CCleanLogger

__all__ = ['CCleaner', 'CleanupType', 'CleanupResult', 'CCleanLogger']