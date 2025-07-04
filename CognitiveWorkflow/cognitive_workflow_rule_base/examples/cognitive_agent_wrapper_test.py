# -*- coding: utf-8 -*-
"""
CognitiveAgent包装器测试套件

完整的测试示例，包含功能测试、分类准确性测试和使用场景演示。
用于验证基于产生式规则的Agent包装器的各项功能。

Author: Claude Code Assistant  
Date: 2025-06-29
Version: 1.0.0
"""

import sys
import os
from typing import Any

# 添加项目根目录和CognitiveWorkflow目录到路径，以便导入模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
cognitive_workflow_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(cognitive_workflow_dir)

# 导入必要的模块
try:
    from pythonTask import Agent, llm_deepseek
    from cognitive_workflow_rule_base.application.cognitive_workflow_agent_wrapper import CognitiveAgent
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保项目路径正确，并且所有依赖模块可用")
    sys.exit(1)


def test_agent_wrapper():
    """测试Agent包装器的核心功能"""
    print("🚀 开始测试基于产生式规则的Agent包装器")
    print("=" * 80)
    
    # 1. 创建基础Agent
    print("📝 步骤1: 创建基础Agent")
    try:
        base_agent = Agent(llm=llm_deepseek)
        print(f"✅ 基础Agent创建成功: {type(base_agent).__name__}")
    except Exception as e:
        print(f"❌ 创建基础Agent失败: {e}")
        return
    
    # 2. 创建认知工作流包装器
    print("\n🧠 步骤2: 创建认知工作流包装器")
    try:
        cognitive_agent = CognitiveAgent(
            base_agent=base_agent,
            enable_auto_recovery=True,
            classification_cache_size=50
        )
        print(f"✅ 认知包装器创建成功: {cognitive_agent}")
    except Exception as e:
        print(f"❌ 创建认知包装器失败: {e}")
        return
    
    # 3. 测试指令分类功能
    print("\n🔍 步骤3: 测试智能指令分类")
    test_instructions = [
        ("什么是机器学习？", "信息性指令"),
        ("解释Python装饰器的原理", "信息性指令"),
        ("打印hello world", "单步骤指令"),
        ("计算1+1的结果", "单步骤指令"),
        ("开发一个Web应用", "多步骤指令"),
        ("创建包含测试的计算器程序", "多步骤指令")
    ]
    
    for instruction, expected_type in test_instructions:
        try:
            instruction_type, execution_mode = cognitive_agent.classify_instruction(instruction)
            print(f"📋 指令: '{instruction}'")
            print(f"   分类: {instruction_type} | {execution_mode}")
            print(f"   预期: {expected_type}")
            print()
        except Exception as e:
            print(f"❌ 分类失败: {instruction} -> {e}")
    
    # 4. 测试同步执行
    print("\n⚡ 步骤4: 测试同步智能执行")
    
    test_cases = [
        "什么是Python？",  # 信息性指令
        "打印当前时间",     # 单步骤指令（如果基础Agent支持）
    ]
    
    for instruction in test_cases:
        print(f"🎯 执行指令: '{instruction}'")
        try:
            result = cognitive_agent.execute_instruction_syn(instruction)
            print(f"✅ 执行成功")
            print(f"   结果类型: {type(result).__name__}")
            if hasattr(result, 'return_value'):
                print(f"   返回值: {result.return_value}")
            elif hasattr(result, 'final_message'):
                print(f"   最终消息: {result.final_message}")
            else:
                print(f"   结果: {str(result)[:200]}...")
            print()
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            print()
    
    # 5. 测试流式执行
    print("\n🔄 步骤5: 测试流式智能执行")
    
    test_instruction = "Python有哪些主要特点？"
    print(f"🎯 流式执行: '{test_instruction}'")
    
    try:
        results = list(cognitive_agent.execute_instruction_stream(test_instruction))
        
        print("📊 流式执行过程:")
        for i, result in enumerate(results):
            if i < len(results) - 1:
                print(f"   步骤 {i+1}: {result}")
            else:
                print(f"   最终结果: {type(result).__name__}")
        print()
    except Exception as e:
        print(f"❌ 流式执行失败: {e}")
        print()
    
    # 6. 显示性能统计
    print("\n📊 步骤6: 性能统计信息")
    try:
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
        
        print(f"\n🔧 工作流引擎状态: {'正常' if stats['workflow_engine_status'] else '异常'}")
        
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
    
    print("\n" + "=" * 80)
    print("🎉 Agent包装器测试完成！")


def test_classification_accuracy():
    """测试指令分类准确性"""
    print("\n🎯 专项测试: 指令分类准确性")
    print("-" * 60)
    
    # 创建简化的测试环境
    try:
        base_agent = Agent(llm=llm_deepseek)
        cognitive_agent = CognitiveAgent(base_agent)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 分类测试用例
    test_cases = [
        # 信息性指令
        ("什么是深度学习？", "informational", "chat"),
        ("解释RESTful API的概念", "informational", "chat"),
        ("Python和Java有什么区别？", "informational", "chat"),
        ("介绍React框架的特点", "informational", "chat"),
        
        # 单步骤执行指令
        ("打印hello world", "executable", "single_step"),
        ("计算2的10次方", "executable", "single_step"),
        ("显示当前目录", "executable", "single_step"),
        ("创建一个空文件test.txt", "executable", "single_step"),
        
        # 多步骤执行指令
        ("开发一个博客系统", "executable", "multi_step"),
        ("创建包含单元测试的计算器", "executable", "multi_step"),
        ("实现用户认证系统", "executable", "multi_step"),
        ("读取配置文件并执行相应操作", "executable", "multi_step"),
    ]
    
    correct_classifications = 0
    total_tests = len(test_cases)
    
    for instruction, expected_type, expected_mode in test_cases:
        try:
            actual_type, actual_mode = cognitive_agent.classify_instruction(instruction)
            
            is_correct = (actual_type == expected_type and actual_mode == expected_mode)
            if is_correct:
                correct_classifications += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"{status} '{instruction}'")
            print(f"     预期: {expected_type}|{expected_mode}")
            print(f"     实际: {actual_type}|{actual_mode}")
            print()
            
        except Exception as e:
            print(f"❌ 分类异常: '{instruction}' -> {e}")
            print()
    
    accuracy = (correct_classifications / total_tests) * 100
    print(f"📊 分类准确率: {correct_classifications}/{total_tests} ({accuracy:.1f}%)")
    
    if accuracy >= 80:
        print("🎉 分类准确率优秀！")
    elif accuracy >= 60:
        print("👍 分类准确率良好")
    else:
        print("⚠️ 分类准确率需要改进")


def demo_usage_scenarios():
    """演示实际使用场景"""
    print("\n💡 使用场景演示")
    print("-" * 60)
    
    try:
        base_agent = Agent(llm=llm_deepseek)
        cognitive_agent = CognitiveAgent(base_agent)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    scenarios = [
        {
            "name": "学习咨询场景",
            "instruction": "什么是微服务架构？",
            "description": "用户询问技术概念"
        },
        {
            "name": "快速任务场景", 
            "instruction": "显示Python版本",
            "description": "简单的系统查询任务"
        },
        {
            "name": "复杂项目场景",
            "instruction": "设计并实现一个简单的聊天机器人",
            "description": "需要多步骤规划的复杂任务"
        }
    ]
    
    for scenario in scenarios:
        print(f"🎭 场景: {scenario['name']}")
        print(f"   描述: {scenario['description']}")
        print(f"   指令: '{scenario['instruction']}'")
        
        try:
            # 分类预测
            instruction_type, execution_mode = cognitive_agent.classify_instruction(scenario['instruction'])
            print(f"   分类: {instruction_type} | {execution_mode}")
            
            # 根据分类显示执行策略
            if instruction_type == "informational":
                print("   策略: 使用对话模式获取信息")
            elif execution_mode == "single_step":
                print("   策略: 直接执行简单任务")
            else:
                print("   策略: 启动认知工作流进行多步骤规划")
            
        except Exception as e:
            print(f"   ❌ 处理异常: {e}")
        
        print()


if __name__ == "__main__":
    """主函数：运行所有测试"""
    try:
        # 主要功能测试
        test_agent_wrapper()
        
        # 分类准确性测试
        test_classification_accuracy()
        
        # 使用场景演示
        demo_usage_scenarios()
        
        print("\n🎊 所有测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()