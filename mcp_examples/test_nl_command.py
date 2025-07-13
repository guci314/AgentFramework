#!/usr/bin/env python3
"""测试自然语言命令执行功能"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent, get_model("deepseek_chat")

# 创建Agent实例
print("创建Agent实例...")
agent = Agent(llm=get_model("deepseek_chat"), stateful=True, max_retries=3, skip_generation=True)

# 测试命令
test_commands = [
    "计算 123 + 456",
    "生成一个包含5个随机数的列表",
    "计算斐波那契数列的前10项"
]

print("\n开始测试自然语言命令执行...\n")

for i, command in enumerate(test_commands, 1):
    print(f"--- 测试 {i} ---")
    print(f"命令: {command}")
    
    try:
        result = agent.execute_sync(command)
        print(f"成功: {result.success}")
        if result.code:
            print(f"执行的代码:\n{result.code}")
        if result.stdout:
            print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
        if result.return_value is not None:
            print(f"返回值: {result.return_value}")
    except Exception as e:
        print(f"执行失败: {str(e)}")
    
    print("\n" + "="*50 + "\n")

print("测试完成！")