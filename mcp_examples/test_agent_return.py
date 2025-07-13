#!/usr/bin/env python3
"""测试 Agent 的返回值结构"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent, get_model("deepseek_chat")

# 创建 Agent 实例
agent = Agent(llm=get_model("deepseek_chat"), stateful=True, max_retries=1, skip_generation=True, skip_evaluation=True)

# 测试不同类型的命令
test_commands = [
    "计算 123 + 456",
    "生成一个包含5个随机数的列表",
    "print('Hello World')"
]

print("=== 测试 Agent 返回值 ===\n")

for command in test_commands:
    print(f"命令: {command}")
    result = agent.execute_sync(command)
    
    print(f"成功: {result.success}")
    print(f"代码: {repr(result.code)}")
    print(f"stdout: {repr(result.stdout)}")
    print(f"stderr: {repr(result.stderr)}")
    print(f"return_value: {repr(result.return_value)}")
    print(f"return_value 类型: {type(result.return_value)}")
    print("-" * 50 + "\n")