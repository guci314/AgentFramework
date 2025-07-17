
def subtract(a, b):
    '''
    实现两个数的减法运算。
    参数:
        a: 第一个数
        b: 第二个数
    返回:
        a - b 的结果
    '''
    return a - b

if __name__ == '__main__':
    # 简单的测试用例
    result1 = subtract(10, 5)
    print(f"10 - 5 = {result1}")
    assert result1 == 5, "测试失败: 10 - 5 应该等于 5"

    result2 = subtract(5, 10)
    print(f"5 - 10 = {result2}")
    assert result2 == -5, "测试失败: 5 - 10 应该等于 -5"

    result3 = subtract(0, 0)
    print(f"0 - 0 = {result3}")
    assert result3 == 0, "测试失败: 0 - 0 应该等于 0"

    print("所有测试通过！")
