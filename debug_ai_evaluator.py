#!/usr/bin/env python3
"""
调试AI评估器问题
==============

测试MockTestResultEvaluator对unittest输出的判断结果。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from static_workflow.result_evaluator import MockTestResultEvaluator
from agent_base import Result


def test_evaluator_with_unittest_output():
    """测试评估器对实际unittest输出的判断"""
    
    evaluator = MockTestResultEvaluator()
    
    # 模拟实际的unittest成功输出（输出到stderr）
    test_scenarios = [
        {
            "name": "实际unittest成功输出",
            "result": Result(
                success=True,
                code="python -m unittest test_calculator.py",
                stdout="",
                stderr=".....\n----------------------------------------------------------------------\nRan 5 tests in 0.000s\n\nOK",
                return_value="5 tests passed"
            )
        },
        {
            "name": "pytest风格输出", 
            "result": Result(
                success=True,
                code="pytest test_calculator.py",
                stdout="",
                stderr="===== test session starts =====\ncollected 5 items\n\ntest_calculator.py .....                     [100%]\n\n===== 5 passed in 0.02s =====",
                return_value="5 passed"
            )
        },
        {
            "name": "简单成功信息",
            "result": Result(
                success=True,
                code="python test.py",
                stdout="All tests passed",
                stderr="",
                return_value="success"
            )
        }
    ]
    
    print("🧪 测试AI评估器对各种输出的判断")
    print("=" * 60)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        result = scenario['result']
        
        print(f"   success: {result.success}")
        print(f"   stdout: {repr(result.stdout)}")
        print(f"   stderr: {repr(result.stderr)}")
        print(f"   return_value: {repr(result.return_value)}")
        
        evaluation = evaluator.evaluate_test_result(
            result_code=result.code,
            result_stdout=result.stdout,
            result_stderr=result.stderr,
            result_return_value=result.return_value
        )
        
        print(f"   -> AI评估结果: {'✅ 通过' if evaluation['passed'] else '❌ 失败'}")
        print(f"   -> 置信度: {evaluation['confidence']:.2f}")
        print(f"   -> 理由: {evaluation['reason']}")


if __name__ == "__main__":
    test_evaluator_with_unittest_output()