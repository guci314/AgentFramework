# -*- coding: utf-8 -*-
"""
认知工作流系统 (Cognitive Workflow System)

基于认知工作流核心理念的智能体协作系统：
- 计划是线性的，导航是动态的
- 三大角色清晰分离：规划者、决策者、执行者
- 状态满足性检查替代固定依赖关系
- 具备自适应和自修复能力

主要组件:
- CognitiveWorkflowEngine: 核心工作流引擎
- CognitivePlanner: 规划者
- CognitiveDecider: 决策者  
- CognitiveExecutor: 执行者
- CognitiveMultiStepAgent: 兼容性适配器

作者: Claude
日期: 2025-06-22
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "基于认知工作流核心理念的智能体协作系统"

# 导入核心组件
from .cognitive_workflow import (
    # 核心引擎
    CognitiveWorkflowEngine,
    
    # 三大角色
    CognitivePlanner,
    CognitiveDecider, 
    CognitiveExecutor,
    
    # 核心数据结构
    CognitiveTask,
    GlobalState,
    TaskPhase,
    TaskStatus,
    
    # 状态检查器
    StateConditionChecker,
    
    # 兼容性函数
    safe_get_result_return_value,
    safe_get_result_error
)

# 导入兼容性适配器
from .cognitive_workflow_adapter import (
    CognitiveMultiStepAgent,
    RegisteredAgent,
    convert_legacy_plan_to_cognitive_tasks,
    create_migration_guide
)

# 定义公开的API
__all__ = [
    # 核心引擎
    "CognitiveWorkflowEngine",
    
    # 三大角色
    "CognitivePlanner",
    "CognitiveDecider",
    "CognitiveExecutor",
    
    # 数据结构
    "CognitiveTask", 
    "GlobalState",
    "TaskPhase",
    "TaskStatus",
    
    # 工具组件
    "StateConditionChecker",
    "safe_get_result_return_value",
    "safe_get_result_error",
    
    # 兼容性组件
    "CognitiveMultiStepAgent",
    "RegisteredAgent",
    "convert_legacy_plan_to_cognitive_tasks",
    "create_migration_guide"
]

def get_version_info():
    """获取版本信息"""
    return {
        "version": __version__,
        "author": __author__, 
        "description": __description__,
        "components": len(__all__),
        "core_philosophy": "计划是线性的，导航是动态的"
    }

def quick_start_guide():
    """快速开始指南"""
    guide = """
# 认知工作流快速开始

## 1. 新项目使用方式
```python
from CognitiveWorkflow import CognitiveWorkflowEngine

# 创建智能体字典
agents = {"coder": coder_agent, "tester": tester_agent}

# 初始化引擎
engine = CognitiveWorkflowEngine(llm=llm, agents=agents)

# 执行工作流
result = engine.execute_cognitive_workflow("开发一个计算器程序")
```

## 2. 兼容性使用方式
```python
from CognitiveWorkflow import CognitiveMultiStepAgent

# 替换原有MultiStepAgent_v2
agent = CognitiveMultiStepAgent(llm=llm, registered_agents=agents)
result = agent.execute_multi_step("开发计算器")
```

## 3. 运行演示
```bash
python demo_cognitive_workflow.py
```

更多信息请查看 README.md
"""
    return guide

# 启动信息
print(f"🧠 认知工作流系统 v{__version__} 已加载")
print(f"   核心理念: {get_version_info()['core_philosophy']}")
print(f"   可用组件: {len(__all__)} 个")