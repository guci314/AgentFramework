#!/usr/bin/env python3
"""
简化版：使用Agent注入Claude Code SDK知识
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

# Claude Code SDK 简化知识库
claude_code_sdk_knowledge = """
# Claude Code Python SDK 知识库

## 安装
pip install claude-code-sdk

## 基本使用
import anyio
from claude_code_sdk import query, ClaudeCodeOptions

async def main():
    messages = []
    async for message in query(
        prompt="编写一个Python函数",
        options=ClaudeCodeOptions(max_turns=3)
    ):
        messages.append(message)
    return messages

## 配置选项
- max_turns: 最大对话轮数
- system_prompt: 系统提示
- cwd: 工作目录 
- allowed_tools: 允许的工具 ["Read", "Write", "Bash"]
- permission_mode: 权限模式 "acceptEdits" 或 "ask"

## 常用工具
- Read: 读取文件
- Write: 写入文件
- Edit: 编辑文件
- Bash: 执行shell命令
- List: 列出文件
- Search: 搜索内容

## 异步编程模式
使用 anyio.run() 或 asyncio.run() 运行异步函数
所有 SDK 操作都是异步的，需要使用 async/await

## 错误处理
使用 try/except 捕获 ClaudeCodeError
"""

# 创建Agent并注入知识
llm = get_model('deepseek_chat')
agent = Agent(llm=llm, stateful=True)
agent.loadKnowledge(claude_code_sdk_knowledge)

if __name__ == "__main__":
    print("=== Claude Code SDK 知识注入演示 ===\n")
    
    # 让Agent创建一个使用SDK的示例
    result = agent.execute_sync("""
    创建一个使用 Claude Code SDK 的 Python 脚本文件 sdk_example.py，包含：
    1. 基本的异步查询示例
    2. 配置选项的使用
    3. 错误处理
    4. 一个实际用例（比如自动生成文档）
    
    确保代码可以直接运行，包含完整的导入语句。
    """)
    
    if result.success:
        print("✅ SDK 示例创建成功！")
        print(f"输出：{result.return_value[:500]}...")
    else:
        print("❌ 创建失败")
        print(f"错误：{result.return_value}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试Agent的SDK知识
    print("=== 测试Agent的SDK知识 ===\n")
    
    question = "如何使用 Claude Code SDK 创建一个自动化代码审查工具？"
    answer = agent.chat_sync(question)
    
    print(f"问题：{question}")
    print(f"回答：{answer.return_value}")
    
    print("\n=== 演示完成 ===")
    print("Agent已具备Claude Code SDK知识，可以回答相关问题。")