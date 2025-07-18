# 具身认知工作流 (Embodied Cognitive Workflow) - Claude 项目指南

## 项目概述

这是一个基于具身认知理论的四层架构智能体工作流系统，实现了完整的认知循环和动态任务执行能力。

## 核心架构

### 四层认知架构
1. **MetaCognitive (元认知)** - 监督、道德约束、策略优化
2. **Ego (自我)** - 理性决策、状态分析、Agent选择
3. **Id (本我)** - 价值评估、目标监控、任务规格
4. **Body (身体)** - 执行感知、工具调用、多Agent协作

## 主要模块

### 核心工作流
- `embodied_cognitive_workflow/embodied_cognitive_workflow.py` - 主认知工作流协调器
- `embodied_cognitive_workflow/meta_cognitive_agent.py` - 元认知智能体
- `embodied_cognitive_workflow/ego_agent.py` - 自我智能体
- `embodied_cognitive_workflow/id_agent.py` - 本我智能体

### 调试系统
- `embodied_cognitive_workflow/cognitive_debugger.py` - 认知调试器（1800+行）
- `embodied_cognitive_workflow/visual_debugger.py` - 可视化调试器GUI

### 示例和演示
- `embodied_cognitive_workflow/demo/` - 演示文件目录
  - `demo_visual_debugger_usage.py` - 调试器使用示例

## 关键技术特性

### 认知循环
- 动态导航：无预定义流程，基于状态实时决策
- 增量式规划：边执行边规划，自适应调整
- 自然语言驱动：使用自然语言描述状态和决策

### 多Agent协作（2025-01-16新增）
- Ego智能选择机制：根据任务需求选择合适的Agent
- 支持多专业Agent：数学专家、文件专家、算法工程师等
- 动态Agent信息传递：决策时传递可用Agent信息

### 调试能力
- 11步认知循环拆解
- 单步执行和断点调试
- 性能分析和状态管理
- 可视化调试界面

## 使用说明

### 基本使用
```python
from embodied_cognitive_workflow.embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model

# 创建LLM
llm = get_model('gemini_2_5_flash')

# 创建专业Agent
agent = Agent(llm=llm)
agent.name = "通用助手"
agent.set_api_specification("通用任务执行能力")

# 创建认知智能体
cognitive_agent = CognitiveAgent(
    llm=llm,
    agents=[agent],
    max_cycles=10,
    verbose=True,
    enable_meta_cognition=False
)

# 执行任务
result = cognitive_agent.execute_sync("你的任务描述")
```

### 可视化调试
```python
from embodied_cognitive_workflow.visual_debugger import CycleDebuggerGUI

# 创建调试器GUI
debugger = CycleDebuggerGUI(cognitive_agent)
debugger.run()
```

## 重要提醒

### 模型配置
- 使用 `llm_lazy.py` 获取模型（推荐）
- 不要使用 `pythonTask.py`，使用 `python_core.py`

### LangChain缓存
- 自动启用SQLite缓存（.langchain.db）
- 所有Agent共享同一缓存

### 环境要求
```python
# 需要设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"
```

## 项目进展

### 已完成 ✅
- 四层认知架构实现
- 认知循环工作流
- 多Agent协作系统
- 认知调试器（1800+行）
- 可视化调试界面
- 完整的测试套件

### 最新更新（2025-01-18）
- 重构visual_debugger支持外部CognitiveAgent
- 添加GUI配置界面
- 任务输入框改为多行文本框
- 文件重组到embodied_cognitive_workflow目录

## 文档资源

详细文档请查看：
- `docs/Agent文档.md` - Agent基础类使用文档
- `embodied_cognitive_workflow/ai_docs/` - 技术文档目录
- `embodied_cognitive_workflow/CLAUDE.md` - 详细项目文档

---
**项目状态**: 活跃开发中  
**最后更新**: 2025-01-18