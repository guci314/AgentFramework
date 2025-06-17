#!/usr/bin/env python3
"""
一键运行MCP计算器示例
自动演示服务器和客户端的交互
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def quick_test():
    """快速测试MCP计算器功能"""
    print("🚀 MCP 计算器快速测试")
    print("=" * 40)
    
    # 设置服务器参数
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )
    
    test_cases = [
        ("add", {"a": 10, "b": 20}, "加法测试: 10 + 20"),
        ("subtract", {"a": 100, "b": 30}, "减法测试: 100 - 30"), 
        ("multiply", {"a": 6, "b": 9}, "乘法测试: 6 × 9"),
        ("add", {"a": 3.14, "b": 2.86}, "小数加法: 3.14 + 2.86"),
        ("subtract", {"a": -5, "b": -3}, "负数减法: (-5) - (-3)"),
    ]
    
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # 获取工具列表
                print("📋 获取服务器工具列表...")
                tools = await session.list_tools()
                if tools and tools.tools:
                    print(f"✅ 发现 {len(tools.tools)} 个工具:")
                    for tool in tools.tools:
                        print(f"   • {tool.name}: {tool.description}")
                else:
                    print("❌ 未发现任何工具")
                    return
                
                print("\n🧪 执行测试用例...")
                print("-" * 40)
                
                success_count = 0
                for tool_name, args, description in test_cases:
                    try:
                        print(f"🔄 {description}")
                        result = await session.call_tool(tool_name, args)
                        
                        if result.content and len(result.content) > 0:
                            result_text = result.content[0].text
                            print(f"✅ {result_text}")
                            success_count += 1
                        else:
                            print(f"❌ 无结果返回")
                        
                    except Exception as e:
                        print(f"❌ 错误: {e}")
                    
                    print()
                
                print("=" * 40)
                print(f"📊 测试完成: {success_count}/{len(test_cases)} 成功")
                
                if success_count == len(test_cases):
                    print("🎉 所有测试通过! MCP服务器工作正常")
                else:
                    print("⚠️  部分测试失败，请检查服务器实现")
    
    except Exception as e:
        print(f"❌ 连接服务器失败: {e}")
        print("\n💡 请确保:")
        print("   1. 已安装 mcp 依赖: pip install mcp")
        print("   2. server.py 文件存在且可执行")
        print("   3. 没有其他进程占用端口")


def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查依赖...")
    
    try:
        import mcp
        print("✅ mcp 库已安装")
        return True
    except ImportError:
        print("❌ mcp 库未安装")
        print("请运行: pip install mcp")
        return False


def show_usage():
    """显示使用说明"""
    print("📖 MCP 计算器使用说明")
    print("=" * 40)
    print("1. 快速测试:     python run_example.py")
    print("2. 启动服务器:   python server.py")
    print("3. 启动客户端:   python client.py")
    print("4. 查看帮助:     python run_example.py --help")
    print()
    print("📁 文件说明:")
    print("• server.py      - MCP服务器实现")
    print("• client.py      - MCP客户端实现")
    print("• run_example.py - 一键测试脚本")
    print("• requirements.txt - 依赖列表")


async def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_usage()
        return
    
    # 检查当前工作目录
    current_dir = Path.cwd()
    expected_files = ['server.py', 'client.py', 'requirements.txt']
    missing_files = [f for f in expected_files if not (current_dir / f).exists()]
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        print(f"请确保在 mcp_example 目录下运行此脚本")
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 运行快速测试
    await quick_test()
    
    print("\n🎯 想要交互式体验吗?")
    choice = input("输入 'y' 启动交互式客户端 (或按 Enter 退出): ").strip().lower()
    
    if choice == 'y':
        print("\n🚀 启动交互式客户端...")
        subprocess.run([sys.executable, "client.py"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        sys.exit(1)