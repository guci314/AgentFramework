
import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    """Calculator类的单元测试"""
    
    def setUp(self):
        self.calc = Calculator()
    
    def test_add(self):
        """测试加法运算"""
        # 正常情况测试
        self.assertEqual(self.calc.add(2, 3), 5)
        # 边界值测试
        self.assertEqual(self.calc.add(-1, 1), 0)
        self.assertEqual(self.calc.add(0, 0), 0)
        # 浮点数测试
        self.assertAlmostEqual(self.calc.add(1.5, 2.5), 4.0)
        # 大数测试
        self.assertEqual(self.calc.add(999999999, 1), 1000000000)
    
    def test_subtract(self):
        """测试减法运算"""
        # 正常情况测试
        self.assertEqual(self.calc.subtract(5, 3), 2)
        # 负数结果测试
        self.assertEqual(self.calc.subtract(3, 5), -2)
        # 边界值测试
        self.assertEqual(self.calc.subtract(0, 0), 0)
        # 浮点数测试
        self.assertAlmostEqual(self.calc.subtract(2.5, 1.5), 1.0)
    
    def test_multiply(self):
        """测试乘法运算"""
        # 正常情况测试
        self.assertEqual(self.calc.multiply(2, 3), 6)
        # 负数测试
        self.assertEqual(self.calc.multiply(-2, 3), -6)
        # 零乘测试
        self.assertEqual(self.calc.multiply(0, 5), 0)
        # 浮点数测试
        self.assertAlmostEqual(self.calc.multiply(1.5, 2), 3.0)
        # 大数测试
        self.assertEqual(self.calc.multiply(999999, 999999), 999998000001)
    
    def test_divide(self):
        """测试除法运算"""
        # 正常情况测试
        self.assertEqual(self.calc.divide(6, 3), 2)
        # 浮点结果测试
        self.assertAlmostEqual(self.calc.divide(5, 2), 2.5)
        # 零被除数测试
        self.assertEqual(self.calc.divide(0, 5), 0)
        # 负数测试
        self.assertEqual(self.calc.divide(-6, 3), -2)
        # 浮点数精确测试
        self.assertAlmostEqual(self.calc.divide(1, 3), 0.33333333, places=7)
    
    def test_divide_by_zero(self):
        """测试除零错误"""
        with self.assertRaises(ValueError) as context:
            self.calc.divide(1, 0)
        self.assertEqual(str(context.exception), "除数不能为零")
        # 测试浮点数除零
        with self.assertRaises(ValueError):
            self.calc.divide(1.5, 0)

if __name__ == '__main__':
    unittest.main()
