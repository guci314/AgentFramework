# CognitiveDebugger 设计文档

## 1. 概述

### 1.1 目标
CognitiveDebugger 是一个用于调试具身认知工作流的包装器工具，提供单步执行、状态检查、断点设置等调试功能，帮助开发者深入理解和优化认知循环的执行过程。

### 1.2 设计原则
- **非侵入性**: 通过包装器模式，不修改原有 CognitiveAgent 代码
- **细粒度控制**: 将认知循环拆解为原子级步骤，支持精确调试
- **状态透明**: 提供完整的状态可视化和修改能力
- **交互友好**: 提供直观的调试接口和丰富的调试信息

## 2. 架构设计

### 2.1 整体架构
```
┌─────────────────────────────────────┐
│         CognitiveDebugger           │
├─────────────────────────────────────┤
│  - wrapped_agent: CognitiveAgent    │
│  - debug_state: DebugState          │
│  - step_executor: StepExecutor      │
│  - breakpoint_manager: BreakpointMgr│
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│         CognitiveAgent              │
│    (原有认知智能体，不修改)           │
└─────────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 CognitiveDebugger (主调试器)
- **职责**: 调试会话管理、对外接口提供
- **主要方法**:
  - `start_debug(instruction: str)`: 开始调试会话
  - `run_one_step() -> StepResult`: 执行单步
  - `run_until_breakpoint() -> List[StepResult]`: 运行到断点
  - `run_to_completion() -> DebugSession`: 运行到结束
  - `inspect_state() -> StateSnapshot`: 检查当前状态
  - `modify_context(modifications: Dict)`: 修改上下文
  - `set_breakpoint(step_type: StepType, condition: str)`: 设置断点

#### 2.2.2 DebugState (调试状态)
- **职责**: 维护调试过程中的所有状态信息
- **主要属性**:
  ```python
  @dataclass
  class DebugState:
      # 执行状态
      current_step: StepType
      cycle_count: int
      is_finished: bool
      execution_start_time: datetime
      
      # 上下文状态
      workflow_context: WorkflowContext
      agent_memory_snapshot: List[BaseMessage]
      
      # 执行历史
      step_history: List[StepResult]
      execution_trace: List[ExecutionTrace]
      
      # 调试控制
      breakpoints: List[Breakpoint]
      step_metadata: Dict[str, Any]
  ```

#### 2.2.3 StepExecutor (步骤执行器)
- **职责**: 执行具体的认知步骤，管理步骤间的状态转换
- **主要方法**:
  - `execute_step(step_type: StepType, input_data: Any) -> StepResult`
  - `get_next_step(current_step: StepType, step_result: StepResult) -> StepType`
  - `can_execute_step(step_type: StepType) -> bool`

#### 2.2.4 BreakpointManager (断点管理器)
- **职责**: 管理断点设置、条件检查、断点触发
- **主要方法**:
  - `add_breakpoint(breakpoint: Breakpoint)`
  - `remove_breakpoint(breakpoint_id: str)`
  - `check_breakpoint(step_type: StepType, context: Dict) -> bool`
  - `list_breakpoints() -> List[Breakpoint]`

## 3. 步骤定义

### 3.1 步骤类型枚举
```python
class StepType(Enum):
    # 初始化阶段
    INIT = "初始化"
    COMPLEXITY_EVAL = "复杂性评估"
    SUPER_EGO_PRE = "超我预监督"
    
    # 认知循环阶段
    CYCLE_START = "循环开始"
    STATE_ANALYSIS = "状态分析"
    DECISION_MAKING = "决策判断"
    ID_EVALUATION = "本我评估"
    BODY_EXECUTION = "身体执行"
    CYCLE_END = "循环结束"
    
    # 结束阶段
    SUPER_EGO_POST = "超我后监督"
    FINALIZE = "最终化"
    COMPLETED = "执行完成"
```

### 3.2 步骤执行流程
```
INIT → COMPLEXITY_EVAL → 分支判断
├── 简单任务: BODY_EXECUTION → FINALIZE → COMPLETED
└── 复杂任务: SUPER_EGO_PRE → CYCLE_START → 
    ┌─循环────────────────────────────────┐
    │ STATE_ANALYSIS → DECISION_MAKING → │
    │ ├── REQUEST_EVALUATION → ID_EVALUATION │
    │ ├── JUDGMENT_FAILED → BODY_EXECUTION   │
    │ └── CONTINUE_CYCLE → CYCLE_END      │
    └─────────────────────────────────────┘
    → SUPER_EGO_POST → FINALIZE → COMPLETED
```

## 4. 数据结构

### 4.1 StepResult (步骤执行结果)
```python
@dataclass
class StepResult:
    # 基本信息
    step_type: StepType
    step_id: str
    timestamp: datetime
    
    # 执行数据
    input_data: Any
    output_data: Any
    execution_time: float
    
    # 状态信息
    agent_layer: str  # 执行层 (SuperEgo/Ego/Id/Body)
    next_step: Optional[StepType]
    
    # 调试信息
    debug_info: Dict[str, Any]
    error: Optional[Exception]
    
    # 认知相关
    decision_type: Optional[DecisionType]
    state_analysis: Optional[str]
    goal_achieved: Optional[bool]
```

### 4.2 ExecutionTrace (执行轨迹)
```python
@dataclass
class ExecutionTrace:
    trace_id: str
    cycle_number: int
    step_sequence: List[StepType]
    decision_path: List[DecisionType]
    state_changes: List[StateChange]
    performance_metrics: PerformanceMetrics
```

### 4.3 Breakpoint (断点)
```python
@dataclass
class Breakpoint:
    id: str
    step_type: StepType
    condition: Optional[str]  # Python表达式
    hit_count: int
    enabled: bool
    description: str
```

### 4.4 StateSnapshot (状态快照)
```python
@dataclass
class StateSnapshot:
    timestamp: datetime
    cycle_count: int
    current_step: StepType
    
    # 上下文状态
    instruction: str
    goal_achieved: bool
    current_state_analysis: str
    id_evaluation: str
    
    # 智能体状态
    memory_length: int
    memory_tokens: int
    agent_layers_status: Dict[str, Any]
    
    # 执行统计
    total_steps: int
    execution_time: float
    performance_metrics: Dict[str, Any]
```

## 5. 接口设计

### 5.1 主要接口
```python
class CognitiveDebugger:
    def __init__(self, cognitive_agent: CognitiveAgent):
        """初始化调试器"""
        
    def start_debug(self, instruction: str) -> None:
        """开始调试会话"""
        
    def run_one_step(self) -> StepResult:
        """执行单步"""
        
    def run_steps(self, count: int) -> List[StepResult]:
        """执行指定步数"""
        
    def run_until_breakpoint(self) -> List[StepResult]:
        """运行到下一个断点"""
        
    def run_to_completion(self) -> DebugSession:
        """运行到结束"""
        
    def inspect_state(self) -> StateSnapshot:
        """检查当前状态"""
        
    def get_execution_trace(self) -> List[ExecutionTrace]:
        """获取执行轨迹"""
        
    def set_breakpoint(self, step_type: StepType, condition: str = None) -> str:
        """设置断点"""
        
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点"""
        
    def modify_context(self, **modifications) -> bool:
        """修改上下文"""
        
    def step_back(self, steps: int = 1) -> bool:
        """回退步骤"""
        
    def reset_debug(self) -> None:
        """重置调试会话"""
```

### 5.2 调试辅助接口
```python
class DebugUtils:
    @staticmethod
    def visualize_execution_flow(execution_trace: List[ExecutionTrace]) -> str:
        """可视化执行流程"""
        
    @staticmethod
    def analyze_performance(step_results: List[StepResult]) -> PerformanceReport:
        """性能分析"""
        
    @staticmethod
    def export_debug_session(debug_state: DebugState) -> Dict:
        """导出调试会话"""
        
    @staticmethod
    def import_debug_session(session_data: Dict) -> DebugState:
        """导入调试会话"""
```

## 6. 使用示例

### 6.1 基本单步调试
```python
# 创建调试器
agent = CognitiveAgent(llm=llm)
debugger = CognitiveDebugger(agent)

# 开始调试
debugger.start_debug("分析销售数据并生成报告")

# 单步执行
while not debugger.debug_state.is_finished:
    step_result = debugger.run_one_step()
    
    print(f"步骤: {step_result.step_type}")
    print(f"执行层: {step_result.agent_layer}")
    print(f"输出: {step_result.output_data}")
    print(f"耗时: {step_result.execution_time:.3f}s")
    
    # 用户交互
    cmd = input("命令 (c=继续, i=检查, b=断点, q=退出): ")
    if cmd == 'q':
        break
    elif cmd == 'i':
        snapshot = debugger.inspect_state()
        print(f"当前状态: {snapshot}")
    elif cmd == 'b':
        debugger.set_breakpoint(StepType.DECISION_MAKING)
```

### 6.2 断点调试
```python
# 设置断点
debugger.set_breakpoint(
    step_type=StepType.DECISION_MAKING,
    condition="decision_type == DecisionType.JUDGMENT_FAILED"
)

# 运行到断点
results = debugger.run_until_breakpoint()
print(f"在断点停止，执行了 {len(results)} 步")

# 检查状态
state = debugger.inspect_state()
print(f"决策类型: {state.debug_info['decision_type']}")
```

### 6.3 性能分析
```python
# 运行完整调试
session = debugger.run_to_completion()

# 分析性能
report = DebugUtils.analyze_performance(session.step_results)
print(f"总执行时间: {report.total_time}")
print(f"平均步骤耗时: {report.avg_step_time}")
print(f"最慢步骤: {report.slowest_step}")

# 可视化执行流程
flow_chart = DebugUtils.visualize_execution_flow(session.execution_trace)
print(flow_chart)
```

## 7. 实现要点

### 7.1 状态保存与恢复
- 每个步骤执行前保存完整状态快照
- 支持回退到任意历史状态
- 内存状态的深拷贝机制

### 7.2 异常处理
- 步骤执行异常的捕获和处理
- 调试器本身异常的隔离
- 原有智能体异常的透传

### 7.3 性能优化
- 状态快照的增量保存
- 大量调试数据的内存管理
- 可选的详细程度控制

### 7.4 扩展性
- 插件式的步骤执行器
- 自定义调试指标
- 第三方调试工具集成

## 8. 后续扩展

### 8.1 可视化界面
- Web界面的步骤可视化
- 认知循环流程图
- 实时状态监控

### 8.2 高级调试功能
- 条件断点和计数断点
- 变量监视和修改
- 执行路径回放

### 8.3 协作调试
- 多人调试会话
- 调试会话分享
- 远程调试支持

---

**文档版本**: v1.0  
**创建日期**: 2025-01-08  
**最后更新**: 2025-01-08  
**作者**: AI Assistant  
**状态**: 设计阶段