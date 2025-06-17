#!/usr/bin/env python3
"""
使用MCP Inspector CLI工具测试计算器
需要先安装: npm install -g @modelcontextprotocol/inspector
"""

import subprocess
import sys
import time
import threading
from pathlib import Path


def start_server():
    """后台启动服务器"""
    return subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def test_with_inspector():
    """使用Inspector CLI测试"""
    print("🔍 使用 MCP Inspector CLI 测试")
    print("=" * 40)
    
    # 检查inspector是否安装
    try:
        result = subprocess.run(
            ["npx", "@modelcontextprotocol/inspector", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print("❌ MCP Inspector 未安装")
            print("请运行: npm install -g @modelcontextprotocol/inspector")
            return
        print("✅ MCP Inspector 已安装")
    except Exception as e:
        print(f"❌ 无法检查 Inspector: {e}")
        print("请确保安装了 Node.js 和 npm")
        return
    
    # 启动服务器
    print("🚀 启动 MCP 服务器...")
    server_process = start_server()
    
    try:
        # 等待服务器启动
        time.sleep(2)
        
        # 测试工具调用
        test_cases = [
            ("add", [("a", "5"), ("b", "3")], "加法测试"),
            ("subtract", [("a", "10"), ("b", "4")], "减法测试"),
            ("multiply", [("a", "6"), ("b", "7")], "乘法测试"),
        ]
        
        for tool_name, args, description in test_cases:
            print(f"\n🔄 {description}: {tool_name}")
            
            # 构建inspector命令
            cmd = [
                "npx", "@modelcontextprotocol/inspector", 
                "--cli", "python", "server.py",
                "--method", "tools/call",
                "--tool-name", tool_name
            ]
            
            # 添加参数
            for arg_name, arg_value in args:
                cmd.extend(["--tool-arg", f"{arg_name}={arg_value}"])
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print(f"✅ 成功: {result.stdout.strip()}")
                else:
                    print(f"❌ 失败: {result.stderr.strip()}")
            
            except subprocess.TimeoutExpired:
                print("❌ 超时")
            except Exception as e:
                print(f"❌ 错误: {e}")
    
    finally:
        # 停止服务器
        server_process.terminate()
        server_process.wait()
        print("\n🛑 服务器已停止")


def show_manual_usage():
    """显示手动使用说明"""
    print("📖 手动使用 MCP Inspector")
    print("=" * 40)
    print("1. 启动服务器:")
    print("   python server.py")
    print()
    print("2. 在另一个终端中使用 Inspector:")
    print("   # 列出工具")
    print("   npx @modelcontextprotocol/inspector --cli python server.py --method tools/list")
    print()
    print("   # 调用加法工具")
    print("   npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name add --tool-arg a=5 --tool-arg b=3")
    print()
    print("   # 调用减法工具")
    print("   npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name subtract --tool-arg a=10 --tool-arg b=4")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        show_manual_usage()
    else:
        test_with_inspector()