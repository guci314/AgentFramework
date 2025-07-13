"""
Calculator class with basic arithmetic operations.
"""
from typing import Union


class Calculator:
    """A simple calculator class supporting basic arithmetic operations.
    
    This calculator provides methods for addition, subtraction, multiplication,
    and division operations with proper error handling and type annotations.
    """
    
    def __init__(self) -> None:
        """Initialize the Calculator instance."""
        pass
    
    def add(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Add two numbers.
        
        Args:
            a: The first number
            b: The second number
            
        Returns:
            The sum of a and b
        """
        return a + b
    
    def subtract(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Subtract b from a.
        
        Args:
            a: The first number (minuend)
            b: The second number (subtrahend)
            
        Returns:
            The difference of a and b
        """
        return a - b
    
    def multiply(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Multiply two numbers.
        
        Args:
            a: The first number
            b: The second number
            
        Returns:
            The product of a and b
        """
        return a * b
    
    def divide(self, a: Union[int, float], b: Union[int, float]) -> float:
        """Divide a by b.
        
        Args:
            a: The dividend
            b: The divisor
            
        Returns:
            The quotient of a divided by b
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
    
    def __str__(self) -> str:
        """Return a string representation of the Calculator.
        
        Returns:
            A user-friendly string representation
        """
        return "Calculator(ready)"
    
    def __repr__(self) -> str:
        """Return a detailed string representation of the Calculator.
        
        Returns:
            A detailed string representation for debugging
        """
        return "Calculator()"