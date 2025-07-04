# 具身认知工作流系统

基于具身认知理论的智能体工作流实现，实现了自我-本我-身体三层架构的动态认知循环。

## 核心架构

### 三层架构
- **心灵层**：
  - `自我智能体 (EgoAgent)`：理性思考、状态分析、指令生成
  - `本我智能体 (IdAgent)`：价值驱动、目标设定、评估监控
- **身体层**：`Agent类`：代码生成、执行、评估一体化
- **协调层**：`EmbodiedCognitiveWorkflow`：统一协调三层交互

### 工作流程
1. **初始化本我**：设定价值标准和目标
2. **认知循环**：
   - 自我分析当前状态
   - 自我决策下一步行动（继续循环/请求评估/判断失败）
   - 生成观察或执行指令
   - 身体执行指令
   - 本我评估目标达成情况

## 快速开始

### 基本使用

```python
from embodied_cognitive_workflow import EmbodiedCognitiveWorkflow
from langchain_openai import ChatOpenAI

# 初始化语言模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 创建工作流
workflow = EmbodiedCognitiveWorkflow(llm=llm)

# 执行任务
result = workflow.执行认知循环("创建一个Calculator类和单元测试")

print(f"执行结果：{result.return_value}")
```

### 便利函数

```python
from embodied_cognitive_workflow import 执行具身认知任务
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo")
result = 执行具身认知任务(llm, "创建一个Calculator类和单元测试")
```

## 运行演示

```bash
# 设置环境变量
export OPENAI_API_KEY='your-api-key'

# 运行Calculator演示
cd embodied_cognitive_workflow
python calculator_demo.py
```

## 核心特性

### 1. 动态认知循环
- 不预设计划，"走一步看一步"
- 基于即时感知做出理性决策
- 自适应的问题解决过程

### 2. 价值驱动决策
- 本我设定明确的价值标准
- 实时监控目标达成情况
- 价值导向的评估和反馈

### 3. 自然语言交互
- 所有组件间用自然语言通信
- 便于理解和调试
- 支持复杂任务的语义理解

### 4. 三层架构协同
- 心灵层负责思考和价值判断
- 身体层负责具体执行
- 协调层管理整体流程

## 配置选项

```python
workflow = EmbodiedCognitiveWorkflow(
    llm=llm,
    身体配置={
        "stateful": True,
        "max_retries": 10,
        "skip_evaluation": False
    },
    最大循环次数=50,
    详细日志=True
)
```

## API 参考

### EmbodiedCognitiveWorkflow

主要方法：
- `执行认知循环(指令: str) -> Result`：执行完整的认知工作流
- `获取工作流状态() -> dict`：获取当前状态信息
- `加载知识(知识: str)`：向所有组件加载知识
- `重置工作流()`：重置工作流状态

### EgoAgent (自我智能体)

主要方法：
- `分析当前状态(上下文: str) -> str`：分析当前状态
- `决策下一步行动(状态分析: str) -> str`：决策行动方向
- `生成观察指令(思考结果: str) -> str`：生成观察指令
- `生成执行指令(感知结果: str) -> str`：生成执行指令

### IdAgent (本我智能体)

主要方法：
- `初始化价值系统(指令: str) -> str`：设定目标和价值标准
- `生成评估指令(评估请求: str) -> str`：生成观察指令
- `评估目标达成(观察结果: str) -> str`：评估目标完成情况

## 错误处理

系统包含完善的错误处理机制：
- 执行失败时的自动重试和错误分析
- 循环次数限制防止无限循环
- 详细的日志记录便于调试

## 注意事项

1. 需要设置 `OPENAI_API_KEY` 环境变量
2. 建议使用 GPT-3.5-turbo 或更高版本的模型
3. 复杂任务可能需要调整最大循环次数
4. 详细日志模式会产生大量输出，生产环境可关闭