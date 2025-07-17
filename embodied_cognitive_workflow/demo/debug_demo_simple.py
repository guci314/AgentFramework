#!/usr/bin/env python3
"""
简单的调试器演示 - 测试基本功能
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

# 使用真正的懒加载模块
sys.path.append(project_dir)
from llm_lazy import get_model

print("✅ 所有导入成功!")

# 获取语言模型
llm = get_model('deepseek_chat')
print("✅ 成功加载模型: deepseek_chat")

# 创建认知智能体
agent = CognitiveAgent(
    llm=llm,
    max_cycles=3,  # 限制循环次数
    verbose=False,
    enable_meta_cognition=False,
    evaluation_mode="internal"
)
print("✅ 成功创建认知智能体")

# 创建调试器
debugger = CognitiveDebugger(agent)
print("✅ 调试器创建成功！")

# 测试简单任务
task = "计算 25 * 4 的结果"
print(f"\n🎯 开始调试任务: {task}")

# 启动调试
debugger.start_debug(task)

# 设置断点
debugger.set_breakpoint(StepType.BODY_EXECUTION, description="身体执行断点")
print("✅ 已设置身体执行断点")

# 执行到断点
print("\n🔍 执行到断点:")
results = debugger.run_until_breakpoint()
for i, result in enumerate(results):
    print(f"  步骤 {i+1}: {result.step_type.value} - 耗时: {result.execution_time:.3f}s")

# 检查状态
snapshot = debugger.capture_debug_snapshot()
print(f"\n📊 当前状态:")
print(f"  - 当前步骤: {snapshot.current_step.value}")
print(f"  - 循环轮数: {snapshot.cycle_count}")
print(f"  - 是否在断点: {debugger.debug_state.at_breakpoint}")

# 继续执行完成
print("\n🔍 继续执行到完成:")
remaining_results = debugger.run_to_completion()
for i, result in enumerate(remaining_results):
    print(f"  步骤 {i+1}: {result.step_type.value} - 耗时: {result.execution_time:.3f}s")

# 获取性能报告
performance_report = debugger.get_performance_report()
print(f"\n📈 性能分析:")
print(f"  - 总执行时间: {performance_report.total_time:.3f}s")
print(f"  - 平均步骤时间: {performance_report.avg_step_time:.3f}s")
print(f"  - 最慢步骤: {performance_report.slowest_step}")

print("\n🎉 调试演示完成！")