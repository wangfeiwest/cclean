"""
Enhanced Security Checking Module for CClean.
Implements multiple security layers and validation mechanisms.
Based on JIEKE66633 project analysis for enhanced safety.
"""

import os
import re
import time
import psutil
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .config import format_bytes
from .logger import CCleanLogger

class SecurityLevel(Enum):
    """Security levels for file operations."""
    SAFE = "safe"          # Safe to delete without backup
    MODERATE = "moderate"   # Safe with backup
    HIGH_RISK = "high_risk" # Requires special handling
    CRITICAL = "critical"   # Never delete

@dataclass
class SecurityResult:
    """Result of security check."""
    is_safe: bool
    security_level: SecurityLevel
    risk_factors: List[str]
    recommendations: List[str]
    
class SecurityChecker:
    """
    Enhanced security checker with multiple validation layers.
    Implements comprehensive safety mechanisms.
    """
    
    def __init__(self, logger: Optional[CCleanLogger] = None):
        self.logger = logger if logger else CCleanLogger.get_instance()
        
        # Critical system directories (never touch)
        self.critical_directories = {
            "C:\\Windows\\System32",
            "C:\\Windows\\SysWOW64", 
            "C:\\Windows\\Boot",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\Windows\\Microsoft.NET",
            "C:\\Windows\\assembly",
            "C:\\Windows\\WinSxS"
        }
        
        # Critical file patterns (never delete)
        self.critical_patterns = {
            r".*\.exe$",
            r".*\.dll$",
            r".*\.sys$", 
            r".*\.ini$",
            r".*\.cfg$",
            r".*\.reg$",
            r".*boot.*",
            r".*system.*",
            r".*ntuser.*"
        }
        
        # High-risk extensions
        self.high_risk_extensions = {
            '.exe', '.dll', '.sys', '.bat', '.cmd', '.ps1',
            '.vbs', '.js', '.jar', '.msi', '.reg', '.inf'
        }
        
        # Safe temporary extensions
        self.safe_temp_extensions = {
            '.tmp', '.temp', '.log', '.bak', '.old', '.cache',
            '.cookies', '.history', '.chk', '.gid', '.dmp'
        }
        
        # Process whitelist - never delete files from these processes
        self.protected_processes = {
            'explorer.exe', 'dwm.exe', 'winlogon.exe', 'csrss.exe',
            'smss.exe', 'wininit.exe', 'services.exe', 'lsass.exe',
            'svchost.exe', 'System', 'Registry'
        }
        
        # File size limits (in bytes)
        self.max_safe_file_size = 100 * 1024 * 1024  # 100MB
        self.min_file_age_seconds = 1800  # 30 minutes
        
        self.logger.info("Security checker initialized with enhanced safety mechanisms")
    
    def check_file_security(self, file_path: Path) -> SecurityResult:
        """
        Perform comprehensive security check on a file.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            SecurityResult with safety assessment
        """
        risk_factors = []
        recommendations = []
        security_level = SecurityLevel.SAFE
        
        try:
            # Basic existence check
            if not file_path.exists():
                return SecurityResult(
                    is_safe=False,
                    security_level=SecurityLevel.CRITICAL,
                    risk_factors=["File does not exist"],
                    recommendations=["Skip non-existent file"]
                )
            
            if not file_path.is_file():
                return SecurityResult(
                    is_safe=False,
                    security_level=SecurityLevel.CRITICAL,
                    risk_factors=["Path is not a file"],
                    recommendations=["Only process files, not directories"]
                )
            
            # Check 1: Critical directory protection
            critical_dir_result = self._check_critical_directories(file_path)
            if critical_dir_result:
                risk_factors.extend(critical_dir_result)
                security_level = SecurityLevel.CRITICAL
            
            # Check 2: Critical file pattern protection
            critical_pattern_result = self._check_critical_patterns(file_path)
            if critical_pattern_result:
                risk_factors.extend(critical_pattern_result)
                security_level = SecurityLevel.CRITICAL
            
            # Check 3: File extension analysis
            extension_result, ext_level = self._check_file_extension(file_path)
            if extension_result:
                risk_factors.extend(extension_result)
                if ext_level.value > security_level.value:
                    security_level = ext_level
            
            # Check 4: File age verification
            age_result = self._check_file_age(file_path)
            if age_result:
                risk_factors.extend(age_result)
                if security_level == SecurityLevel.SAFE:
                    security_level = SecurityLevel.MODERATE
            
            # Check 5: File size verification
            size_result = self._check_file_size(file_path)
            if size_result:
                risk_factors.extend(size_result)
                if security_level == SecurityLevel.SAFE:
                    security_level = SecurityLevel.MODERATE
            
            # Check 6: Process usage verification
            process_result = self._check_file_in_use(file_path)
            if process_result:
                risk_factors.extend(process_result)
                security_level = SecurityLevel.HIGH_RISK
            
            # Check 7: Content analysis for text files
            content_result = self._check_file_content(file_path)
            if content_result:
                risk_factors.extend(content_result)
                if security_level == SecurityLevel.SAFE:
                    security_level = SecurityLevel.MODERATE
            
            # Generate recommendations based on security level
            recommendations = self._generate_recommendations(security_level, file_path)
            
            # Final safety determination
            is_safe = security_level in [SecurityLevel.SAFE, SecurityLevel.MODERATE]
            
            return SecurityResult(
                is_safe=is_safe,
                security_level=security_level,
                risk_factors=risk_factors,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Security check failed for {file_path}: {e}")
            return SecurityResult(
                is_safe=False,
                security_level=SecurityLevel.CRITICAL,
                risk_factors=[f"Security check error: {e}"],
                recommendations=["Skip file due to check error"]
            )
    
    def _check_critical_directories(self, file_path: Path) -> List[str]:
        """Check if file is in critical system directories."""
        risk_factors = []
        
        try:
            file_str = str(file_path.absolute()).upper()
            
            for critical_dir in self.critical_directories:
                if file_str.startswith(critical_dir.upper()):
                    risk_factors.append(f"File in critical system directory: {critical_dir}")
            
        except Exception as e:
            risk_factors.append(f"Directory check error: {e}")
        
        return risk_factors
    
    def _check_critical_patterns(self, file_path: Path) -> List[str]:
        """Check if file matches critical patterns."""
        risk_factors = []
        
        try:
            file_name = file_path.name.lower()
            
            for pattern in self.critical_patterns:
                if re.match(pattern, file_name, re.IGNORECASE):
                    risk_factors.append(f"Matches critical pattern: {pattern}")
            
        except Exception as e:
            risk_factors.append(f"Pattern check error: {e}")
        
        return risk_factors
    
    def _check_file_extension(self, file_path: Path) -> Tuple[List[str], SecurityLevel]:
        """Check file extension for risk assessment."""
        risk_factors = []
        security_level = SecurityLevel.SAFE
        
        try:
            extension = file_path.suffix.lower()
            
            if extension in self.high_risk_extensions:
                risk_factors.append(f"High-risk extension: {extension}")
                security_level = SecurityLevel.HIGH_RISK
            elif extension in self.safe_temp_extensions:
                # Safe temporary file
                pass
            elif extension == "":
                risk_factors.append("No file extension")
                security_level = SecurityLevel.MODERATE
            else:
                # Unknown extension - moderate risk
                risk_factors.append(f"Unknown extension: {extension}")
                security_level = SecurityLevel.MODERATE
            
        except Exception as e:
            risk_factors.append(f"Extension check error: {e}")
            security_level = SecurityLevel.HIGH_RISK
        
        return risk_factors, security_level
    
    def _check_file_age(self, file_path: Path) -> List[str]:
        """Check if file is old enough to be safely deleted."""
        risk_factors = []
        
        try:
            file_stat = file_path.stat()
            current_time = time.time()
            
            # Check modification time
            file_age = current_time - file_stat.st_mtime
            if file_age < self.min_file_age_seconds:
                minutes_old = file_age / 60
                risk_factors.append(f"File too recent: {minutes_old:.1f} minutes old")
            
            # Check access time  
            access_age = current_time - file_stat.st_atime
            if access_age < 600:  # 10 minutes
                risk_factors.append(f"File recently accessed: {access_age/60:.1f} minutes ago")
            
        except Exception as e:
            risk_factors.append(f"Age check error: {e}")
        
        return risk_factors
    
    def _check_file_size(self, file_path: Path) -> List[str]:
        """Check file size for safety."""
        risk_factors = []
        
        try:
            file_size = file_path.stat().st_size
            
            if file_size > self.max_safe_file_size:
                risk_factors.append(f"Large file size: {format_bytes(file_size)}")
            elif file_size == 0:
                risk_factors.append("Empty file")
            
        except Exception as e:
            risk_factors.append(f"Size check error: {e}")
        
        return risk_factors
    
    def _check_file_in_use(self, file_path: Path) -> List[str]:
        """Check if file is currently in use by processes."""
        risk_factors = []
        
        try:
            file_str = str(file_path.absolute())
            
            # Check all running processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Skip protected processes
                    proc_name = proc.info['name']
                    if proc_name in self.protected_processes:
                        continue
                    
                    # Check if process has file open
                    for file_obj in proc.open_files():
                        if file_obj.path.upper() == file_str.upper():
                            risk_factors.append(f"File in use by process: {proc_name} (PID: {proc.info['pid']})")
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process terminated or access denied - skip
                    continue
                except Exception:
                    # Other errors - skip
                    continue
        
        except Exception as e:
            # Don't add risk factor for process check errors - too common
            self.logger.debug(f"Process check error for {file_path}: {e}")
        
        return risk_factors
    
    def _check_file_content(self, file_path: Path) -> List[str]:
        """Analyze file content for text files."""
        risk_factors = []
        
        try:
            # Only check small text files
            if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                return risk_factors
            
            # Try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1024)  # Read first 1KB
                    
                    # Check for configuration-like content
                    config_indicators = [
                        'config', 'setting', 'registry', 'key=', 'value=',
                        'password', 'token', 'secret', 'api_key'
                    ]
                    
                    content_lower = content.lower()
                    for indicator in config_indicators:
                        if indicator in content_lower:
                            risk_factors.append(f"Contains {indicator}-like content")
                            break
                            
            except (UnicodeDecodeError, PermissionError):
                # Not a text file or can't read - skip content check
                pass
        
        except Exception as e:
            # Content check errors are not critical
            self.logger.debug(f"Content check error for {file_path}: {e}")
        
        return risk_factors
    
    def _generate_recommendations(self, security_level: SecurityLevel, file_path: Path) -> List[str]:
        """Generate recommendations based on security level."""
        recommendations = []
        
        if security_level == SecurityLevel.SAFE:
            recommendations.append("Safe to delete without backup")
        elif security_level == SecurityLevel.MODERATE:
            recommendations.append("Safe to delete with backup")
            recommendations.append("Verify file is not needed before deletion")
        elif security_level == SecurityLevel.HIGH_RISK:
            recommendations.append("Requires special handling")
            recommendations.append("Create backup before any action")
            recommendations.append("Manual verification recommended")
        else:  # CRITICAL
            recommendations.append("DO NOT DELETE")
            recommendations.append("Critical system file or high-risk content")
        
        return recommendations
    
    def batch_security_check(self, file_paths: List[Path]) -> Dict[str, SecurityResult]:
        """
        Perform security checks on multiple files.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            Dictionary mapping file paths to security results
        """
        results = {}
        
        for file_path in file_paths:
            try:
                result = self.check_file_security(file_path)
                results[str(file_path)] = result
            except Exception as e:
                self.logger.error(f"Batch security check failed for {file_path}: {e}")
                results[str(file_path)] = SecurityResult(
                    is_safe=False,
                    security_level=SecurityLevel.CRITICAL,
                    risk_factors=[f"Batch check error: {e}"],
                    recommendations=["Skip due to error"]
                )
        
        return results
    
    def get_security_summary(self, results: Dict[str, SecurityResult]) -> Dict:
        """Generate summary of security check results."""
        summary = {
            'total_files': len(results),
            'safe_files': 0,
            'moderate_files': 0,
            'high_risk_files': 0,
            'critical_files': 0,
            'common_risk_factors': {},
            'recommendations': []
        }
        
        # Count security levels
        for result in results.values():
            if result.security_level == SecurityLevel.SAFE:
                summary['safe_files'] += 1
            elif result.security_level == SecurityLevel.MODERATE:
                summary['moderate_files'] += 1
            elif result.security_level == SecurityLevel.HIGH_RISK:
                summary['high_risk_files'] += 1
            else:
                summary['critical_files'] += 1
            
            # Count risk factors
            for risk_factor in result.risk_factors:
                if risk_factor in summary['common_risk_factors']:
                    summary['common_risk_factors'][risk_factor] += 1
                else:
                    summary['common_risk_factors'][risk_factor] = 1
        
        # Generate general recommendations
        if summary['critical_files'] > 0:
            summary['recommendations'].append("Review critical files before any operations")
        if summary['high_risk_files'] > 0:
            summary['recommendations'].append("Handle high-risk files with extra caution")
        if summary['moderate_files'] > 0:
            summary['recommendations'].append("Use backup for moderate-risk files")
        
        return summary