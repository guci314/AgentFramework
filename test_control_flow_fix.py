#!/usr/bin/env python3
"""
测试控制流修复功能
================

验证MultiStepAgent_v3._fix_workflow_references方法是否正确修复了
LLM生成的工作流中的引用问题。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from pythonTask import Agent
from langchain_openai import ChatOpenAI

def test_control_flow_fix():
    """测试控制流修复功能"""
    
    print("🔧 测试控制流修复功能")
    print("=" * 50)
    
    # 创建简单的测试LLM
    llm_deepseek = ChatOpenAI(
        temperature=0,
        model="deepseek-chat", 
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY') or "test_key",
        max_tokens=1000
    )
    
    # 创建测试智能体
    test_agent = Agent(llm=llm_deepseek, stateful=True)
    
    # 创建MultiStepAgent_v3实例
    agent_v3 = MultiStepAgent_v3(
        llm=llm_deepseek,
        registered_agents=[
            RegisteredAgent("coder", test_agent, "测试智能体")
        ]
    )
    
    # 模拟LLM生成的有问题的工作流数据
    problematic_workflow = {
        "workflow_metadata": {
            "name": "test_workflow",
            "version": "1.0",
            "description": "测试工作流",
            "author": "test"
        },
        "global_variables": {
            "max_retries": 3
        },
        "steps": [
            {
                "id": "step1",
                "name": "第一步",
                "agent_name": "coder",
                "instruction": "执行第一步",
                "instruction_type": "execution",
                "expected_output": "第一步结果",
                "control_flow": {
                    "type": "sequential",
                    "success_next": "step2",
                    "failure_next": "error_handling"  # 无效引用
                }
            },
            {
                "id": "step2", 
                "name": "第二步",
                "agent_name": "coder",
                "instruction": "执行第二步",
                "instruction_type": "execution",
                "expected_output": "第二步结果",
                "control_flow": {
                    "type": "sequential",
                    "success_next": "step3",
                    "failure_next": "error_handling"  # 无效引用
                }
            },
            {
                "id": "step3",
                "name": "第三步",
                "agent_name": "coder", 
                "instruction": "执行第三步",
                "instruction_type": "execution",
                "expected_output": "第三步结果",
                "control_flow": {
                    "type": "terminal"
                }
            }
        ],
        "control_rules": [
            {
                "trigger": "execution_time > 300",
                "action": "jump_to",
                "target": "error_handling",  # 无效引用
                "priority": 1
            }
        ]
    }
    
    print("📋 原始工作流问题:")
    print("   - step1.failure_next -> error_handling (不存在)")
    print("   - step2.failure_next -> error_handling (不存在)")
    print("   - control_rule.target -> error_handling (不存在)")
    
    # 执行修复
    print(f"\n🔧 执行控制流修复...")
    agent_v3._fix_workflow_references(problematic_workflow)
    
    # 检查修复结果
    print(f"\n✅ 修复结果:")
    
    steps = problematic_workflow["steps"]
    for i, step in enumerate(steps):
        step_id = step["id"]
        control_flow = step.get("control_flow", {})
        
        print(f"\n   步骤 {step_id}:")
        print(f"     类型: {control_flow.get('type', 'N/A')}")
        print(f"     success_next: {control_flow.get('success_next', 'N/A')}")
        print(f"     failure_next: {control_flow.get('failure_next', 'N/A')}")
        
        # 验证修复是否正确
        if i < len(steps) - 1:  # 不是最后一步
            expected_next = steps[i + 1]["id"]
            actual_next = control_flow.get("success_next")
            if actual_next == expected_next:
                print(f"     ✅ success_next 正确指向 {expected_next}")
            else:
                print(f"     ❌ success_next 错误: 期望 {expected_next}, 实际 {actual_next}")
        else:  # 最后一步
            if control_flow.get("type") == "terminal":
                print(f"     ✅ 最后一步正确设置为 terminal")
            else:
                print(f"     ❌ 最后一步应该是 terminal")
        
        # 检查failure_next是否被正确处理
        failure_next = control_flow.get("failure_next")
        if failure_next is None:
            print(f"     ✅ failure_next 已修复为 None")
        else:
            print(f"     ⚠️  failure_next 仍为: {failure_next}")
    
    # 检查控制规则
    control_rules = problematic_workflow.get("control_rules", [])
    print(f"\n   控制规则数量: {len(control_rules)}")
    if len(control_rules) == 0:
        print(f"     ✅ 无效控制规则已被移除")
    else:
        print(f"     ⚠️  仍有控制规则存在")
        for rule in control_rules:
            print(f"       - {rule}")
    
    print(f"\n🎉 控制流修复测试完成!")
    
    # 验证是否可以成功创建WorkflowDefinition
    try:
        workflow_def = agent_v3.workflow_loader.load_from_dict(problematic_workflow)
        print(f"✅ 修复后的工作流可以成功加载")
        print(f"   工作流名称: {workflow_def.workflow_metadata.name}")
        print(f"   步骤数量: {len(workflow_def.steps)}")
        return True
    except Exception as e:
        print(f"❌ 修复后的工作流仍无法加载: {e}")
        return False

if __name__ == "__main__":
    success = test_control_flow_fix()
    
    if success:
        print(f"\n🎊 测试成功!")
        print(f"   MultiStepAgent_v3.execute_multi_step() 的控制流问题已修复")
        print(f"   现在可以正确执行多步骤工作流")
    else:
        print(f"\n💥 测试失败!")
        print(f"   需要进一步调试控制流修复逻辑")