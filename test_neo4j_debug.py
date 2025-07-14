#!/usr/bin/env python
"""
调试Neo4j问题
"""

import sys
sys.path.insert(0, '.')

from embodied_cognitive_workflow.memory import Neo4jSemanticMemory, Neo4jConfig, Concept

# 创建Neo4j连接
config = Neo4jConfig(database="neo4j")
memory = Neo4jSemanticMemory(config)

# 清空数据
memory.clear()
print("已清空数据库")

# 创建测试数据
root = Concept(
    id="prog_langs",
    name="Programming Languages",
    category="domain",
    attributes={'type': 'knowledge_domain'},
    confidence=1.0
)
root_id = memory.add_concept(root)
print(f"添加根节点: {root_id}")

# 添加子节点
languages = ["Python", "JavaScript", "Rust"]
lang_ids = []
for lang in languages:
    concept = Concept(
        id=f"lang_{lang.lower()}",
        name=lang,
        category="programming_language",
        attributes={'paradigm': 'multi-paradigm'},
        confidence=0.9
    )
    lang_id = memory.add_concept(concept)
    lang_ids.append(lang_id)
    print(f"添加语言: {lang_id}")
    
    # 创建关系
    success = memory.create_relationship(root_id, lang_id, "INCLUDES")
    print(f"  创建关系 {root_id} -> {lang_id}: {success}")

# 获取知识图谱
print("\n获取知识图谱:")
graph = memory.get_knowledge_graph(root_id, depth=2)
print(f"节点数: {len(graph['nodes'])}")
print(f"边数: {len(graph['edges'])}")

# 显示节点详情
print("\n节点列表:")
for node in graph['nodes']:
    print(f"  - {node['id']}: {node['name']}")

# 显示边详情
print("\n边列表:")
for edge in graph['edges']:
    print(f"  - {edge['source']} -> {edge['target']} ({edge['type']})")

# 直接查询检查
print("\n直接查询所有节点:")
all_nodes = memory.list_all(limit=10)
print(f"总节点数: {len(all_nodes)}")
for item in all_nodes:
    print(f"  - {item.id}: {item.content.get('name', 'Unknown')}")

# 检查关系
print("\n检查关系:")
for lang_id in lang_ids:
    related = memory.find_related_concepts(lang_id)
    print(f"{lang_id} 的相关节点: {len(related)}")
    for rel_type, concept in related:
        print(f"  - {rel_type}: {concept.name}")

memory.close()
print("\n调试完成")