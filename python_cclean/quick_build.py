#!/usr/bin/env python3
"""
快速打包脚本 - 简化版PyInstaller配置
用于快速生成可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """主打包函数"""
    print("=" * 60)
    print("🧹 CClean增强版 - 快速打包工具")
    print("=" * 60)
    
    # 检查必要文件
    required_files = [
        "enhanced_quick_clean.py",
        "cclean/__init__.py",
        "cclean/cleaner.py",
        "cclean/config.py",
        "cclean/logger.py",
        "cclean/utils.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        return 1
    
    print("✅ 所有必要文件存在")
    
    # 清理旧的构建文件
    print("🧹 清理旧构建文件...")
    for dir_name in ["build", "dist", "__pycache__"]:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"   清理: {dir_name}")
    
    # 构建PyInstaller命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=CClean增强版_v3.0",
        "--console",
        "--noconfirm",
        "--clean",
        "--add-data=cclean;cclean",
        "enhanced_quick_clean.py"
    ]
    
    # 添加隐藏导入
    hidden_imports = [
        "cclean",
        "cclean.cleaner", 
        "cclean.config",
        "cclean.logger",
        "cclean.utils",
        "cclean.progress",
        "colorama",
        "winreg"
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    print("🚀 开始打包...")
    print(f"命令: {' '.join(cmd)}")
    print()
    
    try:
        # 执行PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        print("\n🎉 打包完成！")
        
        # 检查输出文件
        exe_path = Path("dist/CClean增强版_v3.0.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✅ 可执行文件: {exe_path}")
            print(f"📁 文件大小: {size_mb:.1f} MB")
            
            print("\n📋 使用说明:")
            print("   1. 复制 dist/CClean增强版_v3.0.exe 到目标电脑")
            print("   2. 右键选择 '以管理员身份运行'")
            print("   3. 按照界面提示进行清理")
            
            return 0
        else:
            print("❌ 未找到输出文件")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        return 1
    except FileNotFoundError:
        print("❌ PyInstaller未安装，请运行: pip install pyinstaller")
        return 1

if __name__ == "__main__":
    sys.exit(main())