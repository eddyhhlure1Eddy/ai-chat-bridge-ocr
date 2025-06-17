#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域选择窗口模块
"""

import tkinter as tk
from tkinter import messagebox
import pyautogui
from PIL import Image, ImageTk

class RegionSelectorWindow:
    """区域选择窗口"""
    
    def __init__(self, parent, logger):
        self.parent = parent
        self.logger = logger
        self.selected_region = None
        
    def select_region(self):
        """选择区域"""
        try:
            # 获取屏幕截图
            screenshot = pyautogui.screenshot()
            
            # 创建全屏选择窗口
            self.root = tk.Toplevel(self.parent)
            self.root.title("选择区域 - 拖拽鼠标框选区域")
            self.root.attributes('-fullscreen', True)
            self.root.attributes('-topmost', True)
            self.root.configure(cursor='crosshair', bg='black')
            
            # 创建画布
            self.canvas = tk.Canvas(
                self.root, 
                highlightthickness=0,
                bg='black'
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            # 显示截图
            self.display_screenshot(screenshot)
            
            # 绑定事件
            self.setup_events()
            
            # 选择状态
            self.start_x = None
            self.start_y = None
            self.rect_id = None
            self.info_text_id = None
            
            # 添加说明
            self.add_instructions()
            
            # 等待用户选择
            self.root.wait_window()
            
            return self.selected_region
            
        except Exception as e:
            self.logger.error(f"区域选择失败: {e}")
            return None
            
    def display_screenshot(self, screenshot):
        """显示截图"""
        try:
            # 获取屏幕尺寸
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # 调整截图大小
            if screenshot.size != (screen_width, screen_height):
                screenshot = screenshot.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                
            # 转换为PhotoImage
            self.photo = ImageTk.PhotoImage(screenshot)
            
            # 在画布上显示
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
        except Exception as e:
            self.logger.error(f"显示截图失败: {e}")
            
    def setup_events(self):
        """设置事件绑定"""
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.root.bind('<Escape>', self.on_cancel)
        self.root.bind('<Return>', self.on_confirm)
        self.root.bind('<space>', self.on_confirm)
        
    def add_instructions(self):
        """添加操作说明"""
        instructions = [
            "🖱️ 拖拽鼠标选择聊天区域",
            "⌨️ 按 Enter 或 空格 确认选择", 
            "⌨️ 按 Esc 取消选择",
            "💡 提示：选择区域应包含聊天内容和输入框"
        ]
        
        # 创建半透明背景
        bg_width = 400
        bg_height = len(instructions) * 25 + 20
        
        self.canvas.create_rectangle(
            20, 20, 20 + bg_width, 20 + bg_height,
            fill='black', stipple='gray50', outline='yellow', width=2
        )
        
        # 添加说明文字
        y_offset = 35
        for instruction in instructions:
            self.canvas.create_text(
                30, y_offset,
                text=instruction,
                fill='yellow',
                font=('Arial', 12, 'bold'),
                anchor=tk.W
            )
            y_offset += 25
            
    def on_mouse_down(self, event):
        """鼠标按下事件"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 删除之前的选择框
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            
        # 删除之前的信息文字
        if self.info_text_id:
            self.canvas.delete(self.info_text_id)
            
    def on_mouse_drag(self, event):
        """鼠标拖拽事件"""
        if self.start_x is not None and self.start_y is not None:
            # 删除之前的选择框
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                
            # 绘制新的选择框
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=3, fill='', stipple='gray25'
            )
            
            # 显示尺寸信息
            self.show_size_info(event.x, event.y)
            
    def on_mouse_up(self, event):
        """鼠标释放事件"""
        if self.start_x is not None and self.start_y is not None:
            # 计算选择区域
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            
            # 确保坐标正确（左上角到右下角）
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # 检查区域大小
            if width > 50 and height > 50:
                self.selected_region = (x, y, width, height)
                self.show_confirmation()
            else:
                self.show_error("选择区域太小，请重新选择（最小50x50像素）")
                
    def show_size_info(self, x, y):
        """显示尺寸信息"""
        if self.start_x is not None and self.start_y is not None:
            width = abs(x - self.start_x)
            height = abs(y - self.start_y)
            
            info_text = f"区域大小: {width} x {height} 像素"
            
            # 计算文字位置（避免超出屏幕）
            text_x = min(x + 10, self.canvas.winfo_width() - 200)
            text_y = max(y - 20, 20)
            
            # 删除之前的信息
            if self.info_text_id:
                self.canvas.delete(self.info_text_id)
                
            # 显示新信息
            self.info_text_id = self.canvas.create_text(
                text_x, text_y,
                text=info_text,
                fill='lime',
                font=('Arial', 12, 'bold'),
                anchor=tk.W
            )
            
    def show_confirmation(self):
        """显示确认信息"""
        if self.selected_region:
            x, y, w, h = self.selected_region
            
            # 删除之前的信息
            if self.info_text_id:
                self.canvas.delete(self.info_text_id)
                
            # 显示确认信息
            confirm_text = f"✅ 已选择区域: ({x}, {y}) 大小: {w}x{h}\n按 Enter/空格 确认，按 Esc 取消"
            
            self.info_text_id = self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() - 80,
                text=confirm_text,
                fill='lime',
                font=('Arial', 16, 'bold'),
                anchor=tk.CENTER,
                justify=tk.CENTER
            )
            
            # 高亮选择框
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                
            self.rect_id = self.canvas.create_rectangle(
                x, y, x + w, y + h,
                outline='lime', width=4, fill='', stipple='gray25'
            )
            
    def show_error(self, message):
        """显示错误信息"""
        # 删除之前的信息
        if self.info_text_id:
            self.canvas.delete(self.info_text_id)
            
        self.info_text_id = self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            text=f"❌ {message}",
            fill='red',
            font=('Arial', 16, 'bold'),
            anchor=tk.CENTER
        )
        
        # 重置选择状态
        self.start_x = None
        self.start_y = None
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            
    def on_confirm(self, event):
        """确认选择"""
        if self.selected_region:
            self.root.destroy()
        else:
            self.show_error("请先选择一个区域")
            
    def on_cancel(self, event):
        """取消选择"""
        self.selected_region = None
        self.root.destroy()
