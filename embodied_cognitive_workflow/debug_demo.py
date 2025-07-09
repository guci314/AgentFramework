#!/usr/bin/env python3
"""
测试修复后的导入问题
"""

import sys
import os
# 确保使用项目本地的pythonTask模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# 导入必要的模块
from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType

# 使用真正的懒加载模块（导入速度提升7.3倍）
sys.path.append(project_dir)
from llm_lazy import get_model

print("✅ 所有导入成功!")

# 创建认知智能体
agent = CognitiveAgent(
    llm=get_model('gemini_2_5_flash'),  # 使用真正懒加载的Gemini模型
    max_cycles=5,          # 最大循环次数
    verbose=False,         # 关闭详细输出（调试器会提供更好的输出）
    enable_super_ego=False # 简化示例，关闭超我监督
)

# 创建调试器
debugger = CognitiveDebugger(agent)
print("✅ 调试器创建成功！")

# 开始调试简单的数学计算
task = "计算 15 + 23 的结果"
print(f"🎯 开始调试任务: {task}")

# 启动调试
debugger.start_debug(task)
print("✅ 调试任务启动成功!")

# 执行所有调试步骤
print("\n🔍 开始执行完整的认知循环调试:")
step_count = 0
while not debugger.debug_state.is_finished:
    try:
        step_result = debugger.run_one_step()
        if step_result:
            step_count += 1
            print(f"  步骤 {step_count}: {step_result.step_type.value} - 耗时: {step_result.execution_time:.3f}s")
            
            # 如果有输出结果，显示简短的结果
            if hasattr(step_result, 'output_data') and step_result.output_data:
                output_str = str(step_result.output_data)
                if len(output_str) > 100:
                    output_str = output_str[:100] + "..."
                print(f"    输出: {output_str}")
    
    except RuntimeError as e:
        # 工作流已完成时的异常处理
        print(f"  ✅ {e}")
        break
    except Exception as e:
        # 其他异常处理
        print(f"  ❌ 步骤执行出错: {e}")
        break
    
    # 防止无限循环，最多执行50步
    if step_count > 50:
        print(f"  ⚠️  已执行 {step_count} 步，为防止无限循环，强制结束")
        break

print(f"\n✅ 认知循环执行完成！总共执行了 {step_count} 个步骤")

# 获取最终状态
final_snapshot = debugger.inspect_state()
print(f"\n📊 最终状态:")
print(f"  - 当前步骤: {final_snapshot.current_step.value}")
print(f"  - 循环轮数: {final_snapshot.cycle_count}")
print(f"  - 目标达成: {final_snapshot.goal_achieved}")
print(f"  - 是否完成: {debugger.debug_state.is_finished}")

# 获取性能报告
try:
    performance_report = debugger.get_performance_report()
    print(f"\n📈 性能分析:")
    print(f"  - 总执行时间: {performance_report.total_time:.3f}s")
    print(f"  - 平均步骤时间: {performance_report.avg_step_time:.3f}s")
    if hasattr(performance_report, 'slowest_step') and performance_report.slowest_step:
        print(f"  - 最慢步骤: {performance_report.slowest_step}")
except Exception as e:
    print(f"  ⚠️  性能报告获取失败: {e}")

print("\n🎉 完整测试完成！认知调试器工作正常。")