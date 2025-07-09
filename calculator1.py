
class Calculator:
    """一个增强的计算器类
    
    提供基本数学运算功能，包括：
    - 加减乘除
    - 幂运算
    - 模运算
    支持整数和浮点数运算，并记录最后一次计算结果。
    
    示例:
        >>> calc = Calculator()
        >>> calc.add(2, 3)
        5
        >>> calc.power(2, 3)
        8
        >>> calc.modulo(10, 3)
        1
    """
    
    def __init__(self):
        """初始化计算器"""
        self._last_result = None
        
    def add(self, a: float, b: float) -> float:
        """加法运算
        
        Args:
            a: 第一个操作数
            b: 第二个操作数
            
        Returns:
            两数之和
        """
        result = a + b
        self._last_result = result
        return result
        
    def subtract(self, a: float, b: float) -> float:
        """减法运算
        
        Args:
            a: 被减数
            b: 减数
            
        Returns:
            两数之差
        """
        result = a - b
        self._last_result = result
        return result
        
    def multiply(self, a: float, b: float) -> float:
        """乘法运算
        
        Args:
            a: 第一个因数
            b: 第二个因数
            
        Returns:
            两数之积
        """
        result = a * b
        self._last_result = result
        return result
        
    def divide(self, a: float, b: float) -> float:
        """除法运算
        
        Args:
            a: 被除数
            b: 除数
            
        Returns:
            两数之商
            
        Raises:
            ZeroDivisionError: 当除数为零时抛出
        """
        if b == 0:
            raise ZeroDivisionError("除数不能为零")
        result = a / b
        self._last_result = result
        return result
        
    def power(self, base: float, exponent: float) -> float:
        """幂运算
        
        Args:
            base: 底数
            exponent: 指数
            
        Returns:
            base的exponent次方
        """
        result = base ** exponent
        self._last_result = result
        return result
        
    def modulo(self, a: float, b: float) -> float:
        """模运算
        
        Args:
            a: 被除数
            b: 除数
            
        Returns:
            a除以b的余数
            
        Raises:
            ZeroDivisionError: 当除数为零时抛出
        """
        if b == 0:
            raise ZeroDivisionError("除数不能为零")
        result = a % b
        self._last_result = result
        return result
        
    def get_last_result(self) -> float:
        """获取上一次运算的结果
        
        Returns:
            上一次运算的结果，如果没有运算过则返回None
        """
        return self._last_result
