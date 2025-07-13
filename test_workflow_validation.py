#!/usr/bin/env python3
"""
测试工作流校验功能
================

验证MultiStepAgent_v3的新增工作流校验功能是否能够
在生成阶段就发现和修复问题。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from python_core import Agent
from langchain_openai import ChatOpenAI

def test_workflow_validation():
    """测试工作流校验功能"""
    
    print("🔍 测试工作流校验功能")
    print("=" * 60)
    
    # 创建测试LLM
    get_model("deepseek_chat") = ChatOpenAI(
        temperature=0,
        model="deepseek-chat", 
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY') or "test_key",
        max_tokens=1000
    )
    
    # 创建测试智能体
    test_agent = Agent(llm=get_model("deepseek_chat"), stateful=True)
    
    # 创建MultiStepAgent_v3实例
    agent_v3 = MultiStepAgent_v3(
        llm=get_model("deepseek_chat"),
        registered_agents=[
            RegisteredAgent("coder", test_agent, "编程智能体"),
            RegisteredAgent("tester", test_agent, "测试智能体")
        ]
    )
    
    print("📋 测试用例1: 包含多种错误的工作流")
    
    # 创建包含多种问题的工作流数据
    problematic_workflow = {
        "workflow_metadata": {
            "name": "problematic_workflow",
            "version": "1.0",
            "description": "包含多种问题的测试工作流",
            "author": "test"
        },
        "steps": [
            {
                "id": "step1",
                "name": "第一步",
                "agent_name": "nonexistent_agent",  # ❌ 不存在的智能体
                "instruction": "执行第一步",
                "instruction_type": "execution",
                "control_flow": {
                    "type": "sequential",
                    "success_next": "step2",
                    "failure_next": "error_step"  # ❌ 不存在的步骤
                }
            },
            {
                "id": "step2",
                "name": "第二步", 
                "agent_name": "coder",
                "instruction": "执行第二步",
                "instruction_type": "execution",
                "control_flow": {
                    "type": "loop",
                    "loop_target": "step1",
                    "max_iterations": 3,
                    "exit_on_max": "cleanup_step"  # ❌ 不存在的步骤
                }
            },
            {
                "id": "step3",
                "name": "第三步",
                "agent_name": "tester", 
                "instruction": "执行第三步",
                "instruction_type": "execution",
                "control_flow": {
                    "type": "parallel",
                    "parallel_steps": ["step4", "step5"]  # ❌ 不存在的步骤
                }
            }
        ],
        "control_rules": [
            {
                "trigger": "timeout > 300",
                "action": "jump_to",
                "target": "emergency_step"  # ❌ 不存在的步骤
            }
        ]
    }
    
    # 执行校验
    print(f"\n🔧 执行工作流校验...")
    validation_result = agent_v3._validate_workflow_legality(problematic_workflow)
    
    print(f"\n📊 校验结果:")
    print(f"   是否合法: {validation_result['is_valid']}")
    print(f"   错误数量: {len(validation_result['errors'])}")
    
    print(f"\n📝 发现的错误:")
    for i, error in enumerate(validation_result['errors'], 1):
        print(f"   {i}. {error}")
    
    # 测试修复功能
    print(f"\n🔧 测试修复功能...")
    fixed_workflow = agent_v3._fix_workflow_issues(
        problematic_workflow.copy(), 
        validation_result['errors']
    )
    
    # 重新校验修复后的工作流
    print(f"\n🔍 重新校验修复后的工作流...")
    fixed_validation = agent_v3._validate_workflow_legality(fixed_workflow)
    
    print(f"\n📊 修复后校验结果:")
    print(f"   是否合法: {fixed_validation['is_valid']}")
    print(f"   剩余错误数量: {len(fixed_validation['errors'])}")
    
    if fixed_validation['errors']:
        print(f"\n📝 剩余错误:")
        for i, error in enumerate(fixed_validation['errors'], 1):
            print(f"   {i}. {error}")
    
    # 测试工作流定义创建
    print(f"\n🧪 测试工作流定义创建...")
    try:
        workflow_def = agent_v3.workflow_loader.load_from_dict(fixed_workflow)
        print(f"   ✅ 修复后的工作流可以成功创建WorkflowDefinition")
        print(f"   工作流名称: {workflow_def.workflow_metadata.name}")
        print(f"   步骤数量: {len(workflow_def.steps)}")
        
        # 检查修复效果
        step1 = workflow_def.steps[0]
        step2 = workflow_def.steps[1] if len(workflow_def.steps) > 1 else None
        
        print(f"\n🔍 修复效果检查:")
        print(f"   步骤1智能体: {step1.agent_name} {'✅' if step1.agent_name in ['coder', 'tester'] else '❌'}")
        
        if step1.control_flow:
            print(f"   步骤1 failure_next: {step1.control_flow.failure_next} {'✅' if step1.control_flow.failure_next is None else '❌'}")
        
        if step2 and step2.control_flow:
            print(f"   步骤2 exit_on_max: {step2.control_flow.exit_on_max} {'✅' if step2.control_flow.exit_on_max is None else '❌'}")
        
        creation_success = True
    except Exception as e:
        print(f"   ❌ 工作流定义创建失败: {e}")
        creation_success = False
    
    # 测试用例2: 正常工作流
    print(f"\n" + "=" * 60)
    print(f"📋 测试用例2: 正常工作流（应该通过校验）")
    
    normal_workflow = {
        "workflow_metadata": {
            "name": "normal_workflow",
            "version": "1.0",
            "description": "正常的测试工作流",
            "author": "test"
        },
        "steps": [
            {
                "id": "step1",
                "name": "编写代码",
                "agent_name": "coder",
                "instruction": "编写代码",
                "instruction_type": "execution",
                "control_flow": {
                    "type": "sequential",
                    "success_next": "step2"
                }
            },
            {
                "id": "step2", 
                "name": "运行测试",
                "agent_name": "tester",
                "instruction": "运行测试",
                "instruction_type": "execution",
                "control_flow": {
                    "type": "terminal"
                }
            }
        ]
    }
    
    normal_validation = agent_v3._validate_workflow_legality(normal_workflow)
    print(f"\n📊 正常工作流校验结果:")
    print(f"   是否合法: {normal_validation['is_valid']} {'✅' if normal_validation['is_valid'] else '❌'}")
    print(f"   错误数量: {len(normal_validation['errors'])}")
    
    # 总结
    print(f"\n" + "=" * 60)
    print(f"🎯 测试总结:")
    
    validation_works = not validation_result['is_valid'] and len(validation_result['errors']) > 0
    fixing_works = len(fixed_validation['errors']) < len(validation_result['errors'])
    normal_passes = normal_validation['is_valid']
    
    print(f"   ✅ 校验功能: {'工作正常' if validation_works else '需要改进'}")
    print(f"   ✅ 修复功能: {'工作正常' if fixing_works else '需要改进'}")
    print(f"   ✅ 正常工作流: {'通过校验' if normal_passes else '未通过校验'}")
    print(f"   ✅ 定义创建: {'成功' if creation_success else '失败'}")
    
    overall_success = validation_works and fixing_works and normal_passes and creation_success
    
    return overall_success

if __name__ == "__main__":
    success = test_workflow_validation()
    
    if success:
        print(f"\n🏆 工作流校验功能测试成功!")
        print(f"   现在MultiStepAgent_v3可以在生成阶段就发现和修复问题")
        print(f"   提高了工作流的质量和执行成功率")
    else:
        print(f"\n🔧 工作流校验功能需要进一步优化")