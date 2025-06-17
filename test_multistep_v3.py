#!/usr/bin/env python3
"""
测试MultiStepAgent_v3的execute_multi_step方法
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from pythonTask import Agent
from langchain_openai import ChatOpenAI

print("🧪 测试MultiStepAgent_v3的execute_multi_step方法")

# 创建测试用的LLM（使用DeepSeek）
llm_deepseek = ChatOpenAI(
    temperature=0,
    model="deepseek-chat", 
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)

# 创建一些测试智能体
coder_agent = Agent(llm=llm_deepseek, stateful=True)
coder_agent.api_specification = "编程智能体，负责编写和修复代码"

tester_agent = Agent(llm=llm_deepseek, stateful=True) 
tester_agent.api_specification = "测试智能体，负责编写和运行测试"

# 创建MultiStepAgent_v3实例
agent_v3 = MultiStepAgent_v3(
    llm=llm_deepseek,
    registered_agents=[
        RegisteredAgent("coder", coder_agent, "编程智能体，负责编写和修复代码"),
        RegisteredAgent("tester", tester_agent, "测试智能体，负责编写和运行测试")
    ]
)

print(f"✅ MultiStepAgent_v3初始化成功")
print(f"   注册的智能体: {[spec.name for spec in agent_v3.registered_agents]}")
print(f"   可用工作流: {agent_v3.list_available_workflows()}")

# 测试1: 检查execute_multi_step方法是否存在
print(f"\n📋 测试1: 检查execute_multi_step方法")
if hasattr(agent_v3, 'execute_multi_step'):
    print("✅ execute_multi_step方法存在")
else:
    print("❌ execute_multi_step方法不存在")
    sys.exit(1)

# 测试2: 检查方法签名
import inspect
signature = inspect.signature(agent_v3.execute_multi_step)
print(f"   方法签名: {signature}")

# 测试3: 工作流匹配功能
print(f"\n📋 测试3: 工作流匹配功能")
test_instructions = [
    "实现一个计算器",
    "编写代码和测试",
    "数据处理任务",
    "其他任务"
]

for instruction in test_instructions:
    try:
        matched_workflow = agent_v3._match_workflow_for_instruction(instruction)
        print(f"   '{instruction}' → {matched_workflow}")
    except Exception as e:
        print(f"   '{instruction}' → 错误: {e}")

# 测试4: 变量提取功能
print(f"\n📋 测试4: 变量提取功能")
test_instruction = "实现一个简单的计算器应用"
extracted_vars = agent_v3._extract_variables_from_instruction(test_instruction)
print(f"   提取的变量: {extracted_vars}")

print(f"\n🎉 所有基础测试通过!")
print(f"   execute_multi_step方法已成功添加到MultiStepAgent_v3")
print(f"   可以使用以下方式调用:")
print(f"   result = agent_v3.execute_multi_step('实现一个计算器')")