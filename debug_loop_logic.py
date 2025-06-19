#!/usr/bin/env python3
"""
调试循环逻辑问题
==============

分析为什么会出现无限循环。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from static_workflow.workflow_definitions import ControlFlow, ControlFlowType
from static_workflow.static_workflow_engine import WorkflowState
from static_workflow.control_flow_evaluator import ControlFlowEvaluator 
from static_workflow.result_evaluator import MockTestResultEvaluator
from agent_base import Result


def debug_loop_logic():
    """调试循环逻辑"""
    
    print("🔍 调试循环逻辑问题")
    print("=" * 60)
    
    # 创建模拟的循环控制流（step4的配置）
    loop_control_flow = ControlFlow(
        type=ControlFlowType.LOOP,
        loop_condition=None,  # 方案1：设为None
        loop_target="step3",
        max_iterations=3,
        exit_on_max="step5"
    )
    
    # 创建模拟的工作流状态
    workflow_state = WorkflowState()
    
    # 创建评估器
    ai_evaluator = MockTestResultEvaluator()
    evaluator = ControlFlowEvaluator(ai_evaluator=ai_evaluator)
    
    # 模拟循环执行过程
    print("\n📋 模拟循环执行:")
    
    for iteration in range(5):  # 模拟5次迭代
        loop_key = f"loop_step4"
        current_count = workflow_state.loop_counters.get(loop_key, 0)
        
        print(f"\n--- 迭代 {iteration + 1} ---")
        print(f"当前循环计数: {current_count}")
        
        # 检查最大迭代次数
        max_iterations = loop_control_flow.max_iterations
        if max_iterations and current_count >= max_iterations:
            print(f"✅ 达到最大循环次数 {max_iterations}，应该退出循环")
            print(f"退出目标: {loop_control_flow.exit_on_max}")
            break
        
        # 评估循环条件
        should_continue_loop = True
        if loop_control_flow.loop_condition:
            should_continue_loop = evaluator.evaluate_condition(loop_control_flow.loop_condition)
            print(f"循环条件评估: {should_continue_loop}")
        else:
            print("循环条件为None，默认should_continue_loop=True")
        
        # 模拟step4执行成功（修复代码步骤通常会成功）
        step4_success = True
        print(f"Step4执行结果: {'成功' if step4_success else '失败'}")
        
        # 判断是否继续循环
        if should_continue_loop and step4_success:
            # 继续循环
            workflow_state.loop_counters[loop_key] = current_count + 1
            print(f"✨ 继续循环，回到: {loop_control_flow.loop_target}")
            print(f"循环计数器更新为: {workflow_state.loop_counters[loop_key]}")
        else:
            print(f"❌ 不满足循环条件，应该退出")
            break
    
    print(f"\n最终循环计数器: {workflow_state.loop_counters}")


def debug_test_step_evaluation():
    """调试测试步骤的AI评估"""
    
    print("\n" + "=" * 60)
    print("🤖 调试测试步骤AI评估")
    print("=" * 60)
    
    ai_evaluator = MockTestResultEvaluator()
    evaluator = ControlFlowEvaluator(ai_evaluator=ai_evaluator)
    
    # 模拟step3的条件控制流
    test_control_flow = ControlFlow(
        type=ControlFlowType.CONDITIONAL,
        ai_evaluate_test_result=True,
        ai_confidence_threshold=0.8,
        ai_fallback_condition="last_result.success == True",
        success_next="step5",
        failure_next="step4"
    )
    
    # 模拟实际的unittest输出
    test_result = Result(
        success=True,
        code="python -m unittest test_calculator.py", 
        stdout="",
        stderr=".....\n----------------------------------------------------------------------\nRan 5 tests in 0.000s\n\nOK",
        return_value="5 tests passed"
    )
    
    # 设置评估上下文
    evaluator.set_context(step_result=test_result)
    
    # 进行条件评估
    condition_result = evaluator.evaluate_control_flow_condition(test_control_flow, True)
    
    print(f"测试结果: {test_result}")
    print(f"AI评估结果: {'通过' if condition_result else '失败'}")
    print(f"下一步: {test_control_flow.success_next if condition_result else test_control_flow.failure_next}")


if __name__ == "__main__":
    debug_loop_logic()
    debug_test_step_evaluation()