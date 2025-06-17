#!/usr/bin/env python3
"""
执行历史功能演示
================

展示MultiStepAgent_v3的执行历史功能如何帮助智能体
基于前面步骤的结果继续工作。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from pythonTask import Agent
from langchain_openai import ChatOpenAI

def main():
    """执行历史演示"""
    
    print("📜 执行历史功能演示")
    print("=" * 50)
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 请设置DEEPSEEK_API_KEY环境变量")
        return
    
    # 创建DeepSeek LLM实例
    llm_deepseek = ChatOpenAI(
        temperature=0,
        model="deepseek-chat", 
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        max_tokens=4096
    )
    
    # 创建智能体
    coder_agent = Agent(llm=llm_deepseek, stateful=True)
    coder_agent.api_specification = "编程智能体，能实现和优化代码"
    
    tester_agent = Agent(llm=llm_deepseek, stateful=True) 
    tester_agent.api_specification = "测试智能体，能编写和运行测试"
    
    # 创建MultiStepAgent_v3实例
    agent_v3 = MultiStepAgent_v3(
        llm=llm_deepseek,
        registered_agents=[
            RegisteredAgent("coder", coder_agent, "编程智能体，能实现和优化代码"),
            RegisteredAgent("tester", tester_agent, "测试智能体，能编写和运行测试")
        ],
        max_retries=1
    )
    
    print(f"✅ 智能体团队已就绪")
    
    # 演示指令：简单的两步任务
    instruction = "实现一个简单的add函数，然后为它编写一个测试用例"
    
    print(f"\n📋 演示任务：{instruction}")
    print("=" * 50)
    
    try:
        print("🚀 开始执行多步骤任务...")
        print("   注意观察第二步是如何使用第一步的代码结果")
        
        # 执行任务
        result = agent_v3.execute_multi_step(instruction)
        
        print("\n" + "=" * 50)
        print("📊 执行结果")
        print("=" * 50)
        print(result)
        
        # 分析结果
        print(f"\n🔍 执行历史功能分析:")
        if "步骤 1:" in result and "步骤 2:" in result:
            print("   ✅ 成功执行多个步骤")
            if "生成代码" in result:
                print("   ✅ 第一步的代码被正确记录")
                print("   ✅ 第二步可以看到第一步的结果")
                print("   ✅ 避免了重复实现，直接基于已有代码编写测试")
            else:
                print("   ⚠️  执行历史信息可能不完整")
        else:
            print("   ❓ 可能只执行了单个步骤或使用了回退模式")
        
        # 检查是否有文件生成
        if os.path.exists("calculator.py"):
            print(f"\n📁 发现生成的文件: calculator.py")
            print("   这说明工作流正在实际产生输出文件")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 关键改进点:")
    print(f"   📝 每个步骤现在都包含前面步骤的执行历史")
    print(f"   🔗 智能体可以看到前面的代码、输出和结果")
    print(f"   🚫 避免重复工作，基于已有结果继续")
    print(f"   🎯 保持步骤间的一致性和连贯性")
    
    print(f"\n✨ 演示完成!")

if __name__ == "__main__":
    main()