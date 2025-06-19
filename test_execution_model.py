#!/usr/bin/env python3
"""
测试新的执行实例模型
==================

验证执行实例模型能够正确处理循环场景，解决状态语义冲突问题。
"""

import unittest
import logging
from datetime import datetime

from static_workflow.workflow_definitions import (
    WorkflowDefinition, WorkflowStep, WorkflowMetadata, ControlFlow, ControlFlowType,
    StepExecution, WorkflowExecutionContext, StepStatus
)
from static_workflow.static_workflow_engine import StaticWorkflowEngine

# 设置日志级别
logging.basicConfig(level=logging.INFO)

class TestExecutionModel(unittest.TestCase):
    """测试执行实例模型"""
    
    def setUp(self):
        """设置测试数据"""
        self.execution_counters = {}  # 模拟执行计数器
        
    def mock_step_executor(self, step: WorkflowStep):
        """模拟步骤执行器"""
        step_id = step.id
        
        # 统计执行次数
        if step_id not in self.execution_counters:
            self.execution_counters[step_id] = 0
        self.execution_counters[step_id] += 1
        
        # 模拟不同的执行结果
        if step_id == "test_step":
            # test_step前2次失败，第3次成功
            if self.execution_counters[step_id] < 3:
                return {"success": False, "message": f"测试失败 (第{self.execution_counters[step_id]}次)"}
            else:
                return {"success": True, "message": f"测试成功 (第{self.execution_counters[step_id]}次)"}
        
        elif step_id == "fix_step":
            # fix_step总是成功
            return {"success": True, "message": f"修复完成 (第{self.execution_counters[step_id]}次)"}
        
        else:
            return {"success": True, "message": "默认成功"}
    
    def test_execution_context_basic_functions(self):
        """测试执行上下文的基本功能"""
        print("\n=== 测试执行上下文基本功能 ===")
        
        # 创建执行上下文
        context = WorkflowExecutionContext(workflow_id="test_workflow")
        
        # 测试创建执行实例
        execution1 = context.create_execution("step1")
        self.assertEqual(execution1.step_id, "step1")
        self.assertEqual(execution1.iteration, 1)
        self.assertEqual(execution1.status, StepStatus.PENDING)
        
        # 测试重复执行同一步骤
        execution2 = context.create_execution("step1")
        self.assertEqual(execution2.iteration, 2)
        
        # 测试获取当前执行实例
        current = context.get_current_execution("step1")
        self.assertEqual(current.iteration, 2)
        
        # 测试执行历史
        history = context.get_execution_history("step1")
        self.assertEqual(len(history), 2)
        
        print("✅ 执行上下文基本功能测试通过")
    
    def test_execution_statistics(self):
        """测试执行统计功能"""
        print("\n=== 测试执行统计功能 ===")
        
        context = WorkflowExecutionContext(workflow_id="test_workflow")
        
        # 创建多个执行实例并设置状态
        exec1 = context.create_execution("step1")
        exec1.status = StepStatus.COMPLETED
        
        exec2 = context.create_execution("step1") 
        exec2.status = StepStatus.FAILED
        
        exec3 = context.create_execution("step2")
        exec3.status = StepStatus.COMPLETED
        
        # 测试步骤统计
        step1_stats = context.get_step_statistics("step1")
        self.assertEqual(step1_stats["total_executions"], 2)
        self.assertEqual(step1_stats["completed_executions"], 1)
        self.assertEqual(step1_stats["failed_executions"], 1)
        self.assertEqual(step1_stats["success_rate"], 0.5)
        
        # 测试工作流统计
        workflow_stats = context.get_workflow_statistics()
        self.assertEqual(workflow_stats["total_step_executions"], 3)
        self.assertEqual(workflow_stats["completed_step_executions"], 2)
        self.assertEqual(workflow_stats["failed_step_executions"], 1)
        self.assertEqual(workflow_stats["unique_steps_executed"], 2)
        
        print("✅ 执行统计功能测试通过")
    
    def test_step_execution_properties(self):
        """测试步骤执行实例的属性"""
        print("\n=== 测试步骤执行实例属性 ===")
        
        execution = StepExecution(
            execution_id="test_exec_1",
            step_id="test_step",
            iteration=1
        )
        
        # 测试未完成状态
        self.assertFalse(execution.is_finished)
        self.assertIsNone(execution.duration)
        
        # 设置执行时间并完成
        execution.start_time = datetime.now()
        execution.end_time = datetime.now()
        execution.status = StepStatus.COMPLETED
        
        # 测试完成状态
        self.assertTrue(execution.is_finished)
        self.assertIsNotNone(execution.duration)
        self.assertGreaterEqual(execution.duration, 0)
        
        print("✅ 步骤执行实例属性测试通过")
    
    def test_should_execute_step_logic(self):
        """测试步骤执行判断逻辑"""
        print("\n=== 测试步骤执行判断逻辑 ===")
        
        context = WorkflowExecutionContext(workflow_id="test_workflow")
        
        # 第一次执行：应该执行
        self.assertTrue(context.should_execute_step("step1"))
        
        # 创建未完成的执行实例
        exec1 = context.create_execution("step1")
        exec1.status = StepStatus.RUNNING
        
        # 有运行中的执行：不应该重复执行
        self.assertFalse(context.should_execute_step("step1"))
        
        # 完成执行
        exec1.status = StepStatus.COMPLETED
        
        # 已完成的执行：在循环中可以重新执行
        self.assertTrue(context.should_execute_step("step1"))
        
        print("✅ 步骤执行判断逻辑测试通过")

if __name__ == '__main__':
    print("🧪 开始测试新的执行实例模型")
    print("=" * 50)
    unittest.main(verbosity=2)