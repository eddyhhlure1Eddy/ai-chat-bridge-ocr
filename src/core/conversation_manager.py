#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话管理模块
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import os

class ConversationManager:
    """对话管理器"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # 数据库设置
        self.db_path = 'data/conversations.db'
        self.ensure_data_directory()
        self.init_database()
        
        # 对话设置
        self.max_length = config.get('conversation.max_length', 100)
        self.auto_save = config.get('conversation.auto_save', True)
        self.save_interval = config.get('conversation.save_interval', 10)
        
        # 消息缓存
        self.message_cache = []
        self.last_save_time = datetime.now()
        
    def ensure_data_directory(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
            
    def init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建对话表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE,
                        left_ai TEXT,
                        right_ai TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active'
                    )
                ''')
                
                # 创建消息表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        sender TEXT,
                        recipient TEXT,
                        content TEXT,
                        timestamp TIMESTAMP,
                        message_hash TEXT,
                        ocr_confidence REAL,
                        FOREIGN KEY (session_id) REFERENCES conversations (session_id)
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON messages (session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON messages (timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_hash ON messages (message_hash)')
                
                conn.commit()
                self.logger.info("数据库初始化完成")
                
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            
    def start_conversation(self, left_ai: str, right_ai: str) -> str:
        """开始新对话"""
        try:
            session_id = self.generate_session_id()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversations (session_id, left_ai, right_ai, start_time)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, left_ai, right_ai, datetime.now()))
                conn.commit()
                
            self.logger.info(f"对话开始: {session_id} ({left_ai} ↔ {right_ai})")
            return session_id
            
        except Exception as e:
            self.logger.error(f"开始对话失败: {e}")
            return None
            
    def end_conversation(self, session_id: str):
        """结束对话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE conversations 
                    SET end_time = ?, status = 'completed'
                    WHERE session_id = ?
                ''', (datetime.now(), session_id))
                conn.commit()
                
            self.logger.info(f"对话结束: {session_id}")
            
        except Exception as e:
            self.logger.error(f"结束对话失败: {e}")
            
    def add_message(self, session_id: str, sender: str, recipient: str, 
                   content: str, ocr_confidence: float = None) -> bool:
        """添加消息"""
        try:
            # 检查消息是否重复
            message_hash = self.calculate_message_hash(content)
            if self.is_duplicate_message(session_id, message_hash):
                self.logger.debug("跳过重复消息")
                return False
                
            # 添加到缓存
            message = {
                'session_id': session_id,
                'sender': sender,
                'recipient': recipient,
                'content': content,
                'timestamp': datetime.now(),
                'message_hash': message_hash,
                'ocr_confidence': ocr_confidence
            }
            
            self.message_cache.append(message)
            
            # 自动保存
            if self.auto_save:
                self.save_cached_messages()
                
            self.logger.info(f"消息添加: {sender} → {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加消息失败: {e}")
            return False
            
    def save_cached_messages(self):
        """保存缓存的消息"""
        if not self.message_cache:
            return
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for message in self.message_cache:
                    cursor.execute('''
                        INSERT INTO messages 
                        (session_id, sender, recipient, content, timestamp, message_hash, ocr_confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        message['session_id'],
                        message['sender'],
                        message['recipient'],
                        message['content'],
                        message['timestamp'],
                        message['message_hash'],
                        message['ocr_confidence']
                    ))
                    
                    # 更新对话消息计数
                    cursor.execute('''
                        UPDATE conversations 
                        SET message_count = message_count + 1
                        WHERE session_id = ?
                    ''', (message['session_id'],))
                    
                conn.commit()
                
            self.logger.debug(f"保存了 {len(self.message_cache)} 条消息")
            self.message_cache.clear()
            self.last_save_time = datetime.now()
            
        except Exception as e:
            self.logger.error(f"保存消息失败: {e}")
            
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT sender, recipient, content, timestamp, ocr_confidence
                    FROM messages 
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                ''', (session_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'sender': row[0],
                        'recipient': row[1],
                        'content': row[2],
                        'timestamp': row[3],
                        'ocr_confidence': row[4]
                    })
                    
                return messages
                
        except Exception as e:
            self.logger.error(f"获取对话历史失败: {e}")
            return []
            
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """获取最近的对话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_id, left_ai, right_ai, start_time, end_time, message_count, status
                    FROM conversations 
                    ORDER BY start_time DESC
                    LIMIT ?
                ''', (limit,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'session_id': row[0],
                        'left_ai': row[1],
                        'right_ai': row[2],
                        'start_time': row[3],
                        'end_time': row[4],
                        'message_count': row[5],
                        'status': row[6]
                    })
                    
                return conversations
                
        except Exception as e:
            self.logger.error(f"获取最近对话失败: {e}")
            return []
            
    def export_conversation(self, session_id: str, format: str = 'json') -> str:
        """导出对话"""
        try:
            # 获取对话信息
            conversation = self.get_conversation_info(session_id)
            messages = self.get_conversation_history(session_id)
            
            if format.lower() == 'json':
                return self.export_to_json(conversation, messages)
            elif format.lower() == 'txt':
                return self.export_to_text(conversation, messages)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
        except Exception as e:
            self.logger.error(f"导出对话失败: {e}")
            return ""
            
    def export_to_json(self, conversation: Dict, messages: List[Dict]) -> str:
        """导出为JSON格式"""
        export_data = {
            'conversation': conversation,
            'messages': messages,
            'export_time': datetime.now().isoformat(),
            'total_messages': len(messages)
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
        
    def export_to_text(self, conversation: Dict, messages: List[Dict]) -> str:
        """导出为文本格式"""
        lines = []
        lines.append("AI Chat Bridge OCR - 对话记录")
        lines.append("=" * 50)
        lines.append(f"对话ID: {conversation.get('session_id', 'N/A')}")
        lines.append(f"参与者: {conversation.get('left_ai', 'N/A')} ↔ {conversation.get('right_ai', 'N/A')}")
        lines.append(f"开始时间: {conversation.get('start_time', 'N/A')}")
        lines.append(f"结束时间: {conversation.get('end_time', 'N/A')}")
        lines.append(f"消息总数: {len(messages)}")
        lines.append("")
        lines.append("对话内容:")
        lines.append("-" * 30)
        
        for i, message in enumerate(messages, 1):
            lines.append(f"[{i}] {message['timestamp']}")
            lines.append(f"{message['sender']} → {message['recipient']}:")
            lines.append(f"{message['content']}")
            if message.get('ocr_confidence'):
                lines.append(f"(OCR置信度: {message['ocr_confidence']:.1f}%)")
            lines.append("")
            
        return "\n".join(lines)
        
    def calculate_message_hash(self, content: str) -> str:
        """计算消息哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
        
    def is_duplicate_message(self, session_id: str, message_hash: str) -> bool:
        """检查是否为重复消息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM messages 
                    WHERE session_id = ? AND message_hash = ?
                ''', (session_id, message_hash))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"检查重复消息失败: {e}")
            return False
            
    def generate_session_id(self) -> str:
        """生成会话ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}"
        
    def get_conversation_info(self, session_id: str) -> Dict:
        """获取对话信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_id, left_ai, right_ai, start_time, end_time, message_count, status
                    FROM conversations 
                    WHERE session_id = ?
                ''', (session_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'session_id': row[0],
                        'left_ai': row[1],
                        'right_ai': row[2],
                        'start_time': row[3],
                        'end_time': row[4],
                        'message_count': row[5],
                        'status': row[6]
                    }
                    
        except Exception as e:
            self.logger.error(f"获取对话信息失败: {e}")
            
        return {}
        
    def cleanup_old_conversations(self, days: int = 30):
        """清理旧对话"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除旧消息
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE session_id IN (
                        SELECT session_id FROM conversations 
                        WHERE start_time < ?
                    )
                ''', (cutoff_date,))
                
                # 删除旧对话
                cursor.execute('''
                    DELETE FROM conversations 
                    WHERE start_time < ?
                ''', (cutoff_date,))
                
                conn.commit()
                
            self.logger.info(f"清理了 {days} 天前的对话记录")
            
        except Exception as e:
            self.logger.error(f"清理对话失败: {e}")
