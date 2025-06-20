"""
静态工作流执行引擎模块
==================

实现基于预定义规则的确定性工作流执行引擎。
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

try:
    # 尝试相对导入（当作为包使用时）
    from .workflow_definitions import (
        WorkflowDefinition, WorkflowStep, ControlFlow, ControlFlowType, 
        StepExecutionStatus, ControlRule, StepExecution, WorkflowExecutionContext
    )
    from .control_flow_evaluator import ControlFlowEvaluator
    from .global_state_updater import GlobalStateUpdater
except ImportError:
    # 回退到绝对导入（当直接运行时）
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from workflow_definitions import (
        WorkflowDefinition, WorkflowStep, ControlFlow, ControlFlowType, 
        StepExecutionStatus, ControlRule, StepExecution, WorkflowExecutionContext
    )
    from control_flow_evaluator import ControlFlowEvaluator
    from global_state_updater import GlobalStateUpdater

logger = logging.getLogger(__name__)


@dataclass
class WorkflowExecutionResult:
    """工作流执行结果"""
    success: bool
    workflow_name: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    execution_time: float
    start_time: datetime
    end_time: datetime
    final_result: Any = None
    error_message: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)


# WorkflowState 类已被移除，由 WorkflowExecutionContext 替代


class ParallelExecutor:
    """并行步骤执行器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def execute_parallel_steps(self, 
                             steps: List[WorkflowStep],
                             step_executor: Callable,
                             join_condition: str = "all_complete") -> Dict[str, Any]:
        """执行并行步骤"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有并行任务
            future_to_step = {
                executor.submit(step_executor, step): step 
                for step in steps
            }
            
            # 根据合并条件处理结果
            if join_condition == "any_complete":
                # 任意一个完成即可
                for future in as_completed(future_to_step):
                    step = future_to_step[future]
                    try:
                        result = future.result()
                        results[step.id] = result
                        # 取消其他任务
                        for f in future_to_step:
                            if f != future:
                                f.cancel()
                        break
                    except Exception as e:
                        logger.error(f"并行步骤 {step.id} 执行失败: {e}")
                        results[step.id] = None
            
            else:  # all_complete（默认）
                # 等待所有任务完成
                for future in as_completed(future_to_step):
                    step = future_to_step[future]
                    try:
                        result = future.result()
                        results[step.id] = result
                    except Exception as e:
                        logger.error(f"并行步骤 {step.id} 执行失败: {e}")
                        results[step.id] = None
        
        return results


class StaticWorkflowEngine:
    """静态工作流执行引擎"""
    
    def __init__(self, max_parallel_workers: int = 4, ai_evaluator=None, llm=None, enable_state_updates: bool = True):
        self.evaluator = ControlFlowEvaluator(ai_evaluator=ai_evaluator, llm=llm)
        self.parallel_executor = ParallelExecutor(max_parallel_workers)
        self.step_executor = None  # 将由MultiStepAgent_v3设置
        
        # 状态更新器
        self.state_updater = GlobalStateUpdater(llm=llm, enable_updates=enable_state_updates)
        
        # 执行状态
        self.workflow_definition = None
        self.execution_context = None
        self.execution_start_time = None
        
        # 回调函数
        self.on_step_start = None
        self.on_step_complete = None
        self.on_step_failed = None
        self.on_workflow_complete = None
    
    def set_step_executor(self, executor: Callable[[WorkflowStep], Any]) -> None:
        """设置步骤执行器"""
        self.step_executor = executor
    
    def execute_workflow(self, 
                        workflow_definition: WorkflowDefinition,
                        initial_variables: Dict[str, Any] = None) -> WorkflowExecutionResult:
        """执行完整工作流"""
        
        self.workflow_definition = workflow_definition
        import uuid
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.execution_context = WorkflowExecutionContext(workflow_id=workflow_id)
        self.execution_start_time = datetime.now()
        
        logger.info(f"开始执行工作流: {workflow_definition.workflow_metadata.name}")
        
        try:
            # 初始化上下文变量
            if initial_variables:
                self.execution_context.runtime_variables.update(initial_variables)
            
            # 设置评估器上下文
            self._update_evaluator_context()
            
            # 查找入口步骤（第一个步骤）
            if not workflow_definition.steps:
                raise ValueError("工作流没有定义任何步骤")
            
            current_step_id = workflow_definition.steps[0].id
            
            # 主执行循环
            while current_step_id:
                current_step_id = self._execute_workflow_iteration(current_step_id)
            
            # 生成执行结果
            return self._generate_execution_result(True)
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            return self._generate_execution_result(False, str(e))
    
    def _execute_workflow_iteration(self, step_id: str) -> Optional[str]:
        """执行一个工作流迭代（简化版，基于执行上下文）"""
        
        step = self.workflow_definition.get_step_by_id(step_id)
        if not step:
            logger.error(f"找不到步骤: {step_id}")
            return None
        
        # 检查全局控制规则
        if self._check_global_control_rules():
            return None
        
        # 使用新的执行模型：总是尝试执行步骤，让控制流决定是否需要重新执行
        if step.control_flow and step.control_flow.type == ControlFlowType.PARALLEL:
            return self._handle_parallel_execution(step)
        else:
            return self._execute_single_step(step)
    
    def _execute_single_step(self, step: WorkflowStep) -> Optional[str]:
        """执行单个步骤（基于执行实例）"""
        
        # 创建新的执行实例
        execution = self.execution_context.create_execution(step.id)
        
        logger.info(f"执行步骤: {step.name} ({step.id}) - 第{execution.iteration}次迭代")
        
        # 更新执行状态
        execution.status = StepExecutionStatus.RUNNING
        execution.start_time = datetime.now()
        
        # 回调通知
        if self.on_step_start:
            self.on_step_start(step)
        
        try:
            # 检查超时
            if step.timeout and self._check_step_timeout(execution):
                raise TimeoutError(f"步骤 {step.id} 执行超时")
            
            # 执行步骤
            if not self.step_executor:
                raise ValueError("未设置步骤执行器")
            
            result = self.step_executor(step)
            
            # 更新执行结果
            execution.result = result
            execution.status = StepExecutionStatus.COMPLETED
            execution.end_time = datetime.now()
            
            # 更新运行时变量
            self._update_runtime_variables_from_result(step.id, result)
            
            # 回调通知
            if self.on_step_complete:
                self.on_step_complete(step, result)
            
            # 更新全局状态
            self._update_global_state(step, execution)
            
            logger.info(f"步骤完成: {step.name} (用时: {execution.duration:.2f}s)")
            
            # 确定下一步（基于执行成功）
            return self._get_next_step_id(step, execution, True)
            
        except Exception as e:
            # 处理步骤失败
            return self._handle_step_failure(step, execution, e)
    
    def _handle_step_failure(self, step: WorkflowStep, execution: StepExecution, error: Exception) -> Optional[str]:
        """处理步骤失败（基于执行实例）"""
        
        logger.error(f"步骤失败: {step.name}, 错误: {error}")
        
        # 更新执行实例状态
        execution.status = StepExecutionStatus.FAILED
        execution.end_time = datetime.now()
        execution.error_message = str(error)
        
        # 检查是否需要重试
        if execution.retry_count < step.max_retries:
            # 创建重试执行实例
            retry_execution = self.execution_context.create_execution(step.id)
            retry_execution.retry_count = execution.retry_count + 1
            
            logger.info(f"重试步骤: {step.name} (第{retry_execution.retry_count}次)")
            
            return step.id  # 重新执行当前步骤
        
        # 回调通知
        if self.on_step_failed:
            self.on_step_failed(step, error)
        
        # 确定失败后的下一步
        return self._get_next_step_id(step, execution, False)
    
    def _handle_parallel_execution(self, step: WorkflowStep) -> Optional[str]:
        """处理并行执行"""
        
        control_flow = step.control_flow
        if not control_flow.parallel_steps:
            logger.warning(f"并行步骤 {step.id} 没有定义parallel_steps")
            # 创建执行实例用于获取下一步
            execution = self.execution_context.create_execution(step.id)
            execution.status = StepExecutionStatus.COMPLETED
            return self._get_next_step_id(step, execution, True)
        
        # 获取并行步骤
        parallel_steps = []
        for step_id in control_flow.parallel_steps:
            parallel_step = self.workflow_definition.get_step_by_id(step_id)
            if parallel_step:
                parallel_steps.append(parallel_step)
            else:
                logger.warning(f"找不到并行步骤: {step_id}")
        
        if not parallel_steps:
            # 创建执行实例用于获取下一步
            execution = self.execution_context.create_execution(step.id)
            execution.status = StepExecutionStatus.COMPLETED
            return self._get_next_step_id(step, execution, True)
        
        logger.info(f"开始并行执行 {len(parallel_steps)} 个步骤")
        
        # 执行并行步骤
        results = self.parallel_executor.execute_parallel_steps(
            parallel_steps,
            self._execute_single_step_for_parallel,
            control_flow.join_condition or "all_complete"
        )
        
        # 创建并行步骤的执行实例
        all_success = True
        for step_id, result in results.items():
            parallel_execution = self.execution_context.create_execution(step_id)
            parallel_execution.start_time = datetime.now()
            parallel_execution.end_time = datetime.now()
            
            if result and getattr(result, 'success', False):
                parallel_execution.status = StepExecutionStatus.COMPLETED
                parallel_execution.result = result
            else:
                parallel_execution.status = StepExecutionStatus.FAILED
                all_success = False
        
        # 创建当前步骤的执行实例
        execution = self.execution_context.create_execution(step.id)
        execution.status = StepExecutionStatus.COMPLETED if all_success else StepExecutionStatus.FAILED
        execution.start_time = datetime.now()
        execution.end_time = datetime.now()
        
        return self._get_next_step_id(step, execution, all_success)
    
    def _execute_single_step_for_parallel(self, step: WorkflowStep) -> Any:
        """并行执行时的单步骤执行（使用执行实例模型）"""
        # 注意：在并行执行中，执行实例的创建和管理由_handle_parallel_execution负责
        # 这里只负责实际的执行逻辑
        try:
            if not self.step_executor:
                raise ValueError("未设置步骤执行器")
            
            result = self.step_executor(step)
            return result
            
        except Exception as e:
            logger.error(f"并行步骤 {step.id} 执行失败: {e}")
            raise
    
    def _get_next_step_id(self, current_step: WorkflowStep, execution: StepExecution, success: bool) -> Optional[str]:
        """根据控制流确定下一步骤ID（简化版）"""
        
        control_flow = current_step.control_flow
        if not control_flow:
            # 没有控制流定义，执行下一个步骤
            return self._get_sequential_next_step(current_step.id)
        
        # 更新评估器上下文
        self._update_evaluator_context(execution.result)
        
        if control_flow.type == ControlFlowType.TERMINAL:
            return None
        
        elif control_flow.type == ControlFlowType.SEQUENTIAL:
            next_step_id = control_flow.success_next if success else control_flow.failure_next
            return next_step_id or self._get_sequential_next_step(current_step.id)
        
        elif control_flow.type == ControlFlowType.CONDITIONAL:
            # 评估条件（使用混合方案）
            condition_result = self.evaluator.evaluate_control_flow_condition(control_flow, success)
            next_step_id = control_flow.success_next if condition_result else control_flow.failure_next
            return next_step_id or self._get_sequential_next_step(current_step.id)
        
        elif control_flow.type == ControlFlowType.LOOP:
            return self._handle_loop_control(current_step, execution, success)
        
        elif control_flow.type == ControlFlowType.PARALLEL:
            # 并行步骤的后续步骤
            next_step_id = control_flow.success_next if success else control_flow.failure_next
            return next_step_id or self._get_sequential_next_step(current_step.id)
        
        else:
            logger.warning(f"未知的控制流类型: {control_flow.type}")
            return self._get_sequential_next_step(current_step.id)
    
    def _handle_loop_control(self, current_step: WorkflowStep, execution: StepExecution, success: bool) -> Optional[str]:
        """处理循环控制（简化版）"""
        
        control_flow = current_step.control_flow
        loop_key = f"loop_{current_step.id}"
        
        # 获取当前循环计数（使用执行上下文）
        current_count = self.execution_context.loop_counters.get(loop_key, 0)
        
        # 检查最大迭代次数
        max_iterations = control_flow.max_iterations
        if max_iterations:
            max_iter_value = self.evaluator.interpolate_value(max_iterations)
            if isinstance(max_iter_value, str):
                max_iter_value = int(max_iter_value)
            
            if current_count >= max_iter_value:
                logger.info(f"达到最大循环次数 {max_iter_value}，退出循环")
                return control_flow.exit_on_max or self._get_sequential_next_step(current_step.id)
        
        # 评估循环条件
        should_continue_loop = True
        if control_flow.loop_condition:
            should_continue_loop = self.evaluator.evaluate_condition(control_flow.loop_condition)
        
        if should_continue_loop and success:
            # 继续循环
            self.execution_context.loop_counters[loop_key] = current_count + 1
            
            logger.info(f"循环回到步骤: {control_flow.loop_target} (第{current_count + 1}次)")
            return control_flow.loop_target
        
        # 退出循环
        next_step_id = control_flow.success_next if success else control_flow.failure_next
        return next_step_id or self._get_sequential_next_step(current_step.id)
    
    def _get_sequential_next_step(self, current_step_id: str) -> Optional[str]:
        """获取顺序执行的下一步骤"""
        current_index = self.workflow_definition.get_step_index(current_step_id)
        if current_index >= 0 and current_index < len(self.workflow_definition.steps) - 1:
            return self.workflow_definition.steps[current_index + 1].id
        return None
    
    def _check_global_control_rules(self) -> bool:
        """检查全局控制规则"""
        
        for rule in self.workflow_definition.control_rules:
            if self.evaluator.evaluate_condition(rule.trigger):
                logger.info(f"触发全局控制规则: {rule.action}")
                
                if rule.action == "terminate":
                    if rule.cleanup_steps:
                        self._execute_cleanup_steps(rule.cleanup_steps)
                    return True
                
                elif rule.action == "jump_to" and rule.target:
                    # 在新的执行模型中，跳转逻辑由返回的step_id处理
                    logger.info(f"全局控制规则触发跳转到: {rule.target}")
                    return False
        
        return False
    
    def _execute_cleanup_steps(self, cleanup_step_ids: List[str]) -> None:
        """执行清理步骤"""
        for step_id in cleanup_step_ids:
            step = self.workflow_definition.get_step_by_id(step_id)
            if step:
                logger.info(f"执行清理步骤: {step.name}")
                try:
                    self._execute_single_step(step)
                except Exception as e:
                    logger.error(f"清理步骤失败: {step.name}, 错误: {e}")
    
    def _check_step_timeout(self, execution: StepExecution) -> bool:
        """检查步骤是否超时"""
        step = self.workflow_definition.get_step_by_id(execution.step_id)
        if not step or not step.timeout:
            return False
        
        if not execution.start_time:
            return False
        
        return self.evaluator.check_timeout(execution.start_time, step.timeout)
    
    def _update_evaluator_context(self, step_result: Any = None) -> None:
        """更新评估器上下文"""
        
        # 计算执行统计
        execution_stats = self._calculate_execution_stats()
        
        self.evaluator.set_context(
            global_variables=self.workflow_definition.global_variables,
            runtime_variables=self.execution_context.runtime_variables,
            step_result=step_result,
            execution_stats=execution_stats,
            global_state=self.execution_context.current_global_state
        )
    
    def _calculate_execution_stats(self) -> Dict[str, Any]:
        """计算执行统计信息（基于执行上下文）"""
        
        # 使用执行上下文的统计信息
        workflow_stats = self.execution_context.get_workflow_statistics()
        
        current_time = datetime.now()
        execution_time = (current_time - self.execution_start_time).total_seconds()
        
        return {
            'completed_steps': workflow_stats.get('completed_step_executions', 0),
            'failed_steps': workflow_stats.get('failed_step_executions', 0),
            'total_steps': len(self.workflow_definition.steps),
            'total_executions': workflow_stats.get('total_step_executions', 0),
            'execution_time': execution_time,
            'unique_steps_executed': workflow_stats.get('unique_steps_executed', 0),
            'current_iterations': workflow_stats.get('current_iterations', {}),
        }
    
    
    def _update_runtime_variables_from_result(self, step_id: str, result: Any) -> None:
        """从步骤结果更新运行时变量"""
        
        # 设置通用结果变量
        self.execution_context.runtime_variables[f'{step_id}_result'] = result
        self.execution_context.runtime_variables['last_result'] = result
        
        # 根据结果类型设置特定变量
        if hasattr(result, 'success'):
            self.execution_context.runtime_variables[f'{step_id}_success'] = result.success
            self.execution_context.runtime_variables['last_success'] = result.success
        
        if hasattr(result, 'success'):
            # 为了兼容使用returncode的工作流，将success转换为returncode风格
            returncode_equivalent = 0 if result.success else 1
            self.execution_context.runtime_variables[f'{step_id}_returncode'] = returncode_equivalent
            self.execution_context.runtime_variables['last_returncode'] = returncode_equivalent
            
            # 特殊处理测试结果
            if 'test' in step_id.lower():
                self.execution_context.runtime_variables['test_passed'] = result.success
                self.execution_context.runtime_variables['test_success_rate'] = 1.0 if result.success else 0.0
    
    def _generate_execution_result(self, success: bool, error_message: str = None) -> WorkflowExecutionResult:
        """生成工作流执行结果（基于执行上下文）"""
        
        end_time = datetime.now()
        execution_time = (end_time - self.execution_start_time).total_seconds()
        
        # 使用执行上下文统计步骤状态
        workflow_stats = self.execution_context.get_workflow_statistics()
        completed_steps = workflow_stats.get('completed_step_executions', 0)
        failed_steps = workflow_stats.get('failed_step_executions', 0)
        
        # 计算跳过的步骤（定义了但未执行的步骤）
        executed_step_ids = set(self.execution_context.step_executions.keys())
        defined_step_ids = set(step.id for step in self.workflow_definition.steps)
        skipped_steps = len(defined_step_ids - executed_step_ids)
        
        # 收集步骤结果（基于执行上下文）
        step_results = {}
        for step in self.workflow_definition.steps:
            latest_execution = self.execution_context.get_current_execution(step.id)
            step_stats = self.execution_context.get_step_statistics(step.id)
            
            if latest_execution:
                step_results[step.id] = {
                    'name': step.name,
                    'status': latest_execution.status.value,
                    'result': latest_execution.result,
                    'start_time': latest_execution.start_time.isoformat() if latest_execution.start_time else None,
                    'end_time': latest_execution.end_time.isoformat() if latest_execution.end_time else None,
                    'error_message': latest_execution.error_message,
                    'retry_count': latest_execution.retry_count,
                    'total_executions': step_stats['total_executions'],
                    'success_rate': step_stats['success_rate']
                }
            else:
                step_results[step.id] = {
                    'name': step.name,
                    'status': 'not_executed',
                    'result': None,
                    'start_time': None,
                    'end_time': None,
                    'error_message': None,
                    'retry_count': 0,
                    'total_executions': 0,
                    'success_rate': 0.0
                }
        
        return WorkflowExecutionResult(
            success=success,
            workflow_name=self.workflow_definition.workflow_metadata.name,
            total_steps=len(self.workflow_definition.steps),
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            execution_time=execution_time,
            start_time=self.execution_start_time,
            end_time=end_time,
            error_message=error_message,
            step_results=step_results
        )
    
    def _update_global_state(self, step: WorkflowStep, execution: StepExecution) -> None:
        """更新全局状态"""
        try:
            # 获取当前状态
            current_state = self.execution_context.current_global_state
            
            # 如果是第一次更新，从工作流定义中获取初始状态
            if not current_state and self.workflow_definition.global_state:
                current_state = self.workflow_definition.global_state
            
            # 构建工作流上下文信息
            workflow_context = self._build_workflow_context()
            
            # 使用状态更新器更新状态
            new_state = self.state_updater.update_state(
                current_state=current_state,
                step=step,
                execution=execution,
                workflow_context=workflow_context
            )
            
            # 更新执行上下文中的状态
            if new_state != current_state:
                self.execution_context.update_global_state(new_state)
                logger.info(f"全局状态已更新 (步骤: {step.name})")
                logger.debug(f"新状态: {new_state[:200]}...")
                
        except Exception as e:
            logger.warning(f"全局状态更新失败: {e}")
    
    def _build_workflow_context(self) -> str:
        """构建工作流上下文信息"""
        if not self.workflow_definition:
            return ""
            
        context_parts = []
        
        # 工作流基本信息
        metadata = self.workflow_definition.workflow_metadata
        context_parts.append(f"工作流: {metadata.name}")
        if metadata.description:
            context_parts.append(f"描述: {metadata.description}")
        
        # 执行统计
        stats = self.execution_context.get_workflow_statistics()
        total_steps = stats.get('total_step_executions', 0)
        completed_steps = stats.get('completed_step_executions', 0)
        if total_steps > 0:
            context_parts.append(f"执行进度: {completed_steps}/{total_steps} 步骤已完成")
        
        return " | ".join(context_parts)
    
    def get_current_global_state(self) -> str:
        """获取当前全局状态"""
        if self.execution_context:
            return self.execution_context.current_global_state
        return ""
    
    def get_state_summary(self) -> str:
        """获取状态摘要"""
        if self.execution_context:
            return self.execution_context.get_state_summary()
        return "工作流未开始执行"
    
