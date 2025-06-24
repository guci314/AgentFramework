# -*- coding: utf-8 -*-
"""
工作流引擎层 - Engine Layer

包含产生式规则工作流引擎的实现，作为整个系统的统一入口点。
提供工作流执行的控制接口和状态监控功能。
"""

from .production_rule_workflow_engine import ProductionRuleWorkflowEngine

__all__ = [
    "ProductionRuleWorkflowEngine"
]