# -*- coding: utf-8 -*-
"""
值对象和枚举定义

包含系统中使用的所有枚举类型和值对象，
这些是不可变的业务概念，用于表达业务状态和类型。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class RulePhase(Enum):
    """规则执行阶段枚举"""
    INFORMATION_GATHERING = "information_gathering"  # 信息收集阶段
    PROBLEM_SOLVING = "problem_solving"             # 问题解决阶段
    VERIFICATION = "verification"                   # 验证阶段
    CLEANUP = "cleanup"                            # 清理阶段


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"         # 待执行
    RUNNING = "running"         # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 失败
    SKIPPED = "skipped"        # 跳过
    CANCELLED = "cancelled"    # 取消


class DecisionType(Enum):
    """决策类型枚举"""
    EXECUTE_SELECTED_RULE = "execute_selected_rule"  # 执行选中的规则
    ADD_RULE = "add_rule"                           # 添加新规则
    GOAL_ACHIEVED = "goal_achieved"                 # 目标达成
    GOAL_FAILED = "goal_failed"                     # 目标失败


class RuleSetStatus(Enum):
    """规则集状态枚举"""
    DRAFT = "draft"           # 草稿
    ACTIVE = "active"         # 活跃
    COMPLETED = "completed"   # 已完成
    ABANDONED = "abandoned"   # 已废弃


class ModificationType(Enum):
    """计划修改类型枚举"""
    ADD_RULE = "add_rule"         # 添加规则
    REMOVE_RULE = "remove_rule"   # 删除规则
    MODIFY_RULE = "modify_rule"   # 修改规则
    REORDER_RULES = "reorder_rules"  # 重排规则


@dataclass(frozen=True)
class RuleModification:
    """规则修改记录 - 值对象"""
    modification_type: ModificationType
    target_rule_id: Optional[str]
    new_rule_data: Optional[dict]
    modification_reason: str
    timestamp: datetime
    
    def __post_init__(self):
        """验证修改记录的一致性"""
        if self.modification_type == ModificationType.ADD_RULE:
            if not self.new_rule_data:
                raise ValueError("添加规则时必须提供new_rule_data")
        elif self.modification_type in [ModificationType.REMOVE_RULE, ModificationType.MODIFY_RULE]:
            if not self.target_rule_id:
                raise ValueError("删除或修改规则时必须提供target_rule_id")


@dataclass(frozen=True)
class ExecutionMetrics:
    """执行指标 - 值对象"""
    total_rules_executed: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    total_execution_time: float
    rule_match_accuracy: float
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_rules_executed == 0:
            return 0.0
        return self.successful_executions / self.total_rules_executed
    
    @property
    def failure_rate(self) -> float:
        """失败率"""
        return 1.0 - self.success_rate


@dataclass(frozen=True)
class StateChangeAnalysis:
    """状态变化分析 - 值对象"""
    before_state: str
    after_state: str
    key_changes: list
    semantic_similarity: float
    change_significance: str  # 'minor', 'moderate', 'major'
    timestamp: datetime
    
    def is_significant_change(self) -> bool:
        """是否为重要变化"""
        return self.change_significance in ['moderate', 'major']


@dataclass(frozen=True)
class MatchingResult:
    """匹配结果 - 值对象"""
    is_match: bool
    confidence: float
    reasoning: str
    semantic_similarity: float
    
    def is_confident_match(self, threshold: float = 0.8) -> bool:
        """是否为高置信度匹配"""
        return self.is_match and self.confidence >= threshold


@dataclass(frozen=True)
class WorkflowResult:
    """工作流执行结果 - 值对象"""
    goal: str
    is_successful: bool
    final_state: str
    total_iterations: int
    execution_metrics: ExecutionMetrics
    final_message: str
    completion_timestamp: datetime
    
    def get_summary(self) -> str:
        """获取执行摘要"""
        status = "成功" if self.is_successful else "失败"
        return (f"工作流执行{status}: {self.goal}\n"
                f"总迭代次数: {self.total_iterations}\n"
                f"成功率: {self.execution_metrics.success_rate:.2%}\n"
                f"最终状态: {self.final_state}")


# 常量定义
class RuleConstants:
    """规则系统常量"""
    DEFAULT_RULE_PRIORITY = 50
    MAX_RULE_PRIORITY = 100
    MIN_RULE_PRIORITY = 1
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    MAX_ITERATIONS = 100
    DEFAULT_TIMEOUT_SECONDS = 300


class MatchingConstants:
    """匹配系统常量"""
    HIGH_CONFIDENCE_THRESHOLD = 0.9
    MEDIUM_CONFIDENCE_THRESHOLD = 0.7
    LOW_CONFIDENCE_THRESHOLD = 0.5
    SEMANTIC_SIMILARITY_THRESHOLD = 0.8


class ExecutionConstants:
    """执行系统常量"""
    MAX_RETRY_ATTEMPTS = 3
    DEFAULT_EXECUTION_TIMEOUT = 60
    BATCH_SIZE = 10
    PERFORMANCE_SAMPLE_SIZE = 100