# -*- coding: utf-8 -*-
"""
规则执行服务

专注于规则执行和结果管理，负责将自然语言规则转换为具体的执行动作，
并管理执行结果的标准化和错误处理。
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid

from ...domain.entities import ProductionRule, RuleExecution, GlobalState, WorkflowResult
from ...domain.repositories import ExecutionRepository
from ...domain.value_objects import ExecutionStatus, ExecutionConstants
from .agent_service import AgentService
from .language_model_service import LanguageModelService

logger = logging.getLogger(__name__)


class RuleExecutionService:
    """规则执行服务 - 专注于规则执行和结果管理"""
    
    def __init__(self, 
                 agent_service: AgentService,
                 execution_repository: ExecutionRepository,
                 llm_service: LanguageModelService):
        """
        初始化规则执行服务
        
        Args:
            agent_service: 智能体服务
            execution_repository: 执行仓储
            llm_service: 语言模型服务
        """
        self.agent_service = agent_service
        self.execution_repository = execution_repository
        self.llm_service = llm_service
        
    def execute_rule(self, 
                    rule: ProductionRule, 
                    global_state: GlobalState) -> RuleExecution:
        """
        执行单个规则
        
        Args:
            rule: 要执行的规则
            global_state: 全局状态
            
        Returns:
            RuleExecution: 执行结果
        """
        # 创建执行记录
        rule_execution = RuleExecution(
            id=f"{rule.id}_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # Use deterministic ID
            rule_id=rule.id,
            status=ExecutionStatus.RUNNING
            # started_at=datetime.now()  # Removed for LLM caching
        )
        
        try:
            logger.info(f"开始执行规则: {rule.name}")
            
            # 准备执行上下文
            execution_context = self.prepare_execution_context(rule, global_state)
            rule_execution.execution_context = execution_context
            
            # 保存初始执行记录
            self.execution_repository.save_execution(rule_execution)
            
            # 执行自然语言动作
            result = self._execute_natural_language_action(
                rule.action, 
                rule.agent_name, 
                execution_context
            )
            
            # 验证执行结果
            is_valid = self.validate_execution_result(rule, result)
            if not is_valid:
                logger.warning(f"规则执行结果验证失败: {rule.name}")
                result.success = False
                result.error_details = "执行结果验证失败"
            
            # 计算置信度分数
            confidence_score = self._calculate_confidence_score(rule, result, global_state)
            rule_execution.confidence_score = confidence_score
            
            # 标记执行完成
            rule_execution.mark_completed(result)
            
            logger.info(f"规则执行完成: {rule.name} -> {'成功' if result.success else '失败'}")
            
        except Exception as e:
            error_message = f"规则执行异常: {str(e)}"
            logger.error(error_message)
            
            # 处理执行失败
            rule_execution = self.handle_execution_failure(rule, e)
            
        finally:
            # 保存最终执行记录
            self.execution_repository.save_execution(rule_execution)
        
        return rule_execution
    
    def prepare_execution_context(self, 
                                rule: ProductionRule, 
                                global_state: GlobalState) -> Dict[str, Any]:
        """
        准备执行上下文
        
        Args:
            rule: 要执行的规则
            global_state: 全局状态
            
        Returns:
            Dict[str, Any]: 执行上下文
        """
        execution_context = {
            # 规则信息
            'rule_info': {
                'id': rule.id,
                'name': rule.name,
                'condition': rule.condition,
                'action': rule.action,
                'expected_outcome': rule.expected_outcome,
                'priority': rule.priority,
                'phase': rule.phase.value
            },
            
            # 状态信息
            'state_info': {
                'description': global_state.state,
                'iteration_count': global_state.iteration_count,
                'workflow_id': global_state.workflow_id,
                'goal_achieved': global_state.goal_achieved
            },
            
            # 上下文变量
            'context_variables': global_state.context_variables.copy(),
            
            # 执行历史（最近5条）
            'recent_history': global_state.execution_history[-5:] if global_state.execution_history else [],
            
            # 执行配置
            'execution_config': {
                'timeout': ExecutionConstants.DEFAULT_EXECUTION_TIMEOUT,
                'retry_attempts': ExecutionConstants.MAX_RETRY_ATTEMPTS,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return execution_context
    
    def handle_execution_failure(self, 
                                rule: ProductionRule, 
                                error: Exception) -> RuleExecution:
        """
        处理执行失败
        
        Args:
            rule: 失败的规则
            error: 异常信息
            
        Returns:
            RuleExecution: 失败的执行记录
        """
        error_message = f"规则执行失败: {str(error)}"
        
        rule_execution = RuleExecution(
            id=f"{rule.id}_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # Use deterministic ID
            rule_id=rule.id,
            status=ExecutionStatus.FAILED,
            # started_at=datetime.now(),  # Removed for LLM caching
            completed_at=datetime.now(),  # Keep this as it's set during execution, not initialization
            failure_reason=error_message,
            confidence_score=0.0
        )
        
        # 创建失败结果
        failure_result = WorkflowResult(
            success=False,
            message=error_message,
            error_details=str(error),
            metadata={
                'rule_id': rule.id,
                'rule_name': rule.name,
                'error_type': type(error).__name__
            }
        )
        
        rule_execution.result = failure_result
        
        logger.error(f"规则执行失败: {rule.name} - {error_message}")
        
        return rule_execution
    
    def validate_execution_result(self, 
                                rule: ProductionRule, 
                                result: WorkflowResult) -> bool:
        """
        验证执行结果
        
        Args:
            rule: 执行的规则
            result: 执行结果
            
        Returns:
            bool: 是否有效
        """
        try:
            # 基本验证：结果不能为空
            if result is None:
                return False
            
            # 如果执行失败，直接返回False
            if not result.success:
                return True  # 失败也是有效的结果，只是不成功
            
            # 检查结果消息
            if not result.message or not result.message.strip():
                logger.warning(f"规则 {rule.name} 执行结果消息为空")
                return False
            
            # 如果有期望结果，进行语义验证
            if rule.expected_outcome and rule.expected_outcome.strip():
                return self._validate_natural_language_result(
                    rule.action, result, rule.expected_outcome
                )
            
            return True
            
        except Exception as e:
            logger.error(f"结果验证失败: {e}")
            return False
    
    def _execute_natural_language_action(self, 
                                       action: str, 
                                       agent_name: str, 
                                       context: Dict[str, Any]) -> WorkflowResult:
        """
        执行自然语言动作指令
        
        Args:
            action: 自然语言动作描述
            agent_name: 智能体名称
            context: 执行上下文
            
        Returns:
            WorkflowResult: 执行结果
        """
        try:
            # 准备完整的自然语言指令
            enhanced_instruction = self._prepare_natural_language_instruction(action, context)
            
            # 通过智能体服务执行指令
            result = self.agent_service.execute_natural_language_instruction(
                enhanced_instruction, 
                agent_name, 
                context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"自然语言动作执行失败: {e}")
            return WorkflowResult(
                success=False,
                message=f"动作执行失败: {str(e)}",
                error_details=str(e),
                metadata={'action': action, 'agent_name': agent_name}
            )
    
    def _prepare_natural_language_instruction(self, 
                                            action: str, 
                                            context: Dict[str, Any]) -> str:
        """
        准备自然语言指令
        
        Args:
            action: 原始动作描述
            context: 执行上下文
            
        Returns:
            str: 增强后的自然语言指令
        """
        try:
            # 提取关键上下文信息
            state_desc = context.get('state_info', {}).get('description', '')
            rule_info = context.get('rule_info', {})
            context_vars = context.get('context_variables', {})
            
            # 构建增强指令
            enhanced_instruction = f"""
执行任务: {action}

当前状态: {state_desc}

规则上下文:
- 规则名称: {rule_info.get('name', '')}
- 期望结果: {rule_info.get('expected_outcome', '')}
- 执行阶段: {rule_info.get('phase', '')}

相关上下文变量:
"""
            
            # 添加重要的上下文变量
            important_vars = ['goal', 'current_phase', 'last_execution_success', 'error_count']
            for var in important_vars:
                if var in context_vars:
                    enhanced_instruction += f"- {var}: {context_vars[var]}\n"
            
            # 添加执行历史（如果有）
            recent_history = context.get('recent_history', [])
            if recent_history:
                enhanced_instruction += f"\n最近执行历史:\n"
                for i, history_entry in enumerate(recent_history[-3:], 1):  # 最多3条
                    enhanced_instruction += f"{i}. {history_entry}\n"
            
            enhanced_instruction += f"\n请根据以上信息执行任务: {action}"
            
            return enhanced_instruction
            
        except Exception as e:
            logger.error(f"指令准备失败: {e}")
            return action  # 回退到原始动作
    
    def _validate_natural_language_result(self, 
                                        action: str, 
                                        result: WorkflowResult, 
                                        expected_outcome: str) -> bool:
        """
        验证自然语言执行结果（使用语言模型进行智能验证）
        
        Args:
            action: 执行的动作
            result: 执行结果
            expected_outcome: 期望结果
            
        Returns:
            bool: 是否符合期望
        """
        try:
            # 使用语言模型进行智能验证
            is_valid, confidence, reasoning = self.llm_service.validate_execution_result(
                action=action,
                actual_result=result.message,
                expected_outcome=expected_outcome
            )
            
            logger.debug(f"LLM验证结果: {is_valid}, 置信度: {confidence:.2f}, 原因: {reasoning}")
            
            # 只有在高置信度的情况下才接受验证结果
            if confidence >= 0.7:
                return is_valid
            else:
                # 置信度低时，使用简单的关键词匹配作为备用验证
                logger.warning(f"LLM验证置信度较低({confidence:.2f})，使用关键词匹配作为备用验证")
                return self._fallback_keyword_validation(result.message, expected_outcome)
            
        except Exception as e:
            logger.error(f"LLM验证失败: {e}，使用关键词匹配作为备用验证")
            # LLM验证失败时，回退到关键词匹配
            return self._fallback_keyword_validation(result.message, expected_outcome)
    
    def _fallback_keyword_validation(self, result_text: str, expected_outcome: str) -> bool:
        """
        备用的关键词匹配验证方法
        
        Args:
            result_text: 结果文本
            expected_outcome: 期望结果
            
        Returns:
            bool: 是否匹配
        """
        try:
            result_text_lower = result_text.lower()
            expected_keywords = expected_outcome.lower().split()
            
            # 检查是否包含期望的关键词
            matching_keywords = sum(1 for keyword in expected_keywords 
                                  if keyword in result_text_lower and len(keyword) > 2)
            
            # 如果匹配的关键词超过期望关键词的30%，认为是有效的
            if len(expected_keywords) > 0:
                match_ratio = matching_keywords / len(expected_keywords)
                return match_ratio >= 0.3
            
            return True  # 如果没有期望结果，认为是有效的
            
        except Exception as e:
            logger.error(f"关键词匹配验证失败: {e}")
            return True  # 验证失败时默认为有效
    
    def _calculate_confidence_score(self, 
                                  rule: ProductionRule, 
                                  result: WorkflowResult, 
                                  global_state: GlobalState) -> float:
        """
        计算执行置信度分数
        
        Args:
            rule: 执行的规则
            result: 执行结果
            global_state: 全局状态
            
        Returns:
            float: 置信度分数（0.0-1.0）
        """
        try:
            base_score = 0.5
            
            # 成功执行基础分
            if result.success:
                base_score = 0.7
            else:
                base_score = 0.2
            
            # 消息质量评估
            if result.message and len(result.message.strip()) > 0:
                base_score += 0.1
                
                # 消息长度适中
                if 10 <= len(result.message) <= 500:
                    base_score += 0.1
            
            # 数据完整性
            if result.data is not None:
                base_score += 0.1
            
            # 期望结果匹配度
            if rule.expected_outcome:
                is_valid = self._validate_natural_language_result(
                    rule.action, result, rule.expected_outcome
                )
                if is_valid:
                    base_score += 0.1
            
            # 上下文一致性
            if self._check_context_consistency(result, global_state):
                base_score += 0.05
            
            return min(1.0, base_score)
            
        except Exception as e:
            logger.error(f"置信度分数计算失败: {e}")
            return 0.5
    
    def _check_context_consistency(self, result: WorkflowResult, global_state: GlobalState) -> bool:
        """
        检查上下文一致性
        
        Args:
            result: 执行结果
            global_state: 全局状态
            
        Returns:
            bool: 是否一致
        """
        try:
            # 检查结果元数据是否与状态变量一致
            if result.metadata:
                for key, value in result.metadata.items():
                    if key.startswith('context_'):
                        context_key = key[8:]  # 移除 'context_' 前缀
                        state_value = global_state.context_variables.get(context_key)
                        if state_value is not None and str(value) != str(state_value):
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"上下文一致性检查失败: {e}")
            return True
    
    def get_execution_statistics(self, rule_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取执行统计信息
        
        Args:
            rule_id: 可选的规则ID，如果提供则返回特定规则的统计
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            return self.execution_repository.get_execution_statistics(rule_id)
        except Exception as e:
            logger.error(f"获取执行统计失败: {e}")
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0
            }
    
    def get_recent_executions(self, limit: int = 10) -> List[RuleExecution]:
        """
        获取最近的执行记录
        
        Args:
            limit: 返回的记录数量限制
            
        Returns:
            List[RuleExecution]: 最近的执行记录
        """
        try:
            return self.execution_repository.get_recent_executions(limit)
        except Exception as e:
            logger.error(f"获取最近执行记录失败: {e}")
            return []
    
    def retry_failed_execution(self, execution_id: str) -> Optional[RuleExecution]:
        """
        重试失败的执行
        
        Args:
            execution_id: 失败的执行ID
            
        Returns:
            Optional[RuleExecution]: 重试的执行结果，如果重试失败则返回None
        """
        try:
            # 加载原执行记录
            original_execution = self.execution_repository.load_execution(execution_id)
            
            if original_execution.status != ExecutionStatus.FAILED:
                logger.warning(f"执行 {execution_id} 状态不是失败，无法重试")
                return None
            
            # 这里需要重新构建规则和状态信息
            # 实际实现中可能需要额外的参数或从其他地方获取这些信息
            logger.info(f"重试功能需要额外的规则和状态信息: {execution_id}")
            
            # 当前简化实现，返回None表示需要外部提供更多信息
            return None
            
        except Exception as e:
            logger.error(f"重试执行失败: {e}")
            return None