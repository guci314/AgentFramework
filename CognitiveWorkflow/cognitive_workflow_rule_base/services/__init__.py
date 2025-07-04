
# -*- coding: utf-8 -*-
"""
产生式规则系统服务层 (Services Layer)

提供完整的服务架构，按功能域组织为四个专业化包：
- core: 核心服务
- cognitive: 认知决策服务  
- adaptive: 自适应优化服务
- advanced: 高级优化组件

这种架构设计确保了清晰的职责分离和良好的可维护性。
"""

# 核心服务 (Core Services)
from .core import (
    RuleEngineService,
    RuleGenerationService,
    RuleExecutionService,
    StateService,
    AgentService,
    LanguageModelService
)

# 认知决策服务 (Cognitive Decision Services)  
from .cognitive import (
    CognitiveAdvisor,
    TaskTranslator
)

# 自适应优化服务 (Adaptive Optimization Services)
from .adaptive import (
    AdaptiveReplacementService,
    StrategyEffectivenessTracker
)

# 高级优化组件 (Advanced Optimization Components)
from .advanced import (
    AdvancedPatternRecognitionEngine,
    DynamicParameterOptimizer,
    PredictiveOptimizationFramework,
    IntelligentPerformanceBenchmark,
    ReinforcementLearningOptimizer,
    AdaptiveHyperparameterOptimizer
)

# 向后兼容的主要服务导出
__all__ = [
    # 核心服务
    "RuleEngineService",
    "RuleGenerationService", 
    "RuleExecutionService",
    "StateService",
    "AgentService",
    "LanguageModelService",
    
    # 认知决策服务
    "CognitiveAdvisor",
    "TaskTranslator",
    
    # 自适应优化服务
    "AdaptiveReplacementService",
    "StrategyEffectivenessTracker",
    
    # 高级优化组件
    "AdvancedPatternRecognitionEngine",
    "DynamicParameterOptimizer", 
    "PredictiveOptimizationFramework",
    "IntelligentPerformanceBenchmark",
    "ReinforcementLearningOptimizer",
    "AdaptiveHyperparameterOptimizer"
]
