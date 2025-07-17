# CognitiveDebugger 快速入门指南

## 什么是 CognitiveDebugger？

CognitiveDebugger 是一个强大的调试工具，专门用于调试具身认知工作流。它让您能够：

- 🔍 **单步执行**: 逐步观察AI的"思考过程"
- 🛑 **设置断点**: 在关键步骤暂停执行
- 📊 **性能分析**: 了解每个认知步骤的耗时
- 🔙 **状态回退**: 回到之前的执行状态
- 💾 **会话保存**: 导出和导入调试会话

## 5分钟快速上手

### 步骤1: 导入和设置

```python
# 导入必要的模块
from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType
import pythonTask

# 创建认知智能体
agent = CognitiveAgent(
    llm=pythonTask.llm_gemini_2_5_flash_google,  # 使用Gemini模型
    max_cycles=5,          # 最大循环次数
    verbose=False,         # 关闭详细输出（调试器会提供更好的输出）
    enable_super_ego=False # 简化示例，关闭超我监督
)

# 创建调试器
debugger = CognitiveDebugger(agent)
print("✅ 调试器创建成功！")
```

### 步骤2: 开始调试会话

```python
# 开始调试一个具体任务
task = "计算 25 × 4 + 15 的结果"
debugger.start_debug(task)
```

### 步骤3: 单步执行

```python
# 手动单步执行
print("🔄 开始单步执行...")
step_count = 0

while not debugger.debug_state.is_finished and step_count < 10:
    step_result = debugger.run_one_step()
    
    if step_result is None:
        print("⏸️  遇到断点，执行暂停")
        break
    
    step_count += 1
    print(f"步骤 {step_count}: {step_result.step_type.value}")
    print(f"  执行层: {step_result.agent_layer}")
    print(f"  耗时: {step_result.execution_time:.3f}s")
    print(f"  输出: {str(step_result.output_data)[:50]}...")
    print()

print(f"✅ 执行完成，共 {step_count} 步")
```

### 步骤4: 查看结果和分析

```python
# 查看执行状态
snapshot = debugger.capture_debug_snapshot()
print("📊 执行状态:")
print(f"  总步骤: {snapshot.total_steps}")
print(f"  执行时间: {snapshot.execution_time:.2f}s")
print(f"  目标达成: {'✅' if snapshot.goal_achieved else '❌'}")

# 获取性能报告
report = debugger.get_performance_report()
print(f"\n⚡ 性能分析:")
print(f"  总时间: {report.total_time:.3f}s")
print(f"  平均耗时: {report.avg_step_time:.3f}s")
print(f"  最慢步骤: {report.slowest_step}")

# 可视化执行流程
print(f"\n🔄 执行流程:")
flow_chart = debugger.visualize_execution_flow()
print(flow_chart)
```

## 常用调试模式

### 模式1: 自动执行到完成

最简单的使用方式 - 让调试器自动执行完整个任务：

```python
debugger = CognitiveDebugger(agent)
debugger.start_debug("创建一个Python函数计算斐波那契数列")

# 一次性执行到完成
results = debugger.run_to_completion()

print(f"执行完成，共 {len(results)} 步")

# 查看性能分析
report = debugger.get_performance_report()
print(f"总耗时: {report.total_time:.3f}s")
```

### 模式2: 交互式调试

逐步执行，每一步都询问用户是否继续：

```python
debugger = CognitiveDebugger(agent)
debugger.start_debug("分析一段文本的情感倾向")

while not debugger.debug_state.is_finished:
    # 执行一步
    step_result = debugger.run_one_step()
    
    if step_result is None:
        break
    
    # 显示当前状态
    print(f"🔍 当前步骤: {step_result.step_type.value}")
    print(f"📊 输出: {step_result.output_data}")
    
    # 询问用户
    user_input = input("继续执行? (y/n/s=查看状态): ").lower()
    
    if user_input == 'n':
        print("用户停止执行")
        break
    elif user_input == 's':
        snapshot = debugger.capture_debug_snapshot()
        print(f"当前循环: {snapshot.cycle_count}")
        print(f"当前分析: {snapshot.current_state_analysis}")
```

### 模式3: 断点调试

设置断点在特定步骤暂停：

```python
debugger = CognitiveDebugger(agent)

# 设置断点
bp_id = debugger.set_breakpoint(
    StepType.DECISION_MAKING, 
    description="决策步骤断点"
)

debugger.start_debug("设计一个简单的网页布局")

# 执行到断点
print("🏃 执行到断点...")
results = debugger.run_until_breakpoint()

print(f"在断点停止，已执行 {len(results)} 步")

# 检查当前状态
snapshot = debugger.capture_debug_snapshot()
print(f"停止在: {snapshot.current_step.value}")
print(f"当前分析: {snapshot.current_state_analysis}")

# 移除断点并继续
debugger.remove_breakpoint(bp_id)
remaining_results = debugger.run_to_completion()
print(f"继续执行了 {len(remaining_results)} 步")
```

### 模式4: 条件断点

在满足特定条件时暂停：

```python
debugger = CognitiveDebugger(agent)

# 设置条件断点 - 在第3轮循环时暂停
debugger.set_breakpoint(
    StepType.STATE_ANALYSIS,
    condition="cycle_count >= 3",
    description="第3轮循环断点"
)

# 设置错误断点 - 有错误时暂停
debugger.set_breakpoint(
    StepType.BODY_EXECUTION,
    condition="error is not None", 
    description="错误断点"
)

debugger.start_debug("复杂的数据处理任务")
results = debugger.run_until_breakpoint()

# 分析为什么停止
for bp in debugger.list_breakpoints():
    if bp.hit_count > 0:
        print(f"触发断点: {bp.description} (命中 {bp.hit_count} 次)")
```

## 实用技巧

### 技巧1: 性能优化分析

找出认知循环中的性能瓶颈：

```python
# 执行任务
debugger.start_debug("处理大量数据并生成报告")
results = debugger.run_to_completion()

# 分析性能
report = debugger.get_performance_report()

print("🐌 性能瓶颈分析:")
for step_type, time_spent in report.step_time_breakdown.items():
    percentage = (time_spent / report.total_time) * 100
    if percentage > 20:  # 超过20%的时间
        print(f"  ⚠️  {step_type}: {time_spent:.3f}s ({percentage:.1f}%)")

# 分析循环效率
print("\n🔄 循环效率分析:")
for cycle_data in report.cycle_performance:
    if cycle_data['avg_time'] > 1.0:  # 平均超过1秒
        print(f"  ⚠️  循环 {cycle_data['cycle']}: 平均 {cycle_data['avg_time']:.3f}s/步")
```

### 技巧2: 状态回退和重试

当执行出现问题时，回退到之前的状态：

```python
debugger.start_debug("执行可能出错的任务")

# 执行几步
debugger.run_steps(5)

# 保存当前状态
current_steps = len(debugger.debug_state.step_history)
print(f"当前已执行 {current_steps} 步")

# 继续执行
debugger.run_steps(3)

# 如果发现问题，回退
print("发现问题，回退3步...")
success = debugger.step_back(3)

if success:
    print(f"回退成功，当前步数: {len(debugger.debug_state.step_history)}")
    # 可以重新执行或者修改策略
    debugger.run_one_step()  # 重新执行
```

### 技巧3: 保存和分享调试会话

保存调试会话供后续分析：

```python
# 执行调试会话
debugger.start_debug("重要的分析任务")
results = debugger.run_to_completion()

# 导出会话
session_file = "important_analysis_debug.json"
success = debugger.export_session(session_file)

if success:
    print(f"✅ 调试会话已保存到: {session_file}")
    
    # 稍后可以导入查看
    debugger.import_session(session_file)
    
    # 或者创建新的调试器实例来查看
    new_debugger = CognitiveDebugger(agent)
    new_debugger.import_session(session_file)
```

### 技巧4: 多任务对比

对比不同任务的执行特点：

```python
def analyze_task(task_description):
    debugger = CognitiveDebugger(agent)
    debugger.start_debug(task_description)
    results = debugger.run_to_completion()
    report = debugger.get_performance_report()
    
    return {
        'task': task_description,
        'total_time': report.total_time,
        'step_count': len(results),
        'avg_step_time': report.avg_step_time,
        'cycles': len(report.cycle_performance)
    }

# 对比不同类型的任务
tasks = [
    "计算 123 + 456",
    "写一个排序算法",
    "分析股票市场趋势"
]

print("📊 任务对比分析:")
for task in tasks:
    analysis = analyze_task(task)
    print(f"\n任务: {analysis['task']}")
    print(f"  耗时: {analysis['total_time']:.3f}s")
    print(f"  步数: {analysis['step_count']}")
    print(f"  循环: {analysis['cycles']}")
    print(f"  效率: {analysis['avg_step_time']:.3f}s/步")
```

## 常见问题解答

### Q: 调试器会影响原始执行结果吗？
A: 不会。调试器采用包装器模式，不修改原始智能体的行为，只是将执行过程拆解成可观察的步骤。

### Q: 断点条件可以使用哪些变量？
A: 断点条件可以访问以下变量：
- `cycle_count`: 当前循环轮数
- `step_type`: 当前步骤类型
- `context`: 当前上下文信息
- `error`: 错误信息（如果有）
- `debug_info`: 调试信息字典

### Q: 如何调试性能问题？
A: 使用性能分析功能：
1. 运行完整任务
2. 查看 `get_performance_report()` 的结果
3. 关注 `slowest_step` 和 `step_time_breakdown`
4. 分析 `cycle_performance` 找出低效的循环

### Q: 可以同时调试多个智能体吗？
A: 每个 `CognitiveDebugger` 实例对应一个智能体。要调试多个智能体，需要创建多个调试器实例。

### Q: 调试会话文件很大怎么办？
A: 导出的JSON文件包含完整的执行历史。对于长时间运行的任务，文件可能较大。可以：
1. 定期导出中间结果
2. 只导出关键部分的调试信息
3. 使用压缩工具减小文件大小

## 下一步

- 📖 阅读完整的 [API 文档](cognitive_debugger_api.md)
- 🧪 查看 [设计文档](cognitive_debugger_design.md) 了解内部原理
- 🔧 运行测试套件验证功能: `python test_debugger_comprehensive.py`
- 💡 尝试调试您自己的认知工作流任务

---

**提示**: 调试是理解AI认知过程的最佳方式。通过 CognitiveDebugger，您可以深入观察AI是如何"思考"和"决策"的，这对于优化提示词、改进模型配置、以及理解复杂任务的执行逻辑都非常有帮助。