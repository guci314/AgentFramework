#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StatefulExecutor类单元测试 - 有状态代码执行器测试
"""

import unittest
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import StatefulExecutor
from agent_base import Result


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
# 可以访问之前定义的变量
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
    
    def test_variable_modification(self):
        """测试变量修改"""
        # 初始化变量
        code1 = """
data = {'count': 0, 'values': []}
print(f'初始数据: {data}')
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        
        # 修改变量
        code2 = """
data['count'] += 1
data['values'].append('item1')
print(f'修改后数据: {data}')
"""
        result2 = self.executor.execute_code(code2)
        self.assertTrue(result2.success)
        self.assertIn("'count': 1", result2.stdout)
        self.assertIn("'item1'", result2.stdout)
        
        # 继续修改
        code3 = """
data['count'] += 1
data['values'].extend(['item2', 'item3'])
print(f'再次修改后数据: {data}')
print(f'最终计数: {data["count"]}')
"""
        result3 = self.executor.execute_code(code3)
        self.assertTrue(result3.success)
        self.assertIn("'count': 2", result3.stdout)
        self.assertIn("最终计数: 2", result3.stdout)
    
    def test_function_definition_and_usage(self):
        """测试函数定义和使用"""
        # 定义函数
        code1 = """
def calculate_factorial(n):
    if n <= 1:
        return 1
    else:
        return n * calculate_factorial(n - 1)

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print("函数定义完成")
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        self.assertIn("函数定义完成", result1.stdout)
        
        # 使用函数
        code2 = """
# 使用之前定义的函数
fact_5 = calculate_factorial(5)
fib_8 = fibonacci(8)

print(f"5的阶乘: {fact_5}")
print(f"斐波那契数列第8项: {fib_8}")
"""
        result2 = self.executor.execute_code(code2)
        self.assertTrue(result2.success)
        self.assertIn("5的阶乘: 120", result2.stdout)
        self.assertIn("斐波那契数列第8项: 21", result2.stdout)


class TestStatefulExecutorComplexTypes(unittest.TestCase):
    """StatefulExecutor复杂数据类型测试"""
    
    def setUp(self):
        """测试前准备"""
        self.executor = StatefulExecutor()
    
    def test_numpy_arrays(self):
        """测试numpy数组状态保持"""
        code1 = """
import numpy as np

# 创建numpy数组
arr1 = np.array([1, 2, 3, 4, 5])
arr2 = np.array([[1, 2], [3, 4]])
matrix = np.random.rand(3, 3)

print(f"一维数组: {arr1}")
print(f"二维数组:\\n{arr2}")
print(f"随机矩阵形状: {matrix.shape}")
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        self.assertIn("一维数组:", result1.stdout)
        self.assertIn("二维数组:", result1.stdout)
        
        # 使用之前创建的数组
        code2 = """
# 对数组进行操作
arr1_squared = arr1 ** 2
arr2_sum = np.sum(arr2)
matrix_mean = np.mean(matrix)

print(f"数组平方: {arr1_squared}")
print(f"二维数组和: {arr2_sum}")
print(f"矩阵均值: {matrix_mean:.4f}")
"""
        result2 = self.executor.execute_code(code2)
        self.assertTrue(result2.success)
        self.assertIn("数组平方:", result2.stdout)
        self.assertIn("二维数组和:", result2.stdout)
    
    def test_pandas_dataframes(self):
        """测试pandas DataFrame状态保持"""
        code1 = """
import pandas as pd

# 创建DataFrame
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'score': [85, 92, 78, 96]
}
df = pd.DataFrame(data)

print("原始DataFrame:")
print(df)
print(f"DataFrame形状: {df.shape}")
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        self.assertIn("原始DataFrame:", result1.stdout)
        self.assertIn("Alice", result1.stdout)
        
        # 操作DataFrame
        code2 = """
# 对DataFrame进行操作
df['grade'] = df['score'].apply(lambda x: 'A' if x >= 90 else 'B' if x >= 80 else 'C')
high_scorers = df[df['score'] >= 90]

print("添加等级后的DataFrame:")
print(df)
print("\\n高分者:")
print(high_scorers)
"""
        result2 = self.executor.execute_code(code2)
        self.assertTrue(result2.success)
        self.assertIn("添加等级后的DataFrame:", result2.stdout)
        self.assertIn("高分者:", result2.stdout)
    
    def test_class_instances(self):
        """测试类实例状态保持"""
        code1 = """
class Calculator:
    def __init__(self):
        self.history = []
        
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self):
        return self.history

# 创建计算器实例
calc = Calculator()
result1 = calc.add(10, 20)
result2 = calc.multiply(5, 6)

print(f"加法结果: {result1}")
print(f"乘法结果: {result2}")
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        self.assertIn("加法结果: 30", result1.stdout)
        self.assertIn("乘法结果: 30", result1.stdout)
        
        # 继续使用实例
        code2 = """
# 继续使用之前创建的计算器
result3 = calc.add(100, 200)
result4 = calc.multiply(7, 8)

print(f"新的加法结果: {result3}")
print(f"新的乘法结果: {result4}")
print("\\n计算历史:")
for record in calc.get_history():
    print(f"  {record}")
"""
        result2 = self.executor.execute_code(code2)
        self.assertTrue(result2.success)
        self.assertIn("新的加法结果: 300", result2.stdout)
        self.assertIn("新的乘法结果: 56", result2.stdout)
        self.assertIn("计算历史:", result2.stdout)


class TestStatefulExecutorErrorHandling(unittest.TestCase):
    """StatefulExecutor错误处理测试"""
    
    def setUp(self):
        """测试前准备"""
        self.executor = StatefulExecutor()
    
    def test_syntax_error_handling(self):
        """测试语法错误处理"""
        code = """
def invalid_function(
    print("缺少闭合括号")
"""
        result = self.executor.execute_code(code)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.stderr)
        self.assertIn("语法错误", result.stderr)
    
    def test_runtime_error_recovery(self):
        """测试运行时错误恢复"""
        # 先执行正常代码
        code1 = """
x = 10
y = 5
result1 = x + y
print(f"正常执行: {result1}")
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        
        # 执行有错误的代码
        code2 = """
# 这会产生错误
error_result = undefined_variable + 10
print(f"这行不会执行: {error_result}")
"""
        result2 = self.executor.execute_code(code2)
        self.assertFalse(result2.success)
        self.assertIn("NameError", result2.stderr)
        
        # 验证之前的变量仍然存在
        code3 = """
# 验证之前的变量仍然可用
print(f"x的值仍然是: {x}")
print(f"y的值仍然是: {y}")
print(f"result1的值仍然是: {result1}")
"""
        result3 = self.executor.execute_code(code3)
        self.assertTrue(result3.success)
        self.assertIn("x的值仍然是: 10", result3.stdout)
        self.assertIn("y的值仍然是: 5", result3.stdout)
    
    def test_exception_handling_in_code(self):
        """测试代码中的异常处理"""
        code = """
def divide_safely(a, b):
    try:
        result = a / b
        return result, None
    except ZeroDivisionError as e:
        return None, str(e)

# 测试正常除法
result1, error1 = divide_safely(10, 2)
print(f"10 / 2 = {result1}, 错误: {error1}")

# 测试除零
result2, error2 = divide_safely(10, 0)
print(f"10 / 0 = {result2}, 错误: {error2}")

# 测试变量是否正确设置
print(f"函数调用成功完成")
"""
        result = self.executor.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("10 / 2 = 5.0", result.stdout)
        self.assertIn("10 / 0 = None", result.stdout)
        self.assertIn("division by zero", result.stdout)
        self.assertIn("函数调用成功完成", result.stdout)


class TestStatefulExecutorReturnValue(unittest.TestCase):
    """StatefulExecutor返回值测试"""
    
    def setUp(self):
        """测试前准备"""
        self.executor = StatefulExecutor()
    
    def test_return_value_setting(self):
        """测试return_value设置和获取"""
        code = """
# 计算并设置返回值
data = [1, 2, 3, 4, 5]
sum_value = sum(data)
mean_value = sum_value / len(data)

print(f"数据: {data}")
print(f"总和: {sum_value}")
print(f"平均值: {mean_value}")

return_value = {
    'sum': sum_value,
    'mean': mean_value,
    'count': len(data)
}
"""
        result = self.executor.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("数据: [1, 2, 3, 4, 5]", result.stdout)
        self.assertIn("总和: 15", result.stdout)
        self.assertIn("平均值: 3.0", result.stdout)
        
        # 验证return_value
        return_val = self.executor.get_variable('return_value')
        self.assertIsInstance(return_val, dict)
        self.assertEqual(return_val['sum'], 15)
        self.assertEqual(return_val['mean'], 3.0)
        self.assertEqual(return_val['count'], 5)
    
    def test_return_value_persistence(self):
        """测试return_value在多次执行间的变化"""
        # 第一次设置
        code1 = """
return_value = "first_execution"
print(f"第一次执行，return_value = {return_value}")
"""
        result1 = self.executor.execute_code(code1)
        self.assertTrue(result1.success)
        self.assertEqual(self.executor.get_variable('return_value'), "first_execution")
        
        # 第二次设置
        code2 = """
previous_value = return_value
return_value = "second_execution"
print(f"之前的值: {previous_value}")
print(f"当前的值: {return_value}")
"""
        result2 = self.executor.execute_code(code2)
        self.assertTrue(result2.success)
        self.assertIn("之前的值: first_execution", result2.stdout)
        self.assertIn("当前的值: second_execution", result2.stdout)
        self.assertEqual(self.executor.get_variable('return_value'), "second_execution")


if __name__ == '__main__':
    print("🚀 开始StatefulExecutor类单元测试...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestStatefulExecutorBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestStatefulExecutorComplexTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestStatefulExecutorErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestStatefulExecutorReturnValue))
    
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