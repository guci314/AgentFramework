from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from threading import Lock
import time
import uuid
from datetime import datetime

@dataclass
class Message:
    """消息类"""
    value: Any
    timestamp: float
    offset: int
    topic: str

class Topic:
    """主题类"""
    def __init__(self, name: str):
        self.name = name
        self.messages: List[Message] = []
        self.lock = Lock()
        self.subscribers: List[Callable[[Message], None]] = []
        
    def append(self, value: Any) -> Message:
        """添加消息到主题"""
        with self.lock:
            message = Message(
                value=value,
                timestamp=time.time(),
                offset=len(self.messages),
                topic=self.name
            )
            self.messages.append(message)
            
            # 通知所有订阅者
            for callback in self.subscribers:
                callback(message)
                
            return message
            
    def subscribe(self, callback: Callable[[Message], None]) -> None:
        """订阅主题"""
        self.subscribers.append(callback)

class MemoryKafka:
    """简化版内存Kafka（单例模式）"""
    _instance: Optional['MemoryKafka'] = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                # 初始化实例属性
                cls._instance.topics = {}
                cls._instance.lock = Lock()
            return cls._instance
            
    @classmethod
    def get_instance(cls) -> 'MemoryKafka':
        """获取MemoryKafka实例"""
        if cls._instance is None:
            return cls()
        return cls._instance
        
    @classmethod
    def reset_instance(cls) -> None:
        """重置MemoryKafka实例（主要用于测试）"""
        with cls._lock:
            cls._instance = None
            
    def create_topic(self, name: str) -> Topic:
        """创建主题"""
        with self.lock:
            if name in self.topics:
                return self.topics[name]
            topic = Topic(name)
            self.topics[name] = topic
            return topic
            
    def get_topic(self, name: str) -> Optional[Topic]:
        """获取主题"""
        return self.topics.get(name)
        
    def produce(self, topic_name: str, value: Any) -> Message:
        """生产消息"""
        topic = self.get_topic(topic_name)
        if not topic:
            topic = self.create_topic(topic_name)
        return topic.append(value)
        
    def subscribe(self, topic_name: str, callback: Callable[[Message], None]) -> None:
        """订阅主题"""
        topic = self.get_topic(topic_name)
        if not topic:
            topic = self.create_topic(topic_name)
        topic.subscribe(callback)

