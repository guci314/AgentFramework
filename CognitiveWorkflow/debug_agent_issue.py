#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Agent获取问题的脚本
"""

import sys
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir / "CognitiveWorkflow"
sys.path.append(str(project_root.parent))

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base import create_production_rule_system
from cognitive_workflow_rule_base.cognitive_workflow_agent_wrapper import CognitiveAgent

def test_agent_registry_issue():
    """测试Agent注册表问题"""
    
    print("=== 调试Agent获取问题 ===")
    
    # 1. 创建基础Agent
    base_coder = Agent(llm=llm_deepseek)
    base_coder.api_specification = '代码专家，擅长编写和调试代码'
    
    base_tester = Agent(llm=llm_deepseek)
    base_tester.api_specification = '测试专家，擅长编写测试用例'
    
    # 2. 创建CognitiveAgent包装器 - 显式指定名称
    coder = CognitiveAgent(
        base_agent=base_coder,
        agent_name="coder",
        enable_auto_recovery=True
    )
    
    tester = CognitiveAgent(
        base_agent=base_tester,
        agent_name="tester", 
        enable_auto_recovery=True
    )
    
    print(f"CognitiveAgent名称: coder={coder.agent_name}, tester={tester.agent_name}")
    
    # 3. 创建外部workflow_engine
    agents = {"coder": coder, "tester": tester}
    workflow_engine = create_production_rule_system(
        llm=llm_deepseek,
        agents=agents,
        enable_auto_recovery=True
    )
    
    print(f"外部workflow_engine的agent_registry: {list(workflow_engine.agent_registry.agents.keys())}")
    
    # 4. 检查各层级的AgentService
    print("\n=== 检查AgentService层级结构 ===")
    
    # 外部workflow_engine的AgentService
    external_agent_service = workflow_engine.rule_engine_service.rule_execution.agent_service
    print(f"外部AgentService的agent_registry: {list(external_agent_service.agent_registry.agents.keys())}")
    
    # CognitiveAgent内部workflow_engine的AgentService
    coder_agent_service = coder.workflow_engine.rule_engine_service.rule_execution.agent_service
    print(f"coder内部AgentService的agent_registry: {list(coder_agent_service.agent_registry.agents.keys())}")
    
    tester_agent_service = tester.workflow_engine.rule_engine_service.rule_execution.agent_service  
    print(f"tester内部AgentService的agent_registry: {list(tester_agent_service.agent_registry.agents.keys())}")
    
    # 5. 测试Agent获取
    print("\n=== 测试Agent获取 ===")
    
    try:
        # 外部AgentService获取coder
        external_coder = external_agent_service.get_or_create_agent("coder")
        print(f"✅ 外部AgentService成功获取coder: {type(external_coder)}")
    except Exception as e:
        print(f"❌ 外部AgentService获取coder失败: {e}")
    
    try:
        # coder内部AgentService获取coder
        internal_coder = coder_agent_service.get_or_create_agent("coder")
        print(f"✅ coder内部AgentService成功获取coder: {type(internal_coder)}")
    except Exception as e:
        print(f"❌ coder内部AgentService获取coder失败: {e}")
        
    try:
        # coder内部AgentService获取tester（应该失败）
        internal_tester = coder_agent_service.get_or_create_agent("tester")
        print(f"❌ coder内部AgentService意外成功获取tester: {type(internal_tester)}")
    except Exception as e:
        print(f"✅ coder内部AgentService正确地无法获取tester: {e}")
    
    # 6. 模拟问题：当coder执行需要tester的任务时
    print("\n=== 模拟多Agent协作问题 ===")
    print("如果生成的规则要求使用tester，但当前执行环境是coder的内部workflow_engine")
    print("那么就会出现'无法获取Agent tester: 未找到智能体: tester，可用Agents: [coder]'")
    
    return {
        'external_workflow_engine': workflow_engine,
        'coder': coder,
        'tester': tester
    }

if __name__ == "__main__":
    test_agent_registry_issue()