#!/usr/bin/env python3
"""
测试unittest输出处理
==================

验证AI评估器能正确处理unittest框架输出到stderr的特性。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from static_workflow.result_evaluator import MockTestResultEvaluator
from agent_base import Result


def test_unittest_outputs():
    """测试各种unittest输出场景"""
    
    evaluator = MockTestResultEvaluator()
    
    # 测试案例
    test_cases = [
        {
            "name": "unittest成功 - 基本情况",
            "result": Result(
                success=True,
                code="python -m unittest test_module.py",
                stdout="",
                stderr="Ran 5 tests in 0.123s\n\nOK",
                return_value="5 passed"
            ),
            "expected": True
        },
        {
            "name": "unittest成功 - 详细模式",
            "result": Result(
                success=True,
                code="python -m unittest -v test_module.py",
                stdout="",
                stderr="test_add (test_module.TestCalculator) ... ok\ntest_subtract (test_module.TestCalculator) ... ok\n\nRan 2 tests in 0.001s\n\nOK",
                return_value="2 passed"
            ),
            "expected": True
        },
        {
            "name": "unittest失败 - 有错误",
            "result": Result(
                success=True,
                code="python -m unittest test_module.py",
                stdout="",
                stderr="Ran 3 tests in 0.055s\n\nFAILED (failures=1, errors=1)",
                return_value="1 passed, 1 failed, 1 error"
            ),
            "expected": False
        },
        {
            "name": "unittest失败 - 仅失败",
            "result": Result(
                success=True,
                code="python -m unittest test_module.py",
                stdout="",
                stderr="F..\nRan 3 tests in 0.012s\n\nFAILED (failures=1)",
                return_value="2 passed, 1 failed"
            ),
            "expected": False
        },
        {
            "name": "pytest成功",
            "result": Result(
                success=True,
                code="pytest test_module.py",
                stdout="",
                stderr="===== test session starts =====\ncollected 3 items\n\ntest_module.py ...                     [100%]\n\n===== 3 passed in 0.02s =====",
                return_value="3 passed"
            ),
            "expected": True
        },
        {
            "name": "真正的错误输出",
            "result": Result(
                success=False,
                code="python invalid_syntax.py",
                stdout="",
                stderr="SyntaxError: invalid syntax\n  File \"invalid_syntax.py\", line 1\n    def func(\n           ^\nSyntaxError: unexpected EOF while parsing",
                return_value="error"
            ),
            "expected": False
        }
    ]
    
    print("🧪 测试unittest输出处理")
    print("=" * 60)
    
    success_count = 0
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   stderr内容: {repr(case['result'].stderr[:100])}...")
        
        evaluation = evaluator.evaluate_test_result(
            result_code=case['result'].code,
            result_stdout=case['result'].stdout,
            result_stderr=case['result'].stderr,
            result_return_value=case['result'].return_value
        )
        
        actual = evaluation["passed"]
        expected = case["expected"]
        status = "✅ 通过" if actual == expected else "❌ 失败"
        
        print(f"   期望结果: {expected}")
        print(f"   实际结果: {actual} (置信度: {evaluation['confidence']:.2f})")
        print(f"   判断理由: {evaluation['reason']}")
        print(f"   测试状态: {status}")
        
        if actual == expected:
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"🏆 测试完成: {success_count}/{len(test_cases)} 通过")
    
    if success_count == len(test_cases):
        print("🎉 所有unittest输出处理测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，需要优化判断逻辑。")
        return False


if __name__ == "__main__":
    success = test_unittest_outputs()
    sys.exit(0 if success else 1)