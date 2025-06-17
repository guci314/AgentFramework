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

from .workflow_definitions import (
    WorkflowDefinition, WorkflowStep, ControlFlow, ControlFlowType, 
    StepStatus, ControlRule
)
from .control_flow_evaluator import ControlFlowEvaluator

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


@dataclass
class WorkflowState:
    """工作流执行状态"""
    current_step_id: Optional[str] = None
    execution_stack: List[str] = field(default_factory=list)
    loop_counters: Dict[str, int] = field(default_factory=dict)
    retry_counters: Dict[str, int] = field(default_factory=dict)
    runtime_variables: Dict[str, Any] = field(default_factory=dict)
    parallel_groups: Dict[str, Set[str]] = field(default_factory=dict)
    completed_parallel_steps: Dict[str, Set[str]] = field(default_factory=dict)
    step_start_times: Dict[str, datetime] = field(default_factory=dict)
    
    def reset_step_status(self, step_id: str) -> None:
        """重置步骤状态（用于循环）"""
        if step_id in self.retry_counters:
            del self.retry_counters[step_id]
        if step_id in self.step_start_times:
            del self.step_start_times[step_id]


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
    
    def __init__(self, max_parallel_workers: int = 4):
        self.evaluator = ControlFlowEvaluator()
        self.parallel_executor = ParallelExecutor(max_parallel_workers)
        self.step_executor = None  # 将由MultiStepAgent_v3设置
        
        # 执行状态
        self.workflow_definition = None
        self.workflow_state = None
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
        self.workflow_state = WorkflowState()
        self.execution_start_time = datetime.now()
        
        logger.info(f"开始执行工作流: {workflow_definition.workflow_metadata.name}")
        
        try:
            # 初始化上下文变量
            if initial_variables:
                self.workflow_state.runtime_variables.update(initial_variables)
            
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
        """执行一个工作流迭代"""
        
        step = self.workflow_definition.get_step_by_id(step_id)
        if not step:
            logger.error(f"找不到步骤: {step_id}")
            return None
        
        self.workflow_state.current_step_id = step_id
        
        # 检查全局控制规则
        if self._check_global_control_rules():
            return None
        
        # 检查步骤是否应该被跳过
        if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
            return self._get_next_step_id(step, True)
        
        # 处理不同类型的控制流
        if step.control_flow and step.control_flow.type == ControlFlowType.PARALLEL:
            return self._handle_parallel_execution(step)
        else:
            return self._execute_single_step(step)
    
    def _execute_single_step(self, step: WorkflowStep) -> Optional[str]:
        """执行单个步骤"""
        
        logger.info(f"执行步骤: {step.name} ({step.id})")
        
        # 更新步骤状态
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        self.workflow_state.step_start_times[step.id] = step.start_time
        
        # 回调通知
        if self.on_step_start:
            self.on_step_start(step)
        
        try:
            # 检查超时
            if step.timeout and self._check_step_timeout(step):
                raise TimeoutError(f"步骤 {step.id} 执行超时")
            
            # 执行步骤
            if not self.step_executor:
                raise ValueError("未设置步骤执行器")
            
            result = self.step_executor(step)
            
            # 更新步骤结果
            step.result = result
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now()
            
            # 更新运行时变量
            self._update_runtime_variables_from_result(step.id, result)
            
            # 回调通知
            if self.on_step_complete:
                self.on_step_complete(step, result)
            
            logger.info(f"步骤完成: {step.name}")
            
            # 确定下一步
            return self._get_next_step_id(step, True)
            
        except Exception as e:
            # 处理步骤失败
            return self._handle_step_failure(step, e)
    
    def _handle_step_failure(self, step: WorkflowStep, error: Exception) -> Optional[str]:
        """处理步骤失败"""
        
        logger.error(f"步骤失败: {step.name}, 错误: {error}")
        
        step.status = StepStatus.FAILED
        step.end_time = datetime.now()
        step.error_message = str(error)
        
        # 检查是否需要重试
        retry_count = self.workflow_state.retry_counters.get(step.id, 0)
        if retry_count < step.max_retries:
            # 增加重试计数
            self.workflow_state.retry_counters[step.id] = retry_count + 1
            
            logger.info(f"重试步骤: {step.name} (第{retry_count + 1}次)")
            
            # 重置步骤状态并重试
            step.status = StepStatus.PENDING
            step.retry_count = retry_count + 1
            
            return step.id  # 重新执行当前步骤
        
        # 回调通知
        if self.on_step_failed:
            self.on_step_failed(step, error)
        
        # 确定失败后的下一步
        return self._get_next_step_id(step, False)
    
    def _handle_parallel_execution(self, step: WorkflowStep) -> Optional[str]:
        """处理并行执行"""
        
        control_flow = step.control_flow
        if not control_flow.parallel_steps:
            logger.warning(f"并行步骤 {step.id} 没有定义parallel_steps")
            return self._get_next_step_id(step, True)
        
        # 获取并行步骤
        parallel_steps = []
        for step_id in control_flow.parallel_steps:
            parallel_step = self.workflow_definition.get_step_by_id(step_id)
            if parallel_step:
                parallel_steps.append(parallel_step)
            else:
                logger.warning(f"找不到并行步骤: {step_id}")
        
        if not parallel_steps:
            return self._get_next_step_id(step, True)
        
        logger.info(f"开始并行执行 {len(parallel_steps)} 个步骤")
        
        # 执行并行步骤
        results = self.parallel_executor.execute_parallel_steps(
            parallel_steps,
            self._execute_single_step_for_parallel,
            control_flow.join_condition or "all_complete"
        )
        
        # 更新步骤状态
        all_success = True
        for step_id, result in results.items():
            parallel_step = self.workflow_definition.get_step_by_id(step_id)
            if result and getattr(result, 'success', False):
                parallel_step.status = StepStatus.COMPLETED
                parallel_step.result = result
            else:
                parallel_step.status = StepStatus.FAILED
                all_success = False
        
        # 更新当前步骤状态
        step.status = StepStatus.COMPLETED if all_success else StepStatus.FAILED
        step.end_time = datetime.now()
        
        return self._get_next_step_id(step, all_success)
    
    def _execute_single_step_for_parallel(self, step: WorkflowStep) -> Any:
        """并行执行时的单步骤执行"""
        try:
            step.status = StepStatus.RUNNING
            step.start_time = datetime.now()
            
            if not self.step_executor:
                raise ValueError("未设置步骤执行器")
            
            result = self.step_executor(step)
            
            step.result = result
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now()
            
            return result
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.end_time = datetime.now()
            step.error_message = str(e)
            raise
    
    def _get_next_step_id(self, current_step: WorkflowStep, success: bool) -> Optional[str]:
        """根据控制流确定下一步骤ID"""
        
        control_flow = current_step.control_flow
        if not control_flow:
            # 没有控制流定义，执行下一个步骤
            return self._get_sequential_next_step(current_step.id)
        
        # 更新评估器上下文
        self._update_evaluator_context(current_step.result)
        
        if control_flow.type == ControlFlowType.TERMINAL:
            return None
        
        elif control_flow.type == ControlFlowType.SEQUENTIAL:
            next_step_id = control_flow.success_next if success else control_flow.failure_next
            return next_step_id or self._get_sequential_next_step(current_step.id)
        
        elif control_flow.type == ControlFlowType.CONDITIONAL:
            # 评估条件
            if control_flow.condition:
                condition_result = self.evaluator.evaluate_condition(control_flow.condition)
                next_step_id = control_flow.success_next if condition_result else control_flow.failure_next
            else:
                next_step_id = control_flow.success_next if success else control_flow.failure_next
            
            return next_step_id or self._get_sequential_next_step(current_step.id)
        
        elif control_flow.type == ControlFlowType.LOOP:
            return self._handle_loop_control(current_step, success)
        
        elif control_flow.type == ControlFlowType.PARALLEL:
            # 并行步骤的后续步骤
            next_step_id = control_flow.success_next if success else control_flow.failure_next
            return next_step_id or self._get_sequential_next_step(current_step.id)
        
        else:
            logger.warning(f"未知的控制流类型: {control_flow.type}")
            return self._get_sequential_next_step(current_step.id)
    
    def _handle_loop_control(self, current_step: WorkflowStep, success: bool) -> Optional[str]:
        """处理循环控制"""
        
        control_flow = current_step.control_flow
        loop_key = f"loop_{current_step.id}"
        
        # 获取当前循环计数
        current_count = self.workflow_state.loop_counters.get(loop_key, 0)
        
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
            self.workflow_state.loop_counters[loop_key] = current_count + 1
            
            # 重置目标步骤的状态
            if control_flow.loop_target:
                target_step = self.workflow_definition.get_step_by_id(control_flow.loop_target)
                if target_step:
                    target_step.status = StepStatus.PENDING
                    self.workflow_state.reset_step_status(control_flow.loop_target)
                
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
                    self.workflow_state.current_step_id = rule.target
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
    
    def _check_step_timeout(self, step: WorkflowStep) -> bool:
        """检查步骤是否超时"""
        if not step.timeout:
            return False
        
        start_time = self.workflow_state.step_start_times.get(step.id)
        if not start_time:
            return False
        
        return self.evaluator.check_timeout(start_time, step.timeout)
    
    def _update_evaluator_context(self, step_result: Any = None) -> None:
        """更新评估器上下文"""
        
        # 计算执行统计
        execution_stats = self._calculate_execution_stats()
        
        self.evaluator.set_context(
            global_variables=self.workflow_definition.global_variables,
            runtime_variables=self.workflow_state.runtime_variables,
            step_result=step_result,
            execution_stats=execution_stats
        )
    
    def _calculate_execution_stats(self) -> Dict[str, Any]:
        """计算执行统计信息"""
        
        completed_count = sum(1 for step in self.workflow_definition.steps 
                            if step.status == StepStatus.COMPLETED)
        failed_count = sum(1 for step in self.workflow_definition.steps 
                         if step.status == StepStatus.FAILED)
        
        current_time = datetime.now()
        execution_time = (current_time - self.execution_start_time).total_seconds()
        
        return {
            'completed_steps': completed_count,
            'failed_steps': failed_count,
            'total_steps': len(self.workflow_definition.steps),
            'execution_time': execution_time,
            'retry_count': sum(self.workflow_state.retry_counters.values()),
            'consecutive_failures': self._count_consecutive_failures(),
        }
    
    def _count_consecutive_failures(self) -> int:
        """计算连续失败次数"""
        consecutive_failures = 0
        
        # 从最近执行的步骤开始倒序计算
        for step in reversed(self.workflow_definition.steps):
            if step.status == StepStatus.FAILED:
                consecutive_failures += 1
            elif step.status in [StepStatus.COMPLETED, StepStatus.RUNNING]:
                break
        
        return consecutive_failures
    
    def _update_runtime_variables_from_result(self, step_id: str, result: Any) -> None:
        """从步骤结果更新运行时变量"""
        
        # 设置通用结果变量
        self.workflow_state.runtime_variables[f'{step_id}_result'] = result
        self.workflow_state.runtime_variables['last_result'] = result
        
        # 根据结果类型设置特定变量
        if hasattr(result, 'success'):
            self.workflow_state.runtime_variables[f'{step_id}_success'] = result.success
            self.workflow_state.runtime_variables['last_success'] = result.success
        
        if hasattr(result, 'success'):
            # 为了兼容使用returncode的工作流，将success转换为returncode风格
            returncode_equivalent = 0 if result.success else 1
            self.workflow_state.runtime_variables[f'{step_id}_returncode'] = returncode_equivalent
            self.workflow_state.runtime_variables['last_returncode'] = returncode_equivalent
            
            # 特殊处理测试结果
            if 'test' in step_id.lower():
                self.workflow_state.runtime_variables['test_passed'] = result.success
                self.workflow_state.runtime_variables['test_success_rate'] = 1.0 if result.success else 0.0
    
    def _generate_execution_result(self, success: bool, error_message: str = None) -> WorkflowExecutionResult:
        """生成工作流执行结果"""
        
        end_time = datetime.now()
        execution_time = (end_time - self.execution_start_time).total_seconds()
        
        # 统计步骤状态
        completed_steps = sum(1 for step in self.workflow_definition.steps 
                            if step.status == StepStatus.COMPLETED)
        failed_steps = sum(1 for step in self.workflow_definition.steps 
                         if step.status == StepStatus.FAILED)
        skipped_steps = sum(1 for step in self.workflow_definition.steps 
                          if step.status == StepStatus.SKIPPED)
        
        # 收集步骤结果
        step_results = {}
        for step in self.workflow_definition.steps:
            step_results[step.id] = {
                'name': step.name,
                'status': step.status.value,
                'result': step.result,
                'start_time': step.start_time.isoformat() if step.start_time else None,
                'end_time': step.end_time.isoformat() if step.end_time else None,
                'error_message': step.error_message,
                'retry_count': step.retry_count
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