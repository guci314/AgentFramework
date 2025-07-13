import unittest
from calculator1 import Calculator

class TestCalculator(unittest.TestCase):
    """Calculator类的单元测试"""
    
    def setUp(self):
        """每个测试方法前创建新的计算器实例"""
        self.calc = Calculator()
    
    def test_add(self):
        """测试加法"""
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)
        self.assertEqual(self.calc.add(0, 0), 0)
        self.assertEqual(self.calc.add(2.5, 3.5), 6.0)
    
    def test_subtract(self):
        """测试减法"""
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(10, -5), 15)
        self.assertEqual(self.calc.subtract(0, 0), 0)
        self.assertEqual(self.calc.subtract(5.5, 2.5), 3.0)
    
    def test_multiply(self):
        """测试乘法"""
        self.assertEqual(self.calc.multiply(3, 4), 12)
        self.assertEqual(self.calc.multiply(-2, 5), -10)
        self.assertEqual(self.calc.multiply(0, 100), 0)
        self.assertEqual(self.calc.multiply(1.5, 2), 3.0)
    
    def test_divide(self):
        """测试除法"""
        self.assertEqual(self.calc.divide(10, 2), 5)
        self.assertEqual(self.calc.divide(9, 3), 3)
        self.assertAlmostEqual(self.calc.divide(1, 3), 0.333333, places=6)
        self.assertEqual(self.calc.divide(5.5, 2), 2.75)
        
    def test_divide_by_zero(self):
        """测试除零异常"""
        with self.assertRaises(ValueError):
            self.calc.divide(5, 0)
    
    def test_power(self):
        """测试幂运算"""
        self.assertEqual(self.calc.power(2, 3), 8)
        self.assertEqual(self.calc.power(5, 0), 1)
        self.assertEqual(self.calc.power(10, -1), 0.1)
        self.assertAlmostEqual(self.calc.power(4, 0.5), 2.0)
    
    def test_sqrt(self):
        """测试平方根"""
        self.assertEqual(self.calc.sqrt(4), 2)
        self.assertEqual(self.calc.sqrt(0), 0)
        self.assertAlmostEqual(self.calc.sqrt(2), 1.414213, places=6)
    
    def test_sqrt_negative(self):
        """测试负数平方根异常"""
        with self.assertRaises(ValueError):
            self.calc.sqrt(-1)

if __name__ == '__main__':
    unittest.main()
