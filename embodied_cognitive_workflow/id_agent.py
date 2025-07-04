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
2. 建立清晰的成功标准和评估准则
3. 响应自我的评估请求，主动观察目标状态
4. 基于观察结果判断目标是否达成，给出明确反馈

工作原则：
- 始终以用户的真实需求为导向
- 建立明确、可验证的成功标准
- 主动监控目标达成情况
- 给出明确的评估结论和建议

响应格式：
- 评估结论只能是："工作流结束"或具体的未满足原因
- 观察指令要明确具体，便于身体执行
- 所有交互都用自然语言，清晰易懂
"""
        
        super().__init__(llm, system_message or default_system)
        self.name = "本我智能体"
        self.value_standard = ""
        self.goal_description = ""
    
    def initialize_value_system(self, instruction: str) -> str:
        """
        基于用户指令初始化价值系统，设定目标和标准
        
        Args:
            instruction: 用户的原始指令
            
        Returns:
            str: 价值系统初始化结果，包括目标和标准
        """
        message = f"""用户给出了以下指令，请从中识别核心需求并建立价值标准：

用户指令：
{instruction}

请分析并确定：
1. 用户的核心需求是什么
2. 成功完成任务的具体标准是什么
3. 如何判断目标是否真正达成
4. 可能的验证方式

请提供：
- 目标描述：简洁明确的目标陈述
- 价值标准：具体的成功评判准则
- 验证方法：如何确认目标达成

格式如下：
目标描述：[具体目标]
价值标准：[成功标准列表]
验证方法：[验证方式]"""

        result = self.chat_sync(message)
        response = result.return_value
        
        # 保存价值标准和目标描述到实例变量
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
        message = f"""收到自我的评估请求，需要生成观察指令来了解当前状态：

评估请求：
{evaluation_request}

我的目标：
{self.goal_description}

我的价值标准：
{self.value_standard}

请生成一个具体的观察指令，告诉身体需要检查什么信息来判断目标是否达成。

观察指令应该：
1. 明确说明要观察的具体内容
2. 为什么需要这些信息
3. 如何获取这些信息
4. 用自然语言表达，便于身体理解执行

只返回观察指令，不要其他内容。"""

        result = self.chat_sync(message)
        return result.return_value
    
    def evaluate_goal_achievement(self, observation_result: str) -> str:
        """
        基于观察结果评估目标是否达成
        
        Args:
            observation_result: 身体观察和检查的结果
            
        Returns:
            str: 评估结论 - "工作流结束"或具体的未满足原因
        """
        message = f"""基于观察结果，评估目标是否达成：

观察结果：
{observation_result}

我的目标：
{self.goal_description}

我的价值标准：
{self.value_standard}

请根据价值标准仔细评估观察结果，判断目标是否真正达成。

如果目标已经达成，请回答："工作流结束"

如果目标未达成，请说明具体的原因：
- 缺少什么关键要素
- 哪些标准没有满足
- 需要什么补充工作

只返回评估结论，要么是"工作流结束"，要么是具体的未满足原因。"""

        result = self.chat_sync(message)
        response = result.return_value.strip()
        
        return response
    
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