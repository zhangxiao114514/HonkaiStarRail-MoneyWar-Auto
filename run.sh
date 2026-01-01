#!/bin/bash

# 崩坏：星穹铁道货币战争自动化脚本
# Linux/Mac 运行脚本

echo "========================================"
echo "崩坏：星穹铁道货币战争自动化脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未检测到Python，请先安装Python 3.7或更高版本"
    echo "下载地址：https://www.python.org/downloads/"
    exit 1
fi

# 检查ADB是否安装
if ! command -v adb &> /dev/null; then
    echo "错误：未检测到ADB，请先安装ADB"
    echo "下载地址：https://developer.android.com/studio/releases/platform-tools"
    echo "或使用包管理器安装：sudo apt-get install android-tools-adb (Ubuntu) 或 brew install android-platform-tools (Mac)"
    exit 1
fi

# 检查依赖是否已安装
echo "检查依赖库..."
python3 -c "import numpy, cv2, pytesseract" &> /dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖库..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误：依赖库安装失败"
        exit 1
    fi
fi

echo "启动自动化脚本..."
python3 main.py
