#!/usr/bin/env python3
"""
演示条件断点的使用方法
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

# 获取语言模型
llm = get_model('deepseek_chat')
print("✅ 成功加载模型: deepseek_chat")

# 创建认知智能体（而不是普通的Agent）
agent = CognitiveAgent(
    llm=llm,
    max_cycles=5,
    verbose=False,  # 调试器会处理输出，这里关闭详细输出
    enable_meta_cognition=False,  # 简单任务不需要元认知
    evaluation_mode="internal"
)
print("✅ 成功创建认知智能体")

# 创建调试器
debugger = CognitiveDebugger(agent)
print("✅ 调试器创建成功！")

# 选择一个更简单的任务来演示条件断点
# task = "请计算1到10的所有数字之和，并逐步展示计算过程"
task = """
请开发一个完整的Calculator类和对应的单元测试。请创建两个文件：calculator.py（Calculator类）和 test_calculator.py（单元测试）要求如下：

1. Calculator类功能：
   - 基本四则运算：加法、减法、乘法、除法
   - 错误处理：除零检查
   
# 附加要求：
不需要测试覆盖率
"""
print(f"🎯 开始调试任务: {task}")

# 启动调试
debugger.start_debug(task)
print("✅ 调试任务启动成功!")

# ========== 演示断点功能 ==========
print("\n🔧 设置断点演示:")

# 清除所有现有断点
debugger.clear_breakpoints()
print("✅ 已清除所有现有断点")

# 设置一个无条件断点在决策步骤
print("\n🛑 设置无条件断点：在决策步骤停止")
breakpoint_id = debugger.set_breakpoint(
    StepType.DECISION_MAKING,
    description="决策步骤断点"
)
print(f"   ✅ 断点已设置，ID: {breakpoint_id}")

print("\n📋 当前所有断点:")
for bp in debugger.breakpoint_manager.list_breakpoints():
    print(f"   - [{bp.id}] {bp.step_type.value}: {bp.description}")
    if bp.condition:
        print(f"     条件: {bp.condition}")
    else:
        print(f"     条件: 无条件断点")

# ========== 演示运行到断点 ==========
print("\n🚀 开始执行并演示断点触发:")

# 使用 run_until_breakpoint 方法执行到断点
print("\n▶️  执行到第一个断点...")
results = debugger.run_until_breakpoint()

if results:
    print(f"\n🛑 断点触发！已执行 {len(results)} 个步骤")
    last_step = results[-1]
    print(f"   触发断点的步骤: {last_step.step_type.value}")
    print(f"   循环轮数: {debugger.debug_state.cycle_count}")
    
    # 检查当前状态
    current_state = debugger.capture_debug_snapshot()
    print(f"   当前状态分析: {current_state.current_state_analysis[:100]}...")
    
    # 可以在断点处执行一些调试操作
    print("\n🔍 在断点处进行调试检查...")
    print(f"   - 目标是否达成: {current_state.goal_achieved}")
    print(f"   - 执行步骤数: {current_state.total_steps}")
    
    # 继续执行到下一个断点
    print("\n▶️  继续执行到下一个断点...")
    results = debugger.run_until_breakpoint()
    
    if results:
        print(f"\n🛑 第二个断点触发！")
        last_step = results[-1]
        print(f"   触发断点的步骤: {last_step.step_type.value}")
        
        # 移除断点后继续
        print(f"\n🗑️  移除断点 {breakpoint_id}")
        debugger.remove_breakpoint(breakpoint_id)

# 清除所有断点并正常执行完成
print("\n🧹 清除所有断点")
debugger.clear_breakpoints()

print("\n▶️  继续执行到完成...")
step_count = len(debugger.debug_state.step_history)
while not debugger.debug_state.is_finished:
    try:
        step_result = debugger.run_one_step()
        if step_result:
            step_count += 1
            print(f"  步骤 {step_count}: {step_result.step_type.value} - 耗时: {step_result.execution_time:.3f}s")
            
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
final_snapshot = debugger.capture_debug_snapshot()
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

print("\n🎉 条件断点演示完成！")

# ========== 条件断点使用总结 ==========
print("\n" + "="*60)
print("📚 条件断点使用总结:")
print("="*60)
print("""
1. 基本用法:
   breakpoint_id = debugger.set_breakpoint(
       step_type=StepType.CYCLE_START,
       condition="cycle_count == 2",
       description="描述信息"
   )

2. 条件表达式中可用的变量:
   - cycle_count: 当前循环轮数
   - current_step: 当前步骤类型
   - instruction: 原始指令
   - goal_achieved: 目标是否达成

3. 常用操作:
   - debugger.run_until_breakpoint(): 执行到断点
   - debugger.remove_breakpoint(id): 移除断点
   - debugger.clear_breakpoints(): 清除所有断点
   - debugger.list_breakpoints(): 列出所有断点

4. 条件断点示例:
   - "cycle_count > 3": 循环超过3轮时停止
   - "cycle_count == 2": 在第2轮循环时停止
   - "goal_achieved == True": 目标达成时停止
   - "goal_achieved == False and cycle_count > 5": 超过5轮仍未达成目标时停止
   - "'计算' in instruction": 指令包含特定关键字时停止

5. 调试技巧:
   - 在关键决策点设置断点
   - 使用条件断点捕获异常情况
   - 在断点处检查状态和变量
   - 动态添加和移除断点
""")