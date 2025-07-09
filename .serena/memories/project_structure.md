# 项目结构

## 根目录布局
```
AgentFrameWork/
├── CognitiveWorkflow/          # 高级认知工作流系统
│   ├── cognitive_workflow.py   # 核心引擎（1000+ 行）
│   ├── cognitive_workflow_adapter.py
│   ├── cognitive_workflow_rule_base/  # 生产规则系统
│   └── examples/               # 演示和测试文件
├── static_workflow/            # 静态工作流实现
├── task_master/               # TaskMaster AI 集成
├── examples/                  # 使用示例
├── tests/                     # 综合测试套件
├── mcp_examples/             # 模型上下文协议示例
├── docs/                     # 文档文件
└── embodied_cognitive_workflow/  # 具身认知功能

## 核心文件
- agent_base.py               # 基础代理类
- pythonTask.py              # StatefulExecutor 实现
- enhancedAgent_v2.py        # 遗留多步骤代理
- MultiStepAgent_v3.py       # 改进的多步骤代理
- task_master_agent.py       # TaskMaster 集成
- response_parser_v2.py      # 响应解析系统
- message_compress.py        # 内存压缩

## 配置
- config.yaml                # 主配置
- config_system.py           # 配置管理
- prompts.py                 # 系统提示词
- .env.example              # 环境模板
- requirements.txt          # Python 依赖

## 关键目录
- **CognitiveWorkflow**: 最先进的推荐系统
- **tests**: 60+ 测试文件覆盖所有组件
- **examples**: 实用的使用演示
- **docs**: 教程和指南（英文/中文）

## 入口点
- CognitiveWorkflow 演示用于新项目
- 遗留代理文件用于现有系统
- TaskMaster 用于复杂任务分解
- MCP 示例用于外部工具集成