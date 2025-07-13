#!/usr/bin/env python3
"""
计算器静态工作流演示
=====================

演示MultiStepAgent_v3的基于LLM规划的execute_multi_step功能。
通过自然语言指令"实现一个计算器"自动生成并执行静态工作流。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from python_core import Agent
from langchain_openai import ChatOpenAI

def main():
    """主函数：演示计算器静态工作流"""
    
    print("🧮 计算器静态工作流演示")
    print("=" * 50)
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 请设置DEEPSEEK_API_KEY环境变量")
        print("   export DEEPSEEK_API_KEY='your_api_key_here'")
        return
    
    # 创建DeepSeek LLM实例
    print("🔧 初始化DeepSeek语言模型...")
    get_model("deepseek_chat") = ChatOpenAI(
        temperature=0,
        model="deepseek-chat", 
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        max_tokens=8192
    )
    
    # 创建专门的智能体
    print("🤖 创建专业智能体...")
    
    # 编程智能体
    coder_agent = Agent(llm=get_model("deepseek_chat"), stateful=True)
    coder_agent.api_specification = "专业编程智能体，擅长Python编程，能够编写高质量的代码，包括类设计、函数实现、错误处理等"
    
    # 测试智能体
    tester_agent = Agent(llm=get_model("deepseek_chat"), stateful=True) 
    tester_agent.api_specification = "专业测试智能体，擅长编写单元测试、集成测试，验证代码功能正确性，使用pytest框架"
    
    # 分析师智能体
    analyst_agent = Agent(llm=get_model("deepseek_chat"), stateful=True)
    analyst_agent.api_specification = "需求分析师智能体，擅长分析需求、设计架构、制定实现方案"
    
    # 创建MultiStepAgent_v3实例
    print("🏗️  构建MultiStepAgent_v3...")
    agent_v3 = MultiStepAgent_v3(
        llm=get_model("deepseek_chat"),
        registered_agents=[
            RegisteredAgent("coder", coder_agent, "专业编程智能体，擅长Python编程，能够编写高质量的代码"),
            RegisteredAgent("tester", tester_agent, "专业测试智能体，擅长编写单元测试，验证代码功能正确性"),
            RegisteredAgent("analyst", analyst_agent, "需求分析师智能体，擅长分析需求、设计架构、制定实现方案")
        ],
        max_retries=3,
        max_parallel_workers=2
    )
    
    print(f"✅ 智能体团队已就绪:")
    for spec in agent_v3.registered_agents:
        print(f"   - {spec.name}: {spec.description}")
    
    # 执行主要功能：计算器实现
    print("\n" + "=" * 50)
    print("🚀 开始执行: 实现一个计算器")
    print("=" * 50)
    
    try:
        # 这是核心功能调用
        prompt='''
        实现一个计算器类Calculator，保存到文件calculator.py中。
        编写测试用例，保存到文件test_calculator.py中。
        运行测试用例。
        如果测试用例失败，则修复代码，并重新运行测试用例。
        如果测试用例成功，则结束。
        '''
        result = agent_v3.execute_multi_step(prompt)
        
        print("\n" + "=" * 50)
        print("📊 执行结果")
        print("=" * 50)
        print(result)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        print(f"   错误类型: {type(e).__name__}")
        
        # 显示调试信息
        import traceback
        print(f"\n🔍 详细错误信息:")
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("✨ 演示完成")
    print("=" * 50)

if __name__ == "__main__":
    main()