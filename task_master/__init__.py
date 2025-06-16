"""
Task Master AI 集成模块

提供与 Task Master AI 的完整集成功能，包括：
- MCP 工具封装
- 数据格式转换
- 配置管理
- 监控和分析
"""

from .client import TaskMasterClient
from .data_mapper import TaskMasterDataMapper
from .config import TaskMasterConfig

__all__ = [
    'TaskMasterClient',
    'TaskMasterDataMapper', 
    'TaskMasterConfig'
]

__version__ = "0.1.0"