# -*- coding: utf-8 -*-
"""
基于产生式规则的认知工作流系统

这个包实现了一个完整的产生式规则引擎，支持：
- 自然语言条件匹配
- 动态规则生成和执行
- 语义驱动的工作流导航
- 图灵完备的执行引擎

主要组件:
- Domain Model: 纯业务领域模型
- Service Model: 业务服务实现
- Infrastructure: 技术基础设施
- Engine: 工作流执行引擎

作者: Claude
日期: 2024-12-21
基于: 产生式规则系统理论
"""

__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "基于产生式规则的认知工作流系统"

# 导入核心领域模型
from .domain.entities import (
    ProductionRule,
    RuleSet, 
    RuleExecution,
    GlobalState,
    DecisionResult,
    AgentCapability,
    AgentRegistry,
    WorkflowResult
)

from .domain.value_objects import (
    RulePhase,
    ExecutionStatus,
    DecisionType,
    RuleSetStatus,
    ModificationType
)

from .domain.repositories import (
    RuleRepository,
    StateRepository,
    ExecutionRepository
)

# 导入核心服务
from .services.rule_engine_service import RuleEngineService
from .services.rule_generation_service import RuleGenerationService
from .services.rule_matching_service import RuleMatchingService
from .services.rule_execution_service import RuleExecutionService
from .services.state_service import StateService
from .services.agent_service import AgentService
from .services.language_model_service import LanguageModelService

# 导入基础设施实现
from .infrastructure.repository_impl import (
    RuleRepositoryImpl,
    StateRepositoryImpl,
    ExecutionRepositoryImpl
)

# 导入工作流引擎
from .engine.production_rule_workflow_engine import ProductionRuleWorkflowEngine

# 定义公开的API
__all__ = [
    # 领域模型
    "ProductionRule",
    "RuleSet", 
    "RuleExecution",
    "GlobalState",
    "DecisionResult",
    "AgentCapability",
    "AgentRegistry",
    "WorkflowResult",
    
    # 值对象和枚举
    "RulePhase",
    "ExecutionStatus", 
    "DecisionType",
    "RuleSetStatus",
    "ModificationType",
    
    # 仓储接口
    "RuleRepository",
    "StateRepository",
    "ExecutionRepository",
    
    # 核心服务
    "RuleEngineService",
    "RuleGenerationService",
    "RuleMatchingService", 
    "RuleExecutionService",
    "StateService",
    "AgentService",
    "LanguageModelService",
    
    # 基础设施实现
    "RuleRepositoryImpl",
    "StateRepositoryImpl",
    "ExecutionRepositoryImpl",
    
    # 工作流引擎
    "ProductionRuleWorkflowEngine"
]

def create_production_rule_system(llm, agents, enable_auto_recovery=True, max_workers=4):
    """
    快速创建产生式规则系统的工厂函数
    
    Args:
        llm: 语言模型实例
        agents: 智能体字典 {name: agent_instance}
        enable_auto_recovery: 是否启用自动恢复
        max_workers: 并行执行的最大工作线程数
        
    Returns:
        ProductionRuleWorkflowEngine: 配置好的工作流引擎
    """
    # 创建基础设施
    llm_service = LanguageModelService(llm)
    
    # 创建仓储实现
    rule_repository = RuleRepositoryImpl()
    state_repository = StateRepositoryImpl()
    execution_repository = ExecutionRepositoryImpl()
    
    # 创建Agent注册表
    agent_registry = AgentRegistry()
    for name, agent in agents.items():
        capability = AgentCapability(
            id=name,
            name=name,
            description=getattr(agent, 'api_specification', f'{name} Agent'),
            supported_actions=['*'],  # 支持所有动作
            api_specification=getattr(agent, 'api_specification', ''),
            configuration={}
        )
        agent_registry.register_capability(capability)
    
    # 创建Agent服务
    agent_service = AgentService(agent_registry, agents)
    
    # 创建专门服务
    rule_generation = RuleGenerationService(llm_service)
    rule_matching = RuleMatchingService(llm_service, max_workers)  # 传递max_workers参数
    rule_execution = RuleExecutionService(agent_service, execution_repository, llm_service)
    state_service = StateService(llm_service, state_repository)
    
    # 创建核心引擎服务
    rule_engine_service = RuleEngineService(
        rule_repository=rule_repository,
        state_repository=state_repository,
        execution_repository=execution_repository,
        rule_matching=rule_matching,
        rule_execution=rule_execution,
        rule_generation=rule_generation,
        state_service=state_service,
        enable_auto_recovery=enable_auto_recovery
    )
    
    # 创建工作流引擎，传入agent_registry
    workflow_engine = ProductionRuleWorkflowEngine(rule_engine_service, agent_registry)
    
    return workflow_engine

def get_version_info():
    """获取版本信息"""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "components": len(__all__),
        "core_philosophy": "IF-THEN自然语言产生式规则系统"
    }

# 启动信息
print(f"🔧 产生式规则认知工作流系统 v{__version__} 已加载")
print(f"   核心理念: {get_version_info()['core_philosophy']}")
print(f"   可用组件: {len(__all__)} 个")