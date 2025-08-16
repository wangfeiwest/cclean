@echo off
chcp 65001
title CClean项目GitHub上传工具

echo ====================================
echo 🚀 CClean项目GitHub上传工具
echo ====================================
echo.

echo 📋 上传前检查清单：
echo ✅ 已在GitHub创建新仓库 (cclean)
echo ✅ 仓库设为Public
echo ✅ 未勾选任何初始化选项
echo.

set /p github_username="请输入您的GitHub用户名: "
if "%github_username%"=="" (
    echo ❌ 用户名不能为空
    pause
    exit /b 1
)

echo.
echo 🔗 将连接到: https://github.com/%github_username%/cclean.git
echo.

set /p confirm="确认开始上传？(y/N): "
if /i not "%confirm%"=="y" (
    echo 上传已取消
    pause
    exit /b 0
)

echo.
echo 🚀 开始上传到GitHub...
echo.

:: 添加远程仓库
echo 📡 添加远程仓库...
git remote add origin https://github.com/%github_username%/cclean.git
if errorlevel 1 (
    echo ⚠️  远程仓库可能已存在，尝试更新...
    git remote set-url origin https://github.com/%github_username%/cclean.git
)

:: 验证远程仓库
echo 🔍 验证远程仓库连接...
git remote -v

:: 推送到GitHub
echo 📤 推送代码到GitHub...
git push -u origin master

if errorlevel 1 (
    echo.
    echo ❌ 推送失败，可能的原因：
    echo   1. 仓库名称不正确
    echo   2. 权限问题
    echo   3. 网络连接问题
    echo   4. 仓库已存在内容
    echo.
    echo 💡 解决方案：
    echo   - 确认GitHub仓库已创建且为空
    echo   - 检查网络连接
    echo   - 尝试强制推送: git push -f origin master
    echo.
    pause
    exit /b 1
)

echo.
echo 🎉 上传成功！
echo.
echo 📋 下一步建议：
echo   1. 访问: https://github.com/%github_username%/cclean
echo   2. 检查所有文件是否正确上传
echo   3. 创建第一个Release (v3.0.0)
echo   4. 设置仓库描述和话题标签
echo.
echo ✨ 项目链接: https://github.com/%github_username%/cclean
echo.

pause