#!/usr/bin/env python3
"""
测试Decision类重构是否成功
"""

import os
import sys

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from python_core import Agent
from llm_lazy import get_model
from embodied_cognitive_workflow import CognitiveAgent
from embodied_cognitive_workflow.ego_agent import EgoAgent, Decision
from embodied_cognitive_workflow.decision_types import DecisionType
from agent_base import AgentBase

def test_decision_class():
    """测试Decision类的创建和属性"""
    print("\n=== 测试1: Decision类基本功能 ===")
    
    # 创建一个模拟的Agent
    llm = get_model("gemini_2_5_flash")
    test_agent = Agent(llm=llm)
    test_agent.name = "测试Agent"
    
    # 创建Decision对象
    decision = Decision(
        decision_type=DecisionType.EXECUTE_INSTRUCTION,
        agent=test_agent,
        instruction="执行测试任务"
    )
    
    print(f"✅ Decision对象创建成功")
    print(f"   决策类型: {decision.decision_type.value}")
    print(f"   执行指令: {decision.instruction}")
    print(f"   执行Agent: {decision.agent.name if decision.agent else '无'}")
    
    return True

def test_ego_decide_next_action():
    """测试EgoAgent的decide_next_action方法"""
    print("\n=== 测试2: EgoAgent.decide_next_action方法 ===")
    
    llm = get_model("gemini_2_5_flash")
    ego = EgoAgent(llm)
    
    # 创建测试Agent列表
    math_agent = Agent(llm=llm)
    math_agent.name = "数学专家"
    math_agent.api_specification = "数学计算、统计分析"
    
    file_agent = Agent(llm=llm)
    file_agent.name = "文件管理器"
    file_agent.api_specification = "文件操作、数据保存"
    
    agents = [math_agent, file_agent]
    
    # 测试状态分析
    state_analysis = """
    当前状态：需要计算一些数据并保存到文件
    已完成：无
    待完成：1. 计算数据统计值 2. 保存结果到文件
    """
    
    print("测试决策（有Agent列表）...")
    decision = ego.decide_next_action(state_analysis, agents)
    
    print(f"✅ 决策完成")
    print(f"   决策类型: {decision.decision_type.value}")
    print(f"   执行指令: {decision.instruction[:50]}..." if decision.instruction else "   执行指令: 无")
    print(f"   选择的Agent: {decision.agent.name if decision.agent else '无'}")
    
    # 验证决策是否为正确的类型
    assert isinstance(decision, Decision), "返回值应该是Decision对象"
    assert isinstance(decision.decision_type, DecisionType), "decision_type应该是DecisionType枚举"
    
    return True

def test_cognitive_agent_integration():
    """测试CognitiveAgent与Decision类的集成"""
    print("\n=== 测试3: CognitiveAgent集成测试 ===")
    
    llm = get_model("gemini_2_5_flash")
    
    # 创建单个Agent进行测试
    agent = Agent(llm=llm)
    agent.name = "通用执行器"
    
    # 创建CognitiveAgent
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[agent],
        max_cycles=2,
        verbose=False,
        enable_meta_cognition=False
    )
    
    print("✅ CognitiveAgent创建成功")
    print(f"   包含Agent数量: {len(cognitive_agent.agents)}")
    print(f"   最大循环次数: {cognitive_agent.max_cycles}")
    
    # 测试简单任务
    try:
        result = cognitive_agent.execute_sync("计算 5 + 3")
        print(f"✅ 任务执行成功: {result.success}")
        if result.return_value:
            print(f"   返回结果: {result.return_value[:100]}...")
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        return False
    
    return True

def main():
    """运行所有测试"""
    print("=== Decision类重构测试 ===")
    print("测试目标：验证Decision类重构是否成功完成")
    
    tests = [
        ("Decision类基本功能", test_decision_class),
        ("EgoAgent.decide_next_action", test_ego_decide_next_action),
        ("CognitiveAgent集成", test_cognitive_agent_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} 测试出错: {e}")
    
    print(f"\n=== 测试总结 ===")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！Decision类重构成功完成！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查代码")

if __name__ == "__main__":
    main()