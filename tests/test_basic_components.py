#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础组件测试 - 不需要API密钥的测试
"""

import unittest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置虚拟API密钥以避免导入错误
if not os.getenv('DEEPSEEK_API_KEY'):
    os.environ['DEEPSEEK_API_KEY'] = 'fake_key_for_testing'

from pythonTask import Device, StatefulExecutor
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
        self.assertEqual(result.returncode, 0)
    
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
        self.assertNotEqual(result.returncode, 0)


class TestStatefulExecutorBasic(unittest.TestCase):
    """StatefulExecutor基础功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.executor = StatefulExecutor()
    
    def test_simple_execution(self):
        """测试简单代码执行"""
        code = "print('Hello from StatefulExecutor!')"
        result = self.executor.execute_code(code)
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.success)
        self.assertEqual(result.code, code)
        self.assertIn("Hello from StatefulExecutor!", result.stdout)
    
    def test_variable_persistence(self):
        """测试变量持久化"""
        # 第一次执行：定义变量
        code1 = """
x = 100
y = 200
result = x + y
print(f'第一次计算结果: {result}')
return_value = result
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        self.assertIn("第一次计算结果: 300", result1.stdout)
        
        # 第二次执行：使用之前定义的变量
        code2 = """
z = result * 2
print(f'之前的结果: {result}')
print(f'新的计算结果: {z}')
return_value = z
"""
        result2 = self.executor.execute_code(code2)
        self.assertTrue(result2.success)
        self.assertIn("之前的结果: 300", result2.stdout)
        self.assertIn("新的计算结果: 600", result2.stdout)
    
    def test_get_set_variable(self):
        """测试变量读写接口"""
        # 设置变量
        self.executor.set_variable('test_var', 'test_value')
        self.executor.set_variable('number_var', 42)
        self.executor.set_variable('list_var', [1, 2, 3, 4, 5])
        
        # 读取变量
        self.assertEqual(self.executor.get_variable('test_var'), 'test_value')
        self.assertEqual(self.executor.get_variable('number_var'), 42)
        self.assertEqual(self.executor.get_variable('list_var'), [1, 2, 3, 4, 5])
        
        # 读取不存在的变量
        self.assertIsNone(self.executor.get_variable('nonexistent_var'))


if __name__ == '__main__':
    print("🚀 开始基础组件测试（无需API密钥）...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestStatefulExecutorBasic))
    
    print("="*60)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试总结
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 所有基础测试通过！")
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