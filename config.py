#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os

# 配置参数
CONFIG = {
    # ADB配置
    'adb_path': 'adb',
    'device_id': '',  # 空字符串表示自动选择第一个设备
    
    # 模板配置
    'template_dir': 'templates',
    'template_auto_update': False,  # 是否自动更新模板
    'threshold': 0.8,  # 模板匹配阈值
    'threshold_min': 0.7,  # 最低匹配阈值
    'threshold_max': 0.95,  # 最高匹配阈值
    
    # 运行配置
    'resolution': (1280, 720),  # 目标分辨率
    'max_retries': 3,  # 操作重试次数
    'timeout': 10,  # 操作超时时间（秒）
    'cycle_delay_min': 1,  # 周期间最小延迟（秒）
    'cycle_delay_max': 3,  # 周期间最大延迟（秒）
    'failure_delay_min': 3,  # 失败后最小延迟（秒）
    'failure_delay_max': 5,  # 失败后最大延迟（秒）
    
    # 模板列表
    'templates': {
        'money_war_entry': '货币战争入口',
        'auto_battle': '自动战斗按钮',
        'settlement_confirm': '结算确认按钮'
    },
    
    # 固定坐标（仅1280x720分辨率）
    'fixed_coords': {
        'close_popup': (640, 600),  # 关闭弹窗位置
        'battle_retry': (640, 400),  # 战斗失败重试位置
        'back_button': (50, 50),  # 返回按钮位置
        'stage_select': (640, 400)  # 关卡选择位置
    },
    
    # OCR识别区域
    'ocr_regions': {
        'battle_result': (400, 200, 480, 100)  # 战斗结果识别区域
    },
    
    # 日志配置
    'log_level': 'INFO',  # 日志级别
    'log_file': 'logs/starrail_money_war.log',  # 日志文件路径
    'log_max_size': 10 * 1024 * 1024,  # 日志文件最大大小（字节）
    'log_backup_count': 5,  # 日志文件备份数量
    
    # 进度配置
    'save_progress': False,  # 是否自动保存进度
    'progress_file': 'progress.json',  # 进度文件路径
    'progress_save_interval': 1,  # 进度保存间隔（周期数）
    
    # 调试配置
    'dry_run': False,  # 模拟运行模式
    'debug_mode': False,  # 调试模式
    'screenshot_debug': False  # 截图调试模式
}

def get_config():
    """
    获取配置
    
    Returns:
        dict: 配置字典
    """
    return CONFIG

def validate_config(config):
    """
    验证配置有效性
    
    Args:
        config: 配置字典
    
    Returns:
        bool: 配置是否有效
    """
    # 检查必填字段
    required_fields = ['adb_path', 'template_dir', 'max_retries', 'timeout', 'threshold']
    for field in required_fields:
        if field not in config:
            return False, f"缺少必填配置项: {field}"
    
    # 验证模板目录是否存在
    template_dir = config['template_dir']
    if not os.path.exists(template_dir):
        # 创建模板目录
        try:
            os.makedirs(template_dir, exist_ok=True)
        except Exception as e:
            return False, f"创建模板目录失败: {str(e)}"
    
    return True, "配置有效"
