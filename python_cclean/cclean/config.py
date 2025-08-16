"""
Configuration module for CClean Python version.
Contains all paths, settings, and data structures used throughout the application.
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

VERSION = "1.0.0"
APP_NAME = "CClean - Windows C Drive Cleaner (Python)"

# 更安全的临时文件路径，优先选择用户可控的区域
TEMP_PATHS = [
    "%TEMP%",
    "%LOCALAPPDATA%\\Temp", 
    "%WINDIR%\\Temp",
    "%WINDIR%\\SoftwareDistribution\\Download",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WebCache",
]

# 系统路径单独处理，更加谨慎
SYSTEM_TEMP_PATHS = [
    "%WINDIR%\\Logs",
    "%WINDIR%\\Prefetch"
]

# 高优先级清理路径（大文件集中区域）
HIGH_PRIORITY_PATHS = [
    "%TEMP%",
    "%LOCALAPPDATA%\\Temp",
    "%WINDIR%\\Temp",
    "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache",
    "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache",
    "%WINDIR%\\SoftwareDistribution\\Download",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WebCache"
]

# 文件扩展名优先级（按清理效果排序）
FILE_PRIORITY_EXTENSIONS = {
    'high': ['.tmp', '.temp', '.cache', '.log', '.bak', '.old'],
    'medium': ['.dmp', '.evtx', '.etl', '.blf', '.regtrans-ms'],
    'low': ['.db', '.dat', '.idx', '.lock']
}

# 开发工具专用配置
DEVELOPMENT_CONFIG = {
    # 项目类型检测文件
    'project_indicators': {
        'node': ['package.json', 'yarn.lock', 'package-lock.json', 'node_modules'],
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', '__pycache__', '.venv', 'venv'],
        'java': ['pom.xml', 'build.gradle', 'gradlew', '.gradle', 'target', 'build'],
        'dotnet': ['*.csproj', '*.sln', 'bin', 'obj', 'packages'],
        'rust': ['Cargo.toml', 'Cargo.lock', 'target'],
        'go': ['go.mod', 'go.sum', 'vendor'],
        'php': ['composer.json', 'composer.lock', 'vendor'],
        'unity': ['Assets', 'ProjectSettings', 'Library', 'Temp'],
        'flutter': ['pubspec.yaml', 'pubspec.lock', '.dart_tool'],
    },
    
    # 开发工具缓存路径优先级
    'cache_priorities': {
        'high': [
            'node_modules\\.cache',
            '__pycache__',
            '.gradle\\caches',
            'bin\\Debug',
            'bin\\Release',
            'obj',
            'target\\debug',
            'target\\release',
        ],
        'medium': [
            '.vscode\\extensions',
            '.idea\\caches',
            'Library\\Cache',
            '.pub-cache',
            'vendor\\cache',
        ],
        'low': [
            '.git\\objects',
            'logs',
            'temp',
        ]
    },
    
    # 开发工具大文件模式（优先清理大文件）
    'large_file_patterns': [
        '*.nupkg',      # NuGet packages
        '*.jar',        # Java archives
        '*.war',        # Web archives
        '*.aar',        # Android archives
        '*.tgz',        # Compressed packages
        '*.tar.gz',     # Compressed packages
        '*.whl',        # Python wheels
        '*.egg',        # Python eggs
        '*.gem',        # Ruby gems
        '*.vsix',       # VS Code extensions
        '*.dmg',        # Mac disk images
        '*.iso',        # ISO files
        '*.deb',        # Debian packages
        '*.rpm',        # RPM packages
    ],
    
    # 安全跳过的开发文件
    'safe_skip_patterns': [
        '*.git*',       # Git files
        '*.svn*',       # SVN files
        'node_modules\\*\\package.json',  # Package configs
        'vendor\\*\\composer.json',      # Composer configs
        '.env*',        # Environment files
        'config.*',     # Config files
        'settings.*',   # Settings files
    ]
}

# 系统优化专用配置
SYSTEM_OPTIMIZATION_CONFIG = {
    # 系统优化类别优先级
    'optimization_priorities': {
        'critical': [
            'prefetch',         # Prefetch files
            'thumbnail',        # Thumbnail cache
            'icon_cache',       # Icon cache
            'log_files',        # System logs
            'crash_dumps',      # Crash dumps
        ],
        'high': [
            'search_index',     # Windows Search
            'update_cache',     # Windows Update
            'error_reports',    # Error reporting
            'temp_installer',   # Installer temps
            'driver_cache',     # Driver files
        ],
        'medium': [
            'font_cache',       # Font cache
            'registry_backup',  # Registry backups
            'event_logs',       # Event logs
            'performance_logs', # Performance logs
            'network_cache',    # Network cache
        ],
        'low': [
            'backup_files',     # Backup files
            'activation_cache', # Activation cache
            'media_cache',      # Media cache
            'recent_files',     # Recent files
        ]
    },
    
    # 危险操作警告（需要特别小心的路径）
    'dangerous_paths': [
        '%WINDIR%\\System32\\config\\SAM',      # 安全账户管理器
        '%WINDIR%\\System32\\config\\SYSTEM',   # 系统配置
        '%WINDIR%\\System32\\config\\SOFTWARE', # 软件配置
        '%WINDIR%\\System32\\config\\SECURITY', # 安全配置
        '%WINDIR%\\System32\\config\\DEFAULT',  # 默认用户配置
        '%SYSTEMDRIVE%\\pagefile.sys',          # 虚拟内存文件
        '%SYSTEMDRIVE%\\hiberfil.sys',          # 休眠文件
        '%SYSTEMDRIVE%\\swapfile.sys',          # 交换文件
    ],
    
    # 系统健康检查项目
    'health_checks': [
        'disk_space',       # 磁盘空间检查
        'memory_usage',     # 内存使用率
        'startup_programs', # 启动程序数量
        'service_status',   # 服务状态
        'temp_file_size',   # 临时文件大小
        'registry_size',    # 注册表大小
        'fragmentation',    # 磁盘碎片
        'update_status',    # 更新状态
    ],
    
    # 系统优化建议
    'optimization_suggestions': {
        'disk_cleanup': {
            'threshold': 85,  # 磁盘使用率阈值
            'action': '清理磁盘空间',
            'description': '磁盘空间不足可能影响系统性能'
        },
        'memory_optimization': {
            'threshold': 80,  # 内存使用率阈值  
            'action': '优化内存使用',
            'description': '内存使用率过高影响系统响应速度'
        },
        'startup_optimization': {
            'threshold': 15,  # 启动程序数量阈值
            'action': '禁用不必要的启动程序',
            'description': '过多启动程序会延长开机时间'
        },
        'temp_cleanup': {
            'threshold': 1024 * 1024 * 1024,  # 1GB临时文件阈值
            'action': '清理临时文件',
            'description': '大量临时文件占用磁盘空间'
        }
    },
    
    # 性能优化模式
    'performance_modes': {
        'conservative': {
            'description': '保守清理模式，只删除明确安全的文件',
            'risk_level': 'low',
            'include_categories': ['critical'],
        },
        'standard': {
            'description': '标准清理模式，平衡安全性和效果',
            'risk_level': 'medium', 
            'include_categories': ['critical', 'high'],
        },
        'aggressive': {
            'description': '激进清理模式，最大化系统优化效果',
            'risk_level': 'high',
            'include_categories': ['critical', 'high', 'medium'],
        },
        'expert': {
            'description': '专家模式，包含所有优化项目',
            'risk_level': 'very_high',
            'include_categories': ['critical', 'high', 'medium', 'low'],
        }
    }
}

BROWSER_CACHE_PATHS = [
    # Chrome
    "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache",
    "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Code Cache",
    "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\GPUCache",
    "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Service Worker\\CacheStorage",
    
    # Edge
    "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache",
    "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Code Cache", 
    "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\GPUCache",
    
    # Firefox
    "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*\\cache2",
    "%LOCALAPPDATA%\\Mozilla\\Firefox\\Profiles\\*\\cache2",
    "%APPDATA%\\Mozilla\\Firefox\\Profiles\\*\\startupCache",
    
    # Internet Explorer
    "%LOCALAPPDATA%\\Microsoft\\Windows\\INetCache",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Temporary Internet Files"
]

SYSTEM_CLEANUP_PATHS = [
    # Windows Logs
    "%WINDIR%\\Logs\\CBS",
    "%WINDIR%\\Logs\\DISM", 
    "%WINDIR%\\Logs\\DPX",
    "%WINDIR%\\Logs\\MoSetup",
    "%WINDIR%\\Logs\\NetSetup",
    "%WINDIR%\\Panther",
    
    # Windows Update
    "%WINDIR%\\SoftwareDistribution\\DataStore\\Logs",
    "%WINDIR%\\WindowsUpdate.log",
    
    # System Cache
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db",
    "%WINDIR%\\LiveKernelReports",
    "%WINDIR%\\Minidump",
    "%WINDIR%\\memory.dmp",
    
    # Event Logs (careful with these)
    "%WINDIR%\\System32\\winevt\\Logs\\*.evtx",
    
    # IIS Logs (if applicable)
    "%WINDIR%\\System32\\LogFiles",
    
    # Windows Defender
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History"
]

# Additional paths for thorough cleanup
ADDITIONAL_CLEANUP_PATHS = [
    # User-specific temp
    "%USERPROFILE%\\AppData\\Local\\Temp",
    
    # System temp
    "%SYSTEMROOT%\\Temp",
    
    # Recent files
    "%APPDATA%\\Microsoft\\Windows\\Recent",
    
    # Jump lists
    "%APPDATA%\\Microsoft\\Windows\\Recent\\AutomaticDestinations",
    "%APPDATA%\\Microsoft\\Windows\\Recent\\CustomDestinations",
    
    # Windows Error Reporting
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WER",
    
    # Crash dumps
    "%LOCALAPPDATA%\\CrashDumps",
    
    # Font cache
    "%WINDIR%\\System32\\FNTCACHE.DAT",
    
    # Setup logs
    "%WINDIR%\\inf\\setupapi.dev.log",
    "%WINDIR%\\setupact.log",
    "%WINDIR%\\setuperr.log"
]

# Development tools cleanup paths - 大幅扩展支持
DEVELOPMENT_CLEANUP_PATHS = [
    # Node.js / NPM / Yarn
    "%APPDATA%\\npm-cache",
    "%LOCALAPPDATA%\\npm-cache",
    "%LOCALAPPDATA%\\Yarn\\Cache",
    "%APPDATA%\\npm\\_logs",
    "%TEMP%\\npm-*",
    "%USERPROFILE%\\.npm\\_logs",
    "%USERPROFILE%\\.yarn\\cache",
    
    # Python / Pip / Conda
    "%LOCALAPPDATA%\\pip\\cache",
    "%APPDATA%\\Python\\pip\\cache",
    "%USERPROFILE%\\.cache\\pip",
    "%LOCALAPPDATA%\\conda\\pkgs",
    "%USERPROFILE%\\.conda\\pkgs",
    "%TEMP%\\pip-*",
    "%USERPROFILE%\\AppData\\Local\\pypoetry\\Cache",
    
    # Java / Maven / Gradle
    "%USERPROFILE%\\.gradle\\caches",
    "%USERPROFILE%\\.gradle\\daemon",
    "%USERPROFILE%\\.gradle\\wrapper",
    "%USERPROFILE%\\.m2\\repository",
    "%TEMP%\\hsperfdata_*",
    "%LOCALAPPDATA%\\Android\\Sdk\\temp",
    
    # .NET / NuGet
    "%USERPROFILE%\\.nuget\\packages",
    "%LOCALAPPDATA%\\NuGet\\Cache",
    "%TEMP%\\NuGetScratch",
    "%TEMP%\\VBCSCompiler",
    "%TEMP%\\MSBuild_*",
    
    # Visual Studio
    "%LOCALAPPDATA%\\Microsoft\\VisualStudio\\*\\ComponentModelCache",
    "%LOCALAPPDATA%\\Microsoft\\VisualStudio\\*\\Extensions",
    "%LOCALAPPDATA%\\Microsoft\\VisualStudio\\*\\VTC",
    "%LOCALAPPDATA%\\Microsoft\\VisualStudio\\*\\ActivityLog.xml",
    "%TEMP%\\VSFeedbackIntelliCodeLogs",
    "%TEMP%\\VSRemoteControl",
    
    # VSCode / Code editors
    "%APPDATA%\\Code\\logs",
    "%APPDATA%\\Code\\CachedExtensions",
    "%APPDATA%\\Code\\CachedData",
    "%APPDATA%\\Code\\User\\workspaceStorage",
    "%USERPROFILE%\\.vscode\\extensions\\ms-vscode.cpptools-*\\bin\\*.pdb",
    "%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\logs",
    
    # JetBrains IDEs
    "%USERPROFILE%\\.IntelliJIdea*\\system\\caches",
    "%USERPROFILE%\\.IntelliJIdea*\\system\\log",
    "%USERPROFILE%\\.IntelliJIdea*\\system\\tmp",
    "%USERPROFILE%\\.PyCharm*\\system\\caches",
    "%USERPROFILE%\\.WebStorm*\\system\\caches",
    "%USERPROFILE%\\.DataGrip*\\system\\caches",
    "%LOCALAPPDATA%\\JetBrains\\Toolbox\\logs",
    
    # Git
    "%TEMP%\\git-*",
    "%LOCALAPPDATA%\\GitHubDesktop\\logs",
    
    # Docker
    "%USERPROFILE%\\.docker\\machine\\cache",
    "%PROGRAMDATA%\\Docker\\windowsfilter",
    "%LOCALAPPDATA%\\Docker\\log.txt",
    
    # Unity
    "%LOCALAPPDATA%\\Unity\\cache",
    "%APPDATA%\\Unity\\Logs",
    "%TEMP%\\Unity*",
    
    # Unreal Engine
    "%LOCALAPPDATA%\\UnrealEngine\\*\\Saved\\Logs",
    "%APPDATA%\\Unreal Engine\\AutomationTool\\Logs",
    
    # Go
    "%USERPROFILE%\\go\\pkg\\mod\\cache",
    "%LOCALAPPDATA%\\go-build",
    
    # Rust / Cargo
    "%USERPROFILE%\\.cargo\\registry\\cache",
    "%USERPROFILE%\\.cargo\\git\\db",
    "%LOCALAPPDATA%\\cargo\\registry\\cache",
    
    # PHP / Composer
    "%APPDATA%\\Composer\\cache",
    "%LOCALAPPDATA%\\Composer\\cache",
    
    # Ruby / Gem
    "%USERPROFILE%\\.gem\\specs",
    "%LOCALAPPDATA%\\gem\\cache",
    
    # Swift
    "%LOCALAPPDATA%\\org.swift.swiftpm\\security\\cache",
    
    # CMake
    "%USERPROFILE%\\.cmake\\packages",
    "%TEMP%\\cmake-*",
    
    # Conan (C++)
    "%USERPROFILE%\\.conan\\data",
    
    # Flutter / Dart
    "%USERPROFILE%\\.pub-cache",
    "%LOCALAPPDATA%\\Pub\\Cache",
    "%USERPROFILE%\\AppData\\Local\\flutter_build_cache",
    
    # Electron
    "%USERPROFILE%\\.cache\\electron",
    "%LOCALAPPDATA%\\electron\\Cache",
    
    # Webpack / Build tools
    "%TEMP%\\webpack-*",
    "%USERPROFILE%\\.cache\\webpack",
    "%TEMP%\\terser-webpack-plugin",
    
    # Database tools
    "%LOCALAPPDATA%\\MongoDB\\logs",
    "%TEMP%\\postgresql*",
    "%LOCALAPPDATA%\\MySQL\\data\\*.log",
    
    # Virtualization
    "%USERPROFILE%\\.vagrant.d\\tmp",
    "%LOCALAPPDATA%\\VirtualBox\\VBoxSVC.log",
]

# Media and download cleanup paths  
MEDIA_CLEANUP_PATHS = [
    # Windows Media Player
    "%LOCALAPPDATA%\\Microsoft\\Media Player",
    
    # Adobe temp files
    "%LOCALAPPDATA%\\Adobe\\*\\Cache",
    "%TEMP%\\Adobe*",
    
    # Office temp files
    "%APPDATA%\\Microsoft\\Office\\Recent",
    "%LOCALAPPDATA%\\Microsoft\\Office\\*\\OfficeFileCache",
    "%TEMP%\\Word*",
    "%TEMP%\\Excel*",
    "%TEMP%\\PowerPoint*",
    
    # Download manager temps
    "%USERPROFILE%\\Downloads\\*.tmp",
    "%USERPROFILE%\\Downloads\\*.crdownload",
    "%USERPROFILE%\\Downloads\\*.partial",
]

# Gaming cleanup paths
GAMING_CLEANUP_PATHS = [
    # Steam
    "%PROGRAMFILES(X86)%\\Steam\\dumps",
    "%PROGRAMFILES(X86)%\\Steam\\logs",
    "%PROGRAMFILES(X86)%\\Steam\\appcache\\httpcache",
    
    # Epic Games
    "%LOCALAPPDATA%\\EpicGamesLauncher\\Saved\\Logs",
    "%LOCALAPPDATA%\\EpicGamesLauncher\\Saved\\webcache",
    
    # Origin/EA
    "%APPDATA%\\Origin\\Logs",
    "%LOCALAPPDATA%\\Origin\\Logs",
    
    # Battle.net
    "%PROGRAMDATA%\\Battle.net\\Setup\\Logs",
    
    # Unity
    "%LOCALAPPDATA%\\Unity\\Editor\\Editor.log",
    "%APPDATA%\\Unity\\Editor.log",
]

# System optimization paths - 大幅增强Windows系统优化
SYSTEM_OPTIMIZATION_PATHS = [
    # Windows Search 搜索优化
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WebCache\\*.log",
    "%PROGRAMDATA%\\Microsoft\\Search\\Data\\Applications\\Windows\\edb*.log",
    "%PROGRAMDATA%\\Microsoft\\Search\\Data\\Temp\\*",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\iconcache_*.db",
    
    # Windows Update 更新优化
    "%WINDIR%\\SoftwareDistribution\\Download\\*",
    "%WINDIR%\\SoftwareDistribution\\DataStore\\Logs\\*",
    "%WINDIR%\\System32\\catroot2\\dberr.txt",
    "%WINDIR%\\WindowsUpdate.log",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WindowsUpdate.log",
    
    # 设备驱动优化
    "%WINDIR%\\System32\\DriverStore\\FileRepository\\*.inf_*\\*.pnf",
    "%WINDIR%\\inf\\*.log",
    "%WINDIR%\\inf\\setupapi.dev.log",
    "%WINDIR%\\System32\\LogFiles\\setupapi\\*",
    
    # Windows Installer 安装程序优化
    "%WINDIR%\\Installer\\$PatchCache$\\Managed\\*",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Installer\\*.msi",
    "%TEMP%\\MSI*.LOG",
    "%WINDIR%\\Logs\\CBS\\*",
    "%WINDIR%\\Logs\\DISM\\*",
    
    # 性能监控和ETL日志
    "%WINDIR%\\System32\\LogFiles\\WMI\\RtBackup\\*",
    "%WINDIR%\\System32\\LogFiles\\Sum\\*.etl",
    "%WINDIR%\\System32\\WDI\\LogFiles\\*",
    "%WINDIR%\\System32\\WDI\\RtBackup\\*",
    "%WINDIR%\\System32\\LogFiles\\Scm\\*.etl",
    "%WINDIR%\\System32\\LogFiles\\SpoolerETW\\*",
    
    # 网络和连接优化
    "%SYSTEMROOT%\\System32\\config\\systemprofile\\AppData\\Local\\Microsoft\\Windows\\INetCache\\*",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\INetCache\\*",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\IECompatCache\\*",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\IECompatUaCache\\*",
    
    # Windows错误报告和诊断
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WER\\ReportQueue\\*",
    "%PROGRAMDATA%\\Microsoft\\Windows\\WER\\ReportQueue\\*",
    "%LOCALAPPDATA%\\Microsoft\\Windows\\WER\\ERC\\*",
    "%LOCALAPPDATA%\\CrashDumps\\*",
    "%WINDIR%\\LiveKernelReports\\*",
    "%WINDIR%\\Minidump\\*",
    "%WINDIR%\\memory.dmp",
    
    # Windows Prefetch 预取优化
    "%WINDIR%\\Prefetch\\*.pf",
    "%WINDIR%\\Prefetch\\Layout.ini",
    "%WINDIR%\\Prefetch\\ReadyBoot\\*",
    
    # SuperFetch / SysMain 优化
    "%WINDIR%\\System32\\SysMain.sdb",
    "%WINDIR%\\System32\\SysMain\\*",
    
    # Windows日志服务
    "%WINDIR%\\System32\\winevt\\Logs\\*.evtx",
    "%WINDIR%\\System32\\LogFiles\\*",
    "%WINDIR%\\debug\\*",
    "%WINDIR%\\Panther\\*",
    
    # 字体缓存优化
    "%WINDIR%\\System32\\FNTCACHE.DAT",
    "%LOCALAPPDATA%\\FontCache\\*",
    "%WINDIR%\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache\\*",
    
    # COM+ 组件缓存
    "%WINDIR%\\Registration\\CRMLog\\*",
    "%WINDIR%\\System32\\Com\\dmp\\*",
    
    # Windows Media Player 优化
    "%LOCALAPPDATA%\\Microsoft\\Media Player\\*",
    "%USERPROFILE%\\My Documents\\My Music\\*.wmdb",
    
    # Windows Defender 优化
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History\\Results\\Quick\\*",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Scans\\History\\Results\\Resource\\*",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\Quarantine\\*",
    "%PROGRAMDATA%\\Microsoft\\Windows Defender\\LocalCopy\\*",
    
    # 系统还原点优化
    "%SYSTEMDRIVE%\\System Volume Information\\_restore*\\*",
    
    # Windows备份优化
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Backup\\*",
    "%WINDIR%\\System32\\Backup\\*",
    
    # 任务计划程序日志
    "%WINDIR%\\Tasks\\*.log",
    "%WINDIR%\\System32\\Tasks\\Microsoft\\Windows\\TaskScheduler\\*",
    
    # Windows激活和授权
    "%WINDIR%\\System32\\spp\\store\\cache\\*",
    "%WINDIR%\\ServiceProfiles\\NetworkService\\AppData\\Roaming\\Microsoft\\SoftwareProtectionPlatform\\*",
    
    # DirectX着色器缓存
    "%LOCALAPPDATA%\\D3DSCache\\*",
    "%LOCALAPPDATA%\\NVIDIA\\DXCache\\*",
    "%LOCALAPPDATA%\\AMD\\DxCache\\*",
    
    # Windows资源管理器缓存
    "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\*.db",
    "%APPDATA%\\Microsoft\\Windows\\Recent\\*",
    "%APPDATA%\\Microsoft\\Windows\\Recent\\AutomaticDestinations\\*",
    "%APPDATA%\\Microsoft\\Windows\\Recent\\CustomDestinations\\*",
    
    # 系统性能计数器
    "%WINDIR%\\System32\\PerfLogs\\*",
    "%WINDIR%\\System32\\LogFiles\\Firewall\\*",
    
    # Windows启动优化
    "%WINDIR%\\Bootstat.dat",
    "%WINDIR%\\setupact.log",
    "%WINDIR%\\setuperr.log",
    
    # 注册表备份和事务日志
    "%WINDIR%\\System32\\config\\*.LOG*",
    "%WINDIR%\\System32\\config\\RegBack\\*",
    "%WINDIR%\\System32\\config\\TxR\\*",
]

MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_LOG_FILE = "cclean.log"

# File patterns to exclude from deletion (safety)
PROTECTED_FILES = [
    "desktop.ini",
    "thumbs.db",
    ".gitkeep", 
    "important.txt",
    "readme.txt"
]

# Extensions of files that are generally safe to delete from temp folders
SAFE_TEMP_EXTENSIONS = [
    ".tmp", ".temp", ".log", ".bak", ".old", ".cache", ".dmp",
    ".etl", ".evtx", ".manifest", ".blf", ".regtrans-ms", ".cab",
    ".chk", ".gid", ".fts", ".ftg", ".ftr", ".crdownload", ".partial",
    ".download", ".downloading", ".opdownload", ".oppart", ".bc!",
    ".!ut", ".aria2", ".torchdownload", ".crx", ".part", ".!qb"
]

# File patterns that are safe to delete (older than 1 day)
SAFE_TEMP_PATTERNS = [
    "*.tmp", "*.temp", "*.log", "*.bak", "*.old", 
    "~*.*", "_*.tmp", "*.chk", "*.gid", "*.crdownload", "*.partial",
    "*.download", "*.downloading", "*.opdownload", "*.oppart", "*.bc!",
    "*.!ut", "*.aria2", "*.torchdownload", "*.crx", "*.part", "*.!qb",
    "Thumbs.db", ".DS_Store", "desktop.ini", "*.lnk.bak"
]

# Additional safe extensions for development cleanup
SAFE_DEV_EXTENSIONS = [
    ".pdb", ".ilk", ".exp", ".lib", ".tlog", ".lastbuildstate", 
    ".unsuccessfulbuild", ".idb", ".pch", ".ipch", ".aps", ".ncb",
    ".suo", ".user", ".sdf", ".opensdf", ".db", ".opendb"
]

# Media and cache extensions
SAFE_MEDIA_EXTENSIONS = [
    ".webp", ".avif", ".ico", ".cur", ".ani", ".cached", 
    ".thumbnails", ".thumb", ".preview"
]

# Minimum file age for deletion (in seconds) - 1 hour for temp files
MIN_FILE_AGE_SECONDS = 3600

class CleanupType(Enum):
    """Enumeration of cleanup categories."""
    TEMP_FILES = "temp_files"
    BROWSER_CACHE = "browser_cache" 
    SYSTEM_FILES = "system_files"
    RECYCLE_BIN = "recycle_bin"
    DEVELOPMENT_FILES = "development_files"
    MEDIA_FILES = "media_files"
    GAMING_FILES = "gaming_files"
    SYSTEM_OPTIMIZATION = "system_optimization"
    ALL = "all"

@dataclass
class CleanupResult:
    """Data class to hold cleanup operation results."""
    files_scanned: int = 0
    files_deleted: int = 0
    bytes_freed: int = 0
    error_message: str = ""
    success: bool = True
    
    def __str__(self) -> str:
        if self.success:
            return (f"Success: {self.files_deleted}/{self.files_scanned} files processed, "
                   f"{format_bytes(self.bytes_freed)} freed")
        else:
            return f"Failed: {self.error_message}"

def format_bytes(bytes_value: int) -> str:
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

def expand_environment_variables(path: str) -> str:
    """Expand Windows environment variables in path."""
    return os.path.expandvars(path)

def get_all_cleanup_paths(cleanup_type: CleanupType) -> List[str]:
    """Get all cleanup paths for a specific cleanup type."""
    if cleanup_type == CleanupType.TEMP_FILES:
        return TEMP_PATHS + ADDITIONAL_CLEANUP_PATHS
    elif cleanup_type == CleanupType.BROWSER_CACHE:
        return BROWSER_CACHE_PATHS
    elif cleanup_type == CleanupType.SYSTEM_FILES:
        return SYSTEM_CLEANUP_PATHS
    elif cleanup_type == CleanupType.DEVELOPMENT_FILES:
        return DEVELOPMENT_CLEANUP_PATHS
    elif cleanup_type == CleanupType.MEDIA_FILES:
        return MEDIA_CLEANUP_PATHS
    elif cleanup_type == CleanupType.GAMING_FILES:
        return GAMING_CLEANUP_PATHS
    elif cleanup_type == CleanupType.SYSTEM_OPTIMIZATION:
        return SYSTEM_OPTIMIZATION_PATHS
    elif cleanup_type == CleanupType.ALL:
        return (TEMP_PATHS + BROWSER_CACHE_PATHS + SYSTEM_CLEANUP_PATHS + 
                ADDITIONAL_CLEANUP_PATHS + DEVELOPMENT_CLEANUP_PATHS + 
                MEDIA_CLEANUP_PATHS + GAMING_CLEANUP_PATHS + SYSTEM_OPTIMIZATION_PATHS)
    else:
        return []