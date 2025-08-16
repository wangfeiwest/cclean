#!/usr/bin/env python3
"""
优化版C盘清理器 - 高性能中文版
专注于速度优化和用户体验
"""

import os
import sys
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional

# Add the cclean package to the path
sys.path.insert(0, os.path.dirname(__file__))

from cclean.cleaner import CCleaner
from cclean.config import CleanupType, format_bytes, CleanupResult
from cclean.logger import CCleanLogger
from cclean.utils import get_free_disk_space, find_files, safe_delete_file

class OptimizedCleaner:
    """优化的清理器类，专注于性能提升"""
    
    def __init__(self, logger):
        self.logger = logger
        self.base_cleaner = CCleaner(logger)
        self.progress_callback = None
        self.stop_requested = False
        
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
        self.base_cleaner.set_progress_callback(callback)
    
    def _update_progress(self, message: str, current: int, total: int):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
    
    def _parallel_file_cleanup(self, files: List[Path], operation_name: str) -> CleanupResult:
        """并行文件清理，提升性能"""
        result = CleanupResult()
        
        if not files:
            return result
        
        # 按文件大小排序，优先处理大文件
        files_with_size = []
        for file_path in files:
            try:
                size = file_path.stat().st_size
                files_with_size.append((file_path, size))
            except (OSError, FileNotFoundError):
                continue
        
        # 按大小降序排列
        files_with_size.sort(key=lambda x: x[1], reverse=True)
        sorted_files = [f[0] for f in files_with_size]
        
        total_files = len(sorted_files)
        processed_files = 0
        deleted_files = 0
        total_bytes_freed = 0
        
        # 使用线程池并行处理
        max_workers = min(16, total_files, os.cpu_count() * 2)
        
        def process_file(file_path: Path) -> Tuple[bool, int]:
            """处理单个文件"""
            try:
                file_size = file_path.stat().st_size
                if safe_delete_file(str(file_path)):
                    return True, file_size
                return False, 0
            except Exception:
                return False, 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(process_file, file_path): file_path 
                for file_path in sorted_files
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_file, timeout=300):  # 5分钟超时
                try:
                    success, bytes_freed = future.result(timeout=5)  # 单个文件5秒超时
                    processed_files += 1
                    
                    if success:
                        deleted_files += 1
                        total_bytes_freed += bytes_freed
                    
                    # 更新进度（每10个文件更新一次以减少开销）
                    if processed_files % 10 == 0 or processed_files == total_files:
                        self._update_progress(
                            f"{operation_name} - 已删除 {deleted_files} 个文件",
                            processed_files,
                            total_files
                        )
                    
                except Exception as e:
                    self.logger.warning(f"文件处理失败: {e}")
                    processed_files += 1
        
        result.files_scanned = total_files
        result.files_deleted = deleted_files
        result.bytes_freed = total_bytes_freed
        result.success = True
        
        return result
    
    def fast_temp_cleanup(self) -> CleanupResult:
        """快速临时文件清理"""
        self.logger.info("开始快速临时文件清理...")
        
        # 高优先级临时文件路径
        priority_paths = [
            os.path.expandvars(r"%TEMP%"),
            os.path.expandvars(r"%TMP%"),
            os.path.expandvars(r"%LOCALAPPDATA%\Temp"),
            os.path.expandvars(r"%WINDIR%\Temp"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INetCache"),
        ]
        
        all_files = []
        
        # 快速扫描文件
        for temp_path in priority_paths:
            if os.path.exists(temp_path):
                try:
                    for file_path in find_files(temp_path, max_files=5000):
                        # 只处理超过1小时的文件
                        try:
                            if time.time() - file_path.stat().st_mtime > 3600:
                                all_files.append(file_path)
                        except (OSError, FileNotFoundError):
                            continue
                except Exception as e:
                    self.logger.warning(f"扫描路径失败 {temp_path}: {e}")
        
        return self._parallel_file_cleanup(all_files, "临时文件清理")
    
    def fast_browser_cleanup(self) -> CleanupResult:
        """快速浏览器缓存清理"""
        self.logger.info("开始快速浏览器缓存清理...")
        
        # 浏览器缓存路径
        browser_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache"),
            os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles"),
            os.path.expandvars(r"%LOCALAPPDATA%\Opera Software\Opera Stable\Cache"),
        ]
        
        all_files = []
        
        for browser_path in browser_paths:
            if os.path.exists(browser_path):
                try:
                    for file_path in find_files(browser_path, max_files=3000):
                        all_files.append(file_path)
                except Exception as e:
                    self.logger.warning(f"扫描浏览器路径失败 {browser_path}: {e}")
        
        return self._parallel_file_cleanup(all_files, "浏览器缓存清理")
    
    def smart_cleanup(self, cleanup_type: CleanupType) -> CleanupResult:
        """智能清理，根据类型选择最优策略"""
        if cleanup_type == CleanupType.TEMP_FILES:
            return self.fast_temp_cleanup()
        elif cleanup_type == CleanupType.BROWSER_CACHE:
            return self.fast_browser_cleanup()
        else:
            # 对于其他类型，使用基础清理器
            cleanup_functions = {
                CleanupType.SYSTEM_FILES: self.base_cleaner.clean_system_files,
                CleanupType.DEVELOPMENT_FILES: self.base_cleaner.clean_development_files,
                CleanupType.MEDIA_FILES: self.base_cleaner.clean_media_files,
                CleanupType.GAMING_FILES: self.base_cleaner.clean_gaming_files,
                CleanupType.SYSTEM_OPTIMIZATION: self.base_cleaner.clean_system_optimization,
                CleanupType.RECYCLE_BIN: self.base_cleaner.clean_recycle_bin,
            }
            
            cleanup_function = cleanup_functions.get(cleanup_type)
            if cleanup_function:
                return cleanup_function()
            else:
                return CleanupResult(success=False, error_message=f"不支持的清理类型: {cleanup_type}")

def print_performance_banner():
    """打印性能优化横幅"""
    print("=" * 80)
    print("🚀 超级优化版C盘清理工具 v4.0")
    print("   ⚡ 多线程并行 | 🎯 智能优先级 | 🛡️ 安全保护 | 🇨🇳 中文界面")
    print("=" * 80)
    print()

def display_optimized_categories():
    """显示优化的清理分类"""
    categories = [
        ("1", "🔥 快速临时文件", "优化算法，快速清理系统临时文件"),
        ("2", "🌐 快速浏览器缓存", "并行清理所有浏览器缓存"),
        ("3", "🗂️ 系统文件", "Windows日志和系统缓存"),
        ("4", "💻 开发工具", "IDE缓存、构建产物"),
        ("5", "📁 媒体下载", "未完成下载、媒体缓存"),
        ("6", "🎮 游戏平台", "Steam、Epic等游戏缓存"),
        ("7", "⚙️ 系统优化", "Windows搜索、更新缓存"),
        ("8", "🗑️ 回收站", "清空回收站"),
        ("9", "🚀 智能全面清理", "使用最优算法清理所有分类")
    ]
    
    print("📋 优化清理分类（按性能排序）：")
    print("-" * 70)
    for num, name, desc in categories:
        print(f"  {num}. {name:<18} - {desc}")
    print()

if __name__ == "__main__":
    print_performance_banner()
    display_optimized_categories()
    
    print("💡 提示：选择 1 或 2 可体验最快的清理速度！")
    print()
