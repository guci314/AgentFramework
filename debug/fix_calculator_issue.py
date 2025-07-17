#!/usr/bin/env python3
"""
修复Calculator工作流死循环问题
==========================

手动修复计算器代码中的异常类型不匹配问题。
"""

import os
import sys


def fix_calculator_code():
    """修复calculator.py中的异常类型问题"""
    
    print("🔧 修复calculator.py中的异常类型问题")
    
    # 检查文件是否存在
    if not os.path.exists("calculator.py"):
        print("❌ calculator.py文件不存在")
        return False
    
    # 读取当前内容
    with open("calculator.py", "r") as f:
        content = f.read()
    
    print("📄 当前calculator.py内容:")
    print(content)
    
    # 检查是否包含错误的ValueError
    if "raise ValueError" in content and "divide" in content:
        print("🔍 发现问题：divide方法抛出ValueError而不是ZeroDivisionError")
        
        # 修复：将ValueError替换为ZeroDivisionError
        fixed_content = content.replace(
            'raise ValueError("Division by zero is not allowed")',
            'raise ZeroDivisionError("Division by zero is not allowed")'
        )
        fixed_content = fixed_content.replace(
            'raise ValueError("Cannot divide by zero")', 
            'raise ZeroDivisionError("Cannot divide by zero")'
        )
        
        # 写入修复后的内容
        with open("calculator.py", "w") as f:
            f.write(fixed_content)
        
        print("✅ 已修复calculator.py")
        print("📄 修复后的内容:")
        print(fixed_content)
        
        return True
    else:
        print("✅ calculator.py看起来已经是正确的")
        return True


def verify_tests():
    """验证测试是否通过"""
    
    print("\n🧪 验证测试是否通过")
    
    if not os.path.exists("test_calculator.py"):
        print("❌ test_calculator.py文件不存在")
        return False
    
    # 运行测试
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "test_calculator.py", "-v"],
            capture_output=True, text=True, timeout=30
        )
        
        print("📊 测试结果:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        if result.returncode == 0:
            print("✅ 所有测试通过！")
            return True
        else:
            print("❌ 测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False


def main():
    """主函数"""
    
    print("🚑 Calculator工作流死循环修复工具")
    print("=" * 50)
    
    # 修复代码
    code_fixed = fix_calculator_code()
    
    if code_fixed:
        # 验证修复
        tests_pass = verify_tests()
        
        if tests_pass:
            print("\n🎉 修复成功！现在可以正常运行calculator工作流了。")
            print("\n💡 问题原因：")
            print("   - calculator.py中的divide方法抛出ValueError")
            print("   - 但test_calculator.py期望ZeroDivisionError")
            print("   - 导致测试一直失败，AI修复不准确，形成死循环")
            print("\n✅ 解决方案：") 
            print("   - 手动将ValueError改为ZeroDivisionError")
            print("   - 确保代码和测试的期望一致")
            return True
        else:
            print("\n❌ 修复后测试仍然失败，需要进一步检查")
            return False
    else:
        print("\n❌ 代码修复失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)