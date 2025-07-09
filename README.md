# AgentFrameWork

<div align="center">

🤖 **先进的多功能 AI Agent 框架** 🤖

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*从静态工作流到认知工作流系统的范式转变*

</div>

## 📖 项目概述

AgentFrameWork 是一个先进的多功能 AI Agent 框架，旨在构建、管理和协调能够自主执行复杂多步骤任务的智能代理。它代表了从传统静态代理框架到认知工作流系统的范式转变。

### 🚀 核心特性

- 🧠 **动态认知工作流** - 具有自然语言前置条件的智能任务编排
- 💾 **智能内存管理** - 自动优化和压缩（默认 60,000 token 限制）
- 👥 **多代理协作** - 无缝的代理间通信和状态共享
- 📊 **生产规则引擎** - 基于规则的工作流执行系统
- 🔍 **任务分解** - 智能任务复杂度分析和自动分解
- ⚡ **实时执行** - 支持流式输出的异步执行
- 🐍 **IPython 集成** - 完整的状态化代码执行环境
- 🔌 **MCP 协议** - 模型上下文协议支持外部工具集成

## 🏗️ 系统架构

### 核心系统

1. **CognitiveWorkflow（认知工作流）** ⭐ *推荐*
   - 革命性的动态导航系统
   - 规划者-决策者-执行者三角色架构
   - 自然语言前置条件取代静态依赖

2. **TaskMasterAgent**
   - 与外部 Task Master AI 集成
   - 智能任务分解和优先级管理
   - 高级依赖关系处理

### 架构组件

- **核心**: `AgentBase`, `Agent`, `StatefulExecutor`
- **高级**: `CognitiveWorkflow`, `TaskMasterAgent`
- **内存**: 多种压缩策略和 token 管理
- **状态**: `GlobalState`, `WorkflowState`, `StateConditionChecker`

## 🛠️ 技术栈

- **Python**: 3.6+
- **LangChain**: 0.1.0+ (核心框架)
- **LLM 支持**: OpenAI, Anthropic, Cohere, DeepSeek
- **Token 管理**: tiktoken 0.5.0+
- **执行环境**: IPython 8.0.0+, Jupyter 1.0.0+

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/AgentFrameWork.git
cd AgentFrameWork

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 API 密钥
```

## 🚀 快速开始

### 使用 CognitiveWorkflow（推荐）

```python
from CognitiveWorkflow.cognitive_workflow import CognitiveWorkflowEngine

# 初始化引擎
engine = CognitiveWorkflowEngine(llm=llm, agents=agents)

# 执行高级目标
result = engine.execute_cognitive_workflow("构建一个完整的网络爬虫并分析数据")
```

### 运行示例

```bash
# 认知工作流演示
cd CognitiveWorkflow
python demo_cognitive_workflow.py

# 简单计算器示例
python simple_calculator.py
```

## 📚 文档

- [CLAUDE.md](CLAUDE.md) - AI 助手开发指南
- [用户快速入门指南](docs/USER_QUICK_START_GUIDE.md)
- [认知工作流核心理念](CognitiveWorkflow/认知工作流的核心理念.md)
- [TaskMaster 集成教程](docs/TASK_MASTER_AI_TUTORIAL.md)

## 🧪 测试

```bash
# 运行所有测试
cd tests
python run_all_tests.py

# 运行特定测试
python test_cognitive_workflow.py

# 运行测试并生成覆盖率报告
./run_tests.sh
```

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有贡献者和支持者，让这个项目成为可能。

---

<div align="center">
Made with ❤️ by the AgentFrameWork Team
</div>