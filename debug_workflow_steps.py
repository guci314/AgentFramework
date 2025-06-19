#!/usr/bin/env python3
"""
调试工作流步骤执行顺序
==================

检查calculator工作流的步骤定义和执行顺序。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from pythonTask import Agent
from langchain_openai import ChatOpenAI


def debug_workflow_steps():
    """调试工作流步骤"""
    
    print("🔍 调试calculator工作流步骤")
    print("=" * 60)
    
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 请设置DEEPSEEK_API_KEY环境变量")
        return
    
    # 创建LLM和智能体
    llm = ChatOpenAI(
        temperature=0,
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        max_tokens=8192
    )
    
    coder_agent = Agent(llm=llm, stateful=True)
    tester_agent = Agent(llm=llm, stateful=True)
    
    agent_v3 = MultiStepAgent_v3(
        llm=llm,
        registered_agents=[
            RegisteredAgent("coder", coder_agent, "专业编程智能体"),
            RegisteredAgent("tester", tester_agent, "专业测试智能体")
        ],
        use_mock_evaluator=True
    )
    
    # 生成工作流规划
    test_instruction = """
    实现一个计算器类Calculator，保存到文件calculator.py中。
    编写测试用例，保存到文件test_calculator.py中。
    运行测试用例。
    如果测试用例失败，则修复代码，并重新运行测试用例。
    如果测试用例成功，则结束。
    """
    
    workflow_definition = agent_v3._generate_workflow_plan(test_instruction)
    
    print(f"生成的工作流包含 {len(workflow_definition.steps)} 个步骤:")
    print()
    
    for i, step in enumerate(workflow_definition.steps, 1):
        print(f"{i}. 步骤 {step.id}: {step.name}")
        print(f"   智能体: {step.agent_name}")
        print(f"   指令: {step.instruction[:100]}...")
        
        if step.control_flow:
            cf = step.control_flow
            print(f"   控制流: {cf.type.value}")
            
            if cf.type.value == "conditional":
                print(f"     成功→ {cf.success_next}")
                print(f"     失败→ {cf.failure_next}")
                if getattr(cf, 'ai_evaluate_test_result', False):
                    print(f"     AI评估: True (阈值: {getattr(cf, 'ai_confidence_threshold', 'N/A')})")
            
            elif cf.type.value == "loop":
                print(f"     循环目标: {cf.loop_target}")
                print(f"     最大迭代: {cf.max_iterations}")
                print(f"     循环条件: {cf.loop_condition}")
                print(f"     退出路径: {getattr(cf, 'exit_on_max', 'N/A')}")
            
            elif cf.type.value == "sequential":
                print(f"     下一步: {cf.success_next}")
        else:
            print(f"   控制流: 无")
        
        print()
    
    # 分析循环路径
    print("🔄 循环路径分析:")
    
    test_step = None
    fix_step = None
    
    for step in workflow_definition.steps:
        if step.control_flow and step.control_flow.type.value == "conditional":
            if "test" in step.name.lower() or "run" in step.instruction.lower():
                test_step = step
        elif step.control_flow and step.control_flow.type.value == "loop":
            fix_step = step
    
    if test_step and fix_step:
        print(f"测试步骤: {test_step.id} ({test_step.name})")
        print(f"  失败时跳转到: {test_step.control_flow.failure_next}")
        print(f"修复步骤: {fix_step.id} ({fix_step.name})")  
        print(f"  循环回到: {fix_step.control_flow.loop_target}")
        print(f"  最大循环: {fix_step.control_flow.max_iterations}")
        
        if (test_step.control_flow.failure_next == fix_step.id and 
            fix_step.control_flow.loop_target == test_step.id):
            print("✅ 循环路径配置正确")
        else:
            print("❌ 循环路径配置有问题")
    else:
        print("❌ 未找到标准的测试-修复循环模式")


if __name__ == "__main__":
    debug_workflow_steps()