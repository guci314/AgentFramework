#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态任务添加功能集成测试
验证动态任务添加在真实工作流环境中的完整表现
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime as dt

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CognitiveWorkflow.cognitive_workflow import (
    CognitiveWorkflowEngine, CognitiveTask, TaskPhase, TaskStatus, GlobalState
)
from agent_base import AgentBase, Result


class TestDynamicTaskIntegration(unittest.TestCase):
    """动态任务添加集成测试"""
    
    def setUp(self):
        """集成测试环境设置"""
        # 创建模拟LLM
        self.mock_llm = Mock()
        self.mock_llm.invoke.return_value = Mock(content="模拟LLM响应")
        
        # 创建模拟智能体
        self.mock_agents = {
            'info_collector': Mock(spec=AgentBase),
            'data_analyst': Mock(spec=AgentBase),
            'task_executor': Mock(spec=AgentBase)
        }
        
        # 设置智能体执行结果
        for agent in self.mock_agents.values():
            agent.execute_sync.return_value = Result(
                success=True,
                code="mock_code",
                stdout="模拟执行成功",
                return_value="模拟结果"
            )
        
        # 创建工作流引擎
        self.engine = CognitiveWorkflowEngine(
            llm=self.mock_llm,
            agents=self.mock_agents,
            max_iterations=50,
            enable_auto_recovery=True
        )

    def test_simple_dynamic_task_addition(self):
        """简单动态任务添加测试"""
        # 初始化基础任务
        self.engine.task_list = [
            CognitiveTask(
                id="task_001",
                name="基础任务",
                instruction="执行基础任务",
                agent_name="task_executor",
                instruction_type="execution",
                phase=TaskPhase.EXECUTION,
                expected_output="基础结果",
                precondition="无",
                status=TaskStatus.COMPLETED
            )
        ]
        
        initial_task_count = len(self.engine.task_list)
        
        # 创建动态添加决策
        modification_decision = {
            'action': 'add_tasks',
            'reason': '需要补充数据收集任务',
            'details': {
                'new_tasks': [
                    {
                        'name': '收集补充数据',
                        'instruction': '收集项目所需的补充数据',
                        'agent_name': 'info_collector',
                        'expected_output': '补充数据集',
                        'phase': 'information',
                        'instruction_type': 'information',
                        'precondition': '基础任务已完成'
                    }
                ]
            }
        }
        
        # 应用动态任务添加
        self.engine._apply_plan_modification(modification_decision)
        
        # 验证任务已添加
        self.assertEqual(len(self.engine.task_list), initial_task_count + 1)
        new_task = self.engine.task_list[-1]
        self.assertEqual(new_task.name, '收集补充数据')
        self.assertEqual(new_task.agent_name, 'info_collector')
        self.assertTrue(new_task.id.startswith('dynamic_'))


if __name__ == '__main__':
    unittest.main() 