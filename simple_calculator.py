class SimpleCalculator:
    def __init__(self):
        self.last_result = None
    
    def add(self, a, b):
        """加法运算"""
        self.last_result = a + b
        return self.last_result
    
    def subtract(self, a, b):
        """减法运算"""
        self.last_result = a - b
        return self.last_result
    
    def multiply(self, a, b):
        """乘法运算"""
        self.last_result = a * b
        return self.last_result
    
    def divide(self, a, b):
        """除法运算"""
        if b == 0:
            raise ValueError("除数不能为零")
        self.last_result = a / b
        return self.last_result

def test_calculator():
    calc = SimpleCalculator()
    
    # 测试加法
    assert calc.add(2, 3) == 5, "加法测试失败"
    assert calc.last_result == 5, "加法结果存储失败"
    
    # 测试减法
    assert calc.subtract(5, 2) == 3, "减法测试失败"
    assert calc.last_result == 3, "减法结果存储失败"
    
    # 测试乘法
    assert calc.multiply(3, 4) == 12, "乘法测试失败"
    assert calc.last_result == 12, "乘法结果存储失败"
    
    # 测试除法
    assert calc.divide(10, 2) == 5, "除法测试失败"
    assert calc.last_result == 5, "除法结果存储失败"
    
    # 测试除零异常
    try:
        calc.divide(5, 0)
        assert False, "除零异常未触发"
    except ValueError as e:
        assert str(e) == "除数不能为零", "异常消息不正确"
    
    print("所有单元测试通过")