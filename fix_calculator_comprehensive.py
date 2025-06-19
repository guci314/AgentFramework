#!/usr/bin/env python3
"""
全面修复Calculator工作流问题
==========================

确保calculator.py和test_calculator.py的异常类型匹配。
"""

import os
import sys
import subprocess


def fix_calculator_exception_consistency():
    """修复Calculator异常类型一致性问题"""
    
    print("🔧 全面修复Calculator异常类型一致性问题")
    print("=" * 60)
    
    # 确保calculator.py使用ZeroDivisionError
    calculator_content = '''
class Calculator:
    def __init__(self):
        pass
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
'''.strip()
    
    # 确保test_calculator.py期望ZeroDivisionError
    test_content = '''
import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()
    
    def test_add(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)
        self.assertEqual(self.calc.add(0, 0), 0)
    
    def test_subtract(self):
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(3, 5), -2)
        self.assertEqual(self.calc.subtract(0, 0), 0)
    
    def test_multiply(self):
        self.assertEqual(self.calc.multiply(2, 3), 6)
        self.assertEqual(self.calc.multiply(-1, 1), -1)
        self.assertEqual(self.calc.multiply(0, 5), 0)
    
    def test_divide(self):
        self.assertEqual(self.calc.divide(6, 3), 2)
        self.assertEqual(self.calc.divide(5, 2), 2.5)
        self.assertEqual(self.calc.divide(0, 5), 0)
        
    def test_divide_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            self.calc.divide(5, 0)

if __name__ == '__main__':
    unittest.main()
'''.strip()
    
    # 写入正确的文件内容
    with open('calculator.py', 'w') as f:
        f.write(calculator_content)
    
    with open('test_calculator.py', 'w') as f:
        f.write(test_content)
    
    print("✅ 已更新calculator.py和test_calculator.py")
    print("📝 关键修复:")
    print("   - calculator.py: 使用ZeroDivisionError异常")
    print("   - test_calculator.py: 期望ZeroDivisionError异常")
    
    # 验证测试通过
    print("\n🧪 验证测试结果...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "unittest", "test_calculator.py", "-v"
        ], capture_output=True, text=True, timeout=10)
        
        print("📊 测试输出:")
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        if result.returncode == 0:
            print("✅ 所有测试通过！异常类型一致性问题已解决")
            return True
        else:
            print("❌ 测试仍然失败")
            return False
            
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False


def create_backup_files():
    """创建备份文件防止被覆盖"""
    
    print("\n💾 创建备份文件...")
    
    # 读取当前正确的文件内容
    with open('calculator.py', 'r') as f:
        calc_content = f.read()
    
    with open('test_calculator.py', 'r') as f:
        test_content = f.read()
    
    # 创建备份
    with open('calculator_backup.py', 'w') as f:
        f.write(calc_content)
    
    with open('test_calculator_backup.py', 'w') as f:
        f.write(test_content)
    
    print("✅ 备份文件已创建:")
    print("   - calculator_backup.py")
    print("   - test_calculator_backup.py")


def main():
    """主函数"""
    
    print("🚑 Calculator异常类型一致性修复工具")
    print("=" * 60)
    
    # 修复一致性问题
    success = fix_calculator_exception_consistency()
    
    if success:
        # 创建备份
        create_backup_files()
        
        print("\n🎉 修复完成！")
        print("\n💡 解决方案总结:")
        print("   ✅ calculator.py现在抛出ZeroDivisionError")
        print("   ✅ test_calculator.py期望ZeroDivisionError")
        print("   ✅ 所有测试用例通过")
        print("   ✅ 创建了备份文件防止被覆盖")
        
        print("\n🔄 现在calculator工作流应该能够:")
        print("   1. 运行测试（成功）")
        print("   2. AI评估测试结果为通过")
        print("   3. 正常结束，而不是进入死循环")
        
        return True
    else:
        print("\n❌ 修复失败，需要手动检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)