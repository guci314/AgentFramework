
import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    """Calculator类的单元测试"""
    
    def setUp(self):
        self.calc = Calculator()
    
    def test_add(self):
        """测试加法运算"""
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)
        self.assertEqual(self.calc.add(0, 0), 0)
    
    def test_subtract(self):
        """测试减法运算"""
        self.assertEqual(self.calc.subtract(5, 2), 3)
        self.assertEqual(self.calc.subtract(10, 10), 0)
        self.assertEqual(self.calc.subtract(-1, -1), 0)
    
    def test_multiply(self):
        """测试乘法运算"""
        self.assertEqual(self.calc.multiply(3, 4), 12)
        self.assertEqual(self.calc.multiply(0, 5), 0)
        self.assertEqual(self.calc.multiply(-2, 3), -6)
    
    def test_divide(self):
        """测试除法运算"""
        self.assertEqual(self.calc.divide(10, 2), 5)
        self.assertEqual(self.calc.divide(9, 3), 3)
        self.assertAlmostEqual(self.calc.divide(1, 3), 0.333333, places=6)
    
    def test_divide_by_zero(self):
        """测试除零错误处理"""
        with self.assertRaises(ValueError) as context:
            self.calc.divide(5, 0)
        self.assertEqual(str(context.exception), "除数不能为零")

if __name__ == '__main__':
    unittest.main()
