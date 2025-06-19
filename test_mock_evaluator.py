#!/usr/bin/env python3
"""
测试MockTestResultEvaluator的评估逻辑
==================================

验证AI评估器是否能正确判断测试结果。
"""

import subprocess
import sys
from static_workflow.result_evaluator import MockTestResultEvaluator


def test_mock_evaluator_with_real_output():
    """测试MockTestResultEvaluator是否能正确评估真实的unittest输出"""
    
    print("🧪 测试MockTestResultEvaluator评估逻辑")
    print("=" * 60)
    
    # 运行实际的测试并捕获输出
    result = subprocess.run([
        sys.executable, "-m", "unittest", "test_calculator.py", "-v"
    ], capture_output=True, text=True)
    
    print("📊 实际测试输出:")
    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    
    # 使用MockTestResultEvaluator评估
    evaluator = MockTestResultEvaluator()
    evaluation = evaluator.evaluate_test_result(
        result_stdout=result.stdout,
        result_stderr=result.stderr,
        result_return_value=str(result.returncode)
    )
    
    print("\n🤖 MockTestResultEvaluator评估结果:")
    print(f"通过: {evaluation['passed']}")
    print(f"置信度: {evaluation['confidence']}")
    print(f"理由: {evaluation['reason']}")
    print(f"测试类型: {evaluation['test_type']}")
    print(f"详细信息: {evaluation['details']}")
    
    # 验证评估是否正确
    expected_passed = (result.returncode == 0)
    actual_passed = evaluation['passed']
    
    print(f"\n✅ 评估验证:")
    print(f"期望结果: {'通过' if expected_passed else '失败'}")
    print(f"AI评估: {'通过' if actual_passed else '失败'}")
    
    if expected_passed == actual_passed:
        print("✅ AI评估结果正确！")
        return True
    else:
        print("❌ AI评估结果错误！")
        return False


def test_various_test_outputs():
    """测试各种测试输出场景"""
    
    print("\n🔍 测试各种输出场景")
    print("=" * 60)
    
    evaluator = MockTestResultEvaluator()
    
    test_cases = [
        {
            "name": "成功的unittest输出",
            "stderr": "test_add ... ok\ntest_sub ... ok\n\nRan 2 tests in 0.001s\n\nOK",
            "expected": True
        },
        {
            "name": "失败的unittest输出",
            "stderr": "test_add ... ok\ntest_fail ... FAILED\n\nRan 2 tests in 0.001s\n\nFAILED (failures=1)",
            "expected": False
        },
        {
            "name": "包含0 failed的成功输出",
            "stderr": "Ran 5 tests in 0.001s\n\nOK\n0 failed",
            "expected": True
        },
        {
            "name": "错误的测试输出",
            "stderr": "ERROR: test_divide_by_zero\nRan 5 tests\nFAILED (errors=1)",
            "expected": False
        }
    ]
    
    all_correct = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}:")
        
        evaluation = evaluator.evaluate_test_result(
            result_stderr=test_case['stderr']
        )
        
        result_correct = evaluation['passed'] == test_case['expected']
        print(f"   输入: {test_case['stderr'][:50]}...")
        print(f"   期望: {'通过' if test_case['expected'] else '失败'}")
        print(f"   AI评估: {'通过' if evaluation['passed'] else '失败'}")
        print(f"   置信度: {evaluation['confidence']}")
        print(f"   结果: {'✅ 正确' if result_correct else '❌ 错误'}")
        
        if not result_correct:
            all_correct = False
    
    return all_correct


def main():
    """主函数"""
    
    print("🤖 MockTestResultEvaluator测试工具")
    print("=" * 60)
    
    # 测试真实输出
    real_test_success = test_mock_evaluator_with_real_output()
    
    # 测试各种场景
    scenario_test_success = test_various_test_outputs()
    
    print(f"\n📋 测试总结:")
    print(f"真实输出测试: {'✅ 通过' if real_test_success else '❌ 失败'}")
    print(f"场景测试: {'✅ 通过' if scenario_test_success else '❌ 失败'}")
    
    overall_success = real_test_success and scenario_test_success
    print(f"总体结果: {'✅ 所有测试通过' if overall_success else '❌ 部分测试失败'}")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)