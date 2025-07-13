#!/usr/bin/env python3
"""
使用Agent加载Claude Code知识并创建算术解释器
"""
import os
import sys

# 设置代理服务器
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 添加父目录到Python路径以导入Agent框架
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model

# Claude Code知识库
claude_code_knowledge = """
# Claude Code编程知识库

## 概述
Claude Code是Anthropic的官方CLI工具，用于帮助用户进行软件工程任务。我可以通过Claude Code的方式来帮助你编写代码。

## 核心原则
1. **简洁直接**：代码应该简洁明了，避免过度设计
2. **类型安全**：使用类型注解来提高代码可读性和安全性
3. **错误处理**：妥善处理各种错误情况
4. **文档完善**：每个函数和类都应有清晰的文档字符串
5. **测试驱动**：编写代码时考虑可测试性

## 编写解释器的最佳实践

### 1. 词法分析（Lexing）
将输入字符串分解为标记（tokens）：
```python
import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: Optional[float] = None
    
class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        
    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.text):
            # 跳过空白
            if self.text[self.pos].isspace():
                self.pos += 1
                continue
            # 解析数字
            if self.text[self.pos].isdigit() or self.text[self.pos] == '.':
                tokens.append(self.get_number())
            # 解析运算符
            elif self.text[self.pos] == '+':
                tokens.append(Token(TokenType.PLUS))
                self.pos += 1
            # ... 其他运算符
        tokens.append(Token(TokenType.EOF))
        return tokens
```

### 2. 语法分析（Parsing）
使用递归下降解析器处理运算符优先级：
```python
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def parse(self):
        return self.expr()
        
    def expr(self):
        # 处理加减法（低优先级）
        left = self.term()
        while self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token()
            self.advance()
            right = self.term()
            left = BinaryOp(left, op, right)
        return left
        
    def term(self):
        # 处理乘除法（高优先级）
        left = self.factor()
        while self.current_token().type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.current_token()
            self.advance()
            right = self.factor()
            left = BinaryOp(left, op, right)
        return left
```

### 3. 求值（Evaluation）
遍历抽象语法树并计算结果：
```python
class Evaluator:
    def evaluate(self, node):
        if isinstance(node, Number):
            return node.value
        elif isinstance(node, BinaryOp):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            
            if node.op.type == TokenType.PLUS:
                return left + right
            elif node.op.type == TokenType.MINUS:
                return left - right
            elif node.op.type == TokenType.MULTIPLY:
                return left * right
            elif node.op.type == TokenType.DIVIDE:
                if right == 0:
                    raise ValueError("除数不能为零")
                return left / right
```

### 4. 完整的解释器结构
```python
class ArithmeticInterpreter:
    def __init__(self):
        self.lexer = None
        self.parser = None
        self.evaluator = Evaluator()
        
    def interpret(self, text: str) -> float:
        # 词法分析
        self.lexer = Lexer(text)
        tokens = self.lexer.tokenize()
        
        # 语法分析
        self.parser = Parser(tokens)
        ast = self.parser.parse()
        
        # 求值
        result = self.evaluator.evaluate(ast)
        return result
```

## 实现要点
1. **分离关注点**：词法分析、语法分析和求值应该分开
2. **错误处理**：每个阶段都应有适当的错误处理
3. **支持括号**：正确处理括号内的表达式优先级
4. **浮点数支持**：支持小数运算
5. **清晰的错误消息**：提供有意义的错误信息

## 测试用例
```python
def test_interpreter():
    interpreter = ArithmeticInterpreter()
    
    # 基本运算
    assert interpreter.interpret("2 + 3") == 5
    assert interpreter.interpret("10 - 4") == 6
    assert interpreter.interpret("3 * 4") == 12
    assert interpreter.interpret("15 / 3") == 5
    
    # 优先级
    assert interpreter.interpret("2 + 3 * 4") == 14
    assert interpreter.interpret("(2 + 3) * 4") == 20
    
    # 复杂表达式
    assert interpreter.interpret("2.5 + 3.5 * 2") == 9.5
    assert interpreter.interpret("(10 - 5) * (3 + 2)") == 25
```
"""

# 创建标准Agent
llm = get_model('deepseek_chat')
agent = Agent(llm=llm, stateful=True)

# 注入Claude Code知识
agent.loadKnowledge(claude_code_knowledge)

# 设置Agent的API规范
agent.set_api_specification("""
我是一个具备Claude Code风格编程知识的智能体。我将帮助你创建一个简单的算术解释器。
我会遵循以下原则：
1. 代码简洁清晰
2. 使用类型注解
3. 完善的错误处理
4. 详细的文档字符串
5. 模块化设计
""")

if __name__ == "__main__":
    print("=== Claude Code风格算术解释器创建演示 ===\n")
    
    # 让Agent创建解释器
    result = None
    for chunk in agent.execute_stream("""
    请创建一个完整的算术解释器，保存到arithmetic_interpreter.py文件中。
    要求：
    1. 支持加减乘除四则运算
    2. 支持括号
    3. 支持浮点数
    4. 有完善的错误处理
    5. 包含词法分析器、语法分析器和求值器
    6. 提供一个简单的REPL交互界面（但不要在创建时运行它）
    7. 包含完整的类型注解和文档字符串
    
    重要：只创建文件，不要运行REPL。文件末尾应该是：
    if __name__ == "__main__":
        # 可以运行 repl()，但现在不要执行
        pass
    """):
        print(chunk, end="", flush=True)
        result = chunk
    
    print("\n\n=== 创建测试文件 ===\n")
    
    # 创建测试文件
    for chunk in agent.execute_stream("""
    现在创建一个测试文件test_arithmetic_interpreter.py，测试刚才创建的解释器。
    测试应该包括：
    1. 基本四则运算测试
    2. 运算优先级测试
    3. 括号处理测试
    4. 浮点数运算测试
    5. 错误处理测试（如除零、语法错误等）
    6. 复杂表达式测试
    
    使用unittest框架编写测试。
    """):
        print(chunk, end="", flush=True)
    
    print("\n\n=== 任务完成 ===")
    print("已创建：")
    print("1. arithmetic_interpreter.py - 算术解释器主程序")
    print("2. test_arithmetic_interpreter.py - 单元测试文件")
    print("\n你可以运行以下命令来使用解释器：")
    print("python arithmetic_interpreter.py")
    print("\n或运行测试：")
    print("python -m unittest test_arithmetic_interpreter.py")