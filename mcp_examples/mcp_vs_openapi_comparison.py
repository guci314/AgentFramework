#!/usr/bin/env python3
"""
MCP vs REST/OpenAPI 对比演示
展示两种架构的差异和各自优势
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from multiprocessing import Process
import time

# ========== OpenAPI/REST 实现 ==========

app = FastAPI(title="Calculator API", version="1.0.0")

class CalculationRequest(BaseModel):
    operation: str
    a: float
    b: float

class CalculationResponse(BaseModel):
    result: float
    timestamp: str

@app.post("/calculate", response_model=CalculationResponse)
async def calculate(request: CalculationRequest):
    """执行数学计算"""
    if request.operation == "add":
        result = request.a + request.b
    elif request.operation == "multiply":
        result = request.a * request.b
    elif request.operation == "divide":
        if request.b == 0:
            raise HTTPException(status_code=400, detail="除数不能为零")
        result = request.a / request.b
    else:
        raise HTTPException(status_code=400, detail=f"不支持的操作: {request.operation}")
    
    return CalculationResponse(
        result=result,
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ========== MCP 实现（模拟）==========

class MCPComparison:
    """对比 MCP 和 REST/OpenAPI 的特性"""
    
    @staticmethod
    async def compare_features():
        """详细对比两种架构"""
        print("🔍 MCP vs REST/OpenAPI 深度对比")
        print("=" * 80)
        
        comparisons = [
            {
                "feature": "通信模型",
                "mcp": "双向流式通信 (stdio/websocket)\n• 持久连接\n• 服务器可主动推送\n• 低延迟",
                "rest": "请求-响应模式\n• 无状态\n• 客户端主动拉取\n• 每次请求建立新连接"
            },
            {
                "feature": "协议设计",
                "mcp": "JSON-RPC 2.0\n• 支持批量请求\n• 内置错误处理\n• 请求ID关联",
                "rest": "HTTP + JSON\n• 单个请求/响应\n• HTTP状态码\n• 无内置关联机制"
            },
            {
                "feature": "功能类型",
                "mcp": "三种原语：\n• Tools (函数调用)\n• Resources (数据访问)\n• Prompts (模板系统)",
                "rest": "主要是端点：\n• 通常只有API端点\n• 需要额外设计资源/模板"
            },
            {
                "feature": "会话管理",
                "mcp": "有状态会话\n• 持久化上下文\n• 会话级别认证\n• 支持长时间运行任务",
                "rest": "无状态设计\n• 每次请求携带认证\n• 需要额外机制管理状态"
            },
            {
                "feature": "适用场景",
                "mcp": "• AI Agent 工具集成\n• 需要双向通信\n• 长时间运行的任务\n• 本地工具调用",
                "rest": "• Web服务\n• 公开API\n• 简单的请求响应\n• 跨网络调用"
            }
        ]
        
        for comp in comparisons:
            print(f"\n📌 {comp['feature']}")
            print("-" * 40)
            print(f"MCP:\n{comp['mcp']}")
            print(f"\nREST/OpenAPI:\n{comp['rest']}")
    
    @staticmethod
    async def demonstrate_mcp_advantages():
        """演示 MCP 的独特优势"""
        print("\n\n🚀 MCP 独特优势演示")
        print("=" * 80)
        
        # 1. 双向通信优势
        print("\n1️⃣ 双向通信能力")
        print("-" * 40)
        print("MCP 场景：")
        print("• 服务器检测到数据更新，主动推送给客户端")
        print("• 长时间运行的任务可以实时报告进度")
        print("• 支持订阅模式，自动接收更新")
        print("\nREST 场景：")
        print("• 客户端必须轮询检查更新")
        print("• 长任务需要额外的进度查询端点")
        print("• WebSocket 需要额外实现")
        
        # 2. 统一接口优势
        print("\n2️⃣ 统一的工具生态")
        print("-" * 40)
        print("MCP 提供三种标准化原语：")
        print("```")
        print("// 工具调用")
        print("await session.call_tool('calculator', {operation: 'add', a: 1, b: 2})")
        print("\n// 资源访问")
        print("await session.read_resource('config://settings')")
        print("\n// 提示模板")
        print("await session.get_prompt('code_review', {language: 'python'})")
        print("```")
        print("\nREST 需要为每种功能设计不同的端点和模式")
        
        # 3. 本地集成优势
        print("\n3️⃣ 本地工具集成")
        print("-" * 40)
        print("MCP 优势：")
        print("• 通过 stdio 直接与本地进程通信")
        print("• 无需网络栈，延迟极低")
        print("• 适合集成本地开发工具")
        print("\nREST 限制：")
        print("• 必须通过 HTTP，即使是本地调用")
        print("• 需要处理端口占用、防火墙等问题")
        print("• 额外的序列化开销")
        
        # 4. AI 特化设计
        print("\n4️⃣ 为 AI 特化的设计")
        print("-" * 40)
        print("MCP 特性：")
        print("• Prompts 系统专为 LLM 设计")
        print("• 支持流式响应，适合生成式 AI")
        print("• 内置的上下文管理")
        print("\nREST 需要：")
        print("• 自行设计提示模板系统")
        print("• Server-Sent Events 或 WebSocket 实现流式")
        print("• 手动管理会话上下文")
    
    @staticmethod
    async def show_code_comparison():
        """展示代码层面的对比"""
        print("\n\n💻 代码实现对比")
        print("=" * 80)
        
        print("\n🔧 实现一个进度报告的长任务")
        print("-" * 40)
        
        print("\nMCP 实现（伪代码）：")
        print("```python")
        print("# 服务器端")
        print("@server.call_tool()")
        print("async def long_task(args):")
        print("    for i in range(100):")
        print("        # 直接推送进度")
        print("        await session.send_progress(f'Progress: {i}%')")
        print("        await process_step(i)")
        print("    return 'Task completed'")
        print("\n# 客户端")
        print("async with session:")
        print("    # 自动接收所有进度更新")
        print("    result = await session.call_tool('long_task', {})")
        print("```")
        
        print("\nREST 实现：")
        print("```python")
        print("# 服务器端")
        print("@app.post('/long-task')")
        print("async def start_long_task():")
        print("    task_id = start_background_task()")
        print("    return {'task_id': task_id}")
        print("\n@app.get('/task-status/{task_id}')")
        print("async def get_task_status(task_id: str):")
        print("    return {'progress': get_progress(task_id)}")
        print("\n# 客户端")
        print("task = await client.post('/long-task')")
        print("# 需要轮询检查进度")
        print("while True:")
        print("    status = await client.get(f'/task-status/{task.task_id}')")
        print("    if status.completed:")
        print("        break")
        print("    await asyncio.sleep(1)")
        print("```")
    
    @staticmethod
    async def show_use_case_recommendations():
        """展示使用场景建议"""
        print("\n\n🎯 使用场景建议")
        print("=" * 80)
        
        print("\n✅ 选择 MCP 的场景：")
        print("• 构建 AI Agent 的工具生态")
        print("• 需要本地工具集成（IDE、CLI 工具等）")
        print("• 需要双向实时通信")
        print("• 长时间运行的任务with进度报告")
        print("• 需要统一的工具/资源/提示管理")
        
        print("\n✅ 选择 REST/OpenAPI 的场景：")
        print("• 构建公开的 Web API")
        print("• 需要广泛的客户端支持")
        print("• 简单的无状态服务")
        print("• 需要 CDN 缓存")
        print("• 团队已熟悉 REST 生态")
        
        print("\n🤝 混合使用：")
        print("• MCP 用于 AI Agent 内部工具")
        print("• REST API 用于对外服务")
        print("• 通过适配器连接两种生态")


async def run_rest_comparison():
    """运行 REST API 比较演示"""
    # 启动 FastAPI 服务器
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
    
    server_process = Process(target=run_server)
    server_process.start()
    
    # 等待服务器启动
    await asyncio.sleep(2)
    
    try:
        print("\n📊 REST API 调用演示")
        print("-" * 40)
        
        async with aiohttp.ClientSession() as session:
            # 调用计算 API
            url = "http://127.0.0.1:8000/calculate"
            
            # 成功调用
            data = {"operation": "add", "a": 10, "b": 5}
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"REST 调用: {data}")
                print(f"响应: {result}")
            
            # 错误处理
            data = {"operation": "divide", "a": 10, "b": 0}
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error = await response.json()
                    print(f"\nREST 错误处理: {error['detail']}")
    
    finally:
        server_process.terminate()
        server_process.join()


async def main():
    """主函数"""
    print("🌟 MCP vs REST/OpenAPI 深度对比分析")
    print("展示两种架构的设计理念和适用场景")
    print()
    
    # 1. 特性对比
    await MCPComparison.compare_features()
    
    # 2. MCP 优势演示
    await MCPComparison.demonstrate_mcp_advantages()
    
    # 3. 代码对比
    await MCPComparison.show_code_comparison()
    
    # 4. REST API 演示
    await run_rest_comparison()
    
    # 5. 使用建议
    await MCPComparison.show_use_case_recommendations()
    
    print("\n" + "=" * 80)
    print("✅ 对比分析完成！")
    print("\n💡 核心洞察：")
    print("• MCP 是为 AI Agent 生态特别设计的协议")
    print("• REST/OpenAPI 更适合传统 Web 服务")
    print("• 两者各有优势，可以根据场景选择或混合使用")


if __name__ == "__main__":
    asyncio.run(main())