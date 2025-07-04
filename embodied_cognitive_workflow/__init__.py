"""
具身认知工作流系统

基于具身认知理论的智能体工作流实现，包含：
- 自我智能体 (EgoAgent)：理性思考和决策
- 本我智能体 (IdAgent)：价值驱动和目标监控  
- 具身认知工作流协调器 (EmbodiedCognitiveWorkflow)：三层架构协调

核心特性：
- "走一步看一步"的动态认知循环
- 自然语言驱动的心灵-身体交互
- 价值导向的目标评估和监控
- 基于现有Agent系统的身体层实现
"""

from ego_agent import EgoAgent
from id_agent import IdAgent
from embodied_cognitive_workflow import EmbodiedCognitiveWorkflow, create_embodied_cognitive_workflow, execute_embodied_cognitive_task

__version__ = "1.0.0"

__all__ = [
    "EgoAgent",
    "IdAgent", 
    "EmbodiedCognitiveWorkflow",
    "create_embodied_cognitive_workflow",
    "execute_embodied_cognitive_task"
]