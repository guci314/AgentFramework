#!/usr/bin/env python3
"""
简单的MCP计算器测试 - 无交互版本
演示基本功能，适合自动化测试
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def simple_test():
    """简单的计算器测试"""
    print("🧮 MCP 计算器简单测试")
    print("=" * 30)
    
    # 服务器参数
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )
    
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # 测试用例
                tests = [
                    ("add", {"a": 5, "b": 3}),
                    ("subtract", {"a": 10, "b": 4}), 
                    ("multiply", {"a": 6, "b": 7}),
                ]
                
                for tool_name, args in tests:
                    result = await session.call_tool(tool_name, args)
                    if result.content:
                        print(f"✅ {tool_name}: {result.content[0].text}")
                    else:
                        print(f"❌ {tool_name}: 无结果")
                
                print("\n🎉 测试完成!")
                
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(simple_test())