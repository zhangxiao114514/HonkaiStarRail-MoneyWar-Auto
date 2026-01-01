# 《崩坏：星穹铁道》货币战争自动化脚本

## 项目简介

本脚本用于自动化《崩坏：星穹铁道》游戏中的「货币战争」玩法，实现从进入玩法、选择关卡、开启自动战斗到结算重启的全流程闭环。

## 核心功能

1. **ADB基础操作**：自动检测设备连接、分辨率验证（强制1280×720）
2. **关键UI识别**：模板匹配识别「货币战争入口」「自动战斗按钮」「结算确认按钮」
3. **简单OCR**：识别战斗结果，失败自动重启
4. **全流程闭环**：游戏主界面→进入货币战争→选择关卡→开启自动战斗→结算→重启
5. **异常处理**：超时重试、弹窗自动关闭

## 技术栈

- Python 3.7+
- ADB（Android Debug Bridge）
- OpenCV（模板匹配）
- pytesseract（OCR识别）

## 环境搭建

### 1. 安装Python

- 下载并安装Python 3.7或更高版本
- 下载地址：https://www.python.org/downloads/
- 安装时勾选「Add Python to PATH」

### 2. 安装ADB

#### Windows
- 方法1：安装Android Studio，启用SDK Platform-Tools
- 方法2：直接下载ADB工具包
  - 下载地址：https://developer.android.com/studio/releases/platform-tools
  - 解压后将目录添加到系统环境变量PATH中

#### Linux/Mac
- Ubuntu：`sudo apt-get install android-tools-adb`
- Mac：`brew install android-platform-tools`

### 3. 安装依赖库

```bash
# 进入脚本目录
cd /path/to/script

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置模拟器

- 使用支持1280×720分辨率的模拟器（如夜神、蓝叠、MuMu等）
- 在模拟器设置中，将分辨率设置为 **1280×720**
- 启用模拟器的USB调试模式

## 使用方法

### 启动步骤

1. 启动模拟器，进入《崩坏：星穹铁道》游戏
2. 确保游戏处于主界面
3. 运行脚本：
   - Windows：双击 `run.bat`
   - Linux/Mac：终端执行 `./run.sh`

### 脚本流程

```
开始
├── 检查ADB连接
├── 检查设备分辨率（1280×720）
├── 生成/加载UI模板
├── 循环开始
│   ├── 检查并关闭弹窗
│   ├── 进入货币战争入口
│   ├── 选择关卡
│   ├── 开启自动战斗
│   ├── 等待战斗结束
│   ├── 处理战斗结果
│   ├── 结算确认
│   └── 返回主界面
└── 结束
```

## 配置说明

### 核心配置（main.py）

```python
CONFIG = {
    'adb_path': 'adb',                # ADB工具路径
    'template_dir': 'templates',      # 模板文件目录
    'max_retries': 3,                 # 最大重试次数
    'timeout': 10,                    # 超时时间（秒）
    'threshold': 0.8,                 # 模板匹配阈值
    'resolution': (1280, 720),        # 强制分辨率
    'templates': {                    # 模板配置
        'money_war_entry': '货币战争入口',
        'auto_battle': '自动战斗按钮',
        'settlement_confirm': '结算确认按钮'
    },
    'fixed_coords': {                 # 固定坐标（仅1280×720）
        'close_popup': (640, 600),    # 关闭弹窗位置
        'battle_retry': (640, 400),   # 战斗失败重试位置
        'back_button': (50, 50),      # 返回按钮位置
        'stage_select': (640, 400)    # 关卡选择位置
    },
    'ocr_regions': {                  # OCR识别区域
        'battle_result': (400, 200, 480, 100)  # 战斗结果区域
    }
}
```

## 模板文件

脚本会自动处理模板文件：

1. 首次运行时，若模板目录下无模板文件，会自动生成
2. 模板文件位于 `templates/` 目录：
   - `money_war_entry.png`：货币战争入口
   - `auto_battle.png`：自动战斗按钮
   - `settlement_confirm.png`：结算确认按钮

## 注意事项

1. **分辨率要求**：必须使用1280×720分辨率的模拟器
2. **游戏状态**：启动脚本前，游戏需处于主界面
3. **ADB权限**：确保ADB能正常连接到模拟器
4. **防检测**：脚本包含随机延迟（0.5-1.5秒），降低被检测风险
5. **异常处理**：遇到弹窗会自动点击关闭，超时会重试
6. **OCR配置**：需要安装Tesseract OCR引擎
   - Windows：下载安装 https://github.com/tesseract-ocr/tesseract
   - Linux：`sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim`
   - Mac：`brew install tesseract tesseract-lang`

## 常见问题

### Q: 脚本无法识别UI元素
A: 请确保：
   - 模拟器分辨率为1280×720
   - 游戏处于主界面
   - 首次运行时会自动生成模板，若生成失败可手动截图替换

### Q: ADB连接失败
A: 请检查：
   - 模拟器USB调试已启用
   - ADB版本与模拟器兼容
   - 尝试重启模拟器和ADB服务：
     ```bash
     adb kill-server
     adb start-server
     adb devices
     ```

### Q: OCR识别不准确
A: 请确保：
   - 已安装中文语言包
   - 游戏画面清晰，无遮挡

## 运行日志

脚本输出极简日志，格式为：
```
[HH:MM:SS] 操作类型
```

## 免责声明

1. 本脚本仅用于学习和研究目的
2. 请遵守游戏运营商的用户协议，合理使用脚本
3. 过度使用自动化脚本可能导致账号风险，后果自负
4. 作者不对使用本脚本产生的任何问题负责

## 更新日志

- v1.0.0：初始版本，实现货币战争自动化全流程

## 贡献

欢迎提交Pull Request来帮助改进这个项目！无论是修复bug、添加新功能还是优化代码，你的贡献都将受到欢迎。

### 贡献方式

1. **报告问题**：在GitHub Issues中提交bug报告或功能请求
2. **修复bug**：解决现有Issues中的问题
3. **添加功能**：实现新功能或改进现有功能
4. **优化代码**：提高代码质量、性能或可维护性
5. **完善文档**：改进README.md或添加注释

### 开发流程

1. **创建分支**：从main分支创建新的功能分支
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **开发**：实现功能或修复bug
3. **测试**：确保代码能正常运行，通过所有测试
4. **提交**：提交代码，使用清晰的提交信息
   ```bash
   git commit -m "feat: 添加XXX功能"
   git commit -m "fix: 修复XXX bug"
   ```
5. **创建PR**：在GitHub上创建Pull Request，描述清楚你的变更

### 代码规范

1. **命名规范**：
   - 变量名：使用小写字母和下划线（snake_case）
   - 函数名：使用小写字母和下划线（snake_case）
   - 类名：使用驼峰命名（CamelCase）
2. **缩进**：使用4个空格缩进
3. **注释**：为复杂逻辑添加清晰的注释
4. **行长度**：每行不超过80个字符
5. **导入顺序**：标准库 → 第三方库 → 本地库

### PR提交指南

1. **标题**：简洁明了，使用动词开头
   - 例如："feat: 添加自动阵容选择功能"
   - 例如："fix: 修复ADB连接超时问题"
2. **描述**：
   - 清楚描述变更内容和原因
   - 关联相关Issue（如果有）
   - 说明如何测试你的变更
3. **代码质量**：确保代码符合项目的代码规范
4. **测试**：提供测试方法或测试结果
5. **文档**：如果添加了新功能，更新相关文档

### 测试要求

1. **功能测试**：确保你的变更能正常工作
2. **兼容性测试**：确保你的变更不会破坏现有功能
3. **性能测试**：确保你的变更不会导致性能下降
4. **稳定性测试**：确保你的变更能稳定运行

感谢你的贡献！

## License

MIT
