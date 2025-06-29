#!/usr/bin/env python3
"""
DeepSeek + MCP 集成示例
展示如何使用DeepSeek模型与MCP服务器进行交互
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
import openai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class DeepSeekMCPClient:
    """DeepSeek + MCP 集成客户端"""
    
    def __init__(self, server_command: List[str], api_key: str = None):
        self.server_command = server_command
        self.session: Optional[ClientSession] = None
        self.available_tools = []
        
        # 初始化DeepSeek客户端
        self.deepseek_client = openai.OpenAI(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
    
    async def connect_mcp(self):
        """连接到MCP服务器"""
        print(f"🔌 连接MCP服务器: {' '.join(self.server_command)}")
        
        server_params = StdioServerParameters(
            command=self.server_command[0],
            args=self.server_command[1:] if len(self.server_command) > 1 else []
        )
        
        self.session = await stdio_client(server_params)
        await self.session.initialize()
        
        # 获取可用工具
        tools_result = await self.session.list_tools()
        self.available_tools = tools_result.tools
        
        print(f"✅ MCP连接成功！可用工具: {len(self.available_tools)}")
        for tool in self.available_tools:
            print(f"  🔧 {tool.name}: {tool.description}")
    
    async def call_mcp_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """调用MCP工具"""
        if not self.session:
            raise RuntimeError("MCP未连接")
        
        print(f"🛠️ 调用MCP工具: {name}")
        print(f"📝 参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}")
        
        result = await self.session.call_tool(name, arguments)
        
        # 提取响应内容
        content_parts = []
        for content in result.content:
            if hasattr(content, 'text'):
                content_parts.append(content.text)
            else:
                content_parts.append(str(content))
        
        response = "\n".join(content_parts)
        print(f"✅ MCP工具响应: {response}")
        return response
    
    def get_tools_for_deepseek(self) -> List[Dict[str, Any]]:
        """获取适用于DeepSeek的工具定义"""
        tools = []
        for tool in self.available_tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
        return tools
    
    async def chat_with_deepseek(self, user_message: str, system_prompt: str = None) -> str:
        """使用DeepSeek进行对话，支持MCP工具调用"""
        
        # 构建系统提示
        if system_prompt is None:
            system_prompt = f"""你是一个智能助手，可以使用以下MCP工具来帮助用户：

可用的MCP工具：
"""
            for tool in self.available_tools:
                system_prompt += f"- {tool.name}: {tool.description}\n"
            
            system_prompt += "\n请根据用户需求选择合适的工具。如果需要调用工具，请使用function calling功能。"
        
        # 获取工具定义
        tools = self.get_tools_for_deepseek()
        
        print(f"🤖 DeepSeek处理用户请求...")
        print(f"💬 用户消息: {user_message}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # 调用DeepSeek API
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            response_text = message.content or ""
            
            # 处理工具调用
            if message.tool_calls:
                print(f"🔧 DeepSeek请求调用 {len(message.tool_calls)} 个工具")
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # 调用MCP工具
                    tool_result = await self.call_mcp_tool(tool_name, tool_args)
                    
                    # 将工具结果添加到对话历史
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call.model_dump()]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # 获取DeepSeek对工具结果的最终回复
                final_response = self.deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages
                )
                
                response_text = final_response.choices[0].message.content
            
            print(f"🎯 DeepSeek最终回复: {response_text}")
            return response_text
            
        except Exception as e:
            error_msg = f"DeepSeek调用出错: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            print("🔌 已断开MCP连接")


if __name__ == "__main__":
    print("🌟 DeepSeek + MCP 集成示例")
    print("=" * 50)
    print("📋 功能特性:")
    print("✅ DeepSeek API集成")
    print("✅ MCP工具调用")
    print("✅ Function Calling支持")
    print("✅ 中文对话优化")
    print("=" * 50)
    
    # 环境检查
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("\n⚠️ 环境设置指南：")
        print("1. 获取DeepSeek API密钥: https://platform.deepseek.com/")
        print("2. 设置环境变量: export DEEPSEEK_API_KEY=your_api_key")
        print("3. 安装依赖: pip install openai mcp")
        print("4. 启动MCP服务器: python server.py")
        print("5. 运行此示例")
    else:
        print(f"\n✅ 检测到DeepSeek API密钥，可以开始测试")
        print("💡 要运行完整演示，请确保MCP服务器已启动")
