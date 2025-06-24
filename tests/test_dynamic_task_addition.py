#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态任务添加功能单元测试
测试 CognitiveWorkflowEngine 的动态任务添加相关方法
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
from agent_base import AgentBase


class TestDynamicTaskAddition(unittest.TestCase):
    """动态任务添加功能测试"""
    
    def setUp(self):
        """测试初始化"""
        # 创建模拟LLM
        self.mock_llm = Mock()
        
        # 创建模拟智能体
        self.mock_agents = {
            'test_agent': Mock(spec=AgentBase),
            'info_agent': Mock(spec=AgentBase),
            'exec_agent': Mock(spec=AgentBase)
        }
        
        # 创建工作流引擎
        self.engine = CognitiveWorkflowEngine(
            llm=self.mock_llm,
            agents=self.mock_agents,
            max_iterations=10,
            enable_auto_recovery=True
        )
        
        # 初始化一些基础任务
        self.engine.task_list = [
            CognitiveTask(
                id="task_001",
                name="初始任务",
                instruction="执行初始任务",
                agent_name="test_agent",
                instruction_type="execution",
                phase=TaskPhase.EXECUTION,
                expected_output="初始结果",
                precondition="无"
            )
        ]

    def test_generate_dynamic_task_id(self):
        """测试动态任务ID生成"""
        # 生成ID
        task_id = self.engine._generate_dynamic_task_id()
        
        # 验证格式
        self.assertTrue(task_id.startswith('dynamic_'))
        self.assertIn('_', task_id)
        
        # 验证唯一性
        second_id = self.engine._generate_dynamic_task_id()
        self.assertNotEqual(task_id, second_id)

    def test_validate_new_task_data_valid(self):
        """测试有效任务数据验证"""
        valid_task_data = {
            'name': '测试任务',
            'instruction': '执行测试',
            'agent_name': 'test_agent',
            'expected_output': '测试结果',
            'phase': 'execution',
            'instruction_type': 'execution',
            'precondition': '无特殊要求'
        }
        
        is_valid, errors = self.engine._validate_new_task_data(valid_task_data)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_new_task_data_missing_required_fields(self):
        """测试缺少必填字段的任务数据验证"""
        invalid_task_data = {
            'name': '测试任务',
            # 缺少 instruction, agent_name, expected_output
        }
        
        is_valid, errors = self.engine._validate_new_task_data(invalid_task_data)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('instruction' in error for error in errors))
        self.assertTrue(any('agent_name' in error for error in errors))
        self.assertTrue(any('expected_output' in error for error in errors))

    def test_validate_new_task_data_invalid_agent(self):
        """测试无效智能体的任务数据验证"""
        invalid_task_data = {
            'name': '测试任务',
            'instruction': '执行测试',
            'agent_name': 'nonexistent_agent',  # 不存在的智能体
            'expected_output': '测试结果'
        }
        
        is_valid, errors = self.engine._validate_new_task_data(invalid_task_data)
        
        self.assertFalse(is_valid)
        self.assertTrue(any('智能体' in error and 'nonexistent_agent' in error for error in errors))

    def test_validate_new_task_data_invalid_phase(self):
        """测试无效阶段的任务数据验证"""
        invalid_task_data = {
            'name': '测试任务',
            'instruction': '执行测试',
            'agent_name': 'test_agent',
            'expected_output': '测试结果',
            'phase': 'invalid_phase'  # 无效阶段
        }
        
        is_valid, errors = self.engine._validate_new_task_data(invalid_task_data)
        
        self.assertFalse(is_valid)
        self.assertTrue(any('无效的任务阶段' in error for error in errors))

    def test_create_cognitive_task_from_data(self):
        """测试从数据创建认知任务"""
        task_data = {
            'name': '新任务',
            'instruction': '执行新任务',
            'agent_name': 'test_agent',
            'expected_output': '新结果',
            'phase': 'information',
            'instruction_type': 'information',
            'precondition': '需要完成前置任务'
        }
        
        task = self.engine._create_cognitive_task_from_data(task_data)
        
        self.assertEqual(task.name, '新任务')
        self.assertEqual(task.instruction, '执行新任务')
        self.assertEqual(task.agent_name, 'test_agent')
        self.assertEqual(task.expected_output, '新结果')
        self.assertEqual(task.phase, TaskPhase.INFORMATION)
        self.assertEqual(task.instruction_type, 'information')
        self.assertEqual(task.precondition, '需要完成前置任务')
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertTrue(task.id.startswith('dynamic_'))

    def test_add_dynamic_tasks_success(self):
        """测试成功添加动态任务"""
        modification_decision = {
            'action': 'add_tasks',
            'reason': '需要收集更多信息',
            'details': {
                'new_tasks': [
                    {
                        'name': '收集用户反馈',
                        'instruction': '通过问卷调查收集用户对产品的反馈',
                        'agent_name': 'info_agent',
                        'expected_output': '用户反馈数据',
                        'phase': 'information',
                        'instruction_type': 'information',
                        'precondition': '产品已发布'
                    }
                ]
            }
        }
        
        initial_task_count = len(self.engine.task_list)
        success = self.engine._add_dynamic_tasks(modification_decision)
        
        self.assertTrue(success)
        self.assertEqual(len(self.engine.task_list), initial_task_count + 1)

    def test_add_dynamic_tasks_empty_data(self):
        """测试空任务数据的动态添加"""
        modification_decision = {
            'action': 'add_tasks',
            'reason': '测试空数据',
            'details': {
                'new_tasks': []
            }
        }
        
        initial_task_count = len(self.engine.task_list)
        success = self.engine._add_dynamic_tasks(modification_decision)
        
        self.assertFalse(success)
        self.assertEqual(len(self.engine.task_list), initial_task_count)

    def test_add_dynamic_tasks_invalid_data(self):
        """测试无效任务数据的动态添加"""
        modification_decision = {
            'action': 'add_tasks',
            'reason': '测试无效数据',
            'details': {
                'new_tasks': [
                    {
                        'name': '无效任务',
                        # 缺少必填字段
                        'agent_name': 'nonexistent_agent'
                    }
                ]
            }
        }
        
        initial_task_count = len(self.engine.task_list)
        success = self.engine._add_dynamic_tasks(modification_decision)
        
        self.assertFalse(success)
        self.assertEqual(len(self.engine.task_list), initial_task_count)

    def test_add_dynamic_tasks_partial_success(self):
        """测试部分成功的动态任务添加"""
        modification_decision = {
            'action': 'add_tasks',
            'reason': '测试部分成功',
            'details': {
                'new_tasks': [
                    {
                        'name': '有效任务',
                        'instruction': '执行有效任务',
                        'agent_name': 'test_agent',
                        'expected_output': '有效结果'
                    },
                    {
                        'name': '无效任务',
                        # 缺少必填字段
                    }
                ]
            }
        }
        
        initial_task_count = len(self.engine.task_list)
        success = self.engine._add_dynamic_tasks(modification_decision)
        
        self.assertTrue(success)  # 有一个任务成功就返回True
        self.assertEqual(len(self.engine.task_list), initial_task_count + 1)

    def test_apply_plan_modification_add_tasks(self):
        """测试计划修正中的任务添加"""
        modification_decision = {
            'action': 'add_tasks',
            'reason': '需要补充信息收集任务',
            'details': {
                'new_tasks': [
                    {
                        'name': '补充任务',
                        'instruction': '补充缺失的信息',
                        'agent_name': 'info_agent',
                        'expected_output': '补充信息'
                    }
                ]
            }
        }
        
        initial_task_count = len(self.engine.task_list)
        
        # 调用计划修正方法
        self.engine._apply_plan_modification(modification_decision)
        
        # 验证任务已添加
        self.assertEqual(len(self.engine.task_list), initial_task_count + 1)
        self.assertEqual(self.engine.task_list[-1].name, '补充任务')


if __name__ == '__main__':
    unittest.main() 