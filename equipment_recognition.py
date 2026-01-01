#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装备识别与自动穿戴模块
"""

import re
import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple

class EquipmentRecognizer:
    """装备识别类"""
    
    def __init__(self, ocr, image_processor, logger=None, config=None):
        """初始化装备识别器
        
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
        
        # 装备属性权重
        self.attribute_weights = {
            "暴击": 1.5,
            "暴伤": 1.2,
            "攻击": 1.0,
            "速度": 1.3,
            "防御": 0.5,
            "生命值": 0.4,
            "能量恢复": 1.1,
            "效果命中": 0.8,
            "效果抵抗": 0.7
        }
    
    def recognize_equipment(self, image: np.ndarray, region: Tuple[int, int, int, int] = None) -> Optional[Dict]:
        """识别装备信息
        
        Args:
            image: 包含装备的图像
            region: 装备区域坐标 (x, y, w, h)
            
        Returns:
            装备信息字典，失败返回None
        """
        try:
            # 裁剪装备区域
            if region:
                equipment_image = self.image_processor.crop(image, *region)
            else:
                equipment_image = image
            
            # 图像预处理
            processed_image = self.image_processor.preprocess(equipment_image)
            
            # 使用OCR识别装备文本
            ocr_results = self.ocr.recognize(processed_image)
            
            # 提取装备信息
            equipment_info = self._extract_equipment_info(ocr_results)
            
            if equipment_info:
                # 计算装备评分
                equipment_info['score'] = self._calculate_equipment_score(equipment_info)
                return equipment_info
            
            return None
        except Exception as e:
            self.logger.error(f"装备识别失败: {str(e)}", exc_info=True)
            return None
    
    def _extract_equipment_info(self, ocr_results: List[Dict]) -> Dict:
        """从OCR结果中提取装备信息
        
        Args:
            ocr_results: OCR识别结果
            
        Returns:
            装备信息字典
        """
        equipment_info = {
            'name': '',
            'level': 0,
            'rarity': 0,
            'attributes': {},
            'main_attribute': '',
            'sub_attributes': []
        }
        
        # 合并所有OCR文本
        full_text = ' '.join([result['text'] for result in ocr_results])
        
        self.logger.debug(f"装备OCR文本: {full_text}")
        
        # 提取装备等级
        level_match = re.search(r'等级(\d+)', full_text)
        if level_match:
            equipment_info['level'] = int(level_match.group(1))
        
        # 提取装备稀有度（星级）
        star_match = re.search(r'(\d+)星', full_text)
        if star_match:
            equipment_info['rarity'] = int(star_match.group(1))
        else:
            # 通过文本长度和关键词推断稀有度
            if len(full_text) > 50:
                equipment_info['rarity'] = 5
            elif len(full_text) > 30:
                equipment_info['rarity'] = 4
            else:
                equipment_info['rarity'] = 3
        
        # 提取装备属性
        attributes = self._extract_attributes(full_text)
        equipment_info['attributes'] = attributes
        
        # 确定主属性和副属性
        if attributes:
            # 主属性通常是第一个出现的属性
            main_attr = list(attributes.keys())[0]
            equipment_info['main_attribute'] = main_attr
            
            # 其余为副属性
            equipment_info['sub_attributes'] = list(attributes.keys())[1:]
        
        return equipment_info
    
    def _extract_attributes(self, text: str) -> Dict[str, float]:
        """从文本中提取装备属性
        
        Args:
            text: 包含装备属性的文本
            
        Returns:
            属性字典，键为属性名，值为属性值
        """
        attributes = {}
        
        # 属性提取规则
        attribute_patterns = [
            (r'暴击\s*(\d+(?:\.\d+)?)%?', '暴击'),
            (r'暴伤\s*(\d+(?:\.\d+)?)%?', '暴伤'),
            (r'攻击\s*(\d+(?:\.\d+)?)', '攻击'),
            (r'速度\s*(\d+(?:\.\d+)?)', '速度'),
            (r'防御\s*(\d+(?:\.\d+)?)', '防御'),
            (r'生命\s*(\d+(?:\.\d+)?)', '生命值'),
            (r'能量恢复\s*(\d+(?:\.\d+)?)%?', '能量恢复'),
            (r'效果命中\s*(\d+(?:\.\d+)?)%?', '效果命中'),
            (r'效果抵抗\s*(\d+(?:\.\d+)?)%?', '效果抵抗')
        ]
        
        for pattern, attr_name in attribute_patterns:
            matches = re.findall(pattern, text)
            if matches:
                value = float(matches[0])
                attributes[attr_name] = value
        
        return attributes
    
    def _calculate_equipment_score(self, equipment_info: Dict) -> float:
        """计算装备评分
        
        Args:
            equipment_info: 装备信息字典
            
        Returns:
            装备评分
        """
        score = 0.0
        
        # 稀有度基础分
        rarity_score = equipment_info['rarity'] * 10
        
        # 等级分
        level_score = (equipment_info['level'] / self.config.max_equipment_level) * 20
        
        # 属性分
        attribute_score = 0.0
        for attr_name, value in equipment_info['attributes'].items():
            weight = self.attribute_weights.get(attr_name, 0.5)
            
            # 根据属性类型调整评分
            if attr_name in ['暴击', '暴伤', '效果命中', '效果抵抗', '能量恢复']:
                # 百分比属性
                attribute_score += value * weight * 0.1
            else:
                # 固定值属性
                attribute_score += value * weight * 0.05
        
        # 最优属性加成
        optimal_bonus = 0.0
        for attr in equipment_info['sub_attributes']:
            if attr in self.config.optimal_equipment_attributes:
                optimal_bonus += 5.0
        
        # 总评分
        total_score = rarity_score + level_score + attribute_score + optimal_bonus
        
        return round(total_score, 2)
    
    def is_equipment_better(self, new_equip: Dict, current_equip: Dict) -> bool:
        """比较两件装备哪个更好
        
        Args:
            new_equip: 新装备信息
            current_equip: 当前装备信息
            
        Returns:
            新装备更好返回True，否则返回False
        """
        # 如果新装备评分高10分以上，则认为更好
        if new_equip['score'] - current_equip['score'] >= 10.0:
            return True
        
        # 检查是否有最优属性优势
        new_optimal_count = sum(1 for attr in new_equip['sub_attributes'] if attr in self.config.optimal_equipment_attributes)
        current_optimal_count = sum(1 for attr in current_equip['sub_attributes'] if attr in self.config.optimal_equipment_attributes)
        
        if new_optimal_count > current_optimal_count:
            return True
        
        return False
    
    def find_best_equipment(self, equipment_list: List[Dict]) -> Optional[Dict]:
        """从装备列表中找到最好的装备
        
        Args:
            equipment_list: 装备列表
            
        Returns:
            最好的装备信息，失败返回None
        """
        if not equipment_list:
            return None
        
        # 按评分排序
        sorted_equipment = sorted(equipment_list, key=lambda x: x['score'], reverse=True)
        return sorted_equipment[0]
    
    def recognize_equipment_list(self, image: np.ndarray, equipment_regions: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """识别多个装备
        
        Args:
            image: 包含多个装备的图像
            equipment_regions: 多个装备区域坐标列表
            
        Returns:
            装备信息列表
        """
        equipment_list = []
        
        for i, region in enumerate(equipment_regions):
            self.logger.debug(f"识别第 {i + 1} 个装备")
            equipment = self.recognize_equipment(image, region)
            if equipment:
                equipment_list.append(equipment)
        
        return equipment_list
    
    def get_equip_action_coordinates(self, screen_size: Tuple[int, int], action_type: str) -> Tuple[int, int]:
        """获取装备操作坐标
        
        Args:
            screen_size: 屏幕尺寸 (width, height)
            action_type: 操作类型 ('wear', 'take_off', 'compare', 'confirm')
            
        Returns:
            操作坐标 (x, y)
        """
        width, height = screen_size
        
        # 预定义的装备操作坐标
        action_coords = {
            'wear': (width * 3 // 4, height * 4 // 5),  # 穿戴按钮
            'take_off': (width * 3 // 4, height * 4 // 5),  # 卸下按钮
            'compare': (width * 2 // 3, height * 3 // 5),  # 对比按钮
            'confirm': (width * 3 // 4, height * 9 // 10)  # 确认按钮
        }
        
        return action_coords.get(action_type, (width // 2, height // 2))
