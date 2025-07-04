#!/usr/bin/env python3
"""
简化的 MCP 调用演示
展示语言模型如何与 MCP 服务交互的核心概念
"""

import asyncio
import json
from typing import Dict, Any, List

class MockMCPServer:
    """模拟的 MCP 服务器，展示核心概念"""
    
    def __init__(self):
        self.data_store = {}
        self.call_history = []
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {
                "name": "calculator",
                "description": "执行基本数学运算",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["operation", "a", "b"]
                }
            },
            {
                "name": "data_manager", 
                "description": "管理键值对数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["set", "get", "list"]},
                        "key": {"type": "string"},
                        "value": {"type": "string"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "text_analyzer",
                "description": "分析文本内容",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "text": {"type": "string"},
                        "analysis_type": {"type": "string", "enum": ["count", "words", "summary"]}
                    },
                    "required": ["text", "analysis_type"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用 MCP 工具"""
        # 记录调用历史
        self.call_history.append({
            "tool": tool_name,
            "arguments": arguments,
            "timestamp": "2024-01-01 12:00:00"
        })
        
        print(f"🔧 [MCP服务器] 调用工具: {tool_name}")
        print(f"📝 [MCP服务器] 参数: {json.dumps(arguments, ensure_ascii=False)}")
        
        # 模拟工具执行
        if tool_name == "calculator":
            return await self._handle_calculator(arguments)
        elif tool_name == "data_manager":
            return await self._handle_data_manager(arguments)
        elif tool_name == "text_analyzer":
            return await self._handle_text_analyzer(arguments)
        else:
            return f"❌ 未知工具: {tool_name}"
    
    async def _handle_calculator(self, args: Dict[str, Any]) -> str:
        """处理计算器调用"""
        operation = args.get("operation")
        a = float(args.get("a", 0))
        b = float(args.get("b", 0))
        
        if operation == "add":
            result = a + b
            return f"计算结果: {a} + {b} = {result}"
        elif operation == "subtract":
            result = a - b
            return f"计算结果: {a} - {b} = {result}"
        elif operation == "multiply":
            result = a * b
            return f"计算结果: {a} × {b} = {result}"
        elif operation == "divide":
            if b == 0:
                return "❌ 错误: 除数不能为零"
            result = a / b
            return f"计算结果: {a} ÷ {b} = {result}"
        else:
            return f"❌ 不支持的运算: {operation}"
    
    async def _handle_data_manager(self, args: Dict[str, Any]) -> str:
        """处理数据管理调用"""
        action = args.get("action")
        key = args.get("key")
        value = args.get("value")
        
        if action == "set":
            self.data_store[key] = value
            return f"✅ 已存储: {key} = {value}"
        elif action == "get":
            stored_value = self.data_store.get(key, "未找到")
            return f"📄 {key} = {stored_value}"
        elif action == "list":
            if not self.data_store:
                return "📄 数据库为空"
            items = ", ".join([f"{k}={v}" for k, v in self.data_store.items()])
            return f"📄 存储的数据: {items}"
        else:
            return f"❌ 不支持的操作: {action}"
    
    async def _handle_text_analyzer(self, args: Dict[str, Any]) -> str:
        """处理文本分析调用"""
        text = args.get("text", "")
        analysis_type = args.get("analysis_type")
        
        if analysis_type == "count":
            return f"📊 字符数: {len(text)}"
        elif analysis_type == "words":
            word_count = len(text.split())
            return f"📊 单词数: {word_count}"
        elif analysis_type == "summary":
            return f"📊 文本摘要: 长度{len(text)}字符，{len(text.split())}个单词"
        else:
            return f"❌ 不支持的分析类型: {analysis_type}"

class MockLanguageModel:
    """模拟语言模型，展示如何与 MCP 集成"""
    
    def __init__(self, mcp_server: MockMCPServer):
        self.mcp_server = mcp_server
        self.available_tools = mcp_server.get_available_tools()
    
    async def process_request(self, user_message: str) -> str:
        """处理用户请求，模拟语言模型的推理过程"""
        
        print(f"\n🤖 [语言模型] 收到用户请求: {user_message}")
        print(f"🧠 [语言模型] 分析请求并选择合适的工具...")
        
        # 模拟语言模型的推理过程
        if "计算" in user_message or "+" in user_message or "加" in user_message:
            # 提取数字和运算（简化版）
            if "15" in user_message and "27" in user_message:
                tool_call = {
                    "name": "calculator",
                    "arguments": {"operation": "add", "a": 15, "b": 27}
                }
            else:
                tool_call = {
                    "name": "calculator", 
                    "arguments": {"operation": "add", "a": 10, "b": 20}
                }
        
        elif "存储" in user_message or "保存" in user_message:
            tool_call = {
                "name": "data_manager",
                "arguments": {"action": "set", "key": "calculation_result", "value": "42"}
            }
        
        elif "数据库" in user_message or "有什么数据" in user_message:
            tool_call = {
                "name": "data_manager",
                "arguments": {"action": "list"}
            }
        
        elif "分析" in user_message and "文本" in user_message:
            tool_call = {
                "name": "text_analyzer",
                "arguments": {"text": "Hello MCP World", "analysis_type": "summary"}
            }
        
        else:
            return "🤖 [语言模型] 抱歉，我无法理解您的请求。"
        
        # 调用选择的工具
        print(f"🔗 [语言模型] 调用工具: {tool_call['name']}")
        tool_result = await self.mcp_server.call_tool(
            tool_call["name"], 
            tool_call["arguments"]
        )
        
        # 生成最终响应
        response = f"🤖 [语言模型] 根据您的请求，我调用了 {tool_call['name']} 工具。\n"
        response += f"📋 工具执行结果: {tool_result}\n"
        response += f"💡 这就是您需要的答案！"
        
        return response

async def demonstrate_llm_mcp_interaction():
    """演示语言模型与 MCP 的交互过程"""
    
    print("=" * 70)
    print("🚀 语言模型 + MCP 交互演示")
    print("=" * 70)
    
    # 1. 创建 MCP 服务器
    mcp_server = MockMCPServer()
    print("✅ MCP 服务器已启动")
    
    # 2. 创建语言模型（连接到 MCP）
    llm = MockLanguageModel(mcp_server)
    print("✅ 语言模型已连接到 MCP 服务器")
    
    # 3. 显示可用工具
    print(f"\n📋 MCP 服务器提供的工具:")
    for i, tool in enumerate(llm.available_tools, 1):
        print(f"  {i}. {tool['name']}: {tool['description']}")
    
    # 4. 演示交互场景
    test_scenarios = [
        "帮我计算 15 + 27 等于多少？",
        "请将结果存储到数据库中",
        "现在告诉我数据库中有什么数据？", 
        "帮我分析一下文本内容",
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n" + "="*50)
        print(f"📝 场景 {i}: {scenario}")
        print("="*50)
        
        # 语言模型处理请求
        response = await llm.process_request(scenario)
        print(f"\n✅ 最终响应:\n{response}")
        
        # 稍微暂停一下
        await asyncio.sleep(0.5)
    
    # 5. 显示调用历史
    print(f"\n📊 MCP 工具调用历史:")
    for i, call in enumerate(mcp_server.call_history, 1):
        print(f"  {i}. {call['tool']} - {call['arguments']}")
    
    print(f"\n🎉 演示完成！")
    print(f"💡 这就是语言模型通过 MCP 调用工具的基本流程。")

def explain_mcp_vs_function_call():
    """解释 MCP 与传统 Function Call 的区别"""
    
    print("\n" + "="*60)
    print("📚 MCP vs 传统 Function Call 对比")
    print("="*60)
    
    comparison = {
        "传统 Function Call": {
            "架构": "直接调用模式",
            "标准化": "各厂商格式不同",
            "功能": "仅支持函数调用",
            "状态": "无状态",
            "示例": "OpenAI functions, Anthropic tools"
        },
        "MCP (Model Context Protocol)": {
            "架构": "客户端-服务器架构", 
            "标准化": "统一的协议标准",
            "功能": "工具+资源+提示+采样",
            "状态": "支持持久连接和状态",
            "示例": "本演示中的完整 MCP 实现"
        }
    }
    
    for approach, details in comparison.items():
        print(f"\n🔹 {approach}:")
        for key, value in details.items():
            print(f"  {key}: {value}")
    
    print(f"\n💡 结论: MCP 可以看作是**标准化的增强版 Function Call**")
    print(f"   它不仅统一了工具调用格式，还扩展了功能范围。")

if __name__ == "__main__":
    print("🎯 选择演示内容:")
    print("1. 完整交互演示")
    print("2. MCP vs Function Call 说明")
    print("3. 两者都要")
    
    try:
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == "1":
            asyncio.run(demonstrate_llm_mcp_interaction())
        elif choice == "2":
            explain_mcp_vs_function_call()
        elif choice == "3":
            asyncio.run(demonstrate_llm_mcp_integration())
            explain_mcp_vs_function_call()
        else:
            print("❌ 无效选择，运行默认演示...")
            asyncio.run(demonstrate_llm_mcp_interaction())
            
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"❌ 演示过程出错: {e}")
        import traceback
        traceback.print_exc() 