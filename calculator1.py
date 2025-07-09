
class Calculator:
    """一个简单的计算器类
    
    提供基本的加减乘除运算功能，支持整数和浮点数运算。
    
    示例:
        >>> calc = Calculator()
        >>> calc.add(2, 3)
        5
        >>> calc.divide(10, 2)
        5.0
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
            ValueError: 当除数为零时抛出
        """
        if b == 0:
            raise ValueError("除数不能为零")
        result = a / b
        self._last_result = result
        return result
        
    def get_last_result(self) -> float:
        """获取上一次运算的结果
        
        Returns:
            上一次运算的结果，如果没有运算过则返回None
        """
        return self._last_result
