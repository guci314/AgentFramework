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
        
        # 保存完整的任务规格到实例变量
        self.task_specification = response
        
        # 解析并保存各个部分到对应属性
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

请生成1-2个简单的观察指令，重点检查核心功能是否满足。

观察指令要求：
1. 简洁明了，只检查最核心的1-2项
2. 避免复杂的测试要求（如覆盖率、代码质量等）
3. 实用导向，能运行且基本功能正确即可
4. 用自然语言表达，便于身体执行

只返回观察指令，不要其他内容。"""

        result = self.chat_sync(message)
        return result.return_value
    
    def evaluate_goal_achievement(self, observation_result: str) -> str:
        """
        基于观察结果评估目标是否达成
        
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

评估标准：
- 只要核心功能满足就算成功，不追求完美
- 如果目标已经达成，设置"目标是否达成"为true
- 如果目标未达成，设置"目标是否达成"为false

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