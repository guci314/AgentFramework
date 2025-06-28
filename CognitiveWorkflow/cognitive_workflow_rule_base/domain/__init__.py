# -*- coding: utf-8 -*-
"""
领域模型层 - Domain Layer

包含核心业务实体、值对象和仓储接口，不包含任何技术实现细节。
严格遵循DDD原则，保持领域模型的纯净性。
"""

from .entities import (
    ProductionRule,
    RuleSet,
    RuleExecution, 
    GlobalState,
    DecisionResult,
    AgentRegistry,
    WorkflowResult
)

from .value_objects import (
    RulePhase,
    ExecutionStatus,
    DecisionType,
    RuleSetStatus,
    ModificationType
)

from .repositories import (
    RuleRepository,
    StateRepository,
    ExecutionRepository
)

__all__ = [
    # 核心实体
    "ProductionRule",
    "RuleSet",
    "RuleExecution",
    "GlobalState", 
    "DecisionResult",
    "AgentRegistry",
    "WorkflowResult",
    
    # 值对象
    "RulePhase",
    "ExecutionStatus",
    "DecisionType", 
    "RuleSetStatus",
    "ModificationType",
    
    # 仓储接口
    "RuleRepository",
    "StateRepository",
    "ExecutionRepository"
]