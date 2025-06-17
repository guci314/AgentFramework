"""
AgentFrameWork - 多智能体框架

这是一个基于langchain的多智能体协作框架，支持:
- 多步骤任务规划和执行
- 智能体协作
- 动态控制流(循环、条件分支)
- 记忆管理
"""

from .enhancedAgent_v2 import MultiStepAgent_v2, RegisteredAgent, WorkflowState
from .agent_base import AgentBase, Result
from .pythonTask import Agent, StatefulExecutor

__version__ = "0.1.0"
__all__ = [
        "MultiStepAgent_v2",
    "RegisteredAgent",
    "WorkflowState",
    "AgentBase", 
    "Result",
    "Agent", 
    "StatefulExecutor"
] 