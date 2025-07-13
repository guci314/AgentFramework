
class Calculator:
    def __init__(self):
        pass
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

if __name__ == "__main__":
    calc = Calculator()
    print("Addition:", calc.add(5, 3))
    print("Subtraction:", calc.subtract(5, 3))
    print("Multiplication:", calc.multiply(5, 3))
    print("Division:", calc.divide(5, 3))
