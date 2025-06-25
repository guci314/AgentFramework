# -*- coding: utf-8 -*-
"""
核心业务实体

包含系统的核心业务实体，这些实体承载主要的业务逻辑和状态。
实体具有唯一标识，可以跨越时间边界保持身份。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
import json

from .value_objects import (
    RulePhase, ExecutionStatus, DecisionType, RuleSetStatus,
    RuleModification, ExecutionMetrics, StateChangeAnalysis,
    MatchingResult, WorkflowExecutionResult, RuleConstants,
    ModificationType
)


@dataclass
class WorkflowResult:
    """工作流执行结果实体 - 封装认知工作流任务执行的结果"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_details: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # timestamp: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    
    def is_error(self) -> bool:
        """是否为错误结果"""
        return not self.success
    
    def get_error_message(self) -> str:
        """获取错误消息"""
        if self.error_details:
            return self.error_details
        return self.message if not self.success else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'error_details': self.error_details,
            'metadata': self.metadata
            # 'timestamp': self.timestamp.isoformat()  # Removed for LLM caching
        }


@dataclass
class ProductionRule:
    """产生式规则实体 - 系统的核心业务规则"""
    id: str
    name: str
    condition: str              # 自然语言描述的触发条件 (IF部分)
    action: str                # 要执行的动作指令 (THEN部分)
    agent_capability_id: str    # 引用AgentCapability的ID
    priority: int = RuleConstants.DEFAULT_RULE_PRIORITY  # 规则优先级
    phase: RulePhase = RulePhase.PROBLEM_SOLVING
    expected_outcome: str = ""  # 期望的执行结果
    # created_at: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    # updated_at: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后验证"""
        # Removed UUID generation for LLM caching - ID should be provided explicitly
        # if not self.id:
        #     self.id = str(uuid.uuid4())
        if not (RuleConstants.MIN_RULE_PRIORITY <= self.priority <= RuleConstants.MAX_RULE_PRIORITY):
            raise ValueError(f"规则优先级必须在{RuleConstants.MIN_RULE_PRIORITY}-{RuleConstants.MAX_RULE_PRIORITY}之间")
    
    def is_applicable(self, global_state: 'GlobalState') -> Tuple[bool, float]:
        """
        检查规则是否适用于当前状态
        
        注意：这是一个占位符方法，实际的语义匹配由RuleMatchingService实现
        这里只做基本的结构化检查
        """
        # 基本检查：状态不能为空
        if not global_state or not global_state.description:
            return False, 0.0
        
        # 基本检查：条件不能为空
        if not self.condition.strip():
            return False, 0.0
        
        # 这里返回一个默认值，实际匹配逻辑在Service层
        return True, 0.5
    
    def update_priority(self, new_priority: int) -> None:
        """更新规则优先级"""
        if not (RuleConstants.MIN_RULE_PRIORITY <= new_priority <= RuleConstants.MAX_RULE_PRIORITY):
            raise ValueError(f"优先级必须在{RuleConstants.MIN_RULE_PRIORITY}-{RuleConstants.MAX_RULE_PRIORITY}之间")
        self.priority = new_priority
        # self.updated_at = datetime.now()  # Removed for LLM caching
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'condition': self.condition,
            'action': self.action,
            'agent_capability_id': self.agent_capability_id,
            'priority': self.priority,
            'phase': self.phase.value,
            'expected_outcome': self.expected_outcome,
            # 'created_at': self.created_at.isoformat(),  # Removed for LLM caching
            # 'updated_at': self.updated_at.isoformat(),  # Removed for LLM caching
            'metadata': self.metadata
        }


@dataclass
class RuleExecution:
    """规则执行实体 - 记录具体规则的执行实例"""
    id: str
    rule_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[WorkflowResult] = None
    # started_at: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    completed_at: Optional[datetime] = None
    execution_context: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        """初始化后验证"""
        # Removed UUID generation for LLM caching - ID should be provided explicitly
        # if not self.id:
        #     self.id = str(uuid.uuid4())
    
    def is_successful(self) -> bool:
        """是否执行成功"""
        return self.status == ExecutionStatus.COMPLETED and (
            self.result is None or self.result.success
        )
    
    def get_execution_duration(self) -> Optional[float]:
        """获取执行持续时间（秒）"""
        # Duration calculation removed as started_at was removed for LLM caching
        # Return None as we don't track execution start time anymore
        return None
    
    def mark_completed(self, result: WorkflowResult) -> None:
        """标记执行完成"""
        self.result = result
        self.status = ExecutionStatus.COMPLETED if result.success else ExecutionStatus.FAILED
        self.completed_at = datetime.now()
        if not result.success:
            self.failure_reason = result.get_error_message()
    
    def mark_failed(self, error_message: str) -> None:
        """标记执行失败"""
        self.status = ExecutionStatus.FAILED
        self.failure_reason = error_message
        self.completed_at = datetime.now()
        self.result = WorkflowResult(success=False, message=error_message)


@dataclass
class GlobalState:
    """全局状态实体 - 系统的全局状态管理"""
    id: str
    description: str            # 自然语言状态描述
    context_variables: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[str] = field(default_factory=list)
    # timestamp: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    workflow_id: str = ""
    iteration_count: int = 0
    goal_achieved: bool = False
    
    def __post_init__(self):
        """初始化后验证"""
        # Removed UUID generation for LLM caching - ID should be provided explicitly
        # if not self.id:
        #     self.id = str(uuid.uuid4())
    
    def update_from_result(self, execution_result: WorkflowResult) -> 'GlobalState':
        """根据执行结果更新状态，返回新的状态实例"""
        # 创建新的状态实例（保持不可变性）
        new_state = GlobalState(
            id=f"{self.id}_iter_{self.iteration_count + 1}",  # Use deterministic ID instead of UUID
            description=self.description,
            context_variables=self.context_variables.copy(),
            execution_history=self.execution_history.copy(),
            # timestamp=datetime.now(),  # Removed for LLM caching
            workflow_id=self.workflow_id,
            iteration_count=self.iteration_count + 1,
            goal_achieved=self.goal_achieved
        )
        
        # 更新执行历史
        # Use iteration count instead of timestamp for deterministic history
        history_entry = f"[iter_{new_state.iteration_count}] {execution_result.message}"
        new_state.execution_history.append(history_entry)
        
        # 更新上下文变量
        if execution_result.metadata:
            new_state.context_variables.update(execution_result.metadata)
        
        # 如果执行成功，可能需要更新状态描述
        if execution_result.success and execution_result.data:
            if isinstance(execution_result.data, dict) and 'new_state_description' in execution_result.data:
                new_state.description = execution_result.data['new_state_description']
        
        return new_state
    
    def get_context_value(self, key: str) -> Any:
        """获取上下文变量值"""
        return self.context_variables.get(key)
    
    def set_context_value(self, key: str, value: Any) -> None:
        """设置上下文变量值"""
        self.context_variables[key] = value
        # self.timestamp = datetime.now()  # Removed for LLM caching
    
    def merge_context(self, context: Dict[str, Any]) -> None:
        """合并上下文变量"""
        self.context_variables.update(context)
        # self.timestamp = datetime.now()  # Removed for LLM caching
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'description': self.description,
            'context_variables': self.context_variables,
            'execution_history': self.execution_history,
            # 'timestamp': self.timestamp.isoformat(),  # Removed for LLM caching
            'workflow_id': self.workflow_id,
            'iteration_count': self.iteration_count,
            'goal_achieved': self.goal_achieved
        }


@dataclass
class RuleSet:
    """规则集实体 - 管理一组相关的产生式规则"""
    id: str
    goal: str
    rules: List[ProductionRule] = field(default_factory=list)
    # created_at: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    # updated_at: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    version: int = 1
    status: RuleSetStatus = RuleSetStatus.DRAFT
    modification_history: List[RuleModification] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后验证"""
        # Removed UUID generation for LLM caching - ID should be provided explicitly
        # if not self.id:
        #     self.id = str(uuid.uuid4())
    
    def add_rule(self, rule: ProductionRule) -> None:
        """添加规则"""
        if rule.id in [r.id for r in self.rules]:
            raise ValueError(f"规则ID {rule.id} 已存在")
        
        self.rules.append(rule)
        # self.updated_at = datetime.now()  # Removed for LLM caching
        self.version += 1
        
        # 记录修改历史
        modification = RuleModification(
            modification_type=ModificationType.ADD_RULE,
            target_rule_id=rule.id,
            new_rule_data=rule.to_dict(),
            modification_reason=f"添加新规则: {rule.name}",
            timestamp=datetime.now()
        )
        self.modification_history.append(modification)
    
    def remove_rule(self, rule_id: str) -> bool:
        """删除规则"""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        
        if len(self.rules) < original_count:
            # self.updated_at = datetime.now()  # Removed for LLM caching
            self.version += 1
            
            # 记录修改历史
            modification = RuleModification(
                modification_type=ModificationType.REMOVE_RULE,
                target_rule_id=rule_id,
                new_rule_data=None,
                modification_reason=f"删除规则: {rule_id}",
                timestamp=datetime.now()
            )
            self.modification_history.append(modification)
            return True
        
        return False
    
    def get_rules_by_phase(self, phase: RulePhase) -> List[ProductionRule]:
        """根据阶段获取规则"""
        return [rule for rule in self.rules if rule.phase == phase]
    
    def get_rules_by_priority(self, descending: bool = True) -> List[ProductionRule]:
        """根据优先级排序获取规则"""
        return sorted(self.rules, key=lambda r: r.priority, reverse=descending)
    
    def activate(self) -> None:
        """激活规则集"""
        self.status = RuleSetStatus.ACTIVE
        # self.updated_at = datetime.now()  # Removed for LLM caching
    
    def complete(self) -> None:
        """标记规则集完成"""
        self.status = RuleSetStatus.COMPLETED
        # self.updated_at = datetime.now()  # Removed for LLM caching


@dataclass
class DecisionResult:
    """决策结果实体 - 封装决策过程的结果"""
    selected_rule: Optional[ProductionRule]
    decision_type: DecisionType
    confidence: float
    reasoning: str
    context: Dict[str, Any] = field(default_factory=dict)
    # timestamp: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    alternative_rules: List[ProductionRule] = field(default_factory=list)
    
    def is_execution_decision(self) -> bool:
        """是否为执行决策"""
        return self.decision_type == DecisionType.EXECUTE_SELECTED_RULE
    
    def is_goal_completion(self) -> bool:
        """是否为目标完成"""
        return self.decision_type in [DecisionType.GOAL_ACHIEVED, DecisionType.GOAL_FAILED]
    
    def get_decision_summary(self) -> str:
        """获取决策摘要"""
        if self.decision_type == DecisionType.EXECUTE_SELECTED_RULE:
            return f"执行规则: {self.selected_rule.name if self.selected_rule else 'None'}"
        elif self.decision_type == DecisionType.ADD_RULE:
            return "需要添加新规则"
        elif self.decision_type == DecisionType.GOAL_ACHIEVED:
            return "目标已达成"
        elif self.decision_type == DecisionType.GOAL_FAILED:
            return "目标执行失败"
        return "未知决策类型"


@dataclass
class AgentCapability:
    """智能体能力实体 - 定义智能体的能力和特征"""
    id: str
    name: str
    description: str
    supported_actions: List[str]
    api_specification: str = ""
    configuration: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后验证"""
        # Removed UUID generation for LLM caching - ID should be provided explicitly
        # if not self.id:
        #     self.id = str(uuid.uuid4())
    
    def can_execute_action(self, action: str) -> bool:
        """检查是否能执行指定动作"""
        return '*' in self.supported_actions or action in self.supported_actions
    
    def get_action_specification(self, action: str) -> Dict[str, Any]:
        """获取动作规范"""
        if not self.can_execute_action(action):
            raise ValueError(f"该智能体不支持动作: {action}")
        
        return {
            'action': action,
            'capability_id': self.id,
            'api_specification': self.api_specification,
            'configuration': self.configuration
        }
    
    def update_performance_metric(self, metric_name: str, value: float) -> None:
        """更新性能指标"""
        self.performance_metrics[metric_name] = value


@dataclass
class AgentRegistry:
    """智能体注册表实体 - 管理所有可用的智能体能力"""
    capabilities: Dict[str, AgentCapability] = field(default_factory=dict)
    
    def register_capability(self, capability: AgentCapability) -> None:
        """注册智能体能力"""
        self.capabilities[capability.id] = capability
    
    def get_capability(self, capability_id: str) -> AgentCapability:
        """获取智能体能力"""
        if capability_id not in self.capabilities:
            raise ValueError(f"未找到智能体能力: {capability_id}")
        return self.capabilities[capability_id]
    
    def find_capabilities_by_action(self, action: str) -> List[AgentCapability]:
        """根据动作查找智能体能力"""
        return [
            capability for capability in self.capabilities.values()
            if capability.can_execute_action(action)
        ]
    
    def list_all_capabilities(self) -> List[AgentCapability]:
        """列出所有智能体能力"""
        return list(self.capabilities.values())
    
    def remove_capability(self, capability_id: str) -> bool:
        """移除智能体能力"""
        if capability_id in self.capabilities:
            del self.capabilities[capability_id]
            return True
        return False