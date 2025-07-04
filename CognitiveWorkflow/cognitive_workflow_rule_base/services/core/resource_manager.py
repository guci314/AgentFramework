"""
资源管理器服务 - 负责智能体的动态分配（实例层）

该服务处理从类型层（ProductionRule）到实例层（RuleExecution）的智能体分配，
使用语言模型进行智能匹配，实现动态的资源调度。
"""

from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
import json
import logging

from ...domain.entities import (
    ProductionRule, 
    RuleExecution, 
    AgentRegistry,
    RuleSetExecution,
    GlobalState
)
from .language_model_service import LanguageModelService

logger = logging.getLogger(__name__)


class AllocationStrategy(Protocol):
    """分配策略协议"""
    
    def allocate_agent(
        self,
        rule: ProductionRule,
        available_agents: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """为规则分配智能体"""
        ...


@dataclass
class AllocationResult:
    """分配结果"""
    agent_name: str
    confidence: float
    reasoning: str


class LLMAllocationStrategy:
    """基于语言模型的智能分配策略"""
    
    def __init__(self, llm_service: LanguageModelService):
        self.llm_service = llm_service
    
    def allocate_agent(
        self,
        rule: ProductionRule,
        available_agents: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """使用语言模型为规则分配最合适的智能体"""
        
        # 准备智能体信息
        agent_info = self._prepare_agent_info(available_agents)
        
        # 构建分配提示词
        prompt = self._build_allocation_prompt(rule, agent_info, context)
        
        try:
            # 调用语言模型
            response = self.llm_service.invoke(prompt)
            
            # 解析响应
            result = self._parse_allocation_response(response)
            
            if result and result.agent_name in available_agents:
                logger.info(
                    f"为规则 '{rule.name}' 分配智能体 '{result.agent_name}' "
                    f"(置信度: {result.confidence}, 理由: {result.reasoning})"
                )
                return result.agent_name
            else:
                logger.warning(f"语言模型未能为规则 '{rule.name}' 分配有效的智能体")
                return None
                
        except Exception as e:
            logger.error(f"智能体分配过程中发生错误: {e}")
            return None
    
    def _prepare_agent_info(self, available_agents: Dict[str, Any]) -> str:
        """准备智能体信息描述"""
        agent_descriptions = []
        
        for name, agent in available_agents.items():
            # 获取智能体的能力描述
            spec = getattr(agent, 'api_specification', f'{name} Agent')
            agent_descriptions.append(f"- {name}: {spec}")
        
        return "\n".join(agent_descriptions)
    
    def _build_allocation_prompt(
        self, 
        rule: ProductionRule, 
        agent_info: str,
        context: Dict[str, Any]
    ) -> str:
        """构建智能体分配提示词"""
        
        # 获取当前状态信息
        current_state = context.get('current_state', '未知')
        workflow_goal = context.get('workflow_goal', '未指定')
        
        prompt = f"""你是一个智能资源分配器，需要为产生式规则分配最合适的智能体来执行任务。

## 当前工作流目标
{workflow_goal}

## 当前系统状态
{current_state}

## 需要执行的规则
规则名称: {rule.name}
触发条件: {rule.condition}
执行动作: {rule.action}
预期结果: {rule.expected_outcome}

## 可用的智能体
{agent_info}

## 任务要求
请分析规则的执行需求，选择最合适的智能体来执行这个规则。考虑以下因素：
1. 智能体的能力是否与规则的动作需求匹配
2. 智能体的专业领域是否适合处理该任务
3. 执行该规则所需的具体功能

## 输出格式
请以JSON格式返回你的分配决策：
{{
    "agent_name": "选中的智能体名称",
    "confidence": 0.95,  // 置信度 (0-1)
    "reasoning": "选择该智能体的详细理由"
}}

注意：agent_name必须是上述可用智能体列表中的名称之一。
"""
        
        return prompt
    
    def _parse_allocation_response(self, response: str) -> Optional[AllocationResult]:
        """解析语言模型的分配响应"""
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return AllocationResult(
                    agent_name=data.get('agent_name', ''),
                    confidence=float(data.get('confidence', 0)),
                    reasoning=data.get('reasoning', '')
                )
        except Exception as e:
            logger.error(f"解析分配响应时出错: {e}")
        
        return None


class ResourceManager:
    """资源管理器 - 负责智能体的动态分配和管理"""
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        llm_service: LanguageModelService,
        allocation_strategy: Optional[AllocationStrategy] = None
    ):
        self.agent_registry = agent_registry
        self.llm_service = llm_service
        self.allocation_strategy = allocation_strategy or LLMAllocationStrategy(llm_service)
    
    def allocate_agent_for_rule(
        self,
        rule: ProductionRule,
        rule_set_execution: RuleSetExecution
    ) -> Optional[str]:
        """为规则分配智能体"""
        
        # 获取可用的智能体
        available_agents = self.agent_registry.agents
        
        if not available_agents:
            logger.error("没有可用的智能体")
            return None
        
        # 准备上下文信息
        context = {
            'current_state': rule_set_execution.global_state.state,
            'workflow_goal': rule_set_execution.context.get('goal', ''),
            'execution_history': rule_set_execution.global_state.execution_history,
            'context_variables': rule_set_execution.global_state.context_variables
        }
        
        # 使用策略分配智能体
        allocated_agent = self.allocation_strategy.allocate_agent(
            rule, available_agents, context
        )
        
        # 如果策略分配失败，使用后备方案
        if not allocated_agent:
            allocated_agent = self._fallback_allocation(rule, available_agents)
        
        return allocated_agent
    
    def create_rule_execution(
        self,
        rule: ProductionRule,
        rule_set_execution: RuleSetExecution
    ) -> RuleExecution:
        """创建规则执行实例，包含智能体分配"""
        
        # 分配智能体
        assigned_agent = self.allocate_agent_for_rule(rule, rule_set_execution)
        
        if not assigned_agent:
            raise ValueError(f"无法为规则 '{rule.name}' 分配智能体")
        
        # 创建执行实例
        execution_id = f"{rule.id}_exec_{rule_set_execution.id}"
        
        rule_execution = RuleExecution(
            id=execution_id,
            rule_id=rule.id,
            assigned_agent=assigned_agent,
            execution_context={
                'rule_name': rule.name,
                'rule_set_execution_id': rule_set_execution.id,
                'allocated_by': 'ResourceManager'
            }
        )
        
        return rule_execution
    
    def _fallback_allocation(
        self, 
        rule: ProductionRule,
        available_agents: Dict[str, Any]
    ) -> Optional[str]:
        """后备分配方案 - 基于简单的关键词匹配"""
        
        # 如果规则中原本有agent_name（兼容旧版本），优先使用
        if hasattr(rule, 'metadata') and 'suggested_agent' in rule.metadata:
            suggested = rule.metadata['suggested_agent']
            if suggested in available_agents:
                logger.info(f"使用规则建议的智能体: {suggested}")
                return suggested
        
        # 基于动作关键词的简单匹配
        action_lower = rule.action.lower()
        
        # 定义关键词映射
        keyword_mapping = {
            'calculate': 'CalculatorAgent',
            'compute': 'CalculatorAgent',
            'analyze': 'DataAnalyzer',
            'search': 'SearchAgent',
            'write': 'WriterAgent',
            'generate': 'GeneratorAgent',
            'validate': 'ValidatorAgent',
            'test': 'TesterAgent'
        }
        
        # 查找匹配的智能体
        for keyword, agent_name in keyword_mapping.items():
            if keyword in action_lower and agent_name in available_agents:
                logger.info(f"通过关键词 '{keyword}' 匹配到智能体: {agent_name}")
                return agent_name
        
        # 如果都没有匹配，返回第一个可用的智能体
        first_agent = next(iter(available_agents.keys()))
        logger.warning(f"使用默认智能体: {first_agent}")
        return first_agent
    
    def get_agent_workload(self) -> Dict[str, int]:
        """获取智能体的工作负载统计"""
        # TODO: 实现基于执行历史的负载统计
        return {}
    
    def optimize_allocation(self, execution_history: List[RuleExecution]) -> None:
        """基于执行历史优化分配策略"""
        # TODO: 实现基于历史数据的策略优化
        pass