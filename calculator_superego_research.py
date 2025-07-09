
import math

def add(x, y):
    '''执行加法运算'''
    return x + y

def subtract(x, y):
    '''执行减法运算'''
    return x - y

def multiply(x, y):
    '''执行乘法运算'''
    return x * y

def divide(x, y):
    '''执行除法运算，处理除数为零的情况'''
    if y == 0:
        raise ValueError("除数不能为零！")
    return x / y

def power(x, y):
    '''执行幂运算'''
    return x ** y

def sqrt(x):
    '''执行开方运算，处理负数情况'''
    if x < 0:
        raise ValueError("不能对负数开方！")
    return math.sqrt(x)

def sin_deg(x):
    '''计算正弦值，输入为度数'''
    return math.sin(math.radians(x))

def cos_deg(x):
    '''计算余弦值，输入为度数'''
    return math.cos(math.radians(x))

def tan_deg(x):
    '''计算正切值，输入为度数，处理90度及其倍数的情况'''
    # 检查角度是否接近90度或270度（或其周期性重复），此时tan无定义
    # 使用余弦值接近0来判断，避免浮点数精度问题
    angle_in_radians = math.radians(x)
    if abs(math.cos(angle_in_radians)) < 1e-9: # 如果余弦值非常接近0
        raise ValueError("正切值在90度、270度等角度无定义！")
    return math.tan(angle_in_radians)

def main():
    '''
    主函数，实现命令行交互式计算器。
    支持加、减、乘、除、幂、开方、三角函数操作，并包含基本的错误处理。
    '''
    print("欢迎使用高级计算器！")
    print("支持的操作：")
    print("  二元运算：加 (+), 减 (-), 乘 (*), 除 (/), 幂 (^) ")
    print("  一元运算：开方 (sqrt), 正弦 (sin), 余弦 (cos), 正切 (tan)")
    print("输入 '退出' 结束程序")

    while True:
        try:
            operation = input("请输入操作 (+, -, *, /, ^, sqrt, sin, cos, tan) 或 '退出': ").strip().lower()

            if operation == '退出':
                print("感谢使用，再见！")
                break

            if operation in ('+', '-', '*', '/', '^'):
                num1_str = input("请输入第一个数字: ").strip()
                num2_str = input("请输入第二个数字: ").strip()
                num1 = float(num1_str)
                num2 = float(num2_str)

                result = None
                if operation == '+':
                    result = add(num1, num2)
                elif operation == '-':
                    result = subtract(num1, num2)
                elif operation == '*':
                    result = multiply(num1, num2)
                elif operation == '/':
                    result = divide(num1, num2)
                elif operation == '^':
                    result = power(num1, num2)
                print(f"结果: {num1} {operation} {num2} = {result}")

            elif operation in ('sqrt', 'sin', 'cos', 'tan'):
                num_str = input("请输入数字: ").strip()
                num = float(num_str)

                result = None
                if operation == 'sqrt':
                    result = sqrt(num)
                elif operation == 'sin':
                    result = sin_deg(num)
                elif operation == 'cos':
                    result = cos_deg(num)
                elif operation == 'tan':
                    result = tan_deg(num)
                print(f"结果: {operation}({num}) = {result}")

            else:
                print("无效的操作符，请重新输入。")
                continue

        except ValueError as ve:
            print(f"输入或计算错误: {ve}")
        except Exception as e:
            print(f"发生未知错误: {e}")

if __name__ == '__main__':
    main()
