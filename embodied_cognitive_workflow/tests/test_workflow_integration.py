#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
具身认知工作流集成测试

测试完整的工作流系统集成场景：
1. 端到端工作流执行
2. 多轮认知循环
3. 目标达成流程
4. 错误恢复机制
5. 复杂任务场景
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_cognitive_workflow.embodied_cognitive_workflow import (
    CognitiveAgent, WorkflowContext, WorkflowStatus,
    DecisionType, CycleOutcome, create_cognitive_agent,
    execute_cognitive_task
)
from embodied_cognitive_workflow.ego_agent import EgoAgent
from embodied_cognitive_workflow.id_agent import IdAgent
from python_core import Agent
from agent_base import Result


class TestEndToEndWorkflow(unittest.TestCase):
    """测试端到端工作流执行"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_simple_task_completion(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试简单任务完成流程"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 配置模拟行为 - 简单的一轮完成
        mock_id.initialize_value_system.return_value = "目标：打印Hello World"
        mock_id.get_task_specification.return_value = "打印Hello World到控制台"
        
        # 自我分析和决策
        mock_ego.analyze_current_state.return_value = "需要执行打印任务"
        mock_ego.decide_next_action.return_value = "继续循环"
        mock_ego.chat_sync.return_value = Result(
            True, "", '{"行动类型": "执行", "理由": "执行打印"}', None, ""
        )
        mock_ego.generate_execution_instruction.return_value = "print('Hello World')"
        
        # 身体执行
        mock_body.execute_sync.side_effect = [
            Result(True, "Hello World\n", "", None, ""),  # 执行打印
            Result(True, "", "看到输出: Hello World", None, "")  # 检查结果
        ]
        mock_body.chat_sync.return_value = Result(
            True, "", "成功打印了Hello World", None, ""
        )
        
        # 第二轮：请求评估
        mock_ego.analyze_current_state.return_value = "已执行打印"
        mock_ego.decide_next_action.return_value = "请求评估"
        mock_ego.request_id_evaluation.return_value = "请检查是否成功打印"
        
        # 本我评估
        mock_id.generate_evaluation_instruction.return_value = "检查控制台输出"
        mock_id.evaluate_goal_achievement.return_value = (
            '{"目标是否达成": true, "原因": "成功打印Hello World"}'
        )
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("打印Hello World")
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertIn("成功", result.error)
        self.assertEqual(workflow._status, WorkflowStatus.SUCCESS)
        
        # 验证调用序列
        self.assertEqual(mock_ego.analyze_current_state.call_count, 2)
        self.assertEqual(mock_ego.decide_next_action.call_count, 2)
        mock_id.evaluate_goal_achievement.assert_called_once()
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_multi_cycle_task(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试多轮循环任务"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 配置模拟行为 - 需要三轮完成
        mock_id.initialize_value_system.return_value = "目标：创建并测试计算器"
        mock_id.get_task_specification.return_value = "实现加法功能的计算器"
        
        # 配置三轮循环的行为
        mock_ego.analyze_current_state.side_effect = [
            "开始任务",
            "已创建计算器类",
            "已实现加法功能",
            "功能实现完成"
        ]
        
        mock_ego.decide_next_action.side_effect = [
            "继续循环",  # 第1轮：创建类
            "继续循环",  # 第2轮：实现功能
            "继续循环",  # 第3轮：测试
            "请求评估"   # 第4轮：评估
        ]
        
        # 模拟执行响应
        mock_ego.chat_sync.side_effect = [
            Result(True, "", '{"行动类型": "执行", "理由": "创建类"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "实现功能"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "测试功能"}', None, ""),
        ]
        
        mock_ego.generate_execution_instruction.side_effect = [
            "class Calculator: pass",
            "def add(self, a, b): return a + b",
            "calc = Calculator(); print(calc.add(2, 3))"
        ]
        
        mock_body.execute_sync.side_effect = [
            Result(True, "", "类创建成功", None, ""),
            Result(True, "", "方法添加成功", None, ""),
            Result(True, "5\n", "测试通过", None, ""),
            Result(True, "", "计算器功能正常", None, "")
        ]
        
        # 评估阶段
        mock_ego.request_id_evaluation.return_value = "请评估计算器功能"
        mock_id.generate_evaluation_instruction.return_value = "测试加法: 2+3=?"
        mock_id.evaluate_goal_achievement.return_value = (
            '{"目标是否达成": true, "原因": "加法功能正常"}'
        )
        mock_body.chat_sync.return_value = Result(True, "", "计算器完成", None, "")
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("创建计算器")
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.SUCCESS)
        self.assertEqual(workflow.current_cycle_count, 4)
        
        # 验证执行了多轮
        self.assertEqual(mock_ego.generate_execution_instruction.call_count, 3)


class TestComplexScenarios(unittest.TestCase):
    """测试复杂场景"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_error_recovery_workflow(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试错误恢复工作流"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 初始化
        mock_id.initialize_value_system.return_value = "目标：读取文件内容"
        mock_id.get_task_specification.return_value = "读取config.txt文件"
        
        # 第一轮：尝试读取文件（失败）
        mock_ego.analyze_current_state.side_effect = [
            "开始读取文件",
            "文件不存在，需要创建",
            "文件已创建，再次读取",
            "成功读取文件"
        ]
        
        mock_ego.decide_next_action.side_effect = [
            "继续循环",  # 尝试读取
            "继续循环",  # 创建文件
            "继续循环",  # 再次读取
            "请求评估"   # 评估结果
        ]
        
        # 执行响应
        mock_ego.chat_sync.side_effect = [
            Result(True, "", '{"行动类型": "执行", "理由": "读取文件"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "创建文件"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "重新读取"}', None, ""),
        ]
        
        mock_ego.generate_execution_instruction.side_effect = [
            "with open('config.txt', 'r') as f: content = f.read()",
            "with open('config.txt', 'w') as f: f.write('test config')",
            "with open('config.txt', 'r') as f: print(f.read())"
        ]
        
        # 第一次执行失败，后续成功
        mock_body.execute_sync.side_effect = [
            Result(False, "", "", None, "FileNotFoundError: config.txt"),
            Result(True, "", "文件创建成功", None, ""),
            Result(True, "test config\n", "", None, ""),
            Result(True, "", "文件内容: test config", None, "")
        ]
        
        # 处理错误
        mock_ego.handle_execution_error.return_value = "需要先创建文件"
        
        # 评估
        mock_ego.request_id_evaluation.return_value = "验证文件读取"
        mock_id.generate_evaluation_instruction.return_value = "查看文件内容"
        mock_id.evaluate_goal_achievement.return_value = (
            '{"目标是否达成": true, "原因": "成功读取文件内容"}'
        )
        mock_body.chat_sync.return_value = Result(True, "", "任务完成", None, "")
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("读取config.txt文件")
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.SUCCESS)
        
        # 验证错误处理被调用
        mock_ego.handle_execution_error.assert_called_once()
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_dynamic_goal_adjustment(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试动态目标调整"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 初始化
        mock_id.initialize_value_system.return_value = "目标：创建Web服务器"
        mock_id.get_task_specification.return_value = "HTTP服务器，支持GET请求"
        mock_id.get_current_goal.return_value = "创建Web服务器"
        mock_id.get_value_standard.return_value = "支持GET请求"
        
        # 模拟执行过程中的观察和决策
        cycle_count = 0
        
        def analyze_state_side_effect(context):
            nonlocal cycle_count
            cycle_count += 1
            if cycle_count == 1:
                return "开始创建服务器"
            elif cycle_count == 2:
                return "基础服务器已创建"
            elif cycle_count == 3:
                return "GET请求功能已实现"
            else:
                return "所有功能完成"
        
        mock_ego.analyze_current_state.side_effect = analyze_state_side_effect
        
        # 决策逻辑
        mock_ego.decide_next_action.side_effect = [
            "继续循环",
            "继续循环", 
            "请求评估"
        ]
        
        # 观察和执行混合
        mock_ego.chat_sync.side_effect = [
            Result(True, "", '{"行动类型": "观察", "理由": "了解需求"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "创建服务器"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "实现GET"}', None, ""),
        ]
        
        mock_ego.generate_observation_instruction.return_value = "检查Flask是否已安装"
        mock_ego.generate_execution_instruction.side_effect = [
            "from flask import Flask; app = Flask(__name__)",
            "@app.route('/'); def index(): return 'Hello'"
        ]
        
        mock_body.execute_sync.side_effect = [
            Result(True, "", "Flask已安装", None, ""),
            Result(True, "", "Flask应用创建成功", None, ""),
            Result(True, "", "路由添加成功", None, ""),
            Result(True, "", "服务器可以处理GET请求", None, "")
        ]
        
        # 评估阶段
        mock_ego.request_id_evaluation.return_value = "验证GET请求功能"
        mock_id.generate_evaluation_instruction.return_value = "测试GET /"
        mock_id.evaluate_goal_achievement.return_value = (
            '{"目标是否达成": true, "原因": "GET请求功能正常"}'
        )
        mock_body.chat_sync.return_value = Result(True, "", "Web服务器完成", None, "")
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("创建支持GET请求的Web服务器")
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.SUCCESS)
        
        # 验证观察和执行的混合使用
        mock_ego.generate_observation_instruction.assert_called_once()
        self.assertEqual(mock_ego.generate_execution_instruction.call_count, 2)


class TestFailureScenarios(unittest.TestCase):
    """测试失败场景"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_judgment_failed_scenario(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试判断失败场景"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 初始化
        mock_id.initialize_value_system.return_value = "目标：实现量子计算模拟器"
        mock_id.get_task_specification.return_value = "完整的量子计算模拟"
        
        # 自我分析后判断任务不可行
        mock_ego.analyze_current_state.return_value = "任务复杂度超出能力范围"
        mock_ego.decide_next_action.return_value = "判断失败"
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("实现量子计算模拟器")
        
        # 验证结果
        self.assertFalse(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.FAILED)
        self.assertIn("无法达成", result.error)
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_timeout_scenario(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试超时场景"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 设置较小的最大循环次数
        workflow = CognitiveAgent(
            llm=self.mock_llm, 
            verbose=False,
            max_cycles=3
        )
        
        # 初始化
        mock_id.initialize_value_system.return_value = "目标：永远不会完成的任务"
        mock_id.get_task_specification.return_value = "无限循环任务"
        
        # 自我总是决定继续循环
        mock_ego.analyze_current_state.return_value = "还在进行中"
        mock_ego.decide_next_action.return_value = "继续循环"
        
        # 模拟执行
        mock_ego.chat_sync.return_value = Result(
            True, "", '{"行动类型": "执行", "理由": "继续"}', None, ""
        )
        mock_ego.generate_execution_instruction.return_value = "继续执行"
        mock_body.execute_sync.return_value = Result(True, "", "执行中", None, "")
        
        # 执行工作流
        result = workflow.execute_cognitive_cycle("无限任务")
        
        # 验证结果
        self.assertFalse(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.TIMEOUT)
        self.assertIn("超时", result.error)
        self.assertEqual(workflow.current_cycle_count, 3)
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_exception_handling(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试异常处理"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 初始化正常
        mock_id.initialize_value_system.return_value = "目标：测试任务"
        mock_id.get_task_specification.return_value = "测试"
        
        # 在执行过程中抛出异常
        mock_ego.analyze_current_state.side_effect = Exception("模拟的异常")
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("测试任务")
        
        # 验证结果
        self.assertFalse(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.EXCEPTION)
        self.assertIn("模拟的异常", result.error)


class TestRealWorldScenarios(unittest.TestCase):
    """测试真实世界场景"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')  
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_data_analysis_workflow(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试数据分析工作流"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 初始化数据分析任务
        mock_id.initialize_value_system.return_value = (
            "目标：分析CSV数据并生成统计报告"
        )
        mock_id.get_task_specification.return_value = (
            "读取数据，计算均值、中位数，生成可视化"
        )
        
        # 模拟多步骤数据分析流程
        analysis_steps = [
            ("需要导入pandas", "观察", "import pandas as pd", "pandas已导入"),
            ("需要读取数据", "执行", "df = pd.read_csv('data.csv')", "数据已加载"),
            ("需要计算统计", "执行", "mean = df.mean(); median = df.median()", "统计完成"),
            ("需要生成图表", "执行", "df.plot(); plt.savefig('report.png')", "图表已生成"),
            ("任务似乎完成", "请求评估", None, None)
        ]
        
        step_index = 0
        
        def analyze_state_effect(context):
            nonlocal step_index
            if step_index < len(analysis_steps):
                result = analysis_steps[step_index][0]
                return result
            return "分析完成"
        
        def decide_action_effect(state):
            nonlocal step_index
            if step_index < len(analysis_steps):
                result = analysis_steps[step_index][1]
                if result == "请求评估":
                    return "请求评估"
                step_index += 1
                return "继续循环"
            return "请求评估"
        
        mock_ego.analyze_current_state.side_effect = analyze_state_effect
        mock_ego.decide_next_action.side_effect = decide_action_effect
        
        # 配置执行响应
        execution_responses = []
        for step in analysis_steps[:-1]:
            if step[1] == "观察":
                execution_responses.append(
                    Result(True, "", f'{{"行动类型": "观察", "理由": "{step[0]}"}}', None, "")
                )
            else:
                execution_responses.append(
                    Result(True, "", f'{{"行动类型": "执行", "理由": "{step[0]}"}}', None, "")
                )
        
        mock_ego.chat_sync.side_effect = execution_responses
        
        # 配置指令生成
        mock_ego.generate_observation_instruction.return_value = analysis_steps[0][2]
        mock_ego.generate_execution_instruction.side_effect = [
            step[2] for step in analysis_steps[1:-1] if step[1] == "执行"
        ]
        
        # 配置执行结果
        mock_body.execute_sync.side_effect = [
            Result(True, "", step[3], None, "") for step in analysis_steps[:-1]
        ] + [Result(True, "", "统计报告和图表都已生成", None, "")]
        
        # 配置评估
        mock_ego.request_id_evaluation.return_value = "验证数据分析结果"
        mock_id.generate_evaluation_instruction.return_value = "检查报告文件是否存在"
        mock_id.evaluate_goal_achievement.return_value = (
            '{"目标是否达成": true, "原因": "数据分析和可视化完成"}'
        )
        mock_body.chat_sync.return_value = Result(
            True, "", "数据分析任务成功完成", None, ""
        )
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("分析CSV数据并生成报告")
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.SUCCESS)
        
        # 验证执行了观察和执行的组合
        mock_ego.generate_observation_instruction.assert_called()
        mock_ego.generate_execution_instruction.assert_called()
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_api_development_workflow(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试API开发工作流"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 初始化API开发任务
        mock_id.initialize_value_system.return_value = "目标：创建RESTful API"
        mock_id.get_task_specification.return_value = (
            "实现用户注册和登录API端点"
        )
        mock_id.get_current_goal.return_value = "创建RESTful API"
        mock_id.get_value_standard.return_value = "注册和登录功能正常"
        
        # 模拟API开发步骤
        dev_cycle = 0
        
        def cycle_state_analysis(context):
            nonlocal dev_cycle
            dev_cycle += 1
            
            states = [
                "需要创建Flask应用框架",
                "框架已创建，需要添加用户模型",
                "用户模型已添加，需要实现注册端点",
                "注册端点已实现，需要实现登录端点",
                "所有端点已实现，需要测试"
            ]
            
            if dev_cycle <= len(states):
                return states[dev_cycle - 1]
            return "API开发完成"
        
        mock_ego.analyze_current_state.side_effect = cycle_state_analysis
        
        # 决策：前4轮继续，第5轮请求评估
        mock_ego.decide_next_action.side_effect = [
            "继续循环", "继续循环", "继续循环", "继续循环", "请求评估"
        ]
        
        # 执行指令
        mock_ego.chat_sync.side_effect = [
            Result(True, "", '{"行动类型": "执行", "理由": "创建框架"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "添加模型"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "实现注册"}', None, ""),
            Result(True, "", '{"行动类型": "执行", "理由": "实现登录"}', None, ""),
        ]
        
        mock_ego.generate_execution_instruction.side_effect = [
            "from flask import Flask, request\napp = Flask(__name__)",
            "users = {}  # 简单的内存存储",
            "@app.route('/register', methods=['POST'])\ndef register(): ...",
            "@app.route('/login', methods=['POST'])\ndef login(): ...",
        ]
        
        # 执行结果
        mock_body.execute_sync.side_effect = [
            Result(True, "", "Flask应用创建成功", None, ""),
            Result(True, "", "用户存储已设置", None, ""),
            Result(True, "", "注册端点已添加", None, ""),
            Result(True, "", "登录端点已添加", None, ""),
            Result(True, "", "API测试：注册和登录都正常工作", None, "")
        ]
        
        # 评估配置
        mock_ego.request_id_evaluation.return_value = "验证API功能"
        mock_id.generate_evaluation_instruction.return_value = (
            "测试POST /register和POST /login"
        )
        mock_id.evaluate_goal_achievement.return_value = (
            '{"目标是否达成": true, "原因": "注册和登录API都正常工作"}'
        )
        mock_body.chat_sync.return_value = Result(
            True, "", "RESTful API开发完成", None, ""
        )
        
        # 执行工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("创建用户注册登录的RESTful API")
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.SUCCESS)
        self.assertEqual(workflow.current_cycle_count, 5)
        
        # 验证状态获取
        status = workflow.get_workflow_status()
        self.assertEqual(status["状态"], "成功")
        self.assertEqual(status["目标描述"], "创建RESTful API")


class TestWorkflowFeatures(unittest.TestCase):
    """测试工作流特性"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    def test_knowledge_loading_integration(self):
        """测试知识加载集成"""
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        
        # 模拟组件
        workflow.ego.loadKnowledge = Mock()
        workflow.id_agent.loadKnowledge = Mock()
        workflow.body.loadKnowledge = Mock()
        
        # 加载知识
        knowledge = "Python最佳实践：使用类型提示"
        workflow.load_knowledge(knowledge)
        
        # 验证所有组件都收到知识
        workflow.ego.loadKnowledge.assert_called_with(knowledge)
        workflow.id_agent.loadKnowledge.assert_called_with(knowledge)
        workflow.body.loadKnowledge.assert_called_with(knowledge)
    
    def test_python_module_loading(self):
        """测试Python模块加载"""
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        
        workflow.body.loadPythonModules = Mock()
        
        modules = ['numpy', 'pandas', 'matplotlib']
        workflow.load_python_modules(modules)
        
        workflow.body.loadPythonModules.assert_called_with(modules)
    
    def test_workflow_reset(self):
        """测试工作流重置"""
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        
        # 设置一些状态
        workflow.current_cycle_count = 10
        workflow._set_status(WorkflowStatus.SUCCESS)
        workflow.execution_history.extend(["step1", "step2"])
        
        # 重置
        workflow.reset()
        
        # 验证重置
        self.assertEqual(workflow.current_cycle_count, 0)
        self.assertEqual(workflow._status, WorkflowStatus.NOT_STARTED)
        self.assertEqual(len(workflow.execution_history), 0)
    
    def test_verbose_logging(self):
        """测试详细日志记录"""
        # 创建verbose=True的工作流
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=True)
        
        # 捕获日志输出
        with patch('builtins.print') as mock_print:
            workflow._log("测试日志消息")
            
            # 验证日志被打印
            mock_print.assert_called()
            call_args = mock_print.call_args[0][0]
            self.assertIn("测试日志消息", call_args)
            self.assertIn("[具身认知工作流]", call_args)
    
    def test_workflow_status_properties(self):
        """测试工作流状态属性"""
        workflow = CognitiveAgent(llm=self.mock_llm, verbose=False)
        
        # 测试状态枚举的所有值
        for status in WorkflowStatus:
            workflow._set_status(status)
            self.assertEqual(workflow._status, status)
            self.assertEqual(workflow.workflow_status, status.value)
        
        # 测试循环计数属性
        workflow.current_cycle_count = 42
        self.assertEqual(workflow.current_cycle_count, 42)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便利函数"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    def test_create_workflow_function(self):
        """测试创建工作流便利函数"""
        workflow = create_cognitive_agent(
            self.mock_llm,
            max_cycles=100,
            verbose=False,
            body_config={"name": "test"},
            ego_config={"system_message": "test"},
            id_config={"system_message": "test"}
        )
        
        self.assertIsInstance(workflow, CognitiveAgent)
        self.assertEqual(workflow.max_cycles, 100)
        self.assertFalse(workflow.verbose)
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.CognitiveAgent')
    def test_execute_task_function(self, mock_workflow_class):
        """测试执行任务便利函数"""
        # 模拟工作流
        mock_workflow = Mock()
        mock_workflow.execute_cognitive_cycle.return_value = Result(
            True, "output", "返回值", None, ""
        )
        mock_workflow_class.return_value = mock_workflow
        
        # 执行任务
        result = execute_cognitive_task(
            self.mock_llm,
            "测试任务",
            max_cycles=50,
            verbose=True
        )
        
        # 验证结果
        self.assertTrue(result.success)
        self.assertEqual(result.return_value, "返回值")
        
        # 验证工作流创建参数
        mock_workflow_class.assert_called_with(
            llm=self.mock_llm,
            max_cycles=50,
            verbose=True
        )
        
        # 验证执行被调用
        mock_workflow.execute_cognitive_cycle.assert_called_with("测试任务")


if __name__ == '__main__':
    print("🚀 开始具身认知工作流集成测试...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEndToEndWorkflow,
        TestComplexScenarios,
        TestFailureScenarios,
        TestRealWorldScenarios,
        TestWorkflowFeatures,
        TestConvenienceFunctions
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试总结
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
    else:
        print(f"❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
    
    print(f"📊 测试统计:")
    print(f"   - 运行测试: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    print("="*60)