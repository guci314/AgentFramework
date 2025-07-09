"""
具身认知工作流系统

基于具身认知理论的四层架构智能体工作流实现，包含：
- 超我智能体 (SuperEgoAgent)：元认知监督和道德约束
- 自我智能体 (EgoAgent)：理性思考和决策
- 本我智能体 (IdAgent)：价值驱动和目标监控  
- 身体智能体 (Body)：执行和感知
- 认知智能体 (CognitiveAgent)：四层架构协调的核心智能体

核心特性：
- 四层认知架构：超我-自我-本我-身体的完整认知系统
- UltraThink元认知能力：认知监控、策略优化、反思学习
- 增量式规划的动态认知循环
- 自然语言驱动的心灵-身体交互
- 价值导向的目标评估和监控
- 元认知监督和认知质量控制
- 基于现有Agent系统的身体层实现
"""

try:
    from .ego_agent import EgoAgent
    from .id_agent import IdAgent
    from .embodied_cognitive_workflow import (
        CognitiveAgent, 
        create_cognitive_agent, 
        execute_cognitive_task,
        WorkflowContext,
        DecisionType,
        # 向后兼容
        EmbodiedCognitiveWorkflow,
        create_embodied_cognitive_workflow, 
        execute_embodied_cognitive_task
    )
    from .super_ego_agent import SuperEgoAgent, UltraThinkEngine, CognitiveMonitor, StrategyOptimizer, ReflectionEngine
    from .cognitive_debug_agent import CognitiveDebugAgent, CognitiveDebugger, DebugLevel
    from .gemini_flash_integration import GeminiFlashClient, create_gemini_client
    from .cognitive_debug_visualizer import CognitiveDebugVisualizer
except ImportError:
    # 当作为独立模块使用时的降级导入
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from ego_agent import EgoAgent
    from id_agent import IdAgent
    from embodied_cognitive_workflow import (
        CognitiveAgent, 
        create_cognitive_agent, 
        execute_cognitive_task,
        WorkflowContext,
        DecisionType,
        # 向后兼容
        EmbodiedCognitiveWorkflow,
        create_embodied_cognitive_workflow, 
        execute_embodied_cognitive_task
    )
    from super_ego_agent import SuperEgoAgent, UltraThinkEngine, CognitiveMonitor, StrategyOptimizer, ReflectionEngine
    from cognitive_debug_agent import CognitiveDebugAgent, CognitiveDebugger, DebugLevel
    from gemini_flash_integration import GeminiFlashClient, create_gemini_client
    from cognitive_debug_visualizer import CognitiveDebugVisualizer

__version__ = "1.0.0"

__all__ = [
    "EgoAgent",
    "IdAgent",
    # 新的主要接口
    "CognitiveAgent",
    "create_cognitive_agent", 
    "execute_cognitive_task",
    "WorkflowContext",
    "DecisionType",
    # 向后兼容接口
    "EmbodiedCognitiveWorkflow",
    "create_embodied_cognitive_workflow",
    "execute_embodied_cognitive_task",
    # 超我智能体和元认知功能
    "SuperEgoAgent",
    "UltraThinkEngine",
    "CognitiveMonitor",
    "StrategyOptimizer", 
    "ReflectionEngine",
    # 认知调试功能
    "CognitiveDebugAgent",
    "CognitiveDebugger", 
    "DebugLevel",
    "GeminiFlashClient",
    "create_gemini_client",
    "CognitiveDebugVisualizer"
]