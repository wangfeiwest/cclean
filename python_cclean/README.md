# CClean Python - Windows C盘清理工具

CClean Python 是一个专为 Windows 系统设计的 C 盘清理工具的 Python 实现版本，提供了更好的跨平台兼容性和易用性。

## 🌟 特性亮点

- **🧹 全面清理**: 临时文件、浏览器缓存、系统垃圾文件、回收站
- **🛡️ 安全可靠**: 干运行模式、文件占用检测、智能保护机制
- **⚡ 高效处理**: 多线程文件处理、进度显示、批量操作
- **📊 详细报告**: 彩色输出、日志记录、清理统计
- **🎛️ 灵活控制**: 分类清理、交互确认、静默模式

## 📋 系统要求

- **操作系统**: Windows 10/11 (推荐) 或 Windows 7/8.1
- **Python**: 3.8 或更高版本
- **权限**: 建议以管理员身份运行以获得最佳效果

## 🚀 快速安装

### 方式一：直接安装依赖

```bash
# 克隆或下载项目
cd python_cclean

# 安装依赖包
pip install -r requirements.txt

# 直接运行
python -m cclean.main --help
```

### 方式二：安装为包

```bash
# 安装到系统
pip install .

# 使用命令
cclean-py --help
```

### 方式三：开发模式安装

```bash
# 开发模式安装（可编辑）
pip install -e .

# 安装额外的开发依赖
pip install -e .[dev]
```

## 🎯 使用方法

### 基本命令

```bash
# 扫描所有类别（默认操作）
python -m cclean.main --scan

# 交互式清理所有类别
python -m cclean.main --clean

# 干运行模式（安全预览）
python -m cclean.main --clean --dry-run
```

### 分类清理

```bash
# 只清理临时文件
python -m cclean.main --temp --clean

# 只清理浏览器缓存
python -m cclean.main --browser --clean

# 只清理系统文件
python -m cclean.main --system --clean

# 只清空回收站
python -m cclean.main --recycle --clean
```

### 高级选项

```bash
# 详细输出模式
python -m cclean.main --clean --verbose

# 静默模式（仅日志输出）
python -m cclean.main --clean --quiet

# 自定义日志文件
python -m cclean.main --clean --log my_cleanup.log

# 强制请求管理员权限
python -m cclean.main --clean --force-admin
```

## 📝 命令行参数详解

| 参数 | 简写 | 描述 |
|------|------|------|
| `--scan` | `-s` | 扫描文件但不删除（默认） |
| `--clean` | `-c` | 执行清理操作 |
| `--temp` | `-t` | 仅处理临时文件 |
| `--browser` | `-b` | 仅处理浏览器缓存 |
| `--system` | `-y` | 仅处理系统文件 |
| `--recycle` | `-r` | 仅清空回收站 |
| `--all` | `-a` | 处理所有类别（默认） |
| `--dry-run` | `-d` | 干运行模式 |
| `--verbose` | `-v` | 详细输出 |
| `--quiet` | `-q` | 静默模式 |
| `--log FILE` | `-l` | 指定日志文件 |
| `--no-progress` | | 禁用进度条 |
| `--force-admin` | | 请求管理员权限 |
| `--version` | | 显示版本信息 |
| `--help` | `-h` | 显示帮助信息 |

## 💡 使用示例

### 1. 首次使用建议

```bash
# 先进行全面扫描，了解可清理的内容
python -m cclean.main --scan --verbose
```

### 2. 安全清理流程

```bash
# 1. 干运行测试
python -m cclean.main --clean --dry-run --verbose

# 2. 确认无误后正式清理
python -m cclean.main --clean
```

### 3. 自动化脚本

```bash
# 静默清理所有内容，适合定时任务
python -m cclean.main --clean --quiet --log scheduled_cleanup.log
```

### 4. 针对性清理

```bash
# 只清理浏览器缓存，保持其他文件
python -m cclean.main --browser --clean --verbose
```

## 🗂️ 清理路径详解

### 临时文件 (--temp)
- `%TEMP%` - 用户临时文件
- `%LOCALAPPDATA%\\Temp` - 本地应用数据临时文件
- `%WINDIR%\\Temp` - Windows系统临时文件
- `%WINDIR%\\Prefetch` - 预读文件
- `%LOCALAPPDATA%\\Microsoft\\Windows\\WebCache` - Web缓存

### 浏览器缓存 (--browser)
- **Chrome**: `%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache`
- **Edge**: `%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache`
- **Firefox**: `%APPDATA%\\Mozilla\\Firefox\\Profiles\\*\\cache2`
- **Internet Explorer**: `%LOCALAPPDATA%\\Microsoft\\Windows\\INetCache`

### 系统文件 (--system)
- `%WINDIR%\\Logs` - Windows日志文件
- `%WINDIR%\\SoftwareDistribution\\Download` - Windows更新缓存
- `%WINDIR%\\LiveKernelReports` - 内核报告
- `%WINDIR%\\Minidump` - 内存转储文件
- `%LOCALAPPDATA%\\CrashDumps` - 崩溃转储

## 🛡️ 安全机制

### 文件保护
- **占用检测**: 自动跳过正在使用的文件
- **系统文件保护**: 智能识别重要系统文件
- **白名单机制**: 保护重要配置文件
- **扩展名过滤**: 只删除安全的临时文件类型

### 操作安全
- **干运行模式**: 预览操作结果，不实际删除
- **交互确认**: 清理前用户确认机制
- **详细日志**: 完整记录所有操作
- **错误处理**: 优雅处理各种异常情况

## 📊 输出说明

### 扫描结果示例
```
Scan Results - All Categories:
  Files Found: 1,234
  Space to Free: 2.5 GB
```

### 清理结果示例
```
Cleanup Results - All Categories:
  Files Processed: 1,180/1,234
  Space Freed: 2.3 GB
```

### 进度显示
程序支持实时进度显示，包括：
- 进度条（使用 tqdm 库）
- 百分比显示
- 当前操作状态
- 彩色状态指示

## 🔧 配置选项

### 环境变量
- `CCLEAN_LOG_LEVEL`: 设置日志级别 (DEBUG, INFO, WARNING, ERROR)
- `CCLEAN_MAX_WORKERS`: 设置最大工作线程数
- `CCLEAN_LOG_FILE`: 默认日志文件名

### 自定义配置
可以修改 `config.py` 文件来自定义：
- 清理路径列表
- 保护文件列表
- 安全扩展名列表
- 日志设置

## 🐛 故障排除

### 常见问题

**权限不足**
```bash
# 以管理员身份运行命令提示符
python -m cclean.main --force-admin
```

**依赖包安装失败**
```bash
# 升级 pip 后重新安装
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**找不到某些路径**
- 正常现象，不同系统和浏览器安装情况不同
- 程序会自动跳过不存在的路径

**清理效果不明显**
- 确保以管理员身份运行
- 关闭正在运行的浏览器和其他程序
- 检查磁盘是否为SSD（某些SSD有垃圾回收机制）

### 调试模式

```bash
# 启用详细调试输出
python -m cclean.main --scan --verbose

# 检查日志文件
type cclean.log
```

## 🔄 更新日志

### v1.0.0
- ✨ 初始版本发布
- 🧹 支持临时文件、浏览器缓存、系统文件、回收站清理
- 🛡️ 完整的安全机制和错误处理
- 📊 彩色输出和进度显示
- 📝 详细日志和报告生成

## 🤝 贡献指南

欢迎提交问题报告和功能建议！

### 开发环境设置
```bash
# 克隆项目
git clone <repository-url>
cd python_cclean

# 创建虚拟环境
python -m venv venv
venv\\Scripts\\activate

# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest tests/
```

## ⚖️ 许可证

本项目基于 MIT 许可证开源。详见 LICENSE 文件。

## ⚠️ 免责声明

- 使用本工具前请备份重要数据
- 作者不对数据丢失或系统损坏承担责任
- 建议首次使用时先进行干运行测试
- 请在了解工具功能的前提下使用

## 📞 支持

如果您遇到问题或有改进建议：

1. 查看本 README 和日志文件
2. 搜索已有的 Issues
3. 创建新的 Issue 并提供详细信息
4. 考虑提交 Pull Request

---

**感谢使用 CClean Python！让我们一起保持系统清洁高效！** 🚀