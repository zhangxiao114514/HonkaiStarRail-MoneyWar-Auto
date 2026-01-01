#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色费用识别与自动交易模块
"""

import re
import time
import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple

class TransactionSystem:
    """交易系统类"""
    
    def __init__(self, adb, ocr, image_processor, logger=None, config=None):
        """初始化交易系统
        
        Args:
            adb: ADB控制器对象
            ocr: OCR识别器对象
            image_processor: 图像处理对象
            logger: 日志对象
            config: 配置对象
        """
        self.adb = adb
        self.ocr = ocr
        self.image_processor = image_processor
        self.logger = logger
        self.config = config
        
        # 交易状态
        self.current_credits = 0
        self.last_transaction_time = 0
        
        # 交易操作坐标
        self.transaction_coords = {
            'buy_button': (800, 1500),
            'sell_button': (800, 1600),
            'confirm_button': (600, 1700),
            'cancel_button': (400, 1700),
            'credits_display': (200, 100, 400, 50)
        }
    
    def recognize_credits(self, image: np.ndarray, region: Tuple[int, int, int, int] = None) -> Optional[int]:
        """识别当前角色费用（星穹）
        
        Args:
            image: 包含费用信息的图像
            region: 费用显示区域 (x, y, w, h)
            
        Returns:
            角色费用值，失败返回None
        """
        try:
            # 裁剪费用区域
            if region:
                credits_image = self.image_processor.crop(image, *region)
            else:
                # 使用默认区域
                credits_region = self.transaction_coords['credits_display']
                credits_image = self.image_processor.crop(image, *credits_region)
            
            # 图像预处理
            processed_image = self.image_processor.preprocess(credits_image)
            
            # 使用OCR识别
            ocr_results = self.ocr.recognize(processed_image)
            
            if ocr_results:
                # 合并识别文本
                full_text = ' '.join([result['text'] for result in ocr_results])
                
                # 提取数字
                credits = self._extract_number(full_text)
                if credits is not None:
                    self.current_credits = credits
                    return credits
            
            return None
        except Exception as e:
            self.logger.error(f"识别费用失败: {str(e)}", exc_info=True)
            return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """从文本中提取数字
        
        Args:
            text: 包含数字的文本
            
        Returns:
            提取的数字，失败返回None
        """
        # 提取所有数字
        numbers = re.findall(r'\d+', text)
        
        if numbers:
            # 返回最大的数字（通常是费用）
            return int(max(numbers, key=len))
        
        return None
    
    def recognize_transaction_info(self, image: np.ndarray, region: Tuple[int, int, int, int] = None) -> Optional[Dict]:
        """识别交易界面信息
        
        Args:
            image: 交易界面图像
            region: 交易区域 (x, y, w, h)
            
        Returns:
            交易信息字典，失败返回None
        """
        try:
            # 裁剪交易区域
            if region:
                transaction_image = self.image_processor.crop(image, *region)
            else:
                # 使用配置中的交易区域
                transaction_image = self.image_processor.crop(image, *self.config.transaction_area)
            
            # 图像预处理
            processed_image = self.image_processor.preprocess(transaction_image)
            
            # 使用OCR识别
            ocr_results = self.ocr.recognize(processed_image)
            
            if not ocr_results:
                return None
            
            # 合并识别文本
            full_text = ' '.join([result['text'] for result in ocr_results])
            
            # 提取交易信息
            transaction_info = {
                'item_name': '',
                'price': 0,
                'quantity': 1,
                'available': True
            }
            
            # 提取物品名称（假设物品名称在文本开头）
            transaction_info['item_name'] = full_text.split(' ')[0]
            
            # 提取价格
            price = self._extract_number(full_text)
            if price:
                transaction_info['price'] = price
            
            # 检查是否可购买/出售
            if '售罄' in full_text or '不可用' in full_text:
                transaction_info['available'] = False
            
            return transaction_info
        except Exception as e:
            self.logger.error(f"识别交易信息失败: {str(e)}", exc_info=True)
            return None
    
    def should_buy_item(self, item_info: Dict) -> bool:
        """判断是否应该购买物品
        
        Args:
            item_info: 物品信息字典
            
        Returns:
            应该购买返回True，否则返回False
        """
        # 检查物品是否可用
        if not item_info['available']:
            return False
        
        # 检查价格是否在可接受范围内
        if item_info['price'] > self.config.max_buy_price:
            self.logger.debug(f"物品价格 {item_info['price']} 超过最大购买价格 {self.config.max_buy_price}")
            return False
        
        # 检查当前费用是否足够
        if self.current_credits < item_info['price']:
            self.logger.debug(f"当前费用 {self.current_credits} 不足以购买价格 {item_info['price']} 的物品")
            return False
        
        # 检查交易间隔
        if time.time() - self.last_transaction_time < self.config.transaction_delay:
            return False
        
        return True
    
    def should_sell_item(self, item_info: Dict) -> bool:
        """判断是否应该出售物品
        
        Args:
            item_info: 物品信息字典
            
        Returns:
            应该出售返回True，否则返回False
        """
        # 检查物品是否可出售
        if not item_info['available']:
            return False
        
        # 检查价格是否高于最低出售价格
        if item_info['price'] < self.config.min_sell_price:
            self.logger.debug(f"物品价格 {item_info['price']} 低于最低出售价格 {self.config.min_sell_price}")
            return False
        
        # 检查交易间隔
        if time.time() - self.last_transaction_time < self.config.transaction_delay:
            return False
        
        return True
    
    def execute_buy(self, item_info: Dict) -> bool:
        """执行购买操作
        
        Args:
            item_info: 物品信息字典
            
        Returns:
            购买成功返回True，失败返回False
        """
        try:
            self.logger.info(f"执行购买操作: {item_info['item_name']}，价格: {item_info['price']}")
            
            # 点击购买按钮
            buy_x, buy_y = self.transaction_coords['buy_button']
            if not self.adb.tap(buy_x, buy_y, delay=self.config.operation_delay):
                return False
            
            # 等待确认界面
            time.sleep(self.config.operation_delay * 2)
            
            # 点击确认按钮
            confirm_x, confirm_y = self.transaction_coords['confirm_button']
            if not self.adb.tap(confirm_x, confirm_y, delay=self.config.operation_delay):
                return False
            
            # 更新交易时间
            self.last_transaction_time = time.time()
            
            # 更新当前费用
            self.current_credits -= item_info['price']
            
            self.logger.info(f"购买成功: {item_info['item_name']}")
            return True
        except Exception as e:
            self.logger.error(f"购买操作失败: {str(e)}", exc_info=True)
            return False
    
    def execute_sell(self, item_info: Dict) -> bool:
        """执行出售操作
        
        Args:
            item_info: 物品信息字典
            
        Returns:
            出售成功返回True，失败返回False
        """
        try:
            self.logger.info(f"执行出售操作: {item_info['item_name']}，价格: {item_info['price']}")
            
            # 点击出售按钮
            sell_x, sell_y = self.transaction_coords['sell_button']
            if not self.adb.tap(sell_x, sell_y, delay=self.config.operation_delay):
                return False
            
            # 等待确认界面
            time.sleep(self.config.operation_delay * 2)
            
            # 点击确认按钮
            confirm_x, confirm_y = self.transaction_coords['confirm_button']
            if not self.adb.tap(confirm_x, confirm_y, delay=self.config.operation_delay):
                return False
            
            # 更新交易时间
            self.last_transaction_time = time.time()
            
            # 更新当前费用
            self.current_credits += item_info['price']
            
            self.logger.info(f"出售成功: {item_info['item_name']}")
            return True
        except Exception as e:
            self.logger.error(f"出售操作失败: {str(e)}", exc_info=True)
            return False
    
    def check_transaction_opportunities(self, image: np.ndarray) -> bool:
        """检查并执行交易机会
        
        Args:
            image: 当前屏幕图像
            
        Returns:
            执行了交易返回True，否则返回False
        """
        try:
            # 识别当前费用
            current_credits = self.recognize_credits(image)
            if current_credits is not None:
                self.logger.info(f"当前费用: {current_credits}")
            
            # 识别交易信息
            transaction_info = self.recognize_transaction_info(image)
            if not transaction_info:
                return False
            
            self.logger.debug(f"交易信息: {transaction_info}")
            
            # 判断是否执行交易
            if self.should_buy_item(transaction_info):
                return self.execute_buy(transaction_info)
            elif self.should_sell_item(transaction_info):
                return self.execute_sell(transaction_info)
            
            return False
        except Exception as e:
            self.logger.error(f"检查交易机会失败: {str(e)}", exc_info=True)
            return False
    
    def get_transaction_coordinates(self, action_type: str) -> Tuple[int, int]:
        """获取交易操作坐标
        
        Args:
            action_type: 操作类型 ('buy', 'sell', 'confirm', 'cancel')
            
        Returns:
            操作坐标 (x, y)
        """
        return self.transaction_coords.get(f'{action_type}_button', (0, 0))
    
    def set_transaction_coordinates(self, action_type: str, coords: Tuple[int, int]):
        """设置交易操作坐标
        
        Args:
            action_type: 操作类型
            coords: 坐标 (x, y)
        """
        self.transaction_coords[f'{action_type}_button'] = coords
    
    def get_current_credits(self) -> int:
        """获取当前费用
        
        Returns:
            当前费用
        """
        return self.current_credits
    
    def update_transaction_history(self, transaction_type: str, item_name: str, price: int, success: bool):
        """更新交易历史
        
        Args:
            transaction_type: 交易类型 ('buy' 或 'sell')
            item_name: 物品名称
            price: 交易价格
            success: 交易是否成功
        """
        # 记录交易日志
        status = "成功" if success else "失败"
        self.logger.info(f"交易记录: {transaction_type} {item_name}，价格: {price}，状态: {status}")
        
        # 可以扩展为保存到文件或数据库
    
    def is_transaction_screen(self, image: np.ndarray) -> bool:
        """检查当前是否为交易界面
        
        Args:
            image: 当前屏幕图像
            
        Returns:
            是交易界面返回True，否则返回False
        """
        try:
            # 使用OCR识别界面文本
            ocr_results = self.ocr.recognize(image)
            
            if ocr_results:
                full_text = ' '.join([result['text'] for result in ocr_results])
                
                # 检查是否包含交易相关关键词
                transaction_keywords = ['购买', '出售', '星穹', '价格', '确认', '取消']
                
                for keyword in transaction_keywords:
                    if keyword in full_text:
                        return True
            
            return False
        except Exception as e:
            self.logger.error(f"检查交易界面失败: {str(e)}", exc_info=True)
            return False