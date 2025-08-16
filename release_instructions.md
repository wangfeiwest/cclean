# GitHub Release 创建说明

由于需要GitHub认证，请按以下步骤手动创建Release：

## 方法一：使用GitHub CLI（推荐）

1. 首先登录GitHub CLI：
```bash
gh auth login
```
选择 GitHub.com，然后选择 HTTPS，按提示完成认证。

2. 创建Release并上传文件：
```bash
cd "E:\work\SVN\cclean"
gh release create v3.0.1 --title "CClean Enhanced v3.0.1 - Executable Release" --notes-file release_notes.md "python_cclean/dist/CCleanPortable.exe" "python_cclean/白名单说明.txt"
```

## 方法二：通过GitHub网页界面

1. 访问：https://github.com/wangfeiwest/cclean/releases
2. 点击 "Create a new release"
3. 填写：
   - Tag version: `v3.0.1`
   - Release title: `CClean Enhanced v3.0.1 - Executable Release`
   - Description: 见下方发布说明
4. 上传文件：
   - `python_cclean/dist/CCleanPortable.exe`
   - `python_cclean/白名单说明.txt`
5. 点击 "Publish release"

## 发布说明内容

```markdown
## 🚀 CClean Enhanced v3.0.1 - 可执行文件发布

### 📦 下载文件

- **CCleanPortable.exe** - 便携版可执行文件 (推荐)
- **白名单说明.txt** - 杀毒软件白名单设置说明

### ✨ 新功能

- 🔧 多线程并行清理算法
- 🎯 智能深度清理选项  
- ☢️ 核弹级超级清理模式
- 🔧 深度系统优化工具
- 📁 支持13种清理分类

### 🛡️ 安全说明

**如果杀毒软件误报，请参考白名单说明文件设置**

误报原因：
- PyInstaller打包特征容易触发启发式检测
- 程序需要管理员权限清理系统文件
- 批量文件删除操作被识别为清理工具行为

**安全保证：**
- ✅ 源代码完全开放
- ✅ 只清理临时文件和缓存
- ✅ 包含安全检查机制
- ✅ 不修改重要系统文件

### 🎮 使用方法

1. 下载 `CCleanPortable.exe`
2. 右键"以管理员身份运行"
3. 按照界面提示选择清理类型
4. 等待清理完成

### 📋 系统要求

- Windows 7/8/10/11
- 建议以管理员权限运行获得最佳效果

### 🔗 源代码

完整源代码请查看仓库中的 `python_cclean` 目录。
```

## 文件位置

- 可执行文件：`E:\work\SVN\cclean\python_cclean\dist\CCleanPortable.exe`
- 白名单说明：`E:\work\SVN\cclean\python_cclean\白名单说明.txt`
- Git标签已创建：`v3.0.1`
- 代码已推送到远程仓库