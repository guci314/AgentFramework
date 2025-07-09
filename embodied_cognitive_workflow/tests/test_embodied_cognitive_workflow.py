#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
具身认知工作流主引擎单元测试

测试具身认知工作流系统的核心功能：
1. 工作流初始化和配置
2. 认知循环执行
3. 决策处理逻辑
4. 状态管理和上下文维护
5. 错误处理和超时控制
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_cognitive_workflow.embodied_cognitive_workflow import (
    EmbodiedCognitiveWorkflow, WorkflowContext, WorkflowStatus,
    DecisionType, CycleOutcome, create_embodied_cognitive_workflow,
    execute_embodied_cognitive_task
)
from embodied_cognitive_workflow.ego_agent import EgoAgent
from embodied_cognitive_workflow.id_agent import IdAgent
from pythonTask import Agent
from agent_base import Result


class TestWorkflowInitialization(unittest.TestCase):
    """测试工作流初始化"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    def test_basic_initialization(self):
        """测试基础初始化"""
        workflow = EmbodiedCognitiveWorkflow(llm=self.mock_llm)
        
        self.assertIsNotNone(workflow.body)
        self.assertIsNotNone(workflow.ego)
        self.assertIsNotNone(workflow.id_agent)
        self.assertEqual(workflow.max_cycles, 50)
        self.assertTrue(workflow.verbose)
        self.assertEqual(workflow._status, WorkflowStatus.NOT_STARTED)
        self.assertEqual(workflow.current_cycle_count, 0)
    
    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        body_config = {"name": "test_body"}
        ego_config = {"system_message": "test ego message"}
        id_config = {"system_message": "test id message"}
        
        workflow = EmbodiedCognitiveWorkflow(
            llm=self.mock_llm,
            body_config=body_config,
            ego_config=ego_config,
            id_config=id_config,
            max_cycles=100,
            verbose=False
        )
        
        self.assertEqual(workflow.max_cycles, 100)
        self.assertFalse(workflow.verbose)
        self.assertEqual(workflow.body.name, "身体")  # 名称会被覆盖
    
    def test_knowledge_loading(self):
        """测试知识加载"""
        workflow = EmbodiedCognitiveWorkflow(llm=self.mock_llm, verbose=False)
        
        # 模拟组件的loadKnowledge方法
        workflow.ego.loadKnowledge = Mock()
        workflow.id_agent.loadKnowledge = Mock()
        workflow.body.loadKnowledge = Mock()
        
        knowledge = "测试知识内容"
        workflow.load_knowledge(knowledge)
        
        # 验证所有组件都加载了知识
        workflow.ego.loadKnowledge.assert_called_once_with(knowledge)
        workflow.id_agent.loadKnowledge.assert_called_once_with(knowledge)
        workflow.body.loadKnowledge.assert_called_once_with(knowledge)
    
    def test_python_module_loading(self):
        """测试Python模块加载"""
        workflow = EmbodiedCognitiveWorkflow(llm=self.mock_llm, verbose=False)
        
        workflow.body.loadPythonModules = Mock()
        
        modules = ['math', 'json']
        workflow.load_python_modules(modules)
        
        workflow.body.loadPythonModules.assert_called_once_with(modules)


class TestWorkflowContext(unittest.TestCase):
    """测试工作流上下文管理"""
    
    def test_context_initialization(self):
        """测试上下文初始化"""
        instruction = "测试指令"
        context = WorkflowContext(instruction)
        
        self.assertEqual(context.instruction, instruction)
        self.assertEqual(context.history, [])
        self.assertEqual(context.current_cycle, 0)
        self.assertEqual(context.current_state, "")
        self.assertEqual(context.id_evaluation, "")
        self.assertFalse(context.goal_achieved)
    
    def test_context_updates(self):
        """测试上下文更新"""
        context = WorkflowContext("测试指令")
        
        # 测试添加循环结果
        context.add_cycle_result(1, "第一轮结果")
        self.assertEqual(len(context.history), 1)
        self.assertIn("第1轮结果", context.history[0])
        
        # 测试更新状态
        context.update_current_state("新状态")
        self.assertEqual(context.current_state, "新状态")
        
        # 测试更新评估结果
        context.update_id_evaluation("评估通过")
        self.assertEqual(context.id_evaluation, "评估通过")
        
        # 测试更新目标状态
        context.update_goal_status(True)
        self.assertTrue(context.goal_achieved)
    
    def test_get_current_context(self):
        """测试获取当前上下文"""
        context = WorkflowContext("执行任务")
        context.update_current_state("任务进行中")
        context.update_id_evaluation("需要继续执行")
        context.update_goal_status(False)
        context.add_cycle_result(1, "第一轮完成")
        
        current_context = context.get_current_context()
        
        self.assertIn("用户指令：执行任务", current_context)
        self.assertIn("当前状态：任务进行中", current_context)
        self.assertIn("本我评估：需要继续执行", current_context)
        self.assertIn("目标状态：未达成", current_context)
        self.assertIn("第1轮结果：第一轮完成", current_context)


class TestCognitiveCycle(unittest.TestCase):
    """测试认知循环执行"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.workflow = EmbodiedCognitiveWorkflow(llm=self.mock_llm, verbose=False)
        
        # 模拟各个组件的方法
        self.workflow.ego = Mock(spec=EgoAgent)
        self.workflow.id_agent = Mock(spec=IdAgent)
        self.workflow.body = Mock(spec=Agent)
    
    def test_initialize_workflow(self):
        """测试工作流初始化"""
        instruction = "创建一个计算器"
        
        # 模拟本我初始化
        self.workflow.id_agent.initialize_value_system = Mock(return_value="任务规格")
        self.workflow.id_agent.get_task_specification = Mock(return_value="详细规格")
        
        context = self.workflow._initialize_workflow(instruction)
        
        self.assertIsInstance(context, WorkflowContext)
        self.assertEqual(context.instruction, instruction)
        self.assertEqual(self.workflow._status, WorkflowStatus.RUNNING)
        self.workflow.id_agent.initialize_value_system.assert_called_once_with(instruction)
    
    def test_execute_single_cycle_request_evaluation(self):
        """测试单轮循环 - 请求评估"""
        context = WorkflowContext("测试任务")
        
        # 模拟自我分析和决策
        self.workflow.ego.analyze_current_state = Mock(return_value="状态良好")
        self.workflow.ego.decide_next_action = Mock(return_value="请求评估")
        
        # 模拟评估流程
        self.workflow.ego.request_id_evaluation = Mock(return_value="请求评估目标达成")
        self.workflow.id_agent.generate_evaluation_instruction = Mock(return_value="检查结果")
        self.workflow.body.execute_sync = Mock(return_value=Result(True, "", "检查通过", None, ""))
        self.workflow.id_agent.evaluate_goal_achievement = Mock(
            return_value='{"目标是否达成": true, "原因": "功能完成"}'
        )
        self.workflow.body.chat_sync = Mock(return_value=Result(True, "", "最终状态良好", None, ""))
        
        outcome = self.workflow._execute_single_cycle(context)
        
        self.assertFalse(outcome.continue_workflow)
        self.assertIsNotNone(outcome.final_result)
        self.assertTrue(outcome.final_result.success)
        self.assertEqual(outcome.decision_type, DecisionType.REQUEST_EVALUATION)
    
    def test_execute_single_cycle_judgment_failed(self):
        """测试单轮循环 - 判断失败"""
        context = WorkflowContext("测试任务")
        
        # 模拟自我分析和决策
        self.workflow.ego.analyze_current_state = Mock(return_value="无法继续")
        self.workflow.ego.decide_next_action = Mock(return_value="判断失败")
        
        outcome = self.workflow._execute_single_cycle(context)
        
        self.assertFalse(outcome.continue_workflow)
        self.assertIsNotNone(outcome.final_result)
        self.assertFalse(outcome.final_result.success)
        self.assertEqual(outcome.decision_type, DecisionType.JUDGMENT_FAILED)
        self.assertEqual(self.workflow._status, WorkflowStatus.FAILED)
    
    def test_execute_single_cycle_continue(self):
        """测试单轮循环 - 继续执行"""
        context = WorkflowContext("测试任务")
        
        # 模拟自我分析和决策
        self.workflow.ego.analyze_current_state = Mock(return_value="需要继续")
        self.workflow.ego.decide_next_action = Mock(return_value="继续循环")
        
        # 模拟认知步骤执行
        with patch.object(self.workflow, '_execute_cognitive_step', return_value="执行结果"):
            outcome = self.workflow._execute_single_cycle(context)
        
        self.assertTrue(outcome.continue_workflow)
        self.assertEqual(outcome.cycle_data, "执行结果")
        self.assertEqual(outcome.decision_type, DecisionType.CONTINUE_CYCLE)
    
    def test_execute_main_loop_success(self):
        """测试主循环 - 成功完成"""
        context = WorkflowContext("测试任务")
        
        # 创建成功的循环结果
        success_outcome = CycleOutcome(
            continue_workflow=False,
            final_result=Result(True, "", "成功", None, "任务完成"),
            decision_type=DecisionType.REQUEST_EVALUATION
        )
        
        # 模拟单轮循环返回成功结果
        with patch.object(self.workflow, '_execute_single_cycle', return_value=success_outcome):
            result = self.workflow._execute_main_loop(context)
        
        self.assertTrue(result.success)
        self.assertEqual(result.return_value, "成功")
    
    def test_execute_main_loop_timeout(self):
        """测试主循环 - 超时"""
        context = WorkflowContext("测试任务")
        self.workflow.max_cycles = 2
        
        # 创建继续循环的结果
        continue_outcome = CycleOutcome(
            continue_workflow=True,
            cycle_data="继续执行",
            decision_type=DecisionType.CONTINUE_CYCLE
        )
        
        # 模拟单轮循环一直返回继续
        with patch.object(self.workflow, '_execute_single_cycle', return_value=continue_outcome):
            result = self.workflow._execute_main_loop(context)
        
        self.assertFalse(result.success)
        self.assertIn("超时", result.error)
        self.assertEqual(self.workflow._status, WorkflowStatus.TIMEOUT)


class TestDecisionHandling(unittest.TestCase):
    """测试决策处理逻辑"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.workflow = EmbodiedCognitiveWorkflow(llm=self.mock_llm, verbose=False)
        
        # 模拟组件
        self.workflow.ego = Mock(spec=EgoAgent)
        self.workflow.id_agent = Mock(spec=IdAgent)
        self.workflow.body = Mock(spec=Agent)
    
    def test_make_decision_mapping(self):
        """测试决策映射"""
        test_cases = [
            ("请求评估", DecisionType.REQUEST_EVALUATION),
            ("判断失败", DecisionType.JUDGMENT_FAILED),
            ("继续循环", DecisionType.CONTINUE_CYCLE),
            ("未知决策", DecisionType.REQUEST_EVALUATION)  # 默认值
        ]
        
        for decision_str, expected_type in test_cases:
            result = self.workflow._make_decision(decision_str)
            self.assertEqual(result, expected_type)
    
    def test_handle_evaluation_request_goal_achieved(self):
        """测试处理评估请求 - 目标达成"""
        context = WorkflowContext("测试任务")
        context.update_current_state("任务进行中")
        
        # 模拟评估流程
        self.workflow.ego.request_id_evaluation = Mock(return_value="请求评估")
        self.workflow.id_agent.generate_evaluation_instruction = Mock(return_value="检查指令")
        self.workflow.body.execute_sync = Mock(return_value=Result(True, "", "结果良好", None, ""))
        self.workflow.id_agent.evaluate_goal_achievement = Mock(
            return_value='{"目标是否达成": true, "原因": "任务完成"}'
        )
        self.workflow.body.chat_sync = Mock(return_value=Result(True, "", "最终总结", None, ""))
        
        outcome = self.workflow._handle_evaluation_request(context)
        
        self.assertFalse(outcome.continue_workflow)
        self.assertTrue(outcome.final_result.success)
        self.assertEqual(self.workflow._status, WorkflowStatus.SUCCESS)
        self.assertTrue(context.goal_achieved)
        self.assertEqual(context.id_evaluation, "任务完成")
    
    def test_handle_evaluation_request_goal_not_achieved(self):
        """测试处理评估请求 - 目标未达成"""
        context = WorkflowContext("测试任务")
        
        # 模拟评估流程
        self.workflow.ego.request_id_evaluation = Mock(return_value="请求评估")
        self.workflow.id_agent.generate_evaluation_instruction = Mock(return_value="检查指令")
        self.workflow.body.execute_sync = Mock(return_value=Result(True, "", "还需改进", None, ""))
        self.workflow.id_agent.evaluate_goal_achievement = Mock(
            return_value='{"目标是否达成": false, "原因": "功能不完整"}'
        )
        
        outcome = self.workflow._handle_evaluation_request(context)
        
        self.assertTrue(outcome.continue_workflow)
        self.assertEqual(outcome.cycle_data, "评估结果：功能不完整")
        self.assertFalse(context.goal_achieved)
    
    def test_handle_evaluation_request_json_parse_error(self):
        """测试处理评估请求 - JSON解析错误"""
        context = WorkflowContext("测试任务")
        
        # 模拟评估流程返回无效JSON
        self.workflow.ego.request_id_evaluation = Mock(return_value="请求评估")
        self.workflow.id_agent.generate_evaluation_instruction = Mock(return_value="检查指令")
        self.workflow.body.execute_sync = Mock(return_value=Result(True, "", "结果", None, ""))
        self.workflow.id_agent.evaluate_goal_achievement = Mock(return_value="无效的JSON格式")
        
        outcome = self.workflow._handle_evaluation_request(context)
        
        self.assertTrue(outcome.continue_workflow)
        self.assertEqual(context.id_evaluation, "无效的JSON格式")
        self.assertFalse(context.goal_achieved)
    
    def test_execute_cognitive_step_observation(self):
        """测试执行认知步骤 - 观察"""
        context = WorkflowContext("测试任务")
        context.update_current_state("需要观察")
        
        # 模拟自我决定观察
        mock_response = Result(True, "", '{"行动类型": "观察", "理由": "需要了解状态"}', None, "")
        self.workflow.ego.chat_sync = Mock(return_value=mock_response)
        self.workflow.ego.generate_observation_instruction = Mock(return_value="观察指令")
        self.workflow.body.execute_sync = Mock(
            return_value=Result(True, "", "观察到的内容", None, "")
        )
        
        result = self.workflow._execute_cognitive_step(context)
        
        self.assertIsNotNone(result)
        self.assertIn("观察结果", result)
        self.assertIn("观察到的内容", result)
    
    def test_execute_cognitive_step_execution(self):
        """测试执行认知步骤 - 执行"""
        context = WorkflowContext("测试任务")
        context.update_current_state("需要执行")
        
        # 模拟自我决定执行
        mock_response = Result(True, "", '{"行动类型": "执行", "理由": "需要执行操作"}', None, "")
        self.workflow.ego.chat_sync = Mock(return_value=mock_response)
        self.workflow.ego.generate_execution_instruction = Mock(return_value="执行指令")
        self.workflow.body.execute_sync = Mock(
            return_value=Result(True, "", "执行成功", None, "")
        )
        
        result = self.workflow._execute_cognitive_step(context)
        
        self.assertIsNotNone(result)
        self.assertIn("执行结果", result)
        self.assertIn("执行成功", result)
    
    def test_execute_cognitive_step_error_handling(self):
        """测试执行认知步骤 - 错误处理"""
        context = WorkflowContext("测试任务")
        
        # 模拟执行失败
        mock_response = Result(True, "", '{"行动类型": "执行", "理由": "执行"}', None, "")
        self.workflow.ego.chat_sync = Mock(return_value=mock_response)
        self.workflow.ego.generate_execution_instruction = Mock(return_value="执行指令")
        self.workflow.body.execute_sync = Mock(
            return_value=Result(False, "", "", None, "执行出错")
        )
        self.workflow.ego.handle_execution_error = Mock(return_value="错误处理方案")
        
        result = self.workflow._execute_cognitive_step(context)
        
        self.assertIsNotNone(result)
        self.assertIn("执行失败", result)
        self.assertIn("错误处理方案", result)


class TestWorkflowManagement(unittest.TestCase):
    """测试工作流管理功能"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.workflow = EmbodiedCognitiveWorkflow(llm=self.mock_llm, verbose=False)
    
    def test_workflow_status_tracking(self):
        """测试工作流状态跟踪"""
        # 初始状态
        self.assertEqual(self.workflow._status, WorkflowStatus.NOT_STARTED)
        self.assertEqual(self.workflow.workflow_status, "未开始")
        
        # 设置新状态
        self.workflow._set_status(WorkflowStatus.RUNNING)
        self.assertEqual(self.workflow._status, WorkflowStatus.RUNNING)
        self.assertEqual(self.workflow.workflow_status, "运行中")
        
        # 测试其他状态
        for status in WorkflowStatus:
            self.workflow._set_status(status)
            self.assertEqual(self.workflow._status, status)
            self.assertEqual(self.workflow.workflow_status, status.value)
    
    def test_get_workflow_status(self):
        """测试获取工作流状态"""
        self.workflow.id_agent.get_current_goal = Mock(return_value="创建计算器")
        self.workflow.id_agent.get_value_standard = Mock(return_value="功能完整")
        self.workflow.current_cycle_count = 5
        
        status = self.workflow.get_workflow_status()
        
        self.assertEqual(status["状态"], "未开始")
        self.assertEqual(status["当前循环次数"], 5)
        self.assertEqual(status["最大循环次数"], 50)
        self.assertEqual(status["目标描述"], "创建计算器")
        self.assertEqual(status["价值标准"], "功能完整")
    
    def test_reset_workflow(self):
        """测试重置工作流"""
        # 设置一些状态
        self.workflow.current_cycle_count = 10
        self.workflow._set_status(WorkflowStatus.RUNNING)
        self.workflow.execution_history.append("历史记录")
        
        # 重置
        self.workflow.reset()
        
        self.assertEqual(self.workflow.current_cycle_count, 0)
        self.assertEqual(self.workflow._status, WorkflowStatus.NOT_STARTED)
        self.assertEqual(len(self.workflow.execution_history), 0)
    
    def test_exception_handling(self):
        """测试异常处理"""
        error = Exception("测试异常")
        result = self.workflow._handle_workflow_exception(error)
        
        self.assertFalse(result.success)
        self.assertIn("测试异常", result.error)
        self.assertEqual(self.workflow._status, WorkflowStatus.EXCEPTION)


class TestUtilityFunctions(unittest.TestCase):
    """测试便利函数"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    def test_create_embodied_cognitive_workflow(self):
        """测试工作流创建便利函数"""
        workflow = create_embodied_cognitive_workflow(
            self.mock_llm,
            max_cycles=100,
            verbose=False
        )
        
        self.assertIsInstance(workflow, EmbodiedCognitiveWorkflow)
        self.assertEqual(workflow.max_cycles, 100)
        self.assertFalse(workflow.verbose)
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EmbodiedCognitiveWorkflow')
    def test_execute_embodied_cognitive_task(self, mock_workflow_class):
        """测试任务执行便利函数"""
        # 模拟工作流实例
        mock_workflow = Mock()
        mock_workflow.execute_cognitive_cycle.return_value = Result(
            True, "", "任务完成", None, ""
        )
        mock_workflow_class.return_value = mock_workflow
        
        result = execute_embodied_cognitive_task(
            self.mock_llm,
            "测试任务",
            verbose=False
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.return_value, "任务完成")
        mock_workflow.execute_cognitive_cycle.assert_called_once_with("测试任务")


class TestIntegrationScenarios(unittest.TestCase):
    """测试集成场景"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.Agent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.EgoAgent')
    @patch('embodied_cognitive_workflow.embodied_cognitive_workflow.IdAgent')
    def test_complete_workflow_execution(self, mock_id_class, mock_ego_class, mock_agent_class):
        """测试完整的工作流执行"""
        # 创建模拟对象
        mock_body = Mock(spec=Agent)
        mock_ego = Mock(spec=EgoAgent)
        mock_id = Mock(spec=IdAgent)
        
        mock_agent_class.return_value = mock_body
        mock_ego_class.return_value = mock_ego
        mock_id_class.return_value = mock_id
        
        # 配置模拟行为
        mock_id.initialize_value_system.return_value = "任务规格"
        mock_id.get_task_specification.return_value = "详细规格"
        
        # 第一轮：继续执行
        mock_ego.analyze_current_state.side_effect = ["开始执行", "执行中"]
        mock_ego.decide_next_action.side_effect = ["继续循环", "请求评估"]
        mock_ego.chat_sync.return_value = Result(
            True, "", '{"行动类型": "执行", "理由": "开始"}', None, ""
        )
        mock_ego.generate_execution_instruction.return_value = "执行指令"
        mock_body.execute_sync.side_effect = [
            Result(True, "", "执行成功", None, ""),
            Result(True, "", "检查通过", None, "")
        ]
        
        # 第二轮：请求评估并成功
        mock_ego.request_id_evaluation.return_value = "请求评估"
        mock_id.generate_evaluation_instruction.return_value = "检查指令"
        mock_id.evaluate_goal_achievement.return_value = '{"目标是否达成": true, "原因": "完成"}'
        mock_body.chat_sync.return_value = Result(True, "", "最终状态", None, "")
        
        # 执行工作流
        workflow = EmbodiedCognitiveWorkflow(llm=self.mock_llm, verbose=False)
        result = workflow.execute_cognitive_cycle("创建计算器")
        
        self.assertTrue(result.success)
        self.assertEqual(workflow._status, WorkflowStatus.SUCCESS)
        self.assertEqual(workflow.current_cycle_count, 2)


if __name__ == '__main__':
    print("🚀 开始具身认知工作流主引擎单元测试...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestWorkflowInitialization,
        TestWorkflowContext,
        TestCognitiveCycle,
        TestDecisionHandling,
        TestWorkflowManagement,
        TestUtilityFunctions,
        TestIntegrationScenarios
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