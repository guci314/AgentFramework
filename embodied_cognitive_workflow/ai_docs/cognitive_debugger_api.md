# CognitiveDebugger API 文档

## 概述

CognitiveDebugger 是一个用于调试具身认知工作流的强大工具，提供单步执行、状态检查、断点设置等功能，帮助开发者深入理解和优化认知循环的执行过程。

## 快速开始

```python
from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType
import pythonTask

# 创建认知智能体
agent = CognitiveAgent(
    llm=pythonTask.llm_gemini_2_5_flash_google,
    max_cycles=5,
    verbose=False,
    enable_super_ego=False,
    evaluation_mode="internal"
)

# 创建调试器
debugger = CognitiveDebugger(agent)

# 开始调试会话
debugger.start_debug("计算 15 + 23 的结果")

# 单步执行
while not debugger.debug_state.is_finished:
    step_result = debugger.run_one_step()
    if step_result is None:  # 断点触发
        break
    print(f"步骤: {step_result.step_type.value}, 耗时: {step_result.execution_time:.3f}s")

# 查看性能报告
report = debugger.get_performance_report()
print(f"总执行时间: {report.total_time:.3f}s")
```

## 核心类和接口

### CognitiveDebugger

认知调试器主类，提供所有调试功能。

#### 构造函数

```python
def __init__(self, cognitive_agent: CognitiveAgent)
```

**参数:**
- `cognitive_agent`: 要调试的认知智能体实例

#### 主要方法

##### start_debug(instruction: str) -> None

开始调试会话。

**参数:**
- `instruction`: 要执行的指令

**示例:**
```python
debugger.start_debug("分析销售数据并生成报告")
```

##### run_one_step() -> StepResult

执行单步，返回步骤执行结果。如果触发断点则返回 None。

**返回值:**
- `StepResult`: 步骤执行结果，包含执行时间、输出数据等信息
- `None`: 触发断点或执行完成

**示例:**
```python
step_result = debugger.run_one_step()
if step_result:
    print(f"执行了步骤: {step_result.step_type.value}")
    print(f"执行层: {step_result.agent_layer}")
    print(f"耗时: {step_result.execution_time:.3f}s")
else:
    print("触发断点或执行完成")
```

##### run_steps(count: int) -> List[StepResult]

执行指定步数。

**参数:**
- `count`: 要执行的步数

**返回值:**
- `List[StepResult]`: 执行的步骤结果列表

**示例:**
```python
results = debugger.run_steps(5)
print(f"执行了 {len(results)} 个步骤")
```

##### run_until_breakpoint() -> List[StepResult]

运行直到触发断点。

**返回值:**
- `List[StepResult]`: 执行过程中的所有步骤结果

##### run_to_completion() -> List[StepResult]

运行到完成。

**返回值:**
- `List[StepResult]`: 完整的执行结果

##### inspect_state() -> StateSnapshot

检查当前调试状态。

**返回值:**
- `StateSnapshot`: 当前状态的完整快照

**示例:**
```python
snapshot = debugger.inspect_state()
print(f"当前步骤: {snapshot.current_step.value}")
print(f"循环轮数: {snapshot.cycle_count}")
print(f"目标达成: {snapshot.goal_achieved}")
print(f"内存使用: {snapshot.memory_length} 条消息")
```

##### set_breakpoint(step_type: StepType, condition: str = None, description: str = "") -> str

设置断点。

**参数:**
- `step_type`: 断点的步骤类型
- `condition`: 可选的断点条件（Python表达式）
- `description`: 断点描述

**返回值:**
- `str`: 断点ID

**示例:**
```python
# 无条件断点
bp_id = debugger.set_breakpoint(StepType.STATE_ANALYSIS, description="状态分析断点")

# 条件断点
bp_id = debugger.set_breakpoint(
    StepType.DECISION_MAKING, 
    condition="cycle_count > 2",
    description="第3轮后的决策断点"
)
```

##### remove_breakpoint(breakpoint_id: str) -> bool

移除断点。

**参数:**
- `breakpoint_id`: 断点ID

**返回值:**
- `bool`: 是否成功移除

##### list_breakpoints() -> List[Breakpoint]

列出所有断点。

**返回值:**
- `List[Breakpoint]`: 断点列表

##### step_back(steps: int = 1) -> bool

回退步骤。

**参数:**
- `steps`: 要回退的步数，默认为1

**返回值:**
- `bool`: 是否成功回退

**示例:**
```python
success = debugger.step_back(3)
if success:
    print("成功回退3步")
else:
    print("回退失败")
```

##### get_performance_report() -> PerformanceReport

获取性能分析报告。

**返回值:**
- `PerformanceReport`: 性能分析报告

**示例:**
```python
report = debugger.get_performance_report()
print(f"总执行时间: {report.total_time:.3f}s")
print(f"平均步骤耗时: {report.avg_step_time:.3f}s")
print(f"最慢步骤: {report.slowest_step}")
print(f"最快步骤: {report.fastest_step}")

# 按步骤类型查看耗时
for step_type, time_spent in report.step_time_breakdown.items():
    print(f"{step_type}: {time_spent:.3f}s")
```

##### visualize_execution_flow() -> str

可视化执行流程。

**返回值:**
- `str`: 可视化的执行流程图

**示例:**
```python
flow_chart = debugger.visualize_execution_flow()
print(flow_chart)
```

##### export_session(file_path: str) -> bool

导出调试会话到文件。

**参数:**
- `file_path`: 导出文件路径

**返回值:**
- `bool`: 是否导出成功

**示例:**
```python
success = debugger.export_session("debug_session.json")
if success:
    print("调试会话已导出")
```

##### import_session(file_path: str) -> bool

导入调试会话（仅用于查看数据）。

**参数:**
- `file_path`: 导入文件路径

**返回值:**
- `bool`: 是否导入成功

##### reset_debug() -> None

重置调试会话。

### StepType (枚举)

认知步骤类型枚举。

#### 可用值

- `INIT`: 初始化
- `COMPLEXITY_EVAL`: 复杂性评估
- `SUPER_EGO_PRE`: 超我预监督
- `CYCLE_START`: 循环开始
- `STATE_ANALYSIS`: 状态分析
- `DECISION_MAKING`: 决策判断
- `ID_EVALUATION`: 本我评估
- `BODY_EXECUTION`: 身体执行
- `CYCLE_END`: 循环结束
- `SUPER_EGO_POST`: 超我后监督
- `FINALIZE`: 最终化
- `COMPLETED`: 执行完成

### StepResult

步骤执行结果。

#### 属性

- `step_type: StepType`: 步骤类型
- `step_id: str`: 步骤ID
- `timestamp: datetime`: 执行时间戳
- `input_data: Any`: 输入数据
- `output_data: Any`: 输出数据
- `execution_time: float`: 执行时间（秒）
- `agent_layer: str`: 执行层（SuperEgo/Ego/Id/Body/System）
- `next_step: Optional[StepType]`: 下一个步骤
- `debug_info: Dict[str, Any]`: 调试信息
- `error: Optional[Exception]`: 错误信息（如果有）
- `decision_type: Optional[DecisionType]`: 决策类型（如果适用）
- `state_analysis: Optional[str]`: 状态分析结果（如果适用）
- `goal_achieved: Optional[bool]`: 目标是否达成（如果适用）

### StateSnapshot

状态快照。

#### 属性

- `timestamp: datetime`: 快照时间
- `cycle_count: int`: 循环轮数
- `current_step: StepType`: 当前步骤
- `instruction: str`: 执行指令
- `goal_achieved: bool`: 目标是否达成
- `current_state_analysis: str`: 当前状态分析
- `id_evaluation: str`: 本我评估结果
- `memory_length: int`: 内存长度
- `memory_tokens: int`: 内存token数
- `agent_layers_status: Dict[str, Any]`: 各层智能体状态
- `total_steps: int`: 总步骤数
- `execution_time: float`: 执行时间
- `performance_metrics: Dict[str, Any]`: 性能指标

### Breakpoint

断点定义。

#### 属性

- `id: str`: 断点ID
- `step_type: StepType`: 断点的步骤类型
- `condition: Optional[str]`: 断点条件（Python表达式）
- `hit_count: int`: 命中次数
- `enabled: bool`: 是否启用
- `description: str`: 断点描述

### PerformanceReport

性能分析报告。

#### 属性

- `total_time: float`: 总执行时间
- `avg_step_time: float`: 平均步骤耗时
- `slowest_step: str`: 最慢步骤
- `fastest_step: str`: 最快步骤
- `step_time_breakdown: Dict[str, float]`: 按步骤类型的耗时分解
- `cycle_performance: List[Dict[str, Any]]`: 按循环的性能数据
- `memory_usage_trend: List[int]`: 内存使用趋势
- `token_usage_trend: List[int]`: Token使用趋势

## 调试辅助工具

### DebugUtils

调试辅助工具类，提供静态方法。

#### analyze_performance(step_results: List[StepResult]) -> PerformanceReport

分析性能数据。

#### visualize_execution_flow(step_results: List[StepResult]) -> str

可视化执行流程。

#### export_debug_session(debug_state: DebugState, file_path: str) -> bool

导出调试会话。

#### import_debug_session(file_path: str) -> Optional[Dict]

导入调试会话。

## 高级用法

### 条件断点

条件断点允许您在特定条件满足时暂停执行：

```python
# 在第3轮循环的状态分析阶段暂停
debugger.set_breakpoint(
    StepType.STATE_ANALYSIS,
    condition="cycle_count >= 3",
    description="第3轮循环状态分析"
)

# 在决策类型为"判断失败"时暂停
debugger.set_breakpoint(
    StepType.DECISION_MAKING,
    condition="debug_info.get('decision_type') == 'JUDGMENT_FAILED'",
    description="判断失败时暂停"
)
```

### 性能分析

获取详细的性能分析：

```python
report = debugger.get_performance_report()

print(f"性能分析报告:")
print(f"总时间: {report.total_time:.3f}s")
print(f"平均耗时: {report.avg_step_time:.3f}s")
print(f"最慢步骤: {report.slowest_step}")

print(f"\\n步骤耗时分解:")
for step_type, time_spent in report.step_time_breakdown.items():
    percentage = (time_spent / report.total_time) * 100
    print(f"  {step_type}: {time_spent:.3f}s ({percentage:.1f}%)")

print(f"\\n循环性能:")
for cycle_data in report.cycle_performance:
    print(f"  循环 {cycle_data['cycle']}: {cycle_data['total_time']:.3f}s "
          f"({cycle_data['step_count']} 步)")
```

### 执行流程可视化

```python
flow_chart = debugger.visualize_execution_flow()
print(flow_chart)

# 输出示例:
# 🔄 认知循环执行流程
# ==================================================
#  1. 初始化 (⚙️ System) - 0.001s ✅
#  2. 复杂性评估 (🧠 Ego) - 0.234s ✅
#  3. 循环开始 (⚙️ System) - 0.001s ✅
#  4. 状态分析 (🧠 Ego) - 0.187s ✅
#  5. 决策判断 (🧠 Ego) - 0.156s ✅
#     └─ 决策: DecisionType.REQUEST_EVALUATION
#  6. 本我评估 (💫 Id) - 0.123s ✅
#  7. 身体执行 (🏃 Body) - 0.445s ✅
# ==================================================
# 总步骤: 7
# 总时间: 1.147s
```

### 调试会话导出和导入

```python
# 导出调试会话
debugger.export_session("my_debug_session.json")

# 稍后导入查看
debugger.import_session("my_debug_session.json")

# 导出的JSON文件包含:
# - 版本信息
# - 调试状态
# - 完整的步骤历史
# - 性能指标
# - 断点信息
```

### 状态回退和重放

```python
# 执行一些步骤
debugger.run_steps(5)

# 回退到之前的状态
debugger.step_back(2)

# 继续执行（可能会有不同的结果）
debugger.run_one_step()
```

## 最佳实践

### 1. 调试复杂任务

对于复杂的认知任务，建议：

```python
# 1. 启用详细调试信息
agent = CognitiveAgent(llm=llm, verbose=True, max_cycles=10)
debugger = CognitiveDebugger(agent)

# 2. 设置关键断点
debugger.set_breakpoint(StepType.DECISION_MAKING, description="决策检查点")
debugger.set_breakpoint(StepType.ID_EVALUATION, description="评估检查点")

# 3. 分段执行和检查
debugger.start_debug("复杂任务指令")
while not debugger.debug_state.is_finished:
    # 执行到下一个断点
    results = debugger.run_until_breakpoint()
    
    # 检查当前状态
    snapshot = debugger.inspect_state()
    print(f"当前循环: {snapshot.cycle_count}")
    print(f"当前状态: {snapshot.current_state_analysis}")
    
    # 决定是否继续
    user_input = input("继续执行? (y/n): ")
    if user_input.lower() != 'y':
        break
```

### 2. 性能优化

```python
# 运行完整任务
results = debugger.run_to_completion()

# 分析性能瓶颈
report = debugger.get_performance_report()

# 找出最慢的步骤
print(f"性能瓶颈: {report.slowest_step}")

# 分析循环效率
for cycle_data in report.cycle_performance:
    if cycle_data['avg_time'] > 1.0:  # 超过1秒的循环
        print(f"循环 {cycle_data['cycle']} 较慢: {cycle_data['avg_time']:.3f}s")
```

### 3. 错误诊断

```python
# 设置错误捕获断点
debugger.set_breakpoint(
    StepType.BODY_EXECUTION,
    condition="error is not None",
    description="执行错误断点"
)

# 执行并检查错误
step_result = debugger.run_one_step()
if step_result and step_result.error:
    print(f"发现错误: {step_result.error}")
    print(f"错误发生在: {step_result.step_type.value}")
    print(f"输入数据: {step_result.input_data}")
```

## 故障排除

### 常见问题

1. **断点不触发**
   - 检查步骤类型是否正确
   - 验证条件表达式语法
   - 确认断点已启用

2. **性能分析数据不准确**
   - 确保执行了足够的步骤
   - 检查是否有异常干扰执行

3. **状态快照不完整**
   - 确认调试会话已正确初始化
   - 检查智能体配置是否正确

4. **导出/导入失败**
   - 检查文件路径权限
   - 验证JSON格式完整性

### 调试技巧

1. **使用详细输出模式**
   ```python
   agent = CognitiveAgent(llm=llm, verbose=True)
   ```

2. **逐步验证假设**
   ```python
   # 使用条件断点验证特定假设
   debugger.set_breakpoint(
       StepType.STATE_ANALYSIS,
       condition="'错误' in state_analysis",
       description="检查是否检测到错误"
   )
   ```

3. **比较不同执行路径**
   ```python
   # 导出第一次执行
   debugger.export_session("execution_1.json")
   
   # 重置并再次执行
   debugger.reset_debug()
   debugger.start_debug("相同指令")
   # ... 执行 ...
   debugger.export_session("execution_2.json")
   ```

## 版本信息

- **当前版本**: 1.0.0
- **兼容的Python版本**: 3.8+
- **依赖的主要包**: langchain, tiktoken, dataclasses

## 更新日志

### v1.0.0
- 初始版本发布
- 支持单步调试
- 支持断点功能
- 支持性能分析
- 支持状态回退
- 支持会话导入导出

---

**注意**: 本文档描述的是 CognitiveDebugger v1.0.0 的功能。后续版本可能会有功能增强和API变更。