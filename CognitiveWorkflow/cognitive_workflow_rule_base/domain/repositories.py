# -*- coding: utf-8 -*-
"""
仓储接口定义

定义数据持久化的抽象接口，遵循Repository模式。
这些接口属于Domain Layer，不包含具体的技术实现。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime

from .entities import (
    ProductionRule, RuleSet, RuleExecution, GlobalState
)
from .value_objects import RulePhase, ExecutionStatus


class RuleRepository(ABC):
    """规则仓储接口 - 抽象规则持久化操作"""
    
    @abstractmethod
    def save_rule_set(self, rule_set: RuleSet) -> None:
        """保存规则集"""
        pass
    
    @abstractmethod
    def load_rule_set(self, rule_set_id: str) -> RuleSet:
        """加载规则集"""
        pass
    
    @abstractmethod
    def find_rules_by_condition(self, condition_pattern: str) -> List[ProductionRule]:
        """根据条件模式查找规则"""
        pass
    
    @abstractmethod
    def find_rules_by_phase(self, phase: RulePhase) -> List[ProductionRule]:
        """根据阶段查找规则"""
        pass
    
    @abstractmethod
    def save_rule(self, rule: ProductionRule) -> None:
        """保存单个规则"""
        pass
    
    @abstractmethod
    def load_rule(self, rule_id: str) -> ProductionRule:
        """加载单个规则"""
        pass
    
    @abstractmethod
    def delete_rule(self, rule_id: str) -> bool:
        """删除规则"""
        pass
    
    @abstractmethod
    def find_rules_by_agent_capability(self, capability_id: str) -> List[ProductionRule]:
        """根据智能体能力查找规则"""
        pass
    
    @abstractmethod
    def find_rules_by_priority_range(self, min_priority: int, max_priority: int) -> List[ProductionRule]:
        """根据优先级范围查找规则"""
        pass
    
    @abstractmethod
    def get_rule_count(self) -> int:
        """获取规则总数"""
        pass
    
    @abstractmethod
    def list_all_rule_sets(self) -> List[RuleSet]:
        """列出所有规则集"""
        pass


class StateRepository(ABC):
    """状态仓储接口 - 抽象状态持久化操作"""
    
    @abstractmethod
    def save_state(self, global_state: GlobalState) -> None:
        """保存状态"""
        pass
    
    @abstractmethod
    def load_state(self, state_id: str) -> GlobalState:
        """加载状态"""
        pass
    
    @abstractmethod
    def get_state_history(self, workflow_id: str) -> List[GlobalState]:
        """获取工作流的状态历史"""
        pass
    
    @abstractmethod
    def save_state_snapshot(self, state: GlobalState, snapshot_name: str) -> None:
        """保存状态快照"""
        pass
    
    @abstractmethod
    def load_state_snapshot(self, snapshot_name: str) -> GlobalState:
        """加载状态快照"""
        pass
    
    @abstractmethod
    def find_states_by_workflow(self, workflow_id: str) -> List[GlobalState]:
        """根据工作流ID查找状态"""
        pass
    
    @abstractmethod
    def find_states_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[GlobalState]:
        """根据时间范围查找状态"""
        pass
    
    @abstractmethod
    def get_latest_state(self, workflow_id: str) -> Optional[GlobalState]:
        """获取工作流的最新状态"""
        pass
    
    @abstractmethod
    def delete_old_states(self, cutoff_time: datetime) -> int:
        """删除旧状态，返回删除的数量"""
        pass
    
    @abstractmethod
    def get_state_count(self, workflow_id: Optional[str] = None) -> int:
        """获取状态数量"""
        pass


class ExecutionRepository(ABC):
    """执行仓储接口 - 抽象执行历史管理"""
    
    @abstractmethod
    def save_execution(self, rule_execution: RuleExecution) -> None:
        """保存规则执行记录"""
        pass
    
    @abstractmethod
    def load_execution(self, execution_id: str) -> RuleExecution:
        """加载规则执行记录"""
        pass
    
    @abstractmethod
    def find_executions_by_rule(self, rule_id: str) -> List[RuleExecution]:
        """根据规则ID查找执行记录"""
        pass
    
    @abstractmethod
    def find_failed_executions(
        self, 
        time_range: Tuple[datetime, datetime]
    ) -> List[RuleExecution]:
        """查找失败的执行记录"""
        pass
    
    @abstractmethod
    def find_executions_by_status(self, status: ExecutionStatus) -> List[RuleExecution]:
        """根据状态查找执行记录"""
        pass
    
    @abstractmethod
    def find_executions_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[RuleExecution]:
        """根据时间范围查找执行记录"""
        pass
    
    @abstractmethod
    def get_execution_statistics(
        self, 
        rule_id: Optional[str] = None
    ) -> dict:
        """获取执行统计信息"""
        pass
    
    @abstractmethod
    def get_recent_executions(
        self, 
        limit: int = 100
    ) -> List[RuleExecution]:
        """获取最近的执行记录"""
        pass
    
    @abstractmethod
    def delete_old_executions(self, cutoff_time: datetime) -> int:
        """删除旧的执行记录，返回删除的数量"""
        pass
    
    @abstractmethod
    def get_execution_count(
        self, 
        rule_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None
    ) -> int:
        """获取执行记录数量"""
        pass
    
    @abstractmethod
    def find_long_running_executions(
        self, 
        threshold_seconds: int = 300
    ) -> List[RuleExecution]:
        """查找长时间运行的执行记录"""
        pass
    
    @abstractmethod
    def update_execution_status(
        self, 
        execution_id: str, 
        status: ExecutionStatus,
        failure_reason: Optional[str] = None
    ) -> bool:
        """更新执行状态"""
        pass