class SimpleCalculator:
    def add(self, a, b):
        """加法"""
        return a + b
    
    def subtract(self, a, b):
        """减法"""
        return a - b
    
    def multiply(self, a, b):
        """乘法"""
        return a * b
    
    def divide(self, a, b):
        """除法"""
        if b == 0:
            raise ValueError("除数不能为零")
        return a / b

def run_tests():
    """单元测试"""
    calc = SimpleCalculator()
    test_passed = 0
    total_tests = 5
    
    # 加法测试
    assert calc.add(2, 3) == 5, "加法测试失败"
    test_passed += 1
    
    # 减法测试
    assert calc.subtract(5, 3) == 2, "减法测试失败"
    test_passed += 1
    
    # 乘法测试
    assert calc.multiply(2, 3) == 6, "乘法测试失败"
    test_passed += 1
    
    # 除法测试
    assert calc.divide(6, 3) == 2, "除法测试失败"
    test_passed += 1
    
    # 除零测试
    try:
        calc.divide(1, 0)
        raise AssertionError("除零异常测试失败")
    except ValueError:
        test_passed += 1
    
    print(f"测试完成: 通过 {test_passed}/{total_tests}")
    return test_passed == total_tests

if __name__ == "__main__":
    if run_tests():
        print("所有测试通过")
    else:
        print("测试失败")