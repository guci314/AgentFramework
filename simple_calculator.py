"""
实现一个基础计算器类，包含加减乘除四种基本运算方法
每个方法都包含参数验证和异常处理
"""
class Calculator:
    def __init__(self):
        """
        初始化计算器实例
        可以添加状态变量如历史记录等
        """
        self.history = []
    
    def add(self, a, b):
        """
        加法运算
        a: 第一个操作数
        b: 第二个操作数
        返回: a + b 的结果
        """
        try:
            result = a + b
            self.history.append(f'{a} + {b} = {result}')
            return result
        except TypeError as e:
            self.history.append(f'Failed: {a} + {b} (TypeError)')
            raise ValueError(f'无效的输入类型: {type(a)}和{type(b)}') from e
    
    def subtract(self, a, b):
        """
        减法运算
        a: 被减数
        b: 减数
        返回: a - b 的结果
        """
        try:
            result = a - b
            self.history.append(f'{a} - {b} = {result}')
            return result
        except TypeError as e:
            self.history.append(f'Failed: {a} - {b} (TypeError)')
            raise ValueError(f'无效的输入类型: {type(a)}和{type(b)}') from e
    
    def multiply(self, a, b):
        """
        乘法运算
        a: 第一个因数
        b: 第二个因数
        返回: a * b 的结果
        """
        try:
            result = a * b
            self.history.append(f'{a} * {b} = {result}')
            return result
        except TypeError as e:
            self.history.append(f'Failed: {a} * {b} (TypeError)')
            raise ValueError(f'无效的输入类型: {type(a)}和{type(b)}') from e
    
    def divide(self, a, b):
        """
        除法运算
        a: 被除数
        b: 除数
        返回: a / b 的结果
        """
        try:
            if b == 0:
                self.history.append(f'Failed: {a} / {b} (ZeroDivisionError)')
                raise ZeroDivisionError('除数不能为零')
            result = a / b
            self.history.append(f'{a} / {b} = {result}')
            return result
        except TypeError as e:
            self.history.append(f'Failed: {a} / {b} (TypeError)')
            raise ValueError(f'无效的输入类型: {type(a)}和{type(b)}') from e

if __name__ == '__main__':
    # 测试计算器功能
    calc = Calculator()
    
    # 验证加法
    assert calc.add(5, 3) == 8, "加法测试失败"
    assert calc.add(-1, 1) == 0, "负数加法测试失败"
    
    # 验证减法
    assert calc.subtract(10, 4) == 6, "减法测试失败"
    assert calc.subtract(5, -3) == 8, "负数减法测试失败"
    
    # 验证乘法
    assert calc.multiply(7, 6) == 42, "乘法测试失败"
    assert calc.multiply(0, 100) == 0, "零乘法测试失败"
    
    # 验证除法
    assert calc.divide(10, 2) == 5, "除法测试失败"
    assert calc.divide(1, 2) == 0.5, "分数除法测试失败"
    
    # 验证异常处理
    try:
        calc.divide(1, 0)
        assert False, "零除法异常未触发"
    except ZeroDivisionError:
        pass
    
    try:
        calc.add("1", 2)
        assert False, "类型异常未触发"
    except ValueError:
        pass
    
    # 打印历史记录
    print("操作历史记录:")
    for i, record in enumerate(calc.history, 1):
        print(f"{i}. {record}")
    
    print("所有测试通过!")
