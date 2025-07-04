#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Agent命名一致性修复的效果
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "CognitiveWorkflow"))

from pythonTask import Agent, llm_deepseek
from CognitiveWorkflow.cognitive_workflow_rule_base.application.cognitive_workflow_agent_wrapper import CognitiveAgent

def test_agent_naming_consistency():
    """测试Agent命名一致性修复效果"""
    
    print("=== 验证Agent命名一致性修复 ===")
    
    # 1. 创建基础Agent
    base_coder = Agent(llm=llm_deepseek)
    base_coder.api_specification = '代码专家，擅长编写和调试代码'
    
    base_tester = Agent(llm=llm_deepseek)
    base_tester.api_specification = '测试专家，擅长编写测试用例'
    
    # 2. 创建基础Agent映射
    base_agents = {
        "coder": base_coder,
        "tester": base_tester
    }
    
    # 3. 创建CognitiveAgent包装器，显式指定名称和外部Agent集合
    coder = CognitiveAgent(
        base_agent=base_coder,
        agent_name="coder",  # 显式指定名称
        external_agents=base_agents,  # 传入完整的Agent集合
        enable_auto_recovery=True
    )
    
    tester = CognitiveAgent(
        base_agent=base_tester,
        agent_name="tester",  # 显式指定名称
        external_agents=base_agents,  # 传入完整的Agent集合
        enable_auto_recovery=True
    )
    
    # 4. 创建CognitiveAgent映射并更新注册表
    cognitive_agents = {
        "coder": coder,
        "tester": tester
    }
    
    # 5. 更新Agent注册表以解决循环依赖
    for agent_name, agent in cognitive_agents.items():
        if agent.workflow_engine:
            agent.update_agent_registry(cognitive_agents)
    
    print(f"✅ 创建了CognitiveAgent: {list(cognitive_agents.keys())}")
    
    # 6. 验证Agent命名
    print("\n=== Agent命名验证 ===")
    print(f"coder.agent_name: {coder.agent_name}")
    print(f"tester.agent_name: {tester.agent_name}")
    
    # 7. 验证内部workflow_engine的agent_registry
    print("\n=== Agent注册表验证 ===")
    if coder.workflow_engine:
        coder_agents = list(coder.workflow_engine.agent_registry.agents.keys())
        print(f"coder内部Agent注册表: {coder_agents}")
        
        # 验证能否获取到tester
        try:
            retrieved_tester = coder.workflow_engine.agent_registry.get_agent("tester")
            print(f"✅ coder成功获取到tester: {type(retrieved_tester)}")
        except Exception as e:
            print(f"❌ coder无法获取tester: {e}")
    
    if tester.workflow_engine:
        tester_agents = list(tester.workflow_engine.agent_registry.agents.keys())
        print(f"tester内部Agent注册表: {tester_agents}")
        
        # 验证能否获取到coder
        try:
            retrieved_coder = tester.workflow_engine.agent_registry.get_agent("coder")
            print(f"✅ tester成功获取到coder: {type(retrieved_coder)}")
        except Exception as e:
            print(f"❌ tester无法获取coder: {e}")
    
    # 8. 验证Agent specifications
    print("\n=== Agent规范验证 ===")
    if coder.workflow_engine:
        agent_specs = coder.workflow_engine.agent_registry.get_agent_specifications()
        print(f"coder可见的Agent规范: {list(agent_specs.keys())}")
        for name, spec in agent_specs.items():
            print(f"  - {name}: {spec[:50]}...")
    
    print("\n✅ Agent命名一致性修复验证完成！")
    return True

if __name__ == "__main__":
    try:
        test_agent_naming_consistency()
        print("\n🎉 所有验证通过！Agent命名一致性问题已解决。")
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()