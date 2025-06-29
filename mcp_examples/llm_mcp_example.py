#!/usr/bin/env python3
"""
语言模型调用 MCP 的完整示例
展示如何将语言模型与 MCP 服务器集成
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional
import anthropic
import openai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """MCP 客户端封装"""
    
    def __init__(self, server_command: List[str]):
        self.server_command = server_command
        self.session: Optional[ClientSession] = None
        self.available_tools = []
        self.available_resources = []
        self.available_prompts = []
    
    async def connect(self):
        """连接到 MCP 服务器"""
        print(f"连接到 MCP 服务器: {' '.join(self.server_command)}")
        
        server_params = StdioServerParameters(
            command=self.server_command[0],
            args=self.server_command[1:] if len(self.server_command) > 1 else []
        )
        
        self.session = await stdio_client(server_params)
        
        # 初始化连接
        await self.session.initialize()
        
        # 获取可用工具、资源和提示
        await self.refresh_capabilities()
        
        print(f"✅ 成功连接到 MCP 服务器")
        print(f"📋 可用工具: {len(self.available_tools)}")
        print(f"📁 可用资源: {len(self.available_resources)}")  
        print(f"📝 可用提示: {len(self.available_prompts)}")
    
    async def refresh_capabilities(self):
        """刷新服务器能力"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        # 获取工具列表
        tools_result = await self.session.list_tools()
        self.available_tools = tools_result.tools
        
        # 获取资源列表
        try:
            resources_result = await self.session.list_resources()
            self.available_resources = resources_result.resources
        except:
            self.available_resources = []
        
        # 获取提示列表
        try:
            prompts_result = await self.session.list_prompts()
            self.available_prompts = prompts_result.prompts
        except:
            self.available_prompts = []
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """调用 MCP 工具"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        print(f"🔧 调用工具: {name}")
        print(f"📝 参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}")
        
        result = await self.session.call_tool(name, arguments)
        
        # 提取文本内容
        content_parts = []
        for content in result.content:
            if hasattr(content, 'text'):
                content_parts.append(content.text)
            else:
                content_parts.append(str(content))
        
        response = "\n".join(content_parts)
        print(f"✅ 工具响应: {response}")
        return response
    
    async def read_resource(self, uri: str) -> str:
        """读取 MCP 资源"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        print(f"📁 读取资源: {uri}")
        result = await self.session.read_resource(uri)
        
        content = ""
        for item in result.contents:
            if hasattr(item, 'text'):
                content += item.text
            else:
                content += str(item)
        
        print(f"✅ 资源内容长度: {len(content)} 字符")
        return content
    
    async def get_prompt(self, name: str, arguments: Dict[str, str]) -> str:
        """获取提示模板"""
        if not self.session:
            raise RuntimeError("未连接到服务器")
        
        print(f"📝 获取提示: {name}")
        result = await self.session.get_prompt(name, arguments)
        
        # 提取提示内容
        prompt_parts = []
        for message in result.messages:
            if hasattr(message.content, 'text'):
                prompt_parts.append(message.content.text)
            else:
                prompt_parts.append(str(message.content))
        
        prompt = "\n".join(prompt_parts)
        print(f"✅ 提示模板长度: {len(prompt)} 字符")
        return prompt
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """获取适用于语言模型的工具定义"""
        tools = []
        for tool in self.available_tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        return tools
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            print("🔌 已断开 MCP 连接")

class LLMWithMCP:
    """集成了 MCP 的语言模型"""
    
    def __init__(self, mcp_client: MCPClient, llm_type: str = "anthropic"):
        self.mcp_client = mcp_client
        self.llm_type = llm_type
        
        # 初始化语言模型客户端
        if llm_type == "anthropic":
            self.anthropic_client = anthropic.Anthropic(
                api_key="your-anthropic-api-key"  # 替换为实际API密钥
            )
        elif llm_type == "openai":
            self.openai_client = openai.OpenAI(
                api_key="your-openai-api-key"  # 替换为实际API密钥
            )
    
    async def chat_with_tools(self, user_message: str, system_prompt: str = None) -> str:
        """与语言模型对话，支持工具调用"""
        
        # 构建系统提示
        if system_prompt is None:
            system_prompt = """你是一个智能助手，可以使用多种工具来帮助用户。

可用的 MCP 工具：
"""
            for tool in self.mcp_client.available_tools:
                system_prompt += f"- {tool.name}: {tool.description}\n"
            
            system_prompt += "\n请根据用户需求选择合适的工具。"
        
        # 获取工具定义
        tools = self.mcp_client.get_tools_for_llm()
        
        print(f"🤖 发送消息给 {self.llm_type.upper()}")
        print(f"💬 用户消息: {user_message}")
        
        if self.llm_type == "anthropic":
            return await self._chat_anthropic(user_message, system_prompt, tools)
        elif self.llm_type == "openai":
            return await self._chat_openai(user_message, system_prompt, tools)
        else:
            raise ValueError(f"不支持的语言模型类型: {self.llm_type}")
    
    async def _chat_anthropic(self, user_message: str, system_prompt: str, tools: List[Dict]) -> str:
        """使用 Anthropic Claude 进行对话"""
        # 转换工具格式为 Claude 格式
        claude_tools = []
        for tool in tools:
            claude_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            })
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=claude_tools
            )
            
            # 处理响应
            response_text = ""
            
            for content in response.content:
                if content.type == "text":
                    response_text += content.text
                elif content.type == "tool_use":
                    # 执行工具调用
                    tool_name = content.name
                    tool_input = content.input
                    
                    print(f"🔧 Claude 请求调用工具: {tool_name}")
                    
                    # 调用 MCP 工具
                    tool_result = await self.mcp_client.call_tool(tool_name, tool_input)
                    
                    # 将结果添加到响应中
                    response_text += f"\n\n[工具调用结果]\n{tool_result}"
            
            return response_text
            
        except Exception as e:
            return f"Claude 调用出错: {str(e)}"
    
    async def _chat_openai(self, user_message: str, system_prompt: str, tools: List[Dict]) -> str:
        """使用 OpenAI GPT 进行对话"""
        # 转换工具格式为 OpenAI 格式
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                tools=openai_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            response_text = message.content or ""
            
            # 处理工具调用
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 GPT 请求调用工具: {tool_name}")
                    
                    # 调用 MCP 工具
                    tool_result = await self.mcp_client.call_tool(tool_name, tool_args)
                    
                    # 将结果添加到响应中
                    response_text += f"\n\n[工具调用结果]\n{tool_result}"
            
            return response_text
            
        except Exception as e:
            return f"OpenAI 调用出错: {str(e)}"

async def demo_llm_mcp_integration():
    """演示语言模型与 MCP 的集成"""
    
    print("=" * 60)
    print("🚀 语言模型 + MCP 集成演示")
    print("=" * 60)
    
    # 1. 启动 MCP 客户端
    mcp_client = MCPClient(["python", "mcp_example/server.py"])
    
    try:
        await mcp_client.connect()
        
        # 2. 创建集成了 MCP 的语言模型
        # 注意：需要提供真实的 API 密钥
        llm = LLMWithMCP(mcp_client, llm_type="anthropic")  # 或 "openai"
        
        # 3. 演示对话场景
        test_scenarios = [
            "帮我计算 15 + 27 等于多少",
            "请将结果存储到数据库中，键名为 'calculation_result'",
            "现在告诉我数据库中有什么数据",
            "帮我分析一下文本 'Hello MCP World' 的字符数和单词数",
            "获取当前时间"
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 场景 {i}: {scenario}")
            print("-" * 40)
            
            try:
                # 模拟调用（因为需要真实的 API 密钥）
                print("🤖 [模拟] 语言模型分析请求...")
                
                # 直接调用 MCP 工具演示
                if "计算" in scenario:
                    result = await mcp_client.call_tool("add", {"a": 15, "b": 27})
                elif "存储" in scenario:
                    result = await mcp_client.call_tool("add", {"a": 42, "b": 0})  # 假设结果是42
                    print(f"💾 存储结果: calculation_result = {42}")
                elif "数据库" in scenario:
                    # 演示读取资源
                    print("📁 读取数据存储资源...")
                elif "分析文本" in scenario:
                    print("📝 分析文本内容...")
                elif "时间" in scenario:
                    print("⏰ 获取当前时间...")
                
                print(f"✅ 场景完成")
                
            except Exception as e:
                print(f"❌ 场景执行出错: {str(e)}")
            
            # 等待一下，让用户看清输出
            await asyncio.sleep(1)
        
        # 4. 演示资源访问
        print(f"\n📁 演示资源访问")
        print("-" * 40)
        
        for resource in mcp_client.available_resources:
            print(f"📄 资源: {resource.name} ({resource.uri})")
        
        # 5. 演示提示模板
        print(f"\n📝 演示提示模板")
        print("-" * 40)
        
        for prompt in mcp_client.available_prompts:
            print(f"📋 模板: {prompt.name} - {prompt.description}")
    
    except Exception as e:
        print(f"❌ 演示过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await mcp_client.close()
    
    print("\n🎉 演示完成！")

def create_simple_mcp_demo():
    """创建一个简化的 MCP 演示（不需要真实的语言模型 API）"""
    
    demo_code = '''
# 简化的 MCP 调用演示
import asyncio
import json

async def simple_mcp_demo():
    """简单的 MCP 工具调用演示"""
    
    # 模拟 MCP 工具调用
    tools_results = {
        "calculator": {
            "operation": "add",
            "a": 15,
            "b": 27,
            "result": "计算结果: 15 + 27 = 42"
        },
        "text_analysis": {
            "text": "Hello MCP World",
            "result": "字符数: 15, 单词数: 3"
        },
        "data_storage": {
            "action": "set",
            "key": "demo_key", 
            "value": "demo_value",
            "result": "已存储: demo_key = demo_value"
        }
    }
    
    print("🔧 MCP 工具调用演示:")
    for tool, data in tools_results.items():
        print(f"\\n工具: {tool}")
        print(f"参数: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"结果: {data['result']}")

# 运行演示
asyncio.run(simple_mcp_demo())
'''
    
    print("📝 简化版 MCP 演示代码:")
    print("-" * 40)
    print(demo_code)

if __name__ == "__main__":
    print("选择演示模式:")
    print("1. 完整演示 (需要 MCP 服务器)")
    print("2. 简化演示 (纯代码)")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        # 运行完整演示
        asyncio.run(demo_llm_mcp_integration())
    elif choice == "2":
        # 显示简化演示
        create_simple_mcp_demo()
    else:
        print("无效选择") 