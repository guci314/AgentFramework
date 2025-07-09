#!/usr/bin/env python3
"""
AgentBase.reset() 方法的实际使用示例
展示如何在长对话后重置智能体内存，保持核心知识
"""

import os
from langchain_openai import ChatOpenAI
from agent_base import AgentBase

def example_reset_usage():
    """展示reset方法的实际使用场景"""
    print("🤖 AgentBase.reset() 实际使用示例")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('DEEPSEEK_API_KEY'):
        print("⚠️  未设置API密钥，使用模拟模式")
        # 模拟LLM
        class MockLLM:
            def invoke(self, messages):
                class MockResponse:
                    content = f"这是对'{messages[-1].content}'的回复"
                return MockResponse()
            
            def stream(self, messages):
                return []
        
        llm = MockLLM()
    else:
        # 使用真实的LLM
        if os.getenv('DEEPSEEK_API_KEY'):
            llm = ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                openai_api_base="https://api.deepseek.com",
                max_tokens=200,
                temperature=0.7
            )
            print("✅ 使用DeepSeek模型")
        else:
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                max_tokens=200,
                temperature=0.7
            )
            print("✅ 使用OpenAI模型")
    
    # 场景：客服智能体，需要保持产品知识但清除客户对话历史
    print("\n📋 场景：客服智能体")
    print("   - 需要记住产品知识")
    print("   - 每个客户会话后清除对话历史")
    
    # 1. 创建客服智能体
    print("\n1️⃣ 初始化客服智能体")
    agent = AgentBase(
        llm=llm,
        system_message="你是一个友好的客服助手，帮助客户解答产品相关问题。"
    )
    print(f"   初始内存消息数: {len(agent.memory)}")
    
    # 2. 加载产品知识（这些知识需要永久保留）
    print("\n2️⃣ 加载产品知识库")
    agent.loadKnowledge("""
    产品知识库：
    - 产品名称：智能家居控制系统
    - 价格：标准版 ¥999，专业版 ¥1999
    - 功能：支持语音控制、手机APP控制、定时任务、场景联动
    - 保修：标准版1年，专业版2年
    - 退换货：7天无理由退换
    """)
    print(f"   加载知识后内存消息数: {len(agent.memory)}")
    
    # 3. 第一个客户的对话
    print("\n3️⃣ 客户A的咨询")
    print("   客户A: 你们的产品支持语音控制吗？")
    response1 = agent.chat_sync("你们的产品支持语音控制吗？")
    print(f"   客服: {response1.return_value}")
    
    print("\n   客户A: 标准版和专业版有什么区别？")
    response2 = agent.chat_sync("标准版和专业版有什么区别？")
    print(f"   客服: {response2.return_value}")
    
    print(f"\n   当前内存消息数: {len(agent.memory)}")
    print("   内存内容概览:")
    for i, msg in enumerate(agent.memory[-4:]):  # 只显示最后4条
        msg_type = type(msg).__name__
        content_preview = msg.content[:50].replace('\n', ' ')
        print(f"     [{i}] {msg_type}: {content_preview}...")
    
    # 4. 客户会话结束，重置对话历史
    print("\n4️⃣ 客户A会话结束，重置对话历史")
    print("   执行 agent.reset()")
    agent.reset()
    print(f"   重置后内存消息数: {len(agent.memory)}")
    print("   保留的内容:")
    for i, msg in enumerate(agent.memory):
        msg_type = type(msg).__name__
        content_preview = msg.content[:50].replace('\n', ' ')
        print(f"     [{i}] {msg_type}: {content_preview}...")
    
    # 5. 新客户的对话
    print("\n5️⃣ 客户B的咨询（全新会话）")
    print("   客户B: 请问有什么优惠活动吗？")
    response3 = agent.chat_sync("请问有什么优惠活动吗？")
    print(f"   客服: {response3.return_value}")
    
    # 6. 验证知识保留
    print("\n6️⃣ 验证产品知识仍然保留")
    print("   客户B: 保修期是多久？")
    response4 = agent.chat_sync("保修期是多久？")
    print(f"   客服: {response4.return_value}")
    
    # 7. 总结
    print("\n📊 总结:")
    print("   ✓ reset()成功清除了客户A的对话历史")
    print("   ✓ reset()保留了系统消息和产品知识")
    print("   ✓ 新客户B获得了全新的对话体验")
    print("   ✓ 产品知识在reset后仍然可用")
    
    # 8. 内存管理建议
    print("\n💡 内存管理最佳实践:")
    print("   1. 使用loadKnowledge()加载需要长期保留的信息")
    print("   2. 在适当的时机调用reset()清理对话历史")
    print("   3. reset()自动保护系统消息和标记为protected的消息")
    print("   4. 适合场景：客服系统、多轮任务、隐私保护等")

if __name__ == "__main__":
    example_reset_usage()