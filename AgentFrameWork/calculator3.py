"""
Calculator class implementation with basic arithmetic operations.

This module provides a Calculator class that implements four basic arithmetic
operations (addition, subtraction, multiplication, and division) with proper
type hints, parameter validation, and error handling.
"""

from typing import Union, Optional


class Calculator:
    """
    A calculator class for performing basic arithmetic operations.
    
    This class provides methods for addition, subtraction, multiplication,
    and division with proper parameter validation and error handling.
    
    Attributes:
        None
    
    Examples:
        >>> calc = Calculator()
        >>> calc.add(5, 3)
        8
        >>> calc.subtract(10, 4)
        6
        >>> calc.multiply(3, 7)
        21
        >>> calc.divide(15, 3)
        5.0
    """
    
    def __init__(self) -> None:
        """Initialize the Calculator instance."""
        pass
    
    def add(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Add two numbers together.
        
        Args:
            a (Union[int, float]): The first number to add.
            b (Union[int, float]): The second number to add.
            
        Returns:
            Union[int, float]: The sum of a and b.
            
        Raises:
            TypeError: If either a or b is not a number (int or float).
            
        Examples:
            >>> calc = Calculator()
            >>> calc.add(5, 3)
            8
            >>> calc.add(2.5, 3.7)
            6.2
            >>> calc.add(-10, 5)
            -5
        """
        if not isinstance(a, (int, float)):
            raise TypeError(f"First argument must be a number, got {type(a).__name__}")
        if not isinstance(b, (int, float)):
            raise TypeError(f"Second argument must be a number, got {type(b).__name__}")
        
        return a + b
    
    def subtract(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Subtract the second number from the first number.
        
        Args:
            a (Union[int, float]): The number to subtract from (minuend).
            b (Union[int, float]): The number to subtract (subtrahend).
            
        Returns:
            Union[int, float]: The difference of a and b (a - b).
            
        Raises:
            TypeError: If either a or b is not a number (int or float).
            
        Examples:
            >>> calc = Calculator()
            >>> calc.subtract(10, 4)
            6
            >>> calc.subtract(5.5, 2.3)
            3.2
            >>> calc.subtract(3, 8)
            -5
        """
        if not isinstance(a, (int, float)):
            raise TypeError(f"First argument must be a number, got {type(a).__name__}")
        if not isinstance(b, (int, float)):
            raise TypeError(f"Second argument must be a number, got {type(b).__name__}")
        
        return a - b
    
    def multiply(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Multiply two numbers together.
        
        Args:
            a (Union[int, float]): The first number to multiply (multiplicand).
            b (Union[int, float]): The second number to multiply (multiplier).
            
        Returns:
            Union[int, float]: The product of a and b.
            
        Raises:
            TypeError: If either a or b is not a number (int or float).
            
        Examples:
            >>> calc = Calculator()
            >>> calc.multiply(3, 7)
            21
            >>> calc.multiply(2.5, 4)
            10.0
            >>> calc.multiply(-3, 5)
            -15
            >>> calc.multiply(0, 100)
            0
        """
        if not isinstance(a, (int, float)):
            raise TypeError(f"First argument must be a number, got {type(a).__name__}")
        if not isinstance(b, (int, float)):
            raise TypeError(f"Second argument must be a number, got {type(b).__name__}")
        
        return a * b
    
    def divide(self, a: Union[int, float], b: Union[int, float]) -> float:
        """
        Divide the first number by the second number.
        
        This method always returns a float, even when dividing two integers,
        to maintain consistency and prevent integer division issues.
        
        Args:
            a (Union[int, float]): The number to be divided (dividend).
            b (Union[int, float]): The number to divide by (divisor).
            
        Returns:
            float: The quotient of a divided by b.
            
        Raises:
            TypeError: If either a or b is not a number (int or float).
            ZeroDivisionError: If b is zero.
            
        Examples:
            >>> calc = Calculator()
            >>> calc.divide(15, 3)
            5.0
            >>> calc.divide(10, 4)
            2.5
            >>> calc.divide(7.5, 2.5)
            3.0
            >>> calc.divide(-20, 4)
            -5.0
            >>> calc.divide(5, 0)  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
            ...
            ZeroDivisionError: Cannot divide by zero
        """
        if not isinstance(a, (int, float)):
            raise TypeError(f"First argument must be a number, got {type(a).__name__}")
        if not isinstance(b, (int, float)):
            raise TypeError(f"Second argument must be a number, got {type(b).__name__}")
        
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        
        return float(a) / float(b)
    
    def __repr__(self) -> str:
        """
        Return a string representation of the Calculator instance.
        
        Returns:
            str: A string representation of the Calculator.
        """
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        """
        Return a user-friendly string representation of the Calculator.
        
        Returns:
            str: A descriptive string about the Calculator.
        """
        return "Calculator with basic arithmetic operations: add, subtract, multiply, divide"


# Example usage and testing
if __name__ == "__main__":
    # Create a calculator instance
    calc = Calculator()
    
    # Demonstrate basic operations
    print("Calculator Demo:")
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"3 × 7 = {calc.multiply(3, 7)}")
    print(f"15 ÷ 3 = {calc.divide(15, 3)}")
    
    print("\nFloating point operations:")
    print(f"2.5 + 3.7 = {calc.add(2.5, 3.7)}")
    print(f"10.8 - 4.3 = {calc.subtract(10.8, 4.3)}")
    print(f"2.5 × 4 = {calc.multiply(2.5, 4)}")
    print(f"7.5 ÷ 2.5 = {calc.divide(7.5, 2.5)}")
    
    print("\nError handling demo:")
    try:
        result = calc.divide(10, 0)
    except ZeroDivisionError as e:
        print(f"Error caught: {e}")
    
    try:
        result = calc.add("5", 3)
    except TypeError as e:
        print(f"Error caught: {e}")
    
    print(f"\nString representation: {str(calc)}")
    print(f"Repr: {repr(calc)}")