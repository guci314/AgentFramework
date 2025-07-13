#!/usr/bin/env python3
"""
使用Agent加载Claude Code SDK知识
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

# Claude Code SDK知识库
claude_code_sdk_knowledge = """
# Claude Code Python SDK 知识库

## 概述
Claude Code SDK 是 Anthropic 官方提供的 Python SDK，用于程序化地与 Claude Code 交互。它允许开发者将 AI 编码助手功能直接集成到 Python 应用中。

## 安装和先决条件

### 1. 安装 Claude Code SDK
```bash
pip install claude-code-sdk
```

### 2. 先决条件
- Python 3.10 或更高版本
- Node.js（用于运行 Claude Code CLI）
- Claude Code CLI：
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```

## 基本用法

### 1. 简单查询示例
```python
import anyio
from claude_code_sdk import query, ClaudeCodeOptions, Message

async def main():
    messages: list[Message] = []
    
    # 发送查询并异步接收消息
    async for message in query(
        prompt="Write a haiku about foo.py",
        options=ClaudeCodeOptions(max_turns=3)
    ):
        messages.append(message)
    
    # 打印所有消息
    for msg in messages:
        print(f"{msg.role}: {msg.content}")

# 运行异步函数
anyio.run(main)
```

### 2. 高级配置选项
```python
from pathlib import Path
from claude_code_sdk import ClaudeCodeOptions

# 创建高级配置选项
options = ClaudeCodeOptions(
    # 最大对话轮数
    max_turns=3,
    
    # 自定义系统提示
    system_prompt="You are a helpful assistant",
    
    # 设置工作目录
    cwd=Path("/path/to/project"),
    
    # 允许使用的工具
    allowed_tools=["Read", "Write", "Bash"],
    
    # 权限模式：acceptEdits 自动接受编辑
    permission_mode="acceptEdits"
)
```

## SDK 核心概念

### 1. Message 对象
```python
from claude_code_sdk import Message

# Message 对象包含以下属性
# - role: 消息角色（"user", "assistant", "system"）
# - content: 消息内容
# - timestamp: 时间戳
# - tool_calls: 工具调用信息（如果有）
```

### 2. 异步编程模式
```python
import anyio
from claude_code_sdk import query

async def process_code_task(task_description: str):
    \"\"\"处理编码任务的异步函数\"\"\"
    messages = []
    
    async for message in query(
        prompt=task_description,
        options=ClaudeCodeOptions(
            max_turns=5,
            allowed_tools=["Read", "Write", "Edit", "Bash"]
        )
    ):
        messages.append(message)
        
        # 实时处理消息
        if message.role == "assistant":
            print(f"Claude: {message.content[:100]}...")
    
    return messages
```

### 3. 工具权限控制
```python
# 可用的工具列表
AVAILABLE_TOOLS = [
    "Read",        # 读取文件
    "Write",       # 写入文件
    "Edit",        # 编辑文件
    "Bash",        # 执行 shell 命令
    "List",        # 列出文件
    "Search",      # 搜索内容
    "Move",        # 移动文件
    "Delete",      # 删除文件
]

# 只允许读写操作（安全模式）
safe_options = ClaudeCodeOptions(
    allowed_tools=["Read", "Write"],
    permission_mode="ask"  # 每次操作都询问
)

# 允许所有操作（开发模式）
dev_options = ClaudeCodeOptions(
    allowed_tools=AVAILABLE_TOOLS,
    permission_mode="acceptEdits"  # 自动接受
)
```

## 实际应用示例

### 1. 代码审查助手
```python
async def code_review(file_path: str):
    """使用 Claude Code 进行代码审查"""
    prompt = f\"\"\"Please review the code in {file_path} and provide:
    1. Code quality assessment
    2. Potential bugs or issues
    3. Performance optimization suggestions
    4. Best practices violations\"\"\"
    
    review_messages = []
    async for message in query(
        prompt=prompt,
        options=ClaudeCodeOptions(
            max_turns=3,
            allowed_tools=["Read"],
            cwd=Path(".").absolute()
        )
    ):
        review_messages.append(message)
    
    return review_messages
```

### 2. 自动化重构工具
```python
async def refactor_code(file_pattern: str, refactor_type: str):
    \"\"\"自动化代码重构\"\"\"
    prompt = f\"\"\"
    Find all files matching pattern '{file_pattern}' and apply the following refactoring:
    {refactor_type}
    
    Make sure to:
    - Preserve functionality
    - Improve code readability
    - Follow PEP 8 conventions
    \"\"\"
    
    options = ClaudeCodeOptions(
        max_turns=10,
        allowed_tools=["Read", "Write", "Edit", "List", "Search"],
        permission_mode="ask",
        system_prompt="You are an expert Python refactoring assistant"
    )
    
    messages = []
    async for message in query(prompt=prompt, options=options):
        messages.append(message)
        
    return messages
```

### 3. 测试生成器
```python
async def generate_tests(source_file: str):
    \"\"\"为源代码文件生成单元测试\"\"\"
    prompt = f\"\"\"
    Generate comprehensive unit tests for {source_file}.
    Include:
    - Edge cases
    - Error handling tests
    - Mock objects where needed
    - Parametrized tests for multiple inputs
    Use pytest framework.
    \"\"\"
    
    options = ClaudeCodeOptions(
        max_turns=5,
        allowed_tools=["Read", "Write"],
        cwd=Path(".").absolute()
    )
    
    async for message in query(prompt=prompt, options=options):
        if message.role == "assistant" and "test_" in message.content:
            print("Generated test:", message.content[:200])
```

### 4. 文档生成器
```python
async def generate_docs(module_path: str):
    \"\"\"生成模块文档\"\"\"
    prompt = f\"\"\"
    Generate comprehensive documentation for the module at {module_path}.
    Include:
    - Module overview
    - Class and function documentation
    - Usage examples
    - API reference
    Format as Markdown.
    \"\"\"
    
    docs = await query(
        prompt=prompt,
        options=ClaudeCodeOptions(
            max_turns=3,
            allowed_tools=["Read", "Write"],
            system_prompt="You are a technical documentation expert"
        )
    )
    
    return docs
```

## 错误处理和最佳实践

### 1. 错误处理
```python
from claude_code_sdk import ClaudeCodeError

async def safe_query(prompt: str):
    try:
        messages = []
        async for message in query(prompt=prompt):
            messages.append(message)
        return messages
    except ClaudeCodeError as e:
        print(f"Claude Code error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### 2. 会话管理
```python
class ClaudeCodeSession:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.messages = []
        self.options = ClaudeCodeOptions(
            cwd=project_path,
            max_turns=10,
            allowed_tools=["Read", "Write", "Edit", "Bash"]
        )
    
    async def send_prompt(self, prompt: str):
        \"\"\"发送提示并收集响应\"\"\"
        async for message in query(prompt=prompt, options=self.options):
            self.messages.append(message)
            yield message
    
    def get_history(self):
        \"\"\"获取会话历史\"\"\"
        return self.messages
```

### 3. 流式处理
```python
async def stream_processing():
    \"\"\"实时处理 Claude Code 输出\"\"\"
    async for message in query(
        prompt="Create a Flask API with user authentication",
        options=ClaudeCodeOptions(max_turns=10)
    ):
        # 实时处理每条消息
        if message.role == "assistant":
            # 检查是否包含代码
            if "```python" in message.content:
                print("Generating Python code...")
            elif message.tool_calls:
                print(f"Using tool: {message.tool_calls}")
        
        # 可以在这里添加自定义逻辑
        # 例如：保存到数据库、发送通知等
```

## 集成示例

### 1. 与 FastAPI 集成
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anyio

app = FastAPI()

class CodeRequest(BaseModel):
    prompt: str
    max_turns: int = 3

@app.post("/generate-code")
async def generate_code(request: CodeRequest):
    try:
        messages = []
        async for message in query(
            prompt=request.prompt,
            options=ClaudeCodeOptions(max_turns=request.max_turns)
        ):
            messages.append({
                "role": message.role,
                "content": message.content
            })
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 与 Jupyter 集成
```python
# 在 Jupyter notebook 中使用
import nest_asyncio
nest_asyncio.apply()

async def claude_code_cell(prompt: str):
    \"\"\"在 Jupyter 中使用 Claude Code\"\"\"
    messages = []
    async for message in query(prompt=prompt):
        messages.append(message)
        if message.role == "assistant":
            display(Markdown(message.content))
    return messages

# 使用示例
await claude_code_cell("Create a data visualization function using matplotlib")
```

## 性能优化建议

1. **批处理请求**：将相关任务组合在一起，减少往返次数
2. **缓存响应**：对于重复的查询，考虑缓存结果
3. **异步并发**：利用异步特性并发处理多个任务
4. **工具限制**：只启用必要的工具，减少不必要的权限检查

## 注意事项

- SDK 需要 Claude Code CLI 在后台运行
- 确保有足够的 API 配额
- 大型项目建议设置合适的 `cwd` 以限制访问范围
- 生产环境建议使用 `permission_mode="ask"` 提高安全性
- 注意处理长时间运行的任务，可能需要设置超时
"""

# 创建标准Agent
llm = get_model('deepseek_chat')
agent = Agent(llm=llm, stateful=True)

# 注入Claude Code SDK知识
agent.loadKnowledge(claude_code_sdk_knowledge)

# 设置Agent的API规范
agent.set_api_specification("""
我是一个精通 Claude Code Python SDK 的智能体。我了解：
1. Claude Code SDK 的安装和配置
2. 异步编程模式和 API 使用
3. 各种工具权限和配置选项
4. 实际应用场景和最佳实践
5. 错误处理和性能优化

我可以帮助你：
- 编写使用 Claude Code SDK 的 Python 代码
- 解决 SDK 使用中的问题
- 设计基于 Claude Code 的自动化工具
- 优化 Claude Code 集成方案
""")

if __name__ == "__main__":
    print("=== Claude Code SDK 演示 ===\n")
    
    # 示例1：创建一个使用 Claude Code SDK 的简单脚本
    result = agent.execute_sync("""
    创建一个名为 claude_sdk_example.py 的文件，演示如何使用 Claude Code SDK。
    包含：
    1. 基本的查询示例
    2. 配置选项的使用
    3. 错误处理
    4. 一个实际的用例（比如代码格式化工具）
    
    确保代码有完整的注释和类型提示。
    """)
    
    if result.success:
        print("\n✅ SDK 示例创建成功！")
        print("\n" + "="*50 + "\n")
    
    # 示例2：解答 SDK 使用问题
    print("=== SDK 使用问题解答 ===\n")
    
    answer = agent.chat_sync("""
    如何使用 Claude Code SDK 创建一个自动化的代码审查工具？
    需要考虑哪些配置选项？如何处理大型项目？
    """)
    
    print("回答：")
    print(answer.return_value)
    
    print("\n\n=== 演示完成 ===")
    print("Agent 已经加载了完整的 Claude Code SDK 知识。")
    print("你可以继续提问关于 SDK 的任何问题。")