#!/usr/bin/env python3
"""测试 skip_generation=True 时的返回值"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent, get_model("deepseek_chat")

print("=== 测试 skip_generation=True 时的返回值 ===\n")

# 测试1：skip_generation=True, skip_evaluation=True
print("1. skip_generation=True, skip_evaluation=True:")
agent1 = Agent(llm=get_model("deepseek_chat"), stateful=True, max_retries=1, skip_generation=True, skip_evaluation=True)
result1 = agent1.execute_sync("print('Hello World')")
print(f"  - result.success: {result1.success}")
print(f"  - result.code: {repr(result1.code)}")
print(f"  - result.stdout: {repr(result1.stdout)}")
print(f"  - result.return_value: {repr(result1.return_value)}")
print(f"  - type(result.return_value): {type(result1.return_value)}")

# 测试2：skip_generation=True, skip_evaluation=False
print("\n2. skip_generation=True, skip_evaluation=False:")
agent2 = Agent(llm=get_model("deepseek_chat"), stateful=True, max_retries=1, skip_generation=True, skip_evaluation=False)
result2 = agent2.execute_sync("print('Hello World')")
print(f"  - result.success: {result2.success}")
print(f"  - result.code: {repr(result2.code)}")
print(f"  - result.stdout: {repr(result2.stdout)}")
print(f"  - result.return_value: {repr(result2.return_value)}")
print(f"  - type(result.return_value): {type(result2.return_value)}")

# 测试3：skip_generation=False, skip_evaluation=True
print("\n3. skip_generation=False, skip_evaluation=True:")
agent3 = Agent(llm=get_model("deepseek_chat"), stateful=True, max_retries=1, skip_generation=False, skip_evaluation=True)
result3 = agent3.execute_sync("print('Hello World')")
print(f"  - result.success: {result3.success}")
print(f"  - result.code: {repr(result3.code)}")
print(f"  - result.stdout: {repr(result3.stdout)}")
print(f"  - result.return_value: {repr(result3.return_value)}")
print(f"  - type(result.return_value): {type(result3.return_value)}")

print("\n=== 结论 ===")
print("当 skip_generation=True 时：")
print("- 如果 skip_evaluation=True：return_value 是 None（来自 Device.execute_code）")
print("- 如果 skip_evaluation=False：return_value 是 None（来自原始执行结果）")
print("\n当 skip_generation=False 时：")
print("- return_value 是 LLM 生成的自然语言总结")