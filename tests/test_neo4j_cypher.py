#!/usr/bin/env python
"""
直接运行Cypher查询调试
"""

import sys
sys.path.insert(0, '.')

from embodied_cognitive_workflow.memory import Neo4jSemanticMemory, Neo4jConfig

# 创建Neo4j连接
config = Neo4jConfig(database="neo4j")
memory = Neo4jSemanticMemory(config)

print("运行Cypher查询调试")
print("=" * 50)

# 1. 查看所有节点和关系
with memory.driver.session(database=config.database) as session:
    # 查询所有节点
    result = session.run("MATCH (n:Concept) RETURN n")
    nodes = list(result)
    print(f"\n总节点数: {len(nodes)}")
    
    # 查询所有关系
    result = session.run("MATCH (n1:Concept)-[r]->(n2:Concept) RETURN n1.id as source, type(r) as type, n2.id as target")
    relationships = list(result)
    print(f"总关系数: {len(relationships)}")
    
    for rel in relationships:
        print(f"  {rel['source']} -> {rel['target']} ({rel['type']})")
    
    # 测试知识图谱查询
    print("\n测试知识图谱查询:")
    query = """
    MATCH path = (c:Concept {id: $root_id})-[*0..2]-(related)
    RETURN path
    """
    result = session.run(query, root_id="prog_langs")
    paths = list(result)
    print(f"找到路径数: {len(paths)}")
    
    # 尝试另一种查询方式
    print("\n尝试另一种查询:")
    query2 = """
    MATCH (c:Concept {id: $root_id})
    OPTIONAL MATCH path = (c)-[*1..2]-(related:Concept)
    RETURN c, collect(path) as paths
    """
    result2 = session.run(query2, root_id="prog_langs")
    data = result2.single()
    if data:
        print(f"根节点: {data['c']['name']}")
        print(f"路径数: {len(data['paths'])}")
    
    # 简单的关系查询
    print("\n简单关系查询:")
    query3 = """
    MATCH (c1:Concept {id: $id})-[r]-(c2:Concept)
    RETURN c1.name as source, type(r) as type, c2.name as target
    """
    result3 = session.run(query3, id="prog_langs")
    rels = list(result3)
    print(f"prog_langs 的关系数: {len(rels)}")
    for rel in rels:
        print(f"  {rel['source']} -> {rel['target']} ({rel['type']})")

memory.close()
print("\n调试完成")