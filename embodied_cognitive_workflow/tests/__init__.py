"""
具身认知工作流测试套件

包含具身认知工作流系统的所有单元测试和集成测试。
"""

# 测试模块导入
from . import test_embodied_cognitive_workflow
from . import test_ego_agent
from . import test_id_agent
from . import test_workflow_integration

__all__ = [
    'test_embodied_cognitive_workflow',
    'test_ego_agent',
    'test_id_agent',
    'test_workflow_integration'
]