#!/usr/bin/env python
"""
运行测试的辅助脚本

解决相对导入问题
"""

import sys
import os
import unittest

# 添加项目路径到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入测试模块
from memory.tests import test_neo4j_integration
from memory.tests import test_semantic_memory_neo4j


def run_neo4j_tests():
    """运行Neo4j相关测试"""
    print("运行Neo4j集成测试")
    print("=" * 50)
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试
    # 1. Neo4j语义记忆测试
    suite.addTests(unittest.TestLoader().loadTestsFromModule(test_semantic_memory_neo4j))
    
    # 2. Neo4j集成测试
    suite.addTests(unittest.TestLoader().loadTestsFromModule(test_neo4j_integration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


def run_specific_test(test_name):
    """运行特定测试"""
    print(f"运行测试: {test_name}")
    print("=" * 50)
    
    if test_name == "unit":
        # 只运行单元测试
        suite = unittest.TestLoader().loadTestsFromTestCase(
            test_semantic_memory_neo4j.TestNeo4jSemanticMemoryUnit
        )
    elif test_name == "integration":
        # 只运行集成测试
        suite = unittest.TestSuite()
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            test_semantic_memory_neo4j.TestNeo4jSemanticMemoryIntegration
        ))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            test_neo4j_integration.TestNeo4jIntegrationWithMemoryManager
        ))
    elif test_name == "performance":
        # 只运行性能测试
        suite = unittest.TestLoader().loadTestsFromTestCase(
            test_semantic_memory_neo4j.TestNeo4jSemanticMemoryPerformance
        )
    elif test_name == "migration":
        # 只运行迁移测试
        suite = unittest.TestLoader().loadTestsFromTestCase(
            test_neo4j_integration.TestNeo4jMigration
        )
    else:
        print(f"未知测试: {test_name}")
        return False
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行Neo4j测试')
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'performance', 'migration'],
        help='要运行的测试类型'
    )
    
    args = parser.parse_args()
    
    # 检查Neo4j连接
    print("检查Neo4j连接...")
    try:
        from neo4j import GraphDatabase
        from memory.neo4j_config import Neo4jConfig
        
        config = Neo4jConfig()
        driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password)
        )
        driver.verify_connectivity()
        driver.close()
        print("✓ Neo4j连接成功\n")
    except Exception as e:
        print(f"✗ Neo4j连接失败: {e}")
        print("\n提示：")
        print("1. 确保Neo4j正在运行")
        print("2. 检查连接配置是否正确")
        print("3. 单元测试不需要Neo4j连接\n")
        
        if args.test_type != 'unit':
            return 1
    
    # 运行测试
    if args.test_type == 'all':
        success = run_neo4j_tests()
    else:
        success = run_specific_test(args.test_type)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())