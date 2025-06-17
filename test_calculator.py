
import unittest
from calculator import add, subtract, multiply, divide

class TestCalculator(unittest.TestCase):
    def test_add(self):
        '''测试加法功能'''
        self.assertEqual(add(5, 3), 8)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(0, 0), 0)
        self.assertEqual(add(2.5, 3.5), 6.0)

    def test_subtract(self):
        '''测试减法功能'''
        self.assertEqual(subtract(10, 4), 6)
        self.assertEqual(subtract(5, 5), 0)
        self.assertEqual(subtract(0, 5), -5)
        self.assertEqual(subtract(3.5, 1.5), 2.0)

    def test_multiply(self):
        '''测试乘法功能'''
        self.assertEqual(multiply(6, 7), 42)
        self.assertEqual(multiply(0, 5), 0)
        self.assertEqual(multiply(-3, 4), -12)
        self.assertEqual(multiply(2.5, 4), 10.0)

    def test_divide(self):
        '''测试除法功能'''
        self.assertEqual(divide(10, 2), 5)
        self.assertEqual(divide(9, 3), 3)
        self.assertEqual(divide(5, 2), 2.5)
        self.assertIsNone(divide(5, 0), "除零应返回None")
        self.assertEqual(divide(0, 5), 0)

if __name__ == '__main__':
    unittest.main()
