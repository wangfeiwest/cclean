@echo off
chcp 65001
title CClean增强版打包工具

echo ====================================
echo CClean增强版自动打包脚本 v3.0
echo ====================================
echo.

:: 检查Python是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python已安装

:: 检查PyInstaller是否安装
python -c "import PyInstaller" > nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告：PyInstaller未安装，正在自动安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ 错误：无法安装PyInstaller
        pause
        exit /b 1
    )
)

echo ✅ PyInstaller已准备就绪

:: 检查必要依赖
echo 📦 检查依赖包...
python -c "import colorama" > nul 2>&1
if errorlevel 1 (
    echo 正在安装 colorama...
    pip install colorama
)

python -c "import psutil" > nul 2>&1
if errorlevel 1 (
    echo 正在安装 psutil...
    pip install psutil
)

python -c "import pywin32" > nul 2>&1
if errorlevel 1 (
    echo 正在安装 pywin32...
    pip install pywin32
)

echo ✅ 依赖检查完成

:: 清理旧的构建文件
echo 🧹 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

:: 开始打包
echo 🚀 开始打包CClean增强版...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --clean CCleaner增强版_完整版.spec

if errorlevel 1 (
    echo ❌ 打包失败！请检查错误信息
    pause
    exit /b 1
)

echo.
echo 🎉 打包完成！

:: 检查输出文件
if exist "dist\CClean增强版_v3.0.exe" (
    echo ✅ 可执行文件已生成：dist\CClean增强版_v3.0.exe
    
    :: 获取文件大小
    for %%I in ("dist\CClean增强版_v3.0.exe") do set size=%%~zI
    set /a sizeMB=!size!/1024/1024
    echo 📁 文件大小：!sizeMB! MB
    
    echo.
    echo 📋 使用说明：
    echo   1. 将 dist\CClean增强版_v3.0.exe 复制到目标电脑
    echo   2. 右键点击 "以管理员身份运行"
    echo   3. 按照界面提示进行清理操作
    echo.
    echo 💡 提示：建议定期运行以保持系统清洁
    
    :: 询问是否立即运行
    set /p choice="是否立即测试运行？(y/N): "
    if /i "!choice!"=="y" (
        echo 🔄 启动程序测试...
        start "" "dist\CClean增强版_v3.0.exe"
    )
) else (
    echo ❌ 错误：未找到输出文件
)

echo.
echo 按任意键退出...
pause > nul