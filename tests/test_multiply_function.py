
def multiply(a, b):
    """
    This function takes two arguments, a and b, and returns their product.
    """
    return a * b

if __name__ == '__main__':
    # 简单的测试用例
    result = multiply(5, 3)
    print(f"The result of multiply(5, 3) is: {result}")
    assert result == 15, "Test failed: multiply(5, 3) should be 15"

    result_float = multiply(2.5, 4)
    print(f"The result of multiply(2.5, 4) is: {result_float}")
    assert result_float == 10.0, "Test failed: multiply(2.5, 4) should be 10.0"

    print("All tests passed for multiply function.")
