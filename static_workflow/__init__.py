"""
静态工作流模块
================

MultiStepAgent_v3的静态工作流架构实现。

提供声明式控制流、高性能执行引擎和完整的工作流管理功能。

主要组件:
- MultiStepAgent_v3: 主要智能体类
- StaticWorkflowEngine: 静态工作流执行引擎
- WorkflowDefinition: 工作流定义和Schema
- ControlFlowEvaluator: 控制流条件评估器
"""

from .MultiStepAgent_v3 import MultiStepAgent_v3
from .static_workflow_engine import StaticWorkflowEngine, WorkflowState, WorkflowExecutionResult
from .workflow_definitions import WorkflowDefinition, WorkflowStep, WorkflowLoader
from .control_flow_evaluator import ControlFlowEvaluator

__version__ = "1.0.0"
__all__ = [
    "MultiStepAgent_v3",
    "StaticWorkflowEngine", 
    "WorkflowState",
    "WorkflowExecutionResult",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowLoader",
    "ControlFlowEvaluator"
]