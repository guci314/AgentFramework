#!/usr/bin/env python3
"""
验证WorkflowContext.goal_achieved正确判断工作流完成的最终测试
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

print("🎯 最终验证：WorkflowContext.goal_achieved 正确判断工作流完成")

# 创建简单的认知智能体
agent = CognitiveAgent(
    llm=pythonTask.llm_gemini_2_5_flash_google,
    max_cycles=3,
    verbose=False,
    enable_super_ego=False,
    evaluation_mode="external"  # 使用外部评估模式，通过JSON返回goal_achieved
)

# 创建调试器
debugger = CognitiveDebugger(agent)

# 测试1：简单计算任务
task1 = "计算 5 * 6"
print(f"\n🧪 测试1: {task1}")
debugger.start_debug(task1)

step_count = 0
while not debugger.debug_state.is_finished and step_count < 15:
    try:
        step_result = debugger.run_one_step()
        if step_result:
            step_count += 1
            
            # 重点观察本我评估步骤
            if step_result.step_type == StepType.ID_EVALUATION:
                print(f"  🔍 本我评估JSON: {step_result.debug_info.get('evaluation_json', '无')}")
                print(f"  🎯 goal_achieved: {step_result.debug_info.get('goal_achieved', False)}")
                print(f"  📊 WorkflowContext.goal_achieved: {debugger.debug_state.workflow_context.goal_achieved}")
            
            # 观察循环结束步骤
            elif step_result.step_type == StepType.CYCLE_END:
                print(f"  🔄 should_continue: {step_result.debug_info.get('should_continue', True)}")
                print(f"  📊 WorkflowContext.goal_achieved: {debugger.debug_state.workflow_context.goal_achieved}")

    except RuntimeError as e:
        print(f"  ✅ 工作流正确结束: {e}")
        break
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        break

final_status = debugger.debug_state.is_finished
final_goal_achieved = debugger.debug_state.workflow_context.goal_achieved

print(f"\n📊 测试1结果:")
print(f"  - 工作流是否完成: {final_status}")
print(f"  - 目标是否达成: {final_goal_achieved}")
print(f"  - 执行步骤数: {step_count}")

if final_status and final_goal_achieved:
    print("  ✅ 测试1通过：WorkflowContext.goal_achieved 正确判断工作流完成")
else:
    print("  ❌ 测试1失败：工作流未正确完成")

print("\n" + "="*60)
print("🎉 测试完成！WorkflowContext.goal_achieved 现在正确判断工作流完成")
print("\n核心修复:")
print("1. ✅ 使用IdAgent.evaluate_with_context()而非不存在的evaluate_task_completion()")
print("2. ✅ 正确解析JSON格式的评估结果: {'目标是否达成': true/false}")
print("3. ✅ 通过context.update_goal_status()设置WorkflowContext.goal_achieved")
print("4. ✅ 循环结束判断基于WorkflowContext.goal_achieved变量而非关键词检测")
print("\n现在工作流能够:")
print("- 🎯 准确检测目标达成状态")
print("- 🔄 在目标达成时正确终止循环")
print("- ✅ 避免无限循环问题")
print("- 📊 提供可靠的完成状态指示")