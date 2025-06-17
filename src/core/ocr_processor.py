#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR文字识别处理模块
支持多种OCR引擎，提供文字提取和处理功能
"""

import pytesseract
import easyocr
from PIL import Image
import re
import hashlib
from datetime import datetime
import os

class OCRProcessor:
    """OCR处理器类"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # OCR配置 - 优先使用EasyOCR
        self.engine = config.get('ocr.engine', 'easyocr')  # 默认使用EasyOCR
        self.language = config.get('ocr.language', 'eng+chi_sim')
        self.confidence_threshold = config.get('ocr.confidence_threshold', 60)

        # 初始化OCR引擎 - 优先EasyOCR
        self.easyocr_reader = None
        self.tesseract_available = False

        # 先尝试初始化EasyOCR
        self._init_easyocr()

        # 如果EasyOCR不可用，再尝试Tesseract
        if not self.easyocr_reader:
            self.tesseract_available = self._check_tesseract()
            
        # 文本缓存
        self.text_cache = {}
        self.cache_size_limit = 1000
        
    def _check_tesseract(self):
        """检查Tesseract是否可用"""
        try:
            pytesseract.get_tesseract_version()
            self.logger.info("Tesseract OCR 可用")
            return True
        except Exception as e:
            self.logger.warning(f"Tesseract OCR 不可用: {e}")
            return False
            
    def _init_easyocr(self):
        """初始化EasyOCR"""
        try:
            # 解析语言设置
            languages = []
            if 'eng' in self.language:
                languages.append('en')
            if 'chi_sim' in self.language:
                languages.append('ch_sim')
            if 'chi_tra' in self.language:
                languages.append('ch_tra')
                
            if not languages:
                languages = ['en']
                
            self.easyocr_reader = easyocr.Reader(languages, gpu=False)
            self.logger.info(f"EasyOCR 初始化成功，支持语言: {languages}")
            
        except Exception as e:
            self.logger.error(f"EasyOCR 初始化失败: {e}")
            self.easyocr_reader = None
            
    def extract_text(self, image):
        """
        从图像中提取文字
        
        Args:
            image: PIL.Image对象
            
        Returns:
            str: 提取的文字内容
        """
        try:
            # 检查缓存
            image_hash = self._get_image_hash(image)
            if image_hash in self.text_cache:
                return self.text_cache[image_hash]
                
            text = ""

            # 优先使用EasyOCR（对中文识别更好）
            if self.easyocr_reader:
                text = self._extract_with_easyocr(image)
                if text and len(text.strip()) > 0:
                    self.logger.debug("使用EasyOCR识别成功")
                else:
                    self.logger.debug("EasyOCR识别结果为空，尝试Tesseract")
                    if self.tesseract_available:
                        text = self._extract_with_tesseract(image)
            elif self.tesseract_available:
                text = self._extract_with_tesseract(image)
                self.logger.debug("使用Tesseract识别")
            else:
                self.logger.error("没有可用的OCR引擎")
                    
            # 后处理文本
            processed_text = self._post_process_text(text)
            
            # 缓存结果
            self._cache_text(image_hash, processed_text)
            
            return processed_text
            
        except Exception as e:
            self.logger.error(f"文字提取失败: {e}")
            return ""
            
    def _extract_with_tesseract(self, image):
        """使用Tesseract提取文字"""
        try:
            # Tesseract配置
            config = f'--oem 3 --psm 6 -l {self.language}'
            
            # 提取文字
            text = pytesseract.image_to_string(image, config=config)
            
            # 获取置信度信息
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence < self.confidence_threshold:
                    self.logger.warning(f"OCR置信度较低: {avg_confidence:.1f}%")
                    
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Tesseract提取失败: {e}")
            return ""
            
    def _extract_with_easyocr(self, image):
        """使用EasyOCR提取文字"""
        try:
            # 图像预处理增强
            enhanced_image = self._enhance_for_ocr(image)

            # 转换图像格式
            import numpy as np
            image_array = np.array(enhanced_image)

            # 提取文字
            results = self.easyocr_reader.readtext(image_array)

            # 组合文字结果
            text_parts = []
            for (bbox, text, confidence) in results:
                if confidence >= (self.confidence_threshold / 100.0):
                    text_parts.append(text)
                else:
                    self.logger.debug(f"跳过低置信度文字: {text} ({confidence:.2f})")

            return ' '.join(text_parts)

        except Exception as e:
            self.logger.error(f"EasyOCR提取失败: {e}")
            return ""

    def _enhance_for_ocr(self, image):
        """专门为OCR增强图像"""
        try:
            from PIL import ImageEnhance, ImageOps
            import numpy as np

            # 检查图像亮度
            gray = image.convert('L')
            avg_brightness = np.mean(np.array(gray))

            # 如果图像较暗，进行增强
            if avg_brightness < 100:
                # 增强亮度
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(1.5)

                # 增强对比度
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.3)

                self.logger.debug(f"图像增强：原始亮度{avg_brightness:.1f}，已增强")

            return image

        except Exception as e:
            self.logger.error(f"图像增强失败: {e}")
            return image
            
    def _post_process_text(self, text):
        """后处理文本"""
        if not text:
            return ""
            
        try:
            # 移除多余的空白字符
            text = re.sub(r'\s+', ' ', text)
            
            # 移除特殊字符（保留中英文、数字、常用标点）
            text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]', '', text)
            
            # 修复常见OCR错误
            text = self._fix_common_ocr_errors(text)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"文本后处理失败: {e}")
            return text
            
    def _fix_common_ocr_errors(self, text):
        """修复常见的OCR识别错误"""
        try:
            # 常见字符替换
            replacements = {
                '0': 'O',  # 数字0可能被识别为字母O
                '1': 'l',  # 数字1可能被识别为小写l
                '5': 'S',  # 数字5可能被识别为字母S
                '8': 'B',  # 数字8可能被识别为字母B
                'rn': 'm', # rn组合可能被识别为m
                'vv': 'w', # vv组合可能被识别为w
            }
            
            # 这里只做保守的替换，避免误修正
            # 实际应用中需要根据具体场景调整
            
            return text
            
        except Exception as e:
            self.logger.error(f"OCR错误修复失败: {e}")
            return text
            
    def _get_image_hash(self, image):
        """计算图像哈希值用于缓存"""
        try:
            # 转换为字节数据
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # 计算MD5哈希
            return hashlib.md5(img_byte_arr).hexdigest()
            
        except Exception as e:
            self.logger.error(f"计算图像哈希失败: {e}")
            return str(datetime.now().timestamp())
            
    def _cache_text(self, image_hash, text):
        """缓存文本结果"""
        try:
            # 限制缓存大小
            if len(self.text_cache) >= self.cache_size_limit:
                # 删除最旧的缓存项
                oldest_key = next(iter(self.text_cache))
                del self.text_cache[oldest_key]
                
            self.text_cache[image_hash] = text
            
        except Exception as e:
            self.logger.error(f"缓存文本失败: {e}")
            
    def extract_text_with_positions(self, image):
        """
        提取文字及其位置信息
        
        Args:
            image: PIL.Image对象
            
        Returns:
            list: [(text, x, y, width, height, confidence), ...]
        """
        try:
            results = []
            
            if self.engine == 'tesseract' and self.tesseract_available:
                results = self._extract_positions_tesseract(image)
            elif self.engine == 'easyocr' and self.easyocr_reader:
                results = self._extract_positions_easyocr(image)
                
            return results
            
        except Exception as e:
            self.logger.error(f"提取文字位置失败: {e}")
            return []
            
    def _extract_positions_tesseract(self, image):
        """使用Tesseract提取文字位置"""
        try:
            config = f'--oem 3 --psm 6 -l {self.language}'
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                confidence = int(data['conf'][i])
                
                if text and confidence >= self.confidence_threshold:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    results.append((text, x, y, w, h, confidence))
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Tesseract位置提取失败: {e}")
            return []
            
    def _extract_positions_easyocr(self, image):
        """使用EasyOCR提取文字位置"""
        try:
            import numpy as np
            image_array = np.array(image)
            
            results = []
            ocr_results = self.easyocr_reader.readtext(image_array)
            
            for (bbox, text, confidence) in ocr_results:
                if confidence >= (self.confidence_threshold / 100.0):
                    # 计算边界框
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    x = int(min(x_coords))
                    y = int(min(y_coords))
                    w = int(max(x_coords) - min(x_coords))
                    h = int(max(y_coords) - min(y_coords))
                    
                    results.append((text, x, y, w, h, int(confidence * 100)))
                    
            return results
            
        except Exception as e:
            self.logger.error(f"EasyOCR位置提取失败: {e}")
            return []
            
    def detect_language(self, text):
        """
        检测文本语言
        
        Args:
            text: 文本内容
            
        Returns:
            str: 语言代码 ('en', 'zh', 'mixed')
        """
        try:
            if not text:
                return 'unknown'
                
            # 统计中英文字符
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            
            total_chars = chinese_chars + english_chars
            if total_chars == 0:
                return 'unknown'
                
            chinese_ratio = chinese_chars / total_chars
            
            if chinese_ratio > 0.7:
                return 'zh'
            elif chinese_ratio < 0.3:
                return 'en'
            else:
                return 'mixed'
                
        except Exception as e:
            self.logger.error(f"语言检测失败: {e}")
            return 'unknown'
            
    def clean_cache(self):
        """清理文本缓存"""
        try:
            self.text_cache.clear()
            self.logger.info("文本缓存已清理")
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")
            
    def get_cache_stats(self):
        """获取缓存统计信息"""
        return {
            'cache_size': len(self.text_cache),
            'cache_limit': self.cache_size_limit,
            'engine': self.engine,
            'tesseract_available': self.tesseract_available,
            'easyocr_available': self.easyocr_reader is not None
        }
