#!/usr/bin/env python3
"""
深度清理器 - 激进垃圾文件清理
专门清理更多类型的垃圾文件，提升清理效果
"""

import os
import sys
import time
import glob
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

# Add the cclean package to the path
sys.path.insert(0, os.path.dirname(__file__))

from cclean.config import CleanupResult, format_bytes
from cclean.utils import safe_delete_file, safe_delete_directory

class DeepCleaner:
    """深度清理器 - 更激进的垃圾文件清理"""
    
    def __init__(self, logger):
        self.logger = logger
        self.progress_callback = None
        self.total_scanned = 0
        self.total_deleted = 0
        self.total_bytes_freed = 0
        
        # 扩展的垃圾文件扩展名列表
        self.junk_extensions = {
            # 临时文件
            '.tmp', '.temp', '.bak', '.backup', '.old', '.orig', '.~*',
            # 缓存文件
            '.cache', '.cached', '.dat', '.db-wal', '.db-shm',
            # 日志文件
            '.log', '.log1', '.log2', '.log3', '.log4', '.log5',
            '.etl', '.evtx', '.dmp', '.mdmp',
            # 编译产物
            '.obj', '.pdb', '.ilk', '.exp', '.lib', '.pch',
            '.idb', '.tlog', '.lastbuildstate', '.unsuccessfulbuild',
            # 浏览器相关
            '.crdownload', '.partial', '.download', '.opdownload',
            # 系统文件
            '.chk', '.gid', '.fts', '.ftg', '.fnd',
            # 媒体缓存
            '.thumbdata3', '.thumbdata4', '.thumbdata5', '.thumbdata6',
            '.thumbcache', '.iconcache',
            # Office临时文件
            '.~*', '~$*', '.asd', '.wbk', '.xlk', '.ppt~',
            # 其他
            '.crx-update', '.part', '.filepart', '.bc!', '.!ut'
        }
        
        # 深度清理路径 - 更多垃圾文件位置
        self.deep_cleanup_paths = {
            'system_junk': [
                r'C:\Windows\Temp\*',
                r'C:\Windows\SoftwareDistribution\Download\*',
                r'C:\Windows\Logs\*',
                r'C:\Windows\Prefetch\*.pf',
                r'C:\Windows\LiveKernelReports\*',
                r'C:\Windows\Minidump\*',
                r'C:\Windows\System32\LogFiles\*',
                r'C:\Windows\System32\config\systemprofile\AppData\Local\Temp\*',
                r'C:\ProgramData\Microsoft\Windows\WER\*',
                r'C:\ProgramData\Microsoft\Windows Defender\Scans\History\*',
                r'C:\Windows\System32\winevt\Logs\*.evtx',
                r'C:\Windows\Panther\*',
                r'C:\Windows\inf\setupapi.dev.log',
                r'C:\Windows\setupact.log',
                r'C:\Windows\setuperr.log',
                r'C:\Windows\memory.dmp',
                r'C:\Windows\MEMORY.DMP',
            ],
            'user_junk': [
                os.path.expandvars(r'%TEMP%\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Temp\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\WebCache\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\INetCache\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_*.db'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\iconcache_*.db'),
                os.path.expandvars(r'%LOCALAPPDATA%\IconCache.db'),
                os.path.expandvars(r'%LOCALAPPDATA%\CrashDumps\*'),
                os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Recent\*'),
                os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Recent\AutomaticDestinations\*'),
                os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Recent\CustomDestinations\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\WER\*'),
                os.path.expandvars(r'%USERPROFILE%\AppData\Local\Temp\*'),
                os.path.expandvars(r'%SYSTEMROOT%\Temp\*'),
                os.path.expandvars(r'%WINDIR%\System32\FNTCACHE.DAT'),
            ],
            'browser_deep': [
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\GPUCache\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Service Worker\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Mozilla\Firefox\Profiles\*\cache2\*'),
                os.path.expandvars(r'%APPDATA%\Opera Software\Opera Stable\Cache\*'),
            ],
            'development_deep': [
                os.path.expandvars(r'%APPDATA%\npm-cache\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\pip\cache\*'),
                os.path.expandvars(r'%USERPROFILE%\.gradle\caches\*'),
                os.path.expandvars(r'%USERPROFILE%\.m2\repository\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\VisualStudio\*\ComponentModelCache\*'),
                os.path.expandvars(r'%APPDATA%\Code\logs\*'),
                os.path.expandvars(r'%APPDATA%\Code\CachedExtensions\*'),
            ],
            'media_deep': [
                os.path.expandvars(r'%LOCALAPPDATA%\Adobe\*\Cache\*'),
                os.path.expandvars(r'%TEMP%\Adobe*'),
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Office\*\OfficeFileCache\*'),
                os.path.expandvars(r'%USERPROFILE%\Downloads\*.tmp'),
                os.path.expandvars(r'%USERPROFILE%\Downloads\*.crdownload'),
                os.path.expandvars(r'%USERPROFILE%\Downloads\*.partial'),
            ],
            'gaming_deep': [
                r'C:\Program Files (x86)\Steam\dumps\*',
                r'C:\Program Files (x86)\Steam\logs\*',
                r'C:\Program Files (x86)\Steam\appcache\*',
                os.path.expandvars(r'%LOCALAPPDATA%\EpicGamesLauncher\Saved\Logs\*'),
                os.path.expandvars(r'%LOCALAPPDATA%\EpicGamesLauncher\Saved\webcache\*'),
                os.path.expandvars(r'%APPDATA%\Origin\Logs\*'),
            ]
        }
    
    def set_progress_callback(self, callback):
        """设置进度回调"""
        self.progress_callback = callback
    
    def _update_progress(self, message: str, current: int, total: int):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
    
    def _scan_path_for_junk(self, path_pattern: str) -> List[Path]:
        """扫描路径中的垃圾文件 - 激进模式"""
        junk_files = []

        try:
            # 使用glob匹配文件
            for file_path in glob.glob(path_pattern, recursive=True):
                try:
                    path_obj = Path(file_path)

                    if path_obj.is_file():
                        file_name_lower = path_obj.name.lower()
                        file_size = path_obj.stat().st_size
                        file_age = time.time() - path_obj.stat().st_mtime

                        # 更激进的垃圾文件识别
                        is_junk = False

                        # 1. 检查文件扩展名
                        if any(file_name_lower.endswith(ext.lower()) for ext in self.junk_extensions):
                            is_junk = True

                        # 2. 检查临时文件（年龄超过30分钟）
                        elif any(keyword in file_name_lower for keyword in ['temp', 'tmp', 'cache', 'log']):
                            if file_age > 1800:  # 30分钟
                                is_junk = True

                        # 3. 检查零字节文件
                        elif file_size == 0:
                            is_junk = True

                        # 4. 检查特定模式的文件
                        elif any(pattern in file_name_lower for pattern in [
                            'thumbs.db', 'desktop.ini', '.ds_store', 'icon\r',
                            'ehthumbs.db', 'ehthumbs_vista.db', 'folder.jpg',
                            'albumartsmall.jpg', 'albumart_{', 'picasa.ini'
                        ]):
                            is_junk = True

                        # 5. 检查浏览器缓存文件（所有文件）
                        elif any(cache_dir in str(path_obj).lower() for cache_dir in [
                            'cache', 'webcache', 'cookies', 'history', 'sessions'
                        ]):
                            is_junk = True

                        # 6. 检查大型日志文件（超过10MB且超过1天）
                        elif file_name_lower.endswith('.log') and file_size > 10*1024*1024 and file_age > 86400:
                            is_junk = True

                        # 7. 检查编译产物
                        elif any(file_name_lower.endswith(ext) for ext in [
                            '.obj', '.pdb', '.ilk', '.exp', '.lib', '.pch', '.idb'
                        ]):
                            is_junk = True

                        if is_junk:
                            junk_files.append(path_obj)

                    elif path_obj.is_dir():
                        # 检查空目录或特定缓存目录
                        try:
                            dir_name_lower = path_obj.name.lower()

                            # 空目录
                            if not any(path_obj.iterdir()):
                                junk_files.append(path_obj)
                            # 特定缓存目录（如果包含的都是缓存文件）
                            elif any(cache_name in dir_name_lower for cache_name in [
                                'cache', 'temp', 'tmp', 'logs'
                            ]):
                                # 检查目录中是否都是可删除的文件
                                all_junk = True
                                file_count = 0
                                for item in path_obj.rglob('*'):
                                    if item.is_file():
                                        file_count += 1
                                        if file_count > 100:  # 限制检查数量
                                            break
                                        # 如果有重要文件，则不删除整个目录
                                        if not any(item.name.lower().endswith(ext) for ext in self.junk_extensions):
                                            all_junk = False
                                            break

                                if all_junk and file_count > 0:
                                    junk_files.append(path_obj)

                        except (PermissionError, OSError):
                            pass

                except (OSError, PermissionError, FileNotFoundError):
                    continue

        except Exception as e:
            self.logger.warning(f"扫描路径失败 {path_pattern}: {e}")

        return junk_files
    
    def _aggressive_cleanup(self, file_paths: List[Path], category_name: str) -> CleanupResult:
        """激进清理文件"""
        result = CleanupResult()
        
        if not file_paths:
            return result
        
        total_files = len(file_paths)
        processed = 0
        deleted = 0
        bytes_freed = 0
        
        # 按文件大小排序，优先删除大文件
        file_paths.sort(key=lambda x: self._get_file_size(x), reverse=True)
        
        # 使用多线程并行删除
        max_workers = min(20, total_files, os.cpu_count() * 3)
        
        def delete_file_or_dir(path: Path) -> Tuple[bool, int]:
            """删除文件或目录"""
            try:
                size = self._get_file_size(path)

                if path.is_file():
                    success, error_msg = safe_delete_file(path, dry_run=False)
                    if success:
                        return True, size
                    else:
                        self.logger.debug(f"删除文件失败 {path}: {error_msg}")
                        return False, 0
                elif path.is_dir():
                    success, error_msg = safe_delete_directory(path, dry_run=False)
                    if success:
                        return True, size
                    else:
                        self.logger.debug(f"删除目录失败 {path}: {error_msg}")
                        return False, 0

                return False, 0
            except Exception as e:
                self.logger.debug(f"删除操作异常 {path}: {e}")
                return False, 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(delete_file_or_dir, path): path 
                for path in file_paths
            }
            
            for future in as_completed(future_to_path, timeout=600):  # 10分钟超时
                try:
                    success, size = future.result(timeout=3)  # 单个文件3秒超时
                    processed += 1
                    
                    if success:
                        deleted += 1
                        bytes_freed += size
                    
                    # 更新进度
                    if processed % 50 == 0 or processed == total_files:
                        self._update_progress(
                            f"{category_name} - 已删除 {deleted:,} 个文件",
                            processed,
                            total_files
                        )
                        
                except Exception as e:
                    processed += 1
                    self.logger.warning(f"删除文件失败: {e}")
        
        result.files_scanned = total_files
        result.files_deleted = deleted
        result.bytes_freed = bytes_freed
        result.success = True
        
        return result
    
    def _get_file_size(self, path: Path) -> int:
        """获取文件或目录大小"""
        try:
            if path.is_file():
                return path.stat().st_size
            elif path.is_dir():
                total_size = 0
                for item in path.rglob('*'):
                    if item.is_file():
                        try:
                            total_size += item.stat().st_size
                        except (OSError, FileNotFoundError):
                            continue
                return total_size
        except (OSError, FileNotFoundError):
            pass
        return 0
    
    def deep_system_cleanup(self) -> CleanupResult:
        """深度系统垃圾清理"""
        self.logger.info("开始深度系统垃圾清理...")
        
        all_junk_files = []
        
        # 扫描系统垃圾文件
        for path_pattern in self.deep_cleanup_paths['system_junk']:
            junk_files = self._scan_path_for_junk(path_pattern)
            all_junk_files.extend(junk_files)
        
        return self._aggressive_cleanup(all_junk_files, "深度系统清理")
    
    def deep_user_cleanup(self) -> CleanupResult:
        """深度用户垃圾清理"""
        self.logger.info("开始深度用户垃圾清理...")
        
        all_junk_files = []
        
        # 扫描用户垃圾文件
        for path_pattern in self.deep_cleanup_paths['user_junk']:
            junk_files = self._scan_path_for_junk(path_pattern)
            all_junk_files.extend(junk_files)
        
        return self._aggressive_cleanup(all_junk_files, "深度用户清理")
    
    def deep_browser_cleanup(self) -> CleanupResult:
        """深度浏览器清理"""
        self.logger.info("开始深度浏览器清理...")
        
        all_junk_files = []
        
        # 扫描浏览器垃圾文件
        for path_pattern in self.deep_cleanup_paths['browser_deep']:
            junk_files = self._scan_path_for_junk(path_pattern)
            all_junk_files.extend(junk_files)
        
        return self._aggressive_cleanup(all_junk_files, "深度浏览器清理")
    
    def deep_development_cleanup(self) -> CleanupResult:
        """深度开发工具清理"""
        self.logger.info("开始深度开发工具清理...")
        
        all_junk_files = []
        
        # 扫描开发工具垃圾文件
        for path_pattern in self.deep_cleanup_paths['development_deep']:
            junk_files = self._scan_path_for_junk(path_pattern)
            all_junk_files.extend(junk_files)
        
        return self._aggressive_cleanup(all_junk_files, "深度开发工具清理")

    def deep_media_cleanup(self) -> CleanupResult:
        """深度媒体文件清理"""
        self.logger.info("开始深度媒体文件清理...")

        all_junk_files = []

        # 扫描媒体垃圾文件
        for path_pattern in self.deep_cleanup_paths['media_deep']:
            junk_files = self._scan_path_for_junk(path_pattern)
            all_junk_files.extend(junk_files)

        return self._aggressive_cleanup(all_junk_files, "深度媒体清理")

    def deep_gaming_cleanup(self) -> CleanupResult:
        """深度游戏文件清理"""
        self.logger.info("开始深度游戏文件清理...")

        all_junk_files = []

        # 扫描游戏垃圾文件
        for path_pattern in self.deep_cleanup_paths['gaming_deep']:
            junk_files = self._scan_path_for_junk(path_pattern)
            all_junk_files.extend(junk_files)

        return self._aggressive_cleanup(all_junk_files, "深度游戏清理")

    def registry_cleanup(self) -> CleanupResult:
        """注册表清理（安全模式）"""
        self.logger.info("开始注册表清理...")

        result = CleanupResult()

        try:
            import winreg

            # 清理注册表中的临时项
            cleanup_keys = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"),
            ]

            cleaned_keys = 0

            for hkey, subkey_path in cleanup_keys:
                try:
                    with winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_ALL_ACCESS) as key:
                        # 获取子键数量
                        subkey_count = winreg.QueryInfoKey(key)[0]

                        # 删除所有子键（保留结构）
                        for i in range(subkey_count):
                            try:
                                subkey_name = winreg.EnumKey(key, 0)
                                winreg.DeleteKey(key, subkey_name)
                                cleaned_keys += 1
                            except WindowsError:
                                break

                except WindowsError as e:
                    self.logger.warning(f"无法清理注册表项 {subkey_path}: {e}")

            result.files_deleted = cleaned_keys
            result.success = True
            self.logger.info(f"清理了 {cleaned_keys} 个注册表项")

        except ImportError:
            result.error_message = "无法导入winreg模块"
            self.logger.warning("注册表清理需要winreg模块")
        except Exception as e:
            result.error_message = f"注册表清理失败: {e}"
            self.logger.error(f"注册表清理失败: {e}")

        return result

    def memory_dump_cleanup(self) -> CleanupResult:
        """内存转储文件清理"""
        self.logger.info("开始内存转储文件清理...")

        dump_patterns = [
            r'C:\Windows\Minidump\*.dmp',
            r'C:\Windows\memory.dmp',
            r'C:\Windows\MEMORY.DMP',
            os.path.expandvars(r'%LOCALAPPDATA%\CrashDumps\*.dmp'),
            os.path.expandvars(r'%TEMP%\*.dmp'),
        ]

        all_dump_files = []

        for pattern in dump_patterns:
            dump_files = self._scan_path_for_junk(pattern)
            all_dump_files.extend(dump_files)

        return self._aggressive_cleanup(all_dump_files, "内存转储清理")

    def thumbnail_cache_cleanup(self) -> CleanupResult:
        """缩略图缓存清理"""
        self.logger.info("开始缩略图缓存清理...")

        thumbnail_patterns = [
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\thumbcache_*.db'),
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\iconcache_*.db'),
            os.path.expandvars(r'%LOCALAPPDATA%\IconCache.db'),
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer\*.db'),
        ]

        all_thumbnail_files = []

        for pattern in thumbnail_patterns:
            thumbnail_files = self._scan_path_for_junk(pattern)
            all_thumbnail_files.extend(thumbnail_files)

        return self._aggressive_cleanup(all_thumbnail_files, "缩略图缓存清理")

    def massive_junk_cleanup(self) -> CleanupResult:
        """大规模垃圾文件清理 - 真正释放空间"""
        self.logger.info("开始大规模垃圾文件清理...")

        # 更激进的大文件清理策略
        massive_patterns = [
            # 所有临时目录的所有文件
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%LOCALAPPDATA%\Temp'),
            r'C:\Windows\Temp',

            # 所有浏览器缓存目录
            os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache'),
            os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache'),
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache'),
            os.path.expandvars(r'%LOCALAPPDATA%\Mozilla\Firefox\Profiles'),

            # Windows更新缓存
            r'C:\Windows\SoftwareDistribution\Download',

            # 系统日志
            r'C:\Windows\Logs',
            r'C:\Windows\System32\LogFiles',

            # 预读取文件
            r'C:\Windows\Prefetch',

            # 错误报告
            r'C:\Windows\LiveKernelReports',
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\WER'),

            # 缩略图缓存
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Explorer'),
        ]

        all_massive_files = []

        for base_path in massive_patterns:
            if os.path.exists(base_path):
                try:
                    # 递归扫描整个目录
                    for root, dirs, files in os.walk(base_path):
                        for file in files:
                            try:
                                file_path = Path(root) / file
                                if file_path.exists() and file_path.is_file():
                                    # 更宽松的条件 - 只要不是系统关键文件就删除
                                    if not self._is_critical_system_file(file_path):
                                        all_massive_files.append(file_path)
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue

        return self._aggressive_cleanup(all_massive_files, "大规模垃圾清理")

    def _is_critical_system_file(self, file_path: Path) -> bool:
        """检查是否为关键系统文件"""
        file_name = file_path.name.lower()
        file_ext = file_path.suffix.lower()

        # 保护关键系统文件
        critical_files = {
            'ntuser.dat', 'system.dat', 'software.dat', 'security.dat',
            'sam.dat', 'default.dat', 'usrclass.dat', 'bootmgr',
            'ntldr', 'boot.ini', 'config.sys', 'autoexec.bat'
        }

        critical_extensions = {
            '.exe', '.dll', '.sys', '.drv', '.ocx', '.cpl',
            '.scr', '.msc', '.msi', '.cab'
        }

        # 如果是关键文件名或扩展名，保护它
        if file_name in critical_files or file_ext in critical_extensions:
            return True

        # 保护正在运行的进程文件
        if 'system32' in str(file_path).lower() and file_ext in {'.exe', '.dll'}:
            return True

        return False

    def large_junk_files_cleanup(self) -> CleanupResult:
        """大型垃圾文件清理"""
        self.logger.info("开始大型垃圾文件清理...")

        # 搜索大型垃圾文件的路径
        large_file_patterns = [
            # 大型日志文件
            r'C:\Windows\Logs\**\*.log',
            r'C:\Windows\System32\LogFiles\**\*.log',
            r'C:\Windows\System32\LogFiles\**\*.etl',
            os.path.expandvars(r'%LOCALAPPDATA%\**\*.log'),
            os.path.expandvars(r'%APPDATA%\**\*.log'),

            # 大型缓存文件
            os.path.expandvars(r'%LOCALAPPDATA%\**\Cache\**\*'),
            os.path.expandvars(r'%LOCALAPPDATA%\**\cache\**\*'),
            os.path.expandvars(r'%LOCALAPPDATA%\**\webcache\**\*'),

            # 大型临时文件
            os.path.expandvars(r'%TEMP%\**\*'),
            os.path.expandvars(r'%LOCALAPPDATA%\Temp\**\*'),

            # 转储文件
            r'C:\Windows\Minidump\*.dmp',
            os.path.expandvars(r'%LOCALAPPDATA%\CrashDumps\*.dmp'),
        ]

        large_junk_files = []

        for pattern in large_file_patterns:
            try:
                for file_path in glob.glob(pattern, recursive=True):
                    try:
                        path_obj = Path(file_path)
                        if path_obj.is_file():
                            file_size = path_obj.stat().st_size
                            file_age = time.time() - path_obj.stat().st_mtime

                            # 只处理大于1MB且超过1小时的文件
                            if file_size > 1024*1024 and file_age > 3600:
                                large_junk_files.append(path_obj)

                    except (OSError, PermissionError, FileNotFoundError):
                        continue
            except Exception as e:
                self.logger.warning(f"扫描大文件模式失败 {pattern}: {e}")

        return self._aggressive_cleanup(large_junk_files, "大型垃圾文件清理")

    def windows_update_cleanup(self) -> CleanupResult:
        """Windows更新文件清理"""
        self.logger.info("开始Windows更新文件清理...")

        update_patterns = [
            r'C:\Windows\SoftwareDistribution\Download\*',
            r'C:\Windows\SoftwareDistribution\DataStore\Logs\*',
            r'C:\Windows\WindowsUpdate.log',
            r'C:\Windows\System32\catroot2\*',
            r'C:\Windows\Installer\$PatchCache$\*',
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Installer\*.msi'),
        ]

        update_files = []

        for pattern in update_patterns:
            update_files.extend(self._scan_path_for_junk(pattern))

        return self._aggressive_cleanup(update_files, "Windows更新清理")

    def perform_deep_cleanup(self) -> Dict[str, CleanupResult]:
        """执行全面深度清理"""
        self.logger.info("开始全面深度清理...")

        cleanup_results = {}

        # 按优先级执行清理 - 添加大规模清理
        cleanup_tasks = [
            ("大规模垃圾清理", self.massive_junk_cleanup),
            ("深度用户清理", self.deep_user_cleanup),
            ("深度浏览器清理", self.deep_browser_cleanup),
            ("深度系统清理", self.deep_system_cleanup),
            ("内存转储清理", self.memory_dump_cleanup),
            ("缩略图缓存清理", self.thumbnail_cache_cleanup),
            ("深度媒体清理", self.deep_media_cleanup),
            ("深度开发工具清理", self.deep_development_cleanup),
            ("深度游戏清理", self.deep_gaming_cleanup),
            ("注册表清理", self.registry_cleanup),
        ]

        for task_name, task_func in cleanup_tasks:
            try:
                self.logger.info(f"执行 {task_name}...")
                result = task_func()
                cleanup_results[task_name] = result

                self.total_scanned += result.files_scanned
                self.total_deleted += result.files_deleted
                self.total_bytes_freed += result.bytes_freed

                if result.files_deleted > 0:
                    self.logger.info(f"{task_name} 完成: 删除 {result.files_deleted:,} 个文件, 释放 {format_bytes(result.bytes_freed)}")
                else:
                    self.logger.info(f"{task_name} 完成: 没有找到需要清理的文件")

            except Exception as e:
                self.logger.error(f"{task_name} 失败: {e}")
                cleanup_results[task_name] = CleanupResult(success=False, error_message=str(e))

        return cleanup_results
