import math
from typing import Union

class Calculator:
    """高级科学计算器实现
    
    支持基本算术运算、指数/对数运算、三角函数等数学运算。
    所有方法都包含完整的类型提示和详细的文档说明。
    """
    
    def add(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """加法运算
        Args:
            a: 第一个操作数
            b: 第二个操作数
        Returns:
            两数之和，保持输入类型(int或float)
        """
        return a + b
        
    def subtract(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """减法运算
        Args:
            a: 被减数
            b: 减数
        Returns:
            两数之差，保持输入类型(int或float)
        """
        return a - b
        
    def multiply(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """乘法运算
        Args:
            a: 第一个因数
            b: 第二个因数
        Returns:
            两数之积，保持输入类型(int或float)
        """
        return a * b
        
    def divide(self, a: Union[int, float], b: Union[int, float]) -> float:
        """除法运算
        Args:
            a: 被除数
            b: 除数
        Returns:
            两数之商，总是返回float类型
        Raises:
            ValueError: 当除数为零时抛出
        """
        if b == 0:
            raise ValueError("除数不能为零")
        return float(a) / float(b)
        
    def power(self, base: Union[int, float], exponent: Union[int, float]) -> float:
        """幂运算
        Args:
            base: 底数
            exponent: 指数
        Returns:
            base的exponent次幂
        """
        return math.pow(base, exponent)
        
    def square_root(self, x: Union[int, float]) -> float:
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
        
    def factorial(self, n: int) -> int:
        """阶乘运算
        Args:
            n: 非负整数
        Returns:
            n的阶乘
        Raises:
            ValueError: 当n为负数时抛出
        """
        if n < 0:
            raise ValueError("阶乘只定义在非负整数")
        return math.factorial(n)
        
    def log(self, x: Union[int, float], base: Union[int, float] = math.e) -> float:
        """对数运算
        Args:
            x: 真数
            base: 底数(默认为自然对数e)
        Returns:
            以base为底的x的对数
        Raises:
            ValueError: 当x<=0或base<=0或base=1时抛出
        """
        if x <= 0 or base <= 0 or base == 1:
            raise ValueError("对数参数必须满足x>0, base>0且base≠1")
        return math.log(x, base)
        
    def sin(self, x: Union[int, float], degrees: bool = False) -> float:
        """正弦函数
        Args:
            x: 角度值
            degrees: 是否为角度制(默认为弧度制)
        Returns:
            x的正弦值
        """
        if degrees:
            x = math.radians(x)
        return math.sin(x)

if __name__ == "__main__":
    calc = Calculator()
    print("加法测试:", calc.add(5, 3))
    print("减法测试:", calc.subtract(5, 3))
    print("乘法测试:", calc.multiply(5, 3))
    print("除法测试:", calc.divide(5, 3))
    print("幂运算测试:", calc.power(2, 3))
    print("平方根测试:", calc.square_root(9))
    print("阶乘测试:", calc.factorial(5))
    print("对数测试:", calc.log(100, 10))
    print("正弦测试(角度):", calc.sin(30, degrees=True))
