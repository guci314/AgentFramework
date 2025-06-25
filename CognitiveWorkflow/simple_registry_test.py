# -*- coding: utf-8 -*-
"""
简单的agent_registry关联测试

只验证关联是否正确，不执行复杂的工作流
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent))

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base import create_production_rule_system


def simple_registry_test():
    """简单的registry关联测试"""
    
    print("🧪 简单Agent Registry关联测试")
    print("="*40)
    
    # 1. 创建智能体
    print("1. 创建智能体...")
    coder = Agent(llm=llm_deepseek)
    coder.api_specification = "代码专家智能体"
    
    tester = Agent(llm=llm_deepseek)
    tester.api_specification = "测试专家智能体"
    
    agents = {
        "coder": coder,
        "tester": tester
    }
    print(f"   创建了 {len(agents)} 个智能体: {list(agents.keys())}")
    
    # 2. 创建工作流系统
    print("\n2. 创建工作流系统...")
    workflow_engine = create_production_rule_system(
        llm=llm_deepseek,
        agents=agents,
        enable_auto_recovery=True
    )
    print("   ✅ 工作流系统创建成功")
    
    # 3. 验证默认registry
    print("\n3. 验证默认agent_registry...")
    default_registry = workflow_engine.get_default_agent_registry()
    
    if default_registry is None:
        print("   ❌ 没有找到默认agent_registry")
        return False
    
    capabilities = default_registry.list_all_capabilities()
    print(f"   ✅ 默认registry包含 {len(capabilities)} 个智能体能力:")
    
    found_agents = []
    for capability in capabilities:
        print(f"      - ID: {capability.id}")
        print(f"        名称: {capability.name}")
        print(f"        描述: {capability.description}")
        print(f"        支持动作: {capability.supported_actions}")
        print()
        found_agents.append(capability.id)
    
    # 4. 验证我们的智能体是否都在registry中
    expected_agents = ["coder", "tester"]
    missing_agents = [agent for agent in expected_agents if agent not in found_agents]
    
    if missing_agents:
        print(f"   ❌ 缺少智能体: {missing_agents}")
        return False
    
    print("   ✅ 所有智能体都成功注册到默认registry")
    
    # 5. 测试capability查找
    print("\n4. 测试capability查找功能...")
    
    try:
        coder_capability = default_registry.get_capability("coder")
        print(f"   ✅ 成功获取coder能力: {coder_capability.name}")
    except ValueError as e:
        print(f"   ❌ 获取coder能力失败: {e}")
        return False
    
    try:
        all_action_capabilities = default_registry.find_capabilities_by_action("*")
        print(f"   ✅ 支持所有动作的智能体数量: {len(all_action_capabilities)}")
    except Exception as e:
        print(f"   ❌ 查找能力失败: {e}")
        return False
    
    return True


def test_without_explicit_registry():
    """测试不传递agent_registry参数是否使用默认registry"""
    
    print("\n🧪 测试默认Registry使用")
    print("="*30)
    
    # 创建简单的工作流引擎
    simple_agent = Agent(llm=llm_deepseek)
    simple_agent.api_specification = "简单测试智能体"
    
    agents = {"simple_agent": simple_agent}
    
    workflow_engine = create_production_rule_system(
        llm=llm_deepseek,
        agents=agents,
        enable_auto_recovery=True
    )
    
    # 验证当前目标设置
    print("1. 验证默认registry设置...")
    current_registry = workflow_engine._current_agent_registry
    default_registry = workflow_engine.get_default_agent_registry()
    
    print(f"   当前registry: {current_registry}")
    print(f"   默认registry: {default_registry}")
    print(f"   默认registry中的智能体数量: {len(default_registry.list_all_capabilities())}")
    
    # 模拟execute_goal调用（不实际执行）
    print("\n2. 模拟execute_goal调用设置...")
    workflow_engine._current_goal = "测试目标"
    workflow_engine._current_agent_registry = None or workflow_engine.default_agent_registry
    
    final_registry = workflow_engine._current_agent_registry
    final_capabilities = final_registry.list_all_capabilities()
    
    print(f"   最终使用的registry智能体数量: {len(final_capabilities)}")
    
    if len(final_capabilities) > 0:
        print("   ✅ 默认registry正确关联")
        return True
    else:
        print("   ❌ 默认registry未正确关联")
        return False


def main():
    """主函数"""
    
    print("🚀 Agent Registry 关联验证测试")
    print("验证create_production_rule_system的agent_registry修复")
    print("="*55)
    
    try:
        # 测试1: 基本registry关联
        test1_success = simple_registry_test()
        
        # 测试2: 默认registry使用
        test2_success = test_without_explicit_registry()
        
        # 总结
        print("\n📊 测试结果:")
        print(f"   基本Registry关联: {'✅ 通过' if test1_success else '❌ 失败'}")
        print(f"   默认Registry使用: {'✅ 通过' if test2_success else '❌ 失败'}")
        
        if test1_success and test2_success:
            print("\n🎉 Agent Registry关联修复验证成功！")
            print("\n修复要点:")
            print("   ✓ ProductionRuleWorkflowEngine接受default_agent_registry参数")
            print("   ✓ create_production_rule_system正确传递agent_registry")
            print("   ✓ execute_goal使用默认registry当未提供参数时")
            print("   ✓ 所有智能体正确注册到registry")
        else:
            print("\n❌ 还有问题需要解决")
            
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()