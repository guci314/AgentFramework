#!/usr/bin/env python3
"""
测试循环修复
===========

验证修复后的循环逻辑是否能正确处理已完成步骤的重新执行。
"""

import os
import logging
import sys
from static_workflow.workflow_definitions import *
from static_workflow.static_workflow_engine import StaticWorkflowEngine
from agent_base import Result

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestStepExecutor:
    """测试步骤执行器"""
    
    def __init__(self):
        self.execution_count = {}
        self.test_fail_count = 2  # 前2次测试失败，第3次成功
    
    def execute_step(self, step: WorkflowStep) -> Result:
        """模拟步骤执行"""
        step_id = step.id
        count = self.execution_count.get(step_id, 0) + 1
        self.execution_count[step_id] = count
        
        print(f"🚀 执行步骤 {step_id} (第{count}次): {step.name}")
        print(f"   步骤状态: {step.status.value}")
        
        if step_id == "test_step":
            # 前几次测试失败，最后一次成功
            if count <= self.test_fail_count:
                print(f"   模拟测试失败 (第{count}次)")
                return Result(
                    success=True,  # 步骤执行成功
                    code="python -m unittest test.py",
                    stdout="",
                    stderr="FAILED (errors=1)",
                    return_value="test failed"
                )
            else:
                print(f"   模拟测试成功 (第{count}次)")
                return Result(
                    success=True,
                    code="python -m unittest test.py",
                    stdout="",
                    stderr="Ran 5 tests in 0.001s\n\nOK",
                    return_value="test passed"
                )
        
        elif step_id == "fix_step":
            print(f"   模拟修复代码 (第{count}次)")
            return Result(
                success=True,
                code="# fix code",
                stdout="Fixed issues",
                stderr="",
                return_value="fix completed"
            )
        
        else:
            return Result(
                success=True,
                code="# other step",
                stdout="Step completed",
                stderr="",
                return_value="success"
            )


def create_test_workflow() -> WorkflowDefinition:
    """创建测试工作流"""
    
    return WorkflowDefinition(
        workflow_metadata=WorkflowMetadata(
            name="loop_fix_test",
            version="1.0",
            description="测试循环修复"
        ),
        steps=[
            WorkflowStep(
                id="test_step",
                name="运行测试",
                agent_name="tester",
                instruction="运行测试",
                control_flow=ControlFlow(
                    type=ControlFlowType.CONDITIONAL,
                    ai_evaluate_test_result=True,
                    ai_confidence_threshold=0.5,
                    success_next="end_step",
                    failure_next="fix_step"
                )
            ),
            WorkflowStep(
                id="fix_step", 
                name="修复代码",
                agent_name="coder",
                instruction="修复代码",
                control_flow=ControlFlow(
                    type=ControlFlowType.LOOP,
                    loop_condition=None,
                    loop_target="test_step",
                    max_iterations=3,
                    exit_on_max="end_step"
                )
            ),
            WorkflowStep(
                id="end_step",
                name="结束",
                agent_name="reporter",
                instruction="完成",
                control_flow=ControlFlow(type=ControlFlowType.TERMINAL)
            )
        ]
    )


def test_loop_fix():
    """测试循环修复"""
    
    print("🧪 测试循环修复")
    print("=" * 60)
    
    # 创建AI评估器（强制前2次失败，第3次成功）
    class TestAIEvaluator:
        def __init__(self):
            self.evaluation_count = 0
        
        def evaluate_test_result(self, **kwargs):
            self.evaluation_count += 1
            stderr = kwargs.get("result_stderr", "")
            
            if "OK" in stderr:
                result = True
                reason = "测试通过"
            else:
                result = False
                reason = "测试失败"
            
            print(f"   🤖 AI评估第{self.evaluation_count}次: {'通过' if result else '失败'}")
            
            return {
                "passed": result,
                "confidence": 0.8,
                "reason": reason,
                "test_type": "unit_test",
                "details": {}
            }
    
    # 创建工作流引擎
    ai_evaluator = TestAIEvaluator()
    engine = StaticWorkflowEngine(max_parallel_workers=1, ai_evaluator=ai_evaluator)
    
    # 创建测试执行器
    executor = TestStepExecutor()
    engine.set_step_executor(executor.execute_step)
    
    # 创建工作流
    workflow_def = create_test_workflow()
    
    print("📋 测试场景:")
    print("   - test_step前2次返回失败，第3次返回成功")
    print("   - fix_step每次都成功")
    print("   - 预期：循环2次后成功完成")
    
    print(f"\n🚀 开始执行工作流...")
    
    # 执行工作流
    result = engine.execute_workflow(workflow_def)
    
    print(f"\n📊 执行结果:")
    print(f"   成功: {result.success}")
    print(f"   总步骤: {result.total_steps}")
    print(f"   完成步骤: {result.completed_steps}")
    print(f"   执行时间: {result.execution_time:.2f}秒")
    
    print(f"\n📈 步骤执行统计:")
    for step_id, count in executor.execution_count.items():
        print(f"   {step_id}: {count}次")
    
    # 验证结果
    test_count = executor.execution_count.get("test_step", 0)
    fix_count = executor.execution_count.get("fix_step", 0)
    
    print(f"\n🔍 结果验证:")
    print(f"   test_step执行次数: {test_count} (期望: 3)")
    print(f"   fix_step执行次数: {fix_count} (期望: 2)")
    print(f"   AI评估次数: {ai_evaluator.evaluation_count} (期望: 3)")
    
    success = (
        result.success and 
        test_count == 3 and 
        fix_count == 2 and
        ai_evaluator.evaluation_count == 3
    )
    
    if success:
        print("✅ 循环修复成功！步骤能够正确重新执行")
    else:
        print("❌ 循环修复失败")
        if test_count > 3:
            print("   ⚠️  test_step执行次数过多，可能仍有死循环")
    
    return success


if __name__ == "__main__":
    success = test_loop_fix()
    sys.exit(0 if success else 1)