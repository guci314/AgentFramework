# -*- coding: utf-8 -*-
"""
智能体服务

管理智能体生命周期和能力匹配，为规则执行提供智能体实例。
负责智能体的创建、缓存、性能监控和资源管理。
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ..domain.entities import AgentRegistry, WorkflowResult

logger = logging.getLogger(__name__)


class SystemAgentProxy:
    """系统代理智能体 - 用于处理系统级操作和错误恢复"""
    
    def __init__(self):
        self.api_specification = "系统工具，用于错误恢复和系统级操作"
        
    def execute_sync(self, instruction: str) -> Any:
        """
        执行同步指令
        
        Args:
            instruction: 要执行的指令
            
        Returns:
            执行结果
        """
        logger.info(f"SystemAgentProxy执行指令: {instruction}")
        
        # 简单的系统级操作处理
        if "重试" in instruction or "retry" in instruction.lower():
            return WorkflowResult(
                success=True,
                message="系统重试操作已记录",
                data={"action": "retry", "instruction": instruction},
                metadata={"agent_type": "system_proxy"}
            )
        elif "恢复" in instruction or "recovery" in instruction.lower():
            return WorkflowResult(
                success=True,
                message="系统恢复操作已执行",
                data={"action": "recovery", "instruction": instruction},
                metadata={"agent_type": "system_proxy"}
            )
        elif "检查" in instruction or "check" in instruction.lower():
            return WorkflowResult(
                success=True,
                message="系统检查已完成",
                data={"action": "check", "instruction": instruction},
                metadata={"agent_type": "system_proxy"}
            )
        else:
            return WorkflowResult(
                success=True,
                message="系统操作已执行",
                data={"action": "general", "instruction": instruction},
                metadata={"agent_type": "system_proxy"}
            )
    


class AgentService:
    """智能体服务 - 管理智能体生命周期和能力匹配"""
    
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
        
    def get_or_create_agent(self, agent_name: str) -> Any:
        """
        获取或创建智能体实例
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            智能体实例
            
        Raises:
            ValueError: 如果智能体名称不存在或创建失败
        """
        try:
            # 直接从智能体注册表获取Agent实例
            agent = self.agent_registry.get_agent(agent_name)
            
            # 初始化性能指标
            if agent_name not in self.performance_metrics:
                self.performance_metrics[agent_name] = {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'average_execution_time': 0.0,
                    'last_execution_time': 0.0
                }
            
            logger.debug(f"成功获取Agent: {agent_name}")
            return agent
            
        except Exception as e:
            logger.error(f"获取Agent失败: {agent_name}, 错误: {e}")
            raise ValueError(f"无法获取Agent {agent_name}: {str(e)}")
    
    def execute_natural_language_instruction(self, 
                                           instruction: str, 
                                           agent_name: str, 
                                           context: Dict[str, Any]) -> WorkflowResult:
        """
        执行自然语言指令
        
        Args:
            instruction: 自然语言指令
            agent_name: 智能体名称
            context: 执行上下文
            
        Returns:
            WorkflowResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 获取Agent实例
            agent = self.get_or_create_agent(agent_name)
            
            # 准备执行上下文
            execution_context = self._prepare_execution_context(instruction, context, agent_name)
            
            # 执行指令
            logger.info(f"执行自然语言指令: {instruction[:100]}...")
            
            # 统一调用Agent的execute_sync方法
            if hasattr(agent, 'execute_sync'):
                raw_result = agent.execute_sync(instruction)
                # 转换为标准WorkflowResult格式
                result = self._convert_to_result(raw_result, instruction)
            else:
                raise ValueError(f"Agent {agent_name} 不支持指令执行 (缺少execute_sync方法)")
            
            # 记录性能指标
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(agent_name, True, execution_time)
            
            logger.info(f"指令执行完成，耗时: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            # 记录失败指标
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(agent_name, False, execution_time)
            
            logger.error(f"自然语言指令执行失败: {e}")
            return WorkflowResult(
                success=False,
                message=f"指令执行失败: {str(e)}",
                error_details=str(e),
                metadata={'agent_name': agent_name, 'instruction': instruction}
            )
    
    def validate_agent_capability(self, 
                                agent_name: str, 
                                required_capabilities: List[str]) -> bool:
        """
        验证Agent能力（简化版本）
        
        Args:
            agent_name: 智能体名称
            required_capabilities: 需要的能力列表
            
        Returns:
            bool: 是否具备所需能力
        """
        try:
            # 简化验证：检查Agent是否存在
            agent = self.agent_registry.get_agent(agent_name)
            
            # 所有注册的Agent默认支持所有操作
            # 实际能力验证由Agent实例的execute_sync方法处理
            return True
            
        except Exception as e:
            logger.error(f"Agent验证失败: {e}")
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
                                 agent_name: str) -> Dict[str, Any]:
        """
        准备执行上下文
        
        Args:
            instruction: 指令内容
            context: 原始上下文
            agent_name: 智能体名称
            
        Returns:
            Dict[str, Any]: 准备好的执行上下文
        """
        execution_context = context.copy()
        
        # 添加智能体相关信息
        try:
            agent = self.agent_registry.get_agent(agent_name)
            execution_context['agent_info'] = {
                'name': agent_name,
                'api_specification': getattr(agent, 'api_specification', f'{agent_name} Agent')
            }
        except Exception:
            execution_context['agent_info'] = {
                'name': agent_name,
                'api_specification': f'{agent_name} Agent'
            }
        
        # 添加指令信息
        execution_context['instruction_info'] = {
            'original_instruction': instruction
            # 'timestamp': datetime.now().isoformat()  # Removed for LLM caching
        }
        
        return execution_context
    
    def _convert_to_result(self, raw_result: Any, instruction: str) -> WorkflowResult:
        """
        将智能体的原始执行结果转换为标准WorkflowResult格式
        
        这个方法处理不同类型智能体返回的各种结果格式，统一转换为
        认知工作流系统使用的标准WorkflowResult格式。支持的输入类型：
        
        1. agent_base.WorkflowResult: 带有code, stdout, stderr等属性
        2. cognitive_workflow.WorkflowResult: 已经是标准格式
        3. 字符串: 简单的文本结果
        4. 字典: 包含success, message等字段的结构化结果
        5. 其他类型: 转换为字符串形式
        
        Args:
            raw_result: 智能体返回的原始执行结果，类型可变
            instruction: 原始执行指令，用于错误追踪和元数据
            
        Returns:
            WorkflowResult: 认知工作流的标准结果格式，包含：
                - success: 执行是否成功
                - message: 结果消息
                - data: 结构化数据内容
                - error_details: 错误详情（如果有）
                - metadata: 转换相关的元数据
        
        Raises:
            Exception: 当结果转换过程中发生不可恢复的错误时
        """
        try:
            # 检查是否是agent_base.WorkflowResult对象 (通过属性检查避免直接类型比较)
            if (hasattr(raw_result, 'success') and 
                hasattr(raw_result, 'code') and 
                hasattr(raw_result, 'stdout') and 
                hasattr(raw_result, 'stderr') and 
                hasattr(raw_result, 'return_value')):
                
                # 这是agent_base.WorkflowResult，需要转换为cognitive_workflow.WorkflowResult
                logger.debug("检测到agent_base.WorkflowResult，进行类型转换")
                
                # 构造消息内容
                message_parts = []
                if raw_result.return_value:
                    message_parts.append(f"执行结果: {raw_result.return_value}")
                if raw_result.stdout:
                    message_parts.append(f"输出: {raw_result.stdout}")
                
                message = " | ".join(message_parts) if message_parts else "执行完成"
                
                # 构造数据内容
                data = {
                    'code': raw_result.code,
                    'return_value': raw_result.return_value,
                    'stdout': raw_result.stdout,
                    'stderr': raw_result.stderr
                }
                
                # 构造错误详情
                error_details = raw_result.stderr if raw_result.stderr else None
                
                return WorkflowResult(
                    success=raw_result.success,
                    message=message,
                    data=data,
                    error_details=error_details,
                    metadata={
                        'instruction': instruction,
                        'source_type': 'agent_base_result',
                        'has_code': bool(raw_result.code),
                        'has_output': bool(raw_result.stdout)
                    }
                )
            
            # 如果已经是cognitive_workflow.WorkflowResult对象，直接返回
            if isinstance(raw_result, WorkflowResult):
                logger.debug("检测到cognitive_workflow.WorkflowResult，直接返回")
                return raw_result
            
            # 如果是字符串，创建成功的WorkflowResult
            if isinstance(raw_result, str):
                return WorkflowResult(
                    success=True,
                    message="执行成功",
                    data=raw_result,
                    metadata={'instruction': instruction, 'source_type': 'string'}
                )
            
            # 如果是字典，尝试解析
            if isinstance(raw_result, dict):
                success = raw_result.get('success', True)
                message = raw_result.get('message', '执行完成')
                data = raw_result.get('data')
                error = raw_result.get('error')
                
                return WorkflowResult(
                    success=success,
                    message=message,
                    data=data,
                    error_details=error,
                    metadata={'instruction': instruction, 'source_type': 'dict'}
                )
            
            # 其他类型，创建成功的WorkflowResult
            return WorkflowResult(
                success=True,
                message="执行成功",
                data=str(raw_result),
                metadata={'instruction': instruction, 'source_type': type(raw_result).__name__}
            )
            
        except Exception as e:
            logger.error(f"结果转换失败: {e}")
            return WorkflowResult(
                success=False,
                message="结果转换失败",
                error_details=str(e),
                metadata={'instruction': instruction, 'conversion_error': True}
            )
    
    def _update_performance_metrics(self, 
                                  agent_name: str, 
                                  success: bool, 
                                  execution_time: float) -> None:
        """
        更新性能指标
        
        Args:
            agent_name: 智能体名称
            success: 执行是否成功
            execution_time: 执行时间
        """
        if agent_name not in self.performance_metrics:
            self.performance_metrics[agent_name] = {
                'total_executions': 0,
                'successful_executions': 0,
                'average_execution_time': 0.0,
                'last_execution_time': 0.0
            }
        
        metrics = self.performance_metrics[agent_name]
        
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
        
        # 性能指标现在只在服务层维护，不再传播到实体层
        logger.debug(f"Agent {agent_name} 性能指标已更新: {metrics}")