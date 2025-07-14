"""
Neo4j语义记忆演示

展示如何使用Neo4j作为语义记忆的持久化存储
"""

import os
from datetime import datetime

from memory_manager import MemoryManager, MemoryLayer
from interfaces import TriggerType, Concept
from semantic_memory_neo4j import Neo4jSemanticMemory
from neo4j_config import Neo4jConfig


def demo_neo4j_basic():
    """基础Neo4j功能演示"""
    print("=== Neo4j语义记忆基础演示 ===\n")
    
    # 创建Neo4j配置
    config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="graphiti123!",
        database="demo",
        create_indexes=True
    )
    
    # 创建Neo4j语义记忆
    semantic_memory = Neo4jSemanticMemory(config)
    
    # 清空演示数据
    semantic_memory.clear()
    print("已清空演示数据库")
    
    # 1. 添加概念
    print("\n1. 添加编程语言概念:")
    
    languages = [
        Concept(
            id="python",
            name="Python",
            category="programming_language",
            attributes={
                'paradigm': 'multi-paradigm',
                'typing': 'dynamic',
                'use_cases': ['web', 'data science', 'automation'],
                'year': 1991
            },
            confidence=0.95,
            domain="software_development"
        ),
        Concept(
            id="javascript",
            name="JavaScript",
            category="programming_language",
            attributes={
                'paradigm': 'multi-paradigm',
                'typing': 'dynamic',
                'use_cases': ['web', 'mobile', 'server'],
                'year': 1995
            },
            confidence=0.93,
            domain="software_development"
        ),
        Concept(
            id="rust",
            name="Rust",
            category="programming_language",
            attributes={
                'paradigm': 'multi-paradigm',
                'typing': 'static',
                'use_cases': ['systems', 'web assembly', 'embedded'],
                'year': 2010
            },
            confidence=0.90,
            domain="software_development"
        )
    ]
    
    for lang in languages:
        semantic_memory.add_concept(lang)
        print(f"  添加: {lang.name}")
    
    # 2. 创建关系
    print("\n2. 创建概念关系:")
    
    # 添加框架概念
    frameworks = [
        ("django", "Django", "python", "Web framework for Python"),
        ("react", "React", "javascript", "UI library for JavaScript"),
        ("nodejs", "Node.js", "javascript", "JavaScript runtime")
    ]
    
    for fid, fname, lang_id, desc in frameworks:
        framework = Concept(
            id=fid,
            name=fname,
            category="framework",
            attributes={'description': desc},
            confidence=0.85,
            domain="software_development"
        )
        semantic_memory.add_concept(framework)
        semantic_memory.create_relationship(fid, lang_id, "BUILT_WITH")
        print(f"  {fname} -> BUILT_WITH -> {lang_id}")
    
    # 3. 搜索功能
    print("\n3. 搜索概念:")
    
    search_terms = ["Python", "framework", "web"]
    for term in search_terms:
        results = semantic_memory.recall(term, limit=5)
        print(f"  搜索 '{term}': 找到 {len(results)} 个结果")
        for item in results[:3]:
            print(f"    - {item.content.get('name', 'Unknown')}")
    
    # 4. 知识图谱
    print("\n4. 构建知识图谱:")
    
    # 添加根概念
    root = Concept(
        id="tech_stack",
        name="Modern Tech Stack",
        category="domain",
        attributes={'description': 'Common technology stack'},
        confidence=1.0
    )
    root_id = semantic_memory.add_concept(root)
    
    # 连接到编程语言
    for lang in languages:
        semantic_memory.create_relationship(root_id, lang.id, "INCLUDES")
    
    # 获取知识图谱
    graph = semantic_memory.get_knowledge_graph(root_id, depth=2)
    print(f"  节点数: {len(graph['nodes'])}")
    print(f"  关系数: {len(graph['edges'])}")
    print(f"  根节点: {graph['root']}")
    
    # 5. 统计信息
    print("\n5. 数据库统计:")
    stats = semantic_memory.get_statistics()
    print(f"  总概念数: {stats['total_concepts']}")
    print(f"  总关系数: {stats['total_relationships']}")
    print(f"  平均置信度: {stats['avg_confidence']:.3f}")
    print(f"  类别: {', '.join(stats['categories'][:5])}")
    
    # 关闭连接
    semantic_memory.close()
    print("\n演示完成，连接已关闭")


def demo_memory_manager_with_neo4j():
    """使用Neo4j的记忆管理器演示"""
    print("\n\n=== 记忆管理器 + Neo4j 演示 ===\n")
    
    # 创建Neo4j语义记忆
    config = Neo4jConfig(
        database="demo_manager",
        create_indexes=True
    )
    neo4j_semantic = Neo4jSemanticMemory(config)
    neo4j_semantic.clear()
    
    # 创建记忆管理器
    mm = MemoryManager(
        semantic_memory=neo4j_semantic,
        auto_promote=True
    )
    
    print("1. 处理项目开发过程:")
    
    # 模拟项目开发过程
    project_events = [
        ("开始新项目：电商平台", TriggerType.STATE_CHANGE, {'project': 'ecommerce', 'phase': 'init'}),
        ("选择技术栈：Python + Django", TriggerType.DECISION, {'project': 'ecommerce', 'tech': 'django'}),
        ("遇到性能问题：数据库查询慢", TriggerType.ERROR, {'project': 'ecommerce', 'issue': 'performance'}),
        ("解决方案：添加缓存层", TriggerType.DECISION, {'project': 'ecommerce', 'solution': 'caching'}),
        ("完成用户认证模块", TriggerType.MILESTONE, {'project': 'ecommerce', 'module': 'auth'}),
    ]
    
    for event, trigger, metadata in project_events:
        result = mm.process_information(
            event,
            trigger_type=trigger,
            metadata={**metadata, 'importance': 0.7}
        )
        print(f"  处理: {event}")
        print(f"    存储在: {result['stored_in']}")
    
    # 2. 模拟重复模式（触发语义提取）
    print("\n2. 创建重复模式:")
    
    # 多个项目都遇到类似问题
    for i in range(4):
        mm.episodic.store_episode(
            event="API响应时间过长",
            context={
                'project': f'project_{i}',
                'api_endpoint': '/api/products',
                'response_time': f'{2 + i*0.5}s',
                'solution': '实现分页和缓存'
            },
            outcomes={'improved': True, 'new_response_time': '200ms'}
        )
    
    print("  创建了4个相似的性能优化案例")
    
    # 3. 分析模式
    print("\n3. 模式分析:")
    patterns = mm.analyze_memory_patterns(min_pattern_occurrences=3)
    
    if patterns['episodic_patterns']:
        print(f"  发现 {len(patterns['episodic_patterns'])} 个模式")
        for pattern in patterns['episodic_patterns'][:2]:
            print(f"    - {pattern['pattern']}: 出现 {pattern['occurrences']} 次")
    
    # 4. 跨层搜索
    print("\n4. 跨层记忆搜索:")
    
    search_queries = ["性能", "缓存", "API"]
    for query in search_queries:
        results = mm.recall_with_context(query)
        print(f"\n  搜索 '{query}':")
        for layer, items in results.items():
            if items:
                print(f"    {layer}: {len(items)} 个结果")
    
    # 5. 查看Neo4j中的语义知识
    print("\n5. Neo4j中的语义知识:")
    
    # 直接从Neo4j查询
    concepts = neo4j_semantic.get_concepts_by_category("pattern")
    print(f"  模式类概念: {len(concepts)} 个")
    
    all_concepts = neo4j_semantic.list_all(limit=20)
    print(f"  总概念数: {len(all_concepts)}")
    
    # 显示一些概念
    print("\n  部分概念列表:")
    for concept in all_concepts[:5]:
        item = concept.content
        print(f"    - {item.get('name', 'Unknown')} ({item.get('category', 'unknown')})")
    
    # 6. 清理
    print("\n6. 清理并关闭:")
    neo4j_semantic.close()
    print("  演示完成")


def demo_migration():
    """演示从内存迁移到Neo4j"""
    print("\n\n=== 内存到Neo4j迁移演示 ===\n")
    
    # 1. 创建内存版本
    from semantic_memory import SemanticMemory
    
    print("1. 创建内存版本的语义记忆:")
    in_memory = SemanticMemory()
    
    # 添加一些概念
    concepts = [
        Concept(
            id="ml_basics",
            name="Machine Learning Basics",
            category="knowledge",
            attributes={'topics': ['algorithms', 'data', 'models']},
            confidence=0.9,
            domain="ai"
        ),
        Concept(
            id="neural_nets",
            name="Neural Networks",
            category="knowledge",
            attributes={'topics': ['deep learning', 'backprop', 'layers']},
            confidence=0.85,
            domain="ai"
        )
    ]
    
    for concept in concepts:
        in_memory.add_concept(concept)
    print(f"  添加了 {len(concepts)} 个概念到内存")
    
    # 2. 创建Neo4j版本
    print("\n2. 创建Neo4j版本:")
    config = Neo4jConfig(database="migration_demo")
    neo4j_memory = Neo4jSemanticMemory(config)
    neo4j_memory.clear()
    
    # 3. 迁移数据
    print("\n3. 迁移概念到Neo4j:")
    
    # 获取所有内存中的概念
    migrated_count = 0
    for category, concept_list in in_memory.category_index.items():
        for concept in concept_list:
            neo4j_memory.add_concept(concept)
            migrated_count += 1
            print(f"  迁移: {concept.name}")
    
    print(f"\n  成功迁移 {migrated_count} 个概念")
    
    # 4. 验证
    print("\n4. 验证迁移结果:")
    
    # 检查Neo4j中的概念
    neo4j_concepts = neo4j_memory.list_all()
    print(f"  Neo4j中的概念数: {len(neo4j_concepts)}")
    
    # 比较搜索结果
    test_query = "learning"
    in_memory_results = in_memory.recall(test_query)
    neo4j_results = neo4j_memory.recall(test_query)
    
    print(f"\n  搜索 '{test_query}':")
    print(f"    内存版本: {len(in_memory_results)} 个结果")
    print(f"    Neo4j版本: {len(neo4j_results)} 个结果")
    
    # 5. 清理
    neo4j_memory.close()
    print("\n迁移演示完成")


def main():
    """主函数"""
    print("Neo4j语义记忆完整演示")
    print("=" * 50)
    
    # 检查Neo4j是否可用
    try:
        from neo4j import GraphDatabase
        test_config = Neo4jConfig()
        driver = GraphDatabase.driver(
            test_config.uri,
            auth=(test_config.username, test_config.password)
        )
        driver.verify_connectivity()
        driver.close()
        print("✓ Neo4j连接成功\n")
    except Exception as e:
        print(f"✗ Neo4j连接失败: {e}")
        print("请确保Neo4j正在运行，并且凭据正确")
        print(f"URI: {test_config.uri}")
        print(f"用户名: {test_config.username}")
        return
    
    try:
        # 运行各个演示
        demo_neo4j_basic()
        demo_memory_manager_with_neo4j()
        demo_migration()
        
        print("\n" + "=" * 50)
        print("所有演示完成！")
        print("\n提示：")
        print("1. 可以使用Neo4j Browser查看图数据")
        print("2. 访问 http://localhost:7474")
        print("3. 使用 MATCH (n) RETURN n 查看所有节点")
        
    except Exception as e:
        print(f"\n演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()