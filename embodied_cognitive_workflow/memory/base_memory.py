"""
基础记忆实现

提供记忆存储的基础实现和内存存储策略
"""

from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import json
import pickle
from collections import OrderedDict
import heapq

from .interfaces import IMemory, MemoryItem
from .utils import calculate_similarity, extract_keywords, generate_memory_id, safe_json_dumps


class InMemoryStorage:
    """内存存储策略"""
    
    def __init__(self, max_size: Optional[int] = None):
        """
        初始化内存存储
        
        Args:
            max_size: 最大存储项数，None表示无限制
        """
        self.max_size = max_size
        self._storage: OrderedDict[str, MemoryItem] = OrderedDict()
        self._index: Dict[str, Set[str]] = {}  # 关键词到ID的索引
    
    def put(self, key: str, item: MemoryItem) -> None:
        """存储项"""
        # 如果达到容量限制，移除最旧的项
        if self.max_size and len(self._storage) >= self.max_size:
            if key not in self._storage:
                # 移除最旧的项（OrderedDict保持插入顺序）
                oldest_key = next(iter(self._storage))
                self._remove_from_index(oldest_key)
                del self._storage[oldest_key]
        
        # 存储新项
        self._storage[key] = item
        self._storage.move_to_end(key)  # 移到末尾（最新）
        
        # 更新索引
        self._update_index(key, item)
    
    def get(self, key: str) -> Optional[MemoryItem]:
        """获取项"""
        item = self._storage.get(key)
        if item:
            # 更新访问信息
            item.access_count += 1
            item.last_accessed = datetime.now()
            # 移到末尾表示最近访问
            self._storage.move_to_end(key)
        return item
    
    def delete(self, key: str) -> bool:
        """删除项"""
        if key in self._storage:
            self._remove_from_index(key)
            del self._storage[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """检查是否存在"""
        return key in self._storage
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """列出所有项"""
        items = list(self._storage.values())
        return items[offset:offset + limit]
    
    def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """搜索项"""
        query_keywords = extract_keywords(query.lower())
        
        # 计算每个项的相关性得分
        scored_items = []
        for key, item in self._storage.items():
            score = 0.0
            
            # 基于关键词匹配
            item_keywords = extract_keywords(str(item.content).lower())
            keyword_overlap = len(query_keywords.intersection(item_keywords))
            if keyword_overlap > 0:
                score += keyword_overlap / len(query_keywords)
            
            # 基于内容相似度
            content_str = safe_json_dumps(item.content) if isinstance(item.content, dict) else str(item.content)
            content_similarity = calculate_similarity(query, content_str)
            score += content_similarity
            
            # 考虑重要性
            score *= (1 + item.importance)
            
            # 考虑访问频率
            score *= (1 + item.access_count * 0.1)
            
            if score > 0:
                scored_items.append((score, item))
        
        # 返回得分最高的项
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:limit]]
    
    def clear(self) -> int:
        """清空存储"""
        count = len(self._storage)
        self._storage.clear()
        self._index.clear()
        return count
    
    def size(self) -> int:
        """获取存储大小"""
        return len(self._storage)
    
    def _update_index(self, key: str, item: MemoryItem) -> None:
        """更新索引"""
        # 提取关键词
        content_str = safe_json_dumps(item.content) if isinstance(item.content, dict) else str(item.content)
        keywords = extract_keywords(content_str.lower())
        
        # 更新倒排索引
        for keyword in keywords:
            if keyword not in self._index:
                self._index[keyword] = set()
            self._index[keyword].add(key)
    
    def _remove_from_index(self, key: str) -> None:
        """从索引中移除"""
        # 从所有包含该key的索引中移除
        for keyword_set in self._index.values():
            keyword_set.discard(key)


class BaseMemory(IMemory, ABC):
    """基础记忆实现"""
    
    def __init__(self, storage: Optional[InMemoryStorage] = None):
        """
        初始化基础记忆
        
        Args:
            storage: 存储策略，默认使用内存存储
        """
        self.storage = storage or InMemoryStorage()
    
    def store(self, key: str, content: Any, metadata: Dict[str, Any] = None) -> str:
        """存储记忆项"""
        # 生成ID
        memory_id = key or generate_memory_id()
        
        # 创建记忆项
        item = MemoryItem(
            id=memory_id,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now()
        )
        
        # 存储
        self.storage.put(memory_id, item)
        
        return memory_id
    
    def recall(self, query: str, limit: int = 10, **kwargs) -> List[MemoryItem]:
        """检索记忆"""
        return self.storage.search(query, limit)
    
    def forget(self, key: str) -> bool:
        """删除记忆"""
        return self.storage.delete(key)
    
    def update(self, key: str, content: Any, metadata: Dict[str, Any] = None) -> bool:
        """更新记忆"""
        item = self.storage.get(key)
        if item:
            item.content = content
            if metadata is not None:
                item.metadata.update(metadata)
            item.timestamp = datetime.now()
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """检查记忆是否存在"""
        return self.storage.exists(key)
    
    def get(self, key: str) -> Optional[MemoryItem]:
        """获取单个记忆项"""
        return self.storage.get(key)
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """列出所有记忆项"""
        return self.storage.list_all(limit, offset)
    
    def clear(self) -> int:
        """清空所有记忆"""
        return self.storage.clear()
    
    def size(self) -> int:
        """获取记忆项数量"""
        return self.storage.size()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        items = self.storage.list_all(limit=self.storage.size())
        
        if not items:
            return {
                "total_items": 0,
                "avg_access_count": 0,
                "avg_importance": 0,
                "oldest_timestamp": None,
                "newest_timestamp": None
            }
        
        access_counts = [item.access_count for item in items]
        importances = [item.importance for item in items]
        timestamps = [item.timestamp for item in items]
        
        return {
            "total_items": len(items),
            "avg_access_count": sum(access_counts) / len(access_counts),
            "avg_importance": sum(importances) / len(importances),
            "oldest_timestamp": min(timestamps),
            "newest_timestamp": max(timestamps),
            "most_accessed": max(items, key=lambda x: x.access_count).id if items else None,
            "most_important": max(items, key=lambda x: x.importance).id if items else None
        }