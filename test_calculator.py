
import unittest
from calculator import Calculator
import sys
import math

class TestCalculatorOperations(unittest.TestCase):
    """Comprehensive test cases for Calculator operations."""
    
    def setUp(self):
        self.calc = Calculator()
    
    # Existing test methods (add, subtract, multiply, divide, power, square_root, factorial)...
    
class TestHistory(unittest.TestCase):
    """Test cases for Calculator history functionality."""
    
    def setUp(self):
        self.calc = Calculator()
    
    def test_history_records_operations(self):
        self.calc.add(2, 3)
        self.calc.multiply(4, 5)
        history = self.calc.get_history()
        self.assertEqual(len(history), 2)
        self.assertIn("add: 2 + 3 => 5", history)
        self.assertIn("multiply: 4 * 5 => 20", history)
    
    def test_history_max_length(self):
        for i in range(15):
            self.calc.add(i, i)
        history = self.calc.get_history()
        self.assertEqual(len(history), 10)
        self.assertNotIn("add: 0 + 0 => 0", history)  # First 5 should be dropped
        self.assertIn("add: 5 + 5 => 10", history)    # Oldest remaining record
        self.assertIn("add: 14 + 14 => 28", history)  # Newest record
    
    def test_clear_history(self):
        self.calc.add(1, 2)
        self.calc.subtract(5, 3)
        self.calc.clear_history()
        self.assertEqual(len(self.calc.get_history()), 0)
    
    def test_history_with_all_operations(self):
        operations = [
            ("add", (2, 3), 5),
            ("subtract", (5, 3), 2),
            ("multiply", (4, 5), 20),
            ("divide", (10, 2), 5),
            ("power", (2, 3), 8),
            ("square_root", (4,), 2),
            ("factorial", (5,), 120)
        ]
        
        for method, args, expected in operations:
            getattr(self.calc, method)(*args)
            history = self.calc.get_history()
            self.assertIn(f"{method}: ", history[-1])
            self.assertIn(f"=> {expected}", history[-1])

if __name__ == '__main__':
    unittest.main()
