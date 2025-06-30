class Calculator:
    """简单的计算器类，实现加减乘除基本运算"""
    
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
        """除法运算"""
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b


if __name__ == "__main__":
    calc = Calculator()
    print("Calculator initialized")
