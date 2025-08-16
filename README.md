# 🧹 CClean - Advanced Windows C Drive Cleaner

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)
![Language](https://img.shields.io/badge/language-Python%203.7%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**A powerful, multi-engine Windows C drive cleaning tool with advanced categorization and intelligent cleaning algorithms.**

[English](#english) | [中文](#中文)

</div>

## English

### 🌟 Features

- **🚀 Multi-Engine Architecture**: 5 specialized cleaning engines (Standard + Optimized + Deep + Super + System Optimizer)
- **⚡ High Performance**: Multi-threaded parallel processing for maximum speed
- **🛡️ Safety First**: Intelligent file detection to prevent accidental deletion of important files
- **🎯 Smart Categories**: 13 different cleaning categories for precise garbage file targeting
- **📊 Detailed Reports**: Real-time progress display with comprehensive cleaning statistics
- **🔧 System Optimization**: Deep system performance optimization capabilities
- **💼 Professional Grade**: Suitable for both personal and enterprise use

### 📋 Cleaning Categories

| Category | Description | Safety Level |
|----------|-------------|--------------|
| **Quick Temp Files** | System and user temporary files | ⭐⭐⭐⭐⭐ |
| **Browser Cache** | All browser caches and data | ⭐⭐⭐⭐⭐ |
| **System Files** | Windows logs and system cache | ⭐⭐⭐⭐ |
| **Development Tools** | IDE cache, build artifacts | ⭐⭐⭐ |
| **Media Downloads** | Incomplete downloads, media cache | ⭐⭐⭐⭐ |
| **Gaming Platforms** | Steam, Epic, Origin cache | ⭐⭐⭐ |
| **System Optimization** | Windows search, update cache | ⭐⭐⭐⭐ |
| **Recycle Bin** | Empty recycle bin | ⭐⭐⭐⭐⭐ |
| **Full Standard Clean** | All standard categories | ⭐⭐⭐⭐⭐ |
| **Deep Aggressive** | Deep scan + aggressive cleaning | ⭐⭐⭐ |
| **Smart Deep Clean** | AI-powered cleaning strategy | ⭐⭐⭐⭐ |
| **Nuclear Clean** | Maximum space liberation | ⭐⭐ |
| **System Optimizer** | Comprehensive system optimization | ⭐⭐⭐ |

### 🚀 Quick Start

#### Option 1: Download Pre-built Binary
1. Download the latest release from [Releases](../../releases)
2. Right-click and select "Run as administrator"
3. Follow the interactive prompts

#### Option 2: Build from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/cclean.git
cd cclean/python_cclean

# Install dependencies
pip install -r requirements.txt

# Run directly
python enhanced_quick_clean.py

# Or build executable
python quick_build.py
```

### 📦 Building Executable

Multiple build methods available:

```bash
# Method 1: Automated batch script (Windows)
build_cclean.bat

# Method 2: Python script
python quick_build.py

# Method 3: PyInstaller with spec file
pyinstaller CCleaner增强版_完整版.spec

# Method 4: Manual PyInstaller
pyinstaller --onefile --name=CClean_Enhanced_v3.0 enhanced_quick_clean.py
```

### 📋 Requirements

- **OS**: Windows 10/11
- **Python**: 3.7+ (for building)
- **RAM**: 2GB minimum
- **Dependencies**:
  - `colorama` (terminal colors)
  - `psutil` (system information)
  - `pywin32` (Windows API)

### ⚠️ Safety Notes

- **Admin Rights**: Run as administrator for best results
- **Backup**: Back up important data before first use
- **Nuclear Clean**: May affect program startup speeds (cache rebuild required)
- **System Optimizer**: Modifies system settings, create restore point first

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 中文

### 🌟 功能特性

- **🚀 多引擎架构**: 五大专业清理引擎（标准+优化+深度+超级+系统优化）
- **⚡ 高性能处理**: 多线程并行处理，最大化清理速度
- **🛡️ 安全至上**: 智能文件检测，避免误删重要文件
- **🎯 智能分类**: 13种清理分类，精准定位垃圾文件
- **📊 详细报告**: 实时进度显示，全面清理统计
- **🔧 系统优化**: 深度系统性能优化功能
- **💼 专业级别**: 适用于个人和企业使用

### 📋 清理分类

| 分类 | 说明 | 安全等级 |
|------|------|----------|
| **快速临时文件** | 系统和用户临时文件 | ⭐⭐⭐⭐⭐ |
| **快速浏览器缓存** | 所有浏览器缓存和数据 | ⭐⭐⭐⭐⭐ |
| **系统文件** | Windows日志和系统缓存 | ⭐⭐⭐⭐ |
| **开发工具** | IDE缓存、构建产物 | ⭐⭐⭐ |
| **媒体下载** | 未完成下载、媒体缓存 | ⭐⭐⭐⭐ |
| **游戏平台** | Steam、Epic、Origin缓存 | ⭐⭐⭐ |
| **系统优化** | Windows搜索、更新缓存 | ⭐⭐⭐⭐ |
| **回收站** | 清空回收站 | ⭐⭐⭐⭐⭐ |
| **标准全面清理** | 清理所有标准分类 | ⭐⭐⭐⭐⭐ |
| **深度激进清理** | 深度扫描+激进清理 | ⭐⭐⭐ |
| **智能深度清理** | AI智能清理策略 | ⭐⭐⭐⭐ |
| **核弹级清理** | 最大化空间释放 | ⭐⭐ |
| **系统优化器** | 全面系统优化 | ⭐⭐⭐ |

### 🚀 快速开始

#### 方案一：下载预编译版本
1. 从 [Releases](../../releases) 下载最新版本
2. 右键选择"以管理员身份运行"
3. 按照交互提示操作

#### 方案二：源码运行
```bash
# 克隆仓库
git clone https://github.com/yourusername/cclean.git
cd cclean/python_cclean

# 安装依赖
pip install -r requirements.txt

# 直接运行
python enhanced_quick_clean.py

# 或者构建可执行文件
python quick_build.py
```

### 📦 构建可执行文件

提供多种构建方式：

```bash
# 方法1：自动化批处理脚本（Windows）
build_cclean.bat

# 方法2：Python脚本
python quick_build.py

# 方法3：使用spec文件
pyinstaller CCleaner增强版_完整版.spec

# 方法4：手动PyInstaller
pyinstaller --onefile --name=CClean增强版_v3.0 enhanced_quick_clean.py
```

### 📋 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.7+（用于构建）
- **内存**: 最少2GB
- **依赖包**:
  - `colorama`（终端颜色支持）
  - `psutil`（系统信息获取）
  - `pywin32`（Windows API调用）

### ⚠️ 安全提示

- **管理员权限**: 以管理员身份运行以获得最佳效果
- **数据备份**: 首次使用前备份重要数据
- **核弹级清理**: 可能影响程序启动速度（需要重建缓存）
- **系统优化**: 会修改系统设置，建议先创建还原点

### 🤝 贡献

欢迎贡献代码！请随时提交Pull Request。

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

### 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！ ⭐**

Made with ❤️ by CClean Development Team

</div>