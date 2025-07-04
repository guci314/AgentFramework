#!/usr/bin/env python3
"""检查工具的 schema，了解语言模型如何识别工具功能"""

from langchain_core.tools import tool
from typing import Dict, Any
import json

# 定义一个示例工具
@tool
def get_weather(city: str) -> Dict[str, Any]:
    """查询指定城市的天气信息
    
    Args:
        city: 要查询天气的城市名称
        
    Returns:
        包含天气信息的字典
    """
    return {"city": city, "weather": "晴天"}


@tool
def calculate(expression: str) -> Dict[str, Any]:
    """执行数学计算
    
    Args:
        expression: 数学表达式，例如 "123 + 456" 或 "2 ** 10"
        
    Returns:
        包含计算结果的字典
    """
    return {"result": eval(expression)}


# 检查工具的元数据
print("=== 工具的元数据 ===\n")

# 1. 工具名称
print(f"get_weather 工具名称: {get_weather.name}")
print(f"calculate 工具名称: {calculate.name}")

# 2. 工具描述
print(f"\nget_weather 描述: {get_weather.description}")
print(f"calculate 描述: {calculate.description}")

# 3. 工具的参数 schema
print("\n=== 工具的参数 Schema ===\n")
print("get_weather 参数 schema:")
print(json.dumps(get_weather.args_schema.model_json_schema(), indent=2, ensure_ascii=False))

print("\ncalculate 参数 schema:")
print(json.dumps(calculate.args_schema.model_json_schema(), indent=2, ensure_ascii=False))

# 4. 完整的工具定义（这是发送给语言模型的内容）
print("\n=== 完整的工具定义（OpenAI 格式）===\n")

from langchain_core.utils.function_calling import convert_to_openai_function

print("get_weather 的 OpenAI function 格式:")
print(json.dumps(convert_to_openai_function(get_weather), indent=2, ensure_ascii=False))

print("\ncalculate 的 OpenAI function 格式:")
print(json.dumps(convert_to_openai_function(calculate), indent=2, ensure_ascii=False))

# 5. 演示 bind_tools 如何工作
print("\n=== bind_tools 的工作原理 ===\n")

from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 创建一个模型并绑定工具
llm = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
)

# 绑定工具
llm_with_tools = llm.bind_tools([get_weather, calculate])

# 查看绑定后的效果
print("bind_tools 创建了一个新的 Runnable 对象，它会在调用时自动添加工具信息")

# 实际演示：构建一个请求看看包含了什么
from langchain_core.messages import HumanMessage

# 模拟一个消息
messages = [HumanMessage(content="北京天气如何？")]

# 查看工具定义（这是实际发送给模型的内容）
print("\n实际发送给模型的工具定义:")
tools_info = [convert_to_openai_function(tool) for tool in [get_weather, calculate]]
for tool_info in tools_info:
    print(f"\n工具名称: {tool_info['name']}")
    print(f"描述: {tool_info['description']}")
    print(f"参数定义: {json.dumps(tool_info['parameters'], indent=2, ensure_ascii=False)}")