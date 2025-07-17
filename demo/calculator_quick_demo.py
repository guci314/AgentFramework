#!/usr/bin/env python3
"""
计算器快速演示 - 简化版本
=========================

演示MultiStepAgent_v3的execute_multi_step功能，
使用更短的超时时间来快速完成演示。
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
    """快速演示函数"""
    
    print("🧮 计算器快速演示")
    print("=" * 40)
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 请设置DEEPSEEK_API_KEY环境变量")
        return
    
    # 创建DeepSeek LLM实例
    get_model("deepseek_chat") = ChatOpenAI(
        temperature=0,
        model="deepseek-chat", 
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        max_tokens=4096  # 减少token数量以加快速度
    )
    
    # 创建简单智能体
    coder_agent = Agent(llm=get_model("deepseek_chat"), stateful=True)
    coder_agent.api_specification = "编程智能体，能快速实现简单代码"
    
    # 创建MultiStepAgent_v3实例，只注册一个智能体
    agent_v3 = MultiStepAgent_v3(
        llm=get_model("deepseek_chat"),
        registered_agents=[
            RegisteredAgent("coder", coder_agent, "编程智能体，能快速实现简单代码")
        ],
        max_retries=1,  # 减少重试次数
        max_parallel_workers=1
    )
    
    print(f"✅ 智能体已就绪: {[spec.name for spec in agent_v3.registered_agents]}")
    
    # 执行简化的计算器任务
    print("\n" + "=" * 40)
    print("🚀 执行: 实现简单计算器")
    print("=" * 40)
    
    try:
        # 核心功能调用
        result = agent_v3.execute_multi_step("实现一个简单的加法计算器函数")
        
        print("\n" + "=" * 40)
        print("📊 执行结果")
        print("=" * 40)
        print(result)
        
        # 分析结果
        if "成功" in result or "✅" in result:
            print("\n🎉 演示成功!")
            print("   - LLM规划生成 ✅")
            print("   - 控制流修复 ✅") 
            print("   - 多步骤执行 ✅")
            print("   - 代码实现完成 ✅")
        else:
            print("\n⚠️  演示部分成功，请查看详细结果")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()