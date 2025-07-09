class Calculator:
    """增强的计算器类
    
    提供基本数学运算功能，支持整数和浮点数运算。
    包含完善的错误处理和类型提示。
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
        
    def divide(self, a: float, b: float) -> float:
        """执行除法运算
        
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
        return a / b
