# TaskMasterAgent 集成指南

## 概述

`TaskMasterAgent` 是一个全新的多步骤智能体实现，它完全集成了 Task Master AI 的强大功能，同时保持了 AgentFrameWork 的多智能体协作能力。这个实现提供了三种执行模式，以满足不同的使用需求。

## 核心特性

### 🎯 智能任务管理
- **AI 驱动的任务分解**: 使用 Task Master AI 的智能分析进行任务规划
- **复杂度分析**: 自动评估任务复杂度并提供优化建议
- **依赖关系管理**: 强大的任务依赖图管理和验证
- **智能扩展**: 自动将复杂任务分解为可管理的子任务

### 🔄 多执行模式
1. **Task Master AI 原生模式** (`tm_native`): 完全使用 Task Master AI 进行规划和管理
2. **混合模式** (`hybrid`): Task Master AI 规划 + AgentFrameWork 执行
3. **兼容模式** (`legacy`): 向后兼容原始 MultiStepAgent_v2 逻辑

### 🧠 增强决策系统
- **多维度分析**: 结合复杂度分析、项目状态、执行历史的智能决策
- **12种决策选项**: 从基本的继续/重试到高级的工作流优化
- **自动故障恢复**: 智能生成故障恢复计划

### 🔬 研究功能集成
- **AI 研究支持**: 内置 Task Master AI 的研究功能
- **技术决策辅助**: 为复杂决策提供研究支持
- **知识库集成**: 将研究结果保存到任务中

## 快速开始

### 1. 基本安装

```bash
# 确保安装了必要的依赖
pip install langchain_openai tiktoken
```

### 2. 创建基本实例

```python
from langchain_openai import ChatOpenAI
from task_master_agent import TaskMasterAgent, AgentSpecification
from pythonTask import Agent

# 创建 LLM 实例
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

# 创建智能体
coder = Agent(llm=llm, stateful=True)
coder.api_specification = "编程实现智能体"

tester = Agent(llm=llm, stateful=True)
tester.api_specification = "软件测试智能体"

# 注册智能体
agent_specs = [
    AgentSpecification("coder", coder, "负责编程和代码实现"),
    AgentSpecification("tester", tester, "负责软件测试和质量保证")
]

# 创建 TaskMasterAgent
tm_agent = TaskMasterAgent(
    project_root="./my_project",
    llm=llm,
    agent_specs=agent_specs,
    auto_init=True
)
```

### 3. 执行任务

```python
# Task Master AI 原生模式
result = tm_agent.execute_multi_step(
    main_instruction="开发一个计算器应用",
    mode="tm_native"
)

# 混合模式
result = tm_agent.execute_multi_step(
    main_instruction="开发一个待办事项管理器",
    mode="hybrid"
)

# 使用 PRD 驱动开发
prd_content = """
产品需求文档：博客系统
1. 用户管理功能
2. 文章发布功能
3. 评论系统
"""

result = tm_agent.execute_multi_step(
    main_instruction="根据PRD开发博客系统",
    mode="tm_native",
    use_prd=True,
    prd_content=prd_content
)
```

## 高级功能

### 配置管理

```python
from task_master.config import TaskMasterConfig

# 创建自定义配置
config = TaskMasterConfig()
config.set("task_management.complexity_threshold", 7)
config.set("ai_models.use_research", True)
config.set("execution.max_retries", 5)

# 应用配置
tm_agent = TaskMasterAgent(
    project_root="./my_project",
    llm=llm,
    config=config
)
```

### 研究功能

```python
# 进行技术研究
research_result = tm_agent.research(
    query="Python 单元测试最佳实践",
    save_to_task="3"  # 保存到任务3
)

# 获取复杂度分析
analysis = tm_agent.get_complexity_analysis()
print(f"项目复杂度: {analysis}")
```

### 智能决策

```python
from agent_base import Result

# 模拟执行结果
result = Result(True, "test_code", "success", "", "完成")
task_context = {
    "task_id": "1",
    "task_name": "测试任务",
    "agent_name": "coder"
}

# 进行增强决策
decision = tm_agent.enhanced_decision_making(result, task_context)
print(f"决策: {decision['action']}")
print(f"理由: {decision['reason']}")

# 执行决策
tm_agent.execute_enhanced_decision(decision)
```

### 项目状态监控

```python
# 获取项目状态
status = tm_agent.get_project_status()
print(f"总任务数: {status['total_tasks']}")
print(f"状态分布: {status['status_breakdown']}")
print(f"下一个任务: {status['next_task']}")

# 同步状态
tm_agent.sync_with_tm()
```

## 与 MultiStepAgent_v2 的对比

| 特性 | MultiStepAgent_v2 | TaskMasterAgent |
|------|-------------------|-----------------|
| **任务规划** | 内置 LLM 规划 | Task Master AI 智能分解 |
| **依赖管理** | 简单先决条件 | 强大的依赖图管理 |
| **复杂度分析** | 无 | AI 驱动的复杂度评估 |
| **任务扩展** | 手动分解 | 自动智能扩展 |
| **决策系统** | 基本决策选项 | 12种增强决策选项 |
| **研究功能** | 无 | 内置 AI 研究功能 |
| **项目管理** | 内存存储 | 持久化项目结构 |
| **团队协作** | 基础支持 | 标签、分支、协作功能 |
| **配置管理** | 简单参数 | 完整配置系统 |
| **状态同步** | 无 | 双向状态同步 |

## 迁移指南

### 从 MultiStepAgent_v2 迁移

1. **保持原有代码不变**: TaskMasterAgent 是全新实现，不影响现有代码
2. **逐步迁移**: 可以在同一项目中同时使用两种实现
3. **兼容模式**: 使用 `legacy` 模式可以调用原始逻辑

```python
# 原有代码
from enhancedAgent_v2 import MultiStepAgent_v2
legacy_agent = MultiStepAgent_v2(llm=llm, agent_specs=agent_specs)

# 新代码（兼容模式）
tm_agent = TaskMasterAgent(llm=llm, agent_specs=agent_specs)
result = tm_agent.execute_multi_step(instruction, mode="legacy")

# 新代码（原生模式）
result = tm_agent.execute_multi_step(instruction, mode="tm_native")
```

### 配置迁移

```python
# 将现有配置转换为 TaskMaster 配置
config = TaskMasterConfig()
config.set("execution.max_retries", your_max_retries)
config.set("ai_models.main_model", your_model_name)
```

## 最佳实践

### 1. 模式选择指南

- **使用 `tm_native` 模式当**:
  - 项目复杂度较高
  - 需要强大的依赖管理
  - 希望利用 AI 研究功能
  - 团队协作需求

- **使用 `hybrid` 模式当**:
  - 希望保持现有执行逻辑
  - 只需要改进任务规划
  - 渐进式迁移

- **使用 `legacy` 模式当**:
  - 需要向后兼容
  - 现有逻辑已经稳定
  - 测试和验证阶段

### 2. 配置优化

```python
# 高性能配置
config.set("execution.sync_frequency", "batch")
config.set("task_management.auto_expand_complex", False)
config.set("ai_models.use_research", False)

# 高质量配置
config.set("task_management.complexity_threshold", 3)
config.set("ai_models.use_research", True)
config.set("execution.retry_failed", True)
```

### 3. 错误处理

```python
try:
    result = tm_agent.execute_multi_step(instruction)
except Exception as e:
    # 自动故障恢复
    recovery_decision = tm_agent.enhanced_decision_making(
        current_result=None,
        task_context={"error": str(e)}
    )
    if recovery_decision["action"] == "generate_recovery_plan":
        tm_agent.execute_enhanced_decision(recovery_decision)
```

### 4. 性能监控

```python
# 定期检查项目状态
status = tm_agent.get_project_status()
if status["status_breakdown"].get("failed", 0) > 3:
    # 触发故障分析
    analysis = tm_agent.get_complexity_analysis()
    # 调整策略
```

## 故障排除

### 常见问题

1. **初始化失败**
   ```python
   # 检查项目目录权限
   # 确保 .taskmaster 目录可写
   ```

2. **API 错误**
   ```python
   # 确保设置了正确的 API 密钥
   os.environ["OPENAI_API_KEY"] = "your-api-key"
   ```

3. **模拟模式运行**
   ```python
   # TaskMasterClient 包含模拟实现
   # 用于测试和开发环境
   ```

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查配置**
   ```python
   print(tm_agent.config.get_all())
   ```

3. **验证智能体注册**
   ```python
   print([spec.name for spec in tm_agent.agent_specs])
   ```

## 扩展开发

### 自定义决策逻辑

```python
class CustomTaskMasterAgent(TaskMasterAgent):
    def enhanced_decision_making(self, current_result, task_context, task_history=None):
        # 自定义决策逻辑
        decision = super().enhanced_decision_making(current_result, task_context, task_history)
        
        # 添加自定义处理
        if task_context.get("priority") == "critical":
            decision["action"] = "prioritize"
        
        return decision
```

### 自定义智能体

```python
class SpecializedAgent(Agent):
    def __init__(self, llm, domain="general"):
        super().__init__(llm, stateful=True)
        self.domain = domain
        self.api_specification = f"专门处理{domain}领域的智能体"
    
    def execute_sync(self, instruction):
        # 自定义执行逻辑
        enhanced_instruction = f"作为{self.domain}专家，{instruction}"
        return super().execute_sync(enhanced_instruction)
```

## 总结

`TaskMasterAgent` 提供了一个强大、灵活且易于使用的多步骤任务执行系统。通过集成 Task Master AI 的智能功能，它显著提升了项目管理和任务执行的效率和质量。

### 主要优势

1. **智能化**: AI 驱动的任务分解和决策制定
2. **灵活性**: 三种执行模式适应不同需求
3. **可扩展性**: 完整的配置和扩展系统
4. **兼容性**: 与现有系统无缝集成
5. **可靠性**: 强大的错误处理和恢复机制

### 下一步

1. 尝试基本示例 (`examples/basic_task_master.py`)
2. 阅读 Task Master AI 官方文档
3. 根据项目需求选择合适的执行模式
4. 逐步迁移现有项目
5. 探索高级功能和自定义扩展

欢迎在 GitHub 上提出问题和建议，帮助我们持续改进这个系统！