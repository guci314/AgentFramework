#!/usr/bin/env python3
"""
天气查询 MCP 服务器
提供天气查询功能的标准 MCP 服务器实现
"""

import asyncio
import json
import sys
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 导入天气数据模块
from weather_data import weather_db


# 创建服务器实例
server = Server("weather-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的天气查询工具"""
    return [
        Tool(
            name="get_current_weather",
            description="获取指定城市的当前天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称（支持中英文，如：北京、Beijing、上海、Shanghai）"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_weather_by_coordinates",
            description="根据经纬度坐标获取天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "纬度（-90 到 90）"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "经度（-180 到 180）"
                    }
                },
                "required": ["latitude", "longitude"]
            }
        ),
        Tool(
            name="get_weather_forecast",
            description="获取指定城市的天气预报",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称（支持中英文）"
                    },
                    "days": {
                        "type": "integer",
                        "description": "预报天数（1-7天，默认5天）",
                        "minimum": 1,
                        "maximum": 7,
                        "default": 5
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_forecast_by_coordinates",
            description="根据经纬度坐标获取天气预报",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "纬度（-90 到 90）"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "经度（-180 到 180）"
                    },
                    "days": {
                        "type": "integer",
                        "description": "预报天数（1-7天，默认5天）",
                        "minimum": 1,
                        "maximum": 7,
                        "default": 5
                    }
                },
                "required": ["latitude", "longitude"]
            }
        ),
        Tool(
            name="get_supported_cities",
            description="获取支持查询天气的城市列表",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_city_coordinates",
            description="根据城市名称获取经纬度坐标",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "get_current_weather":
            city = arguments.get("city")
            if not city:
                return [TextContent(type="text", text="错误：缺少城市名称参数")]
            
            try:
                weather_data = weather_db.generate_weather(city=city)
                formatted_report = weather_db.format_weather_report(weather_data)
                
                # 同时返回格式化报告和JSON数据
                response = {
                    "status": "success",
                    "formatted_report": formatted_report,
                    "raw_data": weather_data
                }
                
                return [TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]
                
            except ValueError as e:
                return [TextContent(type="text", text=f"错误：{str(e)}")]
        
        elif name == "get_weather_by_coordinates":
            lat = arguments.get("latitude")
            lon = arguments.get("longitude")
            
            if lat is None or lon is None:
                return [TextContent(type="text", text="错误：缺少纬度或经度参数")]
            
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return [TextContent(type="text", text="错误：坐标超出有效范围")]
            
            try:
                weather_data = weather_db.generate_weather(lat=lat, lon=lon)
                formatted_report = weather_db.format_weather_report(weather_data)
                
                response = {
                    "status": "success",
                    "formatted_report": formatted_report,
                    "raw_data": weather_data
                }
                
                return [TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]
                
            except ValueError as e:
                return [TextContent(type="text", text=f"错误：{str(e)}")]
        
        elif name == "get_weather_forecast":
            city = arguments.get("city")
            days = arguments.get("days", 5)
            
            if not city:
                return [TextContent(type="text", text="错误：缺少城市名称参数")]
            
            if not (1 <= days <= 7):
                return [TextContent(type="text", text="错误：预报天数必须在1-7天之间")]
            
            try:
                forecast_data = weather_db.generate_forecast(city=city, days=days)
                formatted_report = weather_db.format_forecast_report(forecast_data, city)
                
                response = {
                    "status": "success",
                    "formatted_report": formatted_report,
                    "raw_data": forecast_data
                }
                
                return [TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]
                
            except ValueError as e:
                return [TextContent(type="text", text=f"错误：{str(e)}")]
        
        elif name == "get_forecast_by_coordinates":
            lat = arguments.get("latitude")
            lon = arguments.get("longitude")
            days = arguments.get("days", 5)
            
            if lat is None or lon is None:
                return [TextContent(type="text", text="错误：缺少纬度或经度参数")]
            
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return [TextContent(type="text", text="错误：坐标超出有效范围")]
            
            if not (1 <= days <= 7):
                return [TextContent(type="text", text="错误：预报天数必须在1-7天之间")]
            
            try:
                forecast_data = weather_db.generate_forecast(lat=lat, lon=lon, days=days)
                city_name = f"坐标({lat:.2f}, {lon:.2f})"
                formatted_report = weather_db.format_forecast_report(forecast_data, city_name)
                
                response = {
                    "status": "success",
                    "formatted_report": formatted_report,
                    "raw_data": forecast_data
                }
                
                return [TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]
                
            except ValueError as e:
                return [TextContent(type="text", text=f"错误：{str(e)}")]
        
        elif name == "get_supported_cities":
            cities = weather_db.get_supported_cities()
            
            response = {
                "status": "success",
                "message": "支持的城市列表",
                "cities": cities,
                "total_count": len(cities)
            }
            
            return [TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]
        
        elif name == "search_city_coordinates":
            city = arguments.get("city")
            if not city:
                return [TextContent(type="text", text="错误：缺少城市名称参数")]
            
            coordinates = weather_db.get_coordinates(city)
            if coordinates:
                lat, lon = coordinates
                response = {
                    "status": "success",
                    "city": city,
                    "coordinates": {
                        "latitude": lat,
                        "longitude": lon
                    }
                }
            else:
                response = {
                    "status": "error",
                    "message": f"未找到城市 '{city}' 的坐标信息",
                    "suggestion": "请检查城市名称拼写，或查看支持的城市列表"
                }
            
            return [TextContent(type="text", text=json.dumps(response, ensure_ascii=False, indent=2))]
        
        else:
            return [TextContent(type="text", text=f"错误：未知的工具名称 '{name}'")]
    
    except Exception as e:
        error_response = {
            "status": "error",
            "message": f"服务器内部错误：{str(e)}"
        }
        return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False, indent=2))]


async def main():
    """主函数：启动 MCP 服务器"""
    try:
        # 使用标准输入输出运行服务器
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    except Exception as e:
        print(f"服务器启动失败：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    print("🌤️ 天气查询 MCP 服务器启动中...", file=sys.stderr)
    print("支持的功能：", file=sys.stderr)
    print("  - 当前天气查询（按城市名或坐标）", file=sys.stderr)
    print("  - 天气预报查询（1-7天）", file=sys.stderr)
    print("  - 城市坐标查询", file=sys.stderr)
    print("  - 支持城市列表", file=sys.stderr)
    print("服务器就绪，等待客户端连接...", file=sys.stderr)
    
    asyncio.run(main())