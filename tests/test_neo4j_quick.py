#!/usr/bin/env python
"""
快速测试Neo4j集成

在项目根目录运行此脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("Neo4j集成快速测试")
    print("=" * 50)
    
    # 1. 检查Neo4j driver
    print("\n1. 检查Neo4j driver安装")
    try:
        import neo4j
        print("✓ neo4j-driver已安装")
    except ImportError:
        print("✗ 需要安装neo4j-driver")
        print("  运行: pip install neo4j")
        return 1
    
    # 2. 检查模块导入
    print("\n2. 检查模块导入")
    try:
        from embodied_cognitive_workflow.memory import (
            Neo4jSemanticMemory,
            Neo4jConfig,
            MemoryManager,
            Concept,
            NEO4J_AVAILABLE
        )
        
        if NEO4J_AVAILABLE:
            print("✓ Neo4j模块导入成功")
        else:
            print("✗ Neo4j模块不可用")
            return 1
            
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return 1
    
    # 3. 测试Neo4j连接
    print("\n3. 测试Neo4j连接")
    try:
        config = Neo4jConfig(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="graphiti123!",
            database="neo4j"  # 使用默认数据库
        )
        
        print(f"  URI: {config.uri}")
        print(f"  用户: {config.username}")
        print(f"  数据库: {config.database}")
        
        # 创建语义记忆
        semantic_memory = Neo4jSemanticMemory(config)
        print("✓ Neo4j连接成功")
        
        # 4. 基本功能测试
        print("\n4. 基本功能测试")
        
        # 清空测试数据
        semantic_memory.clear()
        print("  ✓ 清空数据库")
        
        # 添加概念
        concept = Concept(
            id="test_concept_1",
            name="Test Concept",
            category="test",
            attributes={'key': 'value'},
            confidence=0.8,
            domain="testing"
        )
        
        concept_id = semantic_memory.add_concept(concept)
        print(f"  ✓ 添加概念: {concept_id}")
        
        # 搜索
        results = semantic_memory.recall("Test", limit=10)
        print(f"  ✓ 搜索结果: {len(results)} 项")
        
        # 统计
        stats = semantic_memory.get_statistics()
        print(f"  ✓ 统计信息: {stats['total_concepts']} 个概念")
        
        # 5. 记忆管理器集成测试
        print("\n5. 记忆管理器集成测试")
        
        mm = MemoryManager(semantic_memory=semantic_memory)
        print("  ✓ 创建记忆管理器(使用Neo4j)")
        
        # 存储信息
        result = mm.process_information(
            "Neo4j集成测试成功",
            metadata={'importance': 0.8}
        )
        print(f"  ✓ 存储信息: {result['stored_in']}")
        
        # 关闭连接
        semantic_memory.close()
        print("\n✓ 所有测试通过！")
        
        print("\n提示:")
        print("- 访问 http://localhost:7474 查看Neo4j Browser")
        print("- 使用 MATCH (n) RETURN n 查看节点")
        print("- 运行完整测试: python test_memory_system.py")
        
        return 0
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        print("\n可能的原因:")
        print("1. Neo4j未运行")
        print("2. 连接参数错误")
        print("3. 认证失败")
        print("\n启动Neo4j Docker:")
        print("docker run -d \\")
        print("  --name neo4j \\")
        print("  -p 7474:7474 -p 7687:7687 \\")
        print("  -e NEO4J_AUTH=neo4j/graphiti123! \\")
        print("  neo4j:latest")
        
        import traceback
        traceback.print_exc()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())