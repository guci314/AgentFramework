
import unittest
import sys
import os

# Add the directory containing calculator.py to the path
# This is necessary if test_calculator.py is in a different directory
# or if running from a context where the current directory isn't in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the Calculator class from the calculator module
# We need to handle potential module reloading if calculator.py was modified
import importlib
try:
    import calculator
    importlib.reload(calculator) # Reload the module to get the latest changes
except ImportError:
    # If calculator.py was just created, it might not be in sys.modules yet
    # In this case, a direct import will work.
    # If it's already in sys.modules but not reloaded, the reload above handles it.
    pass # No action needed, the import will happen below if not already done

# Ensure calculator module is available
if 'calculator' not in sys.modules:
    # This block handles cases where the module might not have been imported yet
    # or if the path was just added.
    # We use importlib.util to load it explicitly if needed.
    spec = importlib.util.spec_from_file_location("calculator", "calculator.py")
    if spec:
        calculator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(calculator)
    else:
        raise ImportError("Could not find calculator.py module.")

from calculator import Calculator

class TestCalculator(unittest.TestCase):
    '''
    Unit tests for the Calculator class.
    '''

    def setUp(self):
        '''Set up for test methods.'''
        self.calc = Calculator()
        print(f"\nSetting up test: {self._testMethodName}")

    def tearDown(self):
        '''Clean up after test methods.'''
        print(f"Tearing down test: {self._testMethodName}")

    def test_add(self):
        '''Test the add method.'''
        print("Testing addition...")
        self.assertEqual(self.calc.add(1, 2), 3)
        self.assertEqual(self.calc.add(-1, 1), 0)
        self.assertEqual(self.calc.add(-1, -1), -2)
        self.assertEqual(self.calc.add(0, 0), 0)
        self.assertEqual(self.calc.add(100, 200), 300)
        print("Addition tests passed.")

    def test_subtract(self):
        '''Test the subtract method.'''
        print("Testing subtraction...")
        self.assertEqual(self.calc.subtract(5, 3), 2)
        self.assertEqual(self.calc.subtract(3, 5), -2)
        self.assertEqual(self.calc.subtract(0, 0), 0)
        self.assertEqual(self.calc.subtract(10, -5), 15)
        self.assertEqual(self.calc.subtract(-5, -10), 5)
        print("Subtraction tests passed.")

    def test_multiply(self):
        '''Test the multiply method.'''
        print("Testing multiplication...")
        self.assertEqual(self.calc.multiply(2, 3), 6)
        self.assertEqual(self.calc.multiply(-2, 3), -6)
        self.assertEqual(self.calc.multiply(-2, -3), 6)
        self.assertEqual(self.calc.multiply(0, 5), 0)
        self.assertEqual(self.calc.multiply(1, 10), 10)
        print("Multiplication tests passed.")

    def test_divide(self):
        '''Test the divide method for valid cases.'''
        print("Testing division...")
        self.assertEqual(self.calc.divide(6, 3), 2.0)
        self.assertEqual(self.calc.divide(5, 2), 2.5)
        self.assertEqual(self.calc.divide(-10, 2), -5.0)
        self.assertEqual(self.calc.divide(10, -2), -5.0)
        self.assertEqual(self.calc.divide(-10, -2), 5.0)
        self.assertEqual(self.calc.divide(0, 5), 0.0)
        print("Division tests passed.")

    def test_divide_by_zero(self):
        '''Test the divide method for division by zero error.'''
        print("Testing division by zero error handling...")
        with self.assertRaisesRegex(ValueError, "Cannot divide by zero!"):
            self.calc.divide(10, 0)
        print("Division by zero error handling test passed.")

# This allows running the tests directly from the script
if __name__ == '__main__':
    # Use TextTestRunner to capture output, especially stderr for unittest
    # unittest.main() by default uses TextTestRunner
    # For Jupyter, we might want to run it programmatically
    print("Running tests for Calculator class...")
    # unittest.main() # This would exit the notebook kernel
    
    # To run tests programmatically without exiting the kernel:
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCalculator))
    
    # Create a TextTestRunner instance
    # We can redirect stdout/stderr if needed, but for now, let it print normally
    runner = unittest.TextTestRunner(verbosity=2) # verbosity=2 shows more details
    runner.run(suite)
    print("All tests finished.")
