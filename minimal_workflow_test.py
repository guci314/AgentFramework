#!/usr/bin/env python3
"""
最小工作流测试
=============

创建一个最小化的工作流测试来重现循环问题。
"""

import os
import logging
import subprocess
import sys
from static_workflow.workflow_definitions import *
from static_workflow.static_workflow_engine import StaticWorkflowEngine
from agent_base import Result
from debug_workflow_ai_evaluation import DebugMockTestResultEvaluator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MinimalStepExecutor:
    """最小步骤执行器，模拟运行测试"""
    
    def __init__(self):
        self.execution_count = {}
    
    def execute_step(self, step: WorkflowStep) -> Result:
        """模拟步骤执行"""
        step_id = step.id
        count = self.execution_count.get(step_id, 0) + 1
        self.execution_count[step_id] = count
        
        print(f"🚀 执行步骤 {step_id} (第{count}次): {step.name}")
        
        if step_id == "test_step":
            # 运行真实的测试
            result = subprocess.run([
                sys.executable, "-m", "unittest", "test_calculator.py", "-v"
            ], capture_output=True, text=True)
            
            test_result = Result(
                success=(result.returncode == 0),
                code="python -m unittest test_calculator.py -v",
                stdout=result.stdout,
                stderr=result.stderr,
                return_value=result.returncode
            )
            
            print(f"   测试结果: success={test_result.success}, returncode={result.returncode}")
            print(f"   stderr前100字符: {repr(result.stderr[:100])}")
            
            return test_result
        
        elif step_id == "fix_step":
            # 模拟修复步骤
            print(f"   执行修复操作 (第{count}次)")
            return Result(
                success=True,
                code="# fix code",
                stdout="Fixed code",
                stderr="",
                return_value="success"
            )
        
        else:
            # 其他步骤
            return Result(
                success=True,
                code="# other step",
                stdout="Step completed",
                stderr="",
                return_value="success"
            )


def create_minimal_workflow() -> WorkflowDefinition:
    """创建最小测试工作流"""
    
    return WorkflowDefinition(
        workflow_metadata=WorkflowMetadata(
            name="minimal_test",
            version="1.0",
            description="最小循环测试"
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


def test_minimal_workflow():
    """测试最小工作流"""
    
    print("🧪 测试最小工作流循环问题")
    print("=" * 60)
    
    # 创建调试AI评估器
    debug_ai_evaluator = DebugMockTestResultEvaluator()
    
    # 创建工作流引擎
    engine = StaticWorkflowEngine(max_parallel_workers=1, ai_evaluator=debug_ai_evaluator)
    
    # 创建最小执行器
    executor = MinimalStepExecutor()
    engine.set_step_executor(executor.execute_step)
    
    # 创建工作流
    workflow_def = create_minimal_workflow()
    
    print("📋 工作流步骤:")
    for step in workflow_def.steps:
        print(f"  {step.id}: {step.name}")
        if step.control_flow:
            cf = step.control_flow
            if cf.type == ControlFlowType.CONDITIONAL:
                print(f"    条件: AI评估={getattr(cf, 'ai_evaluate_test_result', False)}")
                print(f"    成功→{cf.success_next}, 失败→{cf.failure_next}")
            elif cf.type == ControlFlowType.LOOP:
                print(f"    循环: 目标={cf.loop_target}, 最大={cf.max_iterations}, 退出={cf.exit_on_max}")
    
    print(f"\n🚀 开始执行工作流 (最多10步)...")
    
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
    
    # 分析是否有循环问题
    test_count = executor.execution_count.get("test_step", 0)
    fix_count = executor.execution_count.get("fix_step", 0)
    
    if test_count > 1 and fix_count > 0:
        print(f"\n❌ 检测到循环问题:")
        print(f"   test_step执行了{test_count}次")
        print(f"   fix_step执行了{fix_count}次")
        if test_count > 4:  # 1次初始 + 最多3次循环
            print(f"   🔥 可能进入了无限循环！")
    else:
        print(f"\n✅ 未检测到循环问题")


if __name__ == "__main__":
    test_minimal_workflow()