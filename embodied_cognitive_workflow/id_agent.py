"""
本我智能体 (Id Agent)

基于具身认知工作流理论的本我智能体实现。
本我智能体负责价值驱动、目标设定和评估监控。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_base import AgentBase, Result
from langchain_core.language_models import BaseChatModel
from typing import Literal


class IdAgent(AgentBase):
    """
    本我智能体 - 价值驱动系统
    
    职责：
    1. 基于用户指令建立价值标准和目标
    2. 响应自我的评估请求，生成观察指令
    3. 评估目标达成情况，决定工作流继续或终止
    """
    
    def __init__(self, llm: BaseChatModel, system_message: str = None):
        default_system = """你是具身认知工作流系统中的本我智能体，负责价值驱动和目标监控。

你的核心职责：
1. 从用户指令中识别核心需求和价值目标
2. 建立实用的成功标准（要宽松合理，不要过于严格）
3. 响应自我的评估请求，生成简单的观察指令
4. 基于观察结果判断目标是否达成，给出明确反馈

工作原则：
- 以用户的核心需求为导向，不追求完美
- 建立简单、实用的成功标准
- 观察指令要简洁明了，易于执行
- 评估要宽松合理，只要核心功能满足就算成功

响应格式：
- 观察指令要简洁（1-2个核心检查项即可）
- 避免复杂的测试要求（如覆盖率、代码质量评分等）
- 评估标准要实用导向，不追求技术完美
- 所有交互都用自然语言，简单易懂
"""
        
        super().__init__(llm, system_message or default_system)
        self.name = "本我智能体"
        self.value_standard = ""
        self.goal_description = ""
        self.task_specification = ""  # 任务规格：包含目标、标准、验证方法
    
    def initialize_value_system(self, instruction: str) -> str:
        """
        基于用户指令初始化价值系统，设定目标和标准
        
        Args:
            instruction: 用户的原始指令
            
        Returns:
            str: 价值系统初始化结果，包括目标和标准
        """
        message = f"""用户给出了以下指令，请从中识别核心需求并建立简单实用的价值标准：

用户指令：
{instruction}

请分析并确定：
1. 用户的核心需求是什么（提取最重要的1-2个目标）
2. 简单的成功标准（只要核心功能满足就行，不追求完美）
3. 基本的验证方式（1-2个简单检查即可）

注意原则：
- 保持简单实用，不要过于严格
- 避免复杂的技术要求
- 重点关注用户的核心需求
- 标准要宽松合理，易于达成

请提供JSON格式的回复：
{{
    "目标描述": "一句话简洁说明",
    "价值标准": "2-3个简单的成功要点",
    "验证方法": "1-2个基本检查"
}}"""

        result = self.chat_sync(message, response_format={"type": "json_object"})
        response = result.return_value
        
        # 保存完整的任务规格到实例变量
        self.task_specification = response
        
        # 解析JSON并保存各个部分到对应属性
        try:
            import json
            response_data = json.loads(response)
            self.goal_description = response_data.get("目标描述", "")
            self.value_standard = response_data.get("价值标准", "")
            
            # 为了保持兼容性，也构造文本格式的响应
            formatted_response = f"目标描述：{self.goal_description}\n价值标准：{self.value_standard}\n验证方法：{response_data.get('验证方法', '')}"
            return formatted_response
        except (json.JSONDecodeError, KeyError) as e:
            # JSON解析失败，回退到原始响应
            # 尝试用原来的文本解析方式
            if "目标描述：" in response:
                self.goal_description = response.split("目标描述：")[1].split("价值标准：")[0].strip()
            if "价值标准：" in response:
                self.value_standard = response.split("价值标准：")[1].split("验证方法：")[0].strip()
            return response
    
    def generate_evaluation_instruction(self, evaluation_request: str) -> str:
        """
        响应自我的评估请求，生成具体的观察指令
        
        Args:
            evaluation_request: 自我发来的评估请求
            
        Returns:
            str: 发给身体的观察指令
        """
        message = f"""收到自我的评估请求，需要生成简单的观察指令：

评估请求：
{evaluation_request}

我的目标：
{self.goal_description}

我的价值标准：
{self.value_standard}

请生成1个简单的观察指令，只检查最核心的功能是否满足。

观察指令要求：
1. 只要1个核心检查项即可
2. 避免复杂的断言或详细验证
3. 实用导向，能运行且基本功能正确即可
4. 用自然语言表达，便于身体执行

只返回观察指令，不要其他解释。"""

        result = self.chat_sync(message)
        return result.return_value
    
    def generate_evaluation_instruction_with_agent(self, evaluation_request: str, agents: list) -> str:
        """
        响应自我的评估请求，生成具体的观察指令，并指定执行的Agent
        
        Args:
            evaluation_request: 自我发来的评估请求
            agents: 可用的Agent列表
            
        Returns:
            str: JSON格式，包含观察指令和指定的Agent
        """
        # 构建Agent信息
        agent_info = ""
        for agent in agents:
            api_spec = getattr(agent, 'api_specification', None) or "通用执行能力"
            agent_info += f"- {agent.name}: {api_spec}\n"
        
        message = f"""收到自我的评估请求，需要生成观察指令并选择合适的Agent执行：

评估请求：
{evaluation_request}

我的目标：
{self.goal_description}

我的价值标准：
{self.value_standard}

可用Agent：
{agent_info}

请：
1. 生成1个简单的观察指令，只检查最核心的功能是否满足
2. 选择最适合执行这个观察任务的Agent

观察指令要求：
- 只要1个核心检查项即可
- 避免复杂的断言或详细验证
- 实用导向，能运行且基本功能正确即可
- 用自然语言表达，便于Agent执行

返回JSON格式：
{{
    "指令": "具体的观察指令",
    "指定Agent": "选择的Agent名称"
}}"""

        result = self.chat_sync(message, response_format={"type": "json_object"})
        return result.return_value
    
    def evaluate_with_context(self, evaluation_request: str, current_state: str) -> str:
        """
        基于当前状态进行评估
        
        Args:
            evaluation_request: 自我的评估请求
            current_state: 工作流当前状态
            
        Returns:
            str: JSON格式的评估结果
        """
        # 直接使用内部评估（基于当前状态）
        return self._internal_evaluation(current_state, evaluation_request)
    
    def evaluate_goal_achievement(self, observation_result: str) -> str:
        """
        基于观察结果评估目标是否达成（外观评估）
        
        Args:
            observation_result: 身体观察和检查的结果
            
        Returns:
            str: JSON格式的评估结果，包含目标是否达成和原因
        """
        message = f"""基于观察结果，评估目标是否达成：

观察结果：
{observation_result}

我的目标：
{self.goal_description}

我的价值标准：
{self.value_standard}

请根据价值标准评估观察结果，判断目标是否达成。

评估原则：
- 宽松评估，只要核心功能基本满足就算成功
- 不追求完美，允许小瑕疵
- 重点关注用户的核心需求是否得到满足
- 如果基本功能实现就设置为true

请返回JSON格式：
{{
    "目标是否达成": true/false,
    "原因": "简要说明原因"
}}"""

        # 使用response_format强制要求JSON格式响应
        result = self.chat_sync(message, response_format={"type": "json_object"})
        response = result.return_value.strip()
        
        # 验证JSON格式（使用response_format后应该已经是有效JSON）
        try:
            import json
            # 尝试解析JSON以验证格式
            json.loads(response)
            return response
        except json.JSONDecodeError:
            # 如果仍然解析失败，构造一个安全的默认响应
            return '{"目标是否达成": false, "原因": "JSON格式错误，无法解析评估结果"}'
    
    def _internal_evaluation(self, current_state: str, evaluation_request: str) -> str:
        """
        基于工作流当前状态进行内观评估，无需外部观察
        
        Args:
            current_state: 工作流当前状态的自然语言描述
            evaluation_request: 自我的评估请求
            
        Returns:
            str: JSON格式的评估结果
        """
        message = f"""基于工作流内部状态进行内观评估：

工作流当前状态：
{current_state}

评估请求：
{evaluation_request}

我的目标：
{self.goal_description}

我的价值标准：
{self.value_standard}

请基于工作流内部状态信息评估目标是否达成，无需进行外部观察和验证。

评估原则：
- 重点关注状态描述中的关键信息
- 检查是否包含任务完成的标志
- 宽松评估，只要核心功能基本满足就算成功
- 优先信任工作流内部的执行结果
- 如果状态显示执行成功且无明显错误，就认为达成

请返回JSON格式：
{{
    "目标是否达成": true/false,
    "原因": "基于内部状态的评估原因"
}}"""

        # 使用response_format强制要求JSON格式响应
        result = self.chat_sync(message, response_format={"type": "json_object"})
        response = result.return_value.strip()
        
        # 验证JSON格式
        try:
            import json
            json.loads(response)
            return response
        except json.JSONDecodeError:
            # 如果解析失败，构造一个安全的默认响应
            return '{"目标是否达成": false, "原因": "内观评估JSON格式错误"}'
    
    
    def get_current_goal(self) -> str:
        """
        获取当前设定的目标描述
        
        Returns:
            str: 目标描述
        """
        return self.goal_description
    
    def get_value_standard(self) -> str:
        """
        获取当前设定的价值标准
        
        Returns:
            str: 价值标准
        """
        return self.value_standard
    
    def reset_goal(self, new_instruction: str) -> str:
        """
        基于新指令重新设定目标和价值标准
        
        Args:
            new_instruction: 新的用户指令或修正指令
            
        Returns:
            str: 重新设定后的目标和标准
        """
        return self.initialize_value_system(new_instruction)
    
    def adjust_value_standard(self, adjustment_description: str) -> str:
        """
        基于执行过程中的发现调整价值标准
        
        Args:
            adjustment_description: 需要调整的原因和方向
            
        Returns:
            str: 调整后的价值标准
        """
        message = f"""需要基于新信息调整价值标准：

当前目标：
{self.goal_description}

当前价值标准：
{self.value_standard}

调整说明：
{adjustment_description}

请调整价值标准，确保：
1. 仍然符合原始目标
2. 更加现实可行
3. 考虑新发现的约束或要求

请提供调整后的价值标准。"""

        result = self.chat_sync(message)
        self.value_standard = result.return_value
        return self.value_standard
    
    def get_task_specification(self) -> str:
        """
        获取完整的任务规格
        
        Returns:
            str: 任务规格，包含目标、标准、验证方法
        """
        return self.task_specification