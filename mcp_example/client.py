#!/usr/bin/env python3
"""
MCP 客户端示例
连接到MCP服务器并调用计算工具
"""

import asyncio
import sys
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class CalculatorClient:
    """计算器MCP客户端"""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["server.py"]
        )
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用指定的工具"""
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # 初始化会话
                    await session.initialize()
                    
                    # 调用工具
                    result = await session.call_tool(tool_name, arguments)
                    
                    # 提取文本内容
                    if result.content:
                        return result.content[0].text if result.content[0].text else "无结果"
                    else:
                        return "无结果返回"
        
        except Exception as e:
            return f"调用失败: {str(e)}"
    
    async def list_tools(self) -> list:
        """获取可用工具列表"""
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return tools.tools if tools else []
        except Exception as e:
            print(f"获取工具列表失败: {e}")
            return []
    
    async def demo(self):
        """演示各种计算操作"""
        print("🧮 MCP 计算器客户端演示")
        print("=" * 40)
        
        # 获取工具列表
        print("📋 获取可用工具...")
        tools = await self.list_tools()
        if tools:
            print("可用工具:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
        else:
            print("  无可用工具")
        print()
        
        # 测试加法
        print("➕ 测试加法: 5 + 3")
        result = await self.call_tool("add", {"a": 5, "b": 3})
        print(f"  结果: {result}")
        print()
        
        # 测试减法  
        print("➖ 测试减法: 10 - 4")
        result = await self.call_tool("subtract", {"a": 10, "b": 4})
        print(f"  结果: {result}")
        print()
        
        # 测试乘法
        print("✖️ 测试乘法: 6 × 7")
        result = await self.call_tool("multiply", {"a": 6, "b": 7})
        print(f"  结果: {result}")
        print()
        
        # 测试小数
        print("🔢 测试小数: 3.14 + 2.86")
        result = await self.call_tool("add", {"a": 3.14, "b": 2.86})
        print(f"  结果: {result}")
        print()
        
        # 测试错误处理
        print("❌ 测试错误处理: 调用不存在的工具")
        result = await self.call_tool("divide", {"a": 10, "b": 2})
        print(f"  结果: {result}")
        print()
        
        # 交互式计算
        print("🎯 交互式计算 (输入 'quit' 退出)")
        while True:
            try:
                operation = input("请选择操作 (add/subtract/multiply): ").strip()
                if operation.lower() == 'quit':
                    break
                
                if operation not in ['add', 'subtract', 'multiply']:
                    print("无效操作，请选择: add, subtract, multiply")
                    continue
                
                a = float(input("请输入第一个数字: "))
                b = float(input("请输入第二个数字: "))
                
                result = await self.call_tool(operation, {"a": a, "b": b})
                print(f"✅ {result}")
                print()
                
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


async def main():
    """主函数"""
    client = CalculatorClient()
    await client.demo()


if __name__ == "__main__":
    asyncio.run(main())