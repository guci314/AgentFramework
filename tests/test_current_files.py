#!/usr/bin/env python3
"""
测试当前文件状态
===============

验证当前calculator.py和test_calculator.py的状态和测试结果。
"""

import subprocess
import sys
from static_workflow.result_evaluator import MockTestResultEvaluator


def check_file_contents():
    """检查文件内容"""
    
    print("📁 检查文件内容")
    print("=" * 60)
    
    # 检查calculator.py
    try:
        with open('calculator.py', 'r') as f:
            calc_content = f.read()
        
        print("📄 calculator.py内容:")
        print(calc_content)
        
        if "ZeroDivisionError" in calc_content:
            print("✅ calculator.py使用ZeroDivisionError")
        elif "ValueError" in calc_content:
            print("❌ calculator.py使用ValueError（错误）")
        else:
            print("⚠️  calculator.py没有除零异常处理")
            
    except FileNotFoundError:
        print("❌ calculator.py文件不存在")
    
    print()
    
    # 检查test_calculator.py
    try:
        with open('test_calculator.py', 'r') as f:
            test_content = f.read()
        
        print("📄 test_calculator.py关键部分:")
        lines = test_content.split('\n')
        for i, line in enumerate(lines):
            if 'assertRaises' in line or 'ZeroDivisionError' in line or 'ValueError' in line:
                print(f"  第{i+1}行: {line.strip()}")
        
        if "assertRaises(ZeroDivisionError)" in test_content:
            print("✅ test_calculator.py期望ZeroDivisionError")
        elif "assertRaises(ValueError)" in test_content:
            print("❌ test_calculator.py期望ValueError（错误）")
        else:
            print("⚠️  test_calculator.py没有除零测试")
            
    except FileNotFoundError:
        print("❌ test_calculator.py文件不存在")


def run_test_and_analyze():
    """运行测试并分析结果"""
    
    print("\n🧪 运行测试并分析结果")
    print("=" * 60)
    
    # 运行测试
    result = subprocess.run([
        sys.executable, "-m", "unittest", "test_calculator.py", "-v"
    ], capture_output=True, text=True)
    
    print(f"📊 测试结果:")
    print(f"   Return code: {result.returncode}")
    print(f"   STDOUT: {repr(result.stdout)}")
    print(f"   STDERR: {repr(result.stderr)}")
    
    # 分析结果
    if result.returncode == 0:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
        
        # 查找具体错误
        if "ValueError" in result.stderr and "ZeroDivisionError" in result.stderr:
            print("🔍 错误分析: 异常类型不匹配")
        elif "ERROR:" in result.stderr:
            print("🔍 错误分析: 测试执行错误")
        elif "FAILED" in result.stderr:
            print("🔍 错误分析: 断言失败")
    
    # 用AI评估器分析
    print(f"\n🤖 AI评估器分析:")
    evaluator = MockTestResultEvaluator()
    
    evaluation = evaluator.evaluate_test_result(
        result_stdout=result.stdout,
        result_stderr=result.stderr,
        result_return_value=str(result.returncode)
    )
    
    print(f"   AI判断: {'通过' if evaluation['passed'] else '失败'}")
    print(f"   置信度: {evaluation['confidence']}")
    print(f"   理由: {evaluation['reason']}")
    print(f"   详细信息: {evaluation['details']}")
    
    return result.returncode == 0, evaluation['passed']


def main():
    """主函数"""
    
    print("🔍 测试当前文件状态")
    print("=" * 60)
    
    # 检查文件内容
    check_file_contents()
    
    # 运行测试并分析
    test_passed, ai_passed = run_test_and_analyze()
    
    print(f"\n📋 总结:")
    print(f"   实际测试结果: {'通过' if test_passed else '失败'}")
    print(f"   AI评估结果: {'通过' if ai_passed else '失败'}")
    
    if test_passed and ai_passed:
        print("✅ 文件状态正确，测试通过，AI评估正确")
        print("💡 如果工作流仍然循环，问题在工作流执行过程中的数据传递")
    elif test_passed and not ai_passed:
        print("⚠️  测试通过但AI评估错误")
        print("💡 AI评估器逻辑有问题")
    elif not test_passed and ai_passed:
        print("⚠️  测试失败但AI评估错误")
        print("💡 AI评估器过于乐观")
    else:
        print("❌ 测试失败且AI评估正确")
        print("💡 文件内容有问题，需要修复")


if __name__ == "__main__":
    main()