#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import json
import os
from typing import Any, Dict, Optional

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = {}
        self.default_config = self._get_default_config()
        
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "ocr": {
                "engine": "tesseract",
                "language": "eng+chi_sim",
                "confidence_threshold": 60,
                "fallback_engine": "easyocr"
            },
            "capture": {
                "interval": 2.0,
                "image_scale": 2.0,
                "save_screenshots": False,
                "screenshot_retention_days": 7
            },
            "typing": {
                "delay_min": 0.05,
                "delay_max": 0.15,
                "pause_probability": 0.1,
                "pause_duration_min": 0.5,
                "pause_duration_max": 2.0,
                "use_clipboard": True,
                "speed_variation": 0.3,
                "max_message_length": 2000
            },
            "conversation": {
                "max_length": 100,
                "auto_save": True,
                "save_interval": 10,
                "message_similarity_threshold": 0.8,
                "ignore_system_messages": True
            },
            "ui": {
                "theme": "default",
                "font_size": 10,
                "window_size": "1200x800",
                "auto_scroll": True,
                "show_timestamps": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log",
                "max_file_size": "10MB",
                "backup_count": 5,
                "console_output": True
            },
            "detection": {
                "new_message_keywords": [
                    "刚刚", "现在", "just now", "now"
                ],
                "typing_indicators": [
                    "正在输入", "typing", "is typing", "..."
                ],
                "system_message_patterns": [
                    "系统消息", "system", "bot", "助手"
                ]
            },
            "safety": {
                "max_retry_attempts": 3,
                "error_cooldown": 5.0,
                "rate_limit_delay": 1.0,
                "emergency_stop_key": "F12"
            }
        }
        
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    
                # 合并默认配置（处理新增的配置项）
                self.config = self._merge_config(self.default_config, self.config)
            else:
                # 使用默认配置并保存
                self.config = self.default_config.copy()
                self.save_config()
                
        except Exception as e:
            print(f"加载配置失败，使用默认配置: {e}")
            self.config = self.default_config.copy()
            
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
            
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """合并配置，保留用户设置，补充默认值"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键如 'ocr.engine'
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
                    
            return value
            
        except Exception:
            return default
            
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        try:
            keys = key.split('.')
            config = self.config
            
            # 导航到目标位置
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
                
            # 设置值
            config[keys[-1]] = value
            
        except Exception as e:
            print(f"设置配置失败: {e}")
            
    def get_section(self, section: str) -> Dict:
        """
        获取配置段
        
        Args:
            section: 配置段名称
            
        Returns:
            配置段字典
        """
        return self.config.get(section, {})
        
    def update_section(self, section: str, values: Dict):
        """
        更新配置段
        
        Args:
            section: 配置段名称
            values: 新的配置值
        """
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section].update(values)
        
    def reset_to_default(self, section: Optional[str] = None):
        """
        重置为默认配置
        
        Args:
            section: 要重置的配置段，None表示重置全部
        """
        if section:
            if section in self.default_config:
                self.config[section] = self.default_config[section].copy()
        else:
            self.config = self.default_config.copy()
            
    def validate_config(self) -> bool:
        """
        验证配置有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必要的配置项
            required_sections = ['ocr', 'capture', 'typing', 'conversation']
            
            for section in required_sections:
                if section not in self.config:
                    return False
                    
            # 检查数值范围
            if not (0.1 <= self.get('capture.interval', 0) <= 10.0):
                return False
                
            if not (0.01 <= self.get('typing.delay_min', 0) <= 1.0):
                return False
                
            if not (0 <= self.get('ocr.confidence_threshold', 0) <= 100):
                return False
                
            return True
            
        except Exception:
            return False
            
    def export_config(self, filename: str):
        """
        导出配置到文件
        
        Args:
            filename: 导出文件名
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"导出配置失败: {e}")
            
    def import_config(self, filename: str):
        """
        从文件导入配置
        
        Args:
            filename: 配置文件名
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # 验证导入的配置
            temp_config = self.config
            self.config = self._merge_config(self.default_config, imported_config)
            
            if self.validate_config():
                self.save_config()
            else:
                self.config = temp_config
                raise ValueError("导入的配置无效")
                
        except Exception as e:
            print(f"导入配置失败: {e}")
            
    def get_config_info(self) -> Dict:
        """
        获取配置信息
        
        Returns:
            配置信息字典
        """
        return {
            'config_file': self.config_file,
            'config_exists': os.path.exists(self.config_file),
            'config_valid': self.validate_config(),
            'sections': list(self.config.keys()),
            'total_keys': self._count_keys(self.config)
        }
        
    def _count_keys(self, config: Dict) -> int:
        """递归计算配置键数量"""
        count = 0
        for value in config.values():
            if isinstance(value, dict):
                count += self._count_keys(value)
            else:
                count += 1
        return count
