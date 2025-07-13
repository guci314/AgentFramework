#!/usr/bin/env python3
"""
测试Agent是否具备Claude Code SDK知识
"""
import os
import sys

# 设置代理服务器
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model

# Claude Code SDK 知识库
claude_sdk_knowledge = """
# Claude Code Python SDK 知识库

## 重要原则：Claude Code SDK是代码生成工具
**当用户要求编写、创建或生成Python代码时，应该调用Claude Code SDK来完成，而不是直接生成代码。**

### 判断何时使用Claude Code SDK
- ✅ 用户说："编写Python代码"
- ✅ 用户说："创建一个Python文件"
- ✅ 用户说："生成Python脚本"
- ✅ 用户说："实现某个功能"
- ✅ 用户说："写一个类/函数"
- ❌ 用户明确说："直接返回代码"
- ❌ 用户要求解释代码概念
- ❌ 用户询问语法问题

### 使用Claude Code SDK的标准流程
```python
# 当收到编写Python代码的请求时
if "编写" in 用户指令 or "创建" in 用户指令 or "生成" in 用户指令 or "写一个" in 用户指令:
    # 使用Claude Code SDK而不是直接写代码
    use_claude_code_sdk()
else:
    # 其他情况正常处理
    handle_normally()
```

## 基本用法
import anyio
from claude_code_sdk import query, ClaudeCodeOptions

async def main():
    async for message in query(prompt="任务描述"):
        # 重要：正确处理不同类型的消息
        if hasattr(message, 'content'):
            print(message.content)
        else:
            print(message)

## 配置选项
ClaudeCodeOptions(
    max_turns=3,
    system_prompt="系统提示",
    cwd=Path("工作目录"),
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="acceptEdits"
)

## 主要特性
- 异步编程模式
- 可配置的系统提示
- 工具权限控制
- 灵活的项目上下文设置
- 流式消息处理

## 重要：消息处理
Claude Code SDK 返回不同类型的消息对象：
- SystemMessage: 系统初始化消息，通常没有content属性
- TextBlock: 文本消息，有content属性
- ToolUseBlock: 工具使用消息，有content属性
- ResultMessage: 结果消息

**必须使用 hasattr(message, 'content') 检查消息类型，避免AttributeError错误**

## 实际应用示例

### 正确做法（使用Claude Code SDK）
```python
# 应该这样做
import anyio
from claude_code_sdk import query, ClaudeCodeOptions

async def generate_code():
    options = ClaudeCodeOptions(
        allowed_tools=["Write"],
        permission_mode="acceptEdits"
    )
    
    async for message in query(
        prompt="创建一个Calculator类，包含加减乘除方法",
        options=options
    ):
        # 重要：正确处理不同类型的消息
        if hasattr(message, 'content'):
            print(message.content)
        else:
            print(message)

anyio.run(generate_code)
```

### 错误做法（直接生成代码）
```python
# 不要这样做
def create_calculator():
    code = '''
class Calculator:
    def add(self, a, b):
        return a + b
'''
    with open('calculator.py', 'w') as f:
        f.write(code)
```
"""

def test_claude_sdk_knowledge():
    """测试Agent的Claude Code SDK知识"""
    print("=== 测试Claude Code SDK知识 ===\n")
    
    # 创建Agent并注入知识
    llm = get_model('deepseek_chat')
    agent = Agent(llm=llm, stateful=True)
    agent.loadKnowledge(claude_sdk_knowledge)
    
    # 测试问题：让Agent写一个支持加减乘除的解释器Python类
    question = "写一个支持加减乘除的算术解释器Python类。类名Calculator，文件名calculator3.py。"
    
    print(f"问题: {question}")
    try:
        result=None
        for i in agent.execute_stream(question):
            result=i
            print(i,end="",flush=True)
        print(result)
    except Exception as e:
        print(f"错误: {e}\n")
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_claude_sdk_knowledge()