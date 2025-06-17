#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口GUI界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
from datetime import datetime
import json
from PIL import Image, ImageTk

from ..core.screen_capture import ScreenCapture
from ..core.ocr_processor import OCRProcessor
from ..core.region_selector import RegionSelector
from ..core.conversation_manager import ConversationManager
from ..core.auto_typer import AutoTyper
from .region_selector_window import RegionSelectorWindow

class MainWindow:
    """主窗口类"""
    
    def __init__(self, root, config, logger):
        self.root = root
        self.config = config
        self.logger = logger
        
        # 核心组件
        self.screen_capture = ScreenCapture(config, logger)
        self.ocr_processor = OCRProcessor(config, logger)
        self.region_selector = RegionSelector(logger)
        self.conversation_manager = ConversationManager(config, logger)
        self.auto_typer = AutoTyper(config, logger)
        
        # 状态变量
        self.is_running = False
        self.left_region = None
        self.right_region = None
        self.bridge_thread = None
        
        self.setup_ui()
        self.setup_bindings()
        
    def setup_ui(self):
        """设置用户界面"""
        self.root.title("AI Chat Bridge OCR - 非入侵性AI对话桥接器")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # 创建主框架
        self.create_main_frame()
        self.create_control_panel()
        self.create_conversation_display()
        self.create_status_bar()
        
    def create_main_frame(self):
        """创建主框架"""
        # 主容器
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建三列布局
        self.left_frame = ttk.LabelFrame(self.main_frame, text="左侧AI区域", padding="10")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.center_frame = ttk.LabelFrame(self.main_frame, text="对话监控", padding="10")
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        self.right_frame = ttk.LabelFrame(self.main_frame, text="右侧AI区域", padding="10")
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # 设置列权重
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=2)
        self.main_frame.columnconfigure(2, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
    def create_control_panel(self):
        """创建控制面板"""
        # 左侧控制
        self.create_region_controls(self.left_frame, "left")
        
        # 右侧控制
        self.create_region_controls(self.right_frame, "right")
        
        # 中央控制面板
        control_frame = ttk.Frame(self.center_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 开始/停止按钮
        self.start_button = ttk.Button(
            control_frame,
            text="🚀 开始桥接",
            command=self.start_bridge,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹️ 停止桥接",
            command=self.stop_bridge,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 强制停止按钮
        self.force_stop_button = ttk.Button(
            control_frame,
            text="🚨 强制停止",
            command=self.force_stop,
            state=tk.DISABLED
        )
        self.force_stop_button.pack(side=tk.LEFT, padx=5)
        
        # 清空对话按钮
        self.clear_button = ttk.Button(
            control_frame,
            text="🗑️ 清空对话",
            command=self.clear_conversation
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # 导出对话按钮
        self.export_button = ttk.Button(
            control_frame,
            text="💾 导出对话",
            command=self.export_conversation
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # 设置按钮
        self.settings_button = ttk.Button(
            control_frame,
            text="⚙️ 设置",
            command=self.open_settings
        )
        self.settings_button.pack(side=tk.RIGHT)
        
    def create_region_controls(self, parent, side):
        """创建区域控制组件"""
        # 选择区域按钮
        select_button = ttk.Button(
            parent,
            text=f"📍 选择{side}区域",
            command=lambda: self.select_region(side)
        )
        select_button.pack(fill=tk.X, pady=(0, 10))
        
        # 区域预览
        preview_frame = ttk.LabelFrame(parent, text="区域预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 预览画布
        canvas = tk.Canvas(preview_frame, height=150, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 保存画布引用
        if side == "left":
            self.left_canvas = canvas
        else:
            self.right_canvas = canvas
            
        # 区域信息标签
        info_label = ttk.Label(parent, text="未选择区域")
        info_label.pack(fill=tk.X)
        
        # 保存标签引用
        if side == "left":
            self.left_info_label = info_label
        else:
            self.right_info_label = info_label
            
        # 最新消息显示
        message_frame = ttk.LabelFrame(parent, text="最新消息")
        message_frame.pack(fill=tk.BOTH, expand=True)
        
        message_text = scrolledtext.ScrolledText(
            message_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        message_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 保存文本框引用
        if side == "left":
            self.left_message_text = message_text
        else:
            self.right_message_text = message_text
            
    def create_conversation_display(self):
        """创建对话显示区域"""
        # 对话历史
        self.conversation_text = scrolledtext.ScrolledText(
            self.center_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10)
        )
        self.conversation_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置文本标签样式
        self.conversation_text.tag_configure("timestamp", foreground="gray", font=("Consolas", 8))
        self.conversation_text.tag_configure("left_ai", foreground="blue", font=("Consolas", 10, "bold"))
        self.conversation_text.tag_configure("right_ai", foreground="red", font=("Consolas", 10, "bold"))
        self.conversation_text.tag_configure("system", foreground="green", font=("Consolas", 9, "italic"))
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 状态标签
        self.status_label = ttk.Label(
            self.status_frame,
            text="就绪 - 请选择左右两个聊天区域",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode='indeterminate',
            length=100
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        
    def setup_bindings(self):
        """设置事件绑定"""
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 键盘快捷键
        self.root.bind("<Control-s>", lambda e: self.start_bridge())
        self.root.bind("<Control-q>", lambda e: self.stop_bridge())
        self.root.bind("<Control-c>", lambda e: self.clear_conversation())
        self.root.bind("<Control-e>", lambda e: self.export_conversation())
        
    def select_region(self, side):
        """选择屏幕区域"""
        try:
            self.update_status(f"请选择{side}侧聊天区域...")
            
            # 最小化主窗口
            self.root.iconify()
            
            # 等待一下让窗口完全最小化
            self.root.after(500, lambda: self._do_region_selection(side))
            
        except Exception as e:
            self.logger.error(f"选择区域失败: {e}")
            messagebox.showerror("错误", f"选择区域失败:\n{e}")
            
    def _do_region_selection(self, side):
        """执行区域选择"""
        try:
            # 创建区域选择窗口
            selector_window = RegionSelectorWindow(self.root, self.logger)
            region = selector_window.select_region()
            
            if region:
                # 保存区域信息
                if side == "left":
                    self.left_region = region
                    self.update_region_info("left", region)
                else:
                    self.right_region = region
                    self.update_region_info("right", region)
                    
                self.update_status(f"{side}侧区域选择完成")
                self.logger.info(f"{side}侧区域选择: {region}")
                
                # 检查是否可以开始桥接
                self.check_ready_state()
            else:
                self.update_status(f"{side}侧区域选择取消")
                
        except Exception as e:
            self.logger.error(f"区域选择过程出错: {e}")
            messagebox.showerror("错误", f"区域选择失败:\n{e}")
        finally:
            # 恢复主窗口
            self.root.deiconify()
            self.root.lift()
            
    def update_region_info(self, side, region):
        """更新区域信息显示"""
        x, y, w, h = region
        info_text = f"区域: ({x}, {y}) - {w}x{h}"
        
        if side == "left":
            self.left_info_label.config(text=info_text)
            # 更新预览
            self.update_region_preview("left", region)
        else:
            self.right_info_label.config(text=info_text)
            # 更新预览
            self.update_region_preview("right", region)
            
    def update_region_preview(self, side, region):
        """更新区域预览"""
        try:
            # 截取区域图像
            screenshot = self.screen_capture.capture_region(region)
            if screenshot:
                # 缩放图像以适应预览区域
                canvas = self.left_canvas if side == "left" else self.right_canvas
                canvas.delete("all")

                # 等待画布更新尺寸
                canvas.update_idletasks()
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()

                if canvas_width > 1 and canvas_height > 1:
                    # 计算缩放比例
                    scale_x = canvas_width / screenshot.width
                    scale_y = canvas_height / screenshot.height
                    scale = min(scale_x, scale_y)

                    # 缩放图像
                    new_width = int(screenshot.width * scale)
                    new_height = int(screenshot.height * scale)
                    preview_image = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    # 转换为PhotoImage并显示
                    from PIL import ImageTk
                    photo = ImageTk.PhotoImage(preview_image)

                    # 居中显示
                    x_offset = (canvas_width - new_width) // 2
                    y_offset = (canvas_height - new_height) // 2

                    canvas.create_image(
                        x_offset, y_offset,
                        anchor=tk.NW,
                        image=photo
                    )

                    # 保存图像引用防止被垃圾回收
                    canvas.image = photo

                    # 添加区域信息标签
                    x, y, width, height = region
                    info_text = f"区域: ({x}, {y}) - {width}x{height}"
                    canvas.create_text(
                        canvas_width // 2, 10,
                        text=info_text,
                        fill="white",
                        font=("Arial", 8, "bold"),
                        anchor=tk.N
                    )

                    self.logger.debug(f"更新{side}侧区域预览成功: {region}")
                else:
                    # 画布尺寸无效，显示文字信息
                    self._show_text_preview(canvas, region)
            else:
                # 截图失败，显示错误信息
                canvas = self.left_canvas if side == "left" else self.right_canvas
                canvas.delete("all")
                canvas.create_text(
                    canvas.winfo_width() // 2,
                    canvas.winfo_height() // 2,
                    text="预览失败\n请重新选择",
                    fill="red",
                    font=("Arial", 10, "bold"),
                    anchor=tk.CENTER
                )
                self.logger.warning(f"{side}侧区域预览截图失败")

        except Exception as e:
            self.logger.error(f"更新区域预览失败: {e}")
            # 显示错误信息
            canvas = self.left_canvas if side == "left" else self.right_canvas
            canvas.delete("all")
            canvas.create_text(
                canvas.winfo_width() // 2,
                canvas.winfo_height() // 2,
                text="预览出错\n请重新选择",
                fill="orange",
                font=("Arial", 10, "bold"),
                anchor=tk.CENTER
            )

    def _show_text_preview(self, canvas, region):
        """显示文字预览（备用方案）"""
        canvas.delete("all")
        x, y, width, height = region
        canvas.create_text(
            canvas.winfo_width() // 2,
            canvas.winfo_height() // 2,
            text=f"已选择区域\n({x}, {y})\n{width} x {height}",
            fill="blue",
            font=("Arial", 12, "bold"),
            anchor=tk.CENTER
        )
            
    def check_ready_state(self):
        """检查是否准备就绪"""
        if self.left_region and self.right_region:
            self.start_button.config(state=tk.NORMAL)
            self.update_status("准备就绪 - 可以开始桥接")
        else:
            self.start_button.config(state=tk.DISABLED)
            
    def start_bridge(self):
        """开始桥接"""
        if not self.left_region or not self.right_region:
            messagebox.showwarning("警告", "请先选择左右两个聊天区域")
            return
            
        try:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.force_stop_button.config(state=tk.NORMAL)
            self.progress_bar.start()
            
            # 启动桥接线程
            self.bridge_thread = threading.Thread(target=self._bridge_loop, daemon=True)
            self.bridge_thread.start()
            
            self.update_status("桥接已启动")
            self.add_system_message("🚀 AI对话桥接已启动")
            
        except Exception as e:
            self.logger.error(f"启动桥接失败: {e}")
            messagebox.showerror("错误", f"启动桥接失败:\n{e}")
            self.stop_bridge()
            
    def stop_bridge(self):
        """停止桥接"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.force_stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()

        # 等待桥接线程结束
        if hasattr(self, 'bridge_thread') and self.bridge_thread and self.bridge_thread.is_alive():
            self.logger.info("等待桥接线程结束...")
            self.bridge_thread.join(timeout=2.0)
            if self.bridge_thread.is_alive():
                self.logger.warning("桥接线程未能正常结束")

        self.update_status("桥接已停止")
        self.add_system_message("⏹️ AI对话桥接已停止")

    def force_stop(self):
        """强制停止桥接"""
        self.logger.warning("执行强制停止")
        self.is_running = False

        # 强制终止线程
        if hasattr(self, 'bridge_thread') and self.bridge_thread and self.bridge_thread.is_alive():
            self.logger.warning("强制终止桥接线程")
            # 注意：Python没有直接终止线程的安全方法，这里只是设置标志

        # 重置UI状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.force_stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()

        self.update_status("桥接已强制停止")
        self.add_system_message("🚨 AI对话桥接已强制停止")

    def _bridge_loop(self):
        """桥接主循环 - 轮询对话模式"""
        current_speaker = "left"  # 当前发言方：left 或 right
        last_left_content = ""
        last_right_content = ""
        conversation_turn = 0
        max_turns = self.config.get('conversation.max_length', 50)

        self.add_system_message("🔄 开始轮询对话模式")

        while self.is_running and conversation_turn < max_turns:
            try:
                if current_speaker == "left":
                    # 等待左侧AI发言完成
                    new_message = self.wait_for_new_message("left", last_left_content)
                    if new_message:
                        last_left_content = new_message
                        self.update_message_display("left", new_message)

                        # 提取最新回复
                        latest_reply = self.extract_latest_reply(new_message)
                        if latest_reply:
                            self.add_conversation_message("left", "right", latest_reply)

                            # 转发给右侧
                            if self.forward_message_to_side("right", latest_reply):
                                current_speaker = "right"  # 切换到右侧
                                conversation_turn += 1
                                self.add_system_message(f"💬 第{conversation_turn}轮：左侧 → 右侧")
                            else:
                                self.add_system_message("❌ 转发到右侧失败")
                                break
                else:
                    # 等待右侧AI回复完成
                    new_message = self.wait_for_new_message("right", last_right_content)
                    if new_message:
                        last_right_content = new_message
                        self.update_message_display("right", new_message)

                        # 提取最新回复
                        latest_reply = self.extract_latest_reply(new_message)
                        if latest_reply:
                            self.add_conversation_message("right", "left", latest_reply)

                            # 转发给左侧
                            if self.forward_message_to_side("left", latest_reply):
                                current_speaker = "left"  # 切换到左侧
                                conversation_turn += 1
                                self.add_system_message(f"💬 第{conversation_turn}轮：右侧 → 左侧")
                            else:
                                self.add_system_message("❌ 转发到左侧失败")
                                break

                # 检查是否应该停止
                if conversation_turn >= max_turns:
                    self.add_system_message(f"🏁 达到最大轮数({max_turns})，对话结束")
                    break

            except Exception as e:
                self.logger.error(f"桥接循环出错: {e}")
                self.add_system_message(f"❌ 桥接出错: {e}")
                if self.is_running:
                    self.root.after(0, lambda: messagebox.showerror("桥接错误", f"桥接过程出错:\n{e}"))
                break

        self.add_system_message("🔚 对话桥接结束")
        self.root.after(0, self.stop_bridge)
                
    def wait_for_new_message(self, side, last_content, timeout=60):
        """等待指定侧有新消息"""
        region = self.left_region if side == "left" else self.right_region
        start_time = time.time()
        check_interval = 3.0  # 每3秒检查一次

        while self.is_running and (time.time() - start_time) < timeout:
            try:
                # 截取区域
                screenshot = self.screen_capture.capture_region(region)
                if screenshot:
                    # 使用EasyOCR识别
                    current_content = self.ocr_processor.extract_text(screenshot)

                    if current_content and current_content != last_content:
                        # 检查是否真的有新内容
                        if self.has_meaningful_change(last_content, current_content):
                            self.logger.info(f"{side}侧检测到新消息")
                            return current_content

                # 等待间隔
                time.sleep(check_interval)

            except Exception as e:
                self.logger.error(f"等待{side}侧消息时出错: {e}")

        self.logger.warning(f"{side}侧在{timeout}秒内没有新消息")
        return None

    def has_meaningful_change(self, old_content, new_content):
        """检查是否有有意义的内容变化"""
        if not old_content:
            return bool(new_content and len(new_content.strip()) > 10)

        # 计算内容差异
        old_lines = set(old_content.split('\n'))
        new_lines = set(new_content.split('\n'))

        # 检查是否有新的行
        new_additions = new_lines - old_lines
        meaningful_additions = [line for line in new_additions if len(line.strip()) > 5]

        return len(meaningful_additions) > 0

    def extract_latest_reply(self, content):
        """从内容中提取最新的回复"""
        if not content:
            return None

        # 按行分割内容
        lines = [line.strip() for line in content.split('\n') if line.strip()]

        if not lines:
            return None

        # 过滤掉界面元素和无关内容
        filtered_lines = []

        # 定义需要过滤的关键词（界面元素、按钮、时间戳等）
        filter_keywords = [
            # 时间相关
            'time', '时间', '刚刚', 'just now', 'ago', '前', 'seconds', 'minutes', 'hours',
            '秒', '分钟', '小时', '天', 'days',

            # 系统和界面元素
            'system', '系统', 'reply', '回复', 'send', '发送', 'submit', '提交',
            'button', '按钮', 'click', '点击', 'menu', '菜单', 'settings', '设置',
            'tools', '工具', 'search', '搜索', 'claude', 'gpt', 'ai',

            # 状态和提示
            'typing', '正在输入', 'loading', '加载', 'thinking', '思考',
            'preferences', '偏好', 'user', '用户', 'chat', '聊天',

            # 特殊字符和符号
            '•', '○', '●', '◦', '▪', '▫', '■', '□', '▲', '△', '▼', '▽',
            '→', '←', '↑', '↓', '⏰', '🕐', '⌚', '📱', '💬', '🔄',

            # 常见界面文本
            'retry', '重试', 'cancel', '取消', 'confirm', '确认',
            'copy', '复制', 'paste', '粘贴', 'edit', '编辑',
            'delete', '删除', 'save', '保存', 'export', '导出'
        ]

        for line in lines:
            line_lower = line.lower()

            # 跳过包含过滤关键词的行
            if any(keyword in line_lower for keyword in filter_keywords):
                continue

            # 跳过太短的行
            if len(line) < 8:
                continue

            # 跳过只包含数字、符号或单个词的行
            if line.isdigit() or len(line.split()) < 3:
                continue

            # 跳过看起来像时间戳的行 (如: 13:37, 2024-06-17等)
            if any(char in line for char in [':', '-']) and len(line) < 20:
                continue

            # 跳过看起来像按钮或链接的行
            if line.startswith(('http', 'www', '@', '#')) or line.endswith(('...', '→', '←')):
                continue

            filtered_lines.append(line)

        if not filtered_lines:
            return None

        # 返回最长的几行作为最新回复（通常是实际对话内容）
        # 按长度排序，取最长的几行
        filtered_lines.sort(key=len, reverse=True)

        if len(filtered_lines) >= 2:
            # 取最长的2行，按原顺序重新排列
            selected_lines = filtered_lines[:2]
            # 恢复原始顺序
            original_order_lines = []
            for line in lines:
                if line in selected_lines:
                    original_order_lines.append(line)
            return '\n'.join(original_order_lines)
        else:
            return filtered_lines[0] if filtered_lines else None

    def forward_message_to_side(self, target_side, message):
        """转发消息到指定侧"""
        try:
            target_region = self.right_region if target_side == "right" else self.left_region

            self.logger.info(f"转发消息到{target_side}侧: {message[:50]}...")

            # 使用自动输入器发送消息
            success = self.auto_typer.type_message(target_region, message)

            if success:
                self.logger.info(f"消息成功转发到{target_side}侧")
                # 等待一下让消息发送完成
                time.sleep(2)
                return True
            else:
                self.logger.error(f"转发到{target_side}侧失败")
                return False

        except Exception as e:
            self.logger.error(f"转发消息到{target_side}侧失败: {e}")
            return False
            
    def update_message_display(self, side, content):
        """更新消息显示"""
        text_widget = self.left_message_text if side == "left" else self.right_message_text
        
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
        
    def add_conversation_message(self, from_side, to_side, message):
        """添加对话消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        from_label = "左侧AI" if from_side == "left" else "右侧AI"
        to_label = "右侧AI" if to_side == "right" else "左侧AI"
        
        self.conversation_text.config(state=tk.NORMAL)
        
        # 添加时间戳
        self.conversation_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # 添加发送者
        tag = "left_ai" if from_side == "left" else "right_ai"
        self.conversation_text.insert(tk.END, f"{from_label} → {to_label}:\n", tag)
        
        # 添加消息内容
        self.conversation_text.insert(tk.END, f"{message}\n\n")
        
        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(tk.END)
        
    def add_system_message(self, message):
        """添加系统消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.conversation_text.insert(tk.END, f"{message}\n", "system")
        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(tk.END)
        
    def clear_conversation(self):
        """清空对话"""
        if messagebox.askyesno("确认", "确定要清空对话记录吗？"):
            self.conversation_text.config(state=tk.NORMAL)
            self.conversation_text.delete(1.0, tk.END)
            self.conversation_text.config(state=tk.DISABLED)
            self.add_system_message("🗑️ 对话记录已清空")
            
    def export_conversation(self):
        """导出对话"""
        try:
            content = self.conversation_text.get(1.0, tk.END)
            if not content.strip():
                messagebox.showinfo("提示", "没有对话内容可导出")
                return
                
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("JSON文件", "*.json"),
                    ("所有文件", "*.*")
                ]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"对话已导出到:\n{filename}")
                
        except Exception as e:
            self.logger.error(f"导出对话失败: {e}")
            messagebox.showerror("错误", f"导出对话失败:\n{e}")
            
    def open_settings(self):
        """打开设置窗口"""
        # TODO: 实现设置窗口
        messagebox.showinfo("提示", "设置功能正在开发中...")
        
    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)
        self.logger.info(f"状态: {message}")
        
    def stop_all_tasks(self):
        """停止所有任务"""
        self.is_running = False
        if self.bridge_thread and self.bridge_thread.is_alive():
            self.bridge_thread.join(timeout=1.0)
            
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            if messagebox.askyesno("确认退出", "桥接正在运行，确定要退出吗？"):
                self.stop_all_tasks()
                self.root.destroy()
        else:
            self.root.destroy()
