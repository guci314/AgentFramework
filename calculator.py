
class Calculator:
    def add(self, a, b):
        '''Performs addition of two numbers.'''
        return a + b

    def subtract(self, a, b):
        '''Performs subtraction of two numbers.'''
        return a - b

    def multiply(self, a, b):
        '''Performs multiplication of two numbers.'''
        return a * b

    def divide(self, a, b):
        '''
        Performs division of two numbers.
        Handles division by zero error.
        '''
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        return a / b
