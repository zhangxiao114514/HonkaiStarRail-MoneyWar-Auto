#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理模块
负责图像预处理，提高OCR识别准确性
"""

import os
import cv2
import numpy as np
from datetime import datetime
from typing import Optional, Tuple

class ImageProcessor:
    """图像处理类"""
    
    def __init__(self, logger=None, config=None):
        """初始化图像处理模块
        
        Args:
            logger: 日志对象
            config: 配置对象
        """
        self.logger = logger
        self.config = config
        
        # 分辨率适配映射
        self.resolution_map = {
            (1080, 2340): 1.0,  # 标准1080p
            (1440, 3200): 1.333,  # 1440p
            (720, 1600): 0.667,  # 720p
            (2160, 3840): 2.0,  # 4K
            (1080, 1920): 1.0  # 横屏1080p
        }
        
        # 当前屏幕分辨率
        self.current_resolution = (1080, 2340)
        self.scale_factor = 1.0
        
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """加载图像
        
        Args:
            image_path: 图像路径
            
        Returns:
            图像数组，失败返回None
        """
        try:
            if not os.path.exists(image_path):
                self.logger.error(f"图像文件不存在: {image_path}")
                return None
            
            # 使用OpenCV加载图像
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"无法加载图像: {image_path}")
                return None
            
            return image
        except Exception as e:
            self.logger.error(f"加载图像失败: {str(e)}")
            return None
    
    def save_image(self, image: np.ndarray, save_path: str) -> bool:
        """保存图像
        
        Args:
            image: 图像数组
            save_path: 保存路径
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 创建保存目录
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 保存图像
            success = cv2.imwrite(save_path, image)
            if not success:
                self.logger.error(f"无法保存图像: {save_path}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"保存图像失败: {str(e)}")
            return False
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """图像预处理
        
        Args:
            image: 原始图像
            
        Returns:
            预处理后的图像
        """
        try:
            processed = image.copy()
            
            # 1. 转为灰度图
            if self.config.grayscale:
                processed = self.to_grayscale(processed)
            
            # 2. 调整亮度和对比度
            processed = self.adjust_brightness_contrast(
                processed, 
                brightness=self.config.brightness, 
                contrast=self.config.contrast
            )
            
            # 3. 模糊处理（降噪）
            if self.config.blur_kernel > 0:
                processed = self.blur(processed, kernel_size=self.config.blur_kernel)
            
            # 4. 二值化
            processed = self.binarize(processed, threshold=self.config.threshold)
            
            return processed
        except Exception as e:
            self.logger.error(f"图像预处理失败: {str(e)}")
            return image
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """转为灰度图
        
        Args:
            image: 彩色图像
            
        Returns:
            灰度图像
        """
        if len(image.shape) == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def adjust_brightness_contrast(self, image: np.ndarray, brightness: int = 0, contrast: float = 1.0) -> np.ndarray:
        """调整亮度和对比度
        
        Args:
            image: 输入图像
            brightness: 亮度调整值（-255 到 255）
            contrast: 对比度调整因子（0.0 到 3.0）
            
        Returns:
            调整后的图像
        """
        # 应用亮度和对比度调整
        # 公式: new_image = alpha * image + beta
        # alpha = contrast, beta = brightness
        return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)
    
    def blur(self, image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """模糊处理（降噪）
        
        Args:
            image: 输入图像
            kernel_size: 模糊内核大小
            
        Returns:
            模糊后的图像
        """
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    def binarize(self, image: np.ndarray, threshold: int = 128) -> np.ndarray:
        """图像二值化
        
        Args:
            image: 输入图像
            threshold: 二值化阈值
            
        Returns:
            二值化后的图像
        """
        # 如果是彩色图像，转为灰度图
        if len(image.shape) == 3:
            image = self.to_grayscale(image)
        
        # 二值化处理
        _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        return binary
    
    def resize(self, image: np.ndarray, width: int = None, height: int = None, keep_ratio: bool = True) -> np.ndarray:
        """调整图像大小
        
        Args:
            image: 输入图像
            width: 目标宽度
            height: 目标高度
            keep_ratio: 是否保持宽高比
            
        Returns:
            调整大小后的图像
        """
        if not width and not height:
            return image
        
        h, w = image.shape[:2]
        
        if keep_ratio:
            if width and not height:
                # 按宽度缩放
                ratio = width / w
                height = int(h * ratio)
            elif height and not width:
                # 按高度缩放
                ratio = height / h
                width = int(w * ratio)
        
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    
    def crop(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """裁剪图像
        
        Args:
            image: 输入图像
            x: 起始X坐标
            y: 起始Y坐标
            w: 宽度
            h: 高度
            
        Returns:
            裁剪后的图像
        """
        h_img, w_img = image.shape[:2]
        
        # 确保裁剪区域在图像范围内
        x = max(0, x)
        y = max(0, y)
        w = min(w, w_img - x)
        h = min(h, h_img - y)
        
        if w <= 0 or h <= 0:
            self.logger.error(f"无效的裁剪区域: x={x}, y={y}, w={w}, h={h}")
            return image
        
        return image[y:y+h, x:x+w]
    
    def find_template(self, image: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> Optional[Tuple[float, Tuple[int, int, int, int]]]:
        """模板匹配
        
        Args:
            image: 输入图像
            template: 模板图像
            threshold: 匹配阈值
            
        Returns:
            (匹配度, (x, y, w, h))，失败返回None
        """
        try:
            # 如果是彩色图像，转为灰度图
            if len(image.shape) == 3:
                image_gray = self.to_grayscale(image)
            else:
                image_gray = image
            
            if len(template.shape) == 3:
                template_gray = self.to_grayscale(template)
            else:
                template_gray = template
            
            # 模板匹配
            result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            
            # 查找最大值
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template_gray.shape[:2]
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                
                # 计算中心坐标
                center_x = top_left[0] + w // 2
                center_y = top_left[1] + h // 2
                
                return (max_val, (center_x - w//2, center_y - h//2, w, h))
            
            return None
        except Exception as e:
            self.logger.error(f"模板匹配失败: {str(e)}")
            return None
    
    def get_text_region(self, image: np.ndarray, region: Tuple[int, int, int, int]) -> np.ndarray:
        """获取文本区域
        
        Args:
            image: 原始图像
            region: 区域坐标 (x, y, w, h)
            
        Returns:
            文本区域图像
        """
        x, y, w, h = region
        return self.crop(image, x, y, w, h)
    
    def draw_rectangle(self, image: np.ndarray, x: int, y: int, w: int, h: int, color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """绘制矩形
        
        Args:
            image: 输入图像
            x: 起始X坐标
            y: 起始Y坐标
            w: 宽度
            h: 高度
            color: 矩形颜色 (B, G, R)
            thickness: 线条粗细
            
        Returns:
            绘制后的图像
        """
        drawn = image.copy()
        cv2.rectangle(drawn, (x, y), (x + w, y + h), color, thickness)
        return drawn
    
    def draw_text(self, image: np.ndarray, text: str, x: int, y: int, color: Tuple[int, int, int] = (0, 255, 0), font_size: float = 0.5, thickness: int = 1) -> np.ndarray:
        """绘制文本
        
        Args:
            image: 输入图像
            text: 文本内容
            x: X坐标
            y: Y坐标
            color: 文本颜色 (B, G, R)
            font_size: 字体大小
            thickness: 线条粗细
            
        Returns:
            绘制后的图像
        """
        drawn = image.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(drawn, text, (x, y), font, font_size, color, thickness, cv2.LINE_AA)
        return drawn
    
    def get_edges(self, image: np.ndarray, low_threshold: int = 100, high_threshold: int = 200) -> np.ndarray:
        """边缘检测
        
        Args:
            image: 输入图像
            low_threshold: 低阈值
            high_threshold: 高阈值
            
        Returns:
            边缘图像
        """
        # 如果是彩色图像，转为灰度图
        if len(image.shape) == 3:
            image = self.to_grayscale(image)
        
        return cv2.Canny(image, low_threshold, high_threshold)
    
    def count_pixels(self, image: np.ndarray, min_value: int = 0, max_value: int = 255) -> int:
        """统计像素数量
        
        Args:
            image: 输入图像
            min_value: 最小像素值
            max_value: 最大像素值
            
        Returns:
            符合条件的像素数量
        """
        # 如果是彩色图像，转为灰度图
        if len(image.shape) == 3:
            image = self.to_grayscale(image)
        
        return np.sum((image >= min_value) & (image <= max_value))
    
    def get_average_color(self, image: np.ndarray) -> Tuple[int, int, int]:
        """获取平均颜色
        
        Args:
            image: 输入图像
            
        Returns:
            平均颜色 (B, G, R) 或灰度值
        """
        if len(image.shape) == 3:
            # 彩色图像
            avg_color = np.mean(image, axis=(0, 1))
            return tuple(map(int, avg_color))
        else:
            # 灰度图像
            avg_gray = np.mean(image)
            return (int(avg_gray), int(avg_gray), int(avg_gray))
    
    def rotate(self, image: np.ndarray, angle: float, center: Tuple[int, int] = None, scale: float = 1.0) -> np.ndarray:
        """旋转图像
        
        Args:
            image: 输入图像
            angle: 旋转角度
            center: 旋转中心，None表示图像中心
            scale: 缩放因子
            
        Returns:
            旋转后的图像
        """
        h, w = image.shape[:2]
        
        if not center:
            center = (w // 2, h // 2)
        
        # 计算旋转矩阵
        M = cv2.getRotationMatrix2D(center, angle, scale)
        
        # 执行旋转
        rotated = cv2.warpAffine(image, M, (w, h))
        return rotated
    
    def set_current_resolution(self, width: int, height: int):
        """设置当前屏幕分辨率
        
        Args:
            width: 屏幕宽度
            height: 屏幕高度
        """
        self.current_resolution = (width, height)
        
        # 计算缩放因子
        if (width, height) in self.resolution_map:
            self.scale_factor = self.resolution_map[(width, height)]
        else:
            # 计算与标准分辨率的比例
            standard_width, standard_height = 1080, 2340
            self.scale_factor = min(width / standard_width, height / standard_height)
        
        self.logger.info(f"设置当前分辨率: {width}x{height}，缩放因子: {self.scale_factor}")
    
    def scale_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """根据当前分辨率缩放坐标
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            缩放后的坐标 (x, y)
        """
        scaled_x = int(x * self.scale_factor)
        scaled_y = int(y * self.scale_factor)
        return (scaled_x, scaled_y)
    
    def scale_region(self, region: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """根据当前分辨率缩放区域
        
        Args:
            region: 区域坐标 (x, y, w, h)
            
        Returns:
            缩放后的区域 (x, y, w, h)
        """
        x, y, w, h = region
        scaled_x, scaled_y = self.scale_coordinates(x, y)
        scaled_w = int(w * self.scale_factor)
        scaled_h = int(h * self.scale_factor)
        return (scaled_x, scaled_y, scaled_w, scaled_h)
    
    def adaptive_preprocess(self, image: np.ndarray) -> np.ndarray:
        """自适应图像预处理，根据图像特征调整处理参数
        
        Args:
            image: 输入图像
            
        Returns:
            预处理后的图像
        """
        try:
            processed = image.copy()
            h, w = processed.shape[:2]
            
            # 自动调整分辨率
            self.set_current_resolution(w, h)
            
            # 1. 转为灰度图（如果配置启用）
            if self.config.grayscale:
                processed = self.to_grayscale(processed)
            
            # 2. 自动调整亮度和对比度
            # 计算图像亮度均值
            avg_brightness = np.mean(processed)
            
            # 根据亮度自动调整参数
            if avg_brightness < 100:
                # 暗图像，增加亮度
                brightness = self.config.brightness + 20
                contrast = self.config.contrast * 1.2
            elif avg_brightness > 180:
                # 亮图像，降低亮度
                brightness = self.config.brightness - 10
                contrast = self.config.contrast * 0.8
            else:
                # 正常亮度，使用配置参数
                brightness = self.config.brightness
                contrast = self.config.contrast
            
            processed = self.adjust_brightness_contrast(processed, brightness, contrast)
            
            # 3. 自适应模糊处理
            # 根据图像噪声情况调整模糊程度
            blur_kernel = self.config.blur_kernel
            
            # 计算图像梯度（边缘强度）
            if len(processed.shape) == 3:
                gray = self.to_grayscale(processed)
            else:
                gray = processed
            
            edge_strength = np.mean(cv2.Laplacian(gray, cv2.CV_64F).var())
            
            if edge_strength > 100:
                # 边缘较强，降低模糊程度
                blur_kernel = max(1, self.config.blur_kernel - 2)
            elif edge_strength < 20:
                # 边缘较弱，增加模糊程度
                blur_kernel = self.config.blur_kernel + 2
            
            if blur_kernel > 0:
                processed = self.blur(processed, blur_kernel)
            
            # 4. 自适应二值化
            # 根据图像特征选择合适的阈值
            if len(processed.shape) == 3:
                gray = self.to_grayscale(processed)
            else:
                gray = processed
            
            # 使用Otsu阈值
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return processed
        except Exception as e:
            self.logger.error(f"自适应预处理失败: {str(e)}")
            return self.preprocess(image)
