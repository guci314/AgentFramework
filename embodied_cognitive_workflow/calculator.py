
class Calculator:
    """简单的计算器类，包含基本运算方法"""
    
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
        """除法运算，包含除零错误处理"""
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b
