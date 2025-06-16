import unittest

class SimpleCalculator:
    def add(self, a, b):
        '''加法'''
        return a + b
        
    def subtract(self, a, b):
        '''减法'''
        return a - b
        
    def multiply(self, a, b):
        '''乘法'''
        return a * b
        
    def divide(self, a, b):
        '''除法'''
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b

class TestSimpleCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = SimpleCalculator()
        
    def test_add(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)
        
    def test_subtract(self):
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(3, 5), -2)
        
    def test_multiply(self):
        self.assertEqual(self.calc.multiply(2, 3), 6)
        self.assertEqual(self.calc.multiply(-1, 1), -1)
        
    def test_divide(self):
        self.assertEqual(self.calc.divide(6, 3), 2)
        self.assertAlmostEqual(self.calc.divide(1, 3), 0.333333, places=6)
        with self.assertRaises(ValueError):
            self.calc.divide(1, 0)

if __name__ == '__main__':
    unittest.main()