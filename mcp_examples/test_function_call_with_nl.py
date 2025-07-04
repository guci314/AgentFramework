#!/usr/bin/env python3
"""测试带有自然语言命令执行的 function call"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

# 导入 Agent
from pythonTask import Agent, llm_deepseek

# 创建全局 Agent 实例
print("初始化 Agent...")
python_agent = Agent(llm=llm_deepseek, stateful=True, max_retries=1, skip_generation=True, skip_evaluation=True)

@tool
def calculate(expression: str) -> Dict[str, Any]:
    """执行数学计算
    
    Args:
        expression: 数学表达式，例如 "123 + 456" 或 "2 ** 10"
        
    Returns:
        包含计算结果的字典
    """
    try:
        result = python_agent.execute_sync(f"计算 {expression}")
        
        if result.success:
            return {
                "success": True,
                "expression": expression,
                "result": str(result.return_value) if result.return_value else result.stdout,
                "code": result.code if result.code else None
            }
        else:
            return {
                "success": False,
                "expression": expression,
                "error": result.stderr or "计算失败"
            }
    except Exception as e:
        return {
            "success": False,
            "expression": expression,
            "error": str(e)
        }

# 初始化模型
llm = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
).bind_tools([calculate])

# 测试
print("\n=== Function Call 测试 ===\n")

test_query = "请帮我计算 123 + 456 * 789"
print(f"用户查询: {test_query}")

messages = [HumanMessage(content=test_query)]
response = llm.invoke(messages)

print(f"\n模型响应: {response.content if response.content else '(调用工具)'}")

if hasattr(response, 'tool_calls') and response.tool_calls:
    messages.append(response)
    
    for tool_call in response.tool_calls:
        print(f"\n工具调用: {tool_call['name']}")
        print(f"参数: {tool_call['args']}")
        
        # 执行工具
        result = calculate.invoke(tool_call['args'])
        print(f"工具结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 添加工具结果到消息
        tool_message = ToolMessage(
            content=json.dumps(result, ensure_ascii=False),
            tool_call_id=tool_call['id']
        )
        messages.append(tool_message)
    
    # 获取最终回答
    print("\n=== 生成最终回答 ===")
    final_response = llm.invoke(messages)
    print(f"最终回答: {final_response.content}")

print("\n测试完成！")