@echo off

rem 崩坏：星穹铁道货币战争自动化脚本
rem Windows 运行脚本

echo ========================================
echo 崩坏：星穹铁道货币战争自动化脚本
echo ========================================
echo.

rem 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python，请先安装Python 3.7或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

rem 检查ADB是否安装
adb --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到ADB，请先安装ADB
    echo 下载地址：https://developer.android.com/studio/releases/platform-tools
    echo 或安装模拟器（如夜神、蓝叠等）自带ADB
    pause
    exit /b 1
)

rem 检查依赖是否已安装
echo 检查依赖库...
python -c "import numpy, cv2, pytesseract" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装依赖库...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 错误：依赖库安装失败
        pause
        exit /b 1
    )
)

echo 启动自动化脚本...
python main.py

pause
