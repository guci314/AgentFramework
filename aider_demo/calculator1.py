class Calculator:
    """增强的Python计算器类
    
    提供基本数学运算功能，包括：
    - 加减乘除
    - 幂运算
    - 模运算
    - 平方根
    支持整数和浮点数运算，并记录最后一次计算结果。
    
    示例:
        >>> calc = Calculator()
        >>> calc.add(2, 3)
        5.0
        >>> calc.last_result
        5.0
    """
    
    def __init__(self):
        self.last_result = None
    
    def add(self, a: float, b: float) -> float:
        """加法运算"""
        result = a + b
        self.last_result = result
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """减法运算"""
        result = a - b
        self.last_result = result
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """乘法运算"""
        result = a * b
        self.last_result = result
        return result
    
    def divide(self, a: float, b: float) -> float:
        """除法运算"""
        if b == 0:
            raise ValueError("除数不能为零")
        result = a / b
        self.last_result = result
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """幂运算"""
        result = base ** exponent
        self.last_result = result
        return result
    
    def modulo(self, a: float, b: float) -> float:
        """模运算"""
        if b == 0:
            raise ValueError("模数不能为零")
        result = a % b
        self.last_result = result
        return result
    
    def square_root(self, x: float) -> float:
        """平方根运算"""
        if x < 0:
            raise ValueError("不能计算负数的平方根")
        result = x ** 0.5
        self.last_result = result
        return result
