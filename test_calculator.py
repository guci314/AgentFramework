
import unittest
import os
import sys

# 确保 calculator.py 可以在测试环境中被导入
# 如果 calculator.py 不在当前目录，需要调整路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    import calculator
except ImportError:
    print("Error: Could not import calculator.py. Make sure it's in the same directory.")
    sys.exit(1)

class TestCalculator(unittest.TestCase):

    def test_add_positive_numbers(self):
        '''测试加法：正数相加'''
        self.assertEqual(calculator.add(2, 3), 5)
        self.assertEqual(calculator.add(100, 200), 300)
        print("Test add_positive_numbers passed.")

    def test_add_negative_numbers(self):
        '''测试加法：负数相加'''
        self.assertEqual(calculator.add(-2, -3), -5)
        self.assertEqual(calculator.add(-10, -5), -15)
        print("Test add_negative_numbers passed.")

    def test_add_mixed_numbers(self):
        '''测试加法：正数和负数相加'''
        self.assertEqual(calculator.add(5, -3), 2)
        self.assertEqual(calculator.add(-5, 3), -2)
        self.assertEqual(calculator.add(0, -7), -7)
        print("Test add_mixed_numbers passed.")

    def test_add_zero(self):
        '''测试加法：与零相加'''
        self.assertEqual(calculator.add(5, 0), 5)
        self.assertEqual(calculator.add(0, 0), 0)
        print("Test add_zero passed.")

    def test_add_float_numbers(self):
        '''测试加法：浮点数相加'''
        self.assertAlmostEqual(calculator.add(2.5, 3.5), 6.0)
        self.assertAlmostEqual(calculator.add(0.1, 0.2), 0.3)
        print("Test add_float_numbers passed.")

    def test_subtract_positive_numbers(self):
        '''测试减法：正数相减'''
        self.assertEqual(calculator.subtract(5, 3), 2)
        self.assertEqual(calculator.subtract(10, 20), -10)
        print("Test subtract_positive_numbers passed.")

    def test_subtract_negative_numbers(self):
        '''测试减法：负数相减'''
        self.assertEqual(calculator.subtract(-5, -3), -2)
        self.assertEqual(calculator.subtract(-3, -5), 2)
        print("Test subtract_negative_numbers passed.")

    def test_subtract_mixed_numbers(self):
        '''测试减法：正数和负数相减'''
        self.assertEqual(calculator.subtract(5, -3), 8)
        self.assertEqual(calculator.subtract(-5, 3), -8)
        print("Test subtract_mixed_numbers passed.")

    def test_subtract_zero(self):
        '''测试减法：与零相减'''
        self.assertEqual(calculator.subtract(5, 0), 5)
        self.assertEqual(calculator.subtract(0, 5), -5)
        self.assertEqual(calculator.subtract(0, 0), 0)
        print("Test subtract_zero passed.")

    def test_subtract_float_numbers(self):
        '''测试减法：浮点数相减'''
        self.assertAlmostEqual(calculator.subtract(5.5, 2.5), 3.0)
        self.assertAlmostEqual(calculator.subtract(0.3, 0.1), 0.2)
        print("Test subtract_float_numbers passed.")

    def test_multiply_positive_numbers(self):
        '''测试乘法：正数相乘'''
        self.assertEqual(calculator.multiply(2, 3), 6)
        self.assertEqual(calculator.multiply(10, 0.5), 5.0)
        print("Test multiply_positive_numbers passed.")

    def test_multiply_negative_numbers(self):
        '''测试乘法：负数相乘'''
        self.assertEqual(calculator.multiply(-2, -3), 6)
        self.assertEqual(calculator.multiply(-5, 2), -10)
        print("Test multiply_negative_numbers passed.")

    def test_multiply_by_zero(self):
        '''测试乘法：与零相乘'''
        self.assertEqual(calculator.multiply(5, 0), 0)
        self.assertEqual(calculator.multiply(0, 0), 0)
        self.assertEqual(calculator.multiply(-10, 0), 0)
        print("Test multiply_by_zero passed.")

    def test_multiply_float_numbers(self):
        '''测试乘法：浮点数相乘'''
        self.assertAlmostEqual(calculator.multiply(2.5, 2), 5.0)
        self.assertAlmostEqual(calculator.multiply(0.5, 0.5), 0.25)
        print("Test multiply_float_numbers passed.")

    def test_divide_positive_numbers(self):
        '''测试除法：正数相除'''
        self.assertEqual(calculator.divide(6, 3), 2)
        self.assertAlmostEqual(calculator.divide(10, 4), 2.5)
        print("Test divide_positive_numbers passed.")

    def test_divide_negative_numbers(self):
        '''测试除法：负数相除'''
        self.assertEqual(calculator.divide(-6, -3), 2)
        self.assertEqual(calculator.divide(6, -3), -2)
        self.assertEqual(calculator.divide(-6, 3), -2)
        print("Test divide_negative_numbers passed.")

    def test_divide_by_one(self):
        '''测试除法：除以一'''
        self.assertEqual(calculator.divide(5, 1), 5)
        self.assertEqual(calculator.divide(-5, 1), -5)
        print("Test divide_by_one passed.")

    def test_divide_zero_by_number(self):
        '''测试除法：零除以非零数'''
        self.assertEqual(calculator.divide(0, 5), 0)
        self.assertEqual(calculator.divide(0, -5), 0)
        print("Test divide_zero_by_number passed.")

    def test_divide_by_zero(self):
        '''测试除法：除数为零的边界条件'''
        with self.assertRaises(ValueError) as cm:
            calculator.divide(10, 0)
        self.assertEqual(str(cm.exception), "Cannot divide by zero")
        print("Test divide_by_zero passed.")

    def test_divide_float_numbers(self):
        '''测试除法：浮点数相除'''
        self.assertAlmostEqual(calculator.divide(7.5, 2.5), 3.0)
        self.assertAlmostEqual(calculator.divide(1, 3), 0.3333333333333333)
        print("Test divide_float_numbers passed.")

if __name__ == '__main__':
    # 使用 TextTestRunner 运行测试，并指定输出到 stderr
    # unittest 的默认行为就是将结果输出到 stderr
    print("Running tests for calculator.py...")
    unittest.main(exit=False) # exit=False 避免在 Jupyter 环境中退出
