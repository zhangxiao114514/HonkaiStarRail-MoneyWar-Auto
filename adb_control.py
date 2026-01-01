#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB控制模块
负责设备连接、屏幕截图、触控操作等
"""

import os
import subprocess
import time
import re
from typing import Optional, Tuple, List

class ADBController:
    """ADB控制器类"""
    
    def __init__(self, adb_path: str = "adb", device_id: str = "", logger=None):
        """初始化ADB控制器
        
        Args:
            adb_path: ADB工具路径
            device_id: 设备ID，空字符串表示自动选择
            logger: 日志对象
        """
        self.adb_path = adb_path
        self.device_id = device_id
        self.logger = logger
        self.last_screenshot_time = 0
        
    def _run_cmd(self, cmd: str, timeout: int = 5, retry: int = 1) -> Optional[str]:
        """运行ADB命令
        
        Args:
            cmd: 要运行的命令
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
                self.logger.debug(f"运行ADB命令: {full_cmd}")
                
                # 运行命令
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
                    self.logger.error(f"ADB命令失败: {full_cmd}")
                    self.logger.error(f"错误输出: {result.stderr.strip()}")
                    
                    # 重试逻辑
                    if attempt < retry:
                        self.logger.info(f"第 {attempt + 1} 次重试...")
                        time.sleep(1)
                        continue
            except subprocess.TimeoutExpired:
                self.logger.error(f"ADB命令超时: {full_cmd}")
            except Exception as e:
                self.logger.error(f"运行ADB命令时出错: {str(e)}")
        
        return None
    
    def get_devices(self) -> List[str]:
        """获取连接的设备列表
        
        Returns:
            设备ID列表
        """
        output = self._run_cmd("devices")
        if not output:
            return []
        
        devices = []
        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith('List of devices'):
                parts = line.split('\t')
                if len(parts) >= 2 and parts[1] == 'device':
                    devices.append(parts[0])
        
        return devices
    
    def check_connection(self) -> bool:
        """检查ADB连接是否正常
        
        Returns:
            连接正常返回True，否则返回False
        """
        # 如果未指定设备ID，尝试自动选择
        if not self.device_id:
            devices = self.get_devices()
            if not devices:
                self.logger.error("未检测到连接的设备")
                return False
            
            # 选择第一个设备
            self.device_id = devices[0]
            self.logger.info(f"自动选择设备: {self.device_id}")
        
        # 检查设备是否在线
        output = self._run_cmd("shell echo 'test'")
        return output == "test"
    
    def screenshot(self, save_path: str = "screenshot.png") -> Optional[str]:
        """截取屏幕
        
        Args:
            save_path: 截图保存路径
            
        Returns:
            截图文件路径，失败返回None
        """
        try:
            # 检查截图频率，避免过于频繁
            current_time = time.time()
            if current_time - self.last_screenshot_time < 0.3:
                time.sleep(0.3 - (current_time - self.last_screenshot_time))
            
            # 使用ADB截图
            temp_path = "/sdcard/screenshot.png"
            cmd = f"shell screencap -p {temp_path}"
            
            if self._run_cmd(cmd, timeout=3):
                # 拉取截图到本地
                cmd = f"pull {temp_path} {save_path}"
                if self._run_cmd(cmd, timeout=5):
                    # 删除设备上的临时文件
                    self._run_cmd(f"shell rm {temp_path}", timeout=2)
                    self.last_screenshot_time = time.time()
                    return save_path
            
            return None
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return None
    
    def tap(self, x: int, y: int, delay: float = 0.1) -> bool:
        """点击屏幕
        
        Args:
            x: X坐标
            y: Y坐标
            delay: 点击延迟（秒）
            
        Returns:
            成功返回True，失败返回False
        """
        cmd = f"shell input tap {x} {y}"
        result = self._run_cmd(cmd, timeout=2)
        time.sleep(delay)
        return result is not None
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500, delay: float = 0.1) -> bool:
        """滑动屏幕
        
        Args:
            x1: 起始X坐标
            y1: 起始Y坐标
            x2: 结束X坐标
            y2: 结束Y坐标
            duration: 滑动持续时间（毫秒）
            delay: 操作延迟（秒）
            
        Returns:
            成功返回True，失败返回False
        """
        cmd = f"shell input swipe {x1} {y1} {x2} {y2} {duration}"
        result = self._run_cmd(cmd, timeout=3)
        time.sleep(delay)
        return result is not None
    
    def long_press(self, x: int, y: int, duration: int = 1000, delay: float = 0.1) -> bool:
        """长按屏幕
        
        Args:
            x: X坐标
            y: Y坐标
            duration: 长按持续时间（毫秒）
            delay: 操作延迟（秒）
            
        Returns:
            成功返回True，失败返回False
        """
        return self.swipe(x, y, x, y, duration, delay)
    
    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """获取屏幕尺寸
        
        Returns:
            (width, height) 元组，失败返回None
        """
        output = self._run_cmd("shell wm size")
        if not output:
            return None
        
        # 解析输出，例如: Physical size: 1080x2340
        match = re.search(r'\d+x\d+', output)
        if match:
            size = match.group(0).split('x')
            return (int(size[0]), int(size[1]))
        
        return None
    
    def wake_screen(self) -> bool:
        """唤醒屏幕
        
        Returns:
            成功返回True，失败返回False
        """
        # 发送电源键事件
        return self._run_cmd("shell input keyevent 26") is not None
    
    def unlock_screen(self) -> bool:
        """解锁屏幕
        
        Returns:
            成功返回True，失败返回False
        """
        # 唤醒屏幕
        self.wake_screen()
        
        # 滑动解锁
        screen_size = self.get_screen_size()
        if screen_size:
            width, height = screen_size
            # 从下往上滑动
            return self.swipe(width // 2, height * 3 // 4, width // 2, height // 4, 500)
        
        return False
    
    def install_app(self, apk_path: str) -> bool:
        """安装应用
        
        Args:
            apk_path: APK文件路径
            
        Returns:
            成功返回True，失败返回False
        """
        if not os.path.exists(apk_path):
            self.logger.error(f"APK文件不存在: {apk_path}")
            return False
        
        cmd = f"install -r {apk_path}"
        return self._run_cmd(cmd, timeout=60, retry=2) is not None
    
    def get_package_version(self, package_name: str) -> Optional[str]:
        """获取应用版本
        
        Args:
            package_name: 包名
            
        Returns:
            版本号，失败返回None
        """
        cmd = f"shell dumpsys package {package_name} | grep versionName"
        output = self._run_cmd(cmd)
        if output:
            match = re.search(r'versionName=(.*)', output)
            if match:
                return match.group(1)
        
        return None
    
    def force_stop(self, package_name: str) -> bool:
        """强制停止应用
        
        Args:
            package_name: 包名
            
        Returns:
            成功返回True，失败返回False
        """
        cmd = f"shell am force-stop {package_name}"
        return self._run_cmd(cmd) is not None
    
    def start_activity(self, package_name: str, activity_name: str) -> bool:
        """启动应用活动
        
        Args:
            package_name: 包名
            activity_name: 活动名
            
        Returns:
            成功返回True，失败返回False
        """
        cmd = f"shell am start -n {package_name}/{activity_name}"
        return self._run_cmd(cmd) is not None
    
    def is_package_in_foreground(self, package_name: str) -> bool:
        """检查应用是否在前台运行
        
        Args:
            package_name: 包名
            
        Returns:
            在前台返回True，否则返回False
        """
        # 获取当前前台应用包名
        cmd = "shell dumpsys activity activities | grep mResumedActivity"
        output = self._run_cmd(cmd)
        
        if output and package_name in output:
            self.logger.debug(f"应用 {package_name} 正在前台运行")
            return True
        
        self.logger.debug(f"应用 {package_name} 不在前台运行")
        return False
    
    def bring_to_foreground(self, package_name: str, activity_name: str = None) -> bool:
        """将应用切换到前台
        
        Args:
            package_name: 包名
            activity_name: 活动名，None表示使用默认活动
            
        Returns:
            成功返回True，失败返回False
        """
        # 检查是否已经在前台
        if self.is_package_in_foreground(package_name):
            self.logger.info(f"应用 {package_name} 已经在前台运行")
            return True
        
        self.logger.info(f"正在将应用 {package_name} 切换到前台")
        
        try:
            # 尝试使用am start命令启动或切换应用
            if activity_name:
                # 启动指定活动
                return self.start_activity(package_name, activity_name)
            else:
                # 启动应用默认活动
                cmd = f"shell am start -n {package_name}/.GameActivity || am start -n {package_name}/.MainActivity"
                return self._run_cmd(cmd) is not None
        except Exception as e:
            self.logger.error(f"切换应用到前台失败: {str(e)}")
            return False
    
    def switch_game_to_foreground(self, package_name: str, activity_name: str) -> bool:
        """切换游戏到前台，处理各种异常情况
        
        Args:
            package_name: 游戏包名
            activity_name: 游戏主活动名
            
        Returns:
            成功返回True，失败返回False
        """
        self.logger.info(f"尝试切换游戏 {package_name} 到前台")
        
        # 1. 检查设备是否解锁
        if not self.is_screen_on():
            self.logger.info("屏幕已关闭，正在唤醒并解锁")
            self.wake_screen()
            time.sleep(0.5)
            self.unlock_screen()
            time.sleep(1.0)
        
        # 2. 检查并切换游戏到前台
        max_attempts = 3
        for attempt in range(max_attempts):
            if self.bring_to_foreground(package_name, activity_name):
                self.logger.info(f"游戏成功切换到前台（第 {attempt + 1} 次尝试）")
                time.sleep(1.0)  # 等待游戏完全加载
                return True
            
            self.logger.warning(f"第 {attempt + 1} 次尝试切换游戏到前台失败，{max_attempts - attempt - 1} 次重试机会")
            time.sleep(2.0)
        
        self.logger.error("无法将游戏切换到前台")
        return False
    
    def is_screen_on(self) -> bool:
        """检查屏幕是否开启
        
        Returns:
            屏幕开启返回True，否则返回False
        """
        cmd = "shell dumpsys power | grep mWakefulness"
        output = self._run_cmd(cmd)
        
        if output and "Awake" in output:
            return True
        
        return False
