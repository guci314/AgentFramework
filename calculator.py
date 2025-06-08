
# calculator.py
"""
这是一个简单的计算器模块，包含一个Calculator类。
"""

class Calculator:
    """
    一个简单的计算器类，提供基本的算术运算功能。
    """
    def add(self, a, b):
        """
        计算两个数的和。
        :param a: 第一个数 (int 或 float)
        :param b: 第二个数 (int 或 float)
        :return: a 和 b 的和 (int 或 float)
        :raises TypeError: 如果输入参数不是数字类型
        """
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            raise TypeError("输入参数必须是数字类型 (int 或 float)")
        return a + b

    def subtract(self, a, b):
        """
        计算两个数的差。
        :param a: 第一个数 (int 或 float)
        :param b: 第二个数 (int 或 float)
        :return: a 和 b 的差 (int 或 float)
        :raises TypeError: 如果输入参数不是数字类型
        """
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            raise TypeError("输入参数必须是数字类型 (int 或 float)")
        return a - b

    def multiply(self, a, b):
        """
        计算两个数的积。
        :param a: 第一个数 (int 或 float)
        :param b: 第二个数 (int 或 float)
        :return: a 和 b 的积 (int 或 float)
        :raises TypeError: 如果输入参数不是数字类型
        """
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            raise TypeError("输入参数必须是数字类型 (int 或 float)")
        return a * b

    def divide(self, a, b):
        """
        计算两个数的商。
        :param a: 被除数 (int 或 float)
        :param b: 除数 (int 或 float)
        :return: a 除以 b 的商 (float)
        :raises TypeError: 如果输入参数不是数字类型
        :raises ValueError: 如果除数为0
        """
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            raise TypeError("输入参数必须是数字类型 (int 或 float)")
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
