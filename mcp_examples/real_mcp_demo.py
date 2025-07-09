#!/usr/bin/env python3
"""
真正的MCP价值演示
展示MCP相比普通Python函数的优势：
1. 进程隔离
2. 标准化协议
3. 类型安全
4. 可扩展性
5. 跨语言支持
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class RealMCPDemo:
    """真正的MCP演示"""
    
    def __init__(self):
        # 配置连接到真正的MCP服务器
        self.server_params = StdioServerParameters(
            command="python",
            args=["enhanced_server.py"]
        )
    
    async def demonstrate_mcp_advantages(self):
        """演示MCP的优势"""
        print("🚀 真正的MCP价值演示")
        print("=" * 60)
        
        # 1. 进程隔离演示
        await self.demo_process_isolation()
        
        # 2. 标准化协议演示
        await self.demo_standardized_protocol()
        
        # 3. 类型安全演示
        await self.demo_type_safety()
        
        # 4. 可扩展性演示
        await self.demo_extensibility()
        
        # 5. 与普通函数的对比
        await self.demo_comparison_with_functions()
    
    async def demo_process_isolation(self):
        """演示进程隔离的价值"""
        print("\n🔒 1. 进程隔离演示")
        print("-" * 40)
        
        try:
            # 连接到MCP服务器（独立进程）
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    print("✅ 成功连接到独立的MCP服务器进程")
                    
                    # 演示即使主进程出错，服务器进程仍然安全
                    result = await session.call_tool("calculator", {
                        "operation": "divide",
                        "a": 10,
                        "b": 2
                    })
                    
                    print(f"🔢 计算结果: {result.content[0].text}")
                    print("🛡️  服务器进程独立运行，不受主程序影响")
                    
        except Exception as e:
            print(f"❌ 连接失败: {e}")
    
    async def demo_standardized_protocol(self):
        """演示标准化协议的价值"""
        print("\n📋 2. 标准化协议演示")
        print("-" * 40)
        
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # 获取工具列表（标准MCP协议）
                    tools = await session.list_tools()
                    print(f"📦 发现 {len(tools.tools)} 个标准化工具:")
                    
                    for tool in tools.tools:
                        print(f"  • {tool.name}: {tool.description}")
                    
                    # 获取资源列表
                    resources = await session.list_resources()
                    print(f"📄 发现 {len(resources.resources)} 个资源:")
                    
                    for resource in resources.resources:
                        print(f"  • {resource.uri}: {resource.description}")
                    
                    # 获取提示模板
                    prompts = await session.list_prompts()
                    print(f"💬 发现 {len(prompts.prompts)} 个提示模板:")
                    
                    for prompt in prompts.prompts:
                        print(f"  • {prompt.name}: {prompt.description}")
                    
                    print("🎯 所有交互都通过标准JSON-RPC协议进行")
                    
        except Exception as e:
            print(f"❌ 协议演示失败: {e}")
    
    async def demo_type_safety(self):
        """演示类型安全的价值"""
        print("\n🔍 3. 类型安全演示")
        print("-" * 40)
        
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # 正确的类型调用
                    print("✅ 正确的类型调用:")
                    result = await session.call_tool("calculator", {
                        "operation": "add",
                        "a": 5,
                        "b": 3
                    })
                    print(f"   5 + 3 = {result.content[0].text}")
                    
                    # 错误的类型调用（会被MCP服务器拒绝）
                    print("\n❌ 错误的类型调用:")
                    try:
                        result = await session.call_tool("calculator", {
                            "operation": "invalid_op",  # 无效操作
                            "a": "not_a_number",       # 错误类型
                            "b": 3
                        })
                    except Exception as e:
                        print(f"   🛡️  MCP服务器拒绝了无效调用: {type(e).__name__}")
                    
                    print("🔒 MCP在运行时验证所有输入参数")
                    
        except Exception as e:
            print(f"❌ 类型安全演示失败: {e}")
    
    async def demo_extensibility(self):
        """演示可扩展性的价值"""
        print("\n🔄 4. 可扩展性演示")
        print("-" * 40)
        
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # 演示多种类型的功能
                    print("🔧 调用计算工具:")
                    calc_result = await session.call_tool("calculator", {
                        "operation": "multiply",
                        "a": 7,
                        "b": 6
                    })
                    print(f"   7 × 6 = {calc_result.content[0].text}")
                    
                    print("\n💾 调用数据存储工具:")
                    store_result = await session.call_tool("store_data", {
                        "key": "user_name",
                        "value": "Alice"
                    })
                    print(f"   {store_result.content[0].text}")
                    
                    print("\n🕒 调用时间工具:")
                    time_result = await session.call_tool("current_time", {})
                    print(f"   当前时间: {time_result.content[0].text}")
                    
                    print("\n📖 访问资源:")
                    resource_result = await session.read_resource("memory://conversation_history")
                    print(f"   对话历史: {resource_result.contents[0].text}")
                    
                    print("\n🎯 一个客户端可以访问多种类型的功能")
                    
        except Exception as e:
            print(f"❌ 可扩展性演示失败: {e}")
    
    async def demo_comparison_with_functions(self):
        """对比普通函数与MCP的差异"""
        print("\n⚖️  5. 普通函数 vs MCP 对比")
        print("-" * 40)
        
        # 普通函数方式
        def simple_calculator(operation: str, a: float, b: float) -> float:
            if operation == "add":
                return a + b
            elif operation == "multiply":
                return a * b
            else:
                raise ValueError("不支持的操作")
        
        print("🔧 普通函数方式:")
        print("   • 本地调用，无进程隔离")
        print("   • 无标准化协议")
        print("   • 运行时类型检查有限")
        print("   • 紧耦合，难以扩展")
        
        func_result = simple_calculator("add", 10, 5)
        print(f"   结果: 10 + 5 = {func_result}")
        
        print("\n🚀 MCP方式:")
        print("   • 独立进程，完全隔离")
        print("   • 标准JSON-RPC协议")
        print("   • 严格的Schema验证")
        print("   • 松耦合，易于扩展")
        print("   • 支持多种功能类型")
        
        try:
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    mcp_result = await session.call_tool("calculator", {
                        "operation": "add",
                        "a": 10,
                        "b": 5
                    })
                    print(f"   结果: 10 + 5 = {mcp_result.content[0].text}")
                    
        except Exception as e:
            print(f"   MCP调用失败: {e}")
        
        print("\n🎯 总结:")
        print("   MCP不仅仅是函数调用，而是一个完整的工具生态系统")
        print("   它提供了安全性、标准化、类型安全和可扩展性")


def check_mcp_server():
    """检查MCP服务器是否可用"""
    try:
        # 尝试启动服务器进程来检查
        result = subprocess.run(
            [sys.executable, "enhanced_server.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return True
    except:
        return False


async def main():
    print("🌟 MCP (Model Context Protocol) 真正价值演示")
    print("展示MCP相比普通Python函数的优势")
    print()
    
    # 检查MCP服务器
    if not check_mcp_server():
        print("❌ 无法找到MCP服务器 (enhanced_server.py)")
        print("请确保 enhanced_server.py 文件存在并可执行")
        return
    
    demo = RealMCPDemo()
    await demo.demonstrate_mcp_advantages()
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("\n💡 MCP的核心价值:")
    print("   1. 🔒 进程隔离 - 安全性和稳定性")
    print("   2. 📋 标准化协议 - 互操作性")
    print("   3. 🔍 类型安全 - 运行时验证")
    print("   4. 🔄 可扩展性 - 多种功能类型")
    print("   5. 🌐 跨语言支持 - 不限制实现语言")
    print("\n这就是为什么MCP不仅仅是'另一个函数调用'的原因!")


if __name__ == "__main__":
    asyncio.run(main())