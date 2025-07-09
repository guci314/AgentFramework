import math

class Calculator:
    """高级计算器实现，支持加减乘除、幂运算和平方根"""
    
    def add(self, a: float, b: float) -> float:
        """加法运算
        Args:
            a: 第一个操作数
            b: 第二个操作数
        Returns:
            两数之和
        """
        return a + b
        
    def subtract(self, a: float, b: float) -> float:
        """减法运算
        Args:
            a: 被减数
            b: 减数
        Returns:
            两数之差
        """
        return a - b
        
    def multiply(self, a: float, b: float) -> float:
        """乘法运算
        Args:
            a: 第一个因数
            b: 第二个因数
        Returns:
            两数之积
        """
        return a * b
        
    def divide(self, a: float, b: float) -> float:
        """除法运算
        Args:
            a: 被除数
            b: 除数
        Returns:
            两数之商
        Raises:
            ValueError: 当除数为零时抛出
        """
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
        
    def power(self, base: float, exponent: float) -> float:
        """幂运算
        Args:
            base: 底数
            exponent: 指数
        Returns:
            base的exponent次幂
        """
        return math.pow(base, exponent)
        
    def square_root(self, x: float) -> float:
        """平方根运算
        Args:
            x: 需要求平方根的数
        Returns:
            x的平方根
        Raises:
            ValueError: 当x为负数时抛出
        """
        if x < 0:
            raise ValueError("负数没有实数平方根")
        return math.sqrt(x)

if __name__ == "__main__":
    calc = Calculator()
    print("加法测试:", calc.add(5, 3))
    print("减法测试:", calc.subtract(5, 3))
    print("乘法测试:", calc.multiply(5, 3))
    print("除法测试:", calc.divide(5, 3))
    print("幂运算测试:", calc.power(2, 3))
    print("平方根测试:", calc.square_root(9))
