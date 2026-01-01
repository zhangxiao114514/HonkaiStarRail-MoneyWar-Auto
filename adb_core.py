#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB核心模块
仅使用ADB原生命令，提供基础操作封装
"""

import os
import subprocess
import time
import random
import re
from typing import Optional, Tuple, List

class ADBCore:
    """ADB核心操作类"""
    
    def __init__(self, adb_path: str = "adb", logger=None):
        """初始化ADB核心
        
        Args:
            adb_path: ADB工具路径
            logger: 日志对象
        """
        self.adb_path = adb_path
        self.logger = logger
        self.device_id = ""
        self.resolution = (1280, 720)  # 默认分辨率
        self.last_screenshot_time = 0
        
    def log(self, message: str):
        """日志记录
        
        Args:
            message: 日志消息
        """
        if self.logger:
            self.logger(message)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def _run_cmd(self, cmd: str, timeout: int = 10, retry: int = 1) -> Optional[str]:
        """运行ADB命令
        
        Args:
            cmd: 命令内容
            timeout: 超时时间（秒）
            retry: 重试次数
            
        Returns:
            命令输出，失败返回None
        """
        full_cmd = f"{self.adb_path}"
        
        # 添加设备ID
        if self.device_id:
            full_cmd += f" -s {self.device_id}"
        
        full_cmd += f" {cmd}"
        
        for attempt in range(retry + 1):
            try:
                self.log(f"ADB命令: {full_cmd}")
                
                result = subprocess.run(
                    full_cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    self.log(f"ADB命令失败: {result.stderr.strip()}")
                    if attempt < retry:
                        self.log(f"第 {attempt + 1} 次重试...")
                        time.sleep(1)
            except subprocess.TimeoutExpired:
                self.log(f"ADB命令超时: {full_cmd}")
            except Exception as e:
                self.log(f"ADB命令执行错误: {str(e)}")
        
        return None
    
    def check_connection(self) -> bool:
        """检查ADB连接
        
        Returns:
            连接成功返回True，否则返回False
        """
        self.log("检查ADB连接...")
        
        # 获取设备列表
        devices = self.get_devices()
        if not devices:
            self.log("未检测到连接的设备")
            return False
        
        # 选择第一个设备
        self.device_id = devices[0]
        self.log(f"使用设备: {self.device_id}")
        
        # 检查设备分辨率
        if not self.check_resolution():
            self.log("设备分辨率不符合要求，需设置为1280x720")
            return False
        
        self.log("ADB连接正常")
        return True
    
    def get_devices(self) -> List[str]:
        """获取连接的设备列表
        
        Returns:
            设备ID列表
        """
        output = self._run_cmd("devices")
        devices = []
        
        if output:
            for line in output.split('\n'):
                line = line.strip()
                if line and not line.startswith('List of devices'):
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[1] == 'device':
                        devices.append(parts[0])
        
        return devices
    
    def check_resolution(self) -> bool:
        """检查设备分辨率（强制1280x720）
        
        Returns:
            分辨率符合要求返回True，否则返回False
        """
        output = self._run_cmd("shell wm size")
        if output is None:
            self.log("无法获取设备分辨率")
            return False
        
        # 解析分辨率
        match = re.search(r'Physical size: (\d+)x(\d+)', output)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            self.resolution = (width, height)
            
            self.log(f"当前分辨率: {width}x{height}")
            
            # 检查是否符合要求（1280x720）
            if width == 1280 and height == 720:
                return True
        
        return False
    
    def screenshot(self, save_path: str = "screenshot.png") -> Optional[str]:
        """截取屏幕
        
        Args:
            save_path: 保存路径
            
        Returns:
            截图路径，失败返回None
        """
        # 检查截图频率
        current_time = time.time()
        if current_time - self.last_screenshot_time < 0.5:
            time.sleep(0.5 - (current_time - self.last_screenshot_time))
        
        temp_path = "/sdcard/screenshot.png"
        
        # 截图命令
        if self._run_cmd(f"shell screencap -p {temp_path}"):
            # 拉取截图
            if self._run_cmd(f"pull {temp_path} {save_path}"):
                # 删除临时文件
                self._run_cmd(f"shell rm {temp_path}", timeout=2)
                self.last_screenshot_time = time.time()
                return save_path
        
        return None
    
    def tap(self, x: int, y: int, delay: float = 0.0):
        """点击屏幕
        
        Args:
            x: X坐标
            y: Y坐标
            delay: 点击后延迟时间
        """
        cmd = f"shell input tap {x} {y}"
        self._run_cmd(cmd)
        
        # 添加随机延迟
        if delay > 0:
            time.sleep(delay)
        else:
            # 随机延迟0.5-1.5秒
            random_delay = random.uniform(0.5, 1.5)
            self.log(f"随机延迟: {random_delay:.2f}秒")
            time.sleep(random_delay)
    
    def keyevent(self, keycode: int):
        """发送按键事件
        
        Args:
            keycode: 按键代码
        """
        cmd = f"shell input keyevent {keycode}"
        self._run_cmd(cmd)
        time.sleep(random.uniform(0.5, 1.5))
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500):
        """滑动屏幕
        
        Args:
            x1: 起始X坐标
            y1: 起始Y坐标
            x2: 结束X坐标
            y2: 结束Y坐标
            duration: 滑动持续时间（毫秒）
        """
        cmd = f"shell input swipe {x1} {y1} {x2} {y2} {duration}"
        self._run_cmd(cmd)
        time.sleep(random.uniform(0.5, 1.5))
    
    def get_resolution(self) -> Tuple[int, int]:
        """获取设备分辨率
        
        Returns:
            分辨率 (width, height)
        """
        return self.resolution
    
    def close_popup(self):
        """关闭弹窗（点击屏幕中心偏下位置）
        
        用于关闭系统公告等弹窗
        """
        x, y = 640, 600  # 1280x720分辨率下的关闭位置
        self.log("尝试关闭弹窗")
        self.tap(x, y)
    
    def get_device_id(self) -> str:
        """获取当前设备ID
        
        Returns:
            设备ID
        """
        return self.device_id
