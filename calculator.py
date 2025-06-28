def add(a, b):
    """加法函数"""
    return a + b

def subtract(a, b):
    """减法函数"""
    return a - b

def multiply(a, b):
    """乘法函数"""
    return a * b

def divide(a, b):
    """除法函数"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

import unittest
from calculator import add, subtract, multiply, divide

class CalculatorTest(unittest.TestCase):
    """测试计算器基本运算功能"""
    
    def test_add_normal(self):
        """测试加法正常情况"""
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(0, 0), 0)
    
    def test_subtract_normal(self):
        """测试减法正常情况"""
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(10, -5), 15)
        self.assertEqual(subtract(0, 0), 0)
    
    def test_multiply_normal(self):
        """测试乘法正常情况"""
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(multiply(-1, 5), -5)
        self.assertEqual(multiply(0, 100), 0)
    
    def test_divide_normal(self):
        """测试除法正常情况"""
        self.assertEqual(divide(6, 3), 2)
        self.assertEqual(divide(10, 2), 5)
        self.assertEqual(divide(-9, 3), -3)
    
    def test_divide_by_zero(self):
        """测试除数为零的异常情况"""
        with self.assertRaises(ValueError):
            divide(10, 0)
        with self.assertRaises(ValueError):
            divide(0, 0)

if __name__ == '__main__':
    unittest.main()
