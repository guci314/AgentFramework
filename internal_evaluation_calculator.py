
# internal_evaluation_calculator.py

def add(a, b):
    """
    执行加法运算。
    Args:
        a (float/int): 第一个操作数。
        b (float/int): 第二个操作数。
    Returns:
        float/int: 运算结果。
    """
    return a + b

def subtract(a, b):
    """
    执行减法运算。
    Args:
        a (float/int): 第一个操作数。
        b (float/int): 第二个操作数。
    Returns:
        float/int: 运算结果。
    """
    return a - b

def multiply(a, b):
    """
    执行乘法运算。
    Args:
        a (float/int): 第一个操作数。
        b (float/int): 第二个操作数。
    Returns:
        float/int: 运算结果。
    """
    return a * b

def divide(a, b):
    """
    执行除法运算，并处理除零错误。
    Args:
        a (float/int): 被除数。
        b (float/int): 除数。
    Returns:
        float/int: 运算结果。
    Raises:
        ValueError: 如果除数为零。
    """
    if b == 0:
        raise ValueError("除数不能为零！")
    return a / b

def run_calculator():
    """
    运行命令行计算器用户界面。
    """
    print("欢迎使用命令行计算器！")
    print("支持的操作: +, -, *, /")
    print("输入 'exit' 或 'quit' 退出程序。")
    print("-" * 30)

    while True:
        # 获取用户输入的操作符
        operation = input("请输入操作符 (+, -, *, /) 或 'exit'/'quit' 退出: ").strip().lower()

        # 处理退出指令
        if operation in ('exit', 'quit'):
            print("感谢使用，再见！")
            break

        # 验证操作符是否有效
        if operation not in ('+', '-', '*', '/'):
            print(f"错误: 无效的操作符 '{operation}'。请重新输入。")
            print("-" * 30)
            continue

        # 获取并验证第一个数字
        try:
            num1_str = input("请输入第一个数字: ").strip()
            num1 = float(num1_str)
        except ValueError:
            print(f"错误: 无效的第一个数字 '{num1_str}'。请输入一个有效的数字。")
            print("-" * 30)
            continue

        # 获取并验证第二个数字
        try:
            num2_str = input("请输入第二个数字: ").strip()
            num2 = float(num2_str)
        except ValueError:
            print(f"错误: 无效的第二个数字 '{num2_str}'。请输入一个有效的数字。")
            print("-" * 30)
            continue

        # 执行计算并处理可能发生的错误
        result = None
        try:
            if operation == '+':
                result = add(num1, num2)
            elif operation == '-':
                result = subtract(num1, num2)
            elif operation == '*':
                result = multiply(num1, num2)
            elif operation == '/':
                result = divide(num1, num2)
            
            print(f"计算成功: {num1} {operation} {num2} = {result}")

        except ValueError as e:
            print(f"计算错误: {e}")
        except Exception as e:
            print(f"发生未知错误: {e}")
        
        print("-" * 30) # 分隔线，使输出更清晰

if __name__ == "__main__":
    run_calculator()
