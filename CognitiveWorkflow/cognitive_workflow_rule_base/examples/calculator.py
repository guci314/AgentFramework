def add(a, b):
    """Addition operation with input validation"""
    try:
        return float(a) + float(b)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid inputs for addition: {a}, {b}") from e

def subtract(a, b):
    """Subtraction operation with input validation"""
    try:
        return float(a) - float(b)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid inputs for subtraction: {a}, {b}") from e

def multiply(a, b):
    """Multiplication operation with input validation"""
    try:
        return float(a) * float(b)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid inputs for multiplication: {a}, {b}") from e

def divide(a, b):
    """Division operation with input validation and zero division check"""
    try:
        if float(b) == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return float(a) / float(b)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid inputs for division: {a}, {b}") from e
