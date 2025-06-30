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
# from .rule_matching_service import RuleMatchingService  # Removed - functionality integrated into RuleEngineService
from .rule_execution_service import RuleExecutionService
from .state_service import StateService
from .adaptive_replacement_service import AdaptiveReplacementService
from ..utils.concurrent_safe_id_generator import id_generator

logger = logging.getLogger(__name__)


class RuleEngineService:
    """核心规则引擎服务 - 整个产生式规则系统的协调者"""
    
    def __init__(self,
                 rule_repository: RuleRepository,
                 state_repository: StateRepository,
                 execution_repository: ExecutionRepository,
                 rule_execution: RuleExecutionService,
                 rule_generation: RuleGenerationService,
                 state_service: StateService,
                 enable_auto_recovery: bool = True,
                 max_iterations: int = RuleConstants.MAX_ITERATIONS,
                 enable_adaptive_replacement: bool = True):
        """
        初始化规则引擎服务
        
        Args:
            rule_repository: 规则仓储
            state_repository: 状态仓储
            execution_repository: 执行仓储
            rule_execution: 规则执行服务
            rule_generation: 规则生成服务
            state_service: 状态服务
            enable_auto_recovery: 是否启用自动恢复
            max_iterations: 最大迭代次数
            enable_adaptive_replacement: 是否启用自适应规则替换
        """
        self.rule_repository = rule_repository
        self.state_repository = state_repository
        self.execution_repository = execution_repository
        self.rule_execution = rule_execution
        self.rule_generation = rule_generation
        self.state_service = state_service
        self.enable_auto_recovery = enable_auto_recovery
        self.max_iterations = max_iterations
        self.enable_adaptive_replacement = enable_adaptive_replacement
        
        # 初始化自适应替换服务
        if enable_adaptive_replacement:
            self.adaptive_replacement = AdaptiveReplacementService(
                llm_service=rule_generation.llm_service,
                enable_effectiveness_tracking=True  # 启用Phase 2增强功能
            )
        else:
            self.adaptive_replacement = None
        
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
        # 🔑 初始化工作流 - 使用并发安全的ID生成器
        workflow_id = id_generator.generate_workflow_id(goal)
        self._workflow_id = workflow_id
        logger.info(f"生成并发安全的工作流ID: {workflow_id}")
        self._current_agent_registry = agent_registry  # 设置当前智能体注册表供决策使用
        self.rule_generation._current_agent_registry = agent_registry  # 为RuleGenerationService设置智能体注册表
        
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
            
            # 循环检测机制
            decision_history = []  # 存储最近的决策历史
            MAX_LOOP_DETECTION = 5  # 检测循环的最大历史记录数
            
            while iteration_count < self.max_iterations and not goal_achieved:
                iteration_count += 1
                logger.info(f"开始第 {iteration_count} 次迭代")
                
                # 进行决策（选择规则、添加规则、或判断目标达成）
                decision = self.rule_generation.make_decision(global_state, rule_set)
                
                # 循环检测：记录决策历史
                decision_signature = f"{decision.decision_type.value}_{getattr(decision, 'selected_rule', None) and decision.selected_rule.id}_{global_state.state[:50]}"
                decision_history.append(decision_signature)
                
                # 保持历史记录在合理范围内
                if len(decision_history) > MAX_LOOP_DETECTION:
                    decision_history.pop(0)
                
                # 检测循环：如果最近的决策重复出现，可能陷入循环
                if len(decision_history) >= 3:
                    recent_decisions = decision_history[-3:]
                    if len(set(recent_decisions)) == 1:  # 最近3次决策完全相同
                        logger.warning(f"检测到决策循环: {recent_decisions[0]}")
                        logger.warning("强制终止循环，标记目标失败")
                        break
                
                # 处理决策结果
                if decision.decision_type == DecisionType.EXECUTE_SELECTED_RULE:
                    # 执行选中的规则
                    rule_execution = self.rule_execution.execute_rule(
                        decision.selected_rule, global_state
                    )
                    
                    # 更新状态（包含目标达成检查和规则集上下文）
                    global_state = self.state_service.update_state(
                        rule_execution.result, global_state, goal, rule_set
                    )
                    
                    # 检查是否需要错误恢复
                    if not rule_execution.is_successful() and self.enable_auto_recovery:
                        recovery_rules = self.handle_rule_failure(rule_execution, global_state)
                        if recovery_rules:
                            # 使用自适应替换代替简单extend
                            optimized_rules = self._apply_adaptive_replacement(
                                rule_set.rules, recovery_rules, global_state, {
                                    'goal': goal,
                                    'iteration_count': iteration_count,
                                    'context_type': 'error_recovery',
                                    'failed_rule_id': rule_execution.rule_id
                                }
                            )
                            rule_set.rules = optimized_rules
                            self.rule_repository.save_rule_set(rule_set)
                            logger.info(f"错误恢复完成: 规则数量 {len(rule_set.rules)}")
                
                elif decision.decision_type == DecisionType.ADD_RULE:
                    # 使用决策中生成的新规则
                    if decision.new_rules:
                        # 使用自适应替换代替简单extend
                        optimized_rules = self._apply_adaptive_replacement(
                            rule_set.rules, decision.new_rules, global_state, {
                                'goal': goal,
                                'iteration_count': iteration_count,
                                'context_type': 'add_new_rules'
                            }
                        )
                        rule_set.rules = optimized_rules
                        self.rule_repository.save_rule_set(rule_set)
                        logger.info(f"智能添加规则完成: 规则数量 {len(rule_set.rules)}")
                    else:
                        logger.warning("ADD_RULE 决策中没有新规则")
                
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
                        'current_state': global_state.state,
                        'execution_history': global_state.execution_history,
                        'iteration_count': iteration_count
                    })
                    if strategy_rules:
                        # 使用自适应替换代替简单extend
                        optimized_rules = self._apply_adaptive_replacement(
                            rule_set.rules, strategy_rules, global_state, {
                                'goal': goal,
                                'iteration_count': iteration_count,
                                'context_type': 'strategy_adjustment'
                            }
                        )
                        rule_set.rules = optimized_rules
                        self.rule_repository.save_rule_set(rule_set)
                        logger.info(f"策略调整完成: 规则数量 {len(rule_set.rules)}")
                
                # 检查全局状态中的目标达成状态（每次规则执行后状态更新时已包含目标验证）
                if global_state.goal_achieved:
                    goal_achieved = True
                    logger.info("目标已达成（从全局状态中检测到）")
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
                final_state=global_state.state,
                total_iterations=iteration_count,
                execution_metrics=execution_metrics,
                final_message=final_message,
                completion_timestamp=end_time
            )
            
            logger.info(f"工作流执行完成: {final_message}")
            
            # 🔑 释放工作流ID（并发安全）
            try:
                id_generator.release_workflow_id(workflow_id)
                logger.debug(f"已释放工作流ID: {workflow_id}")
            except Exception as e:
                logger.warning(f"释放工作流ID失败: {e}")
            
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
                'global_state': global_state.state,
                'error_message': rule_execution.failure_reason or 'Unknown error'
            }
            
            # 生成恢复规则
            recovery_rules = self.rule_generation.generate_recovery_rules(failure_context)
            
            logger.info(f"生成了 {len(recovery_rules)} 个恢复规则")
            return recovery_rules
            
        except Exception as e:
            logger.error(f"规则失败处理异常: {e}")
            return []
    
    # evaluate_goal_achievement方法已移除 - 直接使用global_state.goal_achieved字段
    # 理由：每次规则执行后状态更新已包含目标验证，无需额外检查
    
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
                'current_state': current_state.state if current_state else 'No active workflow',
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
                'current_state': global_state.state,
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
                    rule.agent_name and rule.agent_name.strip()):
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
    
    
    def _should_generate_new_rule(self, global_state: GlobalState, rule_set: RuleSet) -> bool:
        """
        判断是否应该生成新规则
        
        Args:
            global_state: 当前全局状态
            rule_set: 规则集
            
        Returns:
            bool: 是否应该生成新规则
        """
        try:
            # 检查是否已经尝试生成过太多次新规则
            generation_count = global_state.context_variables.get('new_rule_generation_count', 0)
            if generation_count >= 3:  # 最多生成3次新规则
                logger.warning("已达到新规则生成次数上限")
                return False
            
            # 检查是否有合适的智能体能力来处理当前情况
            current_situation = f"{global_state.state} | 目标: {rule_set.goal}"
            
            # 使用语言模型判断是否需要新规则
            prompt = f"""
请判断当前情况是否需要生成新的产生式规则：

当前状态: {global_state.state}
目标: {rule_set.goal}
现有规则数量: {len(rule_set.rules)}
执行历史: {chr(10).join(global_state.execution_history[-3:]) if global_state.execution_history else '无'}

分析要点：
1. 现有规则是否能覆盖当前情况
2. 是否遇到了新的问题需要解决
3. 是否需要新的执行策略

如果确实需要新规则来推进目标完成，返回"是"，否则返回"否"。
"""
            
            response = self.rule_generation.llm_service.generate_natural_language_response(prompt)
            should_generate = "是" in response.strip()
            
            if should_generate:
                # 更新生成计数
                global_state.context_variables['new_rule_generation_count'] = generation_count + 1
                logger.info("判断需要生成新规则")
            
            return should_generate
            
        except Exception as e:
            logger.error(f"新规则生成判断失败: {e}")
            return False
    
    # 决策相关方法已迁移到RuleGenerationService
    
    # 决策相关方法已迁移到RuleGenerationService 
    # - _format_rules_for_decision
    # - _get_available_capabilities  
    # - _parse_llm_decision
    # - _create_rule_from_llm_data
    # - _print_decision_in_red
    
    def _apply_adaptive_replacement(self,
                                  existing_rules: List[ProductionRule],
                                  new_rules: List[ProductionRule],
                                  global_state: GlobalState,
                                  context: Dict[str, Any]) -> List[ProductionRule]:
        """
        应用自适应规则替换策略
        
        Args:
            existing_rules: 现有规则列表
            new_rules: 新规则列表
            global_state: 当前全局状态
            context: 执行上下文
            
        Returns:
            List[ProductionRule]: 优化后的规则列表
        """
        try:
            # 如果未启用自适应替换，使用保守合并
            if not self.enable_adaptive_replacement or not self.adaptive_replacement:
                logger.debug("自适应替换未启用，使用保守合并")
                return self._conservative_rule_merge(existing_rules, new_rules)
            
            # 使用自适应替换服务进行智能替换
            logger.info(f"应用自适应替换: {context.get('context_type', 'unknown')} - "
                       f"现有规则{len(existing_rules)}个, 新规则{len(new_rules)}个")
            
            optimized_rules = self.adaptive_replacement.execute_adaptive_replacement(
                existing_rules=existing_rules,
                new_rules=new_rules,
                global_state=global_state,
                context=context
            )
            
            logger.info(f"自适应替换完成: {len(existing_rules)} -> {len(optimized_rules)} 个规则")
            return optimized_rules
            
        except Exception as e:
            logger.error(f"自适应替换失败: {e}，使用保守合并")
            return self._conservative_rule_merge(existing_rules, new_rules)
    
    def _conservative_rule_merge(self, 
                               existing_rules: List[ProductionRule],
                               new_rules: List[ProductionRule]) -> List[ProductionRule]:
        """
        保守的规则合并策略（自适应替换失败时的后备方案）
        
        Args:
            existing_rules: 现有规则
            new_rules: 新规则
            
        Returns:
            List[ProductionRule]: 合并后的规则列表
        """
        # 简单合并，避免重复ID
        all_rules = existing_rules + new_rules
        seen_ids = set()
        unique_rules = []
        
        for rule in all_rules:
            if rule.id not in seen_ids:
                unique_rules.append(rule)
                seen_ids.add(rule.id)
        
        # 应用基本的数量限制
        max_total_rules = 15  # 硬性限制避免规则过多
        if len(unique_rules) > max_total_rules:
            # 按优先级排序，保留最高优先级的规则
            unique_rules.sort(key=lambda r: r.priority, reverse=True)
            unique_rules = unique_rules[:max_total_rules]
            logger.warning(f"规则数量超限，保留前{max_total_rules}个高优先级规则")
        
        return unique_rules