#!/usr/bin/env python
"""
调试关系创建问题
"""

import sys
sys.path.insert(0, '.')

from embodied_cognitive_workflow.memory import Neo4jSemanticMemory, Neo4jConfig
from embodied_cognitive_workflow.memory.neo4j_config import CypherQueries

# 创建Neo4j连接
config = Neo4jConfig(database="neo4j")
memory = Neo4jSemanticMemory(config)

print("调试关系创建")
print("=" * 50)

# 直接使用session创建关系
with memory.driver.session(database=config.database) as session:
    # 检查节点是否存在
    result = session.run("MATCH (n:Concept) WHERE n.id IN ['prog_langs', 'lang_python'] RETURN n.id")
    nodes = list(result)
    print(f"找到节点: {[n['n.id'] for n in nodes]}")
    
    # 尝试直接创建关系
    print("\n尝试直接创建关系:")
    try:
        query = """
        MATCH (c1:Concept {id: $id1}), (c2:Concept {id: $id2})
        CREATE (c1)-[r:INCLUDES {created_at: datetime()}]->(c2)
        RETURN r
        """
        result = session.run(query, id1="prog_langs", id2="lang_python")
        rel = result.single()
        if rel:
            print("关系创建成功!")
        else:
            print("关系创建失败 - 没有返回结果")
    except Exception as e:
        print(f"创建关系出错: {e}")
    
    # 再次检查关系
    result = session.run("MATCH (n1:Concept)-[r]->(n2:Concept) RETURN count(r) as count")
    count = result.single()['count']
    print(f"\n当前关系总数: {count}")
    
    # 使用CypherQueries.CREATE_RELATIONSHIP
    print("\n使用CypherQueries.CREATE_RELATIONSHIP:")
    try:
        # 构建查询
        relationship_type = "INCLUDES"
        query = CypherQueries.CREATE_RELATIONSHIP % relationship_type
        print(f"查询: {query}")
        
        result = session.run(
            query,
            concept_id1="prog_langs",
            concept_id2="lang_javascript",
            properties={}
        )
        rel = result.single()
        if rel:
            print("关系创建成功!")
        else:
            print("关系创建失败 - 没有返回结果")
    except Exception as e:
        print(f"创建关系出错: {e}")
    
    # 最终检查
    print("\n最终检查关系:")
    result = session.run("""
    MATCH (n1:Concept)-[r]->(n2:Concept)
    RETURN n1.id as source, type(r) as type, n2.id as target
    """)
    rels = list(result)
    print(f"找到关系数: {len(rels)}")
    for rel in rels:
        print(f"  {rel['source']} -> {rel['target']} ({rel['type']})")

memory.close()
print("\n调试完成")