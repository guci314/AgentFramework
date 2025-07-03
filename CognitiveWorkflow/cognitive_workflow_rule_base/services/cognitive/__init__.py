# -*- coding: utf-8 -*-
"""
认知决策服务包 (Cognitive Decision Services)

提供高级认知和决策功能，包括认知顾问、任务翻译和团队协调等服务。

这些服务实现了系统的智能决策能力，负责工作流规划、上下文处理和多智能体协作。
"""

from .cognitive_advisor import CognitiveAdvisor
from .task_translator import TaskTranslator

__all__ = [
    "CognitiveAdvisor",
    "TaskTranslator"
]