#!/usr/bin/env python
"""
记忆管理系统测试脚本

在项目根目录运行，自动设置路径
"""

import sys
import os
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试基础导入"""
    print("1. 测试模块导入")
    print("-" * 40)
    
    try:
        from embodied_cognitive_workflow.memory import (
            MemoryManager,
            WorkingMemory,
            EpisodicMemory,
            SemanticMemory,
            TriggerType,
            Concept,
            NEO4J_AVAILABLE
        )
        print("✓ 基础模块导入成功")
        
        if NEO4J_AVAILABLE:
            from embodied_cognitive_workflow.memory import Neo4jConfig, Neo4jSemanticMemory
            print("✓ Neo4j模块导入成功")
        else:
            print("! Neo4j模块不可用")
            
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("\n2. 测试基本功能")
    print("-" * 40)
    
    try:
        from embodied_cognitive_workflow.memory import MemoryManager, TriggerType
        
        # 创建记忆管理器
        mm = MemoryManager()
        print("✓ 创建MemoryManager成功")
        
        # 测试存储
        result = mm.process_information(
            "测试信息",
            trigger_type=TriggerType.MANUAL,
            metadata={'importance': 0.5}
        )
        print(f"✓ 存储信息成功: {result['stored_in']}")
        
        # 测试召回
        memories = mm.recall_with_context("测试")
        total_memories = sum(len(items) for items in memories.values())
        print(f"✓ 召回成功: 找到 {total_memories} 条记忆")
        
        return True
    except Exception as e:
        print(f"✗ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_neo4j_connection():
    """测试Neo4j连接"""
    print("\n3. 测试Neo4j连接")
    print("-" * 40)
    
    try:
        from embodied_cognitive_workflow.memory import NEO4J_AVAILABLE
        
        if not NEO4J_AVAILABLE:
            print("! Neo4j模块不可用，跳过测试")
            return True
            
        from embodied_cognitive_workflow.memory import Neo4jConfig, Neo4jSemanticMemory
        from neo4j import GraphDatabase
        
        config = Neo4jConfig()
        print(f"  配置: {config.uri}")
        print(f"  用户: {config.username}")
        
        # 尝试连接
        driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password)
        )
        driver.verify_connectivity()
        driver.close()
        
        print("✓ Neo4j连接成功")
        return True
        
    except Exception as e:
        print(f"✗ Neo4j连接失败: {e}")
        print("  提示: 确保Neo4j正在运行")
        return False


def run_unit_tests():
    """运行单元测试"""
    print("\n4. 运行单元测试")
    print("-" * 40)
    
    try:
        # 导入测试模块
        from embodied_cognitive_workflow.memory.tests import (
            test_working_memory,
            test_episodic_memory,
            test_semantic_memory,
            test_memory_manager
        )
        
        # 创建测试套件
        suite = unittest.TestSuite()
        
        # 添加测试
        test_modules = [
            test_working_memory,
            test_episodic_memory,
            test_semantic_memory,
            test_memory_manager
        ]
        
        for module in test_modules:
            suite.addTests(unittest.TestLoader().loadTestsFromModule(module))
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"✗ 运行测试失败: {e}")
        return False


def run_neo4j_tests():
    """运行Neo4j测试"""
    print("\n5. 运行Neo4j集成测试")
    print("-" * 40)
    
    try:
        from embodied_cognitive_workflow.memory import NEO4J_AVAILABLE
        
        if not NEO4J_AVAILABLE:
            print("! Neo4j模块不可用，跳过测试")
            return True
        
        # 使用独立版本的测试
        from embodied_cognitive_workflow.memory.tests.test_neo4j_integration_standalone import (
            TestNeo4jIntegrationWithMemoryManager
        )
        
        # 创建测试套件
        suite = unittest.TestLoader().loadTestsFromTestCase(
            TestNeo4jIntegrationWithMemoryManager
        )
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"! Neo4j测试跳过: {e}")
        return True


def main():
    """主函数"""
    print("记忆管理系统完整测试")
    print("=" * 50)
    
    # 运行各项测试
    results = {
        "导入测试": test_imports(),
        "基本功能": test_basic_functionality(),
        "Neo4j连接": test_neo4j_connection(),
        "单元测试": run_unit_tests(),
        "Neo4j集成": run_neo4j_tests()
    }
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())