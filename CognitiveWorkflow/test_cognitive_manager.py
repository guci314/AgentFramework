# -*- coding: utf-8 -*-
"""
CognitiveManager 测试用例

专门测试重构后的 CognitiveManager 类的功能：
1. 统一任务管理
2. 决策制定
3. 状态评估
4. 动态任务生成

作者：Claude
日期：2024-12-24
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import logging
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List
from datetime import datetime as dt

from agent_base import Result
from pythonTask import Agent
from CognitiveWorkflow.cognitive_workflow import (
    CognitiveManager, StateConditionChecker, CognitiveTask, 
    TaskPhase, TaskStatus, GlobalState
)

# 配置测试日志
logging.basicConfig(level=logging.WARNING)

class TestCognitiveManager(unittest.TestCase):
    """测试 CognitiveManager 核心功能"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.mock_agents = {
            'coder': Mock(spec=Agent),
            'tester': Mock(spec=Agent),
            'analyst': Mock(spec=Agent)
        }
        self.mock_condition_checker = Mock(spec=StateConditionChecker)
        
        # 创建 CognitiveManager 实例
        self.manager = CognitiveManager(
            llm=self.mock_llm,
            available_agents=self.mock_agents,
            condition_checker=self.mock_condition_checker,
            interactive_mode=False
        )
        
        # 创建测试用的 GlobalState
        self.global_state = GlobalState(current_state="测试状态")
        
    def test_manager_initialization(self):
        """测试管理者初始化"""
        self.assertIsNotNone(self.manager.llm)
        self.assertIsNotNone(self.manager.available_agents)
        self.assertIsNotNone(self.manager.condition_checker)
        self.assertEqual(self.manager.interactive_mode, False)
        self.assertEqual(len(self.manager.decision_history), 0)
        
        # 检查统计信息初始化
        stats = self.manager.get_management_statistics()
        self.assertEqual(stats['tasks_generated'], 0)
        self.assertEqual(stats['decisions_made'], 0)
        self.assertEqual(stats['recovery_attempts'], 0)
        self.assertEqual(stats['dynamic_tasks_added'], 0)
        
    def test_generate_initial_tasks(self):
        """测试初始任务生成"""
        # 模拟 LLM 返回
        mock_response = Mock()
        mock_response.content = '''
        {
            "tasks": [
                {
                    "id": "collect_1",
                    "name": "需求收集",
                    "instruction": "收集项目需求",
                    "agent_name": "analyst",
                    "instruction_type": "information",
                    "phase": "information",
                    "expected_output": "需求文档",
                    "precondition": "项目启动"
                }
            ]
        }
        '''
        self.mock_llm.invoke.return_value = mock_response
        
        # 调用方法
        tasks = self.manager.generate_initial_tasks("创建项目", {"type": "web"})
        
        # 验证结果
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].name, "需求收集")
        self.assertEqual(tasks[0].agent_name, "analyst")
        self.assertEqual(tasks[0].phase, TaskPhase.INFORMATION)
        
        # 验证统计信息更新
        stats = self.manager.get_management_statistics()
        self.assertEqual(stats['tasks_generated'], 1)
        
    def test_generate_recovery_tasks(self):
        """测试修复任务生成"""
        # 创建失败任务
        failed_task = CognitiveTask(
            id="failed_1",
            name="失败任务",
            instruction="测试指令",
            agent_name="coder",
            instruction_type="execution",
            phase=TaskPhase.EXECUTION,
            expected_output="输出",
            precondition="前提"
        )
        
        # 调用方法
        recovery_tasks = self.manager.generate_recovery_tasks(
            failed_task, "错误信息", self.global_state
        )
        
        # 验证结果
        self.assertEqual(len(recovery_tasks), 1)
        self.assertTrue(recovery_tasks[0].id.startswith("retry_"))
        self.assertIn("重试", recovery_tasks[0].name)
        
        # 验证统计信息更新
        stats = self.manager.get_management_statistics()
        self.assertEqual(stats['recovery_attempts'], 1)
        
    def test_find_executable_tasks(self):
        """测试可执行任务查找"""
        # 创建测试任务
        tasks = [
            CognitiveTask(
                id="task_1", name="任务1", instruction="指令1",
                agent_name="coder", instruction_type="execution",
                phase=TaskPhase.EXECUTION, expected_output="输出1",
                precondition="前提1", status=TaskStatus.PENDING
            ),
            CognitiveTask(
                id="task_2", name="任务2", instruction="指令2",
                agent_name="tester", instruction_type="execution",
                phase=TaskPhase.VERIFICATION, expected_output="输出2",
                precondition="前提2", status=TaskStatus.PENDING
            )
        ]
        
        # 模拟条件检查器返回
        self.mock_condition_checker.check_precondition_satisfied.side_effect = [
            (True, 0.8, "满足"),
            (False, 0.3, "不满足")
        ]
        
        # 调用方法
        executable_tasks = self.manager.find_executable_tasks(tasks, self.global_state)
        
        # 验证结果
        self.assertEqual(len(executable_tasks), 1)
        self.assertEqual(executable_tasks[0][0].id, "task_1")
        self.assertEqual(executable_tasks[0][1], 0.8)
        
    def test_select_next_task(self):
        """测试下一任务选择"""
        # 创建可执行任务列表
        task = CognitiveTask(
            id="task_1", name="任务1", instruction="指令1",
            agent_name="coder", instruction_type="execution",
            phase=TaskPhase.EXECUTION, expected_output="输出1",
            precondition="前提1"
        )
        executable_tasks = [(task, 0.8)]
        
        # 测试单个任务情况
        selected_task = self.manager.select_next_task(
            executable_tasks, self.global_state, []
        )
        
        # 验证结果
        self.assertEqual(selected_task.id, "task_1")
        
    def test_evaluate_workflow_status(self):
        """测试工作流状态评估"""
        # 创建不同状态的任务
        tasks = [
            CognitiveTask(
                id="task_1", name="完成任务", instruction="指令1",
                agent_name="coder", instruction_type="execution",
                phase=TaskPhase.EXECUTION, expected_output="输出1",
                precondition="前提1", status=TaskStatus.COMPLETED
            ),
            CognitiveTask(
                id="task_2", name="待执行任务", instruction="指令2",
                agent_name="tester", instruction_type="execution",
                phase=TaskPhase.VERIFICATION, expected_output="输出2",
                precondition="前提2", status=TaskStatus.PENDING
            )
        ]
        
        # 模拟可执行任务查找
        self.manager.find_executable_tasks = Mock(return_value=[(tasks[1], 0.8)])
        
        # 调用方法
        evaluation = self.manager.evaluate_workflow_status(tasks, self.global_state)
        
        # 验证结果
        self.assertEqual(evaluation['total_tasks'], 2)
        self.assertEqual(evaluation['completed_tasks'], 1)
        self.assertEqual(evaluation['pending_tasks'], 1)
        self.assertEqual(evaluation['completion_rate'], 0.5)
        self.assertEqual(evaluation['workflow_status'], 'active')
        self.assertEqual(evaluation['recommendation'], 'continue_execution')
        
    def test_analyze_modification_needs(self):
        """测试修正需求分析"""
        # 创建测试任务
        tasks = [
            CognitiveTask(
                id="task_1", name="任务1", instruction="指令1",
                agent_name="coder", instruction_type="execution",
                phase=TaskPhase.EXECUTION, expected_output="输出1",
                precondition="前提1", status=TaskStatus.PENDING
            )
        ]
        
        # 模拟 LLM 返回
        mock_response = Mock()
        mock_response.content = '''
        {
            "action": "add_tasks",
            "reason": "需要添加前置任务",
            "details": "添加环境准备任务"
        }
        '''
        self.mock_llm.invoke.return_value = mock_response
        
        # 调用方法
        decision = self.manager.analyze_modification_needs(
            tasks, self.global_state, None
        )
        
        # 验证结果
        self.assertEqual(decision['action'], 'add_tasks')
        self.assertEqual(decision['reason'], '需要添加前置任务')
        self.assertIn('timestamp', decision)
        
        # 验证决策历史记录
        self.assertEqual(len(self.manager.decision_history), 1)
        
    def test_generate_dynamic_tasks(self):
        """测试动态任务生成"""
        # 准备修正上下文
        modification_context = {
            'details': {
                'new_tasks': [
                    {
                        'name': '动态任务',
                        'instruction': '动态生成的任务',
                        'agent_name': 'coder',
                        'expected_output': '动态输出',
                        'instruction_type': 'execution',
                        'phase': 'execution',
                        'precondition': '无'
                    }
                ]
            }
        }
        
        # 调用方法
        dynamic_tasks = self.manager.generate_dynamic_tasks(
            modification_context, self.global_state
        )
        
        # 验证结果
        self.assertEqual(len(dynamic_tasks), 1)
        self.assertEqual(dynamic_tasks[0].name, '动态任务')
        self.assertEqual(dynamic_tasks[0].agent_name, 'coder')
        
        # 验证统计信息更新
        stats = self.manager.get_management_statistics()
        self.assertEqual(stats['dynamic_tasks_added'], 1)
        
    def test_build_agent_info_string(self):
        """测试智能体信息字符串构建"""
        # 设置智能体规格
        self.mock_agents['coder'].api_specification = "编码专家"
        self.mock_agents['tester'].name = "测试者"
        
        # 调用私有方法
        agent_info = self.manager._build_agent_info_string()
        
        # 验证结果
        self.assertIn("coder: 编码专家", agent_info)
        self.assertIn("tester (测试者)", agent_info)
        self.assertIn("analyst", agent_info)
        
    def test_validate_new_task_data(self):
        """测试新任务数据验证"""
        # 测试有效数据
        valid_data = {
            'name': '测试任务',
            'instruction': '测试指令',
            'agent_name': 'coder',
            'expected_output': '测试输出'
        }
        
        is_valid, errors = self.manager._validate_new_task_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 测试无效数据
        invalid_data = {
            'name': '测试任务',
            # 缺少必填字段
            'agent_name': 'nonexistent_agent'  # 不存在的智能体
        }
        
        is_valid, errors = self.manager._validate_new_task_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
        
    def test_record_decision(self):
        """测试决策记录"""
        # 记录决策
        decision_data = {'test': 'data'}
        self.manager._record_decision('test_decision', decision_data)
        
        # 验证记录
        self.assertEqual(len(self.manager.decision_history), 1)
        
        decision = self.manager.decision_history[0]
        self.assertEqual(decision['decision_type'], 'test_decision')
        self.assertEqual(decision['data'], decision_data)
        self.assertIn('timestamp', decision)
        
        # 验证统计信息更新
        stats = self.manager.get_management_statistics()
        self.assertEqual(stats['decisions_made'], 1)

if __name__ == "__main__":
    unittest.main()