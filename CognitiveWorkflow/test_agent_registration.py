#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Agent注册问题
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from python_core import Agent, get_model("deepseek_chat")
from cognitive_workflow_rule_base import create_production_rule_system
from cognitive_workflow_rule_base.application.cognitive_workflow_agent_wrapper import IntelligentAgentWrapper

def test_agent_registration():
    """测试Agent注册过程"""
    
    print("=== Agent注册测试 ===")
    
    # 1. 创建基础Agent
    base_coder = Agent(llm=get_model("deepseek_chat"))
    base_coder.api_specification = "代码专家"
    
    base_tester = Agent(llm=get_model("deepseek_chat"))
    base_tester.api_specification = "测试专家"
    
    # 2. 创建IntelligentAgentWrapper包装器
    coder = IntelligentAgentWrapper(base_agent=base_coder, agent_name="coder")
    tester = IntelligentAgentWrapper(base_agent=base_tester, agent_name="tester")
    
    agents = {
        "coder": coder,
        "tester": tester
    }
    
    print(f"创建的agents字典: {list(agents.keys())}")
    
    # 3. 创建工作流系统
    workflow_engine = create_production_rule_system(
        llm=get_model("deepseek_chat"),
        agents=agents
    )
    
    # 4. 获取AgentRegistry并检查注册状态
    agent_registry = workflow_engine.agent_registry
    registered_agents = list(agent_registry.agents.keys())
    print(f"注册表中的agents: {registered_agents}")
    
    # 5. 测试Agent获取
    try:
        agent_service = workflow_engine.rule_engine_service.rule_execution.agent_service
        coder_agent = agent_service.get_or_create_agent("coder")
        print(f"✅ 成功获取coder: {type(coder_agent)}")
        
        tester_agent = agent_service.get_or_create_agent("tester")
        print(f"✅ 成功获取tester: {type(tester_agent)}")
        
    except Exception as e:
        print(f"❌ 获取Agent失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_agent_registration()
    if success:
        print("\n🎉 Agent注册测试通过！")
    else:
        print("\n❌ Agent注册测试失败！")