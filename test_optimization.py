#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后代码测试脚本
"""

print("=== 测试优化后代码 ===")

# 测试配置模块
print("\n1. 测试配置模块:")
try:
    from config import get_config, validate_config
    config = get_config()
    is_valid, message = validate_config(config)
    print(f"   配置加载成功: {is_valid}, {message}")
    print(f"   配置项: {list(config.keys())}")
except Exception as e:
    print(f"   配置模块测试失败: {str(e)}")

# 测试日志模块
print("\n2. 测试日志模块:")
try:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("测试日志输出")
    print("   日志模块测试成功")
except Exception as e:
    print(f"   日志模块测试失败: {str(e)}")

# 测试ADB核心模块
print("\n3. 测试ADB核心模块:")
try:
    from adb_core import ADBCore
    adb = ADBCore(logger=logger)
    print(f"   ADB核心模块测试成功")
except Exception as e:
    print(f"   ADB核心模块测试失败: {str(e)}")

# 测试模板匹配模块
print("\n4. 测试模板匹配模块:")
try:
    from template_matcher import TemplateMatcher
    matcher = TemplateMatcher(logger=logger)
    print(f"   模板匹配模块测试成功")
except Exception as e:
    print(f"   模板匹配模块测试失败: {str(e)}")

print("\n=== 测试完成 ===")
