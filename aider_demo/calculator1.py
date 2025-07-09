class Calculator:
    """简单的Python计算器类"""
    
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
        """除法运算"""
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
