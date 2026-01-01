#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化流程执行模块
实现货币战争玩法的完整自动化逻辑
"""

import time
import cv2
import numpy as np
from typing import Optional, Tuple
from scene_recognition import SceneType

class AutoFlow:
    """自动化流程类"""
    
    def __init__(self, adb, scene_recognizer, ocr, image_processor, logger=None, config=None):
        """初始化自动化流程
        
        Args:
            adb: ADB控制器对象
            scene_recognizer: 场景识别对象
            ocr: OCR识别器对象
            image_processor: 图像处理对象
            logger: 日志对象
            config: 配置对象
        """
        self.adb = adb
        self.scene_recognizer = scene_recognizer
        self.ocr = ocr
        self.image_processor = image_processor
        self.logger = logger
        self.config = config
        
        # 当前状态
        self.current_scene = SceneType.UNKNOWN
        self.current_score = 0
        self.total_battles = 0
        self.win_count = 0
        
        # 操作计数，用于控制操作频率
        self.operation_count = 0
        self.last_operation_time = time.time()
        
    def execute_round(self) -> bool:
        """执行一轮完整的货币战争流程
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            self.logger.info("开始执行一轮货币战争流程")
            
            # 1. 获取当前屏幕截图
            screenshot_path = self.adb.screenshot()
            if not screenshot_path:
                self.logger.error("无法获取屏幕截图")
                return False
            
            # 加载图像
            image = cv2.imread(screenshot_path)
            if image is None:
                self.logger.error("无法加载截图")
                return False
            
            # 2. 识别当前场景
            scene_type, scene_info = self.scene_recognizer.recognize_scene(image)
            self.current_scene = scene_type
            
            # 更新积分信息
            if 'score' in scene_info:
                self.current_score = scene_info['score']
                self.logger.info(f"当前积分: {self.current_score}")
            
            self.logger.info(f"当前场景: {scene_type.name}")
            
            # 3. 根据场景执行相应操作
            success = self._handle_scene(scene_type, image, scene_info)
            
            if success:
                self.logger.info("本轮流程执行成功")
            else:
                self.logger.error("本轮流程执行失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行流程失败: {str(e)}", exc_info=True)
            return False
    
    def _handle_scene(self, scene_type: SceneType, image: np.ndarray, scene_info: dict) -> bool:
        """处理不同场景
        
        Args:
            scene_type: 当前场景类型
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        handlers = {
            SceneType.MAIN_MENU: self._handle_main_menu,
            SceneType.MONEY_WAR_MENU: self._handle_money_war_menu,
            SceneType.BATTLE_PREPARE: self._handle_battle_prepare,
            SceneType.BATTLE_IN_PROGRESS: self._handle_battle_in_progress,
            SceneType.BATTLE_RESULT: self._handle_battle_result,
            SceneType.REWARD_COLLECTION: self._handle_reward_collection,
            SceneType.SCORE_DISPLAY: self._handle_score_display,
            SceneType.UNKNOWN: self._handle_unknown_scene
        }
        
        handler = handlers.get(scene_type, self._handle_unknown_scene)
        return handler(image, scene_info)
    
    def _handle_main_menu(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理主菜单场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.info("处理主菜单场景")
        
        # 查找货币战争入口
        war_button = self.scene_recognizer.detect_button(image, "货币战争")
        if war_button:
            x, y = war_button
            self.logger.info(f"点击货币战争入口: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(self.config.long_operation_delay)
            return True
        
        self.logger.error("未找到货币战争入口")
        return False
    
    def _handle_money_war_menu(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理货币战争菜单场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.info("处理货币战争菜单场景")
        
        # 查找开始挑战按钮
        start_button = self.scene_recognizer.detect_button(image, "开始挑战")
        if not start_button:
            # 使用预设位置
            interaction_points = self.scene_recognizer.find_interaction_points(SceneType.MONEY_WAR_MENU, image)
            start_button = interaction_points.get('start_challenge')
        
        if start_button:
            x, y = start_button
            self.logger.info(f"点击开始挑战: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(self.config.long_operation_delay)
            return True
        
        self.logger.error("未找到开始挑战按钮")
        return False
    
    def _handle_battle_prepare(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理战斗准备场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.info("处理战斗准备场景")
        
        # 查找开始战斗按钮
        start_button = self.scene_recognizer.detect_button(image, "开始")
        if not start_button:
            # 使用预设位置
            interaction_points = self.scene_recognizer.find_interaction_points(SceneType.BATTLE_PREPARE, image)
            start_button = interaction_points.get('start_battle')
        
        if start_button:
            x, y = start_button
            self.logger.info(f"点击开始战斗: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(self.config.long_operation_delay)
            self.total_battles += 1
            return True
        
        self.logger.error("未找到开始战斗按钮")
        return False
    
    def _handle_battle_in_progress(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理战斗进行中场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.info("处理战斗进行中场景")
        
        # 战斗中的自动操作逻辑
        # 这里实现简单的自动战斗逻辑，根据实际情况可以扩展
        
        # 获取交互点
        interaction_points = self.scene_recognizer.find_interaction_points(SceneType.BATTLE_IN_PROGRESS, image)
        
        # 1. 点击技能1
        if 'skill_1' in interaction_points:
            x, y = interaction_points['skill_1']
            self.logger.info(f"使用技能1: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(1.0)
        
        # 2. 点击技能2
        if 'skill_2' in interaction_points:
            x, y = interaction_points['skill_2']
            self.logger.info(f"使用技能2: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(1.0)
        
        # 3. 等待战斗结束
        self.logger.info("等待战斗结束...")
        battle_complete = self._wait_for_battle_complete()
        
        return battle_complete
    
    def _handle_battle_result(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理战斗结果场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.info("处理战斗结果场景")
        
        # 更新战斗统计
        if 'result' in scene_info:
            result = scene_info['result']
            self.logger.info(f"战斗结果: {result}")
            if result == '胜利':
                self.win_count += 1
        
        # 查找确定按钮
        confirm_button = self.scene_recognizer.detect_button(image, "确定")
        if not confirm_button:
            # 使用预设位置
            interaction_points = self.scene_recognizer.find_interaction_points(SceneType.BATTLE_RESULT, image)
            confirm_button = interaction_points.get('confirm')
        
        if confirm_button:
            x, y = confirm_button
            self.logger.info(f"点击确定: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(self.config.long_operation_delay)
            return True
        
        self.logger.error("未找到确定按钮")
        return False
    
    def _handle_reward_collection(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理奖励领取场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.info("处理奖励领取场景")
        
        # 显示奖励信息
        if 'reward' in scene_info and scene_info['reward']:
            reward_str = ", ".join([f"{k}: {v}" for k, v in scene_info['reward'].items()])
            self.logger.info(f"获得奖励: {reward_str}")
        
        # 查找领取奖励按钮
        collect_button = self.scene_recognizer.detect_button(image, "领取奖励")
        if not collect_button:
            # 使用预设位置
            interaction_points = self.scene_recognizer.find_interaction_points(SceneType.REWARD_COLLECTION, image)
            collect_button = interaction_points.get('collect_reward')
        
        if collect_button:
            x, y = collect_button
            self.logger.info(f"点击领取奖励: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(self.config.long_operation_delay)
            return True
        
        self.logger.error("未找到领取奖励按钮")
        return False
    
    def _handle_score_display(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理积分显示场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.info("处理积分显示场景")
        
        # 查找返回按钮
        back_button = self.scene_recognizer.detect_button(image, "返回")
        if back_button:
            x, y = back_button
            self.logger.info(f"点击返回: ({x}, {y})")
            self.adb.tap(x, y, delay=self.config.operation_delay)
            time.sleep(self.config.operation_delay)
            return True
        
        # 如果没有返回按钮，尝试点击屏幕中心
        height, width = image.shape[:2]
        center_x, center_y = width // 2, height // 2
        self.logger.info(f"点击屏幕中心返回: ({center_x}, {center_y})")
        self.adb.tap(center_x, center_y, delay=self.config.operation_delay)
        time.sleep(self.config.operation_delay)
        
        return True
    
    def _handle_unknown_scene(self, image: np.ndarray, scene_info: dict) -> bool:
        """处理未知场景
        
        Args:
            image: 当前屏幕图像
            scene_info: 场景信息
            
        Returns:
            处理成功返回True，失败返回False
        """
        self.logger.warning("处理未知场景")
        
        # 尝试返回主菜单
        self.logger.info("尝试返回主菜单...")
        
        # 点击屏幕底部中心位置
        height, width = image.shape[:2]
        center_x, center_y = width // 2, height * 3 // 4
        
        self.adb.tap(center_x, center_y, delay=self.config.operation_delay)
        time.sleep(self.config.long_operation_delay)
        
        # 再次尝试识别场景
        new_scene, new_info = self.scene_recognizer.recognize_scene(image)
        if new_scene != SceneType.UNKNOWN:
            self.logger.info(f"成功切换到已知场景: {new_scene.name}")
            return True
        
        self.logger.error("无法处理未知场景")
        return False
    
    def _wait_for_battle_complete(self, timeout: int = 60) -> bool:
        """等待战斗结束
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            战斗结束返回True，超时返回False
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 获取当前屏幕
            screenshot_path = self.adb.screenshot()
            if screenshot_path:
                image = cv2.imread(screenshot_path)
                if image:
                    # 识别场景
                    scene_type, scene_info = self.scene_recognizer.recognize_scene(image)
                    
                    # 检查战斗是否结束
                    if self.scene_recognizer.is_battle_complete(scene_type):
                        self.logger.info(f"战斗结束，当前场景: {scene_type.name}")
                        self.current_scene = scene_type
                        return True
            
            # 等待一段时间后再次检查
            time.sleep(2.0)
        
        self.logger.error("等待战斗结束超时")
        return False
    
    def get_current_score(self) -> int:
        """获取当前积分
        
        Returns:
            当前积分
        """
        return self.current_score
    
    def get_battle_stats(self) -> dict:
        """获取战斗统计信息
        
        Returns:
            战斗统计字典
        """
        return {
            'total_battles': self.total_battles,
            'win_count': self.win_count,
            'win_rate': self.win_count / self.total_battles if self.total_battles > 0 else 0,
            'current_score': self.current_score
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.total_battles = 0
        self.win_count = 0
        self.current_score = 0
    
    def _get_random_delay(self, base_delay: float, variation: float = 0.3) -> float:
        """获取随机延迟时间，增加操作随机性
        
        Args:
            base_delay: 基础延迟时间
            variation: 随机变化范围（0-1）
            
        Returns:
            随机延迟时间
        """
        import random
        
        # 计算延迟变化范围
        delay_variation = base_delay * variation
        
        # 生成随机延迟
        random_delay = base_delay + random.uniform(-delay_variation, delay_variation)
        
        # 确保延迟不小于最小值
        min_delay = 0.1
        return max(min_delay, random_delay)
    
    def _safe_operation_delay(self, delay_type: str = 'normal'):
        """安全的操作延迟，避免被检测为异常操作
        
        Args:
            delay_type: 延迟类型 ('normal', 'long')
        """
        # 根据操作类型获取基础延迟
        if delay_type == 'long':
            base_delay = self.config.long_operation_delay
        else:
            base_delay = self.config.operation_delay
        
        # 增加随机性
        random_delay = self._get_random_delay(base_delay)
        
        # 更新操作计数和时间
        self.operation_count += 1
        self.last_operation_time = time.time()
        
        # 每10次操作增加一次长延迟
        if self.operation_count % 10 == 0:
            random_delay += self._get_random_delay(1.0)
            self.logger.debug(f"第 {self.operation_count} 次操作，增加额外延迟")
        
        self.logger.debug(f"操作延迟: {random_delay:.3f}秒")
        time.sleep(random_delay)
    
    def _tap_safe(self, x: int, y: int, delay_type: str = 'normal') -> bool:
        """安全点击，添加随机延迟
        
        Args:
            x: X坐标
            y: Y坐标
            delay_type: 延迟类型
            
        Returns:
            点击成功返回True，失败返回False
        """
        # 执行点击
        success = self.adb.tap(x, y, delay=0)  # 不使用默认延迟，自己控制
        
        # 添加安全延迟
        self._safe_operation_delay(delay_type)
        
        return success
    
    def _swipe_safe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500, delay_type: str = 'normal') -> bool:
        """安全滑动，添加随机延迟
        
        Args:
            x1: 起始X坐标
            y1: 起始Y坐标
            x2: 结束X坐标
            y2: 结束Y坐标
            duration: 滑动持续时间
            delay_type: 延迟类型
            
        Returns:
            滑动成功返回True，失败返回False
        """
        # 执行滑动
        success = self.adb.swipe(x1, y1, x2, y2, duration, delay=0)  # 不使用默认延迟，自己控制
        
        # 添加安全延迟
        self._safe_operation_delay(delay_type)
        
        return success
