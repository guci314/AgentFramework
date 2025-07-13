#!/usr/bin/env python3
"""
CognitiveDebugger 完整测试套件
包含单元测试、集成测试和性能测试
"""

import os
import sys
import unittest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from python_core import *
from llm_lazy import get_model
    from embodied_cognitive_workflow import CognitiveAgent, WorkflowContext, DecisionType
    from cognitive_debugger import (
        CognitiveDebugger, StepType, StepResult, DebugState, 
        Breakpoint, BreakpointManager, StepExecutor, DebugUtils,
        PerformanceReport
    )
    from agent_base import Result
    
    # 使用Gemini模型
    llm_gemini = \1("gemini_2_5_flash")
    
    print("✅ 所有模块导入成功！")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)


class TestDataStructures(unittest.TestCase):
    """测试核心数据结构"""
    
    def test_step_type_enum(self):
        """测试步骤类型枚举"""
        self.assertEqual(StepType.INIT.value, "初始化")
        self.assertEqual(StepType.COMPLEXITY_EVAL.value, "复杂性评估")
        self.assertEqual(StepType.COMPLETED.value, "执行完成")
        
        # 检查所有步骤类型都有值
        for step_type in StepType:
            self.assertIsNotNone(step_type.value)
            self.assertIsInstance(step_type.value, str)
    
    def test_step_result_creation(self):
        """测试步骤结果创建"""
        from datetime import datetime
        
        step_result = StepResult(
            step_type=StepType.INIT,
            step_id="test_001",
            timestamp=datetime.now(),
            input_data="test input",
            output_data="test output",
            execution_time=0.5,
            agent_layer="System",
            next_step=StepType.COMPLEXITY_EVAL
        )
        
        self.assertEqual(step_result.step_type, StepType.INIT)
        self.assertEqual(step_result.step_id, "test_001")
        self.assertEqual(step_result.input_data, "test input")
        self.assertEqual(step_result.output_data, "test output")
        self.assertEqual(step_result.execution_time, 0.5)
        self.assertEqual(step_result.agent_layer, "System")
        self.assertEqual(step_result.next_step, StepType.COMPLEXITY_EVAL)
        self.assertIsNone(step_result.error)
    
    def test_debug_state_initialization(self):
        """测试调试状态初始化"""
        debug_state = DebugState()
        
        self.assertEqual(debug_state.current_step, StepType.INIT)
        self.assertEqual(debug_state.cycle_count, 0)
        self.assertFalse(debug_state.is_finished)
        self.assertIsNone(debug_state.workflow_context)
        self.assertEqual(len(debug_state.step_history), 0)
        self.assertEqual(len(debug_state.breakpoints), 0)
    
    def test_breakpoint_creation(self):
        """测试断点创建"""
        breakpoint = Breakpoint(
            id="bp_001",
            step_type=StepType.STATE_ANALYSIS,
            condition="cycle_count > 2",
            description="测试断点"
        )
        
        self.assertEqual(breakpoint.id, "bp_001")
        self.assertEqual(breakpoint.step_type, StepType.STATE_ANALYSIS)
        self.assertEqual(breakpoint.condition, "cycle_count > 2")
        self.assertEqual(breakpoint.description, "测试断点")
        self.assertTrue(breakpoint.enabled)
        self.assertEqual(breakpoint.hit_count, 0)


class TestBreakpointManager(unittest.TestCase):
    """测试断点管理器"""
    
    def setUp(self):
        self.bp_manager = BreakpointManager()
    
    def test_add_breakpoint(self):
        """测试添加断点"""
        breakpoint = Breakpoint(
            id="bp_001",
            step_type=StepType.STATE_ANALYSIS,
            description="测试断点"
        )
        
        bp_id = self.bp_manager.add_breakpoint(breakpoint)
        self.assertEqual(bp_id, "bp_001")
        self.assertEqual(len(self.bp_manager.breakpoints), 1)
    
    def test_remove_breakpoint(self):
        """测试移除断点"""
        breakpoint = Breakpoint(
            id="bp_001",
            step_type=StepType.STATE_ANALYSIS
        )
        
        self.bp_manager.add_breakpoint(breakpoint)
        self.assertEqual(len(self.bp_manager.breakpoints), 1)
        
        success = self.bp_manager.remove_breakpoint("bp_001")
        self.assertTrue(success)
        self.assertEqual(len(self.bp_manager.breakpoints), 0)
        
        # 测试移除不存在的断点
        success = self.bp_manager.remove_breakpoint("nonexistent")
        self.assertFalse(success)
    
    def test_check_breakpoint_no_condition(self):
        """测试无条件断点检查"""
        breakpoint = Breakpoint(
            id="bp_001",
            step_type=StepType.STATE_ANALYSIS
        )
        
        self.bp_manager.add_breakpoint(breakpoint)
        
        # 匹配的步骤类型应该触发断点
        hit_bp = self.bp_manager.check_breakpoint(
            StepType.STATE_ANALYSIS, 
            {"cycle_count": 1}
        )
        self.assertIsNotNone(hit_bp)
        self.assertEqual(hit_bp.id, "bp_001")
        self.assertEqual(hit_bp.hit_count, 1)
        
        # 不匹配的步骤类型不应该触发断点
        hit_bp = self.bp_manager.check_breakpoint(
            StepType.DECISION_MAKING, 
            {"cycle_count": 1}
        )
        self.assertIsNone(hit_bp)
    
    def test_check_breakpoint_with_condition(self):
        """测试条件断点检查"""
        breakpoint = Breakpoint(
            id="bp_001",
            step_type=StepType.STATE_ANALYSIS,
            condition="cycle_count > 2"
        )
        
        self.bp_manager.add_breakpoint(breakpoint)
        
        # 条件不满足时不应该触发
        hit_bp = self.bp_manager.check_breakpoint(
            StepType.STATE_ANALYSIS, 
            {"cycle_count": 1}
        )
        self.assertIsNone(hit_bp)
        
        # 条件满足时应该触发
        hit_bp = self.bp_manager.check_breakpoint(
            StepType.STATE_ANALYSIS, 
            {"cycle_count": 3}
        )
        self.assertIsNotNone(hit_bp)
        self.assertEqual(hit_bp.id, "bp_001")
    
    def test_enable_disable_breakpoint(self):
        """测试启用/禁用断点"""
        breakpoint = Breakpoint(
            id="bp_001",
            step_type=StepType.STATE_ANALYSIS
        )
        
        self.bp_manager.add_breakpoint(breakpoint)
        
        # 禁用断点
        success = self.bp_manager.disable_breakpoint("bp_001")
        self.assertTrue(success)
        
        # 禁用的断点不应该触发
        hit_bp = self.bp_manager.check_breakpoint(
            StepType.STATE_ANALYSIS, 
            {"cycle_count": 1}
        )
        self.assertIsNone(hit_bp)
        
        # 重新启用断点
        success = self.bp_manager.enable_breakpoint("bp_001")
        self.assertTrue(success)
        
        # 启用的断点应该触发
        hit_bp = self.bp_manager.check_breakpoint(
            StepType.STATE_ANALYSIS, 
            {"cycle_count": 1}
        )
        self.assertIsNotNone(hit_bp)


class TestStepExecutor(unittest.TestCase):
    """测试步骤执行器"""
    
    def setUp(self):
        # 创建模拟的认知智能体
        self.mock_agent = Mock(spec=CognitiveAgent)
        self.mock_agent.max_cycles = 3
        self.mock_agent.enable_meta_cognition= False
        self.mock_agent.evaluation_mode = "internal"
        
        # 模拟各层智能体
        self.mock_agent.ego = Mock()
        self.mock_agent.id = Mock()
        self.mock_agent.body = Mock()
        self.mock_agent.meta_cognition = None
        
        self.step_executor = StepExecutor(self.mock_agent)
        self.debug_state = DebugState()
    
    def test_step_mapping_completeness(self):
        """测试步骤映射完整性"""
        # 检查所有步骤类型都有对应的执行函数
        for step_type in StepType:
            self.assertIn(step_type, self.step_executor.step_mapping)
            self.assertIsNotNone(self.step_executor.step_mapping[step_type])
    
    def test_execute_init_step(self):
        """测试初始化步骤执行"""
        instruction = "测试指令"
        
        step_result = self.step_executor.execute_step(
            StepType.INIT, 
            instruction, 
            self.debug_state
        )
        
        self.assertEqual(step_result.step_type, StepType.INIT)
        self.assertEqual(step_result.agent_layer, "System")
        self.assertIsNone(step_result.error)
        self.assertIsNotNone(self.debug_state.workflow_context)
        self.assertEqual(self.debug_state.workflow_context.instruction, instruction)
    
    def test_execute_complexity_eval_step(self):
        """测试复杂性评估步骤"""
        # 设置模拟返回值
        self.mock_agent._can_handle_directly.return_value = True
        
        # 先执行初始化
        self.step_executor.execute_step(
            StepType.INIT, 
            "简单测试", 
            self.debug_state
        )
        
        # 执行复杂性评估
        step_result = self.step_executor.execute_step(
            StepType.COMPLEXITY_EVAL, 
            None, 
            self.debug_state
        )
        
        self.assertEqual(step_result.step_type, StepType.COMPLEXITY_EVAL)
        self.assertEqual(step_result.agent_layer, "Ego")
        self.assertTrue(step_result.output_data)  # can_handle_directly = True
        self.assertIsNone(step_result.error)
        
        # 验证调用了正确的方法
        self.mock_agent._can_handle_directly.assert_called_once()
    
    def test_get_next_step_logic(self):
        """测试下一步逻辑"""
        # 测试复杂性评估后的分支
        step_result = StepResult(
            step_type=StepType.COMPLEXITY_EVAL,
            step_id="test",
            timestamp=Mock(),
            input_data=None,
            output_data=True,  # 可以直接处理
            execution_time=0.1,
            agent_layer="Ego",
            next_step=StepType.BODY_EXECUTION
        )
        
        next_step = self.step_executor.get_next_step(
            StepType.COMPLEXITY_EVAL, 
            step_result, 
            self.debug_state
        )
        
        self.assertEqual(next_step, StepType.BODY_EXECUTION)
    
    def test_can_execute_step(self):
        """测试步骤执行能力检查"""
        for step_type in StepType:
            self.assertTrue(self.step_executor.can_execute_step(step_type))
        
        # 测试无效步骤类型（如果有的话）
        # 这个测试可能需要根据实际实现调整


class TestCognitiveDebugger(unittest.TestCase):
    """测试认知调试器主类"""
    
    def setUp(self):
        # 创建模拟的认知智能体
        self.mock_agent = Mock(spec=CognitiveAgent)
        self.mock_agent.max_cycles = 3
        self.mock_agent.enable_meta_cognition= False
        self.mock_agent.evaluation_mode = "internal"
        
        # 模拟各层智能体
        self.mock_agent.ego = Mock()
        self.mock_agent.id = Mock()
        self.mock_agent.body = Mock()
        self.mock_agent.meta_cognition = None
        
        self.debugger = CognitiveDebugger(self.mock_agent)
    
    def test_debugger_initialization(self):
        """测试调试器初始化"""
        self.assertEqual(self.debugger.wrapped_agent, self.mock_agent)
        self.assertIsInstance(self.debugger.debug_state, DebugState)
        self.assertIsInstance(self.debugger.step_executor, StepExecutor)
        self.assertIsInstance(self.debugger.breakpoint_manager, BreakpointManager)
        self.assertIsNone(self.debugger._instruction)
    
    def test_start_debug(self):
        """测试开始调试会话"""
        instruction = "测试指令"
        
        self.debugger.start_debug(instruction)
        
        self.assertEqual(self.debugger._instruction, instruction)
        self.assertIsNotNone(self.debugger.debug_state.execution_start_time)
        self.assertEqual(self.debugger.debug_state.current_step, StepType.INIT)
        self.assertFalse(self.debugger.debug_state.is_finished)
    
    def test_reset_debug(self):
        """测试重置调试会话"""
        # 先开始一个会话
        self.debugger.start_debug("测试")
        
        # 重置
        self.debugger.reset_debug()
        
        self.assertIsNone(self.debugger._instruction)
        self.assertEqual(self.debugger.debug_state.current_step, StepType.INIT)
        self.assertEqual(len(self.debugger.debug_state.step_history), 0)
    
    def test_set_and_remove_breakpoint(self):
        """测试设置和移除断点"""
        # 设置断点
        bp_id = self.debugger.set_breakpoint(
            StepType.STATE_ANALYSIS,
            condition="cycle_count > 1",
            description="测试断点"
        )
        
        self.assertIsNotNone(bp_id)
        
        # 列出断点
        breakpoints = self.debugger.list_breakpoints()
        self.assertEqual(len(breakpoints), 1)
        self.assertEqual(breakpoints[0].step_type, StepType.STATE_ANALYSIS)
        
        # 移除断点
        success = self.debugger.remove_breakpoint(bp_id)
        self.assertTrue(success)
        
        # 验证断点已移除
        breakpoints = self.debugger.list_breakpoints()
        self.assertEqual(len(breakpoints), 0)
    
    def test_step_back_functionality(self):
        """测试回退功能"""
        # 先开始调试会话
        self.debugger.start_debug("测试指令")
        
        # 执行几个步骤（模拟）
        from datetime import datetime
        for i in range(3):
            step_result = StepResult(
                step_type=StepType.INIT,
                step_id=f"step_{i}",
                timestamp=datetime.now(),
                input_data=f"input_{i}",
                output_data=f"output_{i}",
                execution_time=0.1,
                agent_layer="System",
                next_step=StepType.COMPLEXITY_EVAL
            )
            self.debugger.debug_state.step_history.append(step_result)
        
        # 测试回退
        initial_count = len(self.debugger.debug_state.step_history)
        success = self.debugger.step_back(2)
        self.assertTrue(success)
        self.assertEqual(
            len(self.debugger.debug_state.step_history), 
            initial_count - 2
        )
        
        # 测试无效回退
        success = self.debugger.step_back(10)  # 超过历史长度
        self.assertFalse(success)
        
        success = self.debugger.step_back(0)   # 无效步数
        self.assertFalse(success)


class TestDebugUtils(unittest.TestCase):
    """测试调试辅助工具"""
    
    def setUp(self):
        from datetime import datetime
        
        # 创建测试用的步骤结果
        self.step_results = [
            StepResult(
                step_type=StepType.INIT,
                step_id="step_1",
                timestamp=datetime.now(),
                input_data="test",
                output_data="result",
                execution_time=0.1,
                agent_layer="System",
                next_step=StepType.COMPLEXITY_EVAL
            ),
            StepResult(
                step_type=StepType.COMPLEXITY_EVAL,
                step_id="step_2", 
                timestamp=datetime.now(),
                input_data="test",
                output_data=True,
                execution_time=0.5,
                agent_layer="Ego",
                next_step=StepType.BODY_EXECUTION
            ),
            StepResult(
                step_type=StepType.BODY_EXECUTION,
                step_id="step_3",
                timestamp=datetime.now(),
                input_data="test",
                output_data="result",
                execution_time=0.3,
                agent_layer="Body",
                next_step=StepType.FINALIZE
            )
        ]
    
    def test_analyze_performance(self):
        """测试性能分析"""
        report = DebugUtils.analyze_performance(self.step_results)
        
        self.assertIsInstance(report, PerformanceReport)
        self.assertEqual(report.total_time, 0.9)  # 0.1 + 0.5 + 0.3
        self.assertEqual(report.avg_step_time, 0.3)  # 0.9 / 3
        self.assertIn("复杂性评估", report.slowest_step)  # 最慢的步骤
        self.assertIn("初始化", report.fastest_step)      # 最快的步骤
        
        # 检查步骤时间分解
        self.assertIn("初始化", report.step_time_breakdown)
        self.assertIn("复杂性评估", report.step_time_breakdown)
        self.assertIn("身体执行", report.step_time_breakdown)
    
    def test_visualize_execution_flow(self):
        """测试执行流程可视化"""
        flow_chart = DebugUtils.visualize_execution_flow(self.step_results)
        
        self.assertIsInstance(flow_chart, str)
        self.assertIn("认知循环执行流程", flow_chart)
        self.assertIn("初始化", flow_chart)
        self.assertIn("复杂性评估", flow_chart)
        self.assertIn("身体执行", flow_chart)
        self.assertIn("总步骤: 3", flow_chart)
        self.assertIn("总时间: 0.900s", flow_chart)
    
    def test_export_import_debug_session(self):
        """测试调试会话导入导出"""
        # 创建测试调试状态
        debug_state = DebugState()
        debug_state.current_step = StepType.STATE_ANALYSIS
        debug_state.cycle_count = 2
        debug_state.step_history = self.step_results
        
        # 导出到临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # 测试导出
            success = DebugUtils.export_debug_session(debug_state, temp_file)
            self.assertTrue(success)
            
            # 验证文件存在且有内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIn("version", data)
            self.assertIn("debug_state", data)
            self.assertIn("step_history", data)
            self.assertEqual(len(data["step_history"]), 3)
            
            # 测试导入
            imported_data = DebugUtils.import_debug_session(temp_file)
            self.assertIsNotNone(imported_data)
            self.assertEqual(imported_data["debug_state"]["cycle_count"], 2)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        # 使用真实的但简化的智能体进行集成测试
        self.agent = Mock(spec=CognitiveAgent)
        self.agent.max_cycles = 2
        self.agent.enable_meta_cognition= False
        self.agent.evaluation_mode = "internal"
        
        # 模拟各层的返回值
        self.agent._can_handle_directly.return_value = False  # 强制使用认知循环
        self.agent.ego = Mock()
        self.agent.ego.analyze_current_state.return_value = "当前状态分析结果"
        self.agent.ego.decide_next_action.return_value = "继续循环"
        
        self.agent.id = Mock()
        self.agent.id.evaluate_task_completion.return_value = "目标已达成"
        
        self.agent.body = Mock()
        mock_result = Result(True, "print('test')", "test", "", "执行成功")
        self.agent.body.execute_sync.return_value = mock_result
        
        self.debugger = CognitiveDebugger(self.agent)
    
    def test_complete_debug_workflow(self):
        """测试完整的调试工作流"""
        # 开始调试
        self.debugger.start_debug("执行测试任务")
        
        # 执行几个步骤
        steps_executed = 0
        max_steps = 10  # 防止无限循环
        
        while not self.debugger.debug_state.is_finished and steps_executed < max_steps:
            step_result = self.debugger.run_one_step()
            if step_result:
                steps_executed += 1
                
                # 验证步骤结果的基本属性
                self.assertIsInstance(step_result.step_type, StepType)
                self.assertIsNotNone(step_result.step_id)
                self.assertIsNotNone(step_result.timestamp)
                self.assertIsNotNone(step_result.agent_layer)
                self.assertGreaterEqual(step_result.execution_time, 0)
            else:
                break
        
        # 验证执行了一些步骤
        self.assertGreater(steps_executed, 0)
        self.assertGreater(len(self.debugger.debug_state.step_history), 0)
        
        # 获取性能报告
        report = self.debugger.get_performance_report()
        self.assertIsInstance(report, PerformanceReport)
        self.assertGreater(report.total_time, 0)
        
        # 获取执行流程可视化
        flow_chart = self.debugger.visualize_execution_flow()
        self.assertIsInstance(flow_chart, str)
        self.assertIn("认知循环执行流程", flow_chart)
    
    def test_breakpoint_integration(self):
        """测试断点集成功能"""
        # 设置断点
        bp_id = self.debugger.set_breakpoint(
            StepType.STATE_ANALYSIS,
            description="集成测试断点"
        )
        
        # 开始调试
        self.debugger.start_debug("断点测试任务")
        
        # 执行到断点
        steps_before_breakpoint = 0
        max_steps = 10
        
        while steps_before_breakpoint < max_steps:
            step_result = self.debugger.run_one_step()
            if step_result is None:  # 断点触发
                break
            steps_before_breakpoint += 1
        
        # 验证在合理步数内触发了断点
        self.assertLess(steps_before_breakpoint, max_steps)
        
        # 移除断点并继续
        self.debugger.remove_breakpoint(bp_id)
        
        # 继续执行应该不会再次停在断点
        step_result = self.debugger.run_one_step()
        self.assertIsNotNone(step_result)


class TestPerformanceAndStress(unittest.TestCase):
    """性能和压力测试"""
    
    def test_large_step_history_performance(self):
        """测试大量步骤历史的性能"""
        from datetime import datetime
        import time
        
        # 创建大量测试步骤
        large_step_results = []
        for i in range(1000):
            step_result = StepResult(
                step_type=StepType.STATE_ANALYSIS,
                step_id=f"step_{i}",
                timestamp=datetime.now(),
                input_data=f"input_{i}",
                output_data=f"output_{i}",
                execution_time=0.001,
                agent_layer="Ego",
                next_step=StepType.DECISION_MAKING
            )
            large_step_results.append(step_result)
        
        # 测试性能分析的执行时间
        start_time = time.time()
        report = DebugUtils.analyze_performance(large_step_results)
        analysis_time = time.time() - start_time
        
        # 性能分析应该在合理时间内完成（< 1秒）
        self.assertLess(analysis_time, 1.0)
        self.assertEqual(len(large_step_results), 1000)
        self.assertGreater(report.total_time, 0)
    
    def test_memory_usage_with_snapshots(self):
        """测试状态快照的内存使用"""
        debugger = CognitiveDebugger(Mock())
        
        # 模拟执行大量步骤以触发快照保存
        for i in range(50):  # 每5步保存一次快照，总共10个快照
            step_result = StepResult(
                step_type=StepType.STATE_ANALYSIS,
                step_id=f"step_{i}",
                timestamp=Mock(),
                input_data=f"input_{i}",
                output_data=f"output_{i}",
                execution_time=0.001,
                agent_layer="Ego",
                next_step=StepType.DECISION_MAKING
            )
            debugger._update_debug_state(step_result)
        
        # 验证快照数量限制
        self.assertLessEqual(len(debugger.debug_state.state_snapshots), 20)
        self.assertEqual(len(debugger.debug_state.step_history), 50)


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行 CognitiveDebugger 完整测试套件")
    print("=" * 80)
    
    # 创建测试套件
    test_classes = [
        TestDataStructures,
        TestBreakpointManager,
        TestStepExecutor,
        TestCognitiveDebugger,
        TestDebugUtils,
        TestIntegration,
        TestPerformanceAndStress
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n🧪 运行 {test_class.__name__} 测试...")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        class_total = result.testsRun
        class_failures = len(result.failures) + len(result.errors)
        class_passed = class_total - class_failures
        
        total_tests += class_total
        passed_tests += class_passed
        
        if class_failures > 0:
            failed_tests.extend([f"{test_class.__name__}.{test}" for test, _ in result.failures + result.errors])
        
        status = "✅" if class_failures == 0 else "❌"
        print(f"   {status} {class_passed}/{class_total} 测试通过")
        
        if result.failures:
            print(f"   ❌ 失败的测试:")
            for test, traceback in result.failures:
                print(f"      - {test}")
        
        if result.errors:
            print(f"   💥 错误的测试:")
            for test, traceback in result.errors:
                print(f"      - {test}")
    
    # 打印总结
    print("\n" + "=" * 80)
    print(f"📊 测试总结:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过测试: {passed_tests}")
    print(f"   失败测试: {total_tests - passed_tests}")
    print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ 失败的测试列表:")
        for test in failed_tests:
            print(f"   - {test}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！CognitiveDebugger 功能完整且稳定")
        return True
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败，需要进一步调试")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)