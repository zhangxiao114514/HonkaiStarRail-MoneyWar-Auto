#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《崩坏：星穹铁道》货币战争自动化脚本
主入口文件
"""

import os
import time
import cv2
import random
import logging
from adb_core import ADBCore
from template_matcher import TemplateMatcher
from config import get_config, validate_config

# 获取配置
CONFIG = get_config()

# 验证配置
is_valid, message = validate_config(CONFIG)
if not is_valid:
    print(f"配置验证失败: {message}")
    exit(1)

class StarRailMoneyWarBot:
    """星穹铁道货币战争机器人"""
    
    def __init__(self):
        """初始化机器人"""
        # 配置日志
        self._setup_logger()
        
        # 初始化ADB核心
        self.adb = ADBCore(logger=self.logger)
        
        # 初始化模板匹配器
        self.matcher = TemplateMatcher(logger=self.logger)
        
        # 加载模板
        self._load_templates()
        
        # 运行状态
        self.running = False
        self.total_battles = 0
    
    def _setup_logger(self):
        """配置日志"""
        # 创建日志目录
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志格式
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        
        # 设置日志级别
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "starrail_money_war.log")),
                logging.StreamHandler()
            ]
        )
        
        # 获取日志记录器
        self.logger = logging.getLogger(__name__)
    
    def _logger(self, message: str):
        """日志输出（兼容旧代码）
        
        Args:
            message: 日志消息
        """
        self.logger.info(message)
    
    def _load_templates(self):
        """加载模板"""
        self.logger.info("加载模板...")
        
        for template_name, description in CONFIG['templates'].items():
            template_path = os.path.join(CONFIG['template_dir'], f"{template_name}.png")
            if os.path.exists(template_path):
                self.matcher.load_template(template_name, template_path)
            else:
                self.logger.info(f"模板不存在: {template_path}，将在运行时自动生成")
    
    def _generate_templates(self):
        """生成模板"""
        self.logger.info("生成模板...")
        
        # 获取屏幕截图
        screenshot_path = self.adb.screenshot()
        if not screenshot_path:
            self.logger.error("无法获取屏幕截图，模板生成失败")
            return False
        
        image = cv2.imread(screenshot_path)
        if image is None:
            self.logger.error("无法加载截图，模板生成失败")
            return False
        
        # 这里需要根据实际情况调整模板区域
        # 以下是示例坐标，实际使用时需要调整
        template_regions = {
            'money_war_entry': (500, 300, 300, 100),
            'auto_battle': (1100, 600, 150, 50),
            'settlement_confirm': (600, 650, 200, 60)
        }
        
        for template_name, region in template_regions.items():
            self.matcher.save_template(template_name, image, region)
            # 立即加载生成的模板
            template_path = os.path.join(CONFIG['template_dir'], f"{template_name}.png")
            self.matcher.load_template(template_name, template_path)
        
        return True
    
    def _wait_and_retry(self, func, retries=3, timeout=10):
        """等待并重试
        
        Args:
            func: 要执行的函数
            retries: 重试次数
            timeout: 超时时间
            
        Returns:
            函数执行结果
        """
        start_time = time.time()
        
        for attempt in range(retries + 1):
            result = func()
            if result:
                return result
            
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.logger.warning(f"操作超时")
                return False
            
            self.logger.info(f"操作失败，第 {attempt + 1} 次重试...")
            time.sleep(random.uniform(0.5, 1.5))
        
        return False
    
    def _check_popup(self):
        """检查并关闭弹窗"""
        # 这里简化处理，直接点击固定位置关闭弹窗
        self.logger.info("检查并关闭弹窗")
        self.adb.tap(*CONFIG['fixed_coords']['close_popup'])
    
    def _enter_money_war(self):
        """进入货币战争玩法"""
        self.logger.info("进入货币战争玩法")
        
        def _do_enter():
            # 1. 截图
            screenshot_path = self.adb.screenshot()
            if not screenshot_path:
                return False
            
            # 2. 加载图像
            image = cv2.imread(screenshot_path)
            if image is None:
                return False
            
            # 3. 匹配货币战争入口
            coords = self.matcher.match_template(image, 'money_war_entry', CONFIG['threshold'])
            if coords:
                # 4. 点击入口
                self.adb.tap(*coords)
                time.sleep(2)  # 长延迟
                return True
            
            return False
        
        return self._wait_and_retry(_do_enter)
    
    def _select_stage(self):
        """选择关卡"""
        self.logger.info("选择关卡")
        # 使用固定坐标点击关卡
        self.adb.tap(*CONFIG['fixed_coords']['stage_select'])
        time.sleep(1.5)
        return True
    
    def _start_auto_battle(self):
        """开始自动战斗"""
        self.logger.info("开始自动战斗")
        
        def _do_start_battle():
            # 1. 截图
            screenshot_path = self.adb.screenshot()
            if not screenshot_path:
                return False
            
            # 2. 加载图像
            image = cv2.imread(screenshot_path)
            if image is None:
                return False
            
            # 3. 匹配自动战斗按钮
            coords = self.matcher.match_template(image, 'auto_battle', CONFIG['threshold'])
            if coords:
                # 4. 点击自动战斗
                self.adb.tap(*coords)
                time.sleep(1.5)
                return True
            
            return False
        
        return self._wait_and_retry(_do_start_battle)
    
    def _wait_for_battle_end(self):
        """等待战斗结束"""
        self.logger.info("等待战斗结束...")
        
        start_time = time.time()
        
        while time.time() - start_time < 60:  # 最大等待60秒
            # 截图
            screenshot_path = self.adb.screenshot()
            if not screenshot_path:
                continue
            
            # 加载图像
            image = cv2.imread(screenshot_path)
            if image is None:
                continue
            
            # 检查是否显示结算界面
            coords = self.matcher.match_template(image, 'settlement_confirm', CONFIG['threshold'])
            if coords:
                self.logger.info("战斗结束，进入结算界面")
                return True
            
            # OCR识别战斗结果
            battle_result = self.matcher.ocr_simple_text(image, CONFIG['ocr_regions']['battle_result'])
            if '胜利' in battle_result or '失败' in battle_result:
                self.logger.info(f"战斗结果: {battle_result}")
                
                # 战斗失败处理
                if '失败' in battle_result:
                    self.logger.warning("战斗失败，点击重试")
                    self.adb.tap(*CONFIG['fixed_coords']['battle_retry'])
                    time.sleep(2)
                    # 重新开始自动战斗
                    self._start_auto_battle()
                
                continue
            
            # 随机延迟
            time.sleep(random.uniform(1, 3))
        
        return False
    
    def _handle_settlement(self):
        """处理结算"""
        self.logger.info("处理结算")
        
        def _do_settlement():
            # 1. 截图
            screenshot_path = self.adb.screenshot()
            if not screenshot_path:
                return False
            
            # 2. 加载图像
            image = cv2.imread(screenshot_path)
            if image is None:
                return False
            
            # 3. 匹配结算确认按钮
            coords = self.matcher.match_template(image, 'settlement_confirm', CONFIG['threshold'])
            if coords:
                # 4. 点击确认
                self.adb.tap(*coords)
                time.sleep(2)
                return True
            
            return False
        
        return self._wait_and_retry(_do_settlement)
    
    def _return_to_entry(self):
        """返回入口界面"""
        self.logger.info("返回入口界面")
        
        # 点击返回按钮
        self.adb.tap(*CONFIG['fixed_coords']['back_button'])
        time.sleep(1.5)
        
        # 再次点击返回，确保回到主界面
        self.adb.tap(*CONFIG['fixed_coords']['back_button'])
        time.sleep(1.5)
        
        return True
    
    def run_cycle(self):
        """运行一个完整周期"""
        self.logger.info("=== 开始货币战争自动化周期 ===")
        
        try:
            # 1. 检查并关闭弹窗
            self._check_popup()
            
            # 2. 进入货币战争
            if not self._enter_money_war():
                self.logger.error("进入货币战争失败")
                return False
            
            # 3. 选择关卡
            if not self._select_stage():
                self.logger.error("选择关卡失败")
                return False
            
            # 4. 开始自动战斗
            if not self._start_auto_battle():
                self.logger.error("开始自动战斗失败")
                return False
            
            # 5. 等待战斗结束
            if not self._wait_for_battle_end():
                self.logger.error("战斗超时")
                return False
            
            # 6. 处理结算
            if not self._handle_settlement():
                self.logger.error("处理结算失败")
                return False
            
            # 7. 返回入口界面
            if not self._return_to_entry():
                self.logger.error("返回入口界面失败")
                return False
            
            # 8. 增加战斗计数
            self.total_battles += 1
            self.logger.info(f"=== 周期完成，总战斗次数: {self.total_battles} ===")
            
            return True
            
        except Exception as e:
            self.logger.error(f"周期执行出错: {str(e)}", exc_info=True)
            return False
    
    def start(self, cycles=0):
        """启动机器人
        
        Args:
            cycles: 运行周期数，0表示无限循环
        """
        self.logger.info("=== 启动星穹铁道货币战争自动化脚本 ===")
        
        # 检查ADB连接
        if not self.adb.check_connection():
            self.logger.error("ADB连接失败，脚本退出")
            return
        
        # 检查模板是否存在，不存在则生成
        has_templates = all(
            os.path.exists(os.path.join(CONFIG['template_dir'], f"{name}.png"))
            for name in CONFIG['templates']
        )
        
        if not has_templates:
            self.logger.info("模板不存在，尝试自动生成")
            if not self._generate_templates():
                self.logger.error("模板生成失败，脚本退出")
                return
        
        # 开始运行
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                # 运行一个周期
                success = self.run_cycle()
                
                # 增加周期计数
                cycle_count += 1
                
                # 检查是否达到指定周期数
                if cycles > 0 and cycle_count >= cycles:
                    self.logger.info(f"已完成 {cycles} 个周期，脚本退出")
                    break
                
                # 循环间隔
                if success:
                    delay = random.uniform(1, 3)
                    self.logger.info(f"休息 {delay:.2f} 秒后开始下一个周期")
                    time.sleep(delay)
                else:
                    # 失败时增加延迟
                    delay = random.uniform(3, 5)
                    self.logger.warning(f"周期失败，休息 {delay:.2f} 秒后重试")
                    time.sleep(delay)
                    # 尝试关闭弹窗
                    self._check_popup()
                    
        except KeyboardInterrupt:
            self.logger.info("用户中断，脚本退出")
        except Exception as e:
            self.logger.error(f"脚本运行出错: {str(e)}", exc_info=True)
        finally:
            self.running = False
            self.logger.info("=== 脚本已停止 ===")
    
    def stop(self):
        """停止机器人"""
        self.running = False


def main():
    """主函数"""
    import argparse
    
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
        "-d", "--dry-run", 
        action="store_true",
        help="模拟运行，不执行实际操作"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志级别
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    # 覆盖配置
    if args.template_dir:
        CONFIG['template_dir'] = args.template_dir
    if args.adb_path:
        CONFIG['adb_path'] = args.adb_path
    
    # 创建机器人实例
    bot = StarRailMoneyWarBot()
    
    # 运行机器人
    bot.start(cycles=args.cycles)


if __name__ == "__main__":
    main()
