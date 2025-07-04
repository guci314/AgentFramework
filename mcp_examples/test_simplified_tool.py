#!/usr/bin/env python3
"""测试简化的工具函数"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pythonTask import Agent, llm_deepseek
from langchain_core.tools import tool

# 创建 Agent
agent = Agent(llm=llm_deepseek, stateful=True, max_retries=1, skip_generation=True, skip_evaluation=True)

@tool
def execute_command(command: str) -> str:
    """执行命令"""
    try:
        result = agent.execute_sync(command)
        
        if result.code and result.stdout:
            return result.stdout.strip()
        
        if result.return_value is not None:
            return str(result.return_value)
        
        if result.stderr:
            return f"错误: {result.stderr}"
        
        return "执行完成"
    except Exception as e:
        return f"执行失败: {str(e)}"

# 测试
test_commands = [
    "计算 123 + 456",
    "计算 123 + 456 * 789",
    "生成一个包含5个随机数的列表",
    "print('Hello World')"
]

print("=== 测试工具函数 ===\n")

for cmd in test_commands:
    print(f"命令: {cmd}")
    result = execute_command.invoke({"command": cmd})
    print(f"结果: {result}")
    print("-" * 50)