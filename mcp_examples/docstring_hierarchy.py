#!/usr/bin/env python3
"""演示语言模型读取哪个 docstring"""

from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function
import json
from typing import Dict, Any

# 模拟 Agent 类和 execute_sync 方法
class DemoAgent:
    """这是 Agent 类的 docstring - 语言模型看不到这个"""
    
    def execute_sync(self, instruction: str) -> Any:
        """这是 execute_sync 方法的 docstring - 语言模型也看不到这个
        
        这个方法执行自然语言指令并返回结果。
        """
        return f"执行了: {instruction}"


# 创建工具函数
@tool
def my_tool(command: str) -> Dict[str, Any]:
    """这是工具函数的 docstring - 语言模型看到的是这个！
    
    这个工具可以执行各种命令。
    
    Args:
        command: 要执行的命令
        
    Returns:
        执行结果的字典
    """
    # 内部使用 Agent
    agent = DemoAgent()
    result = agent.execute_sync(command)
    return {"result": result}


# 展示语言模型实际看到的内容
print("=== 语言模型看到的工具信息 ===\n")

# 1. 工具名称
print(f"工具名称: {my_tool.name}")

# 2. 工具描述（来自工具函数的 docstring）
print(f"\n工具描述:\n{my_tool.description}")

# 3. 完整的工具定义
print("\n完整的工具定义（JSON格式）:")
tool_definition = convert_to_openai_function(my_tool)
print(json.dumps(tool_definition, indent=2, ensure_ascii=False))

# 4. 对比：Agent 和 execute_sync 的 docstring
print("\n=== 对比：其他 docstring（语言模型看不到）===\n")
print(f"Agent 类的 docstring: {DemoAgent.__doc__}")
print(f"\nexecute_sync 方法的 docstring: {DemoAgent.execute_sync.__doc__}")

# 5. 关键点说明
print("\n=== 关键点 ===\n")
print("1. @tool 装饰器只能装饰函数，不能直接装饰类的方法")
print("2. 语言模型只能看到被 @tool 装饰的函数的 docstring")
print("3. Agent.execute_sync 是在工具函数内部调用的实现细节")
print("4. 对语言模型来说，Agent 是完全透明的，它只知道工具函数的接口")

# 6. 最佳实践
print("\n=== 最佳实践 ===\n")
print("在工具函数的 docstring 中：")
print("- 清晰描述工具的功能（不需要提及内部使用的 Agent）")
print("- 提供参数的详细说明和示例")
print("- 说明返回值的格式")
print("- 让描述对语言模型友好，帮助它理解何时使用这个工具")