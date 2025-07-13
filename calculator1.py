from typing import Union

class Calculator:
    """增强的计算器类
    
    提供基本数学运算功能，支持整数和浮点数运算。
    包含完善的错误处理和类型提示。
    
    方法:
        add: 加法运算
        subtract: 减法运算 
        multiply: 乘法运算
        divide: 除法运算
    """
    
    def add(self, a: float, b: float) -> float:
        """执行加法运算
        
        Args:
            a: 第一个操作数
            b: 第二个操作数
            
        Returns:
            两数之和
        """
        return a + b
        
    def subtract(self, a: float, b: float) -> float:
        """执行减法运算
        
        Args:
            a: 被减数
            b: 减数
            
        Returns:
            两数之差
        """
        return a - b
        
    def multiply(self, a: float, b: float) -> float:
        """执行乘法运算
        
        Args:
            a: 第一个因数
            b: 第二个因数
            
        Returns:
            两数之积
        """
        return a * b
        
    def divide(self, a: Union[int, float], b: Union[int, float]) -> float:
        """执行除法运算
        
        Args:
            a: 被除数
            b: 除数
            
        Returns:
            两数之商
            
        Raises:
            ValueError: 当除数为零时抛出
            
        Examples:
            >>> calc = Calculator()
            >>> calc.divide(10, 2)
            5.0
            >>> calc.divide(5, 0)
            ValueError: 除数不能为零，尝试进行 5 / 0 运算
        """
        if b == 0:
            raise ValueError(f"除数不能为零，尝试进行 {a} / {b} 运算")
        return a / b
        
    def power(self, a: float, b: float) -> float:
        """计算幂运算
        
        Args:
            a: 底数
            b: 指数
            
        Returns:
            a的b次方
        """
        return a ** b
        
    def sqrt(self, a: float) -> float:
        """计算平方根
        
        Args:
            a: 需要计算平方根的数
            
        Returns:
            a的平方根
            
        Raises:
            ValueError: 当a为负数时抛出
        """
        if a < 0:
            raise ValueError("不能计算负数的平方根")
        return a ** 0.5
