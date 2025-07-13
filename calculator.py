
class Calculator:
    def add(self, a, b):
        # 确保返回加法结果
        return a + b

    def subtract(self, a, b):
        # 确保返回减法结果
        return a - b

    def multiply(self, a, b):
        # 确保返回乘法结果
        return a * b

    def divide(self, a, b):
        # 确保在除数为零时抛出 ValueError
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        # 确保返回除法结果
        return a / b

if __name__ == '__main__':
    calc = Calculator()
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"5 - 2 = {calc.subtract(5, 2)}")
    print(f"4 * 6 = {calc.multiply(4, 6)}")
    print(f"10 / 2 = {calc.divide(10, 2)}")
    try:
        calc.divide(10, 0)
    except ValueError as e:
        print(f"Error: {e}")
