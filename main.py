#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chat Bridge OCR - 主程序入口
基于OCR的非入侵性AI对话桥接器
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.gui.main_window import MainWindow
    from src.core.config_manager import ConfigManager
    from src.core.logger import Logger
    from src.utils.system_check import SystemChecker
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有文件都在正确的位置")
    sys.exit(1)

class AIChatBridgeApp:
    """AI聊天桥接器主应用程序"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.logger = Logger()
        self.system_checker = SystemChecker()
        self.main_window = None
        
    def check_system_requirements(self):
        """检查系统环境和依赖"""
        self.logger.info("正在检查系统环境...")
        
        # 检查Python版本
        if not self.system_checker.check_python_version():
            messagebox.showerror("系统检查", "需要Python 3.8或更高版本")
            return False
            
        # 检查必要的库
        missing_packages = self.system_checker.check_required_packages()
        if missing_packages:
            msg = f"缺少必要的Python包:\n{', '.join(missing_packages)}\n\n请运行: pip install -r requirements.txt"
            messagebox.showerror("依赖检查", msg)
            return False
            
        # 检查OCR引擎
        if not self.system_checker.check_ocr_engines():
            msg = ("未找到OCR引擎!\n\n"
                   "请安装Tesseract OCR:\n"
                   "Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                   "macOS: brew install tesseract\n"
                   "Linux: sudo apt-get install tesseract-ocr")
            messagebox.showerror("OCR检查", msg)
            return False
            
        self.logger.info("系统环境检查通过")
        return True
        
    def initialize_config(self):
        """初始化配置"""
        try:
            self.config.load_config()
            self.logger.info("配置加载成功")
            return True
        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            messagebox.showerror("配置错误", f"配置文件加载失败:\n{e}")
            return False
            
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            'data',
            'logs', 
            'screenshots',
            'exports'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
        self.logger.info("目录结构创建完成")
        
    def run(self):
        """运行主程序"""
        try:
            # 系统检查
            if not self.check_system_requirements():
                return
                
            # 初始化配置
            if not self.initialize_config():
                return
                
            # 创建目录
            self.create_directories()
            
            # 创建主窗口
            root = tk.Tk()
            self.main_window = MainWindow(root, self.config, self.logger)
            
            # 设置窗口关闭事件
            root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            self.logger.info("AI Chat Bridge OCR 启动成功")
            
            # 启动GUI主循环
            root.mainloop()
            
        except Exception as e:
            self.logger.error(f"程序启动失败: {e}")
            messagebox.showerror("启动错误", f"程序启动失败:\n{e}")
            
    def on_closing(self):
        """程序关闭时的清理工作"""
        try:
            if self.main_window:
                # 停止所有正在运行的任务
                self.main_window.stop_all_tasks()
                
            self.logger.info("AI Chat Bridge OCR 正常退出")
            
            # 销毁窗口
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.root.destroy()
                
        except Exception as e:
            self.logger.error(f"程序退出时发生错误: {e}")
            
def show_splash_screen():
    """显示启动画面"""
    splash = tk.Tk()
    splash.title("AI Chat Bridge OCR")
    splash.geometry("400x300")
    splash.resizable(False, False)
    
    # 居中显示
    splash.eval('tk::PlaceWindow . center')
    
    # 创建启动画面内容
    frame = ttk.Frame(splash, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(
        frame, 
        text="🤖 AI Chat Bridge OCR", 
        font=("Arial", 16, "bold")
    )
    title_label.pack(pady=10)
    
    # 副标题
    subtitle_label = ttk.Label(
        frame,
        text="非入侵性AI对话桥接器",
        font=("Arial", 10)
    )
    subtitle_label.pack(pady=5)
    
    # 版本信息
    version_label = ttk.Label(
        frame,
        text="Version 1.0.0",
        font=("Arial", 8)
    )
    version_label.pack(pady=5)
    
    # 进度条
    progress = ttk.Progressbar(
        frame,
        mode='indeterminate',
        length=300
    )
    progress.pack(pady=20)
    progress.start()
    
    # 状态文本
    status_label = ttk.Label(
        frame,
        text="正在初始化...",
        font=("Arial", 9)
    )
    status_label.pack(pady=5)
    
    # 版权信息
    copyright_label = ttk.Label(
        frame,
        text="© 2024 AI Chat Bridge OCR",
        font=("Arial", 8),
        foreground="gray"
    )
    copyright_label.pack(side=tk.BOTTOM, pady=10)
    
    # 自动关闭启动画面
    def close_splash():
        progress.stop()
        splash.destroy()
        
    splash.after(3000, close_splash)  # 3秒后关闭
    splash.mainloop()

def main():
    """主函数"""
    try:
        # 显示启动画面
        show_splash_screen()
        
        # 创建并运行主应用
        app = AIChatBridgeApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        messagebox.showerror("错误", f"程序运行出错:\n{e}")

if __name__ == "__main__":
    main()
