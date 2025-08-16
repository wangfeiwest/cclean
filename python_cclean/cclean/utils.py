"""
Utility functions for CClean Python version.
Contains file operations, system utilities, and Windows-specific functions.
"""

import os
import sys
import shutil
import glob
import ctypes
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Generator, Optional, Tuple
import psutil

try:
    import win32api
    import win32security
    import win32file
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from .config import expand_environment_variables, PROTECTED_FILES, SAFE_TEMP_EXTENSIONS

def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform.startswith('win')

def has_admin_rights() -> bool:
    """Check if the current process has administrator privileges."""
    if not is_windows():
        return os.geteuid() == 0
    
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False

def request_admin_rights() -> None:
    """Request administrator privileges by restarting with UAC prompt."""
    if not is_windows():
        print("Admin elevation not supported on this platform")
        return
    
    if has_admin_rights():
        return
    
    try:
        # Get current script path
        script_path = os.path.abspath(sys.argv[0])
        
        # Build command line arguments
        args = ' '.join(sys.argv[1:])
        
        # Use ShellExecute to request elevation
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            f'"{script_path}" {args}',
            None, 
            1  # SW_SHOWNORMAL
        )
        
        sys.exit(0)
    except Exception as e:
        print(f"Failed to request admin rights: {e}")

def find_files_fast(path: str, pattern: str = "*", recursive: bool = True, max_files: Optional[int] = None, max_depth: int = 5) -> Generator[Path, None, None]:
    """
    优化的文件查找函数，提高系统文件清理速度。
    
    Args:
        path: Directory path to search
        pattern: File pattern to match (default: *)
        recursive: Whether to search recursively
        max_files: Maximum number of files to return (None for unlimited)
        max_depth: Maximum recursion depth to prevent deep scanning
    
    Yields:
        Path objects for matching files
    """
    file_count = 0
    try:
        expanded_path = expand_environment_variables(path)
        base_path = Path(expanded_path)
        
        if not base_path.exists():
            return
        
        # 快速跳过不存在或无权限的路径
        try:
            if not base_path.is_dir():
                return
        except (OSError, PermissionError):
            return
        
        # 使用os.scandir()代替Path.iterdir()提高性能
        import os
        from collections import deque
        
        dirs_to_process = deque([(base_path, 0)])  # (path, depth)
        
        while dirs_to_process and (max_files is None or file_count < max_files):
            try:
                current_dir, depth = dirs_to_process.popleft()
                
                # 限制扫描深度
                if depth >= max_depth:
                    continue
                
                # 使用scandir提高性能
                with os.scandir(str(current_dir)) as entries:
                    for entry in entries:
                        if max_files and file_count >= max_files:
                            break
                        
                        try:
                            if entry.is_file():
                                if pattern == "*" or Path(entry.name).match(pattern):
                                    yield Path(entry.path)
                                    file_count += 1
                            elif entry.is_dir() and recursive and depth < max_depth - 1:
                                # 快速跳过系统保护目录
                                if not _is_protected_system_dir(entry.name):
                                    dirs_to_process.append((Path(entry.path), depth + 1))
                        except (OSError, PermissionError):
                            continue  # 跳过无权限的文件/目录
                            
            except (OSError, PermissionError):
                continue  # 跳过无权限的目录
                
    except Exception:
        # 忽略任何其他错误，继续处理
        pass

def _is_protected_system_dir(dirname: str) -> bool:
    """检查是否为受保护的系统目录，应该跳过。"""
    protected_dirs = {
        'system32', 'syswow64', 'drivers', 'winsxs', 'system', 
        'catroot', 'catroot2', 'servicing', 'en-us', 'fonts',
        'ime', 'migwiz', 'oobe', 'setup', 'speech', 'twain_32'
    }
    return dirname.lower() in protected_dirs

def find_files(path: str, pattern: str = "*", recursive: bool = True, max_files: Optional[int] = None) -> Generator[Path, None, None]:
    """
    Find files matching pattern in the given path with timeout protection.
    
    Args:
        path: Directory path to search
        pattern: File pattern to match (default: *)
        recursive: Whether to search recursively
        max_files: Maximum number of files to return (None for unlimited)
    
    Yields:
        Path objects for matching files
    """
    file_count = 0
    try:
        expanded_path = expand_environment_variables(path)
        base_path = Path(expanded_path)
        
        if not base_path.exists():
            return
        
        # Skip if it's not a directory and doesn't contain wildcards
        if not base_path.is_dir() and '*' not in expanded_path:
            return
        
        # Handle wildcard patterns in path
        if '*' in expanded_path:
            try:
                for match_path in glob.glob(expanded_path, recursive=recursive):
                    if max_files and file_count >= max_files:
                        break
                    
                    match_base = Path(match_path)
                    if match_base.is_file():
                        yield match_base
                        file_count += 1
                    elif match_base.is_dir() and recursive:
                        # Limit recursive depth for directories
                        remaining = max_files - file_count if max_files else None
                        try:
                            for sub_file in find_files(str(match_base), pattern, False, remaining):  # Non-recursive to avoid deep nesting
                                if max_files and file_count >= max_files:
                                    break
                                yield sub_file
                                file_count += 1
                        except RecursionError:
                            pass  # Skip if too deep
            except OSError:
                pass
            return
        
        # Regular directory search with limits
        if not base_path.is_dir():
            return
            
        try:
            if recursive:
                # Use iterative approach instead of glob for better control
                from collections import deque
                dirs_to_process = deque([base_path])
                max_depth = 10  # Limit recursion depth
                current_depth = 0
                
                while dirs_to_process and current_depth < max_depth:
                    if max_files and file_count >= max_files:
                        break
                    
                    current_dir = dirs_to_process.popleft()
                    try:
                        # Process files in current directory
                        for item in current_dir.iterdir():
                            if max_files and file_count >= max_files:
                                break
                            
                            if item.is_file() and (pattern == "*" or item.match(pattern)):
                                yield item
                                file_count += 1
                            elif item.is_dir() and current_depth < max_depth - 1:
                                dirs_to_process.append(item)
                    except (OSError, PermissionError):
                        continue
                    
                    current_depth += 1
            else:
                # Non-recursive search
                for file_path in base_path.glob(pattern):
                    if max_files and file_count >= max_files:
                        break
                    if file_path.is_file():
                        yield file_path
                        file_count += 1
        except OSError:
            pass
                    
    except (OSError, PermissionError):
        # Skip paths we can't access
        pass

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes. Returns 0 if file doesn't exist or can't be accessed."""
    try:
        return file_path.stat().st_size
    except (OSError, FileNotFoundError):
        return 0

def get_directory_size(dir_path: str) -> int:
    """Calculate total size of all files in directory recursively."""
    total_size = 0
    try:
        expanded_path = expand_environment_variables(dir_path)
        for file_path in find_files(expanded_path):
            total_size += get_file_size(file_path)
    except Exception:
        pass
    return total_size

def is_file_in_use(file_path: Path) -> bool:
    """
    Check if a file is currently in use by another process.
    
    Args:
        file_path: Path to the file to check
    
    Returns:
        True if file is in use, False otherwise
    """
    try:
        # Simple method: try to rename the file to itself
        # This is less intrusive than trying to open exclusively
        temp_name = str(file_path) + ".tmp_check"
        
        # Try to rename and immediately rename back
        file_path.rename(temp_name)
        Path(temp_name).rename(file_path)
        
        return False  # File is not in use
        
    except (OSError, PermissionError, FileNotFoundError):
        # File is in use, permission denied, or doesn't exist
        return True
    except Exception:
        # Any other error - assume file is in use
        return True

def is_system_file(file_path: Path) -> bool:
    """Check if file is a system file that should not be deleted."""
    file_name = file_path.name.lower()
    
    # Check protected file names
    if file_name in [name.lower() for name in PROTECTED_FILES]:
        return True
    
    # Check if it's in system directories that we should be careful with
    try:
        path_str = str(file_path).lower()
        system_dirs = ['system32', 'syswow64', 'drivers']
        if any(sys_dir in path_str for sys_dir in system_dirs):
            # Only delete files with safe extensions from system directories
            if file_path.suffix.lower() not in SAFE_TEMP_EXTENSIONS:
                return True
    except Exception:
        return True
    
    return False

def safe_delete_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Safely delete a file with proper error handling and retry logic.
    
    Args:
        file_path: Path to the file to delete
        dry_run: If True, don't actually delete, just simulate
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if dry_run:
            return True, ""
        
        # Check if file exists
        if not file_path.exists():
            return True, ""  # Already gone
        
        # Additional safety checks
        if is_system_file(file_path):
            return False, "File is protected system file"
        
        # Skip files that are clearly in active use (less strict check)
        if _is_likely_active_file(file_path):
            return False, "File appears to be in active use"
        
        # Check if we have permission to delete
        if not _can_delete_file(file_path):
            return False, "Insufficient permissions to delete file"
        
        # Try to delete the file with enhanced retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Try to remove read-only attribute if present
                if is_windows() and attempt > 0:
                    try:
                        file_path.chmod(0o777)  # Make file writable
                    except (OSError, PermissionError):
                        pass
                
                file_path.unlink()
                return True, ""
                
            except FileNotFoundError:
                return True, ""  # File already gone, consider it success
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    # Wait longer and try again
                    import time
                    time.sleep(0.2 * (attempt + 1))
                    continue
                return False, f"Permission denied: {e}"
                
            except OSError as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.2 * (attempt + 1))
                    continue
                return False, f"OS Error: {e}"
        
        return False, "Failed after all retries"
        
    except Exception as e:
        return False, f"Unexpected error: {e}"

def _can_delete_file(file_path: Path) -> bool:
    """
    Check if we have permission to delete a file.
    
    Args:
        file_path: Path to the file to check
    
    Returns:
        True if we can delete the file, False otherwise
    """
    try:
        # Check if file exists
        if not file_path.exists():
            return True
        
        # Check parent directory write permission
        parent_dir = file_path.parent
        if not os.access(parent_dir, os.W_OK):
            return False
        
        # Check file write permission (for read-only files)
        if not os.access(file_path, os.W_OK):
            # Try to change permissions if we have admin rights
            if is_windows() and has_admin_rights():
                try:
                    file_path.chmod(0o777)
                    return True
                except (OSError, PermissionError):
                    return False
            else:
                return False
        
        return True
        
    except Exception:
        return False

def _is_likely_active_file(file_path: Path) -> bool:
    """Check if file is likely being actively used (less strict than is_file_in_use)."""
    try:
        file_name = file_path.name.lower()
        
        # Skip files with certain patterns that indicate active use
        active_patterns = [
            '.lock', '.lck', '.pid', '.running',
            'lockfile', 'lock.txt'
        ]
        
        for pattern in active_patterns:
            if pattern in file_name:
                return True
        
        # Skip files that are very recent (created in last hour)
        import time
        from .config import MIN_FILE_AGE_SECONDS
        current_time = time.time()
        try:
            file_age = current_time - file_path.stat().st_mtime
            if file_age < MIN_FILE_AGE_SECONDS:  # Default 1 hour
                return True
        except (OSError, AttributeError):
            pass
        
        return False
        
    except Exception:
        return True  # If we can't determine, assume it's active

def is_safe_to_delete(file_path: Path) -> bool:
    """
    Determine if a file is safe to delete based on multiple criteria.
    
    Args:
        file_path: Path to the file to check
    
    Returns:
        True if file is safe to delete, False otherwise
    """
    try:
        from .config import SAFE_TEMP_EXTENSIONS, MIN_FILE_AGE_SECONDS
        import time
        
        # Basic safety checks
        if is_system_file(file_path):
            return False
            
        if _is_likely_active_file(file_path):
            return False
        
        file_name = file_path.name.lower()
        file_ext = file_path.suffix.lower()
        
        # Check if file extension is in safe list
        if file_ext in SAFE_TEMP_EXTENSIONS:
            return True
            
        # Check for safe patterns in temp directories
        if any(temp_dir in str(file_path).lower() for temp_dir in ['temp', 'tmp', 'cache']):
            # Additional patterns that are usually safe in temp directories
            safe_patterns = [
                file_name.startswith('tmp'),
                file_name.startswith('~'),
                file_name.startswith('_'),
                '.tmp' in file_name,
                '.temp' in file_name,
                '.cache' in file_name,
                '.bak' in file_name,
                '.old' in file_name
            ]
            
            if any(safe_patterns):
                # Check file age - only delete if older than minimum age
                try:
                    file_age = time.time() - file_path.stat().st_mtime
                    return file_age >= MIN_FILE_AGE_SECONDS
                except (OSError, AttributeError):
                    return False
        
        # For other locations, be more conservative
        return file_ext in SAFE_TEMP_EXTENSIONS and file_path.stat().st_size < 100 * 1024 * 1024  # < 100MB
        
    except Exception:
        return False  # If in doubt, don't delete

def safe_delete_directory(dir_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Safely delete a directory and all its contents.
    
    Args:
        dir_path: Path to the directory to delete
        dry_run: If True, don't actually delete, just simulate
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        if dry_run:
            return True, ""
        
        if not dir_path.exists():
            return True, ""
        
        shutil.rmtree(str(dir_path), ignore_errors=True)
        return True, ""
        
    except PermissionError:
        return False, "Permission denied"
    except OSError as e:
        return False, f"OS Error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def empty_recycle_bin(dry_run: bool = False) -> Tuple[bool, str]:
    """
    Empty the Windows Recycle Bin.
    
    Args:
        dry_run: If True, don't actually empty, just simulate
    
    Returns:
        Tuple of (success, error_message)
    """
    if not is_windows():
        return False, "Recycle bin operations only supported on Windows"
    
    try:
        if dry_run:
            return True, ""
        
        # Use Windows API to empty recycle bin
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(
            None,  # hwnd
            None,  # pszRootPath (all drives)
            0x0001 | 0x0002 | 0x0004  # SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        )
        
        if result == 0:  # S_OK
            return True, ""
        else:
            return False, f"SHEmptyRecycleBin failed with code: {result}"
            
    except Exception as e:
        return False, f"Failed to empty recycle bin: {e}"

def get_recycle_bin_size() -> int:
    """Get the total size of files in the Recycle Bin."""
    if not is_windows():
        return 0
    
    try:
        # Try to find recycle bin folders on all drives
        total_size = 0
        for drive in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            recycle_paths = [
                f"{drive}:\\$Recycle.Bin",
                f"{drive}:\\RECYCLER"  # For older Windows versions
            ]
            
            for recycle_path in recycle_paths:
                if os.path.exists(recycle_path):
                    total_size += get_directory_size(recycle_path)
                    
        return total_size
    except Exception:
        return 0

def get_current_timestamp() -> str:
    """Get current timestamp as formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def batch_check_paths(paths: List[str]) -> List[str]:
    """
    批量检查路径是否存在，提高性能。支持通配符路径。
    
    Args:
        paths: 要检查的路径列表
    
    Returns:
        存在的路径列表
    """
    existing_paths = []
    for path in paths:
        try:
            expanded_path = expand_environment_variables(path)
            
            # 检查是否包含通配符
            if '*' in expanded_path or '?' in expanded_path:
                # 对于通配符路径，检查父目录是否存在
                parent_path = Path(expanded_path).parent
                if parent_path.exists() and parent_path.is_dir():
                    # 检查是否有匹配的文件
                    try:
                        matching_files = list(parent_path.glob(Path(expanded_path).name))
                        if matching_files:
                            existing_paths.append(path)
                    except (OSError, ValueError):
                        # 如果glob失败，至少父目录存在
                        existing_paths.append(path)
            else:
                # 普通路径直接检查存在性
                if Path(expanded_path).exists():
                    existing_paths.append(path)
        except (OSError, ValueError):
            continue
    return existing_paths

def prioritize_cleanup_paths(paths: List[str]) -> List[str]:
    """
    按清理效果对路径进行优先级排序。
    
    Args:
        paths: 要排序的路径列表
    
    Returns:
        按优先级排序的路径列表
    """
    from .config import HIGH_PRIORITY_PATHS
    
    high_priority = []
    normal_priority = []
    
    for path in paths:
        is_high_priority = False
        for high_path in HIGH_PRIORITY_PATHS:
            if high_path.replace('%', '').lower() in path.lower():
                high_priority.append(path)
                is_high_priority = True
                break
        
        if not is_high_priority:
            normal_priority.append(path)
    
    # 高优先级路径在前
    return high_priority + normal_priority

def detect_project_type(directory: Path) -> list:
    """
    检测目录中的项目类型。
    
    Args:
        directory: 要检测的目录
    
    Returns:
        检测到的项目类型列表
    """
    from .config import DEVELOPMENT_CONFIG
    
    detected_types = []
    
    try:
        if not directory.exists() or not directory.is_dir():
            return detected_types
        
        # 获取目录中的文件和子目录
        items = [item.name for item in directory.iterdir()]
        
        for project_type, indicators in DEVELOPMENT_CONFIG['project_indicators'].items():
            for indicator in indicators:
                if indicator in items:
                    detected_types.append(project_type)
                    break
                    
    except (OSError, PermissionError):
        pass
    
    return detected_types

def get_development_cache_paths(base_paths: list) -> list:
    """
    扫描开发项目并返回优化的缓存清理路径。
    
    Args:
        base_paths: 基础路径列表
    
    Returns:
        优化后的开发缓存路径列表
    """
    optimized_paths = []
    common_dev_dirs = [
        'C:\\dev',
        'C:\\projects',
        'C:\\workspace',
        'C:\\src',
        str(Path.home() / 'dev'),
        str(Path.home() / 'projects'),
        str(Path.home() / 'workspace'),
        str(Path.home() / 'source'),
        str(Path.home() / 'Documents' / 'projects'),
        str(Path.home() / 'Desktop'),
    ]
    
    # 添加原始路径
    optimized_paths.extend(base_paths)
    
    # 扫描常见开发目录
    for dev_dir in common_dev_dirs:
        try:
            dev_path = Path(dev_dir)
            if dev_path.exists() and dev_path.is_dir():
                # 扫描前两层目录
                for project_dir in dev_path.iterdir():
                    if project_dir.is_dir():
                        project_types = detect_project_type(project_dir)
                        if project_types:
                            # 添加项目特定的缓存路径
                            optimized_paths.extend(_get_project_cache_paths(project_dir, project_types))
        except (OSError, PermissionError):
            continue
    
    return list(set(optimized_paths))  # 去重

def _get_project_cache_paths(project_dir: Path, project_types: list) -> list:
    """根据项目类型生成缓存路径。"""
    cache_paths = []
    
    for project_type in project_types:
        if project_type == 'node':
            cache_paths.extend([
                str(project_dir / 'node_modules' / '.cache'),
                str(project_dir / '.npm'),
                str(project_dir / '.yarn'),
                str(project_dir / 'dist'),
                str(project_dir / 'build'),
            ])
        elif project_type == 'python':
            cache_paths.extend([
                str(project_dir / '__pycache__'),
                str(project_dir / '.pytest_cache'),
                str(project_dir / 'build'),
                str(project_dir / 'dist'),
                str(project_dir / '.venv' / 'Lib' / 'site-packages'),
            ])
        elif project_type == 'java':
            cache_paths.extend([
                str(project_dir / 'target'),
                str(project_dir / 'build'),
                str(project_dir / '.gradle'),
            ])
        elif project_type == 'dotnet':
            cache_paths.extend([
                str(project_dir / 'bin'),
                str(project_dir / 'obj'),
                str(project_dir / 'packages'),
            ])
        elif project_type == 'unity':
            cache_paths.extend([
                str(project_dir / 'Library' / 'Cache'),
                str(project_dir / 'Temp'),
                str(project_dir / 'Logs'),
            ])
    
    return cache_paths

def get_development_priority_score(file_path: Path) -> int:
    """
    为开发文件计算专用优先级分数。
    
    Args:
        file_path: 文件路径
    
    Returns:
        开发工具专用优先级分数
    """
    from .config import DEVELOPMENT_CONFIG
    
    score = 0
    file_str = str(file_path).lower()
    file_name = file_path.name.lower()
    
    # 检查是否为大型开发文件
    for pattern in DEVELOPMENT_CONFIG['large_file_patterns']:
        if file_path.match(pattern.lower()):
            score += 200  # 大型包文件优先级最高
            break
    
    # 缓存优先级评分
    for priority, patterns in DEVELOPMENT_CONFIG['cache_priorities'].items():
        for pattern in patterns:
            if pattern.lower() in file_str:
                if priority == 'high':
                    score += 150
                elif priority == 'medium':
                    score += 100
                elif priority == 'low':
                    score += 50
                break
    
    # 开发工具特定路径加分
    dev_indicators = [
        'cache', 'temp', 'tmp', 'build', 'dist', 'target', 'bin', 'obj',
        'node_modules', '__pycache__', '.gradle', 'logs', 'debug', 'release'
    ]
    
    for indicator in dev_indicators:
        if indicator in file_str:
            score += 75
    
    # 文件大小加分（开发文件通常较大）
    try:
        size = file_path.stat().st_size
        if size > 50 * 1024 * 1024:  # 50MB+
            score += 100
        elif size > 10 * 1024 * 1024:  # 10MB+
            score += 75
        elif size > 1024 * 1024:  # 1MB+
            score += 50
    except (OSError, PermissionError):
        pass
    
    return score

def get_system_health_status() -> dict:
    """
    检查系统健康状态并返回详细信息。
    
    Returns:
        系统健康状态字典
    """
    health_status = {
        'overall_score': 0,
        'issues': [],
        'recommendations': [],
        'metrics': {}
    }
    
    try:
        import psutil
        import shutil
        
        # 磁盘空间检查
        disk_usage = shutil.disk_usage('C:')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        health_status['metrics']['disk_usage'] = disk_percent
        
        if disk_percent > 85:
            health_status['issues'].append('磁盘空间不足')
            health_status['recommendations'].append('清理磁盘空间或删除不需要的文件')
        
        # 内存使用率检查
        memory = psutil.virtual_memory()
        health_status['metrics']['memory_usage'] = memory.percent
        
        if memory.percent > 80:
            health_status['issues'].append('内存使用率过高')
            health_status['recommendations'].append('关闭不必要的程序或增加内存')
        
        # 临时文件大小检查
        temp_size = _get_temp_files_size()
        health_status['metrics']['temp_files_size'] = temp_size
        
        if temp_size > 1024 * 1024 * 1024:  # 1GB
            health_status['issues'].append('临时文件过多')
            health_status['recommendations'].append('清理临时文件和缓存')
        
        # 启动程序数量检查（简化版）
        try:
            boot_time = psutil.boot_time()
            current_time = time.time()
            uptime_hours = (current_time - boot_time) / 3600
            health_status['metrics']['uptime_hours'] = uptime_hours
            
            if uptime_hours > 168:  # 一周
                health_status['issues'].append('系统运行时间过长')
                health_status['recommendations'].append('重启系统以释放内存和优化性能')
        except Exception:
            pass
        
        # 计算总体健康分数
        issues_count = len(health_status['issues'])
        if issues_count == 0:
            health_status['overall_score'] = 100
        elif issues_count == 1:
            health_status['overall_score'] = 80
        elif issues_count == 2:
            health_status['overall_score'] = 60
        else:
            health_status['overall_score'] = 40
            
    except Exception as e:
        health_status['issues'].append(f'系统检查出错: {e}')
        health_status['overall_score'] = 50
    
    return health_status

def _get_temp_files_size() -> int:
    """计算临时文件总大小。"""
    total_size = 0
    temp_paths = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        'C:\\Windows\\Temp'
    ]
    
    for temp_path in temp_paths:
        if temp_path and os.path.exists(temp_path):
            try:
                for root, dirs, files in os.walk(temp_path):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue
    
    return total_size

def get_system_optimization_priority_score(file_path: Path) -> int:
    """
    为系统优化文件计算专用优先级分数。
    
    Args:
        file_path: 文件路径
    
    Returns:
        系统优化专用优先级分数
    """
    from .config import SYSTEM_OPTIMIZATION_CONFIG
    
    score = 0
    file_str = str(file_path).lower()
    file_name = file_path.name.lower()
    
    # 根据系统优化类别评分
    for priority, categories in SYSTEM_OPTIMIZATION_CONFIG['optimization_priorities'].items():
        category_score = 0
        if priority == 'critical':
            category_score = 300
        elif priority == 'high':
            category_score = 200
        elif priority == 'medium':
            category_score = 100
        elif priority == 'low':
            category_score = 50
        
        # 检查文件是否属于该类别
        for category in categories:
            if _is_file_in_optimization_category(file_path, category):
                score += category_score
                break
    
    # 文件大小加分
    try:
        size = file_path.stat().st_size
        if size > 100 * 1024 * 1024:  # 100MB+
            score += 150
        elif size > 10 * 1024 * 1024:  # 10MB+
            score += 100
        elif size > 1024 * 1024:  # 1MB+
            score += 50
    except (OSError, PermissionError):
        pass
    
    # 文件扩展名加分
    if file_name.endswith(('.log', '.tmp', '.dmp', '.etl', '.pf')):
        score += 75
    
    return score

def _is_file_in_optimization_category(file_path: Path, category: str) -> bool:
    """检查文件是否属于特定优化类别。"""
    file_str = str(file_path).lower()
    
    category_patterns = {
        'prefetch': ['prefetch', '.pf'],
        'thumbnail': ['thumbcache', 'thumbnail'],
        'icon_cache': ['iconcache', 'fntcache'],
        'log_files': ['.log', 'logs', '\\logfiles\\'],
        'crash_dumps': ['.dmp', 'minidump', 'crashdumps'],
        'search_index': ['search', 'webcache'],
        'update_cache': ['softwaredistribution', 'windowsupdate'],
        'error_reports': ['wer', 'reportqueue'],
        'temp_installer': ['installer', 'msi'],
        'driver_cache': ['driverstore', 'inf'],
        'font_cache': ['fontcache', 'fntcache'],
        'registry_backup': ['regback', 'txr'],
        'event_logs': ['.evtx', 'winevt'],
        'performance_logs': ['.etl', 'wmi', 'wdi'],
        'network_cache': ['inetcache', 'iecompat'],
        'backup_files': ['backup', '.bak'],
        'activation_cache': ['spp', 'softwareprotection'],
        'media_cache': ['media player', 'wmdb'],
        'recent_files': ['recent', 'automaticdestinations']
    }
    
    patterns = category_patterns.get(category, [])
    return any(pattern in file_str for pattern in patterns)

def is_dangerous_system_path(file_path: Path) -> bool:
    """
    检查路径是否为危险的系统路径。
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否为危险路径
    """
    from .config import SYSTEM_OPTIMIZATION_CONFIG
    
    file_str = str(file_path).lower()
    
    # 检查危险路径模式
    for dangerous_path in SYSTEM_OPTIMIZATION_CONFIG['dangerous_paths']:
        dangerous_expanded = expand_environment_variables(dangerous_path).lower()
        if dangerous_expanded in file_str:
            return True
    
    # 额外危险模式检查
    dangerous_patterns = [
        'system32\\config\\sam',
        'system32\\config\\system',
        'system32\\config\\software',
        'system32\\config\\security',
        'pagefile.sys',
        'hiberfil.sys',
        'bootmgr',
        'ntldr',
        'boot.ini'
    ]
    
    return any(pattern in file_str for pattern in dangerous_patterns)

def get_optimization_mode_paths(mode: str) -> list:
    """
    根据优化模式获取对应的清理路径。
    
    Args:
        mode: 优化模式 ('conservative', 'standard', 'aggressive', 'expert')
    
    Returns:
        对应模式的清理路径列表
    """
    from .config import SYSTEM_OPTIMIZATION_CONFIG, SYSTEM_OPTIMIZATION_PATHS
    
    if mode not in SYSTEM_OPTIMIZATION_CONFIG['performance_modes']:
        mode = 'standard'  # 默认模式
    
    mode_config = SYSTEM_OPTIMIZATION_CONFIG['performance_modes'][mode]
    include_categories = mode_config['include_categories']
    
    # 根据模式过滤路径
    filtered_paths = []
    
    for path in SYSTEM_OPTIMIZATION_PATHS:
        path_lower = path.lower()
        should_include = False
        
        # 检查路径是否属于包含的类别
        for priority in include_categories:
            categories = SYSTEM_OPTIMIZATION_CONFIG['optimization_priorities'][priority]
            for category in categories:
                if _path_matches_category(path_lower, category):
                    should_include = True
                    break
            if should_include:
                break
        
        if should_include:
            filtered_paths.append(path)
    
    return filtered_paths

def _path_matches_category(path: str, category: str) -> bool:
    """检查路径是否匹配特定类别。"""
    category_keywords = {
        'prefetch': ['prefetch'],
        'thumbnail': ['thumbcache', 'thumbnail'],
        'icon_cache': ['iconcache', 'fntcache'],
        'log_files': ['logs', '.log'],
        'crash_dumps': ['minidump', 'crashdumps', '.dmp'],
        'search_index': ['search', 'webcache'],
        'update_cache': ['softwaredistribution', 'windowsupdate'],
        'error_reports': ['wer', 'reportqueue'],
        'temp_installer': ['installer', 'msi'],
        'driver_cache': ['driverstore', 'inf'],
        'font_cache': ['fontcache'],
        'registry_backup': ['regback', 'txr'],
        'event_logs': ['winevt', '.evtx'],
        'performance_logs': ['wmi', 'wdi', '.etl'],
        'network_cache': ['inetcache', 'iecompat'],
        'backup_files': ['backup'],
        'activation_cache': ['spp'],
        'media_cache': ['media player'],
        'recent_files': ['recent', 'automaticdestinations']
    }
    
    keywords = category_keywords.get(category, [])
    return any(keyword in path for keyword in keywords)

def is_safe_development_file(file_path: Path) -> bool:
    """
    检查开发文件是否安全清理。
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否安全清理
    """
    from .config import DEVELOPMENT_CONFIG
    
    file_str = str(file_path).lower()
    
    # 检查安全跳过模式
    for pattern in DEVELOPMENT_CONFIG['safe_skip_patterns']:
        if pattern.lower() in file_str:
            return False
    
    # 额外安全检查
    unsafe_indicators = [
        '.git\\', '.svn\\', '.hg\\',  # 版本控制
        'package.json', 'composer.json', 'cargo.toml',  # 包配置
        '.env', 'config.', 'settings.',  # 配置文件
        'license', 'readme', 'changelog',  # 项目文档
        'src\\', 'source\\', 'app\\',  # 源代码目录
    ]
    
    for indicator in unsafe_indicators:
        if indicator in file_str:
            return False
    
    return True

def get_file_priority_score(file_path: Path) -> int:
    """
    根据文件扩展名和路径计算优先级分数。
    
    Args:
        file_path: 文件路径
    
    Returns:
        优先级分数（越高越优先清理）
    """
    from .config import FILE_PRIORITY_EXTENSIONS
    
    score = 0
    file_ext = file_path.suffix.lower()
    file_str = str(file_path).lower()
    
    # 扩展名得分
    if file_ext in FILE_PRIORITY_EXTENSIONS['high']:
        score += 100
    elif file_ext in FILE_PRIORITY_EXTENSIONS['medium']:
        score += 50
    elif file_ext in FILE_PRIORITY_EXTENSIONS['low']:
        score += 25
    
    # 路径得分
    if 'temp' in file_str or 'cache' in file_str:
        score += 30
    if 'log' in file_str:
        score += 20
    if 'old' in file_str or 'backup' in file_str:
        score += 15
    
    # 文件大小得分（大文件优先）
    try:
        size = file_path.stat().st_size
        if size > 10 * 1024 * 1024:  # 10MB+
            score += 50
        elif size > 1024 * 1024:  # 1MB+
            score += 25
        elif size > 100 * 1024:  # 100KB+
            score += 10
    except (OSError, PermissionError):
        pass
    
    return score

def get_large_files_first(path: str, min_size: int = 1024 * 1024) -> Generator[Path, None, None]:
    """
    优先返回大文件，提高清理效率。
    
    Args:
        path: 要扫描的路径
        min_size: 最小文件大小（字节）
    
    Yields:
        大文件路径
    """
    try:
        expanded_path = expand_environment_variables(path)
        base_path = Path(expanded_path)
        
        if not base_path.exists() or not base_path.is_dir():
            return
        
        # 收集文件大小信息
        file_sizes = []
        
        try:
            for entry in os.scandir(str(base_path)):
                if entry.is_file():
                    try:
                        size = entry.stat().st_size
                        if size >= min_size:
                            file_sizes.append((size, Path(entry.path)))
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            return
        
        # 按大小排序，大文件优先
        file_sizes.sort(reverse=True)
        
        for size, file_path in file_sizes:
            yield file_path
            
    except Exception:
        pass

def path_exists(path: str) -> bool:
    """Check if a path exists after expanding environment variables."""
    try:
        expanded_path = expand_environment_variables(path)
        return os.path.exists(expanded_path)
    except Exception:
        return False

def get_free_disk_space(drive: str = "C:") -> int:
    """Get free disk space in bytes for the specified drive."""
    try:
        if is_windows():
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(drive),
                ctypes.pointer(free_bytes),
                None,
                None
            )
            return free_bytes.value
        else:
            statvfs = os.statvfs(drive)
            return statvfs.f_frsize * statvfs.f_bavail
    except Exception:
        return 0

def get_processes_using_file(file_path: Path) -> List[str]:
    """
    Get list of process names that are using the specified file.
    
    Args:
        file_path: Path to the file to check
    
    Returns:
        List of process names using the file
    """
    processes = []
    try:
        file_path_str = str(file_path.absolute()).lower()
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Get open files for the process
                for open_file in proc.open_files():
                    if open_file.path.lower() == file_path_str:
                        processes.append(proc.info['name'])
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
    except Exception:
        pass
    
    return processes

def cleanup_empty_directories(base_path: str, dry_run: bool = False) -> int:
    """
    Remove empty directories recursively.
    
    Args:
        base_path: Base directory to start cleanup from
        dry_run: If True, don't actually delete directories
    
    Returns:
        Number of directories removed
    """
    removed_count = 0
    try:
        expanded_path = expand_environment_variables(base_path)
        base_dir = Path(expanded_path)
        
        if not base_dir.exists():
            return 0
        
        # Walk directories bottom-up to remove empty ones
        for dir_path in sorted(base_dir.rglob('*'), reverse=True):
            if dir_path.is_dir():
                try:
                    # Check if directory is empty
                    if not any(dir_path.iterdir()):
                        if not dry_run:
                            dir_path.rmdir()
                        removed_count += 1
                except (OSError, PermissionError):
                    pass
                    
    except Exception:
        pass
    
    return removed_count