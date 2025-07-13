"""
Calculator3的单元测试模块。

该模块包含对Calculator类的全面测试，包括正常情况和异常情况的测试。
"""

import unittest
from calculator3 import Calculator


class TestCalculator(unittest.TestCase):
    """Calculator类的测试用例。"""
    
    def setUp(self):
        """每个测试方法执行前的准备工作。"""
        self.calc = Calculator()
    
    def test_add_integers(self):
        """测试整数加法。"""
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-5, 3), -2)
        self.assertEqual(self.calc.add(0, 0), 0)
    
    def test_add_floats(self):
        """测试浮点数加法。"""
        self.assertAlmostEqual(self.calc.add(2.5, 3.7), 6.2)
        self.assertAlmostEqual(self.calc.add(-1.5, 2.5), 1.0)
    
    def test_subtract(self):
        """测试减法运算。"""
        self.assertEqual(self.calc.subtract(10, 3), 7)
        self.assertEqual(self.calc.subtract(5, 8), -3)
        self.assertAlmostEqual(self.calc.subtract(7.5, 2.3), 5.2)
    
    def test_multiply(self):
        """测试乘法运算。"""
        self.assertEqual(self.calc.multiply(3, 4), 12)
        self.assertEqual(self.calc.multiply(-2, 5), -10)
        self.assertAlmostEqual(self.calc.multiply(2.5, 4), 10.0)
    
    def test_divide(self):
        """测试除法运算。"""
        self.assertEqual(self.calc.divide(10, 2), 5.0)
        self.assertAlmostEqual(self.calc.divide(7, 3), 2.3333333333333335)
        self.assertEqual(self.calc.divide(-15, 3), -5.0)
    
    def test_divide_by_zero(self):
        """测试除零错误。"""
        with self.assertRaises(ZeroDivisionError):
            self.calc.divide(10, 0)
    
    def test_invalid_type(self):
        """测试类型错误。"""
        with self.assertRaises(TypeError):
            self.calc.add("5", 3)
        with self.assertRaises(TypeError):
            self.calc.multiply(5, [1, 2, 3])
    
    def test_special_values(self):
        """测试特殊值处理。"""
        with self.assertRaises(ValueError):
            self.calc.add(float('inf'), 5)
        with self.assertRaises(ValueError):
            self.calc.multiply(float('nan'), 3)
    
    def test_repr_and_str(self):
        """测试字符串表示方法。"""
        self.assertEqual(repr(self.calc), "Calculator()")
        self.assertEqual(str(self.calc), "Calculator类：提供加、减、乘、除四种基本运算")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)