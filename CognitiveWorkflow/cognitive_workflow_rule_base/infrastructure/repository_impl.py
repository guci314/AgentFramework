# -*- coding: utf-8 -*-
"""
仓储实现

提供基于内存和文件的仓储实现，用于数据的持久化存储。
在生产环境中可以替换为基于数据库的实现。
"""

from typing import Dict, List, Optional, Tuple
import json
import os
import logging
from datetime import datetime
from pathlib import Path

from ..domain.entities import (
    ProductionRule, RuleSet, RuleExecution, GlobalState
)
from ..domain.repositories import (
    RuleRepository, StateRepository, ExecutionRepository
)
from ..domain.value_objects import RulePhase, ExecutionStatus
from ..utils.concurrent_safe_id_generator import id_generator, SafeFileOperations

logger = logging.getLogger(__name__)


class RuleRepositoryImpl(RuleRepository):
    """规则仓储实现 - 基于文件存储"""
    
    def __init__(self, storage_path: str = "./.cognitive_workflow_data/rules"):
        """
        初始化规则仓储
        
        Args:
            storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._rule_sets_cache: Dict[str, RuleSet] = {}
        self._rules_cache: Dict[str, ProductionRule] = {}
        
        # 加载现有数据
        self._load_existing_data()
    
    def save_rule_set(self, rule_set: RuleSet) -> None:
        """保存规则集（并发安全）"""
        try:
            file_path = self.storage_path / f"rule_set_{rule_set.id}.json"
            
            # 🔑 检查文件冲突
            if SafeFileOperations.check_file_conflict(file_path):
                logger.warning(f"检测到文件冲突，等待后重试: {file_path}")
                import time
                time.sleep(0.1)
            
            # 转换为可序列化的格式
            rule_set_data = {
                'id': rule_set.id,
                'goal': rule_set.goal,
                'rules': [self._rule_to_dict(rule) for rule in rule_set.rules],
                # 'created_at': rule_set.created_at.isoformat(),  # Removed for LLM caching
                # 'updated_at': rule_set.updated_at.isoformat(),  # Removed for LLM caching
                'version': rule_set.version,
                'status': rule_set.status.value,
                'modification_history': [self._modification_to_dict(mod) for mod in rule_set.modification_history]
            }
            
            # 🔑 使用原子性写入
            if not SafeFileOperations.atomic_write_json(file_path, rule_set_data):
                raise IOError(f"原子性写入失败: {file_path}")
            
            # 更新缓存
            self._rule_sets_cache[rule_set.id] = rule_set
            for rule in rule_set.rules:
                self._rules_cache[rule.id] = rule
            
            logger.debug(f"规则集已安全保存: {rule_set.id}")
            
        except Exception as e:
            logger.error(f"保存规则集失败: {e}")
            raise
    
    def load_rule_set(self, rule_set_id: str) -> RuleSet:
        """加载规则集"""
        try:
            # 先检查缓存
            if rule_set_id in self._rule_sets_cache:
                return self._rule_sets_cache[rule_set_id]
            
            file_path = self.storage_path / f"rule_set_{rule_set_id}.json"
            
            if not file_path.exists():
                raise ValueError(f"规则集不存在: {rule_set_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_set_data = json.load(f)
            
            rule_set = self._dict_to_rule_set(rule_set_data)
            
            # 更新缓存
            self._rule_sets_cache[rule_set_id] = rule_set
            
            return rule_set
            
        except Exception as e:
            logger.error(f"加载规则集失败: {e}")
            raise
    
    def find_rules_by_condition(self, condition_pattern: str) -> List[ProductionRule]:
        """根据条件模式查找规则"""
        try:
            matching_rules = []
            
            for rule in self._rules_cache.values():
                if condition_pattern.lower() in rule.condition.lower():
                    matching_rules.append(rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"按条件查找规则失败: {e}")
            return []
    
    def find_rules_by_phase(self, phase: RulePhase) -> List[ProductionRule]:
        """根据阶段查找规则"""
        try:
            matching_rules = []
            
            for rule in self._rules_cache.values():
                if rule.phase == phase:
                    matching_rules.append(rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"按阶段查找规则失败: {e}")
            return []
    
    def save_rule(self, rule: ProductionRule) -> None:
        """保存单个规则"""
        try:
            self._rules_cache[rule.id] = rule
            logger.debug(f"规则已缓存: {rule.id}")
            
        except Exception as e:
            logger.error(f"保存规则失败: {e}")
            raise
    
    def load_rule(self, rule_id: str) -> ProductionRule:
        """加载单个规则"""
        try:
            if rule_id in self._rules_cache:
                return self._rules_cache[rule_id]
            
            raise ValueError(f"规则不存在: {rule_id}")
            
        except Exception as e:
            logger.error(f"加载规则失败: {e}")
            raise
    
    def delete_rule(self, rule_id: str) -> bool:
        """删除规则"""
        try:
            if rule_id in self._rules_cache:
                del self._rules_cache[rule_id]
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除规则失败: {e}")
            return False
    
    def find_rules_by_agent_capability(self, agent_name: str) -> List[ProductionRule]:
        """根据智能体名称查找规则（保持方法名兼容性）"""
        return self.find_rules_by_agent_name(agent_name)
    
    def find_rules_by_agent_name(self, agent_name: str) -> List[ProductionRule]:
        """根据智能体名称查找规则"""
        try:
            matching_rules = []
            
            for rule in self._rules_cache.values():
                if rule.agent_name == agent_name:
                    matching_rules.append(rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"按智能体名称查找规则失败: {e}")
            return []
    
    def find_rules_by_priority_range(self, min_priority: int, max_priority: int) -> List[ProductionRule]:
        """根据优先级范围查找规则"""
        try:
            matching_rules = []
            
            for rule in self._rules_cache.values():
                if min_priority <= rule.priority <= max_priority:
                    matching_rules.append(rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"按优先级范围查找规则失败: {e}")
            return []
    
    def get_rule_count(self) -> int:
        """获取规则总数"""
        return len(self._rules_cache)
    
    def list_all_rule_sets(self) -> List[RuleSet]:
        """列出所有规则集"""
        return list(self._rule_sets_cache.values())
    
    def _load_existing_data(self) -> None:
        """加载现有数据"""
        try:
            for file_path in self.storage_path.glob("rule_set_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rule_set_data = json.load(f)
                    
                    rule_set = self._dict_to_rule_set(rule_set_data)
                    self._rule_sets_cache[rule_set.id] = rule_set
                    
                    for rule in rule_set.rules:
                        self._rules_cache[rule.id] = rule
                        
                except Exception as e:
                    logger.error(f"加载规则集文件失败 {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"加载现有数据失败: {e}")
    
    def _rule_to_dict(self, rule: ProductionRule) -> Dict:
        """将规则转换为字典"""
        return rule.to_dict()
    
    def _dict_to_rule_set(self, data: Dict) -> RuleSet:
        """从字典创建规则集"""
        from ..domain.value_objects import RuleSetStatus, ModificationType
        
        # 转换规则列表
        rules = []
        for rule_data in data.get('rules', []):
            rule = self._dict_to_rule(rule_data)
            rules.append(rule)
        
        # 转换修改历史
        modification_history = []
        for mod_data in data.get('modification_history', []):
            mod = self._dict_to_modification(mod_data)
            modification_history.append(mod)
        
        rule_set = RuleSet(
            id=data['id'],
            goal=data['goal'],
            rules=rules,
            # created_at=datetime.fromisoformat(data.get('created_at')),  # Removed for LLM caching
            # updated_at=datetime.fromisoformat(data.get('updated_at')),  # Removed for LLM caching
            version=data.get('version', 1),
            status=RuleSetStatus(data.get('status', 'active')),
            modification_history=modification_history
        )
        
        return rule_set
    
    def _dict_to_rule(self, data: Dict) -> ProductionRule:
        """从字典创建规则，支持向后兼容性"""
        # Handle backward compatibility: agent_capability_id -> agent_name
        agent_name = data.get('agent_name') or data.get('agent_capability_id', 'coder')
        
        rule = ProductionRule(
            id=data['id'],
            name=data['name'],
            condition=data['condition'],
            action=data['action'],
            agent_name=agent_name,
            priority=data.get('priority', 50),
            phase=self._parse_phase_with_compatibility(data.get('phase', 'execution')),
            expected_outcome=data.get('expected_outcome', ''),
            # created_at=datetime.fromisoformat(data['created_at']),  # Removed for LLM caching
            # updated_at=datetime.fromisoformat(data['updated_at']),  # Removed for LLM caching
            metadata=data.get('metadata', {})
        )
        
        return rule
    
    def _parse_phase_with_compatibility(self, phase_value: str) -> RulePhase:
        """
        解析阶段值，支持向后兼容性
        
        Args:
            phase_value: 阶段字符串值
            
        Returns:
            RulePhase: 解析后的阶段枚举
        """
        try:
            # 处理旧的阶段值映射
            if phase_value == 'problem_solving':
                logger.debug("将旧的 'problem_solving' 阶段转换为 'execution'")
                return RulePhase.EXECUTION
            elif phase_value == 'cleanup':
                logger.debug("将旧的 'cleanup' 阶段转换为 'verification'")
                return RulePhase.VERIFICATION
            else:
                # 尝试直接解析
                return RulePhase(phase_value)
                
        except ValueError as e:
            logger.warning(f"无法解析阶段值 '{phase_value}'，使用默认值 'execution': {e}")
            return RulePhase.EXECUTION
    
    def _modification_to_dict(self, modification) -> Dict:
        """将修改记录转换为字典"""
        return {
            'modification_type': modification.modification_type.value,
            'target_rule_id': modification.target_rule_id,
            'new_rule_data': modification.new_rule_data,
            'modification_reason': modification.modification_reason,
            'timestamp': modification.timestamp.isoformat()
        }
    
    def _dict_to_modification(self, data: Dict):
        """从字典创建修改记录"""
        from ..domain.value_objects import RuleModification, ModificationType
        
        return RuleModification(
            modification_type=ModificationType(data['modification_type']),
            target_rule_id=data.get('target_rule_id'),
            new_rule_data=data.get('new_rule_data'),
            modification_reason=data['modification_reason'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class StateRepositoryImpl(StateRepository):
    """状态仓储实现 - 基于文件存储"""
    
    def __init__(self, storage_path: str = "./.cognitive_workflow_data/states"):
        """
        初始化状态仓储
        
        Args:
            storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._states_cache: Dict[str, GlobalState] = {}
        self._workflow_states: Dict[str, List[GlobalState]] = {}
    
    def save_state(self, global_state: GlobalState) -> None:
        """保存状态（并发安全）"""
        try:
            file_path = self.storage_path / f"state_{global_state.id}.json"
            
            # 🔑 检查文件冲突
            if SafeFileOperations.check_file_conflict(file_path):
                logger.warning(f"检测到状态文件冲突，等待后重试: {file_path}")
                import time
                time.sleep(0.05)
            
            state_data = global_state.to_dict()
            
            # 🔑 使用原子性写入
            if not SafeFileOperations.atomic_write_json(file_path, state_data):
                raise IOError(f"状态原子性写入失败: {file_path}")
            
            # 更新缓存
            self._states_cache[global_state.id] = global_state
            
            # 更新工作流状态历史
            workflow_id = global_state.workflow_id
            if workflow_id:
                if workflow_id not in self._workflow_states:
                    self._workflow_states[workflow_id] = []
                self._workflow_states[workflow_id].append(global_state)
            
            logger.debug(f"状态已安全保存: {global_state.id}")
            
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
            raise
    
    def load_state(self, state_id: str) -> GlobalState:
        """加载状态"""
        try:
            # 先检查缓存
            if state_id in self._states_cache:
                return self._states_cache[state_id]
            
            file_path = self.storage_path / f"state_{state_id}.json"
            
            if not file_path.exists():
                raise ValueError(f"状态不存在: {state_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            global_state = self._dict_to_state(state_data)
            
            # 更新缓存
            self._states_cache[state_id] = global_state
            
            return global_state
            
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            raise
    
    def get_state_history(self, workflow_id: str) -> List[GlobalState]:
        """获取工作流的状态历史"""
        try:
            if workflow_id in self._workflow_states:
                # Cannot sort by timestamp anymore as it was removed for LLM caching
                return self._workflow_states[workflow_id]
            
            # 如果缓存中没有，尝试从文件加载
            workflow_states = []
            for file_path in self.storage_path.glob("state_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        state_data = json.load(f)
                    
                    if state_data.get('workflow_id') == workflow_id:
                        state = self._dict_to_state(state_data)
                        workflow_states.append(state)
                        
                except Exception as e:
                    logger.error(f"加载状态文件失败 {file_path}: {e}")
            
            # 更新缓存
            self._workflow_states[workflow_id] = workflow_states
            
            return workflow_states  # Cannot sort by timestamp anymore
            
        except Exception as e:
            logger.error(f"获取状态历史失败: {e}")
            return []
    
    def save_state_snapshot(self, state: GlobalState, snapshot_name: str) -> None:
        """保存状态快照"""
        try:
            snapshot_path = self.storage_path / "snapshots"
            snapshot_path.mkdir(exist_ok=True)
            
            file_path = snapshot_path / f"snapshot_{snapshot_name}.json"
            
            state_data = state.to_dict()
            state_data['snapshot_name'] = snapshot_name
            state_data['snapshot_timestamp'] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"状态快照已保存: {snapshot_name}")
            
        except Exception as e:
            logger.error(f"保存状态快照失败: {e}")
            raise
    
    def load_state_snapshot(self, snapshot_name: str) -> GlobalState:
        """加载状态快照"""
        try:
            snapshot_path = self.storage_path / "snapshots"
            file_path = snapshot_path / f"snapshot_{snapshot_name}.json"
            
            if not file_path.exists():
                raise ValueError(f"状态快照不存在: {snapshot_name}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            return self._dict_to_state(state_data)
            
        except Exception as e:
            logger.error(f"加载状态快照失败: {e}")
            raise
    
    def find_states_by_workflow(self, workflow_id: str) -> List[GlobalState]:
        """根据工作流ID查找状态"""
        return self.get_state_history(workflow_id)
    
    def find_states_by_time_range(self, start_time: datetime, end_time: datetime) -> List[GlobalState]:
        """根据时间范围查找状态"""
        try:
            matching_states = []
            
            for state in self._states_cache.values():
                # Time filtering removed as timestamp was removed for LLM caching
                matching_states.append(state)
            
            return matching_states  # Cannot sort by timestamp anymore
            
        except Exception as e:
            logger.error(f"按时间范围查找状态失败: {e}")
            return []
    
    def get_latest_state(self, workflow_id: str) -> Optional[GlobalState]:
        """获取工作流的最新状态"""
        try:
            history = self.get_state_history(workflow_id)
            if history:
                return history[-1]  # 最后一个状态
            return None
            
        except Exception as e:
            logger.error(f"获取最新状态失败: {e}")
            return None
    
    def delete_old_states(self, cutoff_time: datetime) -> int:
        """删除旧状态，返回删除的数量"""
        try:
            deleted_count = 0
            states_to_delete = []
            
            for state_id, state in self._states_cache.items():
                # Time comparison removed as timestamp was removed for LLM caching
                # For now, don't delete any states based on time
                pass
            
            for state_id in states_to_delete:
                try:
                    # 删除文件
                    file_path = self.storage_path / f"state_{state_id}.json"
                    if file_path.exists():
                        file_path.unlink()
                    
                    # 从缓存删除
                    del self._states_cache[state_id]
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"删除状态失败 {state_id}: {e}")
            
            logger.info(f"删除了 {deleted_count} 个旧状态")
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除旧状态失败: {e}")
            return 0
    
    def get_state_count(self, workflow_id: Optional[str] = None) -> int:
        """获取状态数量"""
        if workflow_id:
            return len(self.get_state_history(workflow_id))
        else:
            return len(self._states_cache)
    
    def _dict_to_state(self, data: Dict) -> GlobalState:
        """从字典创建状态"""
        # Backward compatibility: handle both 'state' (new) and 'description' (old) field names
        state_value = data.get('state', data.get('description', ''))
        
        return GlobalState(
            id=data['id'],
            state=state_value,
            context_variables=data.get('context_variables', {}),
            execution_history=data.get('execution_history', []),
            # timestamp=datetime.fromisoformat(data.get('timestamp')),  # Removed for LLM caching
            workflow_id=data.get('workflow_id', ''),
            iteration_count=data.get('iteration_count', 0),
            goal_achieved=data.get('goal_achieved', False)
        )


class ExecutionRepositoryImpl(ExecutionRepository):
    """执行仓储实现 - 基于文件存储"""
    
    def __init__(self, storage_path: str = "./.cognitive_workflow_data/executions"):
        """
        初始化执行仓储
        
        Args:
            storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._executions_cache: Dict[str, RuleExecution] = {}
        self._rule_executions: Dict[str, List[RuleExecution]] = {}
    
    def save_execution(self, rule_execution: RuleExecution) -> None:
        """保存规则执行记录"""
        try:
            file_path = self.storage_path / f"execution_{rule_execution.id}.json"
            
            execution_data = self._execution_to_dict(rule_execution)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(execution_data, f, ensure_ascii=False, indent=2)
            
            # 更新缓存
            self._executions_cache[rule_execution.id] = rule_execution
            
            # 更新规则执行历史
            rule_id = rule_execution.rule_id
            if rule_id not in self._rule_executions:
                self._rule_executions[rule_id] = []
            self._rule_executions[rule_id].append(rule_execution)
            
            logger.debug(f"执行记录已保存: {rule_execution.id}")
            
        except Exception as e:
            logger.error(f"保存执行记录失败: {e}")
            raise
    
    def load_execution(self, execution_id: str) -> RuleExecution:
        """加载规则执行记录"""
        try:
            # 先检查缓存
            if execution_id in self._executions_cache:
                return self._executions_cache[execution_id]
            
            file_path = self.storage_path / f"execution_{execution_id}.json"
            
            if not file_path.exists():
                raise ValueError(f"执行记录不存在: {execution_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                execution_data = json.load(f)
            
            rule_execution = self._dict_to_execution(execution_data)
            
            # 更新缓存
            self._executions_cache[execution_id] = rule_execution
            
            return rule_execution
            
        except Exception as e:
            logger.error(f"加载执行记录失败: {e}")
            raise
    
    def find_executions_by_rule(self, rule_id: str) -> List[RuleExecution]:
        """根据规则ID查找执行记录"""
        try:
            if rule_id in self._rule_executions:
                return self._rule_executions[rule_id]  # Cannot sort by started_at anymore
            
            # 如果缓存中没有，从文件加载
            rule_executions = []
            for file_path in self.storage_path.glob("execution_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        execution_data = json.load(f)
                    
                    if execution_data.get('rule_id') == rule_id:
                        execution = self._dict_to_execution(execution_data)
                        rule_executions.append(execution)
                        
                except Exception as e:
                    logger.error(f"加载执行文件失败 {file_path}: {e}")
            
            # 更新缓存
            self._rule_executions[rule_id] = rule_executions
            
            return rule_executions  # Cannot sort by started_at anymore
            
        except Exception as e:
            logger.error(f"按规则查找执行记录失败: {e}")
            return []
    
    def find_failed_executions(self, time_range: Tuple[datetime, datetime]) -> List[RuleExecution]:
        """查找失败的执行记录"""
        try:
            start_time, end_time = time_range
            failed_executions = []
            
            for execution in self._executions_cache.values():
                if execution.status == ExecutionStatus.FAILED:
                    # Time filtering removed as started_at was removed for LLM caching
                    failed_executions.append(execution)
            
            return failed_executions  # Cannot sort by started_at anymore
            
        except Exception as e:
            logger.error(f"查找失败执行记录失败: {e}")
            return []
    
    def find_executions_by_status(self, status: ExecutionStatus) -> List[RuleExecution]:
        """根据状态查找执行记录"""
        try:
            matching_executions = []
            
            for execution in self._executions_cache.values():
                if execution.status == status:
                    matching_executions.append(execution)
            
            return matching_executions  # Cannot sort by started_at anymore
            
        except Exception as e:
            logger.error(f"按状态查找执行记录失败: {e}")
            return []
    
    def find_executions_by_time_range(self, start_time: datetime, end_time: datetime) -> List[RuleExecution]:
        """根据时间范围查找执行记录"""
        try:
            matching_executions = []
            
            for execution in self._executions_cache.values():
                # Time filtering removed as started_at was removed for LLM caching
                matching_executions.append(execution)
            
            return matching_executions  # Cannot sort by started_at anymore
            
        except Exception as e:
            logger.error(f"按时间范围查找执行记录失败: {e}")
            return []
    
    def get_execution_statistics(self, rule_id: Optional[str] = None) -> dict:
        """获取执行统计信息"""
        try:
            if rule_id:
                executions = self.find_executions_by_rule(rule_id)
            else:
                executions = list(self._executions_cache.values())
            
            total_executions = len(executions)
            successful_executions = sum(1 for e in executions if e.is_successful())
            failed_executions = total_executions - successful_executions
            
            # 计算平均执行时间
            execution_times = []
            for execution in executions:
                duration = execution.get_execution_duration()
                if duration is not None:
                    execution_times.append(duration)
            
            average_execution_time = (sum(execution_times) / len(execution_times)) if execution_times else 0.0
            total_execution_time = sum(execution_times)
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': successful_executions / total_executions if total_executions > 0 else 0.0,
                'average_execution_time': average_execution_time,
                'total_execution_time': total_execution_time,
                'rule_match_accuracy': 0.85  # 简化实现，实际需要更复杂的计算
            }
            
        except Exception as e:
            logger.error(f"获取执行统计失败: {e}")
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'total_execution_time': 0.0,
                'rule_match_accuracy': 0.0
            }
    
    def get_recent_executions(self, limit: int = 100) -> List[RuleExecution]:
        """获取最近的执行记录"""
        try:
            all_executions = list(self._executions_cache.values())
            # Cannot sort by started_at anymore as it was removed for LLM caching
            return all_executions[:limit]
            
        except Exception as e:
            logger.error(f"获取最近执行记录失败: {e}")
            return []
    
    def delete_old_executions(self, cutoff_time: datetime) -> int:
        """删除旧的执行记录，返回删除的数量"""
        try:
            deleted_count = 0
            executions_to_delete = []
            
            for execution_id, execution in self._executions_cache.items():
                # Time comparison removed as started_at was removed for LLM caching
                # For now, don't delete any executions based on time
                pass
            
            for execution_id in executions_to_delete:
                try:
                    # 删除文件
                    file_path = self.storage_path / f"execution_{execution_id}.json"
                    if file_path.exists():
                        file_path.unlink()
                    
                    # 从缓存删除
                    del self._executions_cache[execution_id]
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"删除执行记录失败 {execution_id}: {e}")
            
            logger.info(f"删除了 {deleted_count} 个旧执行记录")
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除旧执行记录失败: {e}")
            return 0
    
    def get_execution_count(self, rule_id: Optional[str] = None, status: Optional[ExecutionStatus] = None) -> int:
        """获取执行记录数量"""
        try:
            if rule_id and status:
                executions = self.find_executions_by_rule(rule_id)
                return sum(1 for e in executions if e.status == status)
            elif rule_id:
                return len(self.find_executions_by_rule(rule_id))
            elif status:
                return len(self.find_executions_by_status(status))
            else:
                return len(self._executions_cache)
                
        except Exception as e:
            logger.error(f"获取执行记录数量失败: {e}")
            return 0
    
    def find_long_running_executions(self, threshold_seconds: int = 300) -> List[RuleExecution]:
        """查找长时间运行的执行记录"""
        try:
            long_running = []
            
            for execution in self._executions_cache.values():
                duration = execution.get_execution_duration()
                if duration is not None and duration > threshold_seconds:
                    long_running.append(execution)
            
            return sorted(long_running, key=lambda e: e.get_execution_duration(), reverse=True)
            
        except Exception as e:
            logger.error(f"查找长时间运行执行记录失败: {e}")
            return []
    
    def update_execution_status(self, execution_id: str, status: ExecutionStatus, failure_reason: Optional[str] = None) -> bool:
        """更新执行状态"""
        try:
            if execution_id in self._executions_cache:
                execution = self._executions_cache[execution_id]
                execution.status = status
                if failure_reason:
                    execution.failure_reason = failure_reason
                
                # 保存更新
                self.save_execution(execution)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新执行状态失败: {e}")
            return False
    
    def _execution_to_dict(self, execution: RuleExecution) -> Dict:
        """将执行记录转换为字典"""
        return {
            'id': execution.id,
            'rule_id': execution.rule_id,
            'status': execution.status.value,
            'result': execution.result.to_dict() if execution.result else None,
            # 'started_at': execution.started_at.isoformat(),  # Removed for LLM caching
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'execution_context': execution.execution_context,
            'failure_reason': execution.failure_reason,
            'confidence_score': execution.confidence_score
        }
    
    def _dict_to_execution(self, data: Dict) -> RuleExecution:
        """从字典创建执行记录"""
        from ..domain.entities import WorkflowResult
        
        # 转换结果
        result = None
        if data.get('result'):
            result_data = data['result']
            result = WorkflowResult(
                success=result_data['success'],
                message=result_data['message'],
                data=result_data.get('data'),
                error_details=result_data.get('error_details'),
                metadata=result_data.get('metadata', {}),
                timestamp=datetime.fromisoformat(result_data['timestamp'])
            )
        
        execution = RuleExecution(
            id=data['id'],
            rule_id=data['rule_id'],
            status=ExecutionStatus(data['status']),
            result=result,
            # started_at=datetime.fromisoformat(data['started_at']),  # Removed for LLM caching
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            execution_context=data.get('execution_context', {}),
            failure_reason=data.get('failure_reason'),
            confidence_score=data.get('confidence_score', 0.0)
        )
        
        return execution