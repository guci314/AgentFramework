#!/usr/bin/env python
"""
测试导入是否正常工作
"""

import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

print("测试记忆管理系统导入")
print("=" * 50)

# 测试基础导入
try:
    from memory import (
        MemoryManager, 
        WorkingMemory, 
        EpisodicMemory, 
        SemanticMemory,
        TriggerType,
        MemoryLayer,
        Concept,
        NEO4J_AVAILABLE
    )
    print("✓ 基础模块导入成功")
except ImportError as e:
    print(f"✗ 基础模块导入失败: {e}")
    sys.exit(1)

# 测试Neo4j导入
if NEO4J_AVAILABLE:
    try:
        from memory import Neo4jConfig, Neo4jSemanticMemory
        print("✓ Neo4j模块导入成功")
    except ImportError as e:
        print(f"✗ Neo4j模块导入失败: {e}")
else:
    print("! Neo4j模块不可用（可能缺少neo4j-driver）")

# 测试实例化
try:
    # 创建记忆管理器
    mm = MemoryManager()
    print("✓ MemoryManager实例化成功")
    
    # 测试基本功能
    result = mm.process_information("测试信息")
    print("✓ 基本功能测试成功")
    
except Exception as e:
    print(f"✗ 实例化失败: {e}")
    sys.exit(1)

# 测试Neo4j功能（如果可用）
if NEO4J_AVAILABLE:
    try:
        from memory import Neo4jSemanticMemory, Neo4jConfig
        
        # 尝试创建Neo4j实例（可能会失败如果Neo4j未运行）
        config = Neo4jConfig()
        print(f"  Neo4j配置: {config.uri}")
        
        # 注意：这里不实际连接，只是测试类能否导入
        print("✓ Neo4j类可以导入")
        
    except Exception as e:
        print(f"! Neo4j测试跳过: {e}")

print("\n" + "=" * 50)
print("所有导入测试通过！")

# 显示版本信息
from memory import __version__
print(f"\n记忆管理系统版本: {__version__}")

# 运行简单的集成测试
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--test":
    print("\n运行集成测试...")
    
    # 导入测试模块
    from memory.tests import test_neo4j_integration
    import unittest
    
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromModule(test_neo4j_integration)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)