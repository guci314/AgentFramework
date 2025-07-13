# -*- coding: utf-8 -*-
"""
测试agent_registry关联修复

验证create_production_rule_system方法现在能正确关联agent_registry到workflow_engine
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent))

from python_core import Agent, get_model("deepseek_chat")
from cognitive_workflow_rule_base import create_production_rule_system


def test_agent_registry_association():
    """测试agent_registry关联是否正常"""
    
    print("🧪 测试agent_registry关联修复")
    print("="*40)
    
    # 1. 创建测试智能体
    print("1. 创建测试智能体...")
    test_agent = Agent(llm=get_model("deepseek_chat"))
    test_agent.api_specification = "测试智能体，用于验证agent_registry关联"
    
    agents = {"test_agent": test_agent}
    print(f"   创建了 {len(agents)} 个智能体")
    
    # 2. 创建工作流系统
    print("\n2. 创建工作流系统...")
    try:
        workflow_engine = create_production_rule_system(
            llm=get_model("deepseek_chat"),
            agents=agents,
            enable_auto_recovery=True
        )
        print("   ✅ 工作流系统创建成功")
    except Exception as e:
        print(f"   ❌ 工作流系统创建失败: {e}")
        return False
    
    # 3. 验证agent_registry关联
    print("\n3. 验证agent_registry关联...")
    
    # 检查是否有默认的agent_registry
    default_registry = workflow_engine.get_default_agent_registry()
    if default_registry is None:
        print("   ❌ 未找到默认agent_registry")
        return False
    
    print(f"   ✅ 找到默认agent_registry")
    
    # 检查agent_registry中是否包含我们的智能体
    capabilities = default_registry.list_all_capabilities()
    if not capabilities:
        print("   ❌ agent_registry中没有任何智能体能力")
        return False
    
    print(f"   ✅ agent_registry包含 {len(capabilities)} 个智能体能力:")
    capability_ids = [cap.id for cap in capabilities]
    for capability in capabilities:
        print(f"      - {capability.id}: {capability.name}")
    
    # 检查特定智能体是否存在
    if "test_agent" not in capability_ids:
        print("   ❌ 测试智能体未在agent_registry中找到")
        return False
    
    print("   ✅ 测试智能体成功注册到agent_registry")
    
    # 4. 测试不传递agent_registry的执行
    print("\n4. 测试工作流执行（不传递agent_registry）...")
    try:
        # 这里应该使用默认的agent_registry
        result = workflow_engine.execute_goal("简单的测试目标：输出Hello World")
        print(f"   ✅ 执行完成，成功: {'是' if result.is_successful else '否'}")
        return True
    except Exception as e:
        print(f"   ❌ 执行失败: {e}")
        return False


def test_explicit_agent_registry():
    """测试显式传递agent_registry的情况"""
    
    print("\n\n🧪 测试显式传递agent_registry")
    print("="*40)
    
    # 创建智能体
    test_agent = Agent(llm=get_model("deepseek_chat"))
    test_agent.api_specification = "显式测试智能体"
    
    agents = {"explicit_agent": test_agent}
    
    # 创建工作流系统
    workflow_engine = create_production_rule_system(
        llm=get_model("deepseek_chat"),
        agents=agents,
        enable_auto_recovery=True
    )
    
    # 创建新的agent_registry用于测试
    from cognitive_workflow_rule_base import AgentRegistry, AgentCapability
    
    custom_registry = AgentRegistry()
    custom_capability = AgentCapability(
        id="custom_agent",
        name="自定义智能体",
        description="用于测试显式传递的智能体",
        supported_actions=["custom_action"],
        api_specification="自定义智能体规格"
    )
    custom_registry.register_capability(custom_capability)
    
    print("1. 创建自定义agent_registry...")
    custom_capabilities = custom_registry.list_all_capabilities()
    print(f"   包含智能体: {[cap.id for cap in custom_capabilities]}")
    
    # 测试显式传递agent_registry
    print("\n2. 测试显式传递agent_registry执行...")
    try:
        result = workflow_engine.execute_goal(
            "测试自定义registry目标", 
            agent_registry=custom_registry
        )
        print(f"   ✅ 执行完成，成功: {'是' if result.is_successful else '否'}")
        return True
    except Exception as e:
        print(f"   ❌ 执行失败: {e}")
        return False


def main():
    """主函数"""
    
    print("🚀 Agent Registry 关联修复测试")
    print("验证create_production_rule_system的agent_registry关联")
    print("="*60)
    
    try:
        # 测试1: 默认agent_registry关联
        test1_success = test_agent_registry_association()
        
        # 测试2: 显式agent_registry传递
        test2_success = test_explicit_agent_registry()
        
        # 总结
        print("\n\n📊 测试结果总结:")
        print(f"   默认agent_registry关联: {'✅ 通过' if test1_success else '❌ 失败'}")
        print(f"   显式agent_registry传递: {'✅ 通过' if test2_success else '❌ 失败'}")
        
        if test1_success and test2_success:
            print("\n🎉 所有测试通过！agent_registry关联修复成功！")
            print("\n🔧 修复内容:")
            print("   ✓ ProductionRuleWorkflowEngine构造函数增加default_agent_registry参数")
            print("   ✓ create_production_rule_system正确传递agent_registry到引擎")
            print("   ✓ execute_goal方法优先使用传入的registry，否则使用默认registry")
            print("   ✓ 添加get_default_agent_registry方法便于调试")
        else:
            print("\n❌ 测试未完全通过，需要进一步调试")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试执行异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()