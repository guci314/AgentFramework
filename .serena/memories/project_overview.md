# AgentFrameWork 项目概览

## 项目目的
AgentFrameWork 是一个先进的多功能 AI Agent 框架，旨在构建、管理和协调能够自主执行复杂多步骤任务的智能代理。它代表了从传统静态代理框架到认知工作流系统的范式转变。

## 项目演进
1. **早期阶段**: 带有多代理协作的静态工作流
2. **中期阶段**: 迭代优化，改进核心逻辑
3. **当前状态**: 两个先进系统：
   - **CognitiveWorkflow（认知工作流）**: 具有规划者-决策者-执行者角色的动态导航
   - **TaskMasterAgent**: 与外部 Task Master AI 的集成

## 核心特性
- 具有自然语言前置条件的动态认知工作流
- 智能内存管理（默认 60,000 token 限制）
- 多代理协作和状态共享
- 基于生产规则的工作流引擎
- 任务分解和复杂度分析
- 实时流式执行
- 基于 IPython 的状态化代码执行
- MCP（模型上下文协议）集成

## 架构组件
- **核心组件**: AgentBase、Agent、StatefulExecutor
- **高级组件**: CognitiveWorkflow、TaskMasterAgent
- **内存管理**: 压缩策略、token 管理
- **状态管理**: GlobalState、WorkflowState、StateConditionChecker
- **集成支持**: LLM 支持（OpenAI、Anthropic、Cohere、DeepSeek）

## 开发理念
- 新项目优先使用 CognitiveWorkflow
- 使用适配器进行遗留系统迁移
- 自然语言前置条件优于静态依赖
- 动态运行时编排
- 全面的测试和监控