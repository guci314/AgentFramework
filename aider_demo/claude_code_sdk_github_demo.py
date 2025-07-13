#!/usr/bin/env python3
"""
从GitHub仓库提取Claude Code SDK知识并注入Agent
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

# 从GitHub仓库提取的完整Claude Code SDK知识库
claude_code_sdk_github_knowledge = """
# Claude Code SDK Python 完整知识库
# 来源：https://github.com/anthropics/claude-code-sdk-python

## 概述
Claude Code SDK for Python 是一个用于与 Claude Code 交互的 Python 库。它提供了异步查询、流式响应、工具使用和文件操作等功能。

## 系统要求
- Python 3.10+
- Node.js
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

## 安装
```bash
pip install claude-code-sdk
```

## 核心功能

### 1. 基本查询
```python
import anyio
from claude_code_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        # 重要：正确处理不同类型的消息
        if hasattr(message, 'content'):
            print(message.content)
        else:
            print(message)

anyio.run(main)
```

### 2. 配置选项
```python
from claude_code_sdk import ClaudeCodeOptions

options = ClaudeCodeOptions(
    system_prompt="You are a helpful coding assistant",
    max_turns=5,
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits',
    cwd="/path/to/project"
)
```

### 3. 工具使用示例
```python
async def create_file_example():
    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode='acceptEdits'
    )
    
    async for message in query(
        prompt="Create a hello.py file with a greeting function",
        options=options
    ):
        print(f"Message type: {type(message)}")
        # 重要：正确处理不同类型的消息
        if hasattr(message, 'content'):
            print(f"Content: {message.content}")
        else:
            print(f"Content: {message}")
```

## 核心组件

### 1. 查询函数
- `query()`: 主要的异步查询函数
- 支持流式响应
- 返回异步迭代器

### 2. 消息类型
- `AssistantMessage`: Claude的响应消息
- `UserMessage`: 用户输入消息
- `SystemMessage`: 系统指令消息

### 3. 内容块类型
- `TextBlock`: 文本内容块，有content属性
- `ToolUseBlock`: 工具使用块，有content属性
- `ToolResultBlock`: 工具结果块
- `SystemMessage`: 系统消息，通常没有content属性

**重要提醒：必须使用 hasattr(message, 'content') 检查消息类型**

### 4. 配置选项
- `system_prompt`: 自定义系统指令
- `max_turns`: 限制对话轮数
- `allowed_tools`: 指定允许的工具
- `permission_mode`: 控制文件编辑行为
- `cwd`: 设置工作目录

## 可用工具

### 1. 文件操作工具
- `Read`: 读取文件内容
- `Write`: 写入文件内容
- `Edit`: 编辑文件
- `List`: 列出文件和目录

### 2. 系统工具
- `Bash`: 执行shell命令
- `Search`: 搜索文件内容

### 3. 权限模式
- `acceptEdits`: 自动接受所有编辑
- `ask`: 每次编辑前询问
- `reject`: 拒绝所有编辑

## 错误处理

### 1. 异常类型
- `CLINotFoundError`: Claude Code CLI 未找到
- `ProcessError`: 进程执行错误
- `TimeoutError`: 请求超时

### 2. 错误处理示例
```python
from claude_code_sdk import query, CLINotFoundError, ProcessError

async def safe_query():
    try:
        async for message in query(prompt="Hello"):
            print(message)
    except CLINotFoundError:
        print("Claude Code CLI not found. Please install it first.")
    except ProcessError as e:
        print(f"Process error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## 实际应用示例

### 1. 代码生成器
```python
async def generate_code(description: str, filename: str):
    options = ClaudeCodeOptions(
        allowed_tools=["Write"],
        permission_mode='acceptEdits'
    )
    
    prompt = f"Generate a Python file '{filename}' that {description}"
    
    async for message in query(prompt=prompt, options=options):
        if hasattr(message, 'content'):
            print(f"Generated: {message.content}")
```

### 2. 代码审查工具
```python
async def review_code(file_path: str):
    options = ClaudeCodeOptions(
        allowed_tools=["Read"],
        max_turns=3
    )
    
    prompt = f"Please review the code in {file_path} and provide feedback"
    
    async for message in query(prompt=prompt, options=options):
        print(f"Review: {message}")
```

### 3. 自动化重构
```python
async def refactor_code(file_pattern: str):
    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write", "Edit"],
        permission_mode='ask'
    )
    
    prompt = f"Refactor all Python files matching {file_pattern} to follow PEP 8"
    
    async for message in query(prompt=prompt, options=options):
        print(f"Refactoring: {message}")
```

### 4. 测试生成器
```python
async def generate_tests(source_file: str):
    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write"],
        system_prompt="You are a testing expert. Generate comprehensive tests."
    )
    
    prompt = f"Generate unit tests for {source_file} using pytest"
    
    async for message in query(prompt=prompt, options=options):
        print(f"Test generation: {message}")
```

## 最佳实践

### 1. 异步编程
- 始终使用 `async/await` 语法
- 使用 `anyio.run()` 或 `asyncio.run()` 运行异步函数
- 正确处理异步迭代器

### 2. 权限管理
- 生产环境使用 `permission_mode='ask'`
- 开发环境可以使用 `permission_mode='acceptEdits'`
- 限制 `allowed_tools` 以提高安全性

### 3. 错误处理
- 总是包含适当的异常处理
- 处理特定的 SDK 异常类型
- 提供有意义的错误信息

### 4. 性能优化
- 设置合适的 `max_turns` 限制
- 使用适当的 `cwd` 限制文件访问范围
- 批量处理相关任务

## 集成模式

### 1. 与 FastAPI 集成
```python
from fastapi import FastAPI
from claude_code_sdk import query, ClaudeCodeOptions

app = FastAPI()

@app.post("/generate")
async def generate_code(prompt: str):
    results = []
    async for message in query(prompt=prompt):
        results.append(str(message))
    return {"results": results}
```

### 2. 与 Jupyter 集成
```python
import nest_asyncio
nest_asyncio.apply()

async def jupyter_query(prompt: str):
    async for message in query(prompt=prompt):
        display(message)
```

### 3. 命令行工具
```python
import click
import anyio

@click.command()
@click.argument('prompt')
def cli_query(prompt):
    async def run():
        async for message in query(prompt=prompt):
            click.echo(message)
    
    anyio.run(run)
```

## 高级用法

### 1. 流式处理
```python
async def stream_processing(prompt: str):
    buffer = []
    async for message in query(prompt=prompt):
        buffer.append(message)
        if len(buffer) >= 10:  # 批量处理
            process_batch(buffer)
            buffer = []
    
    if buffer:  # 处理剩余消息
        process_batch(buffer)
```

### 2. 会话管理
```python
class CodeSession:
    def __init__(self, cwd: str):
        self.options = ClaudeCodeOptions(
            cwd=cwd,
            allowed_tools=["Read", "Write", "Edit", "Bash"],
            permission_mode='ask'
        )
        self.history = []
    
    async def send(self, prompt: str):
        messages = []
        async for message in query(prompt=prompt, options=self.options):
            messages.append(message)
            self.history.append(message)
        return messages
```

### 3. 工具链组合
```python
async def code_workflow(requirements: str):
    # 1. 生成代码
    options = ClaudeCodeOptions(allowed_tools=["Write"])
    async for message in query(f"Generate code for: {requirements}", options=options):
        print(f"Generated: {message}")
    
    # 2. 运行测试
    options = ClaudeCodeOptions(allowed_tools=["Bash"])
    async for message in query("Run pytest on the generated code", options=options):
        print(f"Test result: {message}")
    
    # 3. 生成文档
    options = ClaudeCodeOptions(allowed_tools=["Read", "Write"])
    async for message in query("Generate documentation", options=options):
        print(f"Documentation: {message}")
```

## 许可证
MIT License - 可自由使用、修改和分发

## 相关资源
- GitHub仓库: https://github.com/anthropics/claude-code-sdk-python
- 官方文档: https://docs.anthropic.com/en/docs/claude-code/sdk
- Claude Code CLI: https://github.com/anthropics/claude-code
"""

def main():
    """主函数：演示Claude Code SDK知识注入"""
    print("=== Claude Code SDK GitHub 知识注入演示 ===\n")
    
    # 创建Agent并注入知识
    llm = get_model('deepseek_chat')
    agent = Agent(llm=llm, stateful=True)
    agent.loadKnowledge(claude_code_sdk_github_knowledge)
    
    # 设置Agent规范
    agent.set_api_specification("""
    我是一个精通Claude Code SDK的专家Assistant。我掌握：
    1. Claude Code SDK的完整API和功能
    2. 异步编程模式和最佳实践
    3. 工具使用和权限管理
    4. 错误处理和性能优化
    5. 各种集成场景和实际应用
    
    我可以帮助你：
    - 设计和实现基于Claude Code SDK的解决方案
    - 解决SDK使用中的问题
    - 提供代码示例和最佳实践建议
    - 优化SDK集成方案
    """)
    
    print("✅ 知识注入完成！\n")
    
    # 测试Agent的知识应用
    print("=== 测试Agent知识应用 ===\n")
    
    test_questions = [
        "使用Claude Code SDK创建一个自动化代码生成工具的Python类",
        "解释Claude Code SDK中的权限模式有哪些选项",
        "如何使用SDK进行错误处理"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"问题{i}: {question}")
        try:
            answer = agent.chat_sync(question)
            if answer.success:
                print(f"回答: {answer.return_value}\n")
                print("-" * 50 + "\n")
            else:
                print(f"回答失败: {answer.return_value}\n")
        except Exception as e:
            print(f"错误: {e}\n")
    
    print("=== 演示完成 ===")
    print("Agent已成功注入Claude Code SDK完整知识！")

if __name__ == "__main__":
    main()