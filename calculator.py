
def add(a, b):
    '''加法运算'''
    return a + b

def subtract(a, b):
    '''减法运算'''
    return a - b

def multiply(a, b):
    '''乘法运算'''
    return a * b

def divide(a, b):
    '''除法运算，包含除零错误处理'''
    try:
        return a / b
    except ZeroDivisionError:
        print("错误：除数不能为零")
        return None

if __name__ == "__main__":
    '''简单的测试用例'''
    print("加法测试: 5 + 3 =", add(5, 3))
    print("减法测试: 10 - 4 =", subtract(10, 4))
    print("乘法测试: 6 * 7 =", multiply(6, 7))
    print("除法测试: 8 / 2 =", divide(8, 2))
    print("除零测试: 5 / 0 =", divide(5, 0))
