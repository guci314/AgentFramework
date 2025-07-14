"""
工作记忆实现

实现了容量限制、时间衰减、触发器驱动和注意力权重机制
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import heapq
from collections import deque

from .interfaces import IWorkingMemory, MemoryItem, TriggerType
from .base_memory import BaseMemory, InMemoryStorage
from .utils import calculate_importance, generate_memory_id


class WorkingMemory(BaseMemory, IWorkingMemory):
    """工作记忆实现"""
    
    def __init__(self, 
                 capacity: int = 7,
                 decay_threshold: timedelta = timedelta(minutes=30),
                 min_importance: float = 0.3):
        """
        初始化工作记忆
        
        Args:
            capacity: 容量限制（默认7±2）
            decay_threshold: 衰减时间阈值
            min_importance: 最小重要性阈值
        """
        # 使用有容量限制的存储
        super().__init__(InMemoryStorage(max_size=capacity * 2))  # 留一些缓冲空间
        
        self.capacity = capacity
        self.decay_threshold = decay_threshold
        self.min_importance = min_importance
        
        # 注意力权重
        self._attention_weights: Dict[str, float] = {}
        
        # 触发器配置
        self._trigger_config = {
            TriggerType.MANUAL: lambda content, **kwargs: True,
            TriggerType.ERROR: self._should_record_error,
            TriggerType.DECISION: self._should_record_decision,
            TriggerType.STATE_CHANGE: self._should_record_state_change,
            TriggerType.MILESTONE: self._should_record_milestone,
            TriggerType.PATTERN_DETECTED: self._should_record_pattern
        }
        
        # 活跃记忆队列（用于快速访问最近使用的记忆）
        self._active_queue: deque = deque(maxlen=capacity)
    
    def add_with_trigger(self, content: Any, trigger_type: TriggerType, **kwargs) -> Optional[str]:
        """基于触发器的记忆添加"""
        # 检查是否应该记录
        trigger_func = self._trigger_config.get(trigger_type)
        if not trigger_func or not trigger_func(content, **kwargs):
            return None
        
        # 计算重要性
        importance = calculate_importance(content, kwargs.get('metadata', {}))
        if importance < self.min_importance:
            return None
        
        # 如果容量已满，执行驱逐策略
        if self.size() >= self.capacity:
            self._evict_least_important()
        
        # 生成ID并存储
        memory_id = generate_memory_id("wm")
        metadata = kwargs.get('metadata')
        if metadata is None:
            metadata = {}
        metadata['trigger_type'] = trigger_type.value
        
        self.store(memory_id, content, metadata)
        
        # 更新注意力权重
        self._attention_weights[memory_id] = importance
        
        # 添加到活跃队列
        self._active_queue.append(memory_id)
        
        return memory_id
    
    def decay(self) -> int:
        """执行时间衰减"""
        current_time = datetime.now()
        decayed_count = 0
        
        # 获取所有记忆项
        items = self.list_all(limit=self.size())
        
        for item in items:
            # 计算年龄
            age = current_time - item.timestamp
            
            # 如果超过衰减阈值且访问次数较少
            if age > self.decay_threshold and item.access_count < 3:
                # 降低重要性
                decay_factor = age.total_seconds() / self.decay_threshold.total_seconds()
                new_importance = item.importance * (1 / decay_factor)
                
                # 如果重要性太低，删除
                if new_importance < self.min_importance:
                    self.forget(item.id)
                    self._attention_weights.pop(item.id, None)
                    decayed_count += 1
                else:
                    # 更新重要性
                    item.importance = new_importance
                    self._attention_weights[item.id] = new_importance
        
        return decayed_count
    
    def get_attention_weights(self) -> Dict[str, float]:
        """获取注意力权重"""
        return self._attention_weights.copy()
    
    def update_attention(self, key: str, weight_delta: float) -> bool:
        """更新注意力权重"""
        if key in self._attention_weights:
            # 更新权重
            self._attention_weights[key] = max(0.0, min(1.0, 
                self._attention_weights[key] + weight_delta))
            
            # 同步更新记忆项的重要性
            item = self.get(key)
            if item:
                item.importance = self._attention_weights[key]
            
            return True
        return False
    
    def get_capacity(self) -> int:
        """获取工作记忆容量"""
        return self.capacity
    
    def set_capacity(self, capacity: int) -> None:
        """设置工作记忆容量"""
        self.capacity = max(3, capacity)  # 最小容量为3
        
        # 如果当前记忆超过新容量，执行驱逐
        while self.size() > self.capacity:
            self._evict_least_important()
    
    def get(self, key: str) -> Optional[MemoryItem]:
        """获取单个记忆项并更新活跃队列"""
        item = super().get(key)
        if item and key in [m for m in self._active_queue]:
            # 如果项在活跃队列中，将其移到末尾
            self._active_queue.remove(key)
            self._active_queue.append(key)
        return item
    
    def get_active_memories(self) -> List[MemoryItem]:
        """获取活跃记忆（最近使用的）"""
        active_items = []
        for memory_id in self._active_queue:
            # 直接从存储获取，不调用get以避免改变顺序
            item = self.storage.get(memory_id)
            if item:
                active_items.append(item)
        return active_items
    
    def _evict_least_important(self) -> bool:
        """驱逐最不重要的记忆"""
        items = self.list_all(limit=self.size())
        if not items:
            return False
        
        # 计算每个项的驱逐分数（越低越容易被驱逐）
        eviction_scores = []
        for item in items:
            # 考虑重要性、访问次数和年龄
            age_factor = (datetime.now() - item.timestamp).total_seconds() / 3600  # 小时
            score = item.importance * (1 + item.access_count) / (1 + age_factor)
            heapq.heappush(eviction_scores, (score, item.id))
        
        # 驱逐分数最低的项
        if eviction_scores:
            _, evicted_id = heapq.heappop(eviction_scores)
            self.forget(evicted_id)
            self._attention_weights.pop(evicted_id, None)
            return True
        
        return False
    
    def _should_record_error(self, content: Any, **kwargs) -> bool:
        """判断是否应该记录错误"""
        # 检查是否包含错误信息
        content_str = str(content).lower()
        error_keywords = ['error', 'exception', 'failed', 'failure', '错误', '异常', '失败']
        return any(keyword in content_str for keyword in error_keywords)
    
    def _should_record_decision(self, content: Any, **kwargs) -> bool:
        """判断是否应该记录决策"""
        # 检查元数据中是否标记为决策
        metadata = kwargs.get('metadata')
        if metadata is None:
            metadata = {}
        if metadata.get('is_decision'):
            return True
        
        # 检查内容中是否包含决策关键词
        content_str = str(content).lower()
        decision_keywords = ['decide', 'decision', 'choose', 'select', '决定', '选择', '判断']
        return any(keyword in content_str for keyword in decision_keywords)
    
    def _should_record_state_change(self, content: Any, **kwargs) -> bool:
        """判断是否应该记录状态变化"""
        # 检查元数据中是否有状态变化标记
        metadata = kwargs.get('metadata')
        if metadata is None:
            metadata = {}
        return bool(metadata.get('state_change') or metadata.get('transition'))
    
    def _should_record_milestone(self, content: Any, **kwargs) -> bool:
        """判断是否应该记录里程碑"""
        # 检查元数据中是否有里程碑标记
        metadata = kwargs.get('metadata')
        if metadata is None:
            metadata = {}
        return bool(metadata.get('milestone') or metadata.get('achievement'))
    
    def _should_record_pattern(self, content: Any, **kwargs) -> bool:
        """判断是否应该记录模式"""
        # 检查元数据中是否有模式标记
        metadata = kwargs.get('metadata')
        if metadata is None:
            metadata = {}
        return bool(metadata.get('pattern') or metadata.get('repeated'))
    
    def consolidate(self) -> Dict[str, Any]:
        """
        整合工作记忆，准备转换到情景记忆
        
        Returns:
            整合后的记忆内容
        """
        items = self.get_active_memories()
        
        if not items:
            return {}
        
        # 按时间排序
        items.sort(key=lambda x: x.timestamp)
        
        # 整合内容
        consolidated = {
            'start_time': items[0].timestamp,
            'end_time': items[-1].timestamp,
            'duration': (items[-1].timestamp - items[0].timestamp).total_seconds(),
            'items_count': len(items),
            'events': []
        }
        
        # 提取事件序列
        for item in items:
            event = {
                'timestamp': item.timestamp,
                'content': item.content,
                'importance': item.importance,
                'trigger_type': item.metadata.get('trigger_type', 'unknown')
            }
            consolidated['events'].append(event)
        
        # 提取关键信息
        errors = [e for e in consolidated['events'] 
                 if e['trigger_type'] == TriggerType.ERROR.value]
        decisions = [e for e in consolidated['events'] 
                    if e['trigger_type'] == TriggerType.DECISION.value]
        
        consolidated['summary'] = {
            'total_errors': len(errors),
            'total_decisions': len(decisions),
            'avg_importance': sum(e['importance'] for e in consolidated['events']) / len(consolidated['events'])
        }
        
        return consolidated