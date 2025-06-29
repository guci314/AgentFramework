#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CognitiveAgent包装器演示

展示CognitiveAgent类的智能指令分类和执行路由功能。
这是一个完整的演示，展示了如何使用认知工作流包装器来增强基础Agent。

Author: Claude Code Assistant
Date: 2025-06-29
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from pythonTask import Agent, llm_deepseek, llm_gemini_2_5_pro_google
from cognitive_workflow_rule_base.cognitive_workflow_agent_wrapper import CognitiveAgent

def main():
    """主演示函数"""
    print("🚀 CognitiveAgent包装器完整演示")
    print("=" * 60)
    
    # 1. 创建基础Agent
    print("📝 步骤1: 创建基础Agent")
    base_agent = Agent(llm=llm_gemini_2_5_pro_google)
    print(f"✅ 基础Agent: {type(base_agent).__name__}")
    
    # 2. 创建CognitiveAgent
    print("\n🧠 步骤2: 创建CognitiveAgent")
    cognitive_agent = CognitiveAgent(
        base_agent=base_agent,
        enable_auto_recovery=True,
        classification_cache_size=50
    )
    print(f"✅ 认知Agent: {cognitive_agent}")
    
    # 3. 测试智能分类
    print("\n🔍 步骤3: 智能指令分类演示")
    test_instructions = [
        ("什么是机器学习？", "信息性查询"),
        ("print('Hello World')", "简单代码执行"), 
        ("开发一个博客系统", "复杂项目开发"),
        ("计算斐波那契数列前10项", "算法实现"),
        ("解释Python装饰器原理", "技术解释"),
        ("创建包含测试的Web API", "多步骤开发")
    ]
    
    for instruction, description in test_instructions:
        instruction_type, execution_mode = cognitive_agent.classify_instruction(instruction)
        print(f"📋 {description}")
        print(f"   指令: '{instruction}'")
        print(f"   分类: {instruction_type} | {execution_mode}")
        print()
    
    # 4. 测试智能执行
    print("⚡ 步骤4: 智能执行演示")
    
    # 信息性指令示例
    print("💬 信息性指令测试:")
    try:
        result1 = cognitive_agent.execute_instruction_syn("什么是Python？")
        print(f"✅ 执行成功，结果类型: {type(result1).__name__}")
        print(f"📄 内容摘要: {str(result1)[:100]}...")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 单步骤指令示例
    print("\n⚡ 单步骤指令测试:")
    try:
        result2 = cognitive_agent.execute_instruction_syn("打印hello world")
        print(f"✅ 执行成功，结果类型: {type(result2).__name__}")
        if hasattr(result2, 'return_value'):
            print(f"📄 返回值: {result2.return_value}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 多步骤指令示例 - 复杂任务
    print("\n🧠 多步骤指令测试 (认知工作流):")
    try:
        result3 = cognitive_agent.execute_instruction_syn("创建一个简单的计算器程序")
        print(f"✅ 执行成功，结果类型: {type(result3).__name__}")
        if hasattr(result3, 'final_message'):
            print(f"📄 最终消息: {result3.final_message}")
        elif hasattr(result3, 'is_successful'):
            print(f"📄 工作流成功: {result3.is_successful}")
            print(f"📄 执行步骤: {result3.total_iterations}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 5. 测试流式执行
    print("\n🔄 步骤5: 流式执行演示")
    test_instruction = "解释Python的主要特点"
    print(f"🎯 流式执行: '{test_instruction}'")
    
    try:
        print("📊 实时输出:")
        for update in cognitive_agent.execute_instruction_stream(test_instruction):
            if isinstance(update, str):
                print(f"   > {update[:80]}...")
            else:
                print(f"   [最终结果: {type(update).__name__}]")
                break
    except Exception as e:
        print(f"❌ 流式执行失败: {e}")
    
    # 6. 性能统计
    print("\n📊 步骤6: 性能统计")
    stats = cognitive_agent.get_performance_stats()
    
    print("🔢 分类统计:")
    print(f"   总分类次数: {stats['classification_stats']['total_classifications']}")
    print(f"   缓存命中次数: {stats['classification_stats']['cache_hits']}")
    print(f"   分类错误次数: {stats['classification_stats']['classification_errors']}")
    
    print("\n💾 缓存信息:")
    print(f"   缓存大小: {stats['cache_info']['size']}/{stats['cache_info']['max_size']}")
    print(f"   命中率: {stats['cache_info']['hit_rate_percent']}%")
    
    print("\n📈 执行分布:")
    for mode, percentage in stats['execution_distribution'].items():
        print(f"   {mode}: {percentage:.1f}%")
    
    print(f"\n🔧 工作流引擎: {'正常' if stats['workflow_engine_status'] else '异常'}")
    
    print("\n🎉 CognitiveAgent包装器演示完成！")

if __name__ == "__main__":
    main()