# -*- coding: utf-8 -*-
"""
产生式规则工作流引擎

作为整个产生式规则系统的统一入口和控制中心，
提供工作流执行、暂停、恢复等控制功能。
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import threading
import time

from ..domain.entities import GlobalState, AgentRegistry
from ..domain.value_objects import ExecutionStatus, WorkflowExecutionResult
from ..services.rule_engine_service import RuleEngineService

logger = logging.getLogger(__name__)


class ProductionRuleWorkflowEngine:
    """产生式规则工作流引擎 - 系统统一入口"""
    
    def __init__(self, rule_engine_service: RuleEngineService, default_agent_registry: AgentRegistry = None):
        """
        初始化工作流引擎
        
        Args:
            rule_engine_service: 核心规则引擎服务
            default_agent_registry: 默认智能体注册表
        """
        self.rule_engine_service = rule_engine_service
        self.default_agent_registry = default_agent_registry or AgentRegistry()
        self.execution_status = ExecutionStatus.PENDING
        self._execution_thread: Optional[threading.Thread] = None
        self._stop_requested = False
        self._pause_requested = False
        self._current_goal: Optional[str] = None
        self._current_agent_registry: Optional[AgentRegistry] = None
        self._execution_result: Optional[WorkflowExecutionResult] = None
        self._execution_lock = threading.Lock()
        
    def execute_goal(self, goal: str) -> WorkflowExecutionResult:
        """
        执行目标工作流（同步版本）
        
        Args:
            goal: 目标描述
            
        Returns:
            WorkflowExecutionResult: 工作流执行结果
        """
        with self._execution_lock:
            if self.execution_status == ExecutionStatus.RUNNING:
                raise RuntimeError("工作流正在执行中，请先停止当前执行")
            
            try:
                logger.info(f"开始执行工作流目标: {goal}")
                self.execution_status = ExecutionStatus.RUNNING
                self._current_goal = goal
                self._current_agent_registry = self.default_agent_registry
                self._stop_requested = False
                self._pause_requested = False
                
                # 执行工作流
                result = self.rule_engine_service.execute_workflow(goal, self._current_agent_registry)
                
                self._execution_result = result
                self.execution_status = ExecutionStatus.COMPLETED if result.is_successful else ExecutionStatus.FAILED
                
                logger.info(f"工作流执行完成: {'成功' if result.is_successful else '失败'}")
                return result
                
            except Exception as e:
                logger.error(f"工作流执行异常: {e}")
                self.execution_status = ExecutionStatus.FAILED
                
                # 创建失败结果
                error_result = WorkflowExecutionResult(
                    goal=goal,
                    is_successful=False,
                    final_state=f"执行异常: {str(e)}",
                    total_iterations=0,
                    execution_metrics=None,
                    final_message=f"工作流执行异常: {str(e)}",
                    completion_timestamp=datetime.now()
                )
                
                self._execution_result = error_result
                return error_result
    
    def execute_goal_async(self, goal: str) -> bool:
        """
        异步执行目标工作流
        
        Args:
            goal: 目标描述
            
        Returns:
            bool: 是否成功启动异步执行
        """
        with self._execution_lock:
            if self.execution_status == ExecutionStatus.RUNNING:
                logger.warning("工作流正在执行中，无法启动新的异步执行")
                return False
            
            try:
                self._current_goal = goal
                self._current_agent_registry = self.default_agent_registry
                self._stop_requested = False
                self._pause_requested = False
                
                # 启动异步执行线程
                self._execution_thread = threading.Thread(
                    target=self._async_execution_worker,
                    args=(goal, self._current_agent_registry),
                    daemon=True
                )
                
                self.execution_status = ExecutionStatus.RUNNING
                self._execution_thread.start()
                
                logger.info(f"异步工作流执行已启动: {goal}")
                return True
                
            except Exception as e:
                logger.error(f"启动异步工作流执行失败: {e}")
                self.execution_status = ExecutionStatus.FAILED
                return False
    
    def pause_execution(self) -> bool:
        """
        暂停执行
        
        Returns:
            bool: 是否成功暂停
        """
        try:
            if self.execution_status != ExecutionStatus.RUNNING:
                logger.warning("工作流未在执行中，无法暂停")
                return False
            
            self._pause_requested = True
            
            # 通知规则引擎暂停
            pause_success = self.rule_engine_service.pause_workflow()
            
            if pause_success:
                logger.info("工作流执行已暂停")
                return True
            else:
                self._pause_requested = False
                logger.warning("工作流暂停失败")
                return False
                
        except Exception as e:
            logger.error(f"暂停工作流失败: {e}")
            self._pause_requested = False
            return False
    
    def resume_execution(self) -> bool:
        """
        恢复执行
        
        Returns:
            bool: 是否成功恢复
        """
        try:
            if not self._pause_requested:
                logger.warning("工作流未暂停，无法恢复")
                return False
            
            # 通知规则引擎恢复
            resume_success = self.rule_engine_service.resume_workflow()
            
            if resume_success:
                self._pause_requested = False
                logger.info("工作流执行已恢复")
                return True
            else:
                logger.warning("工作流恢复失败")
                return False
                
        except Exception as e:
            logger.error(f"恢复工作流失败: {e}")
            return False
    
    def stop_execution(self) -> bool:
        """
        停止执行
        
        Returns:
            bool: 是否成功停止
        """
        try:
            if self.execution_status not in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]:
                logger.warning("工作流未在执行中，无法停止")
                return False
            
            self._stop_requested = True
            self._pause_requested = False
            
            # 等待执行线程结束
            if self._execution_thread and self._execution_thread.is_alive():
                self._execution_thread.join(timeout=5.0)
                
                if self._execution_thread.is_alive():
                    logger.warning("执行线程未能在超时时间内结束")
                    return False
            
            self.execution_status = ExecutionStatus.CANCELLED
            logger.info("工作流执行已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止工作流失败: {e}")
            return False
    
    def get_execution_status(self) -> ExecutionStatus:
        """
        获取执行状态
        
        Returns:
            ExecutionStatus: 当前执行状态
        """
        return self.execution_status
    
    def get_current_state(self) -> Optional[GlobalState]:
        """
        获取当前状态
        
        Returns:
            Optional[GlobalState]: 当前全局状态
        """
        try:
            return self.rule_engine_service.state_service.get_current_state()
        except Exception as e:
            logger.error(f"获取当前状态失败: {e}")
            return None
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """
        获取执行指标
        
        Returns:
            Dict[str, Any]: 执行指标信息
        """
        try:
            metrics = {
                'execution_status': self.execution_status.value,
                'current_goal': self._current_goal,
                'workflow_status': self.rule_engine_service.get_workflow_status(),
                'execution_result': self._execution_result.to_dict() if self._execution_result else None
                # 'timestamp': datetime.now().isoformat()  # Removed for LLM caching
            }
            
            # 添加当前状态信息
            current_state = self.get_current_state()
            if current_state:
                metrics['current_state'] = {
                    'description': current_state.state,
                    'iteration_count': current_state.iteration_count,
                    'goal_achieved': current_state.goal_achieved
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取执行指标失败: {e}")
            return {
                'execution_status': self.execution_status.value,
                'error': str(e)
                # 'timestamp': datetime.now().isoformat()  # Removed for LLM caching
            }
    
    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """
        获取工作流历史
        
        Returns:
            List[Dict[str, Any]]: 工作流历史记录
        """
        try:
            current_state = self.get_current_state()
            if current_state and current_state.workflow_id:
                state_history = self.rule_engine_service.state_service.get_state_history(
                    current_state.workflow_id
                )
                
                history = []
                for state in state_history:
                    history.append({
                        # 'timestamp': state.timestamp.isoformat(),  # Removed for LLM caching
                        'description': state.state,
                        'iteration_count': state.iteration_count,
                        'context_variables': state.context_variables
                    })
                
                return history
            
            return []
            
        except Exception as e:
            logger.error(f"获取工作流历史失败: {e}")
            return []
    
    def is_running(self) -> bool:
        """
        检查是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        return self.execution_status == ExecutionStatus.RUNNING
    
    def is_paused(self) -> bool:
        """
        检查是否已暂停
        
        Returns:
            bool: 是否已暂停
        """
        return self._pause_requested
    
    def get_execution_result(self) -> Optional[WorkflowExecutionResult]:
        """
        获取最后一次执行的结果
        
        Returns:
            Optional[WorkflowExecutionResult]: 执行结果
        """
        return self._execution_result
    
    def get_default_agent_registry(self) -> AgentRegistry:
        """
        获取默认的智能体注册表
        
        Returns:
            AgentRegistry: 默认智能体注册表
        """
        return self.default_agent_registry
    
    @property
    def agent_registry(self) -> AgentRegistry:
        """
        智能体注册表属性（向后兼容）
        
        Returns:
            AgentRegistry: 智能体注册表
        """
        return self.default_agent_registry
    
    def _async_execution_worker(self, goal: str, agent_registry: AgentRegistry) -> None:
        """
        异步执行工作线程
        
        Args:
            goal: 目标描述
            agent_registry: 智能体注册表
        """
        try:
            logger.info(f"异步工作流执行开始: {goal}")
            
            # 执行工作流，支持暂停和停止
            result = self._execute_with_control(goal, agent_registry)
            
            with self._execution_lock:
                self._execution_result = result
                
                if self._stop_requested:
                    self.execution_status = ExecutionStatus.CANCELLED
                    logger.info("异步工作流执行已被停止")
                elif result.is_successful:
                    self.execution_status = ExecutionStatus.COMPLETED
                    logger.info("异步工作流执行成功完成")
                else:
                    self.execution_status = ExecutionStatus.FAILED
                    logger.warning("异步工作流执行失败")
                    
        except Exception as e:
            logger.error(f"异步工作流执行异常: {e}")
            
            with self._execution_lock:
                self.execution_status = ExecutionStatus.FAILED
                self._execution_result = WorkflowExecutionResult(
                    goal=goal,
                    is_successful=False,
                    final_state=f"异步执行异常: {str(e)}",
                    total_iterations=0,
                    execution_metrics=None,
                    final_message=f"异步执行异常: {str(e)}",
                    completion_timestamp=datetime.now()
                )
    
    def _execute_with_control(self, goal: str, agent_registry: AgentRegistry) -> WorkflowExecutionResult:
        """
        支持控制的执行方法
        
        Args:
            goal: 目标描述
            agent_registry: 智能体注册表
            
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        try:
            # 这里需要修改rule_engine_service的execute_workflow方法
            # 以支持中断检查，当前简化实现
            
            # 定期检查停止和暂停请求
            start_time = datetime.now()
            
            while not self._stop_requested:
                if self._pause_requested:
                    # 暂停时等待
                    time.sleep(0.1)
                    continue
                
                # 执行一次迭代或完整工作流
                # 注意：这里需要rule_engine_service支持增量执行
                result = self.rule_engine_service.execute_workflow(goal, agent_registry)
                
                # 检查是否完成
                if result.is_successful or not result.is_successful:
                    return result
                
                # 避免过度消耗CPU
                time.sleep(0.01)
            
            # 如果被停止，返回取消结果
            return WorkflowExecutionResult(
                goal=goal,
                is_successful=False,
                final_state="工作流执行被用户停止",
                total_iterations=0,
                execution_metrics=None,
                final_message="工作流执行被用户停止",
                completion_timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"控制执行失败: {e}")
            return WorkflowExecutionResult(
                goal=goal,
                is_successful=False,
                final_state=f"控制执行异常: {str(e)}",
                total_iterations=0,
                execution_metrics=None,
                final_message=f"控制执行异常: {str(e)}",
                completion_timestamp=datetime.now()
            )
    
    def cleanup(self) -> None:
        """
        清理资源
        """
        try:
            # 停止执行
            if self.is_running():
                self.stop_execution()
            
            # 清理线程
            if self._execution_thread and self._execution_thread.is_alive():
                self._execution_thread.join(timeout=2.0)
            
            logger.info("工作流引擎资源已清理")
            
        except Exception as e:
            logger.error(f"清理工作流引擎资源失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()