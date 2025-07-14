# Cognitive Debugger 重构文档

## 概述

本文档记录了 `cognitive_debugger.py` 为适应 CognitiveAgent 重构所做的必要更改。

## 主要修改

### 1. 移除 `body` 属性引用

#### 问题
- CognitiveAgent 不再维护 `self.body` 属性
- 调试器试图访问 `self.wrapped_agent.body` 导致 AttributeError

#### 解决方案
```python
# 旧代码
"body": {"available": bool(self.wrapped_agent.body)},

# 新代码
"agents": {"available": bool(self.wrapped_agent.agents), "count": len(self.wrapped_agent.agents) if self.wrapped_agent.agents else 0},
```

### 2. 更新评估接口调用

#### 问题
- Id agent 的 `evaluate_with_context` 方法参数从 `body_executor` 改为 `agents`

#### 解决方案
```python
# 旧代码
body_executor=self.agent.body

# 新代码
agents=self.agent.agents
```

### 3. 修复身体执行逻辑

#### 问题
- 直接执行模式和认知循环模式的身体执行需要不同的处理方式

#### 解决方案
```python
def _execute_body_execution(self, input_data: Any, debug_state: DebugState) -> tuple:
    """身体执行步骤"""
    # 检查是否是直接执行模式
    if isinstance(input_data, bool) and input_data:  # can_handle_directly = True
        # 直接执行模式
        instruction = debug_state.workflow_context.instruction
        quick_prompt = f"""直接完成以下任务：
{instruction}

请提供清晰、准确的结果。"""
        execution_result = self.agent._execute_body_operation(quick_prompt)
    else:
        # 认知循环模式
        default_agent = self.agent.agents[0] if self.agent.agents else None
        if default_agent:
            execution_result = default_agent.execute_sync(current_context)
        else:
            execution_result = Result(...)
```

### 4. 控制流修正

#### 问题
- 直接执行模式不应进入循环结束步骤

#### 解决方案
```python
# 直接执行模式应该结束，而不是继续循环
next_step = StepType.FINALIZE if (isinstance(input_data, bool) and input_data) else StepType.CYCLE_END
```

## 执行模式区分

调试器现在正确区分两种执行模式：

### 1. 直接处理模式
- 复杂性评估返回 `True`
- 流程：初始化 → 复杂性评估 → 身体执行 → 最终化
- 使用 `_execute_body_operation` 方法

### 2. 认知循环模式
- 复杂性评估返回 `False`
- 流程：初始化 → 复杂性评估 → 元认知预监督 → 循环开始 → ... → 循环结束 → 最终化
- 使用默认 Agent 的 `execute_sync` 方法

## 兼容性说明

这些修改确保了：
1. 调试器与重构后的 CognitiveAgent 完全兼容
2. 支持新的多 Agent 架构
3. 正确处理直接执行和认知循环两种模式
4. 保持调试功能的完整性

## 测试验证

修改后的调试器通过了以下测试：
- ✅ 直接处理模式的简单计算任务
- ✅ 状态检查和快照功能
- ✅ 性能分析功能
- ✅ 调试信息记录

## 注意事项

1. `cognitive_debug_agent.py` 不需要修改，因为它使用的是 CognitiveAgent 的公共 API
2. 调试器现在正确识别和处理两种执行模式
3. 所有对 `body` 的引用都已更新为使用 `agents` 列表