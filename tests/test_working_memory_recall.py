#!/usr/bin/env python
"""
测试工作记忆的召回功能
"""

import sys
sys.path.insert(0, '.')

from embodied_cognitive_workflow.memory import (
    MemoryManager, WorkingMemory, EpisodicMemory, 
    Neo4jSemanticMemory, Neo4jConfig
)

# 创建各层记忆
working = WorkingMemory()
episodic = EpisodicMemory()
config = Neo4jConfig(database="neo4j")
semantic = Neo4jSemanticMemory(config)

# 创建记忆管理器
manager = MemoryManager(
    working_memory=working,
    episodic_memory=episodic,
    semantic_memory=semantic
)

# 存储到工作记忆
result = manager.process_information(
    info="Exploring design patterns",
    source="test",
    metadata={'importance': 0.8}
)
print(f"存储结果: {result}")

# 尝试不同的查询
queries = ["pattern", "design", "patterns", "Exploring"]
for query in queries:
    results = manager.recall_with_context(query)
    wm_results = results.get('working', [])
    print(f"\n查询 '{query}': 工作记忆结果数 = {len(wm_results)}")
    for item in wm_results:
        print(f"  - {item.content}")

# 直接测试工作记忆
print("\n直接测试工作记忆:")
wm_items = manager.working.recall("pattern", limit=10)
print(f"工作记忆直接查询结果: {len(wm_items)} 项")

# 列出所有工作记忆项
print("\n所有工作记忆项:")
all_items = manager.working.list_all()
for item in all_items:
    print(f"  - {item.id}: {item.content}")

if hasattr(semantic, 'close'):
    semantic.close()
print("\n测试完成")