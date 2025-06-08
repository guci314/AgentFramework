
# test_calculator.py
"""
这是Calculator类的单元测试模块。
"""
import unittest
# 'from calculator import Calculator' will work when test_calculator.py is run/imported
# assuming calculator.py is in the same directory or Python path.
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    """
    Calculator类的测试用例。
    """

    def setUp(self):
        """
        这个方法在每个测试方法执行前调用，用于设置测试环境。
        """
        self.calculator = Calculator()
        # print(f"\n正在运行测试: {self._testMethodName}") # Optional: for verbose logging

    def tearDown(self):
        """
        这个方法在每个测试方法执行后调用，用于清理测试环境。
        """
        # print(f"测试完成: {self._testMethodName}") # Optional: for verbose logging
        pass

    def test_add(self):
        """测试加法功能"""
        self.assertEqual(self.calculator.add(2, 3), 5, "2 + 3 应该等于 5")
        self.assertEqual(self.calculator.add(-1, 1), 0, "-1 + 1 应该等于 0")
        self.assertAlmostEqual(self.calculator.add(0.1, 0.2), 0.3, msg="0.1 + 0.2 应该约等于 0.3")
        # Regex for error message: "输入参数必须是数字类型 (int 或 float)"
        # In the test_calculator.py file, this will be "输入参数必须是数字类型 \(int 或 float\)"
        # The string literal in this triple-quoted code to produce that is "输入参数必须是数字类型 \\(int 或 float\\)"
        with self.assertRaisesRegex(TypeError, "输入参数必须是数字类型 \\(int 或 float\\)"):
            self.calculator.add("2", 3)
        with self.assertRaisesRegex(TypeError, "输入参数必须是数字类型 \\(int 或 float\\)"):
            self.calculator.add(2, "3")

    def test_subtract(self):
        """测试减法功能"""
        self.assertEqual(self.calculator.subtract(10, 5), 5, "10 - 5 应该等于 5")
        self.assertEqual(self.calculator.subtract(-1, -1), 0, "-1 - (-1) 应该等于 0")
        self.assertAlmostEqual(self.calculator.subtract(0.3, 0.1), 0.2, msg="0.3 - 0.1 应该约等于 0.2")
        with self.assertRaisesRegex(TypeError, "输入参数必须是数字类型 \\(int 或 float\\)"):
            self.calculator.subtract("10", 5)

    def test_multiply(self):
        """测试乘法功能"""
        self.assertEqual(self.calculator.multiply(3, 7), 21, "3 * 7 应该等于 21")
        self.assertEqual(self.calculator.multiply(-1, 0), 0, "-1 * 0 应该等于 0")
        self.assertAlmostEqual(self.calculator.multiply(0.5, 0.5), 0.25, msg="0.5 * 0.5 应该约等于 0.25")
        with self.assertRaisesRegex(TypeError, "输入参数必须是数字类型 \\(int 或 float\\)"):
            self.calculator.multiply(None, 5)

    def test_divide(self):
        """测试除法功能"""
        self.assertEqual(self.calculator.divide(10, 2), 5, "10 / 2 应该等于 5")
        self.assertAlmostEqual(self.calculator.divide(5, 2), 2.5, msg="5 / 2 应该等于 2.5")
        
        # Test division by zero
        with self.assertRaisesRegex(ValueError, "除数不能为零"): # No special regex chars here
            self.calculator.divide(10, 0)
        
        # Test type error for division
        with self.assertRaisesRegex(TypeError, "输入参数必须是数字类型 \\(int 或 float\\)"):
            self.calculator.divide(10, "2")

# This part is typically for command-line execution of the test file.
# if __name__ == '__main__':
#     unittest.main(verbosity=2)
