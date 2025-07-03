def add(a, b):
    """Addition operation with input validation"""
    try:
        return float(a) + float(b)
    except (ValueError, TypeError):
        raise ValueError("Invalid input: both arguments must be numbers")

def subtract(a, b):
    """Subtraction operation with input validation"""
    try:
        return float(a) - float(b)
    except (ValueError, TypeError):
        raise ValueError("Invalid input: both arguments must be numbers")

def multiply(a, b):
    """Multiplication operation with input validation"""
    try:
        return float(a) * float(b)
    except (ValueError, TypeError):
        raise ValueError("Invalid input: both arguments must be numbers")

def divide(a, b):
    """Division operation with input validation and zero division check"""
    try:
        if float(b) == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return float(a) / float(b)
    except (ValueError, TypeError):
        raise ValueError("Invalid input: both arguments must be numbers")
