#!/usr/bin/env python3
"""
测试执行历史功能
===============

验证MultiStepAgent_v3在执行步骤时是否正确地添加了
之前步骤的执行历史上下文。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from static_workflow.workflow_definitions import WorkflowDefinition, WorkflowStep, StepExecutionStatus
from python_core import Agent
from langchain_openai import ChatOpenAI
from agent_base import Result

def create_test_workflow():
    """创建测试工作流定义"""
    
    test_workflow_data = {
        "workflow_metadata": {
            "name": "test_history_workflow",
            "version": "1.0",
            "description": "测试执行历史的工作流",
            "author": "test"
        },
        "global_variables": {
            "max_retries": 3
        },
        "steps": [
            {
                "id": "step1",
                "name": "创建基础代码",
                "agent_name": "coder",
                "instruction": "创建一个简单的add函数，返回两个数的和",
                "instruction_type": "execution",
                "expected_output": "包含add函数的Python代码",
                "control_flow": {
                    "type": "sequential",
                    "success_next": "step2"
                }
            },
            {
                "id": "step2", 
                "name": "编写测试代码",
                "agent_name": "tester",
                "instruction": "为前面创建的add函数编写测试用例",
                "instruction_type": "execution",
                "expected_output": "测试add函数的代码",
                "control_flow": {
                    "type": "sequential",
                    "success_next": "step3"
                }
            },
            {
                "id": "step3",
                "name": "生成文档",
                "agent_name": "writer",
                "instruction": "基于前面的代码和测试，编写简单的使用文档",
                "instruction_type": "information",
                "expected_output": "使用文档",
                "control_flow": {
                    "type": "terminal"
                }
            }
        ]
    }
    
    return test_workflow_data

def test_execution_history():
    """测试执行历史功能"""
    
    print("📜 测试执行历史功能")
    print("=" * 50)
    
    # 创建测试LLM（可以是虚拟的）
    llm = ChatOpenAI(
        temperature=0,
        model="deepseek-chat", 
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY') or "test_key",
        max_tokens=1000
    )
    
    # 创建测试智能体
    coder_agent = Agent(llm=llm, stateful=True)
    tester_agent = Agent(llm=llm, stateful=True)
    writer_agent = Agent(llm=llm, stateful=True)
    
    # 创建MultiStepAgent_v3实例
    agent_v3 = MultiStepAgent_v3(
        llm=llm,
        registered_agents=[
            RegisteredAgent("coder", coder_agent, "编程智能体"),
            RegisteredAgent("tester", tester_agent, "测试智能体"),
            RegisteredAgent("writer", writer_agent, "文档智能体")
        ]
    )
    
    # 创建测试工作流
    workflow_data = create_test_workflow()
    workflow_def = agent_v3.workflow_loader.load_from_dict(workflow_data)
    agent_v3.workflow_definition = workflow_def
    
    print(f"✅ 创建了包含 {len(workflow_def.steps)} 个步骤的测试工作流")
    
    # 模拟第一步已完成
    step1 = workflow_def.steps[0]
    step1.status = StepExecutionStatus.COMPLETED
    step1.result = Result(
        success=True,
        code="def add(a, b):\n    return a + b",
        stdout="Successfully created add function",
        stderr=None,
        return_value="add function created"
    )
    
    print(f"✅ 模拟第一步 '{step1.name}' 已完成")
    
    # 测试第二步的指令构建
    step2 = workflow_def.steps[1]
    print(f"\n📋 测试第二步 '{step2.name}' 的指令构建...")
    
    enhanced_instruction = agent_v3._build_enhanced_instruction(step2)
    
    print(f"\n📄 生成的增强指令:")
    print("=" * 50)
    print(enhanced_instruction)
    print("=" * 50)
    
    # 验证指令内容
    checks = [
        ("包含当前步骤信息", step2.name in enhanced_instruction and step2.id in enhanced_instruction),
        ("包含执行历史标题", "执行历史上下文" in enhanced_instruction),
        ("包含第一步信息", step1.name in enhanced_instruction and step1.id in enhanced_instruction),
        ("包含第一步结果", "Successfully created add function" in enhanced_instruction),
        ("包含第一步代码", "def add(a, b)" in enhanced_instruction),
        ("包含重要提示", "基于上述执行历史" in enhanced_instruction),
        ("包含原始指令", step2.instruction in enhanced_instruction)
    ]
    
    print(f"\n✅ 指令内容验证:")
    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False
    
    # 测试第三步（应该包含前两步的历史）
    print(f"\n📋 模拟第二步完成，测试第三步...")
    
    # 模拟第二步也完成
    step2.status = StepExecutionStatus.COMPLETED
    step2.result = Result(
        success=True,
        code="assert add(2, 3) == 5\nassert add(0, 0) == 0",
        stdout="Test cases created successfully",
        stderr=None,
        return_value="test cases created"
    )
    
    step3 = workflow_def.steps[2]
    enhanced_instruction_3 = agent_v3._build_enhanced_instruction(step3)
    
    # 验证第三步包含前两步的历史
    step3_checks = [
        ("包含第一步历史", step1.name in enhanced_instruction_3),
        ("包含第二步历史", step2.name in enhanced_instruction_3),
        ("包含第一步代码结果", "def add(a, b)" in enhanced_instruction_3),
        ("包含第二步测试结果", "assert add(2, 3)" in enhanced_instruction_3)
    ]
    
    print(f"\n✅ 第三步历史内容验证:")
    for check_name, check_result in step3_checks:
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False
    
    # 测试第一步（应该显示无历史）
    print(f"\n📋 测试第一步（无历史）...")
    step1_fresh = workflow_def.steps[0]
    step1_fresh.status = StepExecutionStatus.PENDING  # 重置状态
    enhanced_instruction_1 = agent_v3._build_enhanced_instruction(step1_fresh)
    
    first_step_check = "暂无执行历史" in enhanced_instruction_1 or "这是第一个步骤" in enhanced_instruction_1
    print(f"   {'✅' if first_step_check else '❌'} 第一步正确显示无历史")
    
    if not first_step_check:
        all_passed = False
    
    print(f"\n🎯 测试结果:")
    if all_passed:
        print(f"   🎉 所有测试通过!")
        print(f"   ✅ 执行历史功能正常工作")
        print(f"   ✅ 智能体将能看到之前步骤的结果")
        print(f"   ✅ 可以避免重复工作并保持一致性")
    else:
        print(f"   ❌ 部分测试失败")
        print(f"   需要检查执行历史构建逻辑")
    
    return all_passed

if __name__ == "__main__":
    success = test_execution_history()
    
    if success:
        print(f"\n🏆 执行历史功能测试成功!")
        print(f"   现在每个步骤都会收到前面步骤的执行结果")
        print(f"   智能体可以基于历史结果继续工作")
    else:
        print(f"\n🔧 需要进一步优化执行历史功能")