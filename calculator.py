
class Calculator:
    """基本计算器类，实现四则运算"""
    
    def add(self, a, b):
        """加法运算"""
        return a + b
    
    def subtract(self, a, b):
        """减法运算"""
        return a - b
    
    def multiply(self, a, b):
        """乘法运算"""
        return a * b
    
    def divide(self, a, b):
        """除法运算，处理除零错误"""
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
