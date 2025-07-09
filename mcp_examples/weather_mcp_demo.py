#!/usr/bin/env python3
"""
天气查询 MCP 简化演示
展示天气查询 MCP 工具的核心功能，使用 Mock 服务器实现
"""

import asyncio
import json
from typing import Dict, Any, List
from weather_data import weather_db


class MockWeatherMCPServer:
    """模拟的天气查询 MCP 服务器，展示核心概念"""
    
    def __init__(self):
        self.call_history = []
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用的天气查询工具列表"""
        return [
            {
                "name": "get_current_weather",
                "description": "获取指定城市的当前天气信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称（支持中英文）"}
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "get_weather_by_coordinates",
                "description": "根据经纬度坐标获取天气信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "description": "纬度（-90 到 90）"},
                        "longitude": {"type": "number", "description": "经度（-180 到 180）"}
                    },
                    "required": ["latitude", "longitude"]
                }
            },
            {
                "name": "get_weather_forecast",
                "description": "获取指定城市的天气预报",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"},
                        "days": {"type": "integer", "description": "预报天数（1-7天）", "default": 5}
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "get_supported_cities",
                "description": "获取支持查询天气的城市列表",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定工具"""
        # 记录调用历史
        call_record = {
            "tool": tool_name,
            "arguments": arguments,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.call_history.append(call_record)
        
        try:
            if tool_name == "get_current_weather":
                city = arguments.get("city")
                if not city:
                    return {"status": "error", "message": "缺少城市名称参数"}
                
                weather_data = weather_db.generate_weather(city=city)
                formatted_report = weather_db.format_weather_report(weather_data)
                
                return {
                    "status": "success",
                    "tool": "get_current_weather",
                    "formatted_report": formatted_report,
                    "raw_data": weather_data
                }
            
            elif tool_name == "get_weather_by_coordinates":
                lat = arguments.get("latitude")
                lon = arguments.get("longitude")
                
                if lat is None or lon is None:
                    return {"status": "error", "message": "缺少纬度或经度参数"}
                
                weather_data = weather_db.generate_weather(lat=lat, lon=lon)
                formatted_report = weather_db.format_weather_report(weather_data)
                
                return {
                    "status": "success",
                    "tool": "get_weather_by_coordinates",
                    "formatted_report": formatted_report,
                    "raw_data": weather_data
                }
            
            elif tool_name == "get_weather_forecast":
                city = arguments.get("city")
                days = arguments.get("days", 5)
                
                if not city:
                    return {"status": "error", "message": "缺少城市名称参数"}
                
                forecast_data = weather_db.generate_forecast(city=city, days=days)
                formatted_report = weather_db.format_forecast_report(forecast_data, city)
                
                return {
                    "status": "success",
                    "tool": "get_weather_forecast",
                    "formatted_report": formatted_report,
                    "raw_data": forecast_data
                }
            
            elif tool_name == "get_supported_cities":
                cities = weather_db.get_supported_cities()
                return {
                    "status": "success",
                    "tool": "get_supported_cities",
                    "cities": cities,
                    "total_count": len(cities)
                }
            
            else:
                return {"status": "error", "message": f"未知的工具名称: {tool_name}"}
        
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"服务器内部错误: {str(e)}"}
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """获取工具调用历史"""
        return self.call_history


class WeatherQueryDemo:
    """天气查询演示类"""
    
    def __init__(self):
        self.server = MockWeatherMCPServer()
    
    async def run_demo(self):
        """运行完整的天气查询演示"""
        print("🌤️ 天气查询 MCP 工具演示")
        print("=" * 50)
        
        # 显示可用工具
        await self.show_available_tools()
        
        # 演示各种查询功能
        await self.demo_current_weather()
        await self.demo_coordinates_weather()
        await self.demo_weather_forecast()
        await self.demo_supported_cities()
        
        # 显示调用历史
        await self.show_call_history()
    
    async def show_available_tools(self):
        """显示可用工具"""
        print("\n📋 可用的天气查询工具:")
        tools = self.server.get_available_tools()
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool['name']}: {tool['description']}")
        print()
    
    async def demo_current_weather(self):
        """演示当前天气查询"""
        print("🌡️ 演示：当前天气查询")
        print("-" * 30)
        
        # 查询不同城市的天气
        cities = ["北京", "上海", "london", "tokyo"]
        
        for city in cities:
            print(f"\n🔍 查询 {city} 的天气:")
            result = await self.server.call_tool("get_current_weather", {"city": city})
            
            if result["status"] == "success":
                print(result["formatted_report"])
            else:
                print(f"❌ 查询失败: {result['message']}")
        
        print("\n" + "=" * 50)
    
    async def demo_coordinates_weather(self):
        """演示坐标天气查询"""
        print("🗺️ 演示：坐标天气查询")
        print("-" * 30)
        
        # 使用坐标查询天气
        coordinates = [
            {"latitude": 39.9042, "longitude": 116.4074, "location": "北京"},
            {"latitude": 31.2304, "longitude": 121.4737, "location": "上海"},
            {"latitude": 51.5074, "longitude": -0.1278, "location": "伦敦"}
        ]
        
        for coord in coordinates:
            print(f"\n🔍 查询坐标 ({coord['latitude']}, {coord['longitude']}) 的天气:")
            result = await self.server.call_tool("get_weather_by_coordinates", {
                "latitude": coord["latitude"],
                "longitude": coord["longitude"]
            })
            
            if result["status"] == "success":
                print(result["formatted_report"])
            else:
                print(f"❌ 查询失败: {result['message']}")
        
        print("\n" + "=" * 50)
    
    async def demo_weather_forecast(self):
        """演示天气预报查询"""
        print("📊 演示：天气预报查询")
        print("-" * 30)
        
        # 查询不同城市和天数的预报
        forecast_queries = [
            {"city": "北京", "days": 3},
            {"city": "shanghai", "days": 5},
            {"city": "广州", "days": 7}
        ]
        
        for query in forecast_queries:
            print(f"\n🔍 查询 {query['city']} {query['days']}天预报:")
            result = await self.server.call_tool("get_weather_forecast", query)
            
            if result["status"] == "success":
                print(result["formatted_report"])
            else:
                print(f"❌ 查询失败: {result['message']}")
        
        print("\n" + "=" * 50)
    
    async def demo_supported_cities(self):
        """演示支持的城市列表"""
        print("🏙️ 演示：支持的城市列表")
        print("-" * 30)
        
        result = await self.server.call_tool("get_supported_cities", {})
        
        if result["status"] == "success":
            cities = result["cities"]
            print(f"✅ 共支持 {result['total_count']} 个城市:")
            
            # 按中英文分组显示
            chinese_cities = [city for city in cities if any('\u4e00' <= char <= '\u9fff' for char in city)]
            english_cities = [city for city in cities if city not in chinese_cities]
            
            if chinese_cities:
                print("\n🇨🇳 中文城市:")
                print("  " + ", ".join(chinese_cities))
            
            if english_cities:
                print("\n🌍 英文城市:")
                print("  " + ", ".join(english_cities))
        else:
            print(f"❌ 获取失败: {result['message']}")
        
        print("\n" + "=" * 50)
    
    async def show_call_history(self):
        """显示工具调用历史"""
        print("📝 工具调用历史:")
        print("-" * 30)
        
        history = self.server.get_call_history()
        for i, call in enumerate(history, 1):
            print(f"{i}. 工具: {call['tool']}")
            print(f"   参数: {call['arguments']}")
            print(f"   时间: {call['timestamp']:.2f}")
            print()
        
        print(f"📊 总共调用了 {len(history)} 次工具")


async def main():
    """主函数"""
    print("🌤️ 天气查询 MCP 工具演示程序")
    print("展示天气查询功能的核心概念和使用方法")
    print()
    
    demo = WeatherQueryDemo()
    await demo.run_demo()
    
    print("\n✅ 演示完成！")
    print("这个演示展示了天气查询 MCP 工具的所有主要功能:")
    print("  - 按城市名查询当前天气")
    print("  - 按坐标查询当前天气")
    print("  - 查询天气预报（1-7天）")
    print("  - 获取支持的城市列表")
    print("\n🚀 接下来可以尝试 claude_weather_demo.py 来体验与语言模型的集成!")


if __name__ == "__main__":
    asyncio.run(main())