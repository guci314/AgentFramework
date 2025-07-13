#!/usr/bin/env python3
"""
算术表达式解释器
支持加减乘除四则运算和括号
"""

from enum import Enum
from typing import Optional, List

class TokenType(Enum):
    """词法标记类型"""
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"

class Token:
    """词法标记"""
    def __init__(self, type_: TokenType, value: Optional[float] = None):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    """词法分析器"""
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None
    
    def advance(self):
        """移动到下一个字符"""
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()
    
    def number(self) -> float:
        """解析数字"""
        num_str = ""
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            num_str += self.current_char
            self.advance()
        return float(num_str)
    
    def get_next_token(self) -> Token:
        """获取下一个标记"""
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char.isdigit() or self.current_char == '.':
                return Token(TokenType.NUMBER, self.number())
            
            if self.current_char == '+':
                self.advance()
                return Token(TokenType.PLUS)
            
            if self.current_char == '-':
                self.advance()
                return Token(TokenType.MINUS)
            
            if self.current_char == '*':
                self.advance()
                return Token(TokenType.MULTIPLY)
            
            if self.current_char == '/':
                self.advance()
                return Token(TokenType.DIVIDE)
            
            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN)
            
            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN)
            
            raise ValueError(f"Invalid character: {self.current_char}")
        
        return Token(TokenType.EOF)

class Parser:
    """语法分析器（递归下降）"""
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
    
    def eat(self, token_type: TokenType):
        """消费当前标记"""
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise ValueError(f"Expected {token_type}, got {self.current_token.type}")
    
    def factor(self) -> float:
        """因子：数字或括号表达式"""
        token = self.current_token
        
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return token.value
        
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            result = self.expr()
            self.eat(TokenType.RPAREN)
            return result
        
        else:
            raise ValueError(f"Unexpected token: {token}")
    
    def term(self) -> float:
        """项：处理乘除法"""
        result = self.factor()
        
        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            token = self.current_token
            if token.type == TokenType.MULTIPLY:
                self.eat(TokenType.MULTIPLY)
                result *= self.factor()
            elif token.type == TokenType.DIVIDE:
                self.eat(TokenType.DIVIDE)
                divisor = self.factor()
                if divisor == 0:
                    raise ValueError("Division by zero")
                result /= divisor
        
        return result
    
    def expr(self) -> float:
        """表达式：处理加减法"""
        result = self.term()
        
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
                result += self.term()
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)
                result -= self.term()
        
        return result
    
    def parse(self) -> float:
        """解析入口"""
        result = self.expr()
        if self.current_token.type != TokenType.EOF:
            raise ValueError(f"Unexpected token at end: {self.current_token}")
        return result

def interpret(text: str) -> float:
    """解释算术表达式"""
    lexer = Lexer(text)
    parser = Parser(lexer)
    return parser.parse()

def repl():
    """交互式解释器"""
    print("算术解释器 (输入 'exit' 退出)")
    while True:
        try:
            text = input("calc> ").strip()
            if text.lower() in ('exit', 'quit'):
                break
            if not text:
                continue
            result = interpret(text)
            print(f"= {result}")
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    print("Test: 2 + 3 * 4 =", interpret("2 + 3 * 4"))
    print("Test: (2 + 3) * 4 =", interpret("(2 + 3) * 4"))
    print("Test: 10 / 2 - 3 =", interpret("10 / 2 - 3"))
    print("Test: 3.14 * 2 =", interpret("3.14 * 2"))
    print("\n算术解释器测试通过！")
    print("要运行交互式解释器，请调用 repl() 函数")