# MultiStepAgent v2 与 v3 设计对比

## 一、核心定位差异
| **特性**         | v2 (动态工作流)                | v3 (静态工作流)                |
|------------------|-------------------------------|-------------------------------|
| **设计目标**     | 处理不可预测的探索性任务        | 执行标准化可复用工作流          |
| **典型场景**     | 用户实时问答/动态问题解决       | 月度报表/定时任务/标准化流程    |
| **工作流生成**   | 运行时动态生成 (`plan_execution`) | 预定义配置加载 (`WorkflowLoader`) |
| **架构哲学**     | "轻量灵活胜于规范"              | "规范可靠胜于灵活"              |

## 二、状态管理对比
### 1. v2 (改进后)
```python
class WorkflowState:
    def __init__(self):
        self.control_state = {}   # 控制流状态
        self.global_state = ""    # 新增：自然语言全局状态描述
        self.state_history = []   # 状态变更历史（简版）
    
    def update_global_state(self, new_state: str):
        """更新全局状态（自动保存历史）"""
        if self.global_state:
            self.state_history.append(self.global_state)
        self.global_state = new_state
```
- **特点**：
  - 轻量化（仅字符串描述）
  - 与步骤执行深度集成
  - 更新点：`execute_single_step()`结束时
- **价值**：
  - 提升复杂工作流可观测性
  - 支持AI修复决策
  - 调试效率提升

### 2. v3
```python
@dataclass
class WorkflowExecutionContext:
    current_global_state: str = ""              # 当前状态
    state_update_history: List[str] = []        # 完整历史
    runtime_variables: Dict[str, Any] = {}      # 结构化变量
```
- **特点**：
  - 双模存储（自然语言+结构化变量）
  - 专用更新器 (`GlobalStateUpdater`)
  - 版本控制（完整历史追溯）
- **价值**：
  - 支持跨步骤状态引用
  - 提供执行统计 (`get_workflow_statistics()`)
  - 条件评估依赖 (`ControlFlowEvaluator`)

## 三、工作流分层设计
| **层面**       | v2                          | v3                              |
|----------------|-----------------------------|---------------------------------|
| **类型层**     | ❌ 无                        | ✅ `WorkflowDefinition`         |
|                |                             | ✅ `WorkflowStep`               |
| **实例层**     | ✅ `plan` 动态列表           | ✅ `WorkflowExecutionContext`   |
|                | ✅ 步骤字典 (含状态字段)     | ✅ `StepExecution`              |
| **验证机制**   | ❌ 无                        | ✅ `validate()` 方法            |
| **持久化**     | ❌ 运行时丢失                 | ✅ `WorkflowLoader` 文件支持     |

## 四、控制流实现差异
| **能力**         | v2                            | v3                              |
|------------------|-------------------------------|---------------------------------|
| 循环管理         | `should_break_loop()`         | `ControlFlowType.LOOP`          |
| 条件分支         | 内嵌决策逻辑                   | `ControlFlowEvaluator` 组件     |
| 错误处理         | `handle_generate_fix_task_and_loop()` | `ErrorHandling` 配置化方案     |
| 并行执行         | ❌ 不支持                      | ✅ `ControlFlowType.PARALLEL`    |

## 五、选用指南
### 何时选择 v2？
1. **完全动态场景**：用户问题无法预先确定步骤
2. **简易任务**：步骤数 < 5 的轻量级工作流
3. **快速原型开发**：避免配置开销

### 何时选择 v3？
1. **标准化流程**：需重复执行的固定工作流
2. **复杂控制流**：含并行/条件分支/错误处理
3. **团队协作**：需契约化接口 (YAML/JSON)

### 混合使用模式
```python
def execute_workflow(instruction: Union[str, Path]):
    if isinstance(instruction, Path):  # 配置文件
        return v3_engine.run(instruction)
    else:  # 动态指令
        return v2_agent.run(instruction)
```

## 六、演进路线
### v2 优化方向
1. 添加全局状态（当前优先级）
2. 增加轻量级历史追溯（`deque` 实现）
3. 保持动态性核心优势

### v3 优化方向
1. 增强AI状态更新 (`_llm_state_update`)
2. 完善跨工作流调用
3. 优化大工作流执行性能

> **核心结论**：二者互补而非替代，v2 的灵活性与 v3 的规范性共同构成完整的工作流解决方案。
