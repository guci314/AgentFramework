# AgentFrameWork

一个基于LangChain的多智能体协作框架，支持复杂任务的分解、规划和执行。

## 特性

- **多步骤任务规划**: 自动将复杂任务分解为可执行的步骤
- **智能体协作**: 支持多个智能体协同工作
- **动态控制流**: 支持循环、条件分支等复杂执行逻辑
- **记忆管理**: 智能的记忆压缩和管理机制
- **状态管理**: 完整的执行状态跟踪

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from AgentFrameWork import MultiStepAgent_v2, Agent
from langchain_openai import ChatOpenAI

# 初始化LLM
llm = ChatOpenAI(model="gpt-4")

# 创建多步骤智能体
multi_agent = MultiStepAgent_v2(llm=llm)

# 注册成员智能体
coder = Agent(llm=llm)
multi_agent.register_agent("coder", coder)

# 执行任务
result = multi_agent.execute_multi_step("请用python写一个hello world程序")
print(result)
```

## 核心组件

### MultiStepAgent_v2
主要的多步骤智能体类，负责任务规划和执行协调。

### Agent
基础智能体类，可以执行具体的任务。

### StatefulExecutor
状态执行器，提供代码执行和变量管理功能。

## 文档

详细文档请参考代码中的注释和示例。

## 许可证

MIT License 