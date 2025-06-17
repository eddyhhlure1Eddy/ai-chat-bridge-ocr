#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录模块
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

class Logger:
    """日志记录器"""
    
    def __init__(self, name: str = "AIChatBridge", config: Optional[dict] = None):
        self.name = name
        self.config = config or {}
        self.logger = None
        self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger(self.name)
        
        # 设置日志级别
        level = self.config.get('level', 'INFO')
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        if self.config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
        # 文件处理器
        log_file = self.config.get('file', 'logs/app.log')
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                
            # 创建轮转文件处理器
            max_bytes = self._parse_size(self.config.get('max_file_size', '10MB'))
            backup_count = self.config.get('backup_count', 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
    def _parse_size(self, size_str: str) -> int:
        """解析文件大小字符串"""
        try:
            size_str = size_str.upper()
            if size_str.endswith('KB'):
                return int(size_str[:-2]) * 1024
            elif size_str.endswith('MB'):
                return int(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith('GB'):
                return int(size_str[:-2]) * 1024 * 1024 * 1024
            else:
                return int(size_str)
        except:
            return 10 * 1024 * 1024  # 默认10MB
            
    def debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)
        
    def info(self, message: str, *args, **kwargs):
        """记录信息"""
        self.logger.info(message, *args, **kwargs)
        
    def warning(self, message: str, *args, **kwargs):
        """记录警告"""
        self.logger.warning(message, *args, **kwargs)
        
    def error(self, message: str, *args, **kwargs):
        """记录错误"""
        self.logger.error(message, *args, **kwargs)
        
    def critical(self, message: str, *args, **kwargs):
        """记录严重错误"""
        self.logger.critical(message, *args, **kwargs)
        
    def exception(self, message: str, *args, **kwargs):
        """记录异常信息"""
        self.logger.exception(message, *args, **kwargs)
        
    def log_system_info(self):
        """记录系统信息"""
        import platform
        import sys
        
        self.info("=" * 50)
        self.info("AI Chat Bridge OCR 启动")
        self.info(f"Python版本: {sys.version}")
        self.info(f"操作系统: {platform.system()} {platform.release()}")
        self.info(f"处理器: {platform.processor()}")
        self.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("=" * 50)
        
    def log_config_info(self, config_manager):
        """记录配置信息"""
        try:
            config_info = config_manager.get_config_info()
            self.info("配置信息:")
            self.info(f"  配置文件: {config_info['config_file']}")
            self.info(f"  配置有效: {config_info['config_valid']}")
            self.info(f"  配置段数: {len(config_info['sections'])}")
            self.info(f"  配置项数: {config_info['total_keys']}")
        except Exception as e:
            self.error(f"记录配置信息失败: {e}")
            
    def log_performance(self, operation: str, duration: float, **kwargs):
        """记录性能信息"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.info(f"性能: {operation} 耗时 {duration:.3f}s {extra_info}")
        
    def log_ocr_result(self, text: str, confidence: float = None, engine: str = None):
        """记录OCR结果"""
        text_preview = text[:50] + "..." if len(text) > 50 else text
        confidence_info = f" 置信度:{confidence:.1f}%" if confidence else ""
        engine_info = f" 引擎:{engine}" if engine else ""
        self.debug(f"OCR结果: '{text_preview}'{confidence_info}{engine_info}")
        
    def log_conversation_event(self, event_type: str, from_ai: str = None, to_ai: str = None, message: str = None):
        """记录对话事件"""
        if message:
            message_preview = message[:100] + "..." if len(message) > 100 else message
            self.info(f"对话事件: {event_type} {from_ai}→{to_ai} '{message_preview}'")
        else:
            self.info(f"对话事件: {event_type}")
            
    def log_error_with_context(self, error: Exception, context: dict = None):
        """记录带上下文的错误"""
        self.error(f"错误: {type(error).__name__}: {error}")
        if context:
            for key, value in context.items():
                self.error(f"  {key}: {value}")
                
    def set_level(self, level: str):
        """设置日志级别"""
        try:
            self.logger.setLevel(getattr(logging, level.upper()))
            self.info(f"日志级别已设置为: {level.upper()}")
        except AttributeError:
            self.error(f"无效的日志级别: {level}")
            
    def get_log_stats(self) -> dict:
        """获取日志统计信息"""
        stats = {
            'logger_name': self.name,
            'level': logging.getLevelName(self.logger.level),
            'handlers_count': len(self.logger.handlers),
            'handlers': []
        }
        
        for handler in self.logger.handlers:
            handler_info = {
                'type': type(handler).__name__,
                'level': logging.getLevelName(handler.level)
            }
            
            if hasattr(handler, 'baseFilename'):
                handler_info['file'] = handler.baseFilename
                if os.path.exists(handler.baseFilename):
                    handler_info['file_size'] = os.path.getsize(handler.baseFilename)
                    
            stats['handlers'].append(handler_info)
            
        return stats
