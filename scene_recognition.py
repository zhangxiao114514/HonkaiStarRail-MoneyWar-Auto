#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景识别模块
负责识别游戏界面状态和交互点
"""

import os
import cv2
import numpy as np
from enum import Enum, auto
from typing import Optional, Tuple, Dict

class SceneType(Enum):
    """游戏场景类型"""
    UNKNOWN = auto()
    MAIN_MENU = auto()
    MONEY_WAR_MENU = auto()
    BATTLE_PREPARE = auto()
    BATTLE_IN_PROGRESS = auto()
    BATTLE_RESULT = auto()
    REWARD_COLLECTION = auto()
    SCORE_DISPLAY = auto()

class SceneRecognizer:
    """场景识别类"""
    
    def __init__(self, ocr, image_processor, logger=None, config=None):
        """初始化场景识别模块
        
        Args:
            ocr: OCR识别器对象
            image_processor: 图像处理对象
            logger: 日志对象
            config: 配置对象
        """
        self.ocr = ocr
        self.image_processor = image_processor
        self.logger = logger
        self.config = config
        
        # 场景模板库
        self.templates = {}
        self._load_templates()
        
    def _load_templates(self):
        """加载场景识别模板"""
        # 这里可以加载预定义的场景模板
        # 目前使用文本识别为主，模板匹配为辅
        self.templates = {
            SceneType.MAIN_MENU: ["星穹铁道", "开始游戏", "设置"],
            SceneType.MONEY_WAR_MENU: ["货币战争", "开始挑战", "积分"],
            SceneType.BATTLE_PREPARE: ["准备战斗", "开始", "编队"],
            SceneType.BATTLE_IN_PROGRESS: ["战斗", "技能", "撤退"],
            SceneType.BATTLE_RESULT: ["战斗结束", "胜利", "失败", "获得"],
            SceneType.REWARD_COLLECTION: ["领取奖励", "确定", "奖励"],
            SceneType.SCORE_DISPLAY: ["积分", "排名", "段位"]
        }
    
    def recognize_scene(self, image: np.ndarray) -> Tuple[SceneType, Dict]:
        """识别当前游戏场景
        
        Args:
            image: 当前屏幕图像
            
        Returns:
            (场景类型, 场景信息)
        """
        try:
            scene_info = {}
            
            # 1. 使用OCR识别文本
            ocr_results = self.ocr.recognize(image)
            
            # 提取所有识别到的文本
            recognized_texts = [result['text'] for result in ocr_results]
            full_text = ' '.join(recognized_texts)
            
            self.logger.debug(f"识别到的文本: {full_text}")
            
            # 2. 匹配场景模板
            for scene_type, keywords in self.templates.items():
                match_count = 0
                total_keywords = len(keywords)
                
                for keyword in keywords:
                    if keyword in full_text:
                        match_count += 1
                
                # 计算匹配度
                match_ratio = match_count / total_keywords
                
                if match_ratio >= self.config.scene_recognition_threshold:
                    self.logger.info(f"识别到场景: {scene_type.name}，匹配度: {match_ratio:.2f}")
                    
                    # 提取场景特定信息
                    scene_info = self._extract_scene_info(scene_type, image, ocr_results)
                    return (scene_type, scene_info)
            
            # 3. 如果没有匹配到，尝试特殊场景检测
            special_scene = self._detect_special_scenes(image, ocr_results)
            if special_scene != SceneType.UNKNOWN:
                self.logger.info(f"识别到特殊场景: {special_scene.name}")
                scene_info = self._extract_scene_info(special_scene, image, ocr_results)
                return (special_scene, scene_info)
            
            self.logger.warning(f"无法识别场景，识别到的文本: {full_text}")
            return (SceneType.UNKNOWN, scene_info)
        except Exception as e:
            self.logger.error(f"场景识别失败: {str(e)}", exc_info=True)
            return (SceneType.UNKNOWN, {})
    
    def _detect_special_scenes(self, image: np.ndarray, ocr_results: list) -> SceneType:
        """检测特殊场景
        
        Args:
            image: 当前屏幕图像
            ocr_results: OCR识别结果
            
        Returns:
            场景类型
        """
        # 检测战斗场景（通过UI元素）
        height, width = image.shape[:2]
        
        # 检查是否有战斗相关UI元素
        battle_ui_regions = [
            (width * 7 // 8, height // 8, width // 8, height // 4),  # 右上角技能区域
            (width // 8, height * 3 // 4, width * 3 // 4, height // 4)  # 底部操作区域
        ]
        
        for region in battle_ui_regions:
            x, y, w, h = region
            region_image = self.image_processor.crop(image, x, y, w, h)
            
            # 检查区域内的像素特征
            avg_color = self.image_processor.get_average_color(region_image)
            
            # 如果是深色背景，可能是战斗界面
            if sum(avg_color) < 300:  # 深色背景判断
                return SceneType.BATTLE_IN_PROGRESS
        
        return SceneType.UNKNOWN
    
    def _extract_scene_info(self, scene_type: SceneType, image: np.ndarray, ocr_results: list) -> Dict:
        """提取场景特定信息
        
        Args:
            scene_type: 场景类型
            image: 当前屏幕图像
            ocr_results: OCR识别结果
            
        Returns:
            场景信息字典
        """
        scene_info = {}
        
        # 提取积分信息
        if scene_type in [SceneType.MONEY_WAR_MENU, SceneType.SCORE_DISPLAY, SceneType.BATTLE_RESULT]:
            score = self._extract_score(image, ocr_results)
            if score is not None:
                scene_info['score'] = score
        
        # 提取战斗结果信息
        if scene_type == SceneType.BATTLE_RESULT:
            result = self._extract_battle_result(ocr_results)
            scene_info['result'] = result
        
        # 提取奖励信息
        if scene_type == SceneType.REWARD_COLLECTION:
            reward = self._extract_reward(ocr_results)
            scene_info['reward'] = reward
        
        return scene_info
    
    def _extract_score(self, image: np.ndarray, ocr_results: list) -> Optional[int]:
        """提取积分信息
        
        Args:
            image: 当前屏幕图像
            ocr_results: OCR识别结果
            
        Returns:
            积分值，失败返回None
        """
        # 1. 首先尝试从OCR结果中提取数字
        for result in ocr_results:
            text = result['text']
            
            # 检查文本中是否包含积分相关关键词
            if any(keyword in text for keyword in ['积分', '分数', 'point', 'score']):
                # 提取数字
                import re
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
        
        # 2. 尝试在指定区域识别积分
        score_region = self.config.score_recognition_area
        if score_region:
            score_image = self.image_processor.get_text_region(image, score_region)
            score = self.ocr.recognize_number(score_image)
            if score is not None:
                return score
        
        # 3. 尝试从所有OCR结果中寻找最大的数字作为积分
        all_numbers = []
        for result in ocr_results:
            text = result['text']
            import re
            numbers = re.findall(r'\d+', text)
            all_numbers.extend([int(num) for num in numbers])
        
        if all_numbers:
            # 积分通常是较大的数字
            return max(all_numbers)
        
        return None
    
    def _extract_battle_result(self, ocr_results: list) -> str:
        """提取战斗结果
        
        Args:
            ocr_results: OCR识别结果
            
        Returns:
            战斗结果：胜利、失败或未知
        """
        for result in ocr_results:
            text = result['text']
            if '胜利' in text or 'win' in text.lower():
                return '胜利'
            elif '失败' in text or 'lose' in text.lower():
                return '失败'
        
        return '未知'
    
    def _extract_reward(self, ocr_results: list) -> Dict:
        """提取奖励信息
        
        Args:
            ocr_results: OCR识别结果
            
        Returns:
            奖励信息字典
        """
        reward = {}
        
        for result in ocr_results:
            text = result['text']
            
            # 提取物品和数量
            import re
            item_patterns = [
                r'(\w+)\s*(\d+)',  # 物品名 数量
                r'获得\s*(\w+)\s*(\d+)',  # 获得 物品名 数量
            ]
            
            for pattern in item_patterns:
                match = re.search(pattern, text)
                if match:
                    item_name = match.group(1)
                    item_count = int(match.group(2))
                    reward[item_name] = item_count
        
        return reward
    
    def find_interaction_points(self, scene_type: SceneType, image: np.ndarray) -> Dict[str, Tuple[int, int]]:
        """查找场景中的交互点
        
        Args:
            scene_type: 当前场景类型
            image: 当前屏幕图像
            
        Returns:
            交互点字典，键为交互点名称，值为坐标(x, y)
        """
        interaction_points = {}
        height, width = image.shape[:2]
        
        # 根据场景类型定义交互点
        if scene_type == SceneType.MONEY_WAR_MENU:
            # 开始挑战按钮
            interaction_points['start_challenge'] = (width // 2, height * 3 // 4)
            
        elif scene_type == SceneType.BATTLE_PREPARE:
            # 开始战斗按钮
            interaction_points['start_battle'] = (width // 2, height * 3 // 4)
            
        elif scene_type == SceneType.BATTLE_IN_PROGRESS:
            # 技能按钮位置（示例）
            interaction_points['skill_1'] = (width // 4, height * 7 // 8)
            interaction_points['skill_2'] = (width // 2, height * 7 // 8)
            interaction_points['skill_3'] = (width * 3 // 4, height * 7 // 8)
            
        elif scene_type == SceneType.BATTLE_RESULT:
            # 确定按钮
            interaction_points['confirm'] = (width // 2, height * 3 // 4)
            
        elif scene_type == SceneType.REWARD_COLLECTION:
            # 领取奖励按钮
            interaction_points['collect_reward'] = (width // 2, height * 3 // 4)
            
        return interaction_points
    
    def detect_button(self, image: np.ndarray, button_text: str) -> Optional[Tuple[int, int]]:
        """检测特定按钮位置
        
        Args:
            image: 当前屏幕图像
            button_text: 按钮文本
            
        Returns:
            按钮坐标(x, y)，失败返回None
        """
        try:
            # 使用OCR识别文本
            ocr_results = self.ocr.recognize(image)
            
            for result in ocr_results:
                if button_text in result['text']:
                    # 这里简化处理，返回文本位置的中心
                    # 实际应用中需要更精确的定位
                    height, width = image.shape[:2]
                    return (width // 2, height // 2)
            
            return None
        except Exception as e:
            self.logger.error(f"按钮检测失败: {str(e)}")
            return None
    
    def is_in_battle(self, scene_type: SceneType) -> bool:
        """判断是否处于战斗中
        
        Args:
            scene_type: 当前场景类型
            
        Returns:
            是战斗场景返回True，否则返回False
        """
        return scene_type in [SceneType.BATTLE_IN_PROGRESS, SceneType.BATTLE_PREPARE]
    
    def is_battle_complete(self, scene_type: SceneType) -> bool:
        """判断战斗是否结束
        
        Args:
            scene_type: 当前场景类型
            
        Returns:
            战斗结束返回True，否则返回False
        """
        return scene_type in [SceneType.BATTLE_RESULT, SceneType.REWARD_COLLECTION]
