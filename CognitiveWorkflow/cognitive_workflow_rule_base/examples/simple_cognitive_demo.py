#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的CognitiveAgent演示

专注于核心功能展示，避免复杂的工作流问题。
适合快速了解CognitiveAgent包装器的基本使用方法。

Author: Claude Code Assistant
Date: 2025-06-29
"""

import sys
import os

# 添加项目根目录和CognitiveWorkflow目录到路径，以便导入模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
cognitive_workflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(cognitive_workflow_dir)

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base.application.cognitive_workflow_agent_wrapper import CognitiveAgent

def main():
    """主演示函数"""
    print("🚀 简化的CognitiveAgent演示")
    print("=" * 50)
    
    # 1. 创建基础Agent
    print("📝 步骤1: 创建基础Agent")
    base_agent = Agent(llm=llm_deepseek)
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
        ("计算2+2", "简单计算"),
        ("创建一个Web应用", "复杂项目开发")
    ]
    
    for instruction, description in test_instructions:
        instruction_type, execution_mode = cognitive_agent.classify_instruction(instruction)
        print(f"📋 {description}")
        print(f"   指令: '{instruction}'")
        print(f"   分类: {instruction_type} | {execution_mode}")
        print()
    
    # 4. 测试不同类型的执行
    print("⚡ 步骤4: 智能执行演示")
    
    # 信息性指令
    print("💬 信息性指令测试:")
    try:
        result1 = cognitive_agent.execute_instruction_syn("什么是Python？")
        print(f"✅ 执行成功，结果类型: {type(result1).__name__}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 单步骤指令
    print("\n⚡ 单步骤指令测试:")
    try:
        result2 = cognitive_agent.execute_instruction_syn("计算10*5的结果")
        print(f"✅ 执行成功，结果类型: {type(result2).__name__}")
        if hasattr(result2, 'return_value'):
            print(f"📄 返回值: {result2.return_value}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 简单的多步骤指令（避免文件操作）
    print("\n🧠 多步骤指令测试:")
    try:
        result3 = cognitive_agent.execute_instruction_syn("创建一个简单的计算器函数")
        print(f"✅ 执行成功，结果类型: {type(result3).__name__}")
        if hasattr(result3, 'final_message'):
            print(f"📄 最终消息: {result3.final_message[:200]}...")
        elif hasattr(result3, 'is_successful'):
            print(f"📄 工作流成功: {result3.is_successful}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    # 5. 性能统计
    print("\n📊 步骤5: 性能统计")
    stats = cognitive_agent.get_performance_stats()
    print(f"🔢 总分类次数: {stats['classification_stats']['total_classifications']}")
    print(f"💾 缓存大小: {stats['cache_info']['size']}")
    print(f"🔧 工作流引擎: {'正常' if stats['workflow_engine_status'] else '异常'}")
    
    print("\n🎉 CognitiveAgent演示完成！")

if __name__ == "__main__":
    main()