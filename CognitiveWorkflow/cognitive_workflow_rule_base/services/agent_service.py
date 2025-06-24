# -*- coding: utf-8 -*-
"""
智能体服务

管理Agent生命周期和能力匹配，为规则执行提供Agent实例。
负责Agent的创建、缓存、性能监控和资源管理。
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ..domain.entities import AgentRegistry, AgentCapability, Result

logger = logging.getLogger(__name__)


class AgentService:
    """智能体服务 - 管理Agent生命周期和能力匹配"""
    
    def __init__(self, 
                 agent_registry: AgentRegistry,
                 agent_instances: Optional[Dict[str, Any]] = None):
        """
        初始化智能体服务
        
        Args:
            agent_registry: 智能体注册表
            agent_instances: 预创建的Agent实例字典 {capability_id: agent_instance}
        """
        self.agent_registry = agent_registry
        self.agent_pool: Dict[str, Any] = agent_instances or {}  # Agent实例缓存池
        self.performance_metrics: Dict[str, Dict[str, float]] = {}  # 性能指标
        
    def get_or_create_agent(self, capability_id: str) -> Any:
        """
        获取或创建Agent实例
        
        Args:
            capability_id: 智能体能力ID
            
        Returns:
            Agent实例
            
        Raises:
            ValueError: 如果能力ID不存在或创建失败
        """
        try:
            # 检查缓存池中是否已有实例
            if capability_id in self.agent_pool:
                agent = self.agent_pool[capability_id]
                logger.debug(f"从缓存获取Agent: {capability_id}")
                return agent
            
            # 获取能力定义
            capability = self.agent_registry.get_capability(capability_id)
            
            # 如果缓存池中没有，但预定义实例存在，直接使用
            # 这里假设外部已经传入了正确的Agent实例
            if capability_id not in self.agent_pool:
                logger.warning(f"Agent实例未找到: {capability_id}，请确保已正确初始化")
                raise ValueError(f"Agent实例不存在: {capability_id}")
            
            agent = self.agent_pool[capability_id]
            
            # 初始化性能指标
            if capability_id not in self.performance_metrics:
                self.performance_metrics[capability_id] = {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'average_execution_time': 0.0,
                    'last_execution_time': 0.0
                }
            
            logger.info(f"成功获取Agent: {capability_id}")
            return agent
            
        except Exception as e:
            logger.error(f"获取或创建Agent失败: {capability_id}, 错误: {e}")
            raise ValueError(f"无法获取Agent {capability_id}: {str(e)}")
    
    def execute_natural_language_instruction(self, 
                                           instruction: str, 
                                           capability_id: str, 
                                           context: Dict[str, Any]) -> Result:
        """
        执行自然语言指令
        
        Args:
            instruction: 自然语言指令
            capability_id: 智能体能力ID
            context: 执行上下文
            
        Returns:
            Result: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 获取Agent实例
            agent = self.get_or_create_agent(capability_id)
            
            # 验证Agent能力
            capability = self.agent_registry.get_capability(capability_id)
            
            # 准备执行上下文
            execution_context = self._prepare_execution_context(instruction, context, capability)
            
            # 执行指令
            logger.info(f"执行自然语言指令: {instruction[:100]}...")
            
            # 调用Agent的执行方法
            if hasattr(agent, 'execute_natural_language_instruction'):
                result = agent.execute_natural_language_instruction(instruction, execution_context)
            elif hasattr(agent, 'execute_sync'):
                # 使用同步执行方法
                raw_result = agent.execute_sync(instruction)
                # 转换为标准Result格式
                result = self._convert_to_result(raw_result, instruction)
            else:
                raise ValueError(f"Agent {capability_id} 不支持自然语言指令执行")
            
            # 记录性能指标
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(capability_id, True, execution_time)
            
            logger.info(f"指令执行完成，耗时: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            # 记录失败指标
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(capability_id, False, execution_time)
            
            logger.error(f"自然语言指令执行失败: {e}")
            return Result(
                success=False,
                message=f"指令执行失败: {str(e)}",
                error_details=str(e),
                metadata={'capability_id': capability_id, 'instruction': instruction}
            )
    
    def validate_agent_capability(self, 
                                capability_id: str, 
                                required_capabilities: List[str]) -> bool:
        """
        验证Agent能力
        
        Args:
            capability_id: 智能体能力ID
            required_capabilities: 需要的能力列表
            
        Returns:
            bool: 是否具备所需能力
        """
        try:
            capability = self.agent_registry.get_capability(capability_id)
            
            # 检查是否支持所有必需的能力
            for required_cap in required_capabilities:
                if not capability.can_execute_action(required_cap):
                    logger.warning(f"Agent {capability_id} 不支持能力: {required_cap}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"能力验证失败: {e}")
            return False
    
    def manage_agent_lifecycle(self, agent: Any) -> None:
        """
        管理Agent生命周期
        
        Args:
            agent: Agent实例
        """
        try:
            # 这里可以实现Agent的生命周期管理逻辑
            # 例如：健康检查、资源清理、状态重置等
            
            # 健康检查
            if hasattr(agent, 'health_check'):
                health_status = agent.health_check()
                logger.debug(f"Agent健康检查: {health_status}")
            
            # 内存清理
            if hasattr(agent, 'cleanup_memory'):
                agent.cleanup_memory()
                logger.debug("Agent内存清理完成")
                
        except Exception as e:
            logger.error(f"Agent生命周期管理失败: {e}")
    
    def get_agent_performance_metrics(self, capability_id: str) -> Dict[str, Any]:
        """
        获取Agent性能指标
        
        Args:
            capability_id: 智能体能力ID
            
        Returns:
            Dict[str, Any]: 性能指标
        """
        if capability_id not in self.performance_metrics:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'last_execution_time': 0.0
            }
        
        metrics = self.performance_metrics[capability_id].copy()
        
        # 计算成功率
        total = metrics['total_executions']
        successful = metrics['successful_executions']
        metrics['success_rate'] = successful / total if total > 0 else 0.0
        
        return metrics
    
    def scale_agent_pool(self, capability_id: str, target_count: int) -> None:
        """
        扩缩容Agent池
        
        Args:
            capability_id: 智能体能力ID
            target_count: 目标实例数量
        """
        try:
            # 当前实现为单实例模式，这里记录扩缩容需求
            logger.info(f"Agent池扩缩容请求: {capability_id} -> {target_count}")
            
            # 在实际实现中，这里可以：
            # 1. 创建多个Agent实例
            # 2. 实现负载均衡
            # 3. 管理实例池
            
        except Exception as e:
            logger.error(f"Agent池扩缩容失败: {e}")
    
    def list_available_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的Agent
        
        Returns:
            List[Dict[str, Any]]: Agent信息列表
        """
        agents_info = []
        
        for capability in self.agent_registry.list_all_capabilities():
            agent_info = {
                'capability_id': capability.id,
                'name': capability.name,
                'description': capability.description,
                'supported_actions': capability.supported_actions,
                'is_available': capability.id in self.agent_pool,
                'performance_metrics': self.get_agent_performance_metrics(capability.id)
            }
            agents_info.append(agent_info)
        
        return agents_info
    
    def register_agent_instance(self, capability_id: str, agent_instance: Any) -> None:
        """
        注册Agent实例到缓存池
        
        Args:
            capability_id: 智能体能力ID
            agent_instance: Agent实例
        """
        self.agent_pool[capability_id] = agent_instance
        logger.info(f"Agent实例已注册: {capability_id}")
    
    def _prepare_execution_context(self, 
                                 instruction: str, 
                                 context: Dict[str, Any],
                                 capability: AgentCapability) -> Dict[str, Any]:
        """
        准备执行上下文
        
        Args:
            instruction: 指令内容
            context: 原始上下文
            capability: 智能体能力
            
        Returns:
            Dict[str, Any]: 准备好的执行上下文
        """
        execution_context = context.copy()
        
        # 添加能力相关信息
        execution_context['capability_info'] = {
            'id': capability.id,
            'name': capability.name,
            'description': capability.description,
            'api_specification': capability.api_specification
        }
        
        # 添加指令信息
        execution_context['instruction_info'] = {
            'original_instruction': instruction,
            'timestamp': datetime.now().isoformat()
        }
        
        return execution_context
    
    def _convert_to_result(self, raw_result: Any, instruction: str) -> Result:
        """
        将原始结果转换为标准Result格式
        
        Args:
            raw_result: 原始执行结果
            instruction: 执行的指令
            
        Returns:
            Result: 标准化的结果
        """
        try:
            # 如果已经是Result对象，直接返回
            if isinstance(raw_result, Result):
                return raw_result
            
            # 如果是字符串，创建成功的Result
            if isinstance(raw_result, str):
                return Result(
                    success=True,
                    message="执行成功",
                    data=raw_result,
                    metadata={'instruction': instruction}
                )
            
            # 如果是字典，尝试解析
            if isinstance(raw_result, dict):
                success = raw_result.get('success', True)
                message = raw_result.get('message', '执行完成')
                data = raw_result.get('data')
                error = raw_result.get('error')
                
                return Result(
                    success=success,
                    message=message,
                    data=data,
                    error_details=error,
                    metadata={'instruction': instruction}
                )
            
            # 其他类型，创建成功的Result
            return Result(
                success=True,
                message="执行成功",
                data=str(raw_result),
                metadata={'instruction': instruction}
            )
            
        except Exception as e:
            logger.error(f"结果转换失败: {e}")
            return Result(
                success=False,
                message="结果转换失败",
                error_details=str(e),
                metadata={'instruction': instruction}
            )
    
    def _update_performance_metrics(self, 
                                  capability_id: str, 
                                  success: bool, 
                                  execution_time: float) -> None:
        """
        更新性能指标
        
        Args:
            capability_id: 智能体能力ID
            success: 执行是否成功
            execution_time: 执行时间
        """
        if capability_id not in self.performance_metrics:
            self.performance_metrics[capability_id] = {
                'total_executions': 0,
                'successful_executions': 0,
                'average_execution_time': 0.0,
                'last_execution_time': 0.0
            }
        
        metrics = self.performance_metrics[capability_id]
        
        # 更新统计信息
        metrics['total_executions'] += 1
        if success:
            metrics['successful_executions'] += 1
        
        # 更新平均执行时间
        total_executions = metrics['total_executions']
        current_avg = metrics['average_execution_time']
        metrics['average_execution_time'] = (
            (current_avg * (total_executions - 1) + execution_time) / total_executions
        )
        
        metrics['last_execution_time'] = execution_time
        
        # 更新智能体能力的性能指标
        try:
            capability = self.agent_registry.get_capability(capability_id)
            capability.update_performance_metric('success_rate', 
                                                metrics['successful_executions'] / metrics['total_executions'])
            capability.update_performance_metric('average_execution_time', 
                                                metrics['average_execution_time'])
        except Exception as e:
            logger.error(f"更新能力性能指标失败: {e}")