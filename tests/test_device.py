#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device类单元测试 - 基础代码执行器测试
"""

import unittest
import os
import sys
import tempfile
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pythonTask import Device
from agent_base import Result


class TestDeviceBasic(unittest.TestCase):
    """Device基础功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = Device()
    
    def test_simple_code_execution(self):
        """测试简单代码执行"""
        code = "print('Hello, World!')"
        result = self.device.execute_code(code)
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.success)
        self.assertEqual(result.code, code)
        self.assertIn("Hello, World!", result.stdout)
        # returncode field removed - success already indicates execution status
    
    def test_arithmetic_calculation(self):
        """测试算术计算"""
        code = """
x = 10
y = 20
result = x + y
print(f"计算结果: {result}")
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("计算结果: 30", result.stdout)
    
    def test_syntax_error_handling(self):
        """测试语法错误处理"""
        code = "print('syntax error'"  # 缺少闭合括号
        result = self.device.execute_code(code)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.stderr)
        self.assertIn("SyntaxError", result.stderr)
        # returncode field removed - success field indicates failure
    
    def test_runtime_error_handling(self):
        """测试运行时错误处理"""
        code = """
x = 10
y = 0
result = x / y  # 除零错误
print(result)
"""
        result = self.device.execute_code(code)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.stderr)
        self.assertIn("ZeroDivisionError", result.stderr)
    
    def test_empty_code(self):
        """测试空代码"""
        code = ""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertEqual(result.code, "")
        self.assertEqual(result.stdout, "")
    
    def test_multiline_code(self):
        """测试多行代码"""
        code = """
def greet(name):
    return f"Hello, {name}!"

names = ["Alice", "Bob", "Charlie"]
for name in names:
    print(greet(name))
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("Hello, Alice!", result.stdout)
        self.assertIn("Hello, Bob!", result.stdout)
        self.assertIn("Hello, Charlie!", result.stdout)
    
    def test_import_modules(self):
        """测试导入模块"""
        code = """
import math
import json

# 测试math模块
print(f"π的值: {math.pi}")
print(f"2的平方根: {math.sqrt(2)}")

# 测试json模块
data = {"name": "test", "value": 42}
json_str = json.dumps(data)
print(f"JSON字符串: {json_str}")
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("π的值:", result.stdout)
        self.assertIn("2的平方根:", result.stdout)
        self.assertIn("JSON字符串:", result.stdout)


class TestDeviceEdgeCases(unittest.TestCase):
    """Device边界情况测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = Device()
    
    def test_unicode_content(self):
        """测试Unicode内容处理"""
        code = """
# 测试中文字符
print("你好，世界！")
print("🚀 Python测试")

# 测试特殊字符
special_chars = "!@#$%^&*()_+-=[]{}|;:'\\",./<>?"
print(f"特殊字符: {special_chars}")
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("你好，世界！", result.stdout)
        self.assertIn("🚀 Python测试", result.stdout)
        self.assertIn("特殊字符:", result.stdout)
    
    def test_long_running_code(self):
        """测试长时间运行的代码"""
        code = """
import time
print("开始执行...")
time.sleep(0.1)  # 短暂延迟，避免测试时间过长
print("执行完成!")
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("开始执行...", result.stdout)
        self.assertIn("执行完成!", result.stdout)
    
    def test_large_output(self):
        """测试大量输出"""
        code = """
# 生成较多输出
for i in range(50):
    print(f"行 {i+1}: 这是一个测试输出行")
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("行 1:", result.stdout)
        self.assertIn("行 50:", result.stdout)
    
    def test_file_operations(self):
        """测试文件操作"""
        code = """
import tempfile
import os

# 创建临时文件
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write("测试文件内容\\n")
    f.write("第二行内容\\n")
    temp_path = f.name

print(f"临时文件路径: {temp_path}")

# 读取文件内容
with open(temp_path, 'r') as f:
    content = f.read()
    print(f"文件内容:\\n{content}")

# 清理临时文件
os.unlink(temp_path)
print("文件已删除")
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("临时文件路径:", result.stdout)
        self.assertIn("文件内容:", result.stdout)
        self.assertIn("测试文件内容", result.stdout)
        self.assertIn("文件已删除", result.stdout)
    
    def test_exception_in_function(self):
        """测试函数中的异常"""
        code = """
def divide_numbers(a, b):
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

try:
    result1 = divide_numbers(10, 2)
    print(f"10 / 2 = {result1}")
    
    result2 = divide_numbers(10, 0)  # 会抛出异常
    print(f"10 / 0 = {result2}")
except ValueError as e:
    print(f"捕获异常: {e}")
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("10 / 2 = 5.0", result.stdout)
        self.assertIn("捕获异常: 除数不能为零", result.stdout)


class TestDeviceResultValidation(unittest.TestCase):
    """Device结果验证测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = Device()
    
    def test_result_object_structure(self):
        """测试Result对象结构"""
        code = "print('test')"
        result = self.device.execute_code(code)
        
        # 验证Result对象的属性
        self.assertTrue(hasattr(result, 'success'))
        self.assertTrue(hasattr(result, 'code'))
        self.assertTrue(hasattr(result, 'stdout'))
        self.assertTrue(hasattr(result, 'stderr'))
        # returncode field removed - success field replaces it
        
        # 验证属性类型
        self.assertIsInstance(result.success, bool)
        self.assertIsInstance(result.code, str)
        self.assertIsInstance(result.stdout, str)
        # returncode field removed
    
    def test_successful_execution_result(self):
        """测试成功执行的结果"""
        code = "print('success test')"
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertEqual(result.code, code)
        self.assertIn("success test", result.stdout)
        # returncode field removed - success field indicates success
        # 成功执行时stderr可能为空字符串或None
        self.assertTrue(result.stderr == "" or result.stderr is None)
    
    def test_failed_execution_result(self):
        """测试失败执行的结果"""
        code = "undefined_variable"  # 未定义变量
        result = self.device.execute_code(code)
        
        self.assertFalse(result.success)
        self.assertEqual(result.code, code)
        self.assertIsNotNone(result.stderr)
        # returncode field removed - success field indicates failure
        self.assertIn("NameError", result.stderr)


if __name__ == '__main__':
    print("🚀 开始Device类单元测试...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceResultValidation))
    
    print("="*60)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试总结
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
    else:
        print(f"❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
        if result.failures:
            print("\n失败的测试:")
            for test, error in result.failures:
                print(f"  - {test}: {error}")
                
        if result.errors:
            print("\n错误的测试:")
            for test, error in result.errors:
                print(f"  - {test}: {error}")
    
    print(f"📊 测试统计:")
    print(f"   - 运行测试: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    print("="*60)