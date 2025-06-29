#!/usr/bin/env python3
"""
MCP 加法工具服务器
简单的计算器服务器，提供加法功能，不需要语言模型
"""

import asyncio
import sys
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# 创建服务器实例
server = Server("calculator-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="add",
            description="将两个数字相加",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number", 
                        "description": "第一个数字"
                    },
                    "b": {
                        "type": "number",
                        "description": "第二个数字"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="subtract",
            description="两个数字相减 (a - b)",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "被减数"
                    },
                    "b": {
                        "type": "number", 
                        "description": "减数"
                    }
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="multiply",
            description="两个数字相乘",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "第一个数字"
                    },
                    "b": {
                        "type": "number",
                        "description": "第二个数字"  
                    }
                },
                "required": ["a", "b"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "add":
            a = float(arguments.get("a", 0))
            b = float(arguments.get("b", 0))
            result = a + b
            return [TextContent(
                type="text",
                text=f"计算结果: {a} + {b} = {result}"
            )]
        
        elif name == "subtract":
            a = float(arguments.get("a", 0))
            b = float(arguments.get("b", 0))
            result = a - b
            return [TextContent(
                type="text", 
                text=f"计算结果: {a} - {b} = {result}"
            )]
        
        elif name == "multiply":
            a = float(arguments.get("a", 0))
            b = float(arguments.get("b", 0))
            result = a * b
            return [TextContent(
                type="text",
                text=f"计算结果: {a} × {b} = {result}"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]
    
    except (ValueError, TypeError) as e:
        return [TextContent(
            type="text",
            text=f"参数错误: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"计算错误: {str(e)}"
        )]


async def main():
    """启动服务器"""
    print("启动MCP计算器服务器...", file=sys.stderr)
    print("等待客户端连接...", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())