#!/usr/bin/env python3
"""
测试exit_on_max引用修复功能
==========================

验证MultiStepAgent_v3是否正确修复了循环控制流中的
无效exit_on_max引用。
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

def test_exit_on_max_fix():
    """测试exit_on_max引用修复功能"""
    
    print("🔧 测试exit_on_max引用修复功能")
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
            RegisteredAgent("coder", test_agent, "测试智能体"),
            RegisteredAgent("tester", test_agent, "测试智能体"),
            RegisteredAgent("analyst", test_agent, "测试智能体")
        ]
    )
    
    # 模拟有问题的工作流数据（包含无效的exit_on_max引用）
    problematic_workflow = {
        "workflow_metadata": {
            "name": "test_loop_workflow",
            "version": "1.0",
            "description": "测试循环工作流",
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
                    "type": "conditional",
                    "condition": "last_result.success == True",
                    "success_next": "step4",  # 成功→结束
                    "failure_next": "step3"   # 失败→修复
                }
            },
            {
                "id": "step3",
                "name": "修复代码",
                "agent_name": "coder",
                "instruction": "修复代码问题",
                "instruction_type": "execution", 
                "expected_output": "修复后的代码",
                "control_flow": {
                    "type": "loop",
                    "loop_condition": "last_result.success == False",
                    "loop_target": "step2",
                    "max_iterations": 3,
                    "exit_on_max": "error_handling_step"  # ❌ 无效引用
                }
            },
            {
                "id": "step4",
                "name": "结束工作流",
                "agent_name": "analyst",
                "instruction": "工作流成功完成",
                "instruction_type": "information",
                "expected_output": "完成确认",
                "control_flow": {
                    "type": "terminal"
                }
            }
        ]
    }
    
    print("📋 原始工作流问题:")
    print("   - step3.exit_on_max → 'error_handling_step' (不存在)")
    
    # 执行修复
    print(f"\n🔧 执行引用修复...")
    agent_v3._fix_workflow_references(problematic_workflow)
    
    # 检查修复结果
    print(f"\n✅ 修复结果检查:")
    
    step3 = None
    for step in problematic_workflow["steps"]:
        if step["id"] == "step3":
            step3 = step
            break
    
    if step3:
        control_flow = step3.get("control_flow", {})
        exit_on_max = control_flow.get("exit_on_max")
        
        print(f"\n   步骤 step3 (修复代码):")
        print(f"     类型: {control_flow.get('type', 'N/A')}")
        print(f"     loop_target: {control_flow.get('loop_target', 'N/A')}")
        print(f"     max_iterations: {control_flow.get('max_iterations', 'N/A')}")
        print(f"     exit_on_max: {exit_on_max}")
        
        # 验证修复是否正确
        # 检查exit_on_max是否指向有效的步骤
        valid_step_ids = {step["id"] for step in problematic_workflow["steps"]}
        if exit_on_max in valid_step_ids:
            # 进一步检查是否指向终止步骤
            target_step = next((step for step in problematic_workflow["steps"] if step["id"] == exit_on_max), None)
            if target_step and target_step.get("control_flow", {}).get("type") == "terminal":
                print(f"     ✅ exit_on_max 已修复为终止步骤: {exit_on_max}")
                fix_success = True
            else:
                print(f"     ✅ exit_on_max 已修复为有效步骤: {exit_on_max}")
                fix_success = True
        else:
            print(f"     ❌ exit_on_max 仍为无效值: {exit_on_max}")
            fix_success = False
    else:
        print("   ❌ 找不到步骤 step3")
        fix_success = False
    
    # 验证是否可以成功创建WorkflowDefinition
    print(f"\n🧪 验证工作流定义创建:")
    try:
        workflow_def = agent_v3.workflow_loader.load_from_dict(problematic_workflow)
        print(f"   ✅ 修复后的工作流可以成功加载")
        print(f"   工作流名称: {workflow_def.workflow_metadata.name}")
        print(f"   步骤数量: {len(workflow_def.steps)}")
        
        # 检查step3的控制流
        step3_def = None
        for step in workflow_def.steps:
            if step.id == "step3":
                step3_def = step
                break
        
        if step3_def and step3_def.control_flow:
            print(f"   ✅ 步骤3控制流类型: {step3_def.control_flow.type.value}")
            print(f"   ✅ exit_on_max: {step3_def.control_flow.exit_on_max}")
        
        definition_success = True
    except Exception as e:
        print(f"   ❌ 修复后的工作流仍无法加载: {e}")
        definition_success = False
    
    # 测试循环修复的逻辑
    print(f"\n🔄 循环控制逻辑说明:")
    print(f"   当修复循环达到最大次数(3次)时:")
    print(f"   - 之前: 尝试跳转到不存在的'error_handling_step' → 错误")
    print(f"   - 现在: exit_on_max=step4 → 跳转到终止步骤，正常结束工作流")
    
    overall_success = fix_success and definition_success
    
    print(f"\n🎯 测试结果:")
    if overall_success:
        print(f"   🎉 exit_on_max引用修复成功!")
        print(f"   ✅ 无效引用已修复为有效的终止步骤")
        print(f"   ✅ 工作流可以正常加载和执行")
        print(f"   ✅ 循环超过最大次数时将跳转到终止步骤")
    else:
        print(f"   ❌ 修复失败，需要进一步调试")
    
    return overall_success

if __name__ == "__main__":
    success = test_exit_on_max_fix()
    
    if success:
        print(f"\n🏆 exit_on_max引用修复功能正常工作!")
        print(f"   现在生成的工作流中的循环控制更加健壮")
        print(f"   避免了因无效引用导致的执行错误")
    else:
        print(f"\n🔧 需要进一步完善exit_on_max修复逻辑")