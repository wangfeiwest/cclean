#!/usr/bin/env python3
"""
系统优化器 - 深度系统性能优化
专门优化Windows系统性能，清理系统垃圾，提升运行速度
"""

import os
import sys
import time
import subprocess
import winreg
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

# Add the cclean package to the path
sys.path.insert(0, os.path.dirname(__file__))

from cclean.config import CleanupResult, format_bytes

class SystemOptimizer:
    """系统优化器 - 深度系统性能优化"""
    
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
    
    def optimize_windows_search(self) -> CleanupResult:
        """优化Windows搜索索引"""
        self.logger.info("开始优化Windows搜索索引...")
        
        result = CleanupResult()
        
        # Windows搜索相关路径
        search_paths = [
            Path(os.path.expandvars(r'%PROGRAMDATA%\Microsoft\Search\Data\Applications\Windows')),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\WebCache')),
            Path(os.path.expandvars(r'%PROGRAMDATA%\Microsoft\Search\Data\Temp')),
        ]
        
        total_deleted = 0
        total_bytes = 0
        
        for search_path in search_paths:
            if search_path.exists():
                try:
                    # 清理搜索索引文件
                    for item in search_path.rglob('*'):
                        if item.is_file() and item.suffix.lower() in ['.log', '.edb', '.chk']:
                            try:
                                size = item.stat().st_size
                                item.unlink()
                                total_deleted += 1
                                total_bytes += size
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue
        
        # 重建搜索索引（可选）
        try:
            subprocess.run(['sc', 'stop', 'WSearch'], capture_output=True, timeout=30)
            time.sleep(2)
            subprocess.run(['sc', 'start', 'WSearch'], capture_output=True, timeout=30)
            self.logger.info("Windows搜索服务已重启")
        except Exception as e:
            self.logger.warning(f"重启搜索服务失败: {e}")
        
        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True
        
        return result
    
    def optimize_windows_update(self) -> CleanupResult:
        """优化Windows更新缓存"""
        self.logger.info("开始优化Windows更新缓存...")
        
        result = CleanupResult()
        
        # Windows更新相关路径
        update_paths = [
            Path(r'C:\Windows\SoftwareDistribution\Download'),
            Path(r'C:\Windows\SoftwareDistribution\DataStore\Logs'),
            Path(r'C:\Windows\System32\catroot2'),
        ]
        
        total_deleted = 0
        total_bytes = 0
        
        # 停止Windows更新服务
        try:
            subprocess.run(['net', 'stop', 'wuauserv'], capture_output=True, timeout=30)
            subprocess.run(['net', 'stop', 'cryptSvc'], capture_output=True, timeout=30)
            subprocess.run(['net', 'stop', 'bits'], capture_output=True, timeout=30)
            subprocess.run(['net', 'stop', 'msiserver'], capture_output=True, timeout=30)
            time.sleep(2)
        except Exception as e:
            self.logger.warning(f"停止更新服务失败: {e}")
        
        # 清理更新缓存
        for update_path in update_paths:
            if update_path.exists():
                try:
                    for item in update_path.rglob('*'):
                        if item.is_file():
                            try:
                                size = item.stat().st_size
                                item.unlink()
                                total_deleted += 1
                                total_bytes += size
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue
        
        # 重启Windows更新服务
        try:
            subprocess.run(['net', 'start', 'wuauserv'], capture_output=True, timeout=30)
            subprocess.run(['net', 'start', 'cryptSvc'], capture_output=True, timeout=30)
            subprocess.run(['net', 'start', 'bits'], capture_output=True, timeout=30)
            subprocess.run(['net', 'start', 'msiserver'], capture_output=True, timeout=30)
            self.logger.info("Windows更新服务已重启")
        except Exception as e:
            self.logger.warning(f"重启更新服务失败: {e}")
        
        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True
        
        return result
    
    def optimize_prefetch(self) -> CleanupResult:
        """优化预读取文件"""
        self.logger.info("开始优化预读取文件...")
        
        result = CleanupResult()
        
        prefetch_path = Path(r'C:\Windows\Prefetch')
        
        if prefetch_path.exists():
            total_deleted = 0
            total_bytes = 0
            
            try:
                # 保留最近30天的预读取文件，删除旧的
                cutoff_time = time.time() - (30 * 24 * 3600)  # 30天前
                
                for pf_file in prefetch_path.glob('*.pf'):
                    try:
                        if pf_file.stat().st_mtime < cutoff_time:
                            size = pf_file.stat().st_size
                            pf_file.unlink()
                            total_deleted += 1
                            total_bytes += size
                    except (OSError, PermissionError):
                        continue
                        
            except (OSError, PermissionError):
                pass
            
            result.files_deleted = total_deleted
            result.bytes_freed = total_bytes
        
        result.success = True
        return result
    
    def optimize_event_logs(self) -> CleanupResult:
        """优化事件日志"""
        self.logger.info("开始优化事件日志...")
        
        result = CleanupResult()
        
        # 清理事件日志（需要管理员权限）
        log_commands = [
            'wevtutil cl Application',
            'wevtutil cl System',
            'wevtutil cl Security',
            'wevtutil cl Setup',
            'wevtutil cl "Windows PowerShell"',
        ]
        
        cleared_logs = 0
        
        for command in log_commands:
            try:
                result_cmd = subprocess.run(command, shell=True, capture_output=True, timeout=30)
                if result_cmd.returncode == 0:
                    cleared_logs += 1
                    self.logger.info(f"已清理事件日志: {command.split()[-1]}")
            except Exception as e:
                self.logger.warning(f"清理事件日志失败 {command}: {e}")
        
        result.files_deleted = cleared_logs
        result.success = True
        
        return result
    
    def optimize_dns_cache(self) -> CleanupResult:
        """优化DNS缓存"""
        self.logger.info("开始优化DNS缓存...")
        
        result = CleanupResult()
        
        try:
            # 清理DNS缓存
            subprocess.run(['ipconfig', '/flushdns'], capture_output=True, timeout=30)
            self.logger.info("DNS缓存已清理")
            result.files_deleted = 1
            result.success = True
        except Exception as e:
            self.logger.warning(f"清理DNS缓存失败: {e}")
            result.success = False
        
        return result
    
    def optimize_font_cache(self) -> CleanupResult:
        """优化字体缓存"""
        self.logger.info("开始优化字体缓存...")
        
        result = CleanupResult()
        
        font_cache_files = [
            Path(r'C:\Windows\System32\FNTCACHE.DAT'),
            Path(r'C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache\*'),
        ]
        
        total_deleted = 0
        total_bytes = 0
        
        for font_file in font_cache_files:
            if '*' in str(font_file):
                # 处理通配符路径
                parent_dir = font_file.parent
                if parent_dir.exists():
                    try:
                        for item in parent_dir.glob(font_file.name):
                            if item.is_file():
                                size = item.stat().st_size
                                item.unlink()
                                total_deleted += 1
                                total_bytes += size
                    except (OSError, PermissionError):
                        continue
            else:
                # 处理单个文件
                if font_file.exists():
                    try:
                        size = font_file.stat().st_size
                        font_file.unlink()
                        total_deleted += 1
                        total_bytes += size
                    except (OSError, PermissionError):
                        continue
        
        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True
        
        return result
    
    def optimize_registry_temp(self) -> CleanupResult:
        """优化注册表临时项"""
        self.logger.info("开始优化注册表临时项...")
        
        result = CleanupResult()
        
        try:
            # 清理注册表中的临时项
            temp_keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery"),
            ]
            
            cleaned_keys = 0
            
            for hkey, subkey_path in temp_keys:
                try:
                    with winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_ALL_ACCESS) as key:
                        # 获取值的数量
                        try:
                            i = 0
                            while True:
                                value_name = winreg.EnumValue(key, i)[0]
                                winreg.DeleteValue(key, value_name)
                                cleaned_keys += 1
                                i += 1
                        except WindowsError:
                            # 没有更多值了
                            pass
                            
                except WindowsError:
                    # 键不存在或无法访问
                    continue
            
            result.files_deleted = cleaned_keys
            result.success = True
            self.logger.info(f"清理了 {cleaned_keys} 个注册表项")
            
        except Exception as e:
            result.error_message = f"注册表清理失败: {e}"
            self.logger.error(f"注册表清理失败: {e}")
        
        return result

    def optimize_memory_dumps(self) -> CleanupResult:
        """优化内存转储文件"""
        self.logger.info("开始优化内存转储文件...")

        result = CleanupResult()

        dump_paths = [
            Path(r'C:\Windows\Minidump'),
            Path(r'C:\Windows\memory.dmp'),
            Path(r'C:\Windows\MEMORY.DMP'),
            Path(os.path.expandvars(r'%LOCALAPPDATA%\CrashDumps')),
        ]

        total_deleted = 0
        total_bytes = 0

        for dump_path in dump_paths:
            if dump_path.is_file():
                # 单个文件
                try:
                    size = dump_path.stat().st_size
                    dump_path.unlink()
                    total_deleted += 1
                    total_bytes += size
                except (OSError, PermissionError):
                    continue
            elif dump_path.is_dir():
                # 目录中的所有转储文件
                try:
                    for dump_file in dump_path.glob('*.dmp'):
                        try:
                            size = dump_file.stat().st_size
                            dump_file.unlink()
                            total_deleted += 1
                            total_bytes += size
                        except (OSError, PermissionError):
                            continue
                except (OSError, PermissionError):
                    continue

        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True

        return result

    def optimize_performance_logs(self) -> CleanupResult:
        """优化性能监视器日志"""
        self.logger.info("开始优化性能监视器日志...")

        result = CleanupResult()

        perf_log_paths = [
            Path(r'C:\Windows\System32\LogFiles\WMI'),
            Path(r'C:\Windows\System32\LogFiles\Sum'),
            Path(r'C:\PerfLogs'),
        ]

        total_deleted = 0
        total_bytes = 0

        for log_path in perf_log_paths:
            if log_path.exists():
                try:
                    for item in log_path.rglob('*'):
                        if item.is_file() and item.suffix.lower() in ['.etl', '.blg', '.csv', '.log']:
                            try:
                                size = item.stat().st_size
                                item.unlink()
                                total_deleted += 1
                                total_bytes += size
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue

        result.files_deleted = total_deleted
        result.bytes_freed = total_bytes
        result.success = True

        return result

    def optimize_network_cache(self) -> CleanupResult:
        """优化网络缓存"""
        self.logger.info("开始优化网络缓存...")

        result = CleanupResult()

        # 清理网络相关缓存
        commands = [
            'netsh winsock reset',
            'netsh int ip reset',
            'arp -d *',
            'nbtstat -R',
            'nbtstat -RR',
        ]

        executed_commands = 0

        for command in commands:
            try:
                subprocess.run(command, shell=True, capture_output=True, timeout=30)
                executed_commands += 1
                self.logger.info(f"执行网络优化命令: {command}")
            except Exception as e:
                self.logger.warning(f"网络优化命令失败 {command}: {e}")

        result.files_deleted = executed_commands
        result.success = True

        return result

    def perform_system_optimization(self) -> Dict[str, CleanupResult]:
        """执行完整的系统优化"""
        self.logger.info("开始完整的系统优化...")

        optimization_results = {}

        # 系统优化任务列表
        optimization_tasks = [
            ("Windows搜索优化", self.optimize_windows_search),
            ("Windows更新优化", self.optimize_windows_update),
            ("预读取文件优化", self.optimize_prefetch),
            ("事件日志优化", self.optimize_event_logs),
            ("DNS缓存优化", self.optimize_dns_cache),
            ("字体缓存优化", self.optimize_font_cache),
            ("注册表临时项优化", self.optimize_registry_temp),
            ("内存转储优化", self.optimize_memory_dumps),
            ("性能日志优化", self.optimize_performance_logs),
            ("网络缓存优化", self.optimize_network_cache),
        ]

        for task_name, task_func in optimization_tasks:
            try:
                self.logger.info(f"执行 {task_name}...")
                result = task_func()
                optimization_results[task_name] = result

                if result.files_deleted > 0:
                    self.logger.info(f"{task_name} 完成: 处理 {result.files_deleted:,} 项, 释放 {format_bytes(result.bytes_freed)}")
                else:
                    self.logger.info(f"{task_name} 完成: 没有找到需要优化的内容")

            except Exception as e:
                self.logger.error(f"{task_name} 失败: {e}")
                optimization_results[task_name] = CleanupResult(success=False, error_message=str(e))

        return optimization_results
