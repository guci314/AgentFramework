#!/usr/bin/env python3
"""
调试AI评估逻辑
==============

检查为什么AI评估器对通过的测试返回失败。
"""

import subprocess
import sys
from static_workflow.result_evaluator import MockTestResultEvaluator
from agent_base import Result


def debug_ai_evaluation():
    """调试AI评估逻辑"""
    
    print("🔍 调试AI评估逻辑")
    print("=" * 60)
    
    # 运行实际测试
    result = subprocess.run([
        sys.executable, "-m", "unittest", "test_calculator.py", "-v"
    ], capture_output=True, text=True)
    
    print("📊 实际测试结果:")
    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {repr(result.stdout)}")
    print(f"STDERR: {repr(result.stderr)}")
    
    # 创建Result对象模拟工作流中的情况
    test_result = Result(
        success=(result.returncode == 0),
        code="python -m unittest test_calculator.py -v",
        stdout=result.stdout,
        stderr=result.stderr,
        return_value=result.returncode
    )
    
    print(f"\n📦 Result对象:")
    print(f"success: {test_result.success}")
    print(f"stdout: {repr(test_result.stdout)}")
    print(f"stderr: {repr(test_result.stderr)}")
    print(f"return_value: {test_result.return_value}")
    
    # 使用MockTestResultEvaluator评估
    evaluator = MockTestResultEvaluator()
    
    # 方式1: 直接传递参数
    evaluation1 = evaluator.evaluate_test_result(
        result_stdout=test_result.stdout,
        result_stderr=test_result.stderr,
        result_return_value=str(test_result.return_value)
    )
    
    print(f"\n🤖 方式1 - 直接参数评估:")
    print(f"通过: {evaluation1['passed']}")
    print(f"置信度: {evaluation1['confidence']}")
    print(f"理由: {evaluation1['reason']}")
    
    # 方式2: 使用Result对象的字段
    evaluation2 = evaluator.evaluate_test_result(
        result_code=test_result.code,
        result_stdout=test_result.stdout,
        result_stderr=test_result.stderr,
        result_return_value=test_result.return_value
    )
    
    print(f"\n🤖 方式2 - Result对象字段评估:")
    print(f"通过: {evaluation2['passed']}")
    print(f"置信度: {evaluation2['confidence']}")
    print(f"理由: {evaluation2['reason']}")
    
    # 检查工作流中可能的数据传递问题
    print(f"\n🔍 数据分析:")
    combined_output = f"{test_result.stdout} {test_result.stderr} {test_result.return_value}".lower()
    print(f"合并输出: {repr(combined_output)}")
    
    fail_indicators = [
        "failed", "error", "exception", "traceback", 
        "assertion error", "test failed", "0 passed",
        "failure", "fatal", "critical", "1 failed", 
        "2 failed", "3 failed", "4 failed", "5 failed"
    ]
    
    success_indicators = [
        "passed", "success", "ok", "all tests passed",
        "build successful", "completed successfully"
    ]
    
    found_fail = [ind for ind in fail_indicators if ind in combined_output]
    found_success = [ind for ind in success_indicators if ind in combined_output]
    
    print(f"找到的失败指标: {found_fail}")
    print(f"找到的成功指标: {found_success}")
    print(f"包含'0 failed': {'0 failed' in combined_output}")
    
    # 检查AI评估器内部逻辑
    print(f"\n🧮 评估逻辑检查:")
    has_failures = any(indicator in combined_output for indicator in fail_indicators)
    has_success = any(indicator in combined_output for indicator in success_indicators)
    has_zero_failed = "0 failed" in combined_output
    
    print(f"has_failures (before 0 failed check): {has_failures}")
    print(f"has_success: {has_success}")
    print(f"has_zero_failed: {has_zero_failed}")
    
    if has_zero_failed:
        has_failures = False
        print(f"has_failures (after 0 failed check): {has_failures}")
    
    if has_failures:
        expected_result = False
        expected_reason = "检测到失败指标"
    elif has_success:
        expected_result = True
        expected_reason = "检测到成功指标"
    else:
        expected_result = True
        expected_reason = "默认判断为通过"
    
    print(f"预期结果: {expected_result}")
    print(f"预期理由: {expected_reason}")
    
    # 验证评估是否正确
    if evaluation1['passed'] == expected_result:
        print(f"\n✅ AI评估逻辑正确")
    else:
        print(f"\n❌ AI评估逻辑有问题")
        print(f"   评估结果: {evaluation1['passed']}")
        print(f"   预期结果: {expected_result}")


if __name__ == "__main__":
    debug_ai_evaluation()