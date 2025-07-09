#!/usr/bin/env python3
"""
LLM 调用 MCP 的最佳实践指南
展示标准化的集成套路和关键步骤
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

# MCP 相关导入
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LLM 相关导入（示例）
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


@dataclass
class MCPTool:
    """MCP 工具的统一表示"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    

class LLMProvider(ABC):
    """LLM 提供商的抽象基类"""
    
    @abstractmethod
    def convert_tools(self, mcp_tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """将 MCP 工具格式转换为特定 LLM 的格式"""
        pass
    
    @abstractmethod
    async def call_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用工具调用 LLM"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI/DeepSeek 格式提供商"""
    
    def convert_tools(self, mcp_tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """转换为 OpenAI function calling 格式"""
        return [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
        } for tool in mcp_tools]
    
    async def call_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 实际实现省略，返回示例
        return {
            "tool_calls": [{
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "calculator",
                    "arguments": '{"operation": "add", "a": 5, "b": 3}'
                }
            }]
        }


class AnthropicProvider(LLMProvider):
    """Anthropic Claude 格式提供商"""
    
    def convert_tools(self, mcp_tools: List[MCPTool]) -> List[Dict[str, Any]]:
        """转换为 Claude tool use 格式"""
        return [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        } for tool in mcp_tools]
    
    async def call_with_tools(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 实际实现省略，返回示例
        return {
            "tool_use": {
                "name": "calculator",
                "input": {"operation": "add", "a": 5, "b": 3}
            }
        }


class MCPBestPractices:
    """LLM 调用 MCP 的最佳实践实现"""
    
    def __init__(self, server_command: str = "python", server_args: List[str] = ["server.py"]):
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args
        )
        self.session: Optional[ClientSession] = None
        self.available_tools: List[MCPTool] = []
        self.available_resources = []
        self.available_prompts = []
    
    async def demonstrate_best_practices(self):
        """演示 LLM 调用 MCP 的最佳实践"""
        print("🚀 LLM 调用 MCP 的最佳实践指南")
        print("=" * 80)
        
        # 1. 连接和初始化
        await self._demonstrate_connection()
        
        # 2. 能力发现
        await self._demonstrate_capability_discovery()
        
        # 3. 工具格式转换
        await self._demonstrate_tool_conversion()
        
        # 4. 标准调用流程
        await self._demonstrate_standard_flow()
        
        # 5. 高级模式
        await self._demonstrate_advanced_patterns()
        
        # 6. 错误处理
        await self._demonstrate_error_handling()
        
        # 7. 性能优化
        await self._demonstrate_performance_optimization()
    
    async def _demonstrate_connection(self):
        """步骤 1: 连接和初始化"""
        print("\n📡 步骤 1: 连接和初始化")
        print("-" * 40)
        
        print("最佳实践：")
        print("• 使用上下文管理器确保资源清理")
        print("• 初始化时进行健康检查")
        print("• 设置合理的超时时间")
        
        print("\n示例代码：")
        print("""
async with stdio_client(self.server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # 初始化会话
        await session.initialize()
        
        # 健康检查（可选）
        try:
            tools = await session.list_tools()
            print(f"✅ MCP 服务器正常，发现 {len(tools.tools)} 个工具")
        except Exception as e:
            print(f"❌ MCP 服务器异常: {e}")
        """)
    
    async def _demonstrate_capability_discovery(self):
        """步骤 2: 能力发现"""
        print("\n🔍 步骤 2: 能力发现")
        print("-" * 40)
        
        print("最佳实践：")
        print("• 启动时一次性获取所有能力")
        print("• 缓存能力信息，避免重复查询")
        print("• 动态构建 LLM 的系统提示")
        
        print("\n核心实现：")
        print("""
class MCPCapabilityManager:
    def __init__(self):
        self.tools = {}
        self.resources = {}
        self.prompts = {}
    
    async def discover_capabilities(self, session):
        # 并行获取所有能力
        tools_task = session.list_tools()
        resources_task = session.list_resources()
        prompts_task = session.list_prompts()
        
        tools, resources, prompts = await asyncio.gather(
            tools_task, resources_task, prompts_task
        )
        
        # 构建索引
        self.tools = {t.name: t for t in tools.tools}
        self.resources = {r.uri: r for r in resources.resources}
        self.prompts = {p.name: p for p in prompts.prompts}
        
    def build_system_prompt(self):
        prompt = "你可以使用以下 MCP 功能：\\n\\n"
        
        # 工具列表
        prompt += "🔧 可用工具：\\n"
        for name, tool in self.tools.items():
            prompt += f"- {name}: {tool.description}\\n"
        
        # 资源列表
        if self.resources:
            prompt += "\\n📄 可用资源：\\n"
            for uri, resource in self.resources.items():
                prompt += f"- {uri}: {resource.description}\\n"
        
        return prompt
        """)
    
    async def _demonstrate_tool_conversion(self):
        """步骤 3: 工具格式转换"""
        print("\n🔄 步骤 3: 工具格式转换")
        print("-" * 40)
        
        print("最佳实践：")
        print("• 为每个 LLM 提供商实现转换器")
        print("• 保持 MCP schema 的完整性")
        print("• 处理枚举、约束等特殊情况")
        
        print("\n转换示例：")
        print("""
# MCP 原始格式
mcp_tool = {
    "name": "weather",
    "description": "获取天气信息",
    "inputSchema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["city"]
    }
}

# OpenAI 格式
openai_tool = {
    "type": "function",
    "function": {
        "name": "weather",
        "description": "获取天气信息",
        "parameters": mcp_tool["inputSchema"]  # 直接使用
    }
}

# Anthropic 格式
claude_tool = {
    "name": "weather",
    "description": "获取天气信息",
    "input_schema": mcp_tool["inputSchema"]  # 字段名不同
}
        """)
    
    async def _demonstrate_standard_flow(self):
        """步骤 4: 标准调用流程"""
        print("\n🎯 步骤 4: 标准调用流程")
        print("-" * 40)
        
        print("标准套路（6 步）：")
        print("""
async def process_user_request(self, user_message: str) -> str:
    # 1. 准备消息和工具
    messages = [
        {"role": "system", "content": self.system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # 2. 第一次 LLM 调用（工具选择）
    llm_response = await self.llm.call_with_tools(
        messages=messages,
        tools=self.converted_tools
    )
    
    # 3. 解析工具调用请求
    if has_tool_calls(llm_response):
        tool_results = []
        
        for tool_call in llm_response.tool_calls:
            # 4. 执行 MCP 工具调用
            result = await self.mcp_session.call_tool(
                name=tool_call.name,
                arguments=json.loads(tool_call.arguments)
            )
            
            # 5. 收集工具结果
            tool_results.append({
                "tool_call_id": tool_call.id,
                "content": extract_content(result)
            })
        
        # 6. 第二次 LLM 调用（生成最终回复）
        messages.extend([
            {"role": "assistant", "tool_calls": llm_response.tool_calls},
            {"role": "tool", "content": tool_results}
        ])
        
        final_response = await self.llm.call(messages)
        return final_response.content
    
    return llm_response.content
        """)
    
    async def _demonstrate_advanced_patterns(self):
        """步骤 5: 高级模式"""
        print("\n🎨 步骤 5: 高级模式")
        print("-" * 40)
        
        print("1️⃣ 流式响应处理：")
        print("""
async def stream_with_tools(self, user_message: str):
    # 工具调用部分不能流式
    tool_response = await self.get_tool_calls(user_message)
    
    if tool_response.has_tools:
        # 执行工具
        tool_results = await self.execute_tools(tool_response)
        
        # 流式生成最终回复
        async for chunk in self.llm.stream_with_context(tool_results):
            yield chunk
    else:
        # 直接流式回复
        async for chunk in self.llm.stream(user_message):
            yield chunk
        """)
        
        print("\n2️⃣ 并行工具调用：")
        print("""
# 多个独立工具可以并行调用
tool_tasks = []
for tool_call in llm_response.tool_calls:
    task = self.mcp_session.call_tool(
        tool_call.name,
        json.loads(tool_call.arguments)
    )
    tool_tasks.append(task)

# 并行执行
results = await asyncio.gather(*tool_tasks)
        """)
        
        print("\n3️⃣ 工具链式调用：")
        print("""
# 支持工具结果作为下一个工具的输入
async def chain_tools(self, tool_chain: List[Dict]):
    result = None
    for tool_spec in tool_chain:
        # 使用上一个结果更新参数
        if result and "use_previous_result" in tool_spec:
            tool_spec["arguments"].update({"input": result})
        
        result = await self.mcp_session.call_tool(
            tool_spec["name"],
            tool_spec["arguments"]
        )
    return result
        """)
    
    async def _demonstrate_error_handling(self):
        """步骤 6: 错误处理"""
        print("\n⚠️ 步骤 6: 错误处理")
        print("-" * 40)
        
        print("最佳实践：")
        print("""
async def safe_tool_call(self, name: str, arguments: Dict) -> Dict:
    try:
        result = await self.mcp_session.call_tool(name, arguments)
        return {"success": True, "content": result}
    
    except ValidationError as e:
        # MCP 参数验证失败
        return {
            "success": False,
            "error": "参数验证失败",
            "details": str(e)
        }
    
    except TimeoutError:
        # 工具执行超时
        return {
            "success": False,
            "error": "工具执行超时",
            "fallback": "请稍后重试"
        }
    
    except MCPError as e:
        # MCP 协议错误
        return {
            "success": False,
            "error": "MCP 通信错误",
            "should_retry": True
        }
    
    except Exception as e:
        # 未知错误
        logger.error(f"工具调用失败: {e}")
        return {
            "success": False,
            "error": "工具执行失败",
            "fallback": self.get_fallback_response(name)
        }
        """)
    
    async def _demonstrate_performance_optimization(self):
        """步骤 7: 性能优化"""
        print("\n⚡ 步骤 7: 性能优化")
        print("-" * 40)
        
        print("优化技巧：")
        print("""
1. 连接池管理：
   class MCPConnectionPool:
       def __init__(self, size=5):
           self.pool = asyncio.Queue(size)
           self.size = size
       
       async def get_session(self):
           # 从池中获取或创建新连接
           pass

2. 工具结果缓存：
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   async def cached_tool_call(tool_name: str, args_hash: str):
       # 对确定性工具使用缓存
       pass

3. 批量请求：
   # JSON-RPC 2.0 支持批量请求
   batch_request = [
       {"method": "tools/call", "params": {...}, "id": 1},
       {"method": "tools/call", "params": {...}, "id": 2}
   ]

4. 预加载常用资源：
   async def preload_resources(self):
       common_resources = ["config://settings", "data://cache"]
       tasks = [self.session.read_resource(r) for r in common_resources]
       await asyncio.gather(*tasks)
        """)


async def demonstrate_complete_flow():
    """演示完整的 LLM + MCP 集成流程"""
    print("\n📋 完整集成示例")
    print("=" * 80)
    
    print("""
class LLMMCPIntegration:
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
        self.mcp_client = MCPClient()
        self.capability_manager = MCPCapabilityManager()
    
    async def setup(self):
        # 1. 连接 MCP
        await self.mcp_client.connect()
        
        # 2. 发现能力
        await self.capability_manager.discover_capabilities(
            self.mcp_client.session
        )
        
        # 3. 准备 LLM
        self.system_prompt = self.capability_manager.build_system_prompt()
        self.tools = self.convert_tools_for_llm()
    
    async def chat(self, message: str) -> str:
        # 标准 6 步流程
        # 1. 准备消息
        # 2. LLM 工具选择
        # 3. 解析工具调用
        # 4. 执行 MCP 工具
        # 5. 收集结果
        # 6. 生成最终回复
        pass
    
    async def cleanup(self):
        await self.mcp_client.disconnect()

# 使用示例
async def main():
    integration = LLMMCPIntegration("openai")
    await integration.setup()
    
    response = await integration.chat("北京天气怎么样？")
    print(response)
    
    await integration.cleanup()
    """)


async def main():
    """主函数"""
    print("🌟 LLM 调用 MCP 的最佳实践和标准套路")
    print("展示如何优雅地集成 LLM 和 MCP")
    print()
    
    # 演示最佳实践
    best_practices = MCPBestPractices()
    await best_practices.demonstrate_best_practices()
    
    # 演示完整流程
    await demonstrate_complete_flow()
    
    print("\n" + "=" * 80)
    print("✅ 最佳实践总结")
    print("\n🎯 核心套路（6步）：")
    print("1. 连接 MCP 服务器并初始化")
    print("2. 发现并缓存所有能力")
    print("3. 转换工具格式适配 LLM")
    print("4. LLM 分析并选择工具")
    print("5. 执行 MCP 工具调用")
    print("6. 整合结果生成回复")
    
    print("\n💡 关键要点：")
    print("• 使用上下文管理器管理连接")
    print("• 缓存能力信息避免重复查询")
    print("• 为不同 LLM 实现格式转换器")
    print("• 支持并行和链式工具调用")
    print("• 完善的错误处理和降级策略")
    print("• 性能优化（连接池、缓存等）")


if __name__ == "__main__":
    asyncio.run(main())