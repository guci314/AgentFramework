import unittest
import sys
import os

# 添加项目目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    """测试Calculator类的各个方法"""
    
    def setUp(self):
        """在每个测试方法前创建一个Calculator实例"""
        self.calc = Calculator()
    
    def test_add(self):
        """测试加法运算"""
        self.assertEqual(self.calc.add(3, 5), 8)
        self.assertEqual(self.calc.add(-1, 1), 0)
        self.assertEqual(self.calc.add(0, 0), 0)
    
    def test_subtract(self):
        """测试减法运算"""
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(10, 10), 0)
        self.assertEqual(self.calc.subtract(-1, -1), 0)
    
    def test_multiply(self):
        """测试乘法运算"""
        self.assertEqual(self.calc.multiply(3, 5), 15)
        self.assertEqual(self.calc.multiply(-1, 5), -5)
        self.assertEqual(self.calc.multiply(0, 100), 0)
    
    def test_divide(self):
        """测试除法运算"""
        self.assertEqual(self.calc.divide(10, 2), 5)
        self.assertEqual(self.calc.divide(9, 3), 3)
        self.assertEqual(self.calc.divide(5, 2), 2.5)
        
        # 测试除零异常
        with self.assertRaises(ValueError):
            self.calc.divide(10, 0)

if __name__ == '__main__':
    unittest.main()
