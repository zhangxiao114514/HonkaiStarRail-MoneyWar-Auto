#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os

# 配置参数
CONFIG = {
    'adb_path': 'adb',
    'template_dir': 'templates',
    'max_retries': 3,
    'timeout': 10,
    'threshold': 0.8,
    'resolution': (1280, 720),
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
    }
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
