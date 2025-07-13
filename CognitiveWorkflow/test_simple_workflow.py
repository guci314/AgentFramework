#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的工作流测试
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from python_core import Agent, get_model("deepseek_chat")
from cognitive_workflow_rule_base import create_production_rule_system
from cognitive_workflow_rule_base.application.cognitive_workflow_agent_wrapper import IntelligentAgentWrapper

def test_simple_workflow():
    """测试简单工作流"""
    
    print("=== 简单工作流测试 ===")
    
    # 1. 创建Agent
    base_coder = Agent(llm=get_model("deepseek_chat"))
    base_coder.api_specification = "代码专家"
    
    coder = IntelligentAgentWrapper(base_agent=base_coder, agent_name="coder")
    
    agents = {"coder": coder}
    
    # 2. 创建工作流系统
    workflow_engine = create_production_rule_system(
        llm=get_model("deepseek_chat"),
        agents=agents
    )
    
    # 3. 简单目标
    goal = "创建一个hello.txt文件，内容是hello world"
    
    print(f"执行目标: {goal}")
    
    try:
        # 只执行第一步：生成规则集
        rule_engine = workflow_engine.rule_engine_service
        rule_generation = rule_engine.rule_generation
        
        print("生成规则集...")
        rule_set = rule_generation.generate_rule_set(goal, workflow_engine.agent_registry)
        print(f"✅ 生成了 {len(rule_set.rules)} 个规则")
        
        # 生成决策
        print("生成决策...")
        global_state = rule_engine.state_service.create_initial_state(goal, "test_workflow")
        decision = rule_generation.make_decision(global_state, rule_set)
        print(f"✅ 决策完成: {decision.decision_type}")
        
        # 如果有选中的规则，尝试执行
        if hasattr(decision, 'selected_rule') and decision.selected_rule:
            print(f"准备执行规则: {decision.selected_rule.name}")
            
            # 测试Agent获取
            agent_service = rule_engine.rule_execution.agent_service
            agent_name = decision.selected_rule.agent_name
            print(f"获取Agent: {agent_name}")
            
            agent = agent_service.get_or_create_agent(agent_name)
            print(f"✅ 成功获取Agent: {type(agent)}")
            
            return True
        else:
            print("⚠️ 没有选中的规则，但规则集生成和决策成功")
            return True
            
    except Exception as e:
        print(f"❌ 工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_workflow()
    if success:
        print("\n🎉 简单工作流测试通过！")
    else:
        print("\n❌ 简单工作流测试失败！")