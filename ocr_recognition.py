#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR识别模块
集成Tesseract和PaddleOCR，实现文本识别
"""

import os
import time
from typing import Optional, List, Dict, Tuple

class OCRRecognizer:
    """OCR识别器类"""
    
    def __init__(self, ocr_type: str = "paddle", logger=None, config=None):
        """初始化OCR识别器
        
        Args:
            ocr_type: OCR类型，可选值：paddle, tesseract
            logger: 日志对象
            config: 配置对象
        """
        self.ocr_type = ocr_type.lower()
        self.logger = logger
        self.config = config
        self.ocr_engine = None
        self.initialized = False
        
    def initialize(self) -> bool:
        """初始化OCR引擎
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            self.logger.info(f"初始化{self.ocr_type} OCR引擎...")
            
            if self.ocr_type == "paddle":
                return self._init_paddle_ocr()
            elif self.ocr_type == "tesseract":
                return self._init_tesseract_ocr()
            else:
                self.logger.error(f"不支持的OCR类型: {self.ocr_type}")
                return False
        except Exception as e:
            self.logger.error(f"OCR引擎初始化失败: {str(e)}", exc_info=True)
            return False
    
    def _init_paddle_ocr(self) -> bool:
        """初始化PaddleOCR
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 尝试导入PaddleOCR
            from paddleocr import PaddleOCR
            
            # 配置PaddleOCR
            ocr_config = {
                'lang': self.config.ocr_language,
                'use_angle_cls': True,
                'use_gpu': False,  # 默认使用CPU，避免GPU依赖问题
                'show_log': False
            }
            
            # 如果配置了PaddleOCR路径，添加到系统路径
            if self.config.paddle_ocr_path:
                import sys
                sys.path.append(self.config.paddle_ocr_path)
            
            # 初始化OCR引擎
            self.ocr_engine = PaddleOCR(**ocr_config)
            self.logger.info("PaddleOCR引擎初始化成功")
            self.initialized = True
            return True
        except ImportError:
            self.logger.error("PaddleOCR模块未安装，请运行: pip install paddlepaddle paddleocr")
            return False
        except Exception as e:
            self.logger.error(f"PaddleOCR初始化失败: {str(e)}", exc_info=True)
            return False
    
    def _init_tesseract_ocr(self) -> bool:
        """初始化Tesseract OCR
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 尝试导入pytesseract
            import pytesseract
            
            # 配置Tesseract路径
            if self.config.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_path
            
            if self.config.tesseract_data_path:
                os.environ['TESSDATA_PREFIX'] = self.config.tesseract_data_path
            
            # 测试Tesseract是否可用
            test_result = pytesseract.image_to_string("test")
            self.logger.info("Tesseract OCR引擎初始化成功")
            self.initialized = True
            return True
        except ImportError:
            self.logger.error("pytesseract模块未安装，请运行: pip install pytesseract opencv-python")
            return False
        except Exception as e:
            self.logger.error(f"Tesseract初始化失败: {str(e)}", exc_info=True)
            self.logger.error("请确保Tesseract已正确安装并配置路径")
            return False
    
    def recognize(self, image, region: Tuple[int, int, int, int] = None) -> List[Dict]:
        """识别图像中的文本
        
        Args:
            image: 输入图像（路径或numpy数组）
            region: 识别区域 (x, y, w, h)，None表示全图
            
        Returns:
            识别结果列表，每个结果包含text和confidence字段
        """
        if not self.initialized:
            self.logger.error("OCR引擎未初始化")
            return []
        
        try:
            # 处理图像
            processed_image = self._preprocess_for_ocr(image, region)
            if processed_image is None:
                return []
            
            start_time = time.time()
            
            if self.ocr_type == "paddle":
                results = self._paddle_ocr_recognize(processed_image)
            else:
                results = self._tesseract_ocr_recognize(processed_image)
            
            end_time = time.time()
            self.logger.debug(f"OCR识别耗时: {(end_time - start_time) * 1000:.2f} ms")
            
            # 过滤低置信度结果
            filtered_results = []
            for result in results:
                if result['confidence'] >= self.config.ocr_confidence:
                    filtered_results.append(result)
            
            self.logger.debug(f"OCR识别结果: {filtered_results}")
            return filtered_results
        except Exception as e:
            self.logger.error(f"OCR识别失败: {str(e)}", exc_info=True)
            return []
    
    def _preprocess_for_ocr(self, image, region: Tuple[int, int, int, int] = None):
        """OCR前的图像预处理
        
        Args:
            image: 输入图像
            region: 识别区域
            
        Returns:
            预处理后的图像
        """
        import cv2
        import numpy as np
        
        try:
            # 如果是图像路径，加载图像
            if isinstance(image, str):
                if not os.path.exists(image):
                    self.logger.error(f"图像文件不存在: {image}")
                    return None
                image = cv2.imread(image)
                if image is None:
                    self.logger.error(f"无法加载图像: {image}")
                    return None
            elif not isinstance(image, np.ndarray):
                self.logger.error(f"不支持的图像类型: {type(image)}")
                return None
            
            # 裁剪区域
            if region:
                x, y, w, h = region
                h_img, w_img = image.shape[:2]
                x = max(0, x)
                y = max(0, y)
                w = min(w, w_img - x)
                h = min(h, h_img - y)
                image = image[y:y+h, x:x+w]
            
            return image
        except Exception as e:
            self.logger.error(f"OCR图像预处理失败: {str(e)}")
            return None
    
    def _paddle_ocr_recognize(self, image) -> List[Dict]:
        """使用PaddleOCR识别文本
        
        Args:
            image: 输入图像
            
        Returns:
            识别结果列表
        """
        results = []
        
        try:
            # 使用PaddleOCR识别
            ocr_results = self.ocr_engine.ocr(image, cls=True)
            
            # 处理识别结果
            if ocr_results and ocr_results[0]:
                for line in ocr_results[0]:
                    text = line[1][0]
                    confidence = line[1][1]
                    results.append({
                        'text': text,
                        'confidence': confidence
                    })
        except Exception as e:
            self.logger.error(f"PaddleOCR识别失败: {str(e)}", exc_info=True)
        
        return results
    
    def _tesseract_ocr_recognize(self, image) -> List[Dict]:
        """使用Tesseract OCR识别文本
        
        Args:
            image: 输入图像
            
        Returns:
            识别结果列表
        """
        results = []
        
        try:
            import pytesseract
            
            # 配置Tesseract参数
            config = f'--oem 3 --psm 6 -l {self.config.ocr_language}'
            
            # 使用pytesseract识别
            text = pytesseract.image_to_string(image, config=config)
            
            # 使用image_to_data获取置信度
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            
            for i in range(len(data['text'])):
                text_item = data['text'][i].strip()
                confidence = int(data['conf'][i]) / 100.0
                
                if text_item and confidence > 0:
                    results.append({
                        'text': text_item,
                        'confidence': confidence
                    })
        except Exception as e:
            self.logger.error(f"Tesseract识别失败: {str(e)}", exc_info=True)
        
        return results
    
    def recognize_single_line(self, image, region: Tuple[int, int, int, int] = None) -> Optional[str]:
        """识别单行文本
        
        Args:
            image: 输入图像
            region: 识别区域
            
        Returns:
            识别结果文本，失败返回None
        """
        results = self.recognize(image, region)
        if results:
            # 合并所有识别结果
            return ' '.join([result['text'] for result in results])
        return None
    
    def recognize_number(self, image, region: Tuple[int, int, int, int] = None) -> Optional[int]:
        """识别数字
        
        Args:
            image: 输入图像
            region: 识别区域
            
        Returns:
            识别的数字，失败返回None
        """
        import re
        
        text = self.recognize_single_line(image, region)
        if text:
            # 提取数字
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        
        return None
    
    def cleanup(self):
        """清理OCR引擎资源"""
        try:
            if self.ocr_engine and self.ocr_type == "paddle":
                # PaddleOCR没有明确的关闭方法，这里做一些清理
                self.ocr_engine = None
                self.logger.info("PaddleOCR引擎已清理")
            
            self.initialized = False
        except Exception as e:
            self.logger.error(f"OCR引擎清理失败: {str(e)}")
    
    def get_ocr_type(self) -> str:
        """获取OCR类型
        
        Returns:
            OCR类型
        """
        return self.ocr_type
    
    def is_initialized(self) -> bool:
        """检查OCR引擎是否已初始化
        
        Returns:
            已初始化返回True，否则返回False
        """
        return self.initialized
