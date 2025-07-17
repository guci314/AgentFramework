#!/usr/bin/env python3
"""
测试AgentBase的reset方法
验证reset方法能正确清空内存，同时保留系统消息和受保护的消息
"""

import sys
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent_base import AgentBase

def test_agent_reset():
    """测试AgentBase的reset方法"""
    print("🧪 测试 AgentBase.reset() 方法")
    print("=" * 60)
    
    # 创建一个模拟的LLM（不会真正调用API）
    class MockLLM:
        def invoke(self, messages):
            class MockResponse:
                content = "模拟响应"
            return MockResponse()
        
        def stream(self, messages):
            return []
    
    # 1. 创建带系统消息的智能体
    print("\n1️⃣ 创建智能体并初始化")
    llm = MockLLM()
    agent = AgentBase(llm=llm, system_message="你是一个助手")
    
    # 验证初始状态
    print(f"   初始内存长度: {len(agent.memory)}")
    print(f"   初始系统消息: {agent.memory[0].content if agent.memory else 'None'}")
    assert len(agent.memory) == 1
    assert isinstance(agent.memory[0], SystemMessage)
    assert agent.memory[0].protected == True
    
    # 2. 加载知识（会被保护）
    print("\n2️⃣ 加载知识")
    agent.loadKnowledge("这是重要的知识")
    print(f"   内存长度: {len(agent.memory)}")
    print(f"   知识消息内容: {agent.memory[1].content}")
    assert len(agent.memory) == 3  # SystemMessage + HumanMessage + AIMessage
    
    # 3. 添加普通对话
    print("\n3️⃣ 添加普通对话")
    # 直接添加消息来模拟对话（避免调用真实的LLM）
    agent.memory.append(HumanMessage("用户对话1"))
    agent.memory.append(AIMessage("AI响应1"))
    agent.memory.append(HumanMessage("用户对话2"))
    agent.memory.append(AIMessage("AI响应2"))
    
    print(f"   添加对话后内存长度: {len(agent.memory)}")
    print("   内存内容:")
    for i, msg in enumerate(agent.memory):
        protected = getattr(msg, 'protected', False)
        print(f"     [{i}] {type(msg).__name__}: {msg.content[:30]}... (protected={protected})")
    
    assert len(agent.memory) == 7
    
    # 4. 测试reset方法
    print("\n4️⃣ 执行reset()")
    agent.reset()
    
    print(f"   reset后内存长度: {len(agent.memory)}")
    print("   保留的消息:")
    for i, msg in enumerate(agent.memory):
        protected = getattr(msg, 'protected', False)
        print(f"     [{i}] {type(msg).__name__}: {msg.content[:30]}... (protected={protected})")
    
    # 验证结果
    assert len(agent.memory) == 3  # 只保留了系统消息和loadKnowledge的消息
    assert isinstance(agent.memory[0], SystemMessage)
    assert isinstance(agent.memory[1], HumanMessage) and agent.memory[1].protected
    assert isinstance(agent.memory[2], AIMessage) and agent.memory[2].protected
    assert agent.memory_overloaded == False
    
    # 5. 测试空内存情况
    print("\n5️⃣ 测试空内存情况")
    agent2 = AgentBase(llm=llm)  # 没有系统消息
    agent2.memory.append(HumanMessage("普通消息"))
    print(f"   reset前内存长度: {len(agent2.memory)}")
    agent2.reset()
    print(f"   reset后内存长度: {len(agent2.memory)}")
    assert len(agent2.memory) == 0
    
    # 6. 测试带memory_overloaded标志的情况
    print("\n6️⃣ 测试memory_overloaded标志重置")
    agent.memory_overloaded = True
    print(f"   reset前memory_overloaded: {agent.memory_overloaded}")
    agent.reset()
    print(f"   reset后memory_overloaded: {agent.memory_overloaded}")
    assert agent.memory_overloaded == False
    
    print("\n✅ 所有测试通过！")
    print("\n📊 测试总结:")
    print("   ✓ reset()正确保留了系统消息")
    print("   ✓ reset()正确保留了受保护的消息")
    print("   ✓ reset()正确清除了普通对话消息")
    print("   ✓ reset()正确重置了memory_overloaded标志")
    print("   ✓ reset()在空内存情况下正常工作")

if __name__ == "__main__":
    try:
        test_agent_reset()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()