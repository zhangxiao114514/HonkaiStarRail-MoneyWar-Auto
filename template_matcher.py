#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板匹配模块
用于识别游戏中的关键UI元素
"""

import cv2
import numpy as np
import os
import time
from typing import Optional, Tuple

class TemplateMatcher:
    """模板匹配类"""
    
    def __init__(self, logger=None):
        """初始化模板匹配器
        
        Args:
            logger: 日志对象
        """
        self.logger = logger
        self.templates = {}
        self.template_dir = "templates"
        
        # 创建模板目录
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            self.log("创建模板目录: templates", "INFO")
    
    def log(self, message: str, level: str = "INFO"):
        """日志记录
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        if self.logger:
            # 检查logger是否有日志级别方法
            if hasattr(self.logger, level.lower()):
                getattr(self.logger, level.lower())(message)
            else:
                # 兼容旧的logger接口
                self.logger(message)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] [{level}] {message}")
    
    def load_template(self, name: str, template_path: str) -> bool:
        """加载模板图像
        
        Args:
            name: 模板名称
            template_path: 模板图像路径
            
        Returns:
            加载成功返回True，否则返回False
        """
        try:
            if not os.path.exists(template_path):
                self.log(f"模板文件不存在: {template_path}", "WARNING")
                return False
            
            # 读取模板图像
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                self.log(f"无法加载模板: {template_path}", "ERROR")
                return False
            
            # 验证模板大小合理性
            if template.shape[0] < 10 or template.shape[1] < 10:
                self.log(f"模板尺寸过小: {name} ({template.shape[1]}x{template.shape[0]})")
                # 仍然加载，但给出警告
            
            self.templates[name] = template
            self.log(f"加载模板成功: {name} ({template.shape[1]}x{template.shape[0]})")
            return True
        except Exception as e:
            self.log(f"加载模板失败: {str(e)}", "ERROR")
            return False
    
    def validate_templates(self) -> bool:
        """验证所有已加载模板的有效性
        
        Returns:
            所有模板有效返回True，否则返回False
        """
        if not self.templates:
            self.log("没有加载任何模板", "WARNING")
            return False
        
        all_valid = True
        for name, template in self.templates.items():
            if template is None:
                self.log(f"模板无效: {name}", "ERROR")
                all_valid = False
            elif template.shape[0] < 10 or template.shape[1] < 10:
                self.log(f"模板尺寸过小: {name} ({template.shape[1]}x{template.shape[0]})")
                # 尺寸过小不影响整体验证结果
        
        return all_valid
    
    def check_template_update(self, name: str, current_image, threshold: float = 0.9) -> bool:
        """检查模板是否需要更新
        
        Args:
            name: 模板名称
            current_image: 当前屏幕图像
            threshold: 更新阈值
            
        Returns:
            需要更新返回True，否则返回False
        """
        if name not in self.templates:
            self.log(f"模板不存在: {name}", "WARNING")
            return True
        
        # 匹配当前模板
        match_result = self.match_template(current_image, name, threshold)
        if not match_result:
            self.log(f"模板匹配失败，建议更新: {name}", "INFO")
            return True
        
        return False
    
    def update_template(self, name: str, current_image, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """更新模板
        
        Args:
            name: 模板名称
            current_image: 当前屏幕图像
            region: 模板区域 (x, y, width, height)
            
        Returns:
            模板保存路径，失败返回空字符串
        """
        return self.save_template(name, current_image, region)
    
    def save_template(self, name: str, image: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """保存模板图像
        
        Args:
            name: 模板名称
            image: 源图像
            region: 模板区域 (x, y, w, h)
            
        Returns:
            模板保存路径
        """
        try:
            # 裁剪模板区域
            if region:
                x, y, w, h = region
                template_image = image[y:y+h, x:x+w]
            else:
                template_image = image
            
            # 保存路径
            template_path = os.path.join(self.template_dir, f"{name}.png")
            
            # 保存模板
            if cv2.imwrite(template_path, template_image):
                self.log(f"保存模板成功: {template_path}")
                return template_path
            else:
                self.log(f"保存模板失败: {template_path}")
                return ""
        except Exception as e:
            self.log(f"保存模板出错: {str(e)}")
            return ""
    
    def match_template(self, image: np.ndarray, template_name: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """模板匹配
        
        Args:
            image: 源图像
            template_name: 模板名称
            threshold: 匹配阈值
            
        Returns:
            匹配成功返回中心点坐标 (x, y)，否则返回None
        """
        try:
            # 检查模板是否存在
            if template_name not in self.templates:
                self.log(f"模板不存在: {template_name}")
                return None
            
            template = self.templates[template_name]
            
            # 将源图像转为灰度图
            if len(image.shape) == 3:
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray_image = image
            
            # 模板匹配
            result = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
            
            # 查找匹配位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            self.log(f"模板匹配: {template_name}, 匹配度: {max_val:.4f}, 阈值: {threshold}")
            
            if max_val >= threshold:
                # 计算中心点坐标
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                self.log(f"匹配成功: {template_name}，坐标: ({center_x}, {center_y})")
                return (center_x, center_y)
            
            return None
        except Exception as e:
            self.log(f"模板匹配出错: {str(e)}")
            return None
    
    def match_all_templates(self, image: np.ndarray, threshold: float = 0.8) -> dict:
        """匹配所有模板
        
        Args:
            image: 源图像
            threshold: 匹配阈值
            
        Returns:
            匹配结果字典，键为模板名称，值为坐标
        """
        results = {}
        
        for template_name in self.templates:
            match_result = self.match_template(image, template_name, threshold)
            if match_result:
                results[template_name] = match_result
        
        return results
    
    def ocr_simple_text(self, image: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """简单OCR识别
        
        Args:
            image: 源图像
            region: 识别区域
            
        Returns:
            识别结果文本
        """
        try:
            # 裁剪识别区域
            if region:
                x, y, w, h = region
                ocr_image = image[y:y+h, x:x+w]
            else:
                ocr_image = image
            
            # 转换为灰度图
            if len(ocr_image.shape) == 3:
                gray = cv2.cvtColor(ocr_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = ocr_image
            
            # 二值化处理
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # 使用pytesseract识别
            try:
                import pytesseract
                text = pytesseract.image_to_string(binary, lang='chi_sim', config='--oem 3 --psm 6')
                return text.strip()
            except ImportError:
                self.log("pytesseract未安装，无法进行OCR识别")
                return ""
            except Exception as e:
                self.log(f"OCR识别失败: {str(e)}")
                return ""
        except Exception as e:
            self.log(f"OCR处理出错: {str(e)}")
            return ""
    
    def get_template_size(self, template_name: str) -> Optional[Tuple[int, int]]:
        """获取模板尺寸
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板尺寸 (width, height)，失败返回None
        """
        if template_name in self.templates:
            template = self.templates[template_name]
            h, w = template.shape[:2]
            return (w, h)
        return None
    
    def clear_templates(self):
        """清除所有模板
        """
        self.templates.clear()
        self.log("清除所有模板")
