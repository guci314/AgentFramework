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
    """规则执行阶段枚举 - 三阶段执行模式"""
    INFORMATION_GATHERING = "information_gathering"  # 信息收集阶段
    EXECUTION = "execution"                         # 执行阶段
    VERIFICATION = "verification"                   # 验证阶段


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
    EXECUTE_SELECTED_RULE = "EXECUTE_SELECTED_RULE"  # 执行选中的规则
    ADD_RULE = "ADD_RULE"                           # 添加新规则
    GOAL_ACHIEVED = "GOAL_ACHIEVED"                 # 目标达成
    GOAL_FAILED = "GOAL_FAILED"                     # 目标失败
    INITIALIZE_WORKFLOW = "INITIALIZE_WORKFLOW"     # 初始化工作流


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
class WorkflowExecutionResult:
    """工作流执行结果摘要 - 值对象"""
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
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'goal': self.goal,
            'is_successful': self.is_successful,
            'final_state': self.final_state,
            'total_iterations': self.total_iterations,
            'execution_metrics': {
                'total_rules_executed': self.execution_metrics.total_rules_executed,
                'successful_executions': self.execution_metrics.successful_executions,
                'failed_executions': self.execution_metrics.failed_executions,
                'average_execution_time': self.execution_metrics.average_execution_time,
                'total_execution_time': self.execution_metrics.total_execution_time,
                'rule_match_accuracy': self.execution_metrics.rule_match_accuracy,
                'success_rate': self.execution_metrics.success_rate
            },
            'final_message': self.final_message,
            'completion_timestamp': self.completion_timestamp.isoformat()
        }


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


# 自适应规则替换相关枚举和值对象

class ReplacementStrategyType(Enum):
    """替换策略类型枚举"""
    MINIMAL_REPLACEMENT = "minimal_replacement"           # 最小替换：规则稀缺时
    PERFORMANCE_FOCUSED = "performance_focused"           # 性能导向：优化执行效率
    AGGRESSIVE_CLEANUP = "aggressive_cleanup"             # 激进清理：规则冗余时
    INCREMENTAL_IMPROVEMENT = "incremental_improvement"   # 渐进改进：系统稳定时
    EMERGENCY_REPLACEMENT = "emergency_replacement"       # 紧急替换：频繁失败时
    STRATEGIC_PIVOT = "strategic_pivot"                   # 策略转向：目标偏离时
    AGENT_REBALANCING = "agent_rebalancing"              # 智能体重平衡
    PHASE_OPTIMIZATION = "phase_optimization"            # 阶段优化


class SituationContext(Enum):
    """情境上下文类型枚举"""
    STARTUP_PHASE = "startup_phase"             # 启动阶段
    EXECUTION_PHASE = "execution_phase"         # 执行阶段  
    BOTTLENECK_PHASE = "bottleneck_phase"       # 瓶颈阶段
    COMPLETION_PHASE = "completion_phase"       # 收尾阶段
    RECOVERY_PHASE = "recovery_phase"           # 恢复阶段


@dataclass(frozen=True)
class SituationScore:
    """情境评估分数 - 值对象"""
    rule_density: float           # 规则密度 (0.0-1.0)
    execution_efficiency: float   # 执行效率 (0.0-1.0)
    goal_progress: float          # 目标进度 (0.0-1.0)
    failure_frequency: float      # 失败频率 (0.0-1.0)
    agent_utilization: float      # 智能体利用率 (0.0-1.0)
    phase_distribution: float     # 阶段分布不平衡度 (0.0-1.0)
    
    def get_overall_health(self) -> float:
        """计算整体健康度"""
        # 权重设计：效率和进度更重要
        weights = {
            'execution_efficiency': 0.25,
            'goal_progress': 0.25,
            'rule_density': 0.15,
            'failure_frequency': 0.20,  # 失败率取反
            'agent_utilization': 0.10,
            'phase_distribution': 0.05
        }
        
        health_score = (
            weights['execution_efficiency'] * self.execution_efficiency +
            weights['goal_progress'] * self.goal_progress +
            weights['rule_density'] * (1.0 - self.rule_density) +  # 规则密度过高不好
            weights['failure_frequency'] * (1.0 - self.failure_frequency) +  # 失败率取反
            weights['agent_utilization'] * self.agent_utilization +
            weights['phase_distribution'] * (1.0 - self.phase_distribution)  # 分布不平衡取反
        )
        
        return max(0.0, min(1.0, health_score))
    
    def get_critical_issues(self) -> list:
        """获取关键问题列表"""
        issues = []
        
        if self.execution_efficiency < 0.5:
            issues.append("执行效率过低")
        if self.goal_progress < 0.3:
            issues.append("目标进度停滞")
        if self.failure_frequency > 0.5:
            issues.append("失败频率过高")
        if self.rule_density > 0.8:
            issues.append("规则密度过高")
        if self.agent_utilization < 0.4:
            issues.append("智能体利用率不足")
        if self.phase_distribution > 0.7:
            issues.append("阶段分布严重不平衡")
            
        return issues


@dataclass(frozen=True)
class ReplacementStrategy:
    """替换策略配置 - 值对象"""
    strategy_type: ReplacementStrategyType
    replacement_ratio: float       # 替换比例 (0.0-1.0)
    similarity_threshold: float    # 相似性阈值 (0.0-1.0)
    performance_threshold: float   # 性能阈值 (0.0-1.0)
    priority_adjustment: bool      # 是否调整优先级
    conservative_mode: bool        # 是否启用保守模式
    max_rules_per_phase: int       # 每阶段最大规则数
    max_rules_per_agent: int       # 每智能体最大规则数
    
    def is_aggressive_strategy(self) -> bool:
        """是否为激进策略"""
        return self.replacement_ratio > 0.5 or not self.conservative_mode
    
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        descriptions = {
            ReplacementStrategyType.MINIMAL_REPLACEMENT: "最小化替换，保持系统稳定",
            ReplacementStrategyType.PERFORMANCE_FOCUSED: "性能导向替换，优化执行效率",
            ReplacementStrategyType.AGGRESSIVE_CLEANUP: "激进清理冗余规则",
            ReplacementStrategyType.INCREMENTAL_IMPROVEMENT: "渐进式优化改进",
            ReplacementStrategyType.EMERGENCY_REPLACEMENT: "紧急替换应对危机",
            ReplacementStrategyType.STRATEGIC_PIVOT: "策略性转向重新规划",
            ReplacementStrategyType.AGENT_REBALANCING: "智能体负载重平衡",
            ReplacementStrategyType.PHASE_OPTIMIZATION: "执行阶段优化"
        }
        return descriptions.get(self.strategy_type, "未知策略")


@dataclass(frozen=True)
class StrategyEffectiveness:
    """策略效果评估 - 值对象"""
    strategy_type: ReplacementStrategyType
    applied_context: SituationScore
    before_metrics: ExecutionMetrics
    after_metrics: ExecutionMetrics
    improvement_score: float       # 改进分数 (0.0-1.0)
    application_timestamp: datetime
    
    def get_performance_gain(self) -> float:
        """计算性能提升"""
        if self.before_metrics.success_rate == 0:
            return self.after_metrics.success_rate
        return (self.after_metrics.success_rate - self.before_metrics.success_rate) / self.before_metrics.success_rate
    
    def get_efficiency_gain(self) -> float:
        """计算效率提升"""
        if self.before_metrics.average_execution_time == 0:
            return 0.0
        return (self.before_metrics.average_execution_time - self.after_metrics.average_execution_time) / self.before_metrics.average_execution_time
    
    def is_successful_application(self) -> bool:
        """是否为成功的策略应用"""
        return (
            self.improvement_score > 0.6 and
            self.get_performance_gain() > -0.1 and  # 性能不能显著下降
            self.after_metrics.success_rate > 0.5   # 基本成功率要求
        )


# 自适应替换常量
class AdaptiveReplacementConstants:
    """自适应替换系统常量"""
    # 情境评估阈值
    HIGH_RULE_DENSITY_THRESHOLD = 0.8
    LOW_EXECUTION_EFFICIENCY_THRESHOLD = 0.5
    STALLED_PROGRESS_THRESHOLD = 0.3
    HIGH_FAILURE_FREQUENCY_THRESHOLD = 0.5
    LOW_AGENT_UTILIZATION_THRESHOLD = 0.4
    UNBALANCED_PHASE_DISTRIBUTION_THRESHOLD = 0.7
    
    # 替换策略参数
    DEFAULT_REPLACEMENT_RATIO = 0.3
    MAX_REPLACEMENT_RATIO = 0.8
    MIN_REPLACEMENT_RATIO = 0.1
    DEFAULT_SIMILARITY_THRESHOLD = 0.8
    DEFAULT_PERFORMANCE_THRESHOLD = 0.6
    
    # 规则数量限制
    DEFAULT_MAX_RULES_PER_PHASE = 4
    DEFAULT_MAX_RULES_PER_AGENT = 5
    ABSOLUTE_MAX_TOTAL_RULES = 15
    MIN_TOTAL_RULES = 3
    
    # 策略效果评估
    STRATEGY_EFFECTIVENESS_SAMPLE_SIZE = 10
    MIN_IMPROVEMENT_SCORE = 0.3
    STRATEGY_LEARNING_DECAY_FACTOR = 0.9