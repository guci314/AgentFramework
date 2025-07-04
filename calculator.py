
import math
from collections import deque

class Calculator:
    """A simple calculator class with basic mathematical operations and history tracking."""
    
    def __init__(self):
        self._history = deque(maxlen=10)  # Store last 10 operations
        
    def add(self, a, b):
        """Add two numbers with parameter validation."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers")
        result = a + b
        self._history.append(f"add: {a} + {b} => {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract two numbers with parameter validation."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers")
        result = a - b
        self._history.append(f"subtract: {a} - {b} => {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers with parameter validation."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers")
        result = a * b
        self._history.append(f"multiply: {a} * {b} => {result}")
        return result
    
    def divide(self, a, b):
        """Divide two numbers with parameter validation."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both arguments must be numbers")
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self._history.append(f"divide: {a} / {b} => {result}")
        return result
    
    def power(self, base, exponent, force_integer=False):
        """Calculate base raised to the power of exponent."""
        if not isinstance(base, (int, float)) or not isinstance(exponent, (int, float)):
            raise TypeError("Both arguments must be numbers")
        if exponent == 0:
            result = 1.0
        else:
            result = base ** exponent
            result = float(result) if exponent < 0 else result
        self._history.append(f"power: {base}^{exponent} => {result}")
        return result
    
    def square_root(self, x):
        """Calculate the square root of a number."""
        if not isinstance(x, (int, float)):
            raise TypeError("Input must be a number")
        if x < 0:
            raise ValueError("Cannot calculate square root of negative number")
        result = math.sqrt(x)
        self._history.append(f"square_root: √{x} => {result}")
        return result
    
    def factorial(self, n):
        """
        Calculate factorial of a non-negative integer using iterative approach.
        """
        if not isinstance(n, int):
            raise TypeError("Input must be an integer")
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
            
        if n in (0, 1):
            result = 1
        else:
            use_float = n > 20
            result = 1.0 if use_float else 1
            for i in range(2, n + 1):
                result *= float(i) if use_float else i
                
        self._history.append(f"factorial: {n}! => {result}")
        return result
    
    def get_history(self):
        """Return a list of operation history records."""
        return list(self._history)
    
    def clear_history(self):
        """Clear all operation history records."""
        self._history.clear()
