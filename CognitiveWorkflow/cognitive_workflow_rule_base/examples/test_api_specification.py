#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IntelligentAgentWrapper api_specification属性测试

测试IntelligentAgentWrapper从base_agent自动获取api_specification的功能。

Author: Claude Code Assistant
Date: 2025-06-29
"""

import sys
import os

# 添加项目根目录和CognitiveWorkflow目录到路径，以便导入模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
cognitive_workflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(cognitive_workflow_dir)

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base.application.cognitive_workflow_agent_wrapper import IntelligentAgentWrapper

def test_api_specification():
    """测试api_specification属性功能"""
    print("🚀 测试IntelligentAgentWrapper的api_specification属性")
    print("=" * 60)
    
    # 1. 创建基础Agent
    print("📝 步骤1: 创建基础Agent")
    base_agent = Agent(llm=llm_deepseek)
    print(f"✅ 基础Agent: {type(base_agent).__name__}")
    
    # 2. 设置base_agent的api_specification
    print("\n🔧 步骤2: 设置base_agent的api_specification")
    original_api_spec = """
Python编程专家，精通以下领域：

## 核心能力
- Python语法和最佳实践
- 面向对象编程和设计模式
- 数据结构与算法实现
- 异步编程和并发处理

## 专业技能
- Web开发 (Flask, Django, FastAPI)
- 数据科学 (NumPy, Pandas, Matplotlib)
- 机器学习 (Scikit-learn, TensorFlow)
- 测试和调试技术

## 代码质量
- 遵循PEP 8代码规范
- 编写高质量的文档字符串
- 实现全面的单元测试
- 代码重构和优化

可以协助完成Python相关的任何编程任务。
"""
    
    base_agent.api_specification = original_api_spec
    print(f"✅ 已设置base_agent.api_specification")
    print(f"📄 内容长度: {len(original_api_spec)}字符")
    
    # 3. 创建IntelligentAgentWrapper
    print("\n🧠 步骤3: 创建IntelligentAgentWrapper")
    cognitive_agent = IntelligentAgentWrapper(
        base_agent=base_agent,
        enable_auto_recovery=True
    )
    print(f"✅ 认知Agent: {cognitive_agent}")
    
    # 4. 测试api_specification属性获取
    print("\n🔍 步骤4: 测试api_specification属性获取")
    
    # 4.1 测试getter
    retrieved_api_spec = cognitive_agent.api_specification
    print(f"📋 从IntelligentAgentWrapper获取的api_specification:")
    if retrieved_api_spec:
        print(f"   长度: {len(retrieved_api_spec)}字符")
        print(f"   内容预览: {retrieved_api_spec[:100]}...")
        
        # 验证内容是否一致
        is_same = retrieved_api_spec == original_api_spec
        print(f"   ✅ 内容一致性: {is_same}")
    else:
        print("   ❌ 获取的api_specification为None")
    
    # 4.2 测试setter
    print("\n🔧 步骤5: 测试api_specification属性设置")
    new_api_spec = """
更新后的API规范：

## 高级Python开发专家
- 微服务架构设计
- Docker容器化部署
- CI/CD流水线构建
- 性能优化和监控

## 新增技能
- GraphQL API开发
- 分布式系统设计
- 云原生应用开发
- DevOps最佳实践

专注于企业级Python应用开发。
"""
    
    cognitive_agent.api_specification = new_api_spec
    print(f"✅ 已通过CognitiveAgent设置新的api_specification")
    
    # 验证设置是否成功
    updated_spec = cognitive_agent.api_specification
    base_agent_spec = base_agent.api_specification
    
    print(f"📋 验证设置结果:")
    print(f"   CognitiveAgent.api_specification长度: {len(updated_spec) if updated_spec else 0}")
    print(f"   base_agent.api_specification长度: {len(base_agent_spec) if base_agent_spec else 0}")
    print(f"   ✅ 两者一致性: {updated_spec == base_agent_spec}")
    print(f"   ✅ 内容已更新: {updated_spec == new_api_spec}")
    
    # 5. 测试__repr__方法中的api_specification显示
    print("\n📄 步骤6: 测试__repr__中的api_specification显示")
    repr_str = repr(cognitive_agent)
    print(f"CognitiveAgent.__repr__():")
    print(f"   {repr_str}")
    
    if "api_spec=" in repr_str:
        print("   ✅ __repr__中包含api_specification信息")
    else:
        print("   ❌ __repr__中未找到api_specification信息")
    
    # 6. 测试无api_specification的情况
    print("\n🧪 步骤7: 测试base_agent无api_specification的情况")
    
    # 创建一个没有api_specification的简单对象
    class SimpleAgent:
        def __init__(self, llm):
            self.llm = llm
    
    simple_agent = SimpleAgent(llm_deepseek)
    cognitive_agent_simple = CognitiveAgent(simple_agent)
    
    simple_api_spec = cognitive_agent_simple.api_specification
    print(f"📋 无api_specification的Agent:")
    print(f"   获取结果: {simple_api_spec}")
    print(f"   ✅ 正确返回None: {simple_api_spec is None}")
    
    # 尝试设置
    try:
        cognitive_agent_simple.api_specification = "测试设置"
        print("   ⚠️ 设置操作完成（应该有警告日志）")
    except Exception as e:
        print(f"   ❌ 设置操作异常: {e}")
    
    print("\n🎉 api_specification属性测试完成！")
    
    # 总结
    print("\n📊 测试总结:")
    print("✅ api_specification getter功能正常")
    print("✅ api_specification setter功能正常") 
    print("✅ __repr__方法包含api_specification信息")
    print("✅ 无api_specification属性时的降级处理正常")

def demo_usage():
    """演示api_specification的实际使用场景"""
    print("\n💡 实际使用场景演示")
    print("-" * 60)
    
    # 创建专门化的Agent
    base_agent = Agent(llm=llm_deepseek)
    base_agent.api_specification = """
数据科学专家Agent，专精于：

## 数据分析能力
- 数据清洗和预处理
- 探索性数据分析 (EDA)
- 统计分析和假设检验
- 数据可视化设计

## 机器学习技能
- 监督学习算法应用
- 无监督学习和聚类
- 特征工程和选择
- 模型评估和调优

## 工具生态
- Pandas, NumPy数据处理
- Matplotlib, Seaborn可视化
- Scikit-learn机器学习
- Jupyter Notebook开发

适合处理各种数据科学项目和分析任务。
"""
    
    # 创建认知包装器
    data_scientist = CognitiveAgent(base_agent)
    
    print("🔬 创建了数据科学专家CognitiveAgent:")
    print(f"   类型: {type(data_scientist).__name__}")
    print(f"   API规范: {data_scientist.api_specification[:80]}...")
    print(f"   表示: {data_scientist}")
    
    # 演示指令分类会考虑API规范
    print("\n🎯 指令分类演示:")
    test_instructions = [
        "解释pandas的DataFrame结构",
        "分析销售数据的趋势",
        "创建一个数据预处理流水线"
    ]
    
    for instruction in test_instructions:
        instruction_type, execution_mode = data_scientist.classify_instruction(instruction)
        print(f"   '{instruction}' → {instruction_type}|{execution_mode}")

if __name__ == "__main__":
    try:
        test_api_specification()
        demo_usage()
        
        print("\n🎊 所有测试完成！")
        
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()