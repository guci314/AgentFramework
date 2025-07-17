"""
自我智能体 (Ego Agent)

基于具身认知工作流理论的自我智能体实现。
自我智能体负责理性思考、状态分析和指令生成。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_base import AgentBase, Result
from langchain_core.language_models import BaseChatModel
from typing import Literal, Tuple, Optional, List, Dict

try:
    from .decision_types import Decision, DecisionType
except ImportError:
    from decision_types import Decision, DecisionType


class EgoAgent(AgentBase):
    """
    自我智能体 - 理性思考系统
    
    职责：
    1. 分析当前状态和情况
    2. 决定下一步行动方向
    3. 生成观察和执行指令
    4. 与本我进行评估协调
    """
    
    def __init__(self, llm: BaseChatModel, system_message: str = None):
        default_system = """你是具身认知工作流系统中的自我智能体，负责理性思考和决策。

你的核心职责：
1. 分析当前状态和上下文信息
2. 决定下一步行动：继续循环、请求评估、或判断失败
3. 生成具体的观察指令或执行指令
4. 与本我协调，请求价值评估

工作原则：
- 增量式规划，不做预先规划
- 基于即时感知做出理性决策
- 用自然语言生成清晰的指令
- 优先考虑目标达成的可能性

指令格式要求：
- 观察指令：明确说明需要了解什么信息
- 执行指令：具体描述要执行的操作
- 所有指令都用自然语言表达，便于身体理解执行
"""
        
        super().__init__(llm, system_message or default_system)
        self.name = "自我智能体"
    
    def analyze_current_state(self, context: str) -> str:
        """
        分析当前状态和情况
        
        Args:
            context: 当前的上下文信息，包括任务描述、执行历史等
            
        Returns:
            str: 状态分析结果
        """
        message = f"""请分析当前状态：

上下文信息：
{context}

请分析：
1. 当前处于什么状态
2. 已经完成了什么
3. 还需要做什么
4. 可能遇到的问题或困难

请给出简洁明确的状态分析。"""

        result = self.chat_sync(message)
        return result.return_value
    
    def decide_next_action(self, state_analysis: str, available_agents: Optional[List[AgentBase]] = None) -> Decision:
        """
        基于状态分析决定下一步行动方向
        
        Args:
            state_analysis: 当前状态的分析结果
            available_agents: 可用Agent实例列表
            
        Returns:
            Decision: 包含决策类型、执行者Agent和执行指令的决策对象
        """
        # 构建Agent信息部分
        agents_info = ""
        agent_map = {}  # 用于根据名称查找Agent实例
        if available_agents:  # 即使只有一个Agent也显示信息
            agents_info = "\n\n可用的执行者（Agent）：\n"
            for agent in available_agents:
                agent_name = getattr(agent, 'name', agent.__class__.__name__)
                agent_spec = getattr(agent, 'api_specification', '通用执行能力')
                agents_info += f"- {agent_name}: {agent_spec}\n"
                agent_map[agent_name] = agent
            if len(available_agents) == 1:
                agents_info += f"\n重要：只有一个可用的执行者，请在'执行者'字段使用'{agent_name}'。"
            else:
                agents_info += "\n重要：如果选择'执行指令'，必须在'执行者'字段指定上述列表中的一个Agent名称。"
        
        message = f"""基于以下状态分析，决定下一步行动：

状态分析：
{state_analysis}
{agents_info}

请分析情况并选择下一步行动。返回JSON格式：

{{
    "决策": "选择的行动",
    "指令": "如果决策是执行指令，请提供具体的执行指令",
    "执行者": "如果决策是执行指令，必须从上述Agent列表中选择一个执行者名称",
    "理由": "简要说明理由"
}}

可选的行动：
- "执行指令" - 如果需要执行具体操作，同时在"指令"字段提供具体的执行指令
- "请求评估" - 如果认为可能已经达到目标，需要本我进行评估确认  
- "判断失败" - 如果认为目标无法达成，存在无法解决的问题

注意事项：
- 执行者必须是上面列出的Agent之一，不能选择"自我智能体"或其他不在列表中的名称
- 如果只有一个Agent，直接使用那个Agent的名称
- 如果没有提供Agent列表，执行者字段可以留空"""

        result = self.chat_sync(message, response_format={"type": "json_object"})
        
        try:
            import json
            response_data = json.loads(result.return_value.strip())
            decision = response_data.get("决策", "").strip()
            instruction = response_data.get("指令", "")
            agent_name = response_data.get("执行者", "")
            
            # 将字符串决策转换为DecisionType枚举
            decision_mapping = {
                "请求评估": DecisionType.REQUEST_EVALUATION,
                "判断失败": DecisionType.JUDGMENT_FAILED,
                "执行指令": DecisionType.EXECUTE_INSTRUCTION
            }
            
            decision_type = decision_mapping.get(decision, DecisionType.REQUEST_EVALUATION)
            
            # 如果是执行指令，查找对应的Agent实例
            selected_agent = None
            if decision_type == DecisionType.EXECUTE_INSTRUCTION and available_agents and agent_name:
                if agent_name in agent_map:
                    selected_agent = agent_map[agent_name]
                else:
                    # 如果选择了无效的Agent，使用第一个可用的Agent
                    print(f"警告：选择了无效的执行者 '{agent_name}'，使用默认Agent")
                    selected_agent = available_agents[0] if available_agents else None
            
            return Decision(
                decision_type=decision_type,
                agent=selected_agent,
                instruction=instruction if decision_type == DecisionType.EXECUTE_INSTRUCTION else None
            )
        except (json.JSONDecodeError, KeyError):
            # JSON解析失败，默认请求评估
            return Decision(decision_type=DecisionType.REQUEST_EVALUATION)
    
    def request_id_evaluation(self, current_state: str) -> str:
        """
        请求本我进行评估
        
        Args:
            current_state: 当前状态描述
            
        Returns:
            str: 发给本我的评估请求
        """
        message = f"""需要本我评估当前是否达成目标：

当前状态：
{current_state}

请生成一个发给本我的评估请求，要求本我：
1. 观察当前状态
2. 判断目标是否达成
3. 如果未达成，说明还缺少什么

请用自然语言生成评估请求。"""

        result = self.chat_sync(message)
        return result.return_value
    
    def generate_observation_instruction(self, thinking_result: str) -> str:
        """
        生成观察指令
        
        Args:
            thinking_result: 思考和分析的结果
            
        Returns:
            str: 观察指令
        """
        message = f"""基于以下思考结果，生成一个观察指令：

思考结果：
{thinking_result}

生成一个具体的观察指令，告诉身体需要了解什么信息。指令应该：
1. 明确说明要观察什么
2. 为什么需要这个信息
3. 用自然语言表达，便于身体理解

只返回观察指令，不要其他内容。"""

        result = self.chat_sync(message)
        return result.return_value
    
    def generate_execution_instruction(self, perception_result: str) -> str:
        """
        生成执行指令
        
        Args:
            perception_result: 观察和感知的结果
            
        Returns:
            str: 执行指令
        """
        message = f"""基于以下感知结果，生成一个执行指令：

感知结果：
{perception_result}

生成一个具体的执行指令，告诉身体要做什么。指令应该：
1. 明确说明要执行的操作
2. 为什么需要这个操作
3. 用自然语言表达，便于身体理解和执行

只返回执行指令，不要其他内容。"""

        result = self.chat_sync(message)
        return result.return_value
    
    def handle_execution_error(self, error_info: str, original_instruction: str) -> str:
        """
        处理身体执行错误
        
        Args:
            error_info: 执行失败的错误信息
            original_instruction: 原始的执行指令
            
        Returns:
            str: 错误处理方案
        """
        message = f"""身体执行指令时出现错误，需要分析和处理：

原始指令：
{original_instruction}

错误信息：
{error_info}

请分析错误原因并提出处理方案：
1. 错误是什么原因造成的
2. 是否可以修正指令重新尝试
3. 还是需要改变策略
4. 给出具体的下一步建议

请提供详细的错误分析和处理建议。"""

        result = self.chat_sync(message)
        return result.return_value