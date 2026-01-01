#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件模块
"""

import os
import json
from dataclasses import dataclass, field

@dataclass
class Config:
    """配置类"""
    
    # ------------------------------
    # ADB 配置
    # ------------------------------
    adb_path: str = "adb"  # ADB工具路径，默认使用系统PATH中的adb
    device_id: str = ""     # 设备ID，空字符串表示自动选择
    adb_timeout: int = 5    # ADB命令超时时间（秒）
    
    # ------------------------------
    # OCR 配置
    # ------------------------------
    ocr_type: str = "paddle"  # OCR类型：paddle 或 tesseract
    paddle_ocr_path: str = ""  # PaddleOCR安装路径
    tesseract_path: str = "tesseract"  # Tesseract可执行文件路径
    tesseract_data_path: str = ""  # Tesseract训练数据路径
    ocr_language: str = "chi_sim"  # OCR识别语言
    ocr_confidence: float = 0.8  # OCR置信度阈值
    
    # ------------------------------
    # 图像处理配置
    # ------------------------------
    screenshot_method: str = "adb"  # 截图方式：adb 或 scrcpy
    screenshot_quality: int = 80  # 截图质量（0-100）
    grayscale: bool = True  # 是否转为灰度图
    blur_kernel: int = 3  # 模糊处理内核大小
    contrast: float = 1.2  # 对比度调整因子
    brightness: int = 10  # 亮度调整值
    threshold: int = 128  # 二值化阈值
    
    # ------------------------------
    # 自动化流程配置
    # ------------------------------
    loop_count: int = 10  # 循环执行次数，0表示无限循环
    loop_interval: int = 5  # 循环间隔（秒）
    retry_interval: int = 3  # 失败重试间隔（秒）
    max_retries: int = 3  # 最大重试次数
    operation_delay: float = 0.5  # 操作间隔（秒）
    long_operation_delay: float = 2.0  # 长操作间隔（秒）
    
    # ------------------------------
    # 场景识别配置
    # ------------------------------
    scene_recognition_threshold: float = 0.8  # 场景识别阈值
    template_matching_threshold: float = 0.8  # 模板匹配阈值
    
    # ------------------------------
    # 日志配置
    # ------------------------------
    log_level: str = "INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_file: str = "starrail_bot.log"  # 日志文件路径
    enable_console_log: bool = True  # 是否启用控制台日志
    log_max_size: int = 10 * 1024 * 1024  # 日志文件最大大小（字节）
    log_backup_count: int = 5  # 日志文件备份数量
    
    # ------------------------------
    # 识别参数配置
    # ------------------------------
    score_recognition_area: tuple = field(default_factory=lambda: (100, 50, 300, 100))  # 积分识别区域 (x, y, w, h)
    battle_button_area: tuple = field(default_factory=lambda: (800, 1500, 200, 100))  # 战斗按钮区域
    collect_button_area: tuple = field(default_factory=lambda: (800, 1600, 200, 100))  # 领取按钮区域
    
    # ------------------------------
    # 游戏窗口配置
    # ------------------------------
    game_package: str = "com.miHoYo.hkrpg"  # 游戏包名
    game_activity: str = "com.miHoYo.hkrpg.GameActivity"  # 游戏主活动名
    window_switch_delay: float = 1.0  # 窗口切换延迟（秒）
    
    # ------------------------------
    # 装备识别配置
    # ------------------------------
    equipment_recognition_area: tuple = field(default_factory=lambda: (200, 300, 800, 1200))  # 装备识别区域
    equipment_threshold: float = 0.7  # 装备识别阈值
    max_equipment_level: int = 80  # 最大装备等级
    optimal_equipment_attributes: list = field(default_factory=lambda: ["暴击", "暴伤", "攻击", "速度"])
    
    # ------------------------------
    # 交易系统配置
    # ------------------------------
    transaction_area: tuple = field(default_factory=lambda: (100, 200, 1000, 1400))  # 交易区域
    max_buy_price: int = 10000  # 最大购买价格
    min_sell_price: int = 5000  # 最小出售价格
    transaction_delay: float = 1.5  # 交易操作延迟
    
    # ------------------------------
    # 调试配置
    # ------------------------------
    debug_mode: bool = False  # 是否启用调试模式
    save_screenshots: bool = False  # 是否保存截图到本地
    screenshot_save_path: str = "screenshots"  # 截图保存路径
    
    def __post_init__(self):
        """初始化后处理"""
        # 创建截图保存目录
        if self.save_screenshots and not os.path.exists(self.screenshot_save_path):
            os.makedirs(self.screenshot_save_path)
    
    def load_from_file(self, config_file: str = "config.json"):
        """从JSON文件加载配置"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新配置
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                # 重新初始化后处理
                self.__post_init__()
                return True
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return False
        return False
    
    def save_to_file(self, config_file: str = "config.json"):
        """将配置保存到JSON文件"""
        try:
            # 转换为字典
            config_dict = {
                key: value for key, value in self.__dict__.items()
                if not key.startswith('_')  # 排除私有属性
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
