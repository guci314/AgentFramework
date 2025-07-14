#!/usr/bin/env python
"""
演示不同记忆层的存储选项
"""

from memory_manager import MemoryManager
from working_memory import WorkingMemory
from episodic_memory import EpisodicMemory
from semantic_memory import SemanticMemory
from semantic_memory_neo4j import Neo4jSemanticMemory
from neo4j_config import Neo4jConfig


def demo_default_storage():
    """演示默认存储（全部在内存中）"""
    print("=== 默认存储方案（全部内存） ===")
    
    # 创建默认的记忆管理器
    manager = MemoryManager(
        working_memory=WorkingMemory(),      # 内存存储
        episodic_memory=EpisodicMemory(),    # 内存存储  
        semantic_memory=SemanticMemory()     # 内存存储
    )
    
    # 存储一些信息
    result = manager.process_information(
        "Python是一种高级编程语言",
        metadata={"importance": 0.8}
    )
    
    print(f"存储结果: {result}")
    print("注意: 程序重启后所有数据将丢失\n")


def demo_neo4j_semantic_storage():
    """演示Neo4j持久化存储（仅语义记忆）"""
    print("=== Neo4j持久化方案（仅语义记忆） ===")
    
    # 配置Neo4j
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="graphiti123!",
        database="neo4j"
    )
    
    # 创建混合存储的记忆管理器
    manager = MemoryManager(
        working_memory=WorkingMemory(),                          # 内存存储
        episodic_memory=EpisodicMemory(),                        # 内存存储
        semantic_memory=Neo4jSemanticMemory(config=neo4j_config) # Neo4j存储
    )
    
    # 存储一些信息
    result = manager.process_information(
        "机器学习是人工智能的重要分支",
        metadata={"importance": 0.9}
    )
    
    print(f"存储结果: {result}")
    print("注意: 只有语义记忆会持久化到Neo4j\n")


def demo_storage_architecture():
    """展示存储架构"""
    print("=== 当前存储架构 ===")
    print("""
    1. 工作记忆 (WorkingMemory)
       - 存储: InMemoryStorage (内存)
       - 特点: 快速访问，容量有限(7±2)
       - 数据: 临时的，程序重启后丢失
       
    2. 情景记忆 (EpisodicMemory)  
       - 存储: InMemoryStorage (内存)
       - 特点: 存储事件序列和情景
       - 数据: 临时的，程序重启后丢失
       
    3. 语义记忆 (SemanticMemory)
       - 默认: InMemoryStorage (内存)
       - 可选: Neo4jSemanticMemory (Neo4j图数据库)
       - 特点: 存储概念、知识和关系
       - 数据: 使用Neo4j时可持久化
    """)


def demo_future_possibilities():
    """展示未来可能的扩展"""
    print("=== 未来可能的扩展 ===")
    print("""
    1. 工作记忆持久化选项:
       - Redis (快速缓存)
       - SQLite (轻量级持久化)
       
    2. 情景记忆持久化选项:
       - PostgreSQL (结构化存储)
       - MongoDB (文档存储)
       - Elasticsearch (全文搜索)
       
    3. 统一持久化方案:
       - 所有层都使用Neo4j
       - 混合方案: Redis + PostgreSQL + Neo4j
       
    4. 实现方式:
       # 创建持久化的工作记忆
       class RedisWorkingMemory(BaseMemory, IWorkingMemory):
           def __init__(self, redis_config):
               storage = RedisStorage(redis_config)
               super().__init__(storage)
               
       # 创建持久化的情景记忆
       class PostgresEpisodicMemory(BaseMemory, IEpisodicMemory):
           def __init__(self, pg_config):
               storage = PostgresStorage(pg_config)
               super().__init__(storage)
    """)


if __name__ == "__main__":
    demo_storage_architecture()
    print("\n" + "="*60 + "\n")
    
    demo_default_storage()
    print("\n" + "="*60 + "\n")
    
    try:
        demo_neo4j_semantic_storage()
    except Exception as e:
        print(f"Neo4j连接失败: {e}")
        print("请确保Neo4j正在运行")
    
    print("\n" + "="*60 + "\n")
    demo_future_possibilities()