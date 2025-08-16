#!/usr/bin/env python3
"""
超级清理器 - 最激进的磁盘空间释放
专门针对大文件和占用空间最多的垃圾文件
"""

import os
import sys
import time
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

# Add the cclean package to the path
sys.path.insert(0, os.path.dirname(__file__))

from cclean.config import CleanupResult, format_bytes

class SuperCleaner:
    """超级清理器 - 最激进的空间释放策略"""
    
    def __init__(self, logger):
        self.logger = logger
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """设置进度回调"""
        self.progress_callback = callback
    
    def _update_progress(self, message: str, current: int, total: int):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
    
    def _force_delete_directory(self, dir_path: Path) -> Tuple[bool, int]:
        """强制删除目录及其所有内容"""
        try:
            if not dir_path.exists():
                return True, 0
            
            # 计算目录大小
            total_size = 0
            for item in dir_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, FileNotFoundError):
                        pass
            
            # 强制删除整个目录
            shutil.rmtree(str(dir_path), ignore_errors=True)
            
            # 验证删除是否成功
            if not dir_path.exists():
                return True, total_size
            else:
                return False, 0
                
        except Exception as e:
            self.logger.warning(f"强制删除目录失败 {dir_path}: {e}")
            return False, 0
    
    def nuclear_temp_cleanup(self) -> CleanupResult:
        """核弹级临时文件清理 - 删除所有临时目录"""
        self.logger.info("开始核弹级临时文件清理...")
        
        result = CleanupResult()
        
        # 要完全清空的临时目录
        temp_directories = [
            Path(os.path.expandvars(r'%TEMP%')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Temp')),
            Path(r'C:\Windows\Temp'),
            Path(os.path.expandvars(r'%USERPROFILE%\AppData\Local\Temp')),
        ]
        
        total_deleted = 0
        total_bytes = 0
        
        for temp_dir in temp_directories:
            if temp_dir.exists():
                try:
                    # 删除目录中的所有内容，但保留目录本身
                    for item in temp_dir.iterdir():
                        try:
                            if item.is_file():
                                size = item.stat().st_size
                                item.unlink()
                                total_deleted += 1
                                total_bytes += size
                            elif item.is_dir():
                                success, size = self._force_delete_directory(item)
                                if success:
                                    total_deleted += 1
                                    total_bytes += size
                        except (OSError, PermissionError):
                            continue
                            
                    self._update_progress(f"清理 {temp_dir.name}", total_deleted, total_deleted + 100)
                    
                except (OSError, PermissionError) as e:
                    self.logger.warning(f"无法访问临时目录 {temp_dir}: {e}")
        
        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True
        
        return result
    
    def nuclear_browser_cleanup(self) -> CleanupResult:
        """核弹级浏览器清理 - 删除所有浏览器数据"""
        self.logger.info("开始核弹级浏览器清理...")
        
        result = CleanupResult()
        
        # 浏览器数据目录
        browser_dirs = [
            # Chrome
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\GPUCache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Service Worker')),
            
            # Edge
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache')),
            
            # Firefox
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Mozilla\Firefox\Profiles')),
            Path(os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles')),
            
            # IE/Edge Legacy
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\INetCache')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\WebCache')),
        ]
        
        total_deleted = 0
        total_bytes = 0
        
        for browser_dir in browser_dirs:
            if browser_dir.exists():
                success, size = self._force_delete_directory(browser_dir)
                if success:
                    total_deleted += 1
                    total_bytes += size
                    self._update_progress(f"清理 {browser_dir.name}", total_deleted, len(browser_dirs))
        
        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True
        
        return result
    
    def nuclear_system_cleanup(self) -> CleanupResult:
        """核弹级系统清理 - 清理所有系统垃圾"""
        self.logger.info("开始核弹级系统清理...")
        
        result = CleanupResult()
        
        # 系统垃圾目录
        system_dirs = [
            Path(r'C:\Windows\SoftwareDistribution\Download'),
            Path(r'C:\Windows\Logs'),
            Path(r'C:\Windows\Prefetch'),
            Path(r'C:\Windows\LiveKernelReports'),
            Path(r'C:\Windows\System32\LogFiles'),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\WER')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\CrashDumps')),
        ]
        
        # 单个大文件
        system_files = [
            Path(r'C:\Windows\memory.dmp'),
            Path(r'C:\Windows\MEMORY.DMP'),
            Path(os.path.expandvars(r'%WINDIR%\System32\FNTCACHE.DAT')),
        ]
        
        total_deleted = 0
        total_bytes = 0
        
        # 清理目录
        for system_dir in system_dirs:
            if system_dir.exists():
                success, size = self._force_delete_directory(system_dir)
                if success:
                    total_deleted += 1
                    total_bytes += size
                    # 重新创建空目录（某些目录需要存在）
                    try:
                        system_dir.mkdir(exist_ok=True)
                    except:
                        pass
        
        # 清理单个文件
        for system_file in system_files:
            if system_file.exists():
                try:
                    size = system_file.stat().st_size
                    system_file.unlink()
                    total_deleted += 1
                    total_bytes += size
                except (OSError, PermissionError):
                    continue
        
        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True
        
        return result
    
    def nuclear_thumbnail_cleanup(self) -> CleanupResult:
        """核弹级缩略图清理"""
        self.logger.info("开始核弹级缩略图清理...")
        
        result = CleanupResult()
        
        # 缩略图相关文件和目录
        thumbnail_items = [
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\IconCache.db')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_32.db')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_96.db')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_256.db')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_1024.db')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_idx.db')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_sr.db')),
        ]
        
        total_deleted = 0
        total_bytes = 0
        
        for item in thumbnail_items:
            if item.exists():
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        item.unlink()
                        total_deleted += 1
                        total_bytes += size
                    elif item.is_dir():
                        success, size = self._force_delete_directory(item)
                        if success:
                            total_deleted += 1
                            total_bytes += size
                            # 重新创建Explorer目录
                            if 'Explorer' in str(item):
                                item.mkdir(exist_ok=True)
                except (OSError, PermissionError):
                    continue
        
        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True
        
        return result
    
    def perform_nuclear_cleanup(self) -> dict:
        """执行核弹级清理 - 最大化释放空间"""
        self.logger.info("开始核弹级清理 - 最大化释放空间...")
        
        cleanup_results = {}
        
        # 核弹级清理任务
        nuclear_tasks = [
            ("核弹级临时文件清理", self.nuclear_temp_cleanup),
            ("核弹级浏览器清理", self.nuclear_browser_cleanup),
            ("核弹级系统清理", self.nuclear_system_cleanup),
            ("核弹级缩略图清理", self.nuclear_thumbnail_cleanup),
            ("大文件清理", self.find_and_clean_large_files),
        ]
        
        for task_name, task_func in nuclear_tasks:
            try:
                self.logger.info(f"执行 {task_name}...")
                result = task_func()
                cleanup_results[task_name] = result
                
                if result.files_deleted > 0:
                    self.logger.info(f"{task_name} 完成: 删除 {result.files_deleted:,} 项, 释放 {format_bytes(result.bytes_freed)}")
                else:
                    self.logger.info(f"{task_name} 完成: 没有找到需要清理的内容")
                    
            except Exception as e:
                self.logger.error(f"{task_name} 失败: {e}")
                cleanup_results[task_name] = CleanupResult(success=False, error_message=str(e))
        
        return cleanup_results

    def find_and_clean_large_files(self) -> CleanupResult:
        """查找并清理大文件"""
        self.logger.info("开始查找并清理大文件...")

        result = CleanupResult()

        # 搜索大文件的路径
        search_paths = [
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%LOCALAPPDATA%'),
            r'C:\Windows\Temp',
            r'C:\Windows\Logs',
            r'C:\Windows\SoftwareDistribution',
        ]

        large_files = []

        for search_path in search_paths:
            if os.path.exists(search_path):
                try:
                    for root, dirs, files in os.walk(search_path):
                        for file in files:
                            try:
                                file_path = Path(root) / file
                                if file_path.exists():
                                    file_size = file_path.stat().st_size
                                    # 查找大于50MB的文件
                                    if file_size > 50 * 1024 * 1024:
                                        large_files.append((file_path, file_size))
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue

        # 按文件大小排序，优先删除最大的文件
        large_files.sort(key=lambda x: x[1], reverse=True)

        total_deleted = 0
        total_bytes = 0

        for file_path, file_size in large_files[:20]:  # 只处理前20个最大的文件
            try:
                file_path.unlink()
                total_deleted += 1
                total_bytes += file_size
                self.logger.info(f"删除大文件: {file_path.name} ({format_bytes(file_size)})")
            except (OSError, PermissionError):
                continue

        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True

        return result
