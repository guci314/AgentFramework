"""
记忆管理系统接口定义

定义了三层记忆架构的抽象接口和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum


class MemoryType(Enum):
    """记忆类型枚举"""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class TriggerType(Enum):
    """触发器类型枚举"""
    MANUAL = "manual"
    ERROR = "error"
    DECISION = "decision"
    STATE_CHANGE = "state_change"
    MILESTONE = "milestone"
    PATTERN_DETECTED = "pattern_detected"


@dataclass
class MemoryItem:
    """基础记忆项"""
    id: str  # 记忆项的唯一标识符
    content: Any  # 记忆的实际内容，可以是任意类型的数据
    timestamp: datetime = field(default_factory=datetime.now)  # 记忆创建的时间戳
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加的元数据信息
    access_count: int = 0  # 记忆被访问的次数
    last_accessed: Optional[datetime] = None  # 最后一次访问的时间
    importance: float = 0.5  # 记忆的重要性评分，范围0-1，越高越重要
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Episode:
    """情景记忆项"""
    id: str  # 情景的唯一标识符
    event: str  # 事件的描述，记录发生了什么
    context: Dict[str, Any]  # 事件发生时的上下文信息
    timestamp: datetime = field(default_factory=datetime.now)  # 事件发生的时间
    project_id: Optional[str] = None  # 关联的项目ID，用于项目级别的记忆组织
    participants: List[str] = field(default_factory=list)  # 参与事件的实体列表（如人员、系统等）
    outcomes: Dict[str, Any] = field(default_factory=dict)  # 事件的结果或产出
    related_episodes: List[str] = field(default_factory=list)  # 相关联的其他情景ID列表
    
    def to_memory_item(self) -> MemoryItem:
        """转换为基础记忆项"""
        return MemoryItem(
            id=self.id,
            content={
                "event": self.event,
                "context": self.context,
                "outcomes": self.outcomes
            },
            timestamp=self.timestamp,
            metadata={
                "type": "episode",
                "project_id": self.project_id,
                "participants": self.participants,
                "related_episodes": self.related_episodes
            }
        )


@dataclass
class Concept:
    """语义记忆项"""
    id: str  # 概念的唯一标识符
    name: str  # 概念的名称
    category: str  # 概念所属的类别（如：技术、方法、模式等）
    attributes: Dict[str, Any]  # 概念的属性集合，描述概念的特征
    relationships: Dict[str, List[str]] = field(default_factory=dict)  # 与其他概念的关系映射，键为关系类型，值为相关概念ID列表
    confidence: float = 0.5  # 概念的置信度，表示对该概念认知的确定程度（0-1）
    examples: List[Dict[str, Any]] = field(default_factory=list)  # 概念的实例或示例，帮助理解概念
    domain: Optional[str] = None  # 概念所属的领域（如：机器学习、软件工程等）
    
    def to_memory_item(self) -> MemoryItem:
        """转换为基础记忆项"""
        return MemoryItem(
            id=self.id,
            content={
                "name": self.name,
                "attributes": self.attributes,
                "examples": self.examples
            },
            metadata={
                "type": "concept",
                "category": self.category,
                "domain": self.domain,
                "relationships": self.relationships,
                "confidence": self.confidence
            },
            importance=self.confidence
        )


class IMemory(ABC):
    """记忆层基础接口"""
    
    @abstractmethod
    def store(self, key: str, content: Any, metadata: Dict[str, Any] = None) -> str:
        """
        存储记忆项
        
        Args:
            key: 记忆键
            content: 记忆内容
            metadata: 元数据
            
        Returns:
            记忆项ID
        """
        pass
    
    @abstractmethod
    def recall(self, query: str, limit: int = 10, **kwargs) -> List[MemoryItem]:
        """
        检索记忆
        
        Args:
            query: 查询字符串
            limit: 返回结果数量限制
            **kwargs: 额外的查询参数
            
        Returns:
            记忆项列表
        """
        pass
    
    @abstractmethod
    def forget(self, key: str) -> bool:
        """
        删除记忆
        
        Args:
            key: 记忆键
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    def update(self, key: str, content: Any, metadata: Dict[str, Any] = None) -> bool:
        """
        更新记忆
        
        Args:
            key: 记忆键
            content: 新内容
            metadata: 新元数据
            
        Returns:
            是否成功更新
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查记忆是否存在
        
        Args:
            key: 记忆键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[MemoryItem]:
        """
        获取单个记忆项
        
        Args:
            key: 记忆键
            
        Returns:
            记忆项或None
        """
        pass
    
    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """
        列出所有记忆项
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            记忆项列表
        """
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """
        清空所有记忆
        
        Returns:
            清除的记忆项数量
        """
        pass
    
    @abstractmethod
    def size(self) -> int:
        """
        获取记忆项数量
        
        Returns:
            记忆项数量
        """
        pass


class IWorkingMemory(IMemory):
    """工作记忆接口"""
    
    @abstractmethod
    def add_with_trigger(self, content: Any, trigger_type: TriggerType, **kwargs) -> Optional[str]:
        """
        基于触发器的记忆添加
        
        Args:
            content: 记忆内容
            trigger_type: 触发器类型
            **kwargs: 额外参数
            
        Returns:
            记忆ID或None（如果不满足触发条件）
        """
        pass
    
    @abstractmethod
    def decay(self) -> int:
        """
        执行时间衰减，清理过期记忆
        
        Returns:
            清理的项数
        """
        pass
    
    @abstractmethod
    def get_attention_weights(self) -> Dict[str, float]:
        """
        获取注意力权重
        
        Returns:
            记忆ID到权重的映射
        """
        pass
    
    @abstractmethod
    def update_attention(self, key: str, weight_delta: float) -> bool:
        """
        更新注意力权重
        
        Args:
            key: 记忆键
            weight_delta: 权重变化量
            
        Returns:
            是否成功更新
        """
        pass
    
    @abstractmethod
    def get_capacity(self) -> int:
        """
        获取工作记忆容量
        
        Returns:
            容量大小
        """
        pass
    
    @abstractmethod
    def set_capacity(self, capacity: int) -> None:
        """
        设置工作记忆容量
        
        Args:
            capacity: 新容量
        """
        pass


class IEpisodicMemory(IMemory):
    """情景记忆接口"""
    
    @abstractmethod
    def store_episode(self, event: str, context: Dict[str, Any], **kwargs) -> str:
        """
        存储情景事件
        
        Args:
            event: 事件描述
            context: 事件上下文
            **kwargs: 额外参数（如project_id, participants等）
            
        Returns:
            情景记忆ID
        """
        pass
    
    @abstractmethod
    def query_timeline(self, start: datetime, end: datetime, project_id: Optional[str] = None) -> List[Episode]:
        """
        按时间线查询
        
        Args:
            start: 开始时间
            end: 结束时间
            project_id: 项目ID（可选）
            
        Returns:
            情景列表
        """
        pass
    
    @abstractmethod
    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """
        获取项目上下文
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目相关的所有上下文信息
        """
        pass
    
    @abstractmethod
    def link_episodes(self, episode_id1: str, episode_id2: str, relationship: str) -> bool:
        """
        关联两个情景
        
        Args:
            episode_id1: 情景1的ID
            episode_id2: 情景2的ID
            relationship: 关系类型
            
        Returns:
            是否成功关联
        """
        pass
    
    @abstractmethod
    def get_related_episodes(self, episode_id: str, relationship: Optional[str] = None) -> List[Episode]:
        """
        获取相关情景
        
        Args:
            episode_id: 情景ID
            relationship: 关系类型（可选）
            
        Returns:
            相关情景列表
        """
        pass


class ISemanticMemory(IMemory):
    """语义记忆接口"""
    
    @abstractmethod
    def add_concept(self, concept: Concept) -> str:
        """
        添加概念知识
        
        Args:
            concept: 概念对象
            
        Returns:
            概念ID
        """
        pass
    
    @abstractmethod
    def find_patterns(self, domain: str, min_confidence: float = 0.5) -> List[Concept]:
        """
        查找领域模式
        
        Args:
            domain: 领域名称
            min_confidence: 最小置信度
            
        Returns:
            概念列表
        """
        pass
    
    @abstractmethod
    def get_knowledge_graph(self, root_concept: str, depth: int = 2) -> Dict[str, Any]:
        """
        获取知识图谱
        
        Args:
            root_concept: 根概念
            depth: 探索深度
            
        Returns:
            知识图谱结构
        """
        pass
    
    @abstractmethod
    def update_concept_confidence(self, concept_id: str, confidence_delta: float) -> bool:
        """
        更新概念置信度
        
        Args:
            concept_id: 概念ID
            confidence_delta: 置信度变化量
            
        Returns:
            是否成功更新
        """
        pass
    
    @abstractmethod
    def merge_concepts(self, concept_id1: str, concept_id2: str) -> Optional[str]:
        """
        合并两个相似概念
        
        Args:
            concept_id1: 概念1的ID
            concept_id2: 概念2的ID
            
        Returns:
            合并后的概念ID或None
        """
        pass
    
    @abstractmethod
    def get_concepts_by_category(self, category: str) -> List[Concept]:
        """
        按类别获取概念
        
        Args:
            category: 类别名称
            
        Returns:
            概念列表
        """
        pass


class MemoryLayer(Enum):
    """记忆层级枚举"""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    ALL = "all"