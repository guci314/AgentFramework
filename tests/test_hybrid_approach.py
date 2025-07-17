#!/usr/bin/env python3
"""
测试混合方案AI评估功能
=================

测试AI布尔字段和传统字符串条件的混合配置方案。
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from static_workflow.workflow_definitions import (
    WorkflowDefinition, WorkflowStep, ControlFlow, ControlFlowType,
    WorkflowMetadata, WorkflowLoader
)
from static_workflow.control_flow_evaluator import ControlFlowEvaluator
from static_workflow.result_evaluator import MockTestResultEvaluator
from agent_base import Result

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_workflow_with_ai_fields() -> WorkflowDefinition:
    """创建带有AI评估字段的测试工作流"""
    
    # 创建工作流步骤
    steps = [
        WorkflowStep(
            id="step1",
            name="运行测试",
            agent_name="test_agent",
            instruction="运行单元测试",
            control_flow=ControlFlow(
                type=ControlFlowType.CONDITIONAL,
                success_next="step2",
                failure_next="step3",
                # 使用AI布尔字段评估
                ai_evaluate_test_result=True,
                ai_confidence_threshold=0.7,
                ai_fallback_condition="last_result.success == True"
            )
        ),
        WorkflowStep(
            id="step2",
            name="测试通过",
            agent_name="report_agent",
            instruction="生成测试通过报告"
        ),
        WorkflowStep(
            id="step3",
            name="测试失败",
            agent_name="report_agent", 
            instruction="生成测试失败报告"
        )
    ]
    
    return WorkflowDefinition(
        workflow_metadata=WorkflowMetadata(
            name="AI混合评估测试工作流",
            version="1.0",
            description="测试AI布尔字段和传统条件的混合方案"
        ),
        steps=steps
    )


def create_test_workflow_with_string_condition() -> WorkflowDefinition:
    """创建带有传统字符串条件的测试工作流"""
    
    steps = [
        WorkflowStep(
            id="step1",
            name="运行测试",
            agent_name="test_agent",
            instruction="运行单元测试",
            control_flow=ControlFlow(
                type=ControlFlowType.CONDITIONAL,
                success_next="step2",
                failure_next="step3",
                # 使用传统条件表达式
                condition="ai_evaluate_test_result"
            )
        ),
        WorkflowStep(
            id="step2", 
            name="测试通过",
            agent_name="report_agent",
            instruction="生成测试通过报告"
        ),
        WorkflowStep(
            id="step3",
            name="测试失败",
            agent_name="report_agent",
            instruction="生成测试失败报告"
        )
    ]
    
    return WorkflowDefinition(
        workflow_metadata=WorkflowMetadata(
            name="传统条件评估测试工作流",
            version="1.0", 
            description="测试传统字符串条件方式的AI评估"
        ),
        steps=steps
    )


def test_workflow_validation():
    """测试工作流验证功能"""
    logger.info("=== 测试工作流验证功能 ===")
    
    # 测试有效的AI配置
    workflow1 = create_test_workflow_with_ai_fields()
    errors1 = workflow1.validate()
    logger.info(f"AI字段配置验证结果: {len(errors1)} 个错误")
    for error in errors1:
        logger.warning(f"  - {error}")
    
    # 测试传统条件配置
    workflow2 = create_test_workflow_with_string_condition()
    errors2 = workflow2.validate()
    logger.info(f"传统条件配置验证结果: {len(errors2)} 个错误")
    for error in errors2:
        logger.warning(f"  - {error}")
    
    # 测试无效的置信度阈值
    workflow3 = create_test_workflow_with_ai_fields()
    workflow3.steps[0].control_flow.ai_confidence_threshold = 1.5  # 无效值
    errors3 = workflow3.validate()
    logger.info(f"无效置信度阈值验证结果: {len(errors3)} 个错误")
    for error in errors3:
        logger.warning(f"  - {error}")
    
    # 测试同时使用AI字段和条件表达式的警告
    workflow4 = create_test_workflow_with_ai_fields()
    workflow4.steps[0].control_flow.condition = "last_result.success == True"  # 同时设置
    errors4 = workflow4.validate()
    logger.info(f"混合配置冲突验证结果: {len(errors4)} 个错误")
    for error in errors4:
        logger.warning(f"  - {error}")
    
    return len(errors1) == 0 and len(errors2) == 0 and len(errors3) > 0 and len(errors4) > 0


def test_ai_field_evaluation():
    """测试AI布尔字段评估"""
    logger.info("=== 测试AI布尔字段评估 ===")
    
    # 创建AI评估器
    ai_evaluator = MockTestResultEvaluator()
    
    # 创建控制流评估器
    evaluator = ControlFlowEvaluator(ai_evaluator=ai_evaluator)
    
    # 创建测试结果（模拟unittest输出到stderr的情况）
    test_result = Result(
        success=True,
        code="python -m unittest test_calculator.py",
        stdout="",  # unittest通常不向stdout输出
        stderr="Ran 5 tests in 0.123s\n\nOK",  # unittest输出到stderr
        return_value="0 failed, 5 passed"
    )
    
    # 设置评估上下文
    evaluator.set_context(step_result=test_result)
    
    # 创建控制流配置
    control_flow = ControlFlow(
        type=ControlFlowType.CONDITIONAL,
        ai_evaluate_test_result=True,
        ai_confidence_threshold=0.7,
        ai_fallback_condition="last_result.success == True"
    )
    
    # 测试AI评估
    result = evaluator.evaluate_control_flow_condition(control_flow)
    logger.info(f"AI字段评估结果: {result}")
    
    # 测试低置信度回退
    control_flow.ai_confidence_threshold = 0.9  # 设置高阈值
    result_fallback = evaluator.evaluate_control_flow_condition(control_flow)  
    logger.info(f"高阈值回退评估结果: {result_fallback}")
    
    # 测试unittest失败的情况
    failed_test_result = Result(
        success=True,  # 命令执行成功
        code="python -m unittest test_calculator.py",
        stdout="",
        stderr="Ran 5 tests in 0.123s\n\nFAILED (failures=2)",  # unittest失败输出
        return_value="2 failed, 3 passed"
    )
    
    evaluator.set_context(step_result=failed_test_result)
    control_flow.ai_confidence_threshold = 0.7  # 重置阈值
    failed_result = evaluator.evaluate_control_flow_condition(control_flow)
    logger.info(f"失败测试评估结果: {failed_result}")
    
    return result is True and failed_result is False


def test_string_condition_evaluation():
    """测试传统字符串条件评估"""
    logger.info("=== 测试传统字符串条件评估 ===")
    
    # 创建AI评估器
    ai_evaluator = MockTestResultEvaluator()
    
    # 创建控制流评估器
    evaluator = ControlFlowEvaluator(ai_evaluator=ai_evaluator)
    
    # 创建测试结果（模拟unittest输出到stderr的情况）
    test_result = Result(
        success=True,
        code="python -m unittest test_calculator.py",
        stdout="", 
        stderr="Ran 5 tests in 0.123s\n\nOK",
        return_value="0 failed, 5 passed"
    )
    
    # 设置评估上下文
    evaluator.set_context(step_result=test_result)
    
    # 测试传统条件评估
    result1 = evaluator.evaluate_condition("last_result.success == True")
    logger.info(f"传统条件评估结果: {result1}")
    
    # 测试AI字符串条件评估
    result2 = evaluator.evaluate_condition("ai_evaluate_test_result")
    logger.info(f"AI字符串条件评估结果: {result2}")
    
    return result1 is True and result2 is True


def test_workflow_serialization():
    """测试工作流序列化和反序列化"""
    logger.info("=== 测试工作流序列化 ===")
    
    # 创建测试工作流
    workflow = create_test_workflow_with_ai_fields()
    
    # 保存到临时文件
    temp_file = "temp_workflow_test.json"
    
    try:
        WorkflowLoader.save_to_file(workflow, temp_file)
        logger.info(f"工作流已保存到: {temp_file}")
        
        # 验证文件内容
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查AI字段是否正确保存
        step1_cf = data['steps'][0]['control_flow']
        ai_fields_present = (
            'ai_evaluate_test_result' in step1_cf and
            'ai_confidence_threshold' in step1_cf and 
            'ai_fallback_condition' in step1_cf
        )
        logger.info(f"AI字段保存检查: {ai_fields_present}")
        
        # 重新加载工作流
        loaded_workflow = WorkflowLoader.load_from_file(temp_file)
        logger.info(f"工作流重新加载成功: {loaded_workflow.workflow_metadata.name}")
        
        # 检查加载的AI字段
        loaded_cf = loaded_workflow.steps[0].control_flow
        ai_fields_loaded = (
            loaded_cf.ai_evaluate_test_result == True and
            loaded_cf.ai_confidence_threshold == 0.7 and
            loaded_cf.ai_fallback_condition == "last_result.success == True"
        )
        logger.info(f"AI字段加载检查: {ai_fields_loaded}")
        
        return ai_fields_present and ai_fields_loaded
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)


def run_all_tests():
    """运行所有测试"""
    logger.info("开始混合方案功能测试")
    
    tests = [
        ("工作流验证", test_workflow_validation),
        ("AI字段评估", test_ai_field_evaluation), 
        ("字符串条件评估", test_string_condition_evaluation),
        ("工作流序列化", test_workflow_serialization)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = "✓ 通过" if result else "✗ 失败"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"{test_name}: ✗ 异常 - {e}")
        
        logger.info("-" * 50)
    
    # 汇总结果
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    logger.info(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！混合方案实现成功。")
    else:
        logger.warning("⚠️  部分测试失败，需要检查实现。")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)