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

架构设计原则:
- LLM缓存优化: 系统移除了所有自动生成的UUID和时间戳字段，
  使用确定性ID生成策略，以提高语言模型缓存效率和系统可预测性
- 服务解耦: RuleMatchingService功能已整合到RuleEngineService中，
  简化架构并提高性能

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
    RuleSetExecution,
    GlobalState,
    DecisionResult,
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

# 导入核心服务 - 使用新的包结构
from .services.core.rule_engine_service import RuleEngineService
from .services.core.rule_generation_service import RuleGenerationService
# from .services.rule_matching_service import RuleMatchingService  # Removed - functionality integrated into RuleEngineService
from .services.core.rule_execution_service import RuleExecutionService
from .services.core.state_service import StateService
from .services.core.agent_service import AgentService
from .services.core.language_model_service import LanguageModelService
from .services.core.resource_manager import ResourceManager

# 导入基础设施实现
from .infrastructure.repository_impl import (
    RuleRepositoryImpl,
    StateRepositoryImpl,
    ExecutionRepositoryImpl
)

# 导入应用层组件
from .application.production_rule_workflow_engine import ProductionRuleWorkflowEngine
from .application.cognitive_workflow_agent_wrapper import CognitiveAgent

# 定义公开的API
__all__ = [
    # 领域模型
    "ProductionRule",
    "RuleSet", 
    "RuleExecution",
    "RuleSetExecution",
    "GlobalState",
    "DecisionResult",
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
    # "RuleMatchingService",  # Removed - functionality integrated into RuleEngineService 
    "RuleExecutionService",
    "StateService",
    "AgentService",
    "LanguageModelService",
    "ResourceManager",
    
    # 基础设施实现
    "RuleRepositoryImpl",
    "StateRepositoryImpl",
    "ExecutionRepositoryImpl",
    
    # 应用层组件
    "ProductionRuleWorkflowEngine",
    "CognitiveAgent"
]

def create_production_rule_system(llm, agents, enable_auto_recovery=True, enable_adaptive_replacement=True, enable_context_filtering=True):
    """
    快速创建产生式规则系统的工厂函数
    
    Args:
        llm: 语言模型实例
        agents: 智能体字典 {name: agent_instance}
        enable_auto_recovery: 是否启用自动恢复
        enable_adaptive_replacement: 是否启用自适应规则替换
        enable_context_filtering: 是否启用上下文过滤（TaskTranslator）
        
    Returns:
        ProductionRuleWorkflowEngine: 配置好的工作流引擎
    """
    # 创建基础设施
    llm_service = LanguageModelService(llm)
    
    # 创建仓储实现
    rule_repository = RuleRepositoryImpl()
    state_repository = StateRepositoryImpl()
    execution_repository = ExecutionRepositoryImpl()
    
    # 创建Agent注册表 - 直接管理Agent实例
    agent_registry = AgentRegistry()
    
    # 注册用户提供的智能体
    for name, agent in agents.items():
        agent_registry.register_agent(name, agent)
    
    # 创建TaskTranslator（如果启用）
    task_translator = None
    if enable_context_filtering:
        try:
            from .services.cognitive.task_translator import TaskTranslator
            task_translator = TaskTranslator(llm)
        except ImportError:
            task_translator = None
    
    # 创建Agent服务，注入TaskTranslator
    agent_service = AgentService(
        agent_registry=agent_registry, 
        agent_instances=agents,
        task_translator=task_translator,
        enable_context_filtering=enable_context_filtering
    )
    
    # 创建ResourceManager用于智能体动态分配
    resource_manager = ResourceManager(
        agent_registry=agent_registry,
        llm_service=llm_service
    )
    
    # 创建专门服务
    rule_generation = RuleGenerationService(llm_service, agent_registry)
    # rule_matching = RuleMatchingService(llm_service, max_workers)  # Removed - functionality integrated into RuleEngineService
    rule_execution = RuleExecutionService(agent_service, execution_repository, llm_service, resource_manager)
    state_service = StateService(llm_service, state_repository)
    
    # 创建核心引擎服务
    rule_engine_service = RuleEngineService(
        rule_repository=rule_repository,
        state_repository=state_repository,
        execution_repository=execution_repository,
        rule_execution=rule_execution,
        rule_generation=rule_generation,
        state_service=state_service,
        enable_auto_recovery=enable_auto_recovery,
        enable_adaptive_replacement=enable_adaptive_replacement,
        resource_manager=resource_manager
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