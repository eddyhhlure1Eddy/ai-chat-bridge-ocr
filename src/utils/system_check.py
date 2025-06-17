#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统环境检查模块
"""

import sys
import subprocess
import importlib
import shutil
from typing import List

class SystemChecker:
    """系统环境检查器"""
    
    def __init__(self):
        self.required_packages = [
            'PIL',  # pillow
            'pytesseract',
            'pyautogui', 
            'cv2',  # opencv-python
            'easyocr',
            'numpy',
            'pyperclip'
        ]
        
    def check_python_version(self, min_version=(3, 8)) -> bool:
        """检查Python版本"""
        try:
            current_version = sys.version_info[:2]
            return current_version >= min_version
        except Exception:
            return False
            
    def check_required_packages(self) -> List[str]:
        """检查必要的Python包"""
        missing_packages = []
        
        for package in self.required_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                # 处理包名映射
                if package == 'PIL':
                    missing_packages.append('pillow')
                elif package == 'cv2':
                    missing_packages.append('opencv-python')
                else:
                    missing_packages.append(package)
                    
        return missing_packages
        
    def check_ocr_engines(self) -> bool:
        """检查OCR引擎是否可用"""
        # 检查Tesseract
        tesseract_available = self._check_tesseract()
        
        # 检查EasyOCR
        easyocr_available = self._check_easyocr()
        
        return tesseract_available or easyocr_available
        
    def _check_tesseract(self) -> bool:
        """检查Tesseract OCR"""
        try:
            # 检查tesseract命令是否存在
            if shutil.which('tesseract'):
                return True
                
            # 检查pytesseract是否能正常工作
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
            
    def _check_easyocr(self) -> bool:
        """检查EasyOCR"""
        try:
            import easyocr
            return True
        except Exception:
            return False
            
    def get_system_info(self) -> dict:
        """获取系统信息"""
        import platform
        
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'tesseract_available': self._check_tesseract(),
            'easyocr_available': self._check_easyocr()
        }
        
    def install_package(self, package_name: str) -> bool:
        """安装Python包"""
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package_name
            ])
            return True
        except subprocess.CalledProcessError:
            return False
