#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
屏幕截图模块
负责截取指定区域的屏幕内容
"""

import pyautogui
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
import os
from datetime import datetime

class ScreenCapture:
    """屏幕截图类"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        # 禁用pyautogui的安全检查
        pyautogui.FAILSAFE = False

        # 截图设置
        self.image_scale = config.get('capture.image_scale', 2.0)
        self.save_screenshots = config.get('capture.save_screenshots', False)
        self.screenshot_dir = 'screenshots'

        # 确保截图目录存在
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def capture_region(self, region):
        """
        截取指定区域的屏幕内容

        Args:
            region: 区域坐标 (x, y, width, height)

        Returns:
            PIL.Image: 截图图像，失败返回None
        """
        try:
            x, y, width, height = region

            # 使用pyautogui截图
            screenshot = pyautogui.screenshot(region=(x, y, width, height))

            # 图像预处理
            processed_image = self.preprocess_image(screenshot)

            # 保存截图（如果启用）
            if self.save_screenshots:
                self.save_screenshot(processed_image, region)

            return processed_image

        except Exception as e:
            self.logger.error(f"截取区域失败 {region}: {e}")
            return None

    def capture_full_screen(self):
        """
        截取全屏

        Returns:
            PIL.Image: 全屏截图
        """
        try:
            screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            self.logger.error(f"全屏截图失败: {e}")
            return None
            
    def preprocess_image(self, image):
        """
        图像预处理，提高OCR识别率
        
        Args:
            image: PIL.Image对象
            
        Returns:
            PIL.Image: 处理后的图像
        """
        try:
            # 转换为RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            # 放大图像提高清晰度
            if self.image_scale != 1.0:
                new_width = int(image.width * self.image_scale)
                new_height = int(image.height * self.image_scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
            # 增强对比度
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # 增强锐度
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # 转换为OpenCV格式进行进一步处理
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # 去噪
            cv_image = cv2.bilateralFilter(cv_image, 9, 75, 75)
            
            # 转换回PIL格式
            processed_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            
            return processed_image
            
        except Exception as e:
            self.logger.error(f"图像预处理失败: {e}")
            return image  # 返回原图像
            
    def enhance_for_ocr(self, image):
        """
        专门为OCR优化图像
        
        Args:
            image: PIL.Image对象
            
        Returns:
            PIL.Image: OCR优化后的图像
        """
        try:
            # 转换为灰度图
            gray_image = image.convert('L')
            
            # 转换为OpenCV格式
            cv_image = np.array(gray_image)
            
            # 自适应阈值处理
            binary_image = cv2.adaptiveThreshold(
                cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 形态学操作去除噪点
            kernel = np.ones((1, 1), np.uint8)
            binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
            
            # 转换回PIL格式
            enhanced_image = Image.fromarray(binary_image)
            
            return enhanced_image
            
        except Exception as e:
            self.logger.error(f"OCR图像增强失败: {e}")
            return image.convert('L')  # 返回灰度图
            
    def save_screenshot(self, image, region):
        """
        保存截图到文件
        
        Args:
            image: PIL.Image对象
            region: 区域坐标
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            x, y, w, h = region
            filename = f"screenshot_{timestamp}_{x}_{y}_{w}x{h}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            image.save(filepath)
            self.logger.debug(f"截图已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存截图失败: {e}")
            
    def get_screen_size(self):
        """
        获取屏幕尺寸
        
        Returns:
            tuple: (width, height)
        """
        try:
            return pyautogui.size()
        except Exception as e:
            self.logger.error(f"获取屏幕尺寸失败: {e}")
            return (1920, 1080)  # 默认值
            
    def validate_region(self, region):
        """
        验证区域坐标是否有效
        
        Args:
            region: 区域坐标 (x, y, width, height)
            
        Returns:
            bool: 是否有效
        """
        try:
            x, y, width, height = region
            screen_width, screen_height = self.get_screen_size()
            
            # 检查坐标是否在屏幕范围内
            if x < 0 or y < 0:
                return False
                
            if x + width > screen_width or y + height > screen_height:
                return False
                
            # 检查尺寸是否合理
            if width <= 0 or height <= 0:
                return False
                
            if width < 10 or height < 10:  # 最小尺寸限制
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"验证区域失败: {e}")
            return False
            
    def crop_image(self, image, crop_region):
        """
        裁剪图像
        
        Args:
            image: PIL.Image对象
            crop_region: 裁剪区域 (x, y, width, height)
            
        Returns:
            PIL.Image: 裁剪后的图像
        """
        try:
            x, y, width, height = crop_region
            cropped = image.crop((x, y, x + width, y + height))
            return cropped
        except Exception as e:
            self.logger.error(f"裁剪图像失败: {e}")
            return image
            
    def compare_images(self, image1, image2, threshold=0.95):
        """
        比较两个图像的相似度
        
        Args:
            image1, image2: PIL.Image对象
            threshold: 相似度阈值
            
        Returns:
            bool: 是否相似
        """
        try:
            # 确保图像尺寸相同
            if image1.size != image2.size:
                image2 = image2.resize(image1.size)
                
            # 转换为numpy数组
            arr1 = np.array(image1.convert('L'))
            arr2 = np.array(image2.convert('L'))
            
            # 计算结构相似性（简化版本）
            # 使用numpy计算相似度
            diff = np.abs(arr1.astype(float) - arr2.astype(float))
            similarity = 1.0 - (np.mean(diff) / 255.0)
            
            return similarity >= threshold
            
        except Exception as e:
            self.logger.error(f"图像比较失败: {e}")
            return False
            
    def detect_text_regions(self, image):
        """
        检测图像中的文本区域
        
        Args:
            image: PIL.Image对象
            
        Returns:
            list: 文本区域列表 [(x, y, width, height), ...]
        """
        try:
            # 转换为OpenCV格式
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # 使用MSER检测文本区域
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            
            # 转换为边界框
            text_regions = []
            for region in regions:
                x, y, w, h = cv2.boundingRect(region)
                # 过滤太小的区域
                if w > 10 and h > 10:
                    text_regions.append((x, y, w, h))
                    
            return text_regions
            
        except Exception as e:
            self.logger.error(f"文本区域检测失败: {e}")
            return []
            
    def cleanup_old_screenshots(self, days=7):
        """
        清理旧的截图文件
        
        Args:
            days: 保留天数
        """
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            for filename in os.listdir(self.screenshot_dir):
                filepath = os.path.join(self.screenshot_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        self.logger.debug(f"删除旧截图: {filename}")
                        
        except Exception as e:
            self.logger.error(f"清理截图失败: {e}")
