class Calculator:
    """简单的计算器类，提供基本四则运算"""
    
    def add(self, a: float, b: float) -> float:
        """加法运算"""
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """减法运算"""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """乘法运算"""
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        """除法运算
        注意: 当除数为0时会抛出ZeroDivisionError
        """
        if b == 0:
            raise ZeroDivisionError("除数不能为0")
        return a / b
