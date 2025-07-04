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
    # timestamp: datetime = field(default_factory=datetime.now)  # 已移除: LLM缓存优化
    
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
            # 'timestamp': self.timestamp.isoformat()  # 已移除: LLM缓存优化
        }


@dataclass
class ProductionRule:
    """产生式规则实体 - 系统的核心业务规则（类型层）"""
    id: str
    name: str
    condition: str              # 自然语言描述的触发条件 (IF部分)
    action: str                # 要执行的动作指令 (THEN部分)
    # agent_name: str            # 已移至实例层(RuleExecution.assigned_agent)
    priority: int = RuleConstants.DEFAULT_RULE_PRIORITY  # 规则优先级
    phase: RulePhase = RulePhase.EXECUTION
    expected_outcome: str = ""  # 期望的执行结果
    # created_at: datetime = field(default_factory=datetime.now)  # 已移除: LLM缓存优化
    # updated_at: datetime = field(default_factory=datetime.now)  # 已移除: LLM缓存优化
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后验证"""
        # 已移除UUID自动生成: LLM缓存优化 - ID需要显式提供
        # if not self.id:
        #     self.id = str(uuid.uuid4())
        if not (RuleConstants.MIN_RULE_PRIORITY <= self.priority <= RuleConstants.MAX_RULE_PRIORITY):
            raise ValueError(f"规则优先级必须在{RuleConstants.MIN_RULE_PRIORITY}-{RuleConstants.MAX_RULE_PRIORITY}之间")
    
    def is_applicable(self, global_state: 'GlobalState') -> Tuple[bool, float]:
        """
        检查规则是否适用于当前状态
        
        注意：这是一个占位符方法，实际的语义匹配已集成到RuleEngineService中
        这里只做基本的结构化检查
        """
        # 基本检查：状态不能为空
        if not global_state or not global_state.state:
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
            # 'agent_name': self.agent_name,  # 已移至实例层
            'priority': self.priority,
            'phase': self.phase.value,
            'expected_outcome': self.expected_outcome,
            # 'created_at': self.created_at.isoformat(),  # Removed for LLM caching
            # 'updated_at': self.updated_at.isoformat(),  # Removed for LLM caching
            'metadata': self.metadata
        }


@dataclass
class RuleExecution:
    """规则执行实体 - 记录具体规则的执行实例（实例层）"""
    id: str
    rule_id: str
    assigned_agent: Optional[str] = None  # 实例层分配的具体agent
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[WorkflowResult] = None
    # started_at: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    completed_at: Optional[datetime] = None
    execution_context: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        """初始化后验证"""
        # 已移除UUID自动生成: LLM缓存优化 - ID需要显式提供
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
class WorkflowState:
    """
    增强版工作流状态管理 - 解决死循环问题的核心类
    
    新增功能:
    - 执行规则历史跟踪
    - 完成任务列表管理
    - 失败尝试记录
    - 循环检测机制
    """
    id: str
    state: str                  # 自然语言状态描述
    context_variables: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[str] = field(default_factory=list)
    workflow_id: str = ""
    iteration_count: int = 0
    goal_achieved: bool = False
    
    # 🔑 关键增强：防止死循环的核心字段
    executed_rules: set = field(default_factory=set)           # 已执行规则ID集合
    completed_tasks: List[str] = field(default_factory=list)   # 已完成任务列表
    failed_attempts: Dict[str, int] = field(default_factory=dict)  # 规则失败次数计数
    last_decision_context: Dict[str, Any] = field(default_factory=dict)  # 上次决策上下文
    
    # 循环检测相关
    state_fingerprints: List[str] = field(default_factory=list)  # 状态指纹历史
    consecutive_same_rule_count: int = 0                         # 连续执行相同规则计数
    last_executed_rule_id: Optional[str] = None                 # 上次执行的规则ID
    
    def __post_init__(self):
        """初始化后验证和处理"""
        # 确保executed_rules是set类型
        if not isinstance(self.executed_rules, set):
            self.executed_rules = set(self.executed_rules) if self.executed_rules else set()
    
    def mark_rule_executed(self, rule_id: str, success: bool = True) -> None:
        """标记规则已执行"""
        self.executed_rules.add(rule_id)
        
        # 更新连续相同规则计数
        if rule_id == self.last_executed_rule_id:
            self.consecutive_same_rule_count += 1
        else:
            self.consecutive_same_rule_count = 1
            self.last_executed_rule_id = rule_id
        
        # 记录失败尝试
        if not success:
            self.failed_attempts[rule_id] = self.failed_attempts.get(rule_id, 0) + 1
    
    def is_rule_executed(self, rule_id: str) -> bool:
        """检查规则是否已执行"""
        return rule_id in self.executed_rules
    
    def add_completed_task(self, task_description: str) -> None:
        """添加已完成任务"""
        if task_description not in self.completed_tasks:
            self.completed_tasks.append(task_description)
    
    def get_rule_failure_count(self, rule_id: str) -> int:
        """获取规则失败次数"""
        return self.failed_attempts.get(rule_id, 0)
    
    def should_skip_rule(self, rule_id: str, max_failures: int = 3) -> bool:
        """判断是否应该跳过规则（失败次数过多）"""
        return self.get_rule_failure_count(rule_id) >= max_failures
    
    def detect_potential_loop(self, max_consecutive: int = 3) -> bool:
        """检测潜在的死循环"""
        return self.consecutive_same_rule_count >= max_consecutive
    
    def generate_state_fingerprint(self) -> str:
        """生成状态指纹用于循环检测"""
        import hashlib
        
        # 创建状态的唯一标识
        fingerprint_data = {
            'state': self.state,
            'executed_rules': sorted(list(self.executed_rules)),
            'completed_tasks': self.completed_tasks,
            'iteration': self.iteration_count
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()[:16]
    
    def check_state_cycle(self, lookback_window: int = 5) -> bool:
        """检查状态是否陷入循环"""
        current_fingerprint = self.generate_state_fingerprint()
        
        # 添加当前指纹到历史
        self.state_fingerprints.append(current_fingerprint)
        
        # 只保留最近的指纹记录
        if len(self.state_fingerprints) > lookback_window * 2:
            self.state_fingerprints = self.state_fingerprints[-lookback_window * 2:]
        
        # 检查是否有重复的指纹在回溯窗口内
        if len(self.state_fingerprints) >= lookback_window:
            recent_fingerprints = self.state_fingerprints[-lookback_window:]
            return current_fingerprint in recent_fingerprints[:-1]  # 排除当前指纹
        
        return False
    
    def get_available_rules(self, all_rules: List['ProductionRule']) -> List['ProductionRule']:
        """获取可执行的规则列表（过滤已执行和失败过多的规则）"""
        available_rules = []
        
        for rule in all_rules:
            # 跳过已执行的规则
            if self.is_rule_executed(rule.id):
                continue
            
            # 跳过失败次数过多的规则
            if self.should_skip_rule(rule.id):
                continue
            
            available_rules.append(rule)
        
        return available_rules
    
    def reset_rule_execution_state(self, rule_id: str) -> None:
        """重置规则执行状态（用于错误恢复）"""
        self.executed_rules.discard(rule_id)
        if rule_id in self.failed_attempts:
            del self.failed_attempts[rule_id]
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要信息"""
        return {
            'total_rules_executed': len(self.executed_rules),
            'completed_tasks_count': len(self.completed_tasks),
            'total_failures': sum(self.failed_attempts.values()),
            'iteration_count': self.iteration_count,
            'potential_loop_detected': self.detect_potential_loop(),
            'state_cycle_detected': self.check_state_cycle() if self.state_fingerprints else False,
            'most_failed_rule': max(self.failed_attempts.items(), key=lambda x: x[1])[0] if self.failed_attempts else None
        }
    
    def update_from_result(self, execution_result: WorkflowResult, executed_rule_id: Optional[str] = None) -> 'WorkflowState':
        """根据执行结果更新状态，返回新的状态实例"""
        # 创建新的状态实例（保持不可变性）
        new_state = WorkflowState(
            id=f"{self.id}_iter_{self.iteration_count + 1}",
            state=self.state,
            context_variables=self.context_variables.copy(),
            execution_history=self.execution_history.copy(),
            workflow_id=self.workflow_id,
            iteration_count=self.iteration_count + 1,
            goal_achieved=self.goal_achieved,
            
            # 复制增强字段
            executed_rules=self.executed_rules.copy(),
            completed_tasks=self.completed_tasks.copy(),
            failed_attempts=self.failed_attempts.copy(),
            last_decision_context=self.last_decision_context.copy(),
            state_fingerprints=self.state_fingerprints.copy(),
            consecutive_same_rule_count=self.consecutive_same_rule_count,
            last_executed_rule_id=self.last_executed_rule_id
        )
        
        # 标记规则执行
        if executed_rule_id:
            new_state.mark_rule_executed(executed_rule_id, execution_result.success)
        
        # 更新执行历史
        history_entry = f"[iter_{new_state.iteration_count}] {execution_result.message}"
        new_state.execution_history.append(history_entry)
        
        # 更新上下文变量
        if execution_result.metadata:
            new_state.context_variables.update(execution_result.metadata)
        
        # 如果执行成功，可能需要更新状态描述
        if execution_result.success and execution_result.data:
            if isinstance(execution_result.data, dict) and 'new_state' in execution_result.data:
                new_state.state = execution_result.data['new_state']
            
            # 添加完成的任务
            if isinstance(execution_result.data, dict) and 'completed_task' in execution_result.data:
                new_state.add_completed_task(execution_result.data['completed_task'])
        
        return new_state
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'state': self.state,
            'context_variables': self.context_variables,
            'execution_history': self.execution_history,
            'workflow_id': self.workflow_id,
            'iteration_count': self.iteration_count,
            'goal_achieved': self.goal_achieved,
            'executed_rules': list(self.executed_rules),
            'completed_tasks': self.completed_tasks,
            'failed_attempts': self.failed_attempts,
            'last_decision_context': self.last_decision_context,
            'consecutive_same_rule_count': self.consecutive_same_rule_count,
            'last_executed_rule_id': self.last_executed_rule_id,
            'execution_summary': self.get_execution_summary()
        }


@dataclass
class GlobalState:
    """全局状态实体 - 系统的全局状态管理（保持向后兼容）"""
    id: str
    state: str                  # 自然语言状态描述
    context_variables: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[str] = field(default_factory=list)
    # timestamp: datetime = field(default_factory=datetime.now)  # 已移除: LLM缓存优化
    workflow_id: str = ""
    iteration_count: int = 0
    goal_achieved: bool = False
    
    def __post_init__(self):
        """初始化后验证"""
        # 已移除UUID自动生成: LLM缓存优化 - ID需要显式提供
        # if not self.id:
        #     self.id = str(uuid.uuid4())
    
    def update_from_result(self, execution_result: WorkflowResult) -> 'GlobalState':
        """根据执行结果更新状态，返回新的状态实例"""
        # 创建新的状态实例（保持不可变性）
        new_state = GlobalState(
            id=f"{self.id}_iter_{self.iteration_count + 1}",  # Use deterministic ID instead of UUID
            state=self.state,
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
            if isinstance(execution_result.data, dict) and 'new_state' in execution_result.data:
                new_state.state = execution_result.data['new_state']
        
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
            'state': self.state,
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
    # created_at: datetime = field(default_factory=datetime.now)  # 已移除: LLM缓存优化
    # updated_at: datetime = field(default_factory=datetime.now)  # 已移除: LLM缓存优化
    version: int = 1
    status: RuleSetStatus = RuleSetStatus.DRAFT
    modification_history: List[RuleModification] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后验证"""
        # 已移除UUID自动生成: LLM缓存优化 - ID需要显式提供
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
    """
    决策结果实体 - 封装产生式规则工作流决策过程的结果
    
    该类代表LLM决策引擎在分析当前状态和可用规则后做出的智能决策。
    决策结果包含具体的行动指令、置信度评估和详细推理过程。
    
    Attributes:
        selected_rule (Optional[ProductionRule]): 被选中执行的规则
            - 当 decision_type == EXECUTE_SELECTED_RULE 时，包含要执行的具体规则对象
            - 当 decision_type == ADD_RULE 或 GOAL_FAILED 时，为 None
            - 规则对象包含完整的条件(IF)、动作(THEN)、智能体能力等信息
            
        decision_type (DecisionType): 决策类型，指示接下来应该采取的行动
            - EXECUTE_SELECTED_RULE: 执行现有规则（最常见的决策）
            - ADD_RULE: 生成新规则来处理当前情况
            - GOAL_ACHIEVED: 工作流目标已成功达成
            - GOAL_FAILED: 目标执行失败，无法继续推进
            
        confidence (float): 决策置信度，范围 [0.0, 1.0]
            - 0.9-1.0: 高置信度，LLM对决策非常确信
            - 0.7-0.8: 中等置信度，决策合理但可能需要监控
            - 0.5-0.6: 低置信度，决策不确定，建议人工审核
            - 0.0-0.4: 极低置信度，可能需要重新分析或获取更多信息
            
        reasoning (str): 决策推理过程的详细说明
            - 解释为什么选择了特定的决策类型
            - 描述分析过程中考虑的关键因素
            - 说明规则匹配或新规则生成的理由
            - 提供人类可理解的决策依据，便于调试和优化
            
        context (Dict[str, Any]): 决策上下文信息
            - state_description: 决策时的状态描述
            - total_applicable_rules: 可用规则总数
            - relevance_score: 规则相关性评分
            - selection_method: 选择方法标识
            - alternative_options: 备选方案信息
            - 其他与决策过程相关的元数据
            
        new_rules (List[ProductionRule]): 新生成的规则列表
            - 当 decision_type == ADD_RULE 时，包含LLM生成的新规则
            - 每个规则都是完整的 ProductionRule 对象，可以立即添加到规则集中
            - 规则按优先级排序，优先级高的规则在列表前面
            - 当 decision_type != ADD_RULE 时，此列表为空
            
    使用示例:
        # 执行规则决策
        if decision.decision_type == DecisionType.EXECUTE_SELECTED_RULE:
            rule = decision.selected_rule
            print(f"执行规则: {rule.name}, 置信度: {decision.confidence}")
            
        # 添加新规则决策  
        elif decision.decision_type == DecisionType.ADD_RULE:
            for rule in decision.new_rules:
                rule_set.add_rule(rule)
            print(f"添加了 {len(decision.new_rules)} 个新规则")
            
        # 目标完成决策
        elif decision.decision_type == DecisionType.GOAL_ACHIEVED:
            print("工作流目标已达成！")
            
    注意事项:
        - 决策结果是不可变的，一旦创建就不应修改
        - confidence 值应该与 reasoning 的描述一致
        - selected_rule 和 new_rules 是互斥的，不会同时包含内容
        - context 字段用于存储调试和分析信息，不影响决策执行
    """
    selected_rule: Optional[ProductionRule]
    decision_type: DecisionType
    confidence: float
    reasoning: str
    context: Dict[str, Any] = field(default_factory=dict)
    # timestamp: datetime = field(default_factory=datetime.now)  # 已移除: LLM缓存优化
    new_rules: List[ProductionRule] = field(default_factory=list)
    
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
            new_rules_count = len(self.new_rules) if self.new_rules else 0
            return f"需要添加新规则 ({new_rules_count} 个)"
        elif self.decision_type == DecisionType.GOAL_ACHIEVED:
            return "目标已达成"
        elif self.decision_type == DecisionType.GOAL_FAILED:
            return "目标执行失败"
        return "未知决策类型"




@dataclass
class AgentRegistry:
    """智能体注册表实体 - 直接管理Agent实例"""
    agents: Dict[str, Any] = field(default_factory=dict)  # Any为AgentBase类型，避免循环导入
    
    def register_agent(self, name: str, agent: Any) -> None:
        """注册Agent实例"""
        self.agents[name] = agent
    
    def get_agent(self, name: str) -> Any:
        """获取Agent实例"""
        if name not in self.agents:
            raise ValueError(f"未找到智能体: {name}")
        return self.agents[name]
    
    def find_agents_by_specification(self, task_description: str) -> List[tuple]:
        """根据任务描述查找合适的Agent，返回(name, agent)元组列表"""
        return [
            (name, agent) for name, agent in self.agents.items()
            if hasattr(agent, 'api_specification') and agent.api_specification
        ]
    
    def list_all_agents(self) -> List[tuple]:
        """列出所有Agent实例，返回(name, agent)元组列表"""
        return list(self.agents.items())
    
    def get_agent_specifications(self) -> Dict[str, str]:
        """获取所有Agent的能力规范"""
        return {
            name: getattr(agent, 'api_specification', f'{name} Agent')
            for name, agent in self.agents.items()
        }
    
    def remove_agent(self, name: str) -> bool:
        """移除Agent实例"""
        if name in self.agents:
            del self.agents[name]
            return True
        return False


@dataclass
class RuleSetExecution:
    """规则集执行实体 - 管理规则集的执行实例（实例层）"""
    id: str
    rule_set_id: str  # 对应的规则集ID（类型层）
    global_state: GlobalState  # 工作流当前状态
    rule_executions: List[RuleExecution] = field(default_factory=list)  # 规则执行记录
    status: ExecutionStatus = ExecutionStatus.PENDING
    # started_at: datetime = field(default_factory=datetime.now)  # Removed for LLM caching
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)  # 执行上下文
    
    def add_rule_execution(self, rule_execution: RuleExecution) -> None:
        """添加规则执行记录"""
        self.rule_executions.append(rule_execution)
    
    def get_latest_execution(self) -> Optional[RuleExecution]:
        """获取最新的规则执行记录"""
        return self.rule_executions[-1] if self.rule_executions else None
    
    def is_completed(self) -> bool:
        """检查执行是否完成"""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
    
    def mark_completed(self, success: bool = True) -> None:
        """标记执行完成"""
        self.status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'rule_set_id': self.rule_set_id,
            'global_state': self.global_state.to_dict(),
            'rule_executions': [exec.id for exec in self.rule_executions],
            'status': self.status.value,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'context': self.context
        }