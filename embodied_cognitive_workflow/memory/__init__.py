"""
记忆管理系统

基于人类认知的三层记忆架构实现：
- 工作记忆（Working Memory）：短期临时存储，容量有限
- 情景记忆（Episodic Memory）：项目和任务相关的经验存储
- 语义记忆（Semantic Memory）：抽象的知识和模式存储

核心特性：
- 组合架构设计，支持灵活扩展
- 记忆层级间的自动转化机制
- 上下文感知的记忆召回
- 生命周期管理和自动遗忘
"""

from .interfaces import (
    IMemory,
    IWorkingMemory,
    IEpisodicMemory,
    ISemanticMemory,
    MemoryItem,
    Episode,
    Concept,
    TriggerType,
    MemoryLayer
)

from .base_memory import BaseMemory, InMemoryStorage

from .working_memory import WorkingMemory

from .episodic_memory import EpisodicMemory

from .semantic_memory import SemanticMemory

from .memory_manager import MemoryManager

from .transformers import (
    IMemoryTransformer,
    WorkingToEpisodicTransformer,
    EpisodicToSemanticTransformer,
    SemanticToEpisodicTransformer,
    EpisodicToWorkingTransformer
)

from .utils import (
    calculate_similarity,
    extract_keywords,
    generate_memory_id,
    calculate_importance
)

# 生命周期管理
from .memory_lifecycle import (
    MemoryLifecycleManager,
    LifecyclePolicy,
    LifecycleStage,
    LifecycleMetadata
)

# Neo4j支持
try:
    from .neo4j_config import Neo4jConfig
    from .semantic_memory_neo4j import Neo4jSemanticMemory
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

__version__ = "1.0.0"

__all__ = [
    # 接口
    "IMemory",
    "IWorkingMemory",
    "IEpisodicMemory",
    "ISemanticMemory",
    "MemoryItem",
    "Episode",
    "Concept",
    "TriggerType",
    "MemoryLayer",
    
    # 基础实现
    "BaseMemory",
    "InMemoryStorage",
    
    # 三层记忆
    "WorkingMemory",
    "EpisodicMemory",
    "SemanticMemory",
    
    # 管理器
    "MemoryManager",
    
    # 转换器
    "IMemoryTransformer",
    "WorkingToEpisodicTransformer",
    "EpisodicToSemanticTransformer",
    "SemanticToEpisodicTransformer",
    "EpisodicToWorkingTransformer",
    
    # 工具函数
    "calculate_similarity",
    "extract_keywords",
    "generate_memory_id",
    "calculate_importance",
    
    # 生命周期管理
    "MemoryLifecycleManager",
    "LifecyclePolicy",
    "LifecycleStage",
    "LifecycleMetadata",
    
    # Neo4j标记
    "NEO4J_AVAILABLE"
]

# 如果Neo4j可用，添加到导出列表
if NEO4J_AVAILABLE:
    __all__.extend(["Neo4jConfig", "Neo4jSemanticMemory"])