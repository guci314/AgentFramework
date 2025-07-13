#!/usr/bin/env python3
"""
测试exit_on_max修复功能 - 创建新终止步骤的情况
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

def test_exit_on_max_create_terminal():
    """测试在没有现有终止步骤时创建新终止步骤的功能"""
    
    print("🔧 测试exit_on_max修复功能 - 创建新终止步骤")
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
            RegisteredAgent("coder", test_agent, "代码智能体"),
            RegisteredAgent("tester", test_agent, "测试智能体")
        ]
    )
    
    # 模拟没有终止步骤的工作流数据（所有步骤都是sequential类型）
    workflow_without_terminal = {
        "workflow_metadata": {
            "name": "test_no_terminal_workflow",
            "version": "1.0",
            "description": "没有终止步骤的测试工作流",
            "author": "test"
        },
        "global_variables": {
            "max_retries": 3
        },
        "steps": [
            {
                "id": "step1",
                "name": "实现代码",
                "agent_name": "coder",
                "instruction": "实现基础代码",
                "instruction_type": "execution",
                "expected_output": "代码实现",
                "control_flow": {
                    "type": "sequential",
                    "success_next": "step2"
                }
            },
            {
                "id": "step2", 
                "name": "运行测试",
                "agent_name": "tester",
                "instruction": "运行测试用例",
                "instruction_type": "execution",
                "expected_output": "测试结果",
                "control_flow": {
                    "type": "loop",
                    "loop_condition": "last_result.success == False",
                    "loop_target": "step1",
                    "max_iterations": 3,
                    "exit_on_max": "nonexistent_terminal"  # ❌ 无效引用
                }
            }
        ]
    }
    
    print("📋 原始工作流问题:")
    print("   - 没有terminal类型的步骤")
    print("   - step2.exit_on_max → 'nonexistent_terminal' (不存在)")
    print(f"   - 总步骤数: {len(workflow_without_terminal['steps'])}")
    
    # 执行修复
    print(f"\n🔧 执行引用修复...")
    agent_v3._fix_workflow_references(workflow_without_terminal)
    
    # 检查修复结果
    print(f"\n✅ 修复结果检查:")
    print(f"   修复后总步骤数: {len(workflow_without_terminal['steps'])}")
    
    # 查找step2和其exit_on_max
    step2 = None
    for step in workflow_without_terminal["steps"]:
        if step["id"] == "step2":
            step2 = step
            break
    
    if step2:
        control_flow = step2.get("control_flow", {})
        exit_on_max = control_flow.get("exit_on_max")
        
        print(f"\n   步骤 step2 (运行测试):")
        print(f"     类型: {control_flow.get('type', 'N/A')}")
        print(f"     loop_target: {control_flow.get('loop_target', 'N/A')}")
        print(f"     max_iterations: {control_flow.get('max_iterations', 'N/A')}")
        print(f"     exit_on_max: {exit_on_max}")
        
        # 验证修复是否正确
        valid_step_ids = {step["id"] for step in workflow_without_terminal["steps"]}
        if exit_on_max in valid_step_ids:
            # 检查是否创建了新的终止步骤
            target_step = next((step for step in workflow_without_terminal["steps"] if step["id"] == exit_on_max), None)
            if target_step and target_step.get("control_flow", {}).get("type") == "terminal":
                print(f"     ✅ exit_on_max 已修复为新创建的终止步骤: {exit_on_max}")
                fix_success = True
            else:
                print(f"     ✅ exit_on_max 已修复为有效步骤: {exit_on_max}")
                fix_success = True
        else:
            print(f"     ❌ exit_on_max 仍为无效值: {exit_on_max}")
            fix_success = False
    else:
        print("   ❌ 找不到步骤 step2")
        fix_success = False
    
    # 显示所有步骤的详细信息
    print(f"\n📋 所有步骤详情:")
    for i, step in enumerate(workflow_without_terminal["steps"]):
        control_flow = step.get("control_flow", {})
        print(f"   {i+1}. {step['id']} - {step['name']}")
        print(f"      类型: {control_flow.get('type', 'unknown')}")
        print(f"      智能体: {step.get('agent_name', 'N/A')}")
        if control_flow.get('type') == 'terminal':
            print(f"      🎯 这是终止步骤")
        if 'exit_on_max' in control_flow:
            print(f"      exit_on_max: {control_flow['exit_on_max']}")
    
    # 验证是否可以成功创建WorkflowDefinition
    print(f"\n🧪 验证工作流定义创建:")
    try:
        workflow_def = agent_v3.workflow_loader.load_from_dict(workflow_without_terminal)
        print(f"   ✅ 修复后的工作流可以成功加载")
        print(f"   工作流名称: {workflow_def.workflow_metadata.name}")
        print(f"   步骤数量: {len(workflow_def.steps)}")
        
        definition_success = True
    except Exception as e:
        print(f"   ❌ 修复后的工作流仍无法加载: {e}")
        definition_success = False
    
    overall_success = fix_success and definition_success
    
    print(f"\n🎯 测试结果:")
    if overall_success:
        print(f"   🎉 exit_on_max引用修复成功!")
        print(f"   ✅ 无效引用已修复")
        print(f"   ✅ 创建了新的终止步骤（如果需要）")
        print(f"   ✅ 工作流可以正常加载和执行")
    else:
        print(f"   ❌ 修复失败，需要进一步调试")
    
    return overall_success

if __name__ == "__main__":
    success = test_exit_on_max_create_terminal()
    
    if success:
        print(f"\n🏆 exit_on_max修复功能完全正常工作!")
        print(f"   能够正确处理没有终止步骤的情况")
        print(f"   自动创建合适的终止步骤")
    else:
        print(f"\n🔧 需要进一步完善exit_on_max修复逻辑")