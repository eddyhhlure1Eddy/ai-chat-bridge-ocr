#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域选择模块
"""

import tkinter as tk
from tkinter import messagebox
import pyautogui
from PIL import Image, ImageTk

class RegionSelector:
    """区域选择器"""
    
    def __init__(self, logger):
        self.logger = logger
        self.selected_region = None
        
    def select_region(self):
        """选择屏幕区域"""
        try:
            # 获取屏幕截图
            screenshot = pyautogui.screenshot()
            
            # 创建选择窗口
            selector_window = RegionSelectorWindow(screenshot, self.logger)
            region = selector_window.get_selected_region()
            
            if region:
                self.selected_region = region
                self.logger.info(f"区域选择完成: {region}")
                
            return region
            
        except Exception as e:
            self.logger.error(f"区域选择失败: {e}")
            return None

class RegionSelectorWindow:
    """区域选择窗口"""
    
    def __init__(self, screenshot, logger):
        self.screenshot = screenshot
        self.logger = logger
        self.selected_region = None

        try:
            self.root = tk.Toplevel()
            self.root.title("选择区域 - 拖拽选择，Enter确认，Esc取消")

            # 设置窗口属性
            self.root.attributes('-fullscreen', True)
            self.root.attributes('-topmost', True)
            self.root.configure(cursor='crosshair', bg='black')

            # 设置透明度（可选）
            # self.root.attributes('-alpha', 0.9)

            # 创建画布
            self.canvas = tk.Canvas(
                self.root,
                highlightthickness=0,
                bg='black',
                cursor='crosshair'
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)

            # 绑定事件
            self.canvas.bind('<Button-1>', self.on_click)
            self.canvas.bind('<B1-Motion>', self.on_drag)
            self.canvas.bind('<ButtonRelease-1>', self.on_release)
            self.root.bind('<Escape>', self.on_cancel)
            self.root.bind('<Return>', self.on_confirm)
            self.root.bind('<Key>', self.on_key)  # 添加键盘事件

            # 确保窗口获得焦点
            self.root.focus_set()

            # 选择状态
            self.start_x = None
            self.start_y = None
            self.rect_id = None

            # 显示截图
            self.display_screenshot()

            # 添加说明文字
            self.add_instructions()

            self.logger.info("区域选择窗口初始化成功")

        except Exception as e:
            self.logger.error(f"区域选择窗口初始化失败: {e}")
            raise
        
    def display_screenshot(self):
        """显示截图"""
        try:
            # 获取屏幕尺寸
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            # 检查截图是否有效
            if not self.screenshot:
                self.logger.error("截图为空，创建黑色背景")
                from PIL import Image
                self.screenshot = Image.new('RGB', (screen_width, screen_height), color='black')

            # 缩放截图以适应屏幕
            screenshot_resized = self.screenshot.resize((screen_width, screen_height), Image.Resampling.LANCZOS)

            # 检查图像亮度，如果太暗则增强
            import numpy as np
            img_array = np.array(screenshot_resized)
            avg_brightness = np.mean(img_array)

            if avg_brightness < 50:
                self.logger.warning(f"截图较暗 (亮度: {avg_brightness:.1f})，进行增强")
                from PIL import ImageEnhance

                # 增强亮度
                enhancer = ImageEnhance.Brightness(screenshot_resized)
                screenshot_resized = enhancer.enhance(1.5)

                # 增强对比度
                enhancer = ImageEnhance.Contrast(screenshot_resized)
                screenshot_resized = enhancer.enhance(1.3)

            # 转换为PhotoImage
            from PIL import ImageTk
            self.photo = ImageTk.PhotoImage(screenshot_resized)

            # 在画布上显示截图
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            self.logger.info(f"截图显示成功，尺寸: {screenshot_resized.size}")

        except Exception as e:
            self.logger.error(f"显示截图失败: {e}")
            # 创建一个带提示的背景
            self.canvas.configure(bg='gray20')
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="截图显示失败\n请按 Esc 取消",
                fill='white',
                font=('Arial', 20, 'bold'),
                anchor=tk.CENTER
            )
            
    def add_instructions(self):
        """添加操作说明"""
        try:
            # 主要说明
            instructions = [
                "🖱️ 拖拽鼠标选择聊天区域",
                "⌨️ 按 Enter 确认选择",
                "⌨️ 按 Esc 取消选择",
                "💡 选择区域要包含聊天内容和输入框"
            ]

            # 创建半透明背景
            bg_width = 400
            bg_height = len(instructions) * 35 + 20
            self.canvas.create_rectangle(
                30, 30, 30 + bg_width, 30 + bg_height,
                fill='black', outline='yellow', width=2,
                stipple='gray50'
            )

            y_offset = 50
            for instruction in instructions:
                self.canvas.create_text(
                    50, y_offset,
                    text=instruction,
                    fill='yellow',
                    font=('Arial', 12, 'bold'),
                    anchor=tk.W
                )
                y_offset += 35

            # 右下角状态提示
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            self.canvas.create_text(
                screen_width - 50, screen_height - 50,
                text="AI Chat Bridge OCR - 区域选择",
                fill='cyan',
                font=('Arial', 10),
                anchor=tk.SE
            )

        except Exception as e:
            self.logger.error(f"添加说明文字失败: {e}")

    def on_key(self, event):
        """键盘事件处理"""
        if event.keysym == 'Escape':
            self.on_cancel(event)
        elif event.keysym == 'Return':
            self.on_confirm(event)
            
    def on_click(self, event):
        """鼠标点击事件"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 删除之前的选择框
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            
    def on_drag(self, event):
        """鼠标拖拽事件"""
        if self.start_x is not None and self.start_y is not None:
            # 删除之前的选择框
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                
            # 绘制新的选择框
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=2, fill='', stipple='gray50'
            )
            
            # 显示坐标信息
            self.show_coordinates(event.x, event.y)
            
    def on_release(self, event):
        """鼠标释放事件"""
        if self.start_x is not None and self.start_y is not None:
            # 计算选择区域
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            
            # 确保坐标正确
            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # 检查区域大小
            if width > 10 and height > 10:
                self.selected_region = (x, y, width, height)
                self.show_selection_info()
            else:
                messagebox.showwarning("选择无效", "选择区域太小，请重新选择")
                
    def show_coordinates(self, x, y):
        """显示坐标信息"""
        if hasattr(self, 'coord_text'):
            self.canvas.delete(self.coord_text)
            
        coord_info = f"坐标: ({x}, {y})"
        if self.start_x is not None:
            width = abs(x - self.start_x)
            height = abs(y - self.start_y)
            coord_info += f" 大小: {width}x{height}"
            
        self.coord_text = self.canvas.create_text(
            x + 10, y - 10,
            text=coord_info,
            fill='yellow',
            font=('Arial', 10, 'bold'),
            anchor=tk.W
        )
        
    def show_selection_info(self):
        """显示选择信息"""
        if self.selected_region:
            x, y, w, h = self.selected_region
            info = f"已选择区域: ({x}, {y}) 大小: {w}x{h}\n按 Enter 确认，按 Esc 取消"
            
            # 删除之前的信息
            if hasattr(self, 'info_text'):
                self.canvas.delete(self.info_text)
                
            self.info_text = self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() - 50,
                text=info,
                fill='lime',
                font=('Arial', 16, 'bold'),
                anchor=tk.CENTER
            )
            
    def on_confirm(self, event):
        """确认选择"""
        if self.selected_region:
            self.root.destroy()
        else:
            messagebox.showwarning("未选择", "请先选择一个区域")
            
    def on_cancel(self, event):
        """取消选择"""
        self.selected_region = None
        self.root.destroy()
        
    def get_selected_region(self):
        """获取选择的区域"""
        self.root.wait_window()
        return self.selected_region
