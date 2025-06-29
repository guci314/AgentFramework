# -*- coding: utf-8 -*-
"""
基础使用示例

展示如何使用产生式规则认知工作流系统的基本功能。
"""

import sys
import os
from pathlib import Path
# from blue_print_patch_simple import add_blue_print_to_method



# 添加父目录到路径，以便导入模块
sys.path.append(str(Path(__file__).parent.parent.parent))

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base import create_production_rule_system
from cognitive_workflow_rule_base.cognitive_workflow_agent_wrapper import CognitiveAgent

# from cognitive_workflow_rule_base.services.rule_generation_service import RuleGenerationService
# add_blue_print_to_method('generate_rule_set',RuleGenerationService)
# from pythonTask import Agent
# add_blue_print_to_method('execute_sync',Agent)

selected_llm = llm_deepseek

def create_demo_agents():
    """创建演示用的智能体"""
    
    # 创建基础代码专家Agent
    base_coder = Agent(llm=selected_llm)
    base_coder.loadKnowledge('unittest的测试结果在标准错误流而不是标准输出流')
    base_coder.api_specification = '''
    代码专家，擅长编写、调试和优化代码。
    支持多种编程语言，特别是Python。
    '''
    
    # 创建基础测试专家Agent
    base_tester = Agent(llm=selected_llm)
    base_tester.loadKnowledge('unittest的测试结果在标准错误流而不是标准输出流')
    base_tester.api_specification = '''
    测试专家，擅长编写测试用例和验证代码质量。
    熟悉各种测试框架和测试策略。
    '''
    
    # 使用CognitiveAgent包装基础Agent，获得智能分类和路由能力
    coder = CognitiveAgent(
        base_agent=base_coder,
        enable_auto_recovery=True,
        classification_cache_size=50
    )
    
    tester = CognitiveAgent(
        base_agent=base_tester,
        enable_auto_recovery=True,
        classification_cache_size=50
    )
    
    print(f"✅ 创建CognitiveAgent包装器:")
    print(f"   - coder: {coder}")
    print(f"   - tester: {tester}")
    
    return {
        "coder": coder,
        "tester": tester,
    }


def basic_example():
    """基础使用示例"""
    
    print("🔧 产生式规则认知工作流基础示例")
    print("="*50)
    
    # 1. 创建智能体
    print("1. 创建智能体...")
    agents = create_demo_agents()
    print(f"   创建了 {len(agents)} 个智能体: {list(agents.keys())}")
    
    # 2. 初始化工作流系统
    print("\n2. 初始化产生式规则工作流系统...")
    workflow_engine = create_production_rule_system(
        llm=selected_llm,
        agents=agents,
        enable_auto_recovery=True
    )
    print("   系统初始化完成")
    
    # 3. 定义目标
    goal = "创建一个简单的Python Hello World程序,打印hello world 789 ， 文件保存在hello_world.py"
    print(f"\n3. 执行目标: {goal}")
    
    # 4. 执行工作流
    print("\n4. 开始执行工作流...")
    try:
        result = workflow_engine.execute_goal(goal)
        
        # 5. 显示结果
        print("\n5. 执行结果:")
        print(f"   成功: {'是' if result.is_successful else '否'}")
        print(f"   总迭代次数: {result.total_iterations}")
        print(f"   最终状态: {result.final_state}")
        print(f"   完成消息: {result.final_message}")
        
        if result.execution_metrics:
            print(f"   成功率: {result.execution_metrics.success_rate:.2%}")
            print(f"   平均执行时间: {result.execution_metrics.average_execution_time:.2f}秒")
        
        return result
        
    except Exception as e:
        print(f"   执行失败: {e}")
        return None


def show_system_status(workflow_engine):
    """显示系统状态"""
    
    print("\n📊 系统状态信息:")
    print("-"*30)
    
    try:
        # 获取执行指标
        metrics = workflow_engine.get_execution_metrics()
        print(f"执行状态: {metrics.get('execution_status', 'unknown')}")
        print(f"当前目标: {metrics.get('current_goal', 'none')}")
        
        current_state = metrics.get('current_state')
        if current_state:
            print(f"当前状态: {current_state.get('description', 'unknown')}")
            print(f"迭代次数: {current_state.get('iteration_count', 0)}")
            print(f"目标达成: {'是' if current_state.get('goal_achieved', False) else '否'}")
        
        # 获取工作流历史
        history = workflow_engine.get_workflow_history()
        if history:
            print(f"\n历史记录 (最近5条):")
            for i, entry in enumerate(history[-5:], 1):
                # Use iteration_count instead of timestamp (timestamp removed for LLM caching)
                iteration_info = f"iter_{entry.get('iteration_count', i)}"
                description = entry.get('description', entry.get('state', 'No description'))[:100]
                print(f"  {i}. [{iteration_info}] {description}...")
        
    except Exception as e:
        print(f"获取系统状态失败: {e}")


def demonstrate_rule_based_execution():
    """演示基于规则的执行过程"""
    
    print("\n🧠 产生式规则执行演示")
    print("="*40)
    
    # 创建智能体
    agents = create_demo_agents()
    
    # 初始化系统
    workflow_engine = create_production_rule_system(
        llm=selected_llm,
        agents=agents,
        enable_auto_recovery=True
    )
    
    #4. 生成使用说明文档，使用markdown格式，文件保存在calculator.md
    # 定义一个更复杂的目标
    complex_goal = """
    开发一个简单的计算器程序，要求：
    1. 实现加减乘除四个基本运算
    2. 编写完整的单元测试
    3. 运行测试，确保测试通过
    4. 文件保存在calculator.py
    """
    
    print(f"目标: {complex_goal}")
    print("\n开始执行...")
    
    try:
        result = workflow_engine.execute_goal(complex_goal)
        
        print(f"\n执行完成:")
        print(f"结果: {'成功' if result.is_successful else '失败'}")
        print(f"迭代次数: {result.total_iterations}")
        print(f"最终状态: {result.final_state[:200]}...")
        
        # 显示详细的执行指标
        if result.execution_metrics:
            metrics = result.execution_metrics
            print(f"\n执行指标:")
            print(f"  总规则执行次数: {metrics.total_rules_executed}")
            print(f"  成功执行次数: {metrics.successful_executions}")
            print(f"  失败执行次数: {metrics.failed_executions}")
            print(f"  成功率: {metrics.success_rate:.2%}")
            print(f"  平均执行时间: {metrics.average_execution_time:.2f}秒")
        
        # 显示系统状态
        show_system_status(workflow_engine)
        
    except Exception as e:
        print(f"执行失败: {e}")


def main():
    """主函数"""
    
    print("🚀 产生式规则认知工作流系统演示")
    print("基于IF-THEN自然语言规则的智能工作流")
    print("="*60)
    
    try:
        # 基础示例
        print("\n【示例1: 基础使用】")
        result1 = basic_example()
        
        if result1:
            print("\n✅ 基础示例执行成功")
        else:
            print("\n❌ 基础示例执行失败")
        
        # # 规则执行演示
        # print("\n\n【示例2: 复杂规则执行】")
        # demonstrate_rule_based_execution()
        
        # print("\n🎉 演示完成!")
        # print("\n核心特性展示:")
        # print("✓ 自然语言IF-THEN规则")
        # print("✓ 语义驱动的规则匹配")
        # print("✓ 动态规则生成和修正")
        # print("✓ 自适应错误恢复")
        # print("✓ 端到端自然语言处理")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n\n演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
