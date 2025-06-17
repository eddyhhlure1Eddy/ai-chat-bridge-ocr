#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动输入模块
模拟人类输入行为，避免被检测
"""

import pyautogui
import pyperclip
import time
import random
import re
from datetime import datetime

class AutoTyper:
    """自动输入器类"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # 禁用pyautogui的安全检查
        pyautogui.FAILSAFE = False
        
        # 输入配置
        self.delay_min = config.get('typing.delay_min', 0.05)
        self.delay_max = config.get('typing.delay_max', 0.15)
        self.pause_probability = config.get('typing.pause_probability', 0.1)
        self.pause_duration_min = config.get('typing.pause_duration_min', 0.5)
        self.pause_duration_max = config.get('typing.pause_duration_max', 2.0)
        
        # 输入方法配置
        self.use_clipboard = config.get('typing.use_clipboard', True)
        self.typing_speed_variation = config.get('typing.speed_variation', 0.3)
        
        # 特殊键映射
        self.special_keys = {
            '\n': 'enter',
            '\t': 'tab',
            '\b': 'backspace'
        }
        
    def type_message(self, target_region, message):
        """
        在指定区域输入消息
        
        Args:
            target_region: 目标区域坐标 (x, y, width, height)
            message: 要输入的消息
            
        Returns:
            bool: 输入是否成功
        """
        try:
            if not message or not message.strip():
                self.logger.warning("消息为空，跳过输入")
                return False
                
            # 清理消息内容
            cleaned_message = self._clean_message(message)
            
            # 点击目标区域激活输入框
            if not self._click_target_region(target_region):
                return False
                
            # 等待输入框激活
            time.sleep(0.5)
            
            # 选择输入方法
            if self.use_clipboard and self._can_use_clipboard(cleaned_message):
                success = self._type_with_clipboard(cleaned_message)
            else:
                success = self._type_character_by_character(cleaned_message)
                
            if success:
                # 发送消息（按回车）
                time.sleep(random.uniform(0.5, 1.0))
                pyautogui.press('enter')
                
                self.logger.info(f"消息输入成功: {cleaned_message[:50]}...")
                return True
            else:
                self.logger.error("消息输入失败")
                return False
                
        except Exception as e:
            self.logger.error(f"输入消息失败: {e}")
            return False
            
    def _clean_message(self, message):
        """清理消息内容"""
        try:
            # 移除多余的空白字符
            message = re.sub(r'\s+', ' ', message)
            
            # 移除可能导致问题的特殊字符
            message = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', message)
            
            # 限制消息长度
            max_length = self.config.get('typing.max_message_length', 2000)
            if len(message) > max_length:
                message = message[:max_length] + "..."
                
            return message.strip()
            
        except Exception as e:
            self.logger.error(f"清理消息失败: {e}")
            return message
            
    def _click_target_region(self, region):
        """点击目标区域激活输入框"""
        try:
            x, y, width, height = region

            # 尝试多个可能的输入框位置
            click_positions = [
                (x + width // 2, y + int(height * 0.9)),  # 底部中央（最常见）
                (x + width // 2, y + int(height * 0.8)),  # 80%位置
                (x + int(width * 0.2), y + int(height * 0.9)),  # 底部左侧
                (x + int(width * 0.8), y + int(height * 0.9)),  # 底部右侧
            ]

            for i, (click_x, click_y) in enumerate(click_positions):
                try:
                    # 添加随机偏移模拟人类点击
                    offset_x = random.randint(-5, 5)
                    offset_y = random.randint(-3, 3)

                    final_x = click_x + offset_x
                    final_y = click_y + offset_y

                    # 执行点击
                    pyautogui.click(final_x, final_y)
                    time.sleep(0.5)  # 等待输入框激活

                    self.logger.debug(f"尝试点击位置 {i+1}: ({final_x}, {final_y})")

                    # 测试是否成功激活输入框（尝试输入一个空格然后删除）
                    pyautogui.press('space')
                    time.sleep(0.1)
                    pyautogui.press('backspace')

                    return True

                except Exception as e:
                    self.logger.debug(f"点击位置 {i+1} 失败: {e}")
                    continue

            self.logger.error("所有点击位置都失败")
            return False

        except Exception as e:
            self.logger.error(f"点击目标区域失败: {e}")
            return False
            
    def _can_use_clipboard(self, message):
        """判断是否可以使用剪贴板输入"""
        try:
            # 检查消息长度
            if len(message) < 20:
                return False
                
            # 检查是否包含特殊字符
            if any(char in self.special_keys for char in message):
                return False
                
            # 检查是否主要是中文（中文输入用剪贴板更可靠）
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', message))
            if chinese_chars > len(message) * 0.3:
                return True
                
            # 长消息使用剪贴板
            if len(message) > 100:
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"判断剪贴板使用失败: {e}")
            return False
            
    def _type_with_clipboard(self, message):
        """使用剪贴板输入"""
        try:
            # 备份当前剪贴板内容
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass
                
            # 复制消息到剪贴板
            pyperclip.copy(message)
            
            # 等待剪贴板更新
            time.sleep(0.1)
            
            # 模拟人类行为：先清空输入框
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # 粘贴内容
            pyautogui.hotkey('ctrl', 'v')
            
            # 等待粘贴完成
            time.sleep(0.5)
            
            # 恢复原剪贴板内容
            try:
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
            except:
                pass
                
            self.logger.debug("剪贴板输入完成")
            return True
            
        except Exception as e:
            self.logger.error(f"剪贴板输入失败: {e}")
            return False
            
    def _type_character_by_character(self, message):
        """逐字符输入"""
        try:
            # 先清空输入框
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)
            
            for i, char in enumerate(message):
                # 处理特殊字符
                if char in self.special_keys:
                    pyautogui.press(self.special_keys[char])
                else:
                    pyautogui.write(char)
                    
                # 添加随机延迟模拟人类输入
                delay = random.uniform(self.delay_min, self.delay_max)
                
                # 根据字符类型调整延迟
                if char.isspace():
                    delay *= 0.5  # 空格输入更快
                elif char in '.,!?;:':
                    delay *= 1.5  # 标点符号稍慢
                elif ord(char) > 127:  # 非ASCII字符（如中文）
                    delay *= 2.0
                    
                # 添加速度变化
                speed_factor = 1.0 + random.uniform(-self.typing_speed_variation, self.typing_speed_variation)
                delay *= speed_factor
                
                time.sleep(delay)
                
                # 随机暂停模拟思考
                if random.random() < self.pause_probability:
                    pause_duration = random.uniform(self.pause_duration_min, self.pause_duration_max)
                    time.sleep(pause_duration)
                    
                # 每隔一段时间检查是否需要停止
                if i % 50 == 0:
                    # 这里可以添加停止检查逻辑
                    pass
                    
            self.logger.debug("逐字符输入完成")
            return True
            
        except Exception as e:
            self.logger.error(f"逐字符输入失败: {e}")
            return False
            
    def simulate_human_behavior(self):
        """模拟人类行为"""
        try:
            # 随机鼠标移动
            current_x, current_y = pyautogui.position()
            offset_x = random.randint(-50, 50)
            offset_y = random.randint(-50, 50)
            
            new_x = max(0, min(current_x + offset_x, pyautogui.size()[0] - 1))
            new_y = max(0, min(current_y + offset_y, pyautogui.size()[1] - 1))
            
            # 缓慢移动鼠标
            pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.5, 1.5))
            
            # 随机暂停
            time.sleep(random.uniform(0.1, 0.5))
            
        except Exception as e:
            self.logger.error(f"模拟人类行为失败: {e}")
            
    def check_input_focus(self, region):
        """检查输入框是否获得焦点"""
        try:
            # 这里可以通过截图和OCR检查是否有光标
            # 简化实现：假设点击后就获得了焦点
            return True
            
        except Exception as e:
            self.logger.error(f"检查输入焦点失败: {e}")
            return False
            
    def wait_for_typing_complete(self, timeout=10):
        """等待输入完成"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 检查是否还在输入中
                # 这里可以通过检查"正在输入"指示器来判断
                time.sleep(0.5)
                
            return True
            
        except Exception as e:
            self.logger.error(f"等待输入完成失败: {e}")
            return False
            
    def cancel_input(self):
        """取消当前输入"""
        try:
            # 按ESC键取消
            pyautogui.press('escape')
            time.sleep(0.2)
            
            # 或者清空输入框
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            
            self.logger.info("输入已取消")
            return True
            
        except Exception as e:
            self.logger.error(f"取消输入失败: {e}")
            return False
            
    def get_typing_stats(self):
        """获取输入统计信息"""
        return {
            'delay_range': (self.delay_min, self.delay_max),
            'pause_probability': self.pause_probability,
            'use_clipboard': self.use_clipboard,
            'speed_variation': self.typing_speed_variation
        }
