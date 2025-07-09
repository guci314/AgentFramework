#!/usr/bin/env python3
"""
Claude Sonnet 天气查询集成演示
展示如何使用 Claude Sonnet 语言模型调用天气查询 MCP 工具
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置代理服务器环境变量
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 导入天气查询模块
from weather_mcp_demo import MockWeatherMCPServer


class WeatherToolWrapper:
    """天气查询工具包装类，简化版本"""
    
    def __init__(self, name: str, description: str, weather_server: MockWeatherMCPServer):
        self.name = name
        self.description = description
        self.weather_server = weather_server
    
    async def call(self, **kwargs) -> str:
        """调用工具"""
        result = await self.weather_server.call_tool(self.name, kwargs)
        
        if result["status"] == "success":
            if "formatted_report" in result:
                return result["formatted_report"]
            else:
                return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return f"错误：{result['message']}"


class ClaudeWeatherAgent:
    """Claude 天气查询智能助手"""
    
    def __init__(self):
        # 初始化 Claude Sonnet 模型
        self.llm = ChatOpenAI(
            temperature=0,
            model="anthropic/claude-sonnet-4", 
            base_url='https://openrouter.ai/api/v1',
            api_key=os.getenv('OPENROUTER_API_KEY'),
        )
        
        # 初始化天气服务器
        self.weather_server = MockWeatherMCPServer()
        
        # 创建工具映射
        self.tools = {
            "get_current_weather": WeatherToolWrapper(
                name="get_current_weather",
                description="获取指定城市的当前天气信息",
                weather_server=self.weather_server
            ),
            "get_weather_by_coordinates": WeatherToolWrapper(
                name="get_weather_by_coordinates", 
                description="根据经纬度坐标获取天气信息",
                weather_server=self.weather_server
            ),
            "get_weather_forecast": WeatherToolWrapper(
                name="get_weather_forecast",
                description="获取指定城市的天气预报",
                weather_server=self.weather_server
            ),
            "get_supported_cities": WeatherToolWrapper(
                name="get_supported_cities",
                description="获取支持查询天气的城市列表",
                weather_server=self.weather_server
            )
        }
        
        # 对话历史
        self.conversation_history = []
        
        # 系统提示词
        self.system_prompt = """你是一个专业的天气查询助手，可以帮助用户查询全球各地的天气信息。

你有以下工具可以使用：

1. get_current_weather(city: str) - 获取指定城市的当前天气
   参数：city - 城市名称（支持中英文，如：北京、Beijing、上海、Shanghai）

2. get_weather_by_coordinates(latitude: float, longitude: float) - 根据坐标获取天气
   参数：latitude - 纬度（-90 到 90），longitude - 经度（-180 到 180）

3. get_weather_forecast(city: str, days: int = 5) - 获取天气预报
   参数：city - 城市名称，days - 预报天数（1-7天）

4. get_supported_cities() - 获取支持的城市列表

使用指南：
- 当用户询问天气时，首先分析他们的需求（当前天气 vs 预报）
- 识别城市名称，如果用户提供的城市不在支持列表中，建议相近的城市
- 如果用户提供坐标，使用坐标查询
- 提供友好、详细的天气信息解释
- 可以根据天气情况给出合理的建议（如穿衣、出行等）

请用中文回答，保持友好和专业的语气。"""
    
    async def chat(self, user_input: str) -> str:
        """与用户进行对话"""
        try:
            # 添加用户消息到历史
            self.conversation_history.append(HumanMessage(content=user_input))
            
            # 分析用户意图并决定是否需要调用工具
            intent_result = await self.analyze_intent(user_input)
            
            if intent_result["needs_tool"]:
                # 调用相应的工具
                tool_result = await self.call_weather_tool(intent_result)
                
                # 生成基于工具结果的回复
                response = await self.generate_response_with_tool_result(user_input, tool_result)
            else:
                # 直接生成回复
                response = await self.generate_direct_response(user_input)
            
            # 添加AI回复到历史
            self.conversation_history.append(AIMessage(content=response))
            
            return response
            
        except Exception as e:
            error_msg = f"抱歉，处理您的请求时出现了错误：{str(e)}"
            self.conversation_history.append(AIMessage(content=error_msg))
            return error_msg
    
    async def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """分析用户意图"""
        # 简化的意图分析，基于关键词和模式匹配
        user_input_lower = user_input.lower()
        
        # 检查是否包含天气相关关键词
        weather_keywords = ["天气", "温度", "下雨", "晴天", "多云", "weather", "temperature", "rain", "预报", "forecast"]
        if not any(keyword in user_input_lower for keyword in weather_keywords):
            return {"needs_tool": False, "reasoning": "不是天气查询"}
        
        # 提取城市名
        cities = ["北京", "beijing", "上海", "shanghai", "广州", "guangzhou", "深圳", "shenzhen", 
                 "杭州", "hangzhou", "成都", "chengdu", "西安", "xian", "london", "伦敦", 
                 "new york", "纽约", "tokyo", "东京", "paris", "巴黎", "singapore", "新加坡"]
        
        detected_city = None
        for city in cities:
            if city in user_input_lower:
                detected_city = city
                break
        
        # 检查坐标查询
        import re
        coord_pattern = r'\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)?'
        coord_match = re.search(coord_pattern, user_input)
        
        if coord_match:
            lat, lon = float(coord_match.group(1)), float(coord_match.group(2))
            return {
                "needs_tool": True,
                "tool_name": "get_weather_by_coordinates",
                "parameters": {"latitude": lat, "longitude": lon},
                "reasoning": "坐标查询"
            }
        
        # 检查预报查询
        if any(word in user_input_lower for word in ["预报", "未来", "明天", "后天", "forecast", "天"]):
            days = 5  # 默认5天
            # 尝试提取天数
            day_pattern = r'(\d+)\s*天'
            day_match = re.search(day_pattern, user_input)
            if day_match:
                days = min(int(day_match.group(1)), 7)  # 最多7天
            
            return {
                "needs_tool": True,
                "tool_name": "get_weather_forecast",
                "parameters": {"city": detected_city or "北京", "days": days},
                "reasoning": "天气预报查询"
            }
        
        # 检查城市列表查询
        if any(word in user_input_lower for word in ["支持", "城市", "列表", "哪些"]):
            return {
                "needs_tool": True,
                "tool_name": "get_supported_cities",
                "parameters": {},
                "reasoning": "城市列表查询"
            }
        
        # 默认当前天气查询
        return {
            "needs_tool": True,
            "tool_name": "get_current_weather",
            "parameters": {"city": detected_city or "北京"},
            "reasoning": "当前天气查询"
        }
    
    async def call_weather_tool(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """调用天气工具"""
        tool_name = intent_result.get("tool_name")
        parameters = intent_result.get("parameters", {})
        
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            result = await tool.call(**parameters)
            return {"success": True, "result": result, "tool": tool_name}
        else:
            return {"success": False, "error": f"未知的工具: {tool_name}"}
    
    async def generate_response_with_tool_result(self, user_input: str, tool_result: Dict[str, Any]) -> str:
        """基于工具结果生成回复"""
        if tool_result["success"]:
            prompt = f"""
用户询问："{user_input}"

我使用工具 {tool_result['tool']} 获得了以下天气信息：
{tool_result['result']}

请基于这些信息，用自然、友好的语言回答用户的问题。可以添加一些实用的建议（如穿衣、出行建议等）。
"""
        else:
            prompt = f"""
用户询问："{user_input}"

在查询天气信息时遇到了问题：{tool_result['error']}

请礼貌地告知用户遇到的问题，并提供替代建议。
"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def generate_direct_response(self, user_input: str) -> str:
        """直接生成回复（不使用工具）"""
        messages = [
            SystemMessage(content=self.system_prompt)
        ] + self.conversation_history[-10:]  # 保留最近10轮对话
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []


async def interactive_demo():
    """交互式演示"""
    print("🌤️ Claude Sonnet 天气查询助手")
    print("=" * 50)
    print("您可以询问各种天气相关问题，例如：")
    print("  - 北京今天天气怎么样？")
    print("  - 上海未来3天的天气预报")
    print("  - 坐标 (31.2304, 121.4737) 的天气")
    print("  - 支持哪些城市？")
    print("输入 'quit' 退出，输入 'clear' 清空对话历史")
    print("=" * 50)
    
    agent = ClaudeWeatherAgent()
    
    while True:
        try:
            user_input = input("\n🤔 您的问题: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！感谢使用天气查询助手！")
                break
            
            if user_input.lower() in ['clear', '清空']:
                agent.clear_history()
                print("✅ 对话历史已清空")
                continue
            
            if not user_input:
                continue
            
            print("\n🤖 正在查询...")
            response = await agent.chat(user_input)
            print(f"\n🤖 助手: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 再见！感谢使用天气查询助手！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")


async def batch_demo():
    """批量演示"""
    print("🌤️ Claude Sonnet 天气查询批量演示")
    print("=" * 50)
    
    agent = ClaudeWeatherAgent()
    
    # 演示问题列表
    demo_questions = [
        "你好，我想了解一下北京今天的天气情况",
        "上海明天会下雨吗？",
        "给我查询广州未来5天的天气预报",
        "你支持查询哪些城市的天气？",
        "坐标 (39.9042, 116.4074) 这个位置的天气如何？",
        "深圳和杭州哪个城市今天更适合户外活动？",
        "今天穿什么衣服比较合适？我在成都",
    ]
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. 🤔 用户问题: {question}")
        print("-" * 40)
        
        try:
            response = await agent.chat(question)
            print(f"🤖 助手回复: {response}")
        except Exception as e:
            print(f"❌ 处理失败: {e}")
        
        print("\n" + "=" * 50)
    
    print("\n✅ 批量演示完成！")


async def main():
    """主函数 - 直接进入批量演示模式"""
    print("🌤️ Claude Sonnet 天气查询集成演示")
    print("展示 Claude Sonnet 如何调用天气查询 MCP 工具")
    print("🚀 自动运行批量演示模式")
    print()
    
    # 检查 API 密钥
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ 错误：请在 .env 文件中设置 OPENROUTER_API_KEY")
        print("   或者设置环境变量 OPENROUTER_API_KEY")
        return
    
    try:
        # 直接运行批量演示
        await batch_demo()
    
    except KeyboardInterrupt:
        print("\n👋 演示结束！")


if __name__ == "__main__":
    asyncio.run(main())