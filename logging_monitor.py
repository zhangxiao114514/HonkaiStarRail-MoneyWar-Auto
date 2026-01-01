#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志与状态监控模块
负责记录运行日志和监控脚本状态
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import threading

class Logger:
    """日志类"""
    
    def __init__(self, log_level: str = "INFO", log_file: str = "starrail_bot.log", enable_console: bool = True):
        """初始化日志
        
        Args:
            log_level: 日志级别
            log_file: 日志文件路径
            enable_console: 是否启用控制台日志
        """
        self.log_level = log_level.upper()
        self.log_file = log_file
        self.enable_console = enable_console
        
        # 创建日志目录
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 初始化日志配置
        self.logger = self._setup_logger()
        
        # 线程锁，确保日志线程安全
        self.lock = threading.Lock()
        
    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器
        
        Returns:
            配置好的日志记录器
        """
        # 创建日志记录器
        logger = logging.getLogger("StarRailBot")
        logger.setLevel(self.log_level)
        
        # 清除已有的处理器
        logger.handlers.clear()
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器，支持日志轮转
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def debug(self, message: str):
        """记录DEBUG级别的日志
        
        Args:
            message: 日志消息
        """
        with self.lock:
            self.logger.debug(message)
    
    def info(self, message: str):
        """记录INFO级别的日志
        
        Args:
            message: 日志消息
        """
        with self.lock:
            self.logger.info(message)
    
    def warning(self, message: str):
        """记录WARNING级别的日志
        
        Args:
            message: 日志消息
        """
        with self.lock:
            self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """记录ERROR级别的日志
        
        Args:
            message: 日志消息
            exc_info: 是否记录异常信息
        """
        with self.lock:
            self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """记录CRITICAL级别的日志
        
        Args:
            message: 日志消息
            exc_info: 是否记录异常信息
        """
        with self.lock:
            self.logger.critical(message, exc_info=exc_info)
    
    def set_level(self, level: str):
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        level = level.upper()
        self.log_level = level
        
        # 更新日志记录器级别
        self.logger.setLevel(level)
        
        # 更新所有处理器的级别
        for handler in self.logger.handlers:
            handler.setLevel(level)
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径
        
        Returns:
            日志文件路径
        """
        return self.log_file
    
    def get_log_content(self, lines: int = 100) -> str:
        """获取日志内容
        
        Args:
            lines: 要获取的行数
            
        Returns:
            日志内容
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            # 返回最后N行
            return ''.join(log_lines[-lines:])
        except Exception as e:
            self.error(f"读取日志文件失败: {str(e)}")
            return ""
    
    def clear_log(self) -> bool:
        """清空日志文件
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 关闭所有处理器
            for handler in self.logger.handlers:
                handler.close()
            
            # 清空日志文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            # 重新设置日志处理器
            self.logger = self._setup_logger()
            return True
        except Exception as e:
            self.error(f"清空日志文件失败: {str(e)}")
            return False
    
    def export_log(self, export_path: str = None) -> str:
        """导出日志文件
        
        Args:
            export_path: 导出路径，None表示使用默认命名
            
        Returns:
            导出的日志文件路径
        """
        try:
            if not export_path:
                # 使用默认命名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                export_path = f"starrail_bot_log_{timestamp}.log"
            
            # 复制日志文件
            with open(self.log_file, 'r', encoding='utf-8') as src:
                with open(export_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            self.info(f"日志已导出到: {export_path}")
            return export_path
        except Exception as e:
            self.error(f"导出日志文件失败: {str(e)}")
            return ""

class StatusMonitor:
    """状态监控类"""
    
    def __init__(self, logger: Logger):
        """初始化状态监控
        
        Args:
            logger: 日志对象
        """
        self.logger = logger
        self.start_time = datetime.now()
        
        # 状态信息
        self.status = {
            'running': False,
            'current_scene': "UNKNOWN",
            'current_score': 0,
            'total_battles': 0,
            'win_count': 0,
            'win_rate': 0.0,
            'execution_time': "00:00:00",
            'last_operation': "初始化",
            'last_operation_time': datetime.now(),
            'current_credits': 0,
            'equipment_score': 0,
            'transaction_count': 0
        }
        
        # 操作日志记录
        self.operation_log = []
        self.max_log_entries = 1000  # 最大日志条目数
        
        # 线程锁
        self.lock = threading.Lock()
    
    def update_status(self, **kwargs):
        """更新状态信息
        
        Args:
            **kwargs: 要更新的状态字段
        """
        with self.lock:
            for key, value in kwargs.items():
                if key in self.status:
                    self.status[key] = value
            
            # 更新执行时间
            self.status['execution_time'] = str(datetime.now() - self.start_time).split('.')[0]
    
    def get_status(self) -> dict:
        """获取当前状态
        
        Returns:
            当前状态字典
        """
        with self.lock:
            return self.status.copy()
    
    def start_monitoring(self):
        """开始监控
        """
        self.status['running'] = True
        self.status['start_time'] = datetime.now()
        self.logger.info("状态监控已启动")
    
    def stop_monitoring(self):
        """停止监控
        """
        self.status['running'] = False
        self.logger.info("状态监控已停止")
    
    def log_status(self):
        """记录当前状态到日志
        """
        with self.lock:
            status_str = " | ".join([f"{k}: {v}" for k, v in self.status.items()])
            self.logger.info(f"当前状态: {status_str}")
    
    def get_status_string(self) -> str:
        """获取状态字符串
        
        Returns:
            状态字符串
        """
        with self.lock:
            return " | ".join([f"{k}: {v}" for k, v in self.status.items()])
    
    def reset(self):
        """重置状态
        """
        with self.lock:
            self.__init__(self.logger)
            self.logger.info("状态监控已重置")
    
    def log_operation(self, operation_name: str, success: bool, details: dict = None):
        """记录操作日志
        
        Args:
            operation_name: 操作名称
            success: 操作是否成功
            details: 操作详细信息
        """
        with self.lock:
            # 创建日志条目
            log_entry = {
                'timestamp': datetime.now(),
                'operation': operation_name,
                'success': success,
                'details': details or {}
            }
            
            # 添加到日志列表
            self.operation_log.append(log_entry)
            
            # 限制日志数量
            if len(self.operation_log) > self.max_log_entries:
                self.operation_log.pop(0)  # 移除最早的日志
            
            # 更新状态
            self.status['last_operation'] = operation_name
            self.status['last_operation_time'] = datetime.now()
            
            # 记录到日志文件
            status = "成功" if success else "失败"
            details_str = f"，详情: {details}" if details else ""
            self.logger.info(f"操作: {operation_name}，状态: {status}{details_str}")
    
    def export_operation_log(self, export_path: str = None) -> str:
        """导出操作日志
        
        Args:
            export_path: 导出路径，None表示使用默认命名
            
        Returns:
            导出的日志文件路径
        """
        try:
            if not export_path:
                # 使用默认命名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                export_path = f"operation_log_{timestamp}.json"
            
            # 导出为JSON格式
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.operation_log, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"操作日志已导出到: {export_path}")
            return export_path
        except Exception as e:
            self.logger.error(f"导出操作日志失败: {str(e)}")
            return ""
    
    def get_operation_log(self, limit: int = 50) -> list:
        """获取操作日志
        
        Args:
            limit: 返回的日志数量
            
        Returns:
            操作日志列表
        """
        with self.lock:
            return self.operation_log[-limit:]
    
    def get_operation_summary(self) -> dict:
        """获取操作统计摘要
        
        Returns:
            操作统计字典
        """
        with self.lock:
            total_operations = len(self.operation_log)
            success_operations = sum(1 for log in self.operation_log if log['success'])
            
            # 按操作类型统计
            operation_types = {}
            for log in self.operation_log:
                op_name = log['operation']
                if op_name not in operation_types:
                    operation_types[op_name] = {'total': 0, 'success': 0}
                
                operation_types[op_name]['total'] += 1
                if log['success']:
                    operation_types[op_name]['success'] += 1
            
            return {
                'total_operations': total_operations,
                'success_rate': success_operations / total_operations if total_operations > 0 else 0,
                'operation_types': operation_types,
                'log_duration': str(datetime.now() - self.start_time).split('.')[0]
            }
    
    def update_with_game_data(self, score: int = None, credits: int = None, equipment_score: int = None):
        """使用游戏数据更新状态
        
        Args:
            score: 当前积分
            credits: 当前星穹
            equipment_score: 装备评分
        """
        with self.lock:
            updated = False
            
            if score is not None and score != self.status['current_score']:
                old_score = self.status['current_score']
                self.status['current_score'] = score
                self.logger.info(f"积分变化: {old_score} → {score} (变化: +{score - old_score})")
                updated = True
            
            if credits is not None and credits != self.status['current_credits']:
                old_credits = self.status['current_credits']
                self.status['current_credits'] = credits
                self.logger.info(f"星穹变化: {old_credits} → {credits} (变化: +{credits - old_credits})")
                updated = True
            
            if equipment_score is not None and equipment_score != self.status['equipment_score']:
                self.status['equipment_score'] = equipment_score
                self.logger.info(f"装备评分: {equipment_score}")
                updated = True
            
            if updated:
                self.log_operation("状态更新", True, {
                    'score': self.status['current_score'],
                    'credits': self.status['current_credits'],
                    'equipment_score': self.status['equipment_score']
                })
