# -*- coding: utf-8 -*-
"""
规则引擎服务

核心规则引擎服务，作为整个产生式规则系统的协调者。
负责编排各个专门服务，管理完整的工作流程。
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid

from ..domain.entities import (
    ProductionRule, RuleSet, RuleExecution, GlobalState, DecisionResult
)
from ..domain.repositories import RuleRepository, StateRepository, ExecutionRepository
from ..domain.value_objects import (
    DecisionType, ExecutionStatus, WorkflowExecutionResult, ExecutionMetrics, RuleConstants
)
from .rule_generation_service import RuleGenerationService
from .rule_matching_service import RuleMatchingService
from .rule_execution_service import RuleExecutionService
from .state_service import StateService

logger = logging.getLogger(__name__)


class RuleEngineService:
    """核心规则引擎服务 - 整个产生式规则系统的协调者"""
    
    def __init__(self,
                 rule_repository: RuleRepository,
                 state_repository: StateRepository,
                 execution_repository: ExecutionRepository,
                 rule_matching: RuleMatchingService,
                 rule_execution: RuleExecutionService,
                 rule_generation: RuleGenerationService,
                 state_service: StateService,
                 enable_auto_recovery: bool = True,
                 max_iterations: int = RuleConstants.MAX_ITERATIONS):
        """
        初始化规则引擎服务
        
        Args:
            rule_repository: 规则仓储
            state_repository: 状态仓储
            execution_repository: 执行仓储
            rule_matching: 规则匹配服务
            rule_execution: 规则执行服务
            rule_generation: 规则生成服务
            state_service: 状态服务
            enable_auto_recovery: 是否启用自动恢复
            max_iterations: 最大迭代次数
        """
        self.rule_repository = rule_repository
        self.state_repository = state_repository
        self.execution_repository = execution_repository
        self.rule_matching = rule_matching
        self.rule_execution = rule_execution
        self.rule_generation = rule_generation
        self.state_service = state_service
        self.enable_auto_recovery = enable_auto_recovery
        self.max_iterations = max_iterations
        
        # 运行时状态
        self._current_rule_set: Optional[RuleSet] = None
        self._workflow_id: Optional[str] = None
        
    def execute_workflow(self, goal: str, agent_registry: Any) -> WorkflowExecutionResult:
        """
        执行完整的工作流程
        
        Args:
            goal: 工作流目标
            agent_registry: 智能体注册表
            
        Returns:
            WorkflowExecutionResult: 工作流执行结果
        """
        # 初始化工作流 - Use deterministic ID for better caching
        workflow_id = f"workflow_{goal.replace(' ', '_')[:20]}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        self._workflow_id = workflow_id
        
        start_time = datetime.now()
        logger.info(f"开始执行工作流: {goal} (ID: {workflow_id})")
        
        try:
            # 1. 生成初始规则集
            rule_set = self.rule_generation.generate_rule_set(goal, agent_registry)
            self._current_rule_set = rule_set
            self.rule_repository.save_rule_set(rule_set)
            
            # 2. 创建初始状态
            global_state = self.state_service.create_initial_state(goal, workflow_id)
            
            # 3. 执行主循环
            iteration_count = 0
            goal_achieved = False
            
            while iteration_count < self.max_iterations and not goal_achieved:
                iteration_count += 1
                logger.info(f"开始第 {iteration_count} 次迭代")
                
                # 选择要执行的规则
                decision = self.select_rule(global_state, rule_set)
                
                # 处理决策结果
                if decision.decision_type == DecisionType.EXECUTE_SELECTED_RULE:
                    # 执行选中的规则
                    rule_execution = self.rule_execution.execute_rule(
                        decision.selected_rule, global_state
                    )
                    
                    # 更新状态
                    global_state = self.state_service.update_state(
                        rule_execution.result, global_state
                    )
                    
                    # 检查是否需要错误恢复
                    if not rule_execution.is_successful() and self.enable_auto_recovery:
                        recovery_rules = self.handle_rule_failure(rule_execution, global_state)
                        if recovery_rules:
                            rule_set.rules.extend(recovery_rules)
                            self.rule_repository.save_rule_set(rule_set)
                
                elif decision.decision_type == DecisionType.ADD_RULE:
                    # 生成新规则
                    new_rules = self._generate_new_rules_for_situation(global_state, goal)
                    if new_rules:
                        rule_set.rules.extend(new_rules)
                        self.rule_repository.save_rule_set(rule_set)
                        logger.info(f"添加了 {len(new_rules)} 个新规则")
                
                elif decision.decision_type == DecisionType.GOAL_ACHIEVED:
                    goal_achieved = True
                    global_state.goal_achieved = True
                    self.state_service.save_state(global_state)
                    logger.info("目标已达成，工作流完成")
                    break
                    
                elif decision.decision_type == DecisionType.GOAL_FAILED:
                    logger.warning("目标执行失败，尝试策略调整")
                    strategy_rules = self.rule_generation.generate_strategy_adjustment_rules({
                        'goal': goal,
                        'current_state': global_state.description,
                        'execution_history': global_state.execution_history,
                        'iteration_count': iteration_count
                    })
                    if strategy_rules:
                        rule_set.rules.extend(strategy_rules)
                        self.rule_repository.save_rule_set(rule_set)
                
                # 定期检查目标达成
                if iteration_count % 5 == 0:
                    goal_achieved = self.evaluate_goal_achievement(global_state, goal)
                    if goal_achieved:
                        global_state.goal_achieved = True
                        self.state_service.save_state(global_state)
                        break
            
            # 4. 生成执行结果
            end_time = datetime.now()
            execution_metrics = self._calculate_execution_metrics(workflow_id)
            
            # 确定最终状态
            final_message = ""
            if goal_achieved:
                final_message = f"工作流成功完成，目标已达成"
            elif iteration_count >= self.max_iterations:
                final_message = f"达到最大迭代次数 ({self.max_iterations})，工作流终止"
            else:
                final_message = "工作流异常终止"
            
            workflow_result = WorkflowExecutionResult(
                goal=goal,
                is_successful=goal_achieved,
                final_state=global_state.description,
                total_iterations=iteration_count,
                execution_metrics=execution_metrics,
                final_message=final_message,
                completion_timestamp=end_time
            )
            
            logger.info(f"工作流执行完成: {final_message}")
            return workflow_result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            
            # 创建失败结果
            end_time = datetime.now()
            execution_metrics = ExecutionMetrics(
                total_rules_executed=0,
                successful_executions=0,
                failed_executions=1,
                average_execution_time=0.0,
                total_execution_time=(end_time - start_time).total_seconds(),
                rule_match_accuracy=0.0
            )
            
            return WorkflowExecutionResult(
                goal=goal,
                is_successful=False,
                final_state=f"工作流执行异常: {str(e)}",
                total_iterations=0,
                execution_metrics=execution_metrics,
                final_message=f"工作流执行失败: {str(e)}",
                completion_timestamp=end_time
            )
    
    def select_rule(self, 
                   global_state: GlobalState, 
                   rule_set: RuleSet) -> DecisionResult:
        """
        选择适合当前状态的规则
        
        Args:
            global_state: 当前全局状态
            rule_set: 规则集
            
        Returns:
            DecisionResult: 规则选择决策结果
        """
        try:
            logger.debug("开始规则选择过程")
            
            # 1. 查找适用的规则
            applicable_rules = self.rule_matching.find_applicable_rules(global_state, rule_set)
            
            # 2. 选择最佳规则
            decision = self.rule_matching.select_best_rule(applicable_rules, global_state)
            
            logger.debug(f"规则选择决策: {decision.decision_type.value}")
            return decision
            
        except Exception as e:
            logger.error(f"规则选择失败: {e}")
            return DecisionResult(
                selected_rule=None,
                decision_type=DecisionType.GOAL_FAILED,
                confidence=0.0,
                reasoning=f"规则选择失败: {str(e)}"
            )
    
    def handle_rule_failure(self, 
                          rule_execution: RuleExecution, 
                          global_state: GlobalState) -> List[ProductionRule]:
        """
        处理规则执行失败，生成恢复规则
        
        Args:
            rule_execution: 失败的规则执行
            global_state: 全局状态
            
        Returns:
            List[ProductionRule]: 恢复规则列表
        """
        try:
            logger.info(f"处理规则执行失败: {rule_execution.rule_id}")
            
            # 构建失败上下文
            failure_context = {
                'rule_id': rule_execution.rule_id,
                'failure_reason': rule_execution.failure_reason,
                'execution_context': rule_execution.execution_context,
                'global_state': global_state.description,
                'error_message': rule_execution.failure_reason or 'Unknown error'
            }
            
            # 生成恢复规则
            recovery_rules = self.rule_generation.generate_recovery_rules(failure_context)
            
            logger.info(f"生成了 {len(recovery_rules)} 个恢复规则")
            return recovery_rules
            
        except Exception as e:
            logger.error(f"规则失败处理异常: {e}")
            return []
    
    def evaluate_goal_achievement(self, global_state: GlobalState, goal: str) -> bool:
        """
        评估目标是否达成
        
        Args:
            global_state: 全局状态
            goal: 目标描述
            
        Returns:
            bool: 是否达成目标
        """
        try:
            return self.state_service.evaluate_goal_achievement(goal, global_state)
        except Exception as e:
            logger.error(f"目标达成评估失败: {e}")
            return False
    
    def manage_rule_lifecycle(self, rule_set: RuleSet) -> None:
        """
        管理规则生命周期
        
        Args:
            rule_set: 规则集
        """
        try:
            # 验证规则集
            issues = self.rule_generation.validate_rule_set(rule_set)
            if issues:
                logger.warning(f"规则集存在问题: {', '.join(issues[:3])}")
            
            # 优化规则优先级
            if len(rule_set.rules) > 5:
                optimized_rules = self.rule_generation.optimize_rule_priorities(rule_set.rules)
                rule_set.rules = optimized_rules
                self.rule_repository.save_rule_set(rule_set)
                logger.info("规则优先级已优化")
            
            # 清理过期或无效规则
            self._cleanup_invalid_rules(rule_set)
            
        except Exception as e:
            logger.error(f"规则生命周期管理失败: {e}")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        获取工作流状态
        
        Returns:
            Dict[str, Any]: 工作流状态信息
        """
        try:
            current_state = self.state_service.get_current_state()
            
            status = {
                'workflow_id': self._workflow_id,
                'current_state': current_state.description if current_state else 'No active workflow',
                'iteration_count': current_state.iteration_count if current_state else 0,
                'goal_achieved': current_state.goal_achieved if current_state else False,
                'rule_count': len(self._current_rule_set.rules) if self._current_rule_set else 0
                # 'timestamp': datetime.now().isoformat()  # Removed for LLM caching
            }
            
            return status
            
        except Exception as e:
            logger.error(f"获取工作流状态失败: {e}")
            return {
                'workflow_id': self._workflow_id,
                'current_state': 'Status unavailable',
                'error': str(e)
            }
    
    def pause_workflow(self) -> bool:
        """
        暂停工作流
        
        Returns:
            bool: 是否成功暂停
        """
        try:
            # 保存当前状态
            current_state = self.state_service.get_current_state()
            if current_state:
                current_state.context_variables['workflow_paused'] = True
                self.state_service.save_state(current_state)
            
            logger.info("工作流已暂停")
            return True
            
        except Exception as e:
            logger.error(f"暂停工作流失败: {e}")
            return False
    
    def resume_workflow(self) -> bool:
        """
        恢复工作流
        
        Returns:
            bool: 是否成功恢复
        """
        try:
            # 恢复状态
            current_state = self.state_service.get_current_state()
            if current_state:
                current_state.context_variables.pop('workflow_paused', None)
                self.state_service.save_state(current_state)
            
            logger.info("工作流已恢复")
            return True
            
        except Exception as e:
            logger.error(f"恢复工作流失败: {e}")
            return False
    
    def _generate_new_rules_for_situation(self, 
                                        global_state: GlobalState, 
                                        goal: str) -> List[ProductionRule]:
        """
        为当前情况生成新规则
        
        Args:
            global_state: 全局状态
            goal: 目标
            
        Returns:
            List[ProductionRule]: 新生成的规则列表
        """
        try:
            # 分析当前情况
            situation_context = {
                'goal': goal,
                'current_state': global_state.description,
                'iteration_count': global_state.iteration_count,
                'context_variables': global_state.context_variables,
                'recent_history': global_state.execution_history[-5:] if global_state.execution_history else []
            }
            
            # 判断需要什么类型的规则
            if global_state.iteration_count > 10:
                # 如果迭代次数较多，可能需要策略调整规则
                return self.rule_generation.generate_strategy_adjustment_rules(situation_context)
            else:
                # 否则生成技术修复规则
                return self.rule_generation.generate_recovery_rules(situation_context)
                
        except Exception as e:
            logger.error(f"新规则生成失败: {e}")
            return []
    
    def _calculate_execution_metrics(self, workflow_id: str) -> ExecutionMetrics:
        """
        计算执行指标
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            ExecutionMetrics: 执行指标
        """
        try:
            # 获取所有相关的执行记录
            stats = self.rule_execution.get_execution_statistics()
            
            return ExecutionMetrics(
                total_rules_executed=stats.get('total_executions', 0),
                successful_executions=stats.get('successful_executions', 0),
                failed_executions=stats.get('failed_executions', 0),
                average_execution_time=stats.get('average_execution_time', 0.0),
                total_execution_time=stats.get('total_execution_time', 0.0),
                rule_match_accuracy=stats.get('rule_match_accuracy', 0.0)
            )
            
        except Exception as e:
            logger.error(f"执行指标计算失败: {e}")
            return ExecutionMetrics(
                total_rules_executed=0,
                successful_executions=0,
                failed_executions=0,
                average_execution_time=0.0,
                total_execution_time=0.0,
                rule_match_accuracy=0.0
            )
    
    def _cleanup_invalid_rules(self, rule_set: RuleSet) -> None:
        """
        清理无效规则
        
        Args:
            rule_set: 规则集
        """
        try:
            original_count = len(rule_set.rules)
            
            # 移除空的或无效的规则
            valid_rules = []
            for rule in rule_set.rules:
                if (rule.condition and rule.condition.strip() and 
                    rule.action and rule.action.strip() and
                    rule.agent_capability_id and rule.agent_capability_id.strip()):
                    valid_rules.append(rule)
                else:
                    logger.warning(f"移除无效规则: {rule.id}")
            
            rule_set.rules = valid_rules
            
            removed_count = original_count - len(valid_rules)
            if removed_count > 0:
                logger.info(f"清理了 {removed_count} 个无效规则")
                self.rule_repository.save_rule_set(rule_set)
                
        except Exception as e:
            logger.error(f"规则清理失败: {e}")
    
    def get_rule_set(self) -> Optional[RuleSet]:
        """
        获取当前规则集
        
        Returns:
            Optional[RuleSet]: 当前规则集
        """
        return self._current_rule_set
    
    def add_rule_to_current_set(self, rule: ProductionRule) -> bool:
        """
        向当前规则集添加规则
        
        Args:
            rule: 要添加的规则
            
        Returns:
            bool: 是否成功添加
        """
        try:
            if self._current_rule_set:
                self._current_rule_set.add_rule(rule)
                self.rule_repository.save_rule_set(self._current_rule_set)
                logger.info(f"规则已添加: {rule.name}")
                return True
            else:
                logger.warning("没有活跃的规则集，无法添加规则")
                return False
                
        except Exception as e:
            logger.error(f"添加规则失败: {e}")
            return False