#!/usr/bin/env python3
"""
简化版蓝色打印猴子补丁函数
"""

import functools

def add_blue_print_to_method(method, target_class=None):
    """
    为方法添加猴子补丁，用蓝色字体打印输入参数和返回值
    
    Args:
        method: 方法名(字符串) 或 方法对象
        target_class: 当method是字符串时，指定目标类
    
    Returns:
        恢复原始方法的函数
    """
    
    # 蓝色字体的ANSI代码
    BLUE = '\033[94m'
    BOLD_BLUE = '\033[1;94m'
    RESET = '\033[0m'
    
    if isinstance(method, str):
        # 如果传入方法名字符串
        if target_class is None:
            raise ValueError("传入方法名时，必须提供目标类")
        
        method_name = method
        original_method = getattr(target_class, method_name)
        
        # 保存原始方法
        original_backup = original_method
        
        # 创建增强方法
        @functools.wraps(original_method)
        def enhanced_method(self, *args, **kwargs):
            # 打印输入参数
            args_str = ', '.join([repr(arg) for arg in args])
            kwargs_str = ', '.join([f'{k}={repr(v)}' for k, v in kwargs.items()])
            params_str = ', '.join(filter(None, [args_str, kwargs_str]))
            print(f"{BLUE}🔵 {target_class.__name__}.{method_name} 输入参数: ({params_str}){RESET}")
            
            # 调用原方法
            result = original_method(self, *args, **kwargs)
            
            # 打印返回值
            print(f"{BOLD_BLUE}🔵 {target_class.__name__}.{method_name} 返回值: {result}{RESET}")
            return result
        
        # 应用猴子补丁
        setattr(target_class, method_name, enhanced_method)
        
        # 返回恢复函数
        def restore():
            setattr(target_class, method_name, original_backup)
            print(f"已恢复 {target_class.__name__}.{method_name} 的原始方法")
        
        return restore
        
    elif callable(method):
        # 如果传入的是函数对象
        @functools.wraps(method)
        def enhanced_function(*args, **kwargs):
            # 打印输入参数
            args_str = ', '.join([repr(arg) for arg in args])
            kwargs_str = ', '.join([f'{k}={repr(v)}' for k, v in kwargs.items()])
            params_str = ', '.join(filter(None, [args_str, kwargs_str]))
            print(f"{BLUE}🔵 {method.__name__} 输入参数: ({params_str}){RESET}")
            
            # 调用原函数
            result = method(*args, **kwargs)
            
            # 打印返回值
            print(f"{BOLD_BLUE}🔵 {method.__name__} 返回值: {result}{RESET}")
            return result
        
        return enhanced_function
        
    else:
        raise ValueError("method必须是字符串或可调用对象")

# 使用示例
if __name__ == "__main__":
    print("🔵 蓝色打印猴子补丁使用示例\n")
    
    # 示例1: 为类方法添加猴子补丁
    class Calculator:
        def add(self, a, b):
            return a + b
        
        def multiply(self, a, b):
            return a * b
    
    print("=== 类方法示例 ===")
    calc = Calculator()
    
    # 为add方法添加蓝色打印
    restore_add = add_blue_print_to_method('add', Calculator)
    
    # 测试
    result = calc.add(10, 20)
    print(f"程序中获得的结果: {result}\n")
    
    # 恢复原始方法
    restore_add()
    result = calc.add(5, 15)
    print(f"恢复后的结果: {result}\n")
    
    # 示例2: 为普通函数添加猴子补丁
    print("=== 普通函数示例 ===")
    
    def greet(name):
        return f"Hello, {name}!"
    
    # 创建增强版本
    enhanced_greet = add_blue_print_to_method(greet)
    
    # 对比测试
    print("原始函数:")
    result1 = greet("Alice")
    print(f"程序中获得的结果: {result1}\n")
    
    print("增强后的函数:")
    result2 = enhanced_greet("Bob")
    print(f"程序中获得的结果: {result2}")
