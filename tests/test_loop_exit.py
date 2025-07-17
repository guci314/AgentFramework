#!/usr/bin/env python3
"""
测试循环退出机制
==============

模拟一个简单的工作流来验证max_iterations是否正确工作。
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from static_workflow.workflow_definitions import *
from static_workflow.static_workflow_engine import StaticWorkflowEngine
from agent_base import Result

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockStepExecutor:
    """模拟步骤执行器"""
    
    def __init__(self):
        self.execution_count = {}
    
    def execute_step(self, step: WorkflowStep) -> Result:
        """模拟步骤执行"""
        step_id = step.id
        count = self.execution_count.get(step_id, 0) + 1
        self.execution_count[step_id] = count
        
        print(f"🚀 执行步骤 {step_id} (第{count}次)")
        
        if step_id == "test_step":
            # 模拟测试总是失败
            return Result(
                success=True,  # 步骤执行成功
                code="python -m unittest test.py",
                stdout="",
                stderr="FAILED (errors=1)",
                return_value="1 failed, 4 passed"
            )
        
        elif step_id == "fix_step":
            # 模拟修复步骤总是成功，但不解决问题
            return Result(
                success=True,
                code="# fix code",
                stdout="Fixed some issues",
                stderr="",
                return_value="success"
            )
        
        else:
            # 其他步骤正常成功
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
            name="loop_exit_test",
            version="1.0",
            description="测试循环退出机制"
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
                    ai_confidence_threshold=0.8,
                    ai_fallback_condition="last_result.success == True",
                    success_next="complete_step",
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
                    loop_condition=None,  # 使用方案1的配置
                    loop_target="test_step",
                    max_iterations=3,
                    exit_on_max="complete_step"
                )
            ),
            WorkflowStep(
                id="complete_step",
                name="完成",
                agent_name="reporter",
                instruction="生成报告",
                control_flow=ControlFlow(type=ControlFlowType.TERMINAL)
            )
        ]
    )


def test_loop_exit_mechanism():
    """测试循环退出机制"""
    
    print("🧪 测试循环退出机制")
    print("=" * 60)
    
    # 创建工作流引擎（不使用AI评估器，我们手动控制评估结果）
    engine = StaticWorkflowEngine(max_parallel_workers=1)
    
    # 创建模拟执行器
    mock_executor = MockStepExecutor()
    engine.set_step_executor(mock_executor.execute_step)
    
    # 创建测试工作流
    workflow_def = create_test_workflow()
    
    # 手动修改评估器以强制返回失败结果
    class ForcedFailureEvaluator:
        def evaluate_control_flow_condition(self, control_flow, default_success_state=True):
            if getattr(control_flow, 'ai_evaluate_test_result', False):
                print("   🤖 AI评估: 强制返回失败")
                return False  # 强制返回失败，模拟测试一直不通过
            return default_success_state
        
        def set_context(self, **kwargs):
            pass
        
        def evaluate_condition(self, condition):
            return True
        
        def interpolate_value(self, value):
            return value
    
    engine.evaluator = ForcedFailureEvaluator()
    
    # 执行工作流
    print("\n🚀 开始执行工作流...")
    result = engine.execute_workflow(workflow_def)
    
    print(f"\n📊 执行结果:")
    print(f"   成功: {result.success}")
    print(f"   总步骤: {result.total_steps}")
    print(f"   完成步骤: {result.completed_steps}")
    print(f"   执行时间: {result.execution_time:.2f}秒")
    
    print(f"\n📈 步骤执行统计:")
    for step_id, count in mock_executor.execution_count.items():
        print(f"   {step_id}: {count}次")
    
    # 验证循环退出
    fix_step_count = mock_executor.execution_count.get("fix_step", 0)
    test_step_count = mock_executor.execution_count.get("test_step", 0)
    
    print(f"\n🔍 循环退出验证:")
    print(f"   fix_step执行次数: {fix_step_count} (期望: ≤3)")
    print(f"   test_step执行次数: {test_step_count} (期望: ≤4)")  # 初始1次 + 最多3次循环
    
    if fix_step_count <= 3 and test_step_count <= 4:
        print("✅ 循环退出机制工作正常")
        return True
    else:
        print("❌ 循环退出机制有问题")
        return False


if __name__ == "__main__":
    success = test_loop_exit_mechanism()
    sys.exit(0 if success else 1)