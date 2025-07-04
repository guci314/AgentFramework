#!/usr/bin/env python3
"""
增强版 MCP 服务器示例
展示完整的 MCP 功能：工具、资源、提示模板
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent, Resource, 
    Prompt, PromptArgument, PromptMessage,
    GetPromptResult
)

# 创建服务器实例
server = Server("enhanced-mcp-server")

# 模拟数据存储
data_store = {}
conversation_history = []

@server.list_tools()
async def list_tools() -> List[Tool]:
    """列出所有可用工具"""
    return [
        # 计算器工具
        Tool(
            name="calculator",
            description="执行基本数学运算",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide", "power"],
                        "description": "运算类型"
                    },
                    "a": {"type": "number", "description": "第一个数字"},
                    "b": {"type": "number", "description": "第二个数字"}
                },
                "required": ["operation", "a", "b"]
            }
        ),
        
        # 数据存储工具
        Tool(
            name="data_manager",
            description="管理键值对数据存储",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["set", "get", "delete", "list", "clear"],
                        "description": "操作类型"
                    },
                    "key": {"type": "string", "description": "数据键"},
                    "value": {"type": "string", "description": "数据值（仅用于set操作）"}
                },
                "required": ["action"]
            }
        ),
        
        # 时间工具
        Tool(
            name="datetime_tool",
            description="获取当前时间和日期信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "时间格式，默认为ISO格式",
                        "default": "iso"
                    },
                    "timezone": {
                        "type": "string", 
                        "description": "时区，默认为本地时区",
                        "default": "local"
                    }
                }
            }
        ),
        
        # 文本处理工具
        Tool(
            name="text_processor",
            description="处理文本：统计、转换、分析",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["count", "upper", "lower", "reverse", "word_count"],
                        "description": "处理类型"
                    },
                    "text": {"type": "string", "description": "要处理的文本"}
                },
                "required": ["action", "text"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    try:
        # 记录工具调用历史
        conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "tool": name,
            "arguments": arguments
        })
        
        if name == "calculator":
            return await handle_calculator(arguments)
        elif name == "data_manager":
            return await handle_data_manager(arguments)
        elif name == "datetime_tool":
            return await handle_datetime_tool(arguments)
        elif name == "text_processor":
            return await handle_text_processor(arguments)
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
            
    except Exception as e:
        return [TextContent(type="text", text=f"工具执行错误: {str(e)}")]

async def handle_calculator(args: Dict[str, Any]) -> List[TextContent]:
    """处理计算器操作"""
    operation = args.get("operation")
    a = float(args.get("a", 0))
    b = float(args.get("b", 0))
    
    if operation == "add":
        result = a + b
        symbol = "+"
    elif operation == "subtract":
        result = a - b
        symbol = "-"
    elif operation == "multiply":
        result = a * b
        symbol = "×"
    elif operation == "divide":
        if b == 0:
            return [TextContent(type="text", text="错误：除数不能为零")]
        result = a / b
        symbol = "÷"
    elif operation == "power":
        result = a ** b
        symbol = "^"
    else:
        return [TextContent(type="text", text=f"不支持的运算: {operation}")]
    
    return [TextContent(
        type="text",
        text=f"计算结果: {a} {symbol} {b} = {result}"
    )]

async def handle_data_manager(args: Dict[str, Any]) -> List[TextContent]:
    """处理数据管理操作"""
    action = args.get("action")
    key = args.get("key")
    value = args.get("value")
    
    if action == "set":
        if not key or value is None:
            return [TextContent(type="text", text="设置数据需要提供键和值")]
        data_store[key] = value
        return [TextContent(type="text", text=f"已设置: {key} = {value}")]
    
    elif action == "get":
        if not key:
            return [TextContent(type="text", text="获取数据需要提供键")]
        value = data_store.get(key)
        if value is None:
            return [TextContent(type="text", text=f"未找到键: {key}")]
        return [TextContent(type="text", text=f"{key} = {value}")]
    
    elif action == "delete":
        if not key:
            return [TextContent(type="text", text="删除数据需要提供键")]
        if key in data_store:
            del data_store[key]
            return [TextContent(type="text", text=f"已删除: {key}")]
        return [TextContent(type="text", text=f"未找到键: {key}")]
    
    elif action == "list":
        if not data_store:
            return [TextContent(type="text", text="数据存储为空")]
        items = "\n".join([f"  {k}: {v}" for k, v in data_store.items()])
        return [TextContent(type="text", text=f"存储的数据:\n{items}")]
    
    elif action == "clear":
        count = len(data_store)
        data_store.clear()
        return [TextContent(type="text", text=f"已清空数据存储，删除了 {count} 项")]
    
    else:
        return [TextContent(type="text", text=f"不支持的操作: {action}")]

async def handle_datetime_tool(args: Dict[str, Any]) -> List[TextContent]:
    """处理时间工具操作"""
    format_type = args.get("format", "iso")
    now = datetime.now()
    
    if format_type == "iso":
        time_str = now.isoformat()
    elif format_type == "readable":
        time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
    elif format_type == "date":
        time_str = now.strftime("%Y-%m-%d")
    elif format_type == "time":
        time_str = now.strftime("%H:%M:%S")
    else:
        time_str = now.strftime(format_type)
    
    return [TextContent(type="text", text=f"当前时间: {time_str}")]

async def handle_text_processor(args: Dict[str, Any]) -> List[TextContent]:
    """处理文本处理操作"""
    action = args.get("action")
    text = args.get("text", "")
    
    if action == "count":
        result = f"字符数: {len(text)}"
    elif action == "upper":
        result = f"大写: {text.upper()}"
    elif action == "lower":
        result = f"小写: {text.lower()}"
    elif action == "reverse":
        result = f"反转: {text[::-1]}"
    elif action == "word_count":
        words = len(text.split())
        result = f"单词数: {words}"
    else:
        result = f"不支持的操作: {action}"
    
    return [TextContent(type="text", text=result)]

# 资源管理
@server.list_resources()
async def list_resources() -> List[Resource]:
    """列出可用资源"""
    return [
        Resource(
            uri="data://store",
            name="数据存储",
            description="当前数据存储的内容",
            mimeType="application/json"
        ),
        Resource(
            uri="history://conversations",
            name="对话历史",
            description="工具调用历史记录",
            mimeType="application/json"
        ),
        Resource(
            uri="config://server",
            name="服务器配置",
            description="MCP服务器配置信息",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri == "data://store":
        return json.dumps(data_store, indent=2, ensure_ascii=False)
    elif uri == "history://conversations":
        return json.dumps(conversation_history, indent=2, ensure_ascii=False)
    elif uri == "config://server":
        config = {
            "server_name": "enhanced-mcp-server",
            "version": "1.0.0",
            "tools": len(await list_tools()),
            "data_items": len(data_store),
            "conversation_count": len(conversation_history)
        }
        return json.dumps(config, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"未知资源: {uri}")

# 提示模板
@server.list_prompts()
async def list_prompts() -> List[Prompt]:
    """列出可用提示模板"""
    return [
        Prompt(
            name="data_analysis",
            description="数据分析助手",
            arguments=[
                PromptArgument(
                    name="data_description",
                    description="数据描述",
                    required=True
                ),
                PromptArgument(
                    name="analysis_type",
                    description="分析类型",
                    required=False
                )
            ]
        ),
        Prompt(
            name="problem_solver",
            description="问题解决助手",
            arguments=[
                PromptArgument(
                    name="problem",
                    description="问题描述",
                    required=True
                ),
                PromptArgument(
                    name="context",
                    description="背景信息",
                    required=False
                )
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
    """获取提示模板"""
    if name == "data_analysis":
        data_desc = arguments.get("data_description", "")
        analysis_type = arguments.get("analysis_type", "综合分析")
        
        prompt = f"""作为数据分析专家，请分析以下数据：

数据描述：{data_desc}
分析类型：{analysis_type}

请提供：
1. 数据概览
2. 关键指标
3. 趋势分析
4. 异常检测
5. 建议措施

请使用MCP工具来辅助分析。"""

        return GetPromptResult(
            description=f"分析数据：{data_desc[:50]}...",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt)
                )
            ]
        )
    
    elif name == "problem_solver":
        problem = arguments.get("problem", "")
        context = arguments.get("context", "")
        
        prompt = f"""作为问题解决专家，请帮助解决以下问题：

问题：{problem}
背景：{context}

请：
1. 分析问题本质
2. 提供解决方案
3. 评估可行性
4. 给出实施建议

可以使用MCP工具来辅助解决问题。"""

        return GetPromptResult(
            description=f"解决问题：{problem[:50]}...",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt)
                )
            ]
        )
    
    else:
        raise ValueError(f"未知提示模板: {name}")

async def main():
    """启动增强版MCP服务器"""
    print("启动增强版MCP服务器...", file=sys.stderr)
    print("功能包括：工具调用、资源访问、提示模板", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 