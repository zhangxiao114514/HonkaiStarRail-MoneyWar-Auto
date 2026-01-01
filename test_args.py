#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试命令行参数解析功能
"""

import argparse

def test_argparse():
    """测试参数解析"""
    print("=== 测试命令行参数解析 ===")
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="《崩坏：星穹铁道》货币战争自动化脚本")
    
    # 添加参数
    parser.add_argument(
        "-c", "--cycles", 
        type=int, 
        default=0, 
        help="运行周期数，0表示无限循环"
    )
    parser.add_argument(
        "-l", "--log-level", 
        type=str, 
        default="INFO", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别"
    )
    parser.add_argument(
        "--template-dir", 
        type=str, 
        default=None,
        help="模板目录路径"
    )
    parser.add_argument(
        "--adb-path", 
        type=str, 
        default=None,
        help="ADB可执行文件路径"
    )
    parser.add_argument(
        "-s", "--device", 
        type=str, 
        default=None,
        help="指定设备ID，不指定则自动检测并使用第一个设备"
    )
    parser.add_argument(
        "--all-devices", 
        action="store_true",
        help="在所有连接的设备上运行脚本"
    )
    parser.add_argument(
        "-n", "--dry-run", 
        action="store_true",
        help="模拟运行，不执行实际操作"
    )
    parser.add_argument(
        "--save-progress", 
        action="store_true",
        help="保存运行进度，支持断点续跑"
    )
    parser.add_argument(
        "--progress-file", 
        type=str, 
        default="progress.json",
        help="进度保存文件路径"
    )
    parser.add_argument(
        "--resume", 
        action="store_true",
        help="从保存的进度中恢复运行"
    )
    
    # 打印帮助信息
    print("\n1. 帮助信息:")
    parser.print_help()
    
    # 测试解析
    print("\n2. 解析测试:")
    test_args = [
        "-c", "10",
        "-l", "DEBUG",
        "-s", "device123",
        "--save-progress",
        "--progress-file", "test_progress.json"
    ]
    
    args = parser.parse_args(test_args)
    print(f"   解析结果: {args}")
    print(f"   cycles: {args.cycles}")
    print(f"   log_level: {args.log_level}")
    print(f"   device: {args.device}")
    print(f"   save_progress: {args.save_progress}")
    print(f"   progress_file: {args.progress_file}")
    print(f"   all_devices: {args.all_devices}")
    print(f"   dry_run: {args.dry_run}")
    print(f"   resume: {args.resume}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_argparse()
