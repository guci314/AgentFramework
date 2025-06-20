#!/usr/bin/env python3
"""
自然语言状态管理测试
==================

测试新的自然语言全局状态管理功能，包括：
1. 全局状态更新
2. 自然语言条件评估
3. 状态历史追踪
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.workflow_definitions import (
    WorkflowDefinition, WorkflowMetadata, WorkflowStep, StepExecution, 
    StepExecutionStatus, WorkflowExecutionContext
)
from static_workflow.global_state_updater import GlobalStateUpdater
from static_workflow.control_flow_evaluator import ControlFlowEvaluator


class TestNaturalLanguageState(unittest.TestCase):
    """测试自然语言状态管理"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟的LLM
        self.mock_llm = Mock()
        
        # 创建测试用的工作流定义
        self.workflow_def = WorkflowDefinition(
            workflow_metadata=WorkflowMetadata(
                name="计算器开发流程",
                version="1.0",
                description="开发一个简单计算器的工作流"
            ),
            steps=[
                WorkflowStep(
                    id="step1",
                    name="创建基础代码",
                    agent_name="coder",
                    instruction="创建一个简单的add函数",
                    expected_output="包含add函数的Python代码"
                ),
                WorkflowStep(
                    id="step2", 
                    name="编写测试",
                    agent_name="tester",
                    instruction="为add函数编写测试用例",
                    expected_output="包含测试用例的Python代码"
                )
            ],
            global_state="工作流即将开始，目标是创建一个简单的计算器程序。"
        )
        
        # 创建执行上下文
        self.execution_context = WorkflowExecutionContext("test-workflow-001")
    
    def test_global_state_updater_basic(self):
        """测试基础的全局状态更新功能"""
        print("\n🧪 测试基础的全局状态更新功能")
        
        # 创建状态更新器（不使用LLM）
        updater = GlobalStateUpdater(llm=None, enable_updates=True)
        
        # 创建步骤执行实例
        step = self.workflow_def.steps[0]  # "创建基础代码"
        execution = StepExecution("exec-1", "step1", 1)
        execution.status = StepExecutionStatus.COMPLETED
        
        # 测试简单的状态更新
        current_state = "工作流刚开始。"
        new_state = updater.update_state(current_state, step, execution)
        
        print(f"   原状态: {current_state}")
        print(f"   新状态: {new_state}")
        
        # 验证状态更新
        self.assertIn("创建基础代码", new_state)
        self.assertIn("step1", new_state)
        self.assertTrue(len(new_state) > len(current_state))
        
        print("   ✅ 基础状态更新功能正常")
    
    def test_global_state_updater_with_llm(self):
        """测试使用LLM的智能状态更新"""
        print("\n🧪 测试使用LLM的智能状态更新")
        
        # 配置模拟LLM返回
        mock_response = Mock()
        mock_response.content = """工作流正在进行中。

已完成工作：
- 创建了基础的add函数，实现了两个数的加法运算
- 代码结构清晰，遵循Python编程规范

当前状态：
- 基础功能开发完成
- 准备进入测试阶段

下一步计划：
- 编写测试用例验证add函数的正确性"""

        self.mock_llm.invoke.return_value = mock_response
        
        # 创建状态更新器（使用LLM）
        updater = GlobalStateUpdater(llm=self.mock_llm, enable_updates=True)
        
        # 创建步骤执行实例
        step = self.workflow_def.steps[0]
        execution = StepExecution("exec-1", "step1", 1)
        execution.status = StepExecutionStatus.COMPLETED
        
        # 测试LLM状态更新
        current_state = "工作流刚开始，准备创建计算器代码。"
        new_state = updater.update_state(current_state, step, execution, "计算器开发项目")
        
        print(f"   原状态: {current_state}")
        print(f"   新状态: {new_state[:200]}...")
        
        # 验证LLM被正确调用
        self.mock_llm.invoke.assert_called_once()
        
        # 验证状态内容
        self.assertIn("add函数", new_state)
        self.assertIn("测试阶段", new_state)
        
        print("   ✅ LLM智能状态更新功能正常")
    
    def test_workflow_execution_context_state_management(self):
        """测试工作流执行上下文的状态管理"""
        print("\n🧪 测试工作流执行上下文的状态管理")
        
        # 测试状态更新
        initial_state = "工作流开始执行"
        self.execution_context.update_global_state(initial_state)
        
        self.assertEqual(self.execution_context.current_global_state, initial_state)
        self.assertEqual(len(self.execution_context.state_update_history), 0)
        
        # 测试第二次更新
        second_state = "第一步完成，开始第二步"
        self.execution_context.update_global_state(second_state)
        
        self.assertEqual(self.execution_context.current_global_state, second_state)
        self.assertEqual(len(self.execution_context.state_update_history), 1)
        self.assertEqual(self.execution_context.state_update_history[0], initial_state)
        
        # 测试状态摘要
        summary = self.execution_context.get_state_summary()
        print(f"   状态摘要: {summary}")
        
        self.assertIn("第2次更新", summary)
        self.assertIn(second_state, summary)
        
        # 测试状态历史
        history = self.execution_context.get_state_history(limit=3)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], initial_state)
        self.assertEqual(history[1], second_state)
        
        print("   ✅ 状态管理功能正常")
    
    def test_control_flow_evaluator_natural_language(self):
        """测试控制流评估器的自然语言支持"""
        print("\n🧪 测试控制流评估器的自然语言支持")
        
        # 配置模拟LLM返回
        self.mock_llm.invoke.return_value = Mock(content="true")
        
        # 创建评估器
        evaluator = ControlFlowEvaluator(llm=self.mock_llm)
        
        # 设置上下文
        evaluator.set_context(
            global_state="已成功创建add函数，代码质量良好，所有基本功能都已实现。"
        )
        
        # 测试自然语言条件评估
        condition = "add函数是否已经创建完成"
        result = evaluator.evaluate_natural_language_condition(condition)
        
        print(f"   条件: {condition}")
        print(f"   评估结果: {result}")
        
        # 验证结果
        self.assertTrue(result)
        self.mock_llm.invoke.assert_called_once()
        
        # 测试不满足的条件
        self.mock_llm.reset_mock()
        self.mock_llm.invoke.return_value = Mock(content="false")
        
        condition2 = "是否已经完成所有测试"
        result2 = evaluator.evaluate_natural_language_condition(condition2)
        
        print(f"   条件: {condition2}")
        print(f"   评估结果: {result2}")
        
        self.assertFalse(result2)
        
        print("   ✅ 自然语言条件评估功能正常")
    
    def test_data_extraction_from_natural_language(self):
        """测试从自然语言状态中提取结构化数据"""
        print("\n🧪 测试从自然语言状态中提取结构化数据")
        
        # 创建状态更新器
        updater = GlobalStateUpdater(llm=None)  # 使用简单提取
        
        # 测试状态文本
        state_text = """工作流进展顺利 (2024-01-15 14:30:00)
        
已完成 3 个步骤：
- 创建基础代码: 成功
- 编写测试用例: 成功  
- 运行测试: 成功

当前状态良好，所有测试通过。"""
        
        # 提取结构化数据
        extracted = updater.extract_structured_data(state_text)
        
        print(f"   状态文本: {state_text[:100]}...")
        print(f"   提取的数据: {extracted}")
        
        # 验证提取结果
        self.assertIn('last_update_time', extracted)
        self.assertEqual(extracted['last_update_time'], '2024-01-15 14:30:00')
        self.assertEqual(extracted['status'], 'success')
        
        print("   ✅ 数据提取功能正常")
    
    def test_workflow_definition_with_global_state(self):
        """测试工作流定义中的全局状态字段"""
        print("\n🧪 测试工作流定义中的全局状态字段")
        
        # 验证全局状态字段存在
        self.assertTrue(hasattr(self.workflow_def, 'global_state'))
        self.assertEqual(self.workflow_def.global_state, "工作流即将开始，目标是创建一个简单的计算器程序。")
        
        # 验证向后兼容性
        self.assertTrue(hasattr(self.workflow_def, 'global_variables'))
        self.assertIsInstance(self.workflow_def.global_variables, dict)
        
        print(f"   初始全局状态: {self.workflow_def.global_state}")
        print(f"   全局变量(向后兼容): {self.workflow_def.global_variables}")
        print("   ✅ 工作流定义支持自然语言状态")


def run_integration_test():
    """运行集成测试"""
    print("\n" + "="*60)
    print("🧪 自然语言状态管理集成测试")
    print("="*60)
    
    try:
        # 导入依赖
        from static_workflow.static_workflow_engine import StaticWorkflowEngine
        from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3
        
        print("\n✅ 所有模块导入成功")
        
        # 测试引擎创建
        mock_llm = Mock()
        engine = StaticWorkflowEngine(llm=mock_llm, enable_state_updates=True)
        
        print("✅ StaticWorkflowEngine 支持LLM状态更新")
        
        # 验证状态更新器存在
        assert hasattr(engine, 'state_updater')
        assert engine.state_updater.llm == mock_llm
        
        print("✅ 状态更新器正确配置")
        
        # 验证控制流评估器支持LLM
        assert hasattr(engine.evaluator, 'llm') 
        assert engine.evaluator.llm == mock_llm
        
        print("✅ 控制流评估器支持自然语言")
        
        print("\n🎉 集成测试全部通过！")
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)
    
    # 运行集成测试
    run_integration_test()