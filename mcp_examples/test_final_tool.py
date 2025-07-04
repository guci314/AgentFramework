#!/usr/bin/env python3
"""测试最终的工具函数"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from pythonTask import Agent, llm_deepseek

# 创建 Agent
agent = Agent(llm=llm_deepseek, stateful=True, max_retries=1, skip_evaluation=True)

@tool
def calculate(expression: str) -> str:
    """计算数学表达式
    
    Args:
        expression: 数学表达式
        
    Returns:
        计算结果
    """
    try:
        result = agent.execute_sync(f"计算 {expression}")
        if result.return_value is not None:
            return str(result.return_value)
        elif result.stdout:
            return result.stdout.strip()
        else:
            return "无结果"
    except Exception as e:
        return f"错误: {str(e)}"

# 测试
print("=== 测试工具函数 ===\n")

# 直接测试工具
print("1. 直接调用工具:")
result = calculate.invoke({"expression": "123 + 456"})
print(f"结果: {result}\n")

# 通过 LLM 测试
print("2. 通过 LLM 调用:")
llm = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
).bind_tools([calculate])

messages = [HumanMessage(content="帮我计算 123 + 456")]
response = llm.invoke(messages)

if hasattr(response, 'tool_calls') and response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"工具调用: {tool_call['name']}")
        print(f"参数: {tool_call['args']}")
        
        result = calculate.invoke(tool_call['args'])
        print(f"结果: {result}")