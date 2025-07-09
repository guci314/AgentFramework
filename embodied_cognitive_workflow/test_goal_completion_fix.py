#!/usr/bin/env python3
"""
测试目标完成判断修复
"""

import sys
import os
# 确保使用项目本地的pythonTask模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType
import pythonTask

print("🧪 测试目标完成判断修复")

# 创建简单的认知智能体
agent = CognitiveAgent(
    llm=pythonTask.llm_gemini_2_5_flash_google,
    max_cycles=3,  # 设置更小的循环数
    verbose=False,
    enable_super_ego=False
)

# 创建调试器
debugger = CognitiveDebugger(agent)

# 开始一个简单的任务
task = "计算 2+2"
print(f"🎯 开始调试任务: {task}")
debugger.start_debug(task)

print("\n🔍 执行调试步骤（最多20步或完成）:")
step_count = 0
max_steps = 20

while not debugger.debug_state.is_finished and step_count < max_steps:
    try:
        step_result = debugger.run_one_step()
        if step_result:
            step_count += 1
            print(f"  步骤 {step_count}: {step_result.step_type.value} - 耗时: {step_result.execution_time:.3f}s")
            
            # 特别关注本我评估步骤
            if step_result.step_type == StepType.ID_EVALUATION:
                print(f"    📋 本我评估结果: {step_result.output_data}")
                print(f"    🎯 目标达成状态: {debugger.debug_state.workflow_context.goal_achieved}")
    
    except RuntimeError as e:
        print(f"  ✅ {e}")
        break
    except Exception as e:
        print(f"  ❌ 步骤执行出错: {e}")
        break

print(f"\n📊 最终状态:")
print(f"  - 执行步骤数: {step_count}")
print(f"  - 是否完成: {debugger.debug_state.is_finished}")
if hasattr(debugger.debug_state, 'workflow_context'):
    print(f"  - 目标达成: {debugger.debug_state.workflow_context.goal_achieved}")

if debugger.debug_state.is_finished:
    print("🎉 测试成功！工作流正确完成并退出。")
elif step_count >= max_steps:
    print("⚠️  达到最大步骤数限制，可能仍存在无限循环问题。")
else:
    print("❓ 工作流意外结束。")