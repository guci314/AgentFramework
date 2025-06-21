class Calculator:
    def __init__(self):
        self._last_result = None
    
    def add(self, a, b):
        """加法运算"""
        result = a + b
        self._last_result = result
        return result
    
    def subtract(self, a, b):
        """减法运算"""
        result = a - b
        self._last_result = result
        return result
    
    def multiply(self, a, b):
        """乘法运算"""
        result = a * b
        self._last_result = result
        return result
    
    def divide(self, a, b):
        """除法运算"""
        if b == 0:
            raise ValueError("除数不能为零")
        result = a / b
        self._last_result = result
        return result
    
    def get_last_result(self):
        """获取上一次计算结果"""
        return self._last_result


def test_calculator():
    """单元测试函数"""
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.subtract(5, 2) == 3
    assert calc.multiply(3, 4) == 12
    assert calc.divide(10, 2) == 5
    try:
        calc.divide(5, 0)
        assert False
    except ValueError:
        pass
