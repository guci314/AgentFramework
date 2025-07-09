class Calculator:
    """一个简单的计算器类"""
    
    def add(self, a, b):
        """加法"""
        return a + b
        
    def subtract(self, a, b):
        """减法"""
        return a - b
        
    def multiply(self, a, b):
        """乘法"""
        return a * b
        
    def divide(self, a, b):
        """除法"""
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
