"""
决策类型定义模块

包含决策相关的枚举和数据类定义，避免循环导入问题。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# 前向引用，避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from agent_base import AgentBase


class DecisionType(Enum):
    """决策类型枚举"""
    REQUEST_EVALUATION = "请求评估"
    JUDGMENT_FAILED = "判断失败"
    EXECUTE_INSTRUCTION = "执行指令"


@dataclass
class Decision:
    """
    决策结果类，封装Ego的决策信息
    
    Attributes:
        decision_type: 决策类型 (执行指令/请求评估/判断失败)
        agent: 执行者Agent实例（仅在执行指令时需要）
        instruction: 执行指令内容（仅在执行指令时需要）
    """
    decision_type: DecisionType
    agent: Optional['AgentBase'] = None
    instruction: Optional[str] = None