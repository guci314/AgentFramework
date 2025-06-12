import unittest

class SimpleCalculator:
    '''简单的计算器类，支持加减乘除运算'''
    
    def add(self, a, b):
        '''加法运算'''
        return a + b
    
    def subtract(self, a, b):
        '''减法运算'''
        return a - b
    
    def multiply(self, a, b):
        '''乘法运算'''
        return a * b
    
    def divide(self, a, b):
        '''除法运算'''
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b

class TestSimpleCalculator(unittest.TestCase):
    '''计算器单元测试类'''
    
    def setUp(self):
        self.calc = SimpleCalculator()
    
    def test_add(self):
        '''测试加法'''
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.add(-1, 1), 0)
        self.assertEqual(self.calc.add(0, 0), 0)
    
    def test_subtract(self):
        '''测试减法'''
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(-1, -1), 0)
        self.assertEqual(self.calc.subtract(0, 0), 0)
    
    def test_multiply(self):
        '''测试乘法'''
        self.assertEqual(self.calc.multiply(2, 3), 6)
        self.assertEqual(self.calc.multiply(-1, 1), -1)
        self.assertEqual(self.calc.multiply(0, 5), 0)
    
    def test_divide(self):
        '''测试除法'''
        self.assertEqual(self.calc.divide(6, 3), 2)
        self.assertEqual(self.calc.divide(5, 2), 2.5)
        self.assertEqual(self.calc.divide(-4, 2), -2)
        with self.assertRaises(ValueError):
            self.calc.divide(1, 0)

if __name__ == '__main__':
    unittest.main()
