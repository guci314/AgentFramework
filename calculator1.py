class Calculator:
    """基本计算器实现，支持加减乘除运算"""
    
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
    print("加法测试:", calc.add(5, 3))
    print("减法测试:", calc.subtract(5, 3))
    print("乘法测试:", calc.multiply(5, 3))
    print("除法测试:", calc.divide(5, 3))