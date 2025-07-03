
import unittest
from calculator import add, subtract, multiply, divide

class TestCalculator(unittest.TestCase):
    def test_divide(self):
        self.assertEqual(divide(6, 3), 2)
        self.assertEqual(divide(-10, 2), -5)
        self.assertEqual(divide(1, 2), 0.5)
        self.assertEqual(divide(0, 5), 0)
        self.assertEqual(divide(2.5, 0.5), 5.0)
        self.assertEqual(divide(-9, -3), 3)
        
    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(10, 0)
        with self.assertRaises(ValueError):
            divide(0, 0)
        with self.assertRaises(ValueError):
            divide(-5, 0)

    def test_multiply(self):
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(multiply(-1, 5), -5)
        self.assertEqual(multiply(0, 100), 0)
        self.assertEqual(multiply(2.5, 4), 10.0)
        self.assertEqual(multiply(-3, -4), 12)
        self.assertEqual(multiply(999999, 0), 0)  # 大数乘零测试

    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(-1, 1), -2)
        self.assertEqual(subtract(0, 0), 0)
        self.assertEqual(subtract(3.5, 1.5), 2.0)
        self.assertEqual(subtract(10, -5), 15)

    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(-1, 1), -2)
        self.assertEqual(subtract(0, 0), 0)
        self.assertEqual(subtract(3.5, 1.5), 2.0)
        self.assertEqual(subtract(10, -5), 15)

    def test_add(self):
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(0, 0), 0)
        self.assertEqual(add(2.5, 3.5), 6.0)

if __name__ == '__main__':
    unittest.main()
