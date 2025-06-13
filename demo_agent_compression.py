#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示Agent消息压缩功能的脚本
"""

import os
from agent_base import AgentBase, reduce_memory_decorator_compress
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DemoAgent(AgentBase):
    """演示用的Agent类，带有消息压缩功能"""
    
    @reduce_memory_decorator_compress(max_tokens=2000)  # 设置较低的token限制以触发压缩
    def chat_with_compression(self, message: str):
        """带有消息压缩功能的聊天方法"""
        # 添加用户消息到记忆中
        self.memory.append(HumanMessage(content=message))
        
        # 生成模拟回复（当LLM不可用时）
        if not self.llm:
            # 创建足够长的回复以触发压缩机制
            long_reply = (
                f"收到消息: {message}. 当前处于模拟模式，API连接失败。"
                "此回复设计为足够长以触发消息压缩机制。" * 30
            )
            self.memory.append(AIMessage(content=long_reply))
            return long_reply
        
        # 调用LLM生成回复
        try:
            response = self.llm.invoke(self.memory)
            self.memory.append(AIMessage(content=response.content))
            return response.content
        except Exception as e:
            error_msg = f"生成回复时出错: {str(e)}"
            self.memory.append(AIMessage(content=error_msg))
            return error_msg

def demo_compression():
    """演示压缩功能"""
    print("🚀 开始演示Agent消息压缩功能...\n")
    
    # 创建演示Agent
    try:
        # 尝试使用实际的LLM（如果有API key）
        llm = ChatOpenAI(
            temperature=0,
            model="google/gemini-2.0-flash-001", 
            base_url='https://openrouter.ai/api/v1',
            api_key=os.getenv('OPENROUTER_API_KEY')
        )
        print("✅ 成功连接到语言模型")
    except Exception as e:
        print(f"⚠️  无法连接到语言模型，使用模拟模式: {e}")
        llm = None
    
    # 初始化Agent
    agent = DemoAgent(
        llm=llm,
        system_message="你是一个专业的销售数据分析助手，擅长分析各种销售相关的问题。"
    )
    
    print(f"📊 初始memory状态: {len(agent.memory)} 条消息\n")
    
    # 模拟一系列对话以积累足够的消息触发压缩
    conversation_steps = [
        "你好，我是新手用户，请问你能帮我分析销售数据吗？",
        "我有一个CSV文件，里面包含了过去一年的销售记录",
        "数据包括了销售日期、产品名称、销售地区、销售人员和销售金额",
        "请问我应该如何开始分析这些数据？",
        "我特别想了解哪个地区的销售表现最好",
        "还想知道哪个产品最受欢迎",
        "能否帮我制定一个详细的分析计划？",
        "分析完成后，我希望能生成一份专业的报告",
        "报告需要包含图表和详细的数据解释",
        "最后，请给我一些提高销售的建议",
        "这些建议要基于数据分析的结果",
        "请开始执行分析任务吧"
    ]
    
    print("💬 开始模拟对话...\n")
    
    for i, message in enumerate(conversation_steps, 1):
        print(f"👤 用户 [{i:2d}/12]: {message}")
        
        # 显示调用前的消息数量
        print(f"📊 调用前memory: {len(agent.memory)} 条消息")
        
        # 调用带压缩功能的聊天方法
        response = agent.chat_with_compression(message)
        
        # 显示调用后的消息数量
        print(f"📊 调用后memory: {len(agent.memory)} 条消息")
        print(f"🤖 AI回复: {response[:100]}{'...' if len(response) > 100 else ''}")
        
        # 显示是否发生了压缩
        if hasattr(agent, 'memory_overloaded') and agent.memory_overloaded:
            print("🔄 检测到消息压缩发生!")
        
        print("-" * 80)
    
    print(f"\n✅ 演示完成!")
    print(f"📈 最终统计:")
    print(f"   - 最终memory消息数: {len(agent.memory)} 条")
    print(f"   - 是否发生过压缩: {'是' if hasattr(agent, 'memory_overloaded') and agent.memory_overloaded else '否'}")
    
    # 显示最终的memory结构
    print(f"\n🔍 最终memory结构:")
    for i, msg in enumerate(agent.memory):
        msg_type = type(msg).__name__
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        protected = "🔒" if hasattr(msg, 'protected') and msg.protected else "📝"
        print(f"   [{i+1:2d}] {protected} {msg_type}: {content_preview}")

if __name__ == "__main__":
    demo_compression() 
