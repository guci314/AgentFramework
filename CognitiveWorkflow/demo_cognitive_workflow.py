# -*- coding: utf-8 -*-
"""
认知工作流系统演示

展示真正的认知工作流如何运作：
1. 动态导航而非静态流程图
2. 三角色协作
3. 状态满足性检查
4. 自适应和自修复能力

作者：Claude  
日期：2024-12-21
"""

import logging
import sys
from typing import Dict, Any
from pythonTask import Agent, llm_deepseek, StatefulExecutor
from cognitive_workflow import (
    CognitiveWorkflowEngine, CognitiveTask, TaskPhase, TaskStatus, GlobalState
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def create_mock_agents() -> Dict[str, Agent]:
    """创建模拟智能体用于演示"""
    
    # 创建代码专家
    coder = Agent(
        llm=llm_deepseek
    )
    coder.api_specification='''
    代码专家，擅长编写、调试和优化代码。
    '''
    
    # 创建测试专家
    tester = Agent(
        llm=llm_deepseek
    )
    tester.api_specification='''
    测试专家，擅长编写测试用例和验证代码质量。
    '''
    
    # 创建分析师
    analyst = Agent(
        llm=llm_deepseek
    )
    analyst.api_specification='''
    分析师，擅长需求分析和文档整理。
    '''
    
    return {
        "coder": coder,
        "tester": tester,
        "analyst": analyst
    }

def demo_simple_calculator():
    """演示：简单计算器开发 - 认知工作流vs传统工作流的对比"""
    
    print("🧠 === 认知工作流演示：智能计算器开发 ===")
    print()
    
    # 创建智能体
    agents = create_mock_agents()
    
    # 初始化认知工作流引擎
    workflow_engine = CognitiveWorkflowEngine(
        llm=llm_deepseek,
        agents=agents,
        max_iterations=20,
        enable_auto_recovery=True
    )
    
    # 定义高层次目标 - 用户只需提供这个
    goal = """
    开发一个简单的python hello world程序
    """
    
    print(f"🎯 目标: {goal}")
    print()
    print("🚀 启动认知工作流引擎...")
    print("=" * 60)
    
    try:
        # 执行认知工作流
        result_summary = workflow_engine.execute_cognitive_workflow(goal)
        
        print()
        print("=" * 60)
        print("📊 工作流执行摘要:")
        print(f"  总迭代次数: {result_summary['total_iterations']}")
        print(f"  总任务数: {result_summary['total_tasks']}")
        print(f"  已完成: {result_summary['completed_tasks']}")
        print(f"  失败: {result_summary['failed_tasks']}")
        print(f"  待处理: {result_summary['pending_tasks']}")
        print(f"  成功率: {result_summary['success_rate']:.2%}")
        print(f"  最终状态: {result_summary['final_state']}")
        
        # 显示任务状态报告
        print()
        print("📋 详细任务报告:")
        print(workflow_engine.get_task_status_report())
        
        return result_summary
        
    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        return None

def demo_comparison_with_traditional():
    """对比演示：认知工作流 vs 传统工作流"""
    
    print()
    print("🔍 === 认知工作流 vs 传统工作流对比 ===")
    print()
    
    print("【传统工作流的问题】")
    print("1. 静态流程图：所有分支和循环必须预先定义")
    print("2. 固定依赖关系：step2必须等step1完成，无法动态调整")  
    print("3. 缺乏自适应能力：无法处理预料之外的情况")
    print("4. 角色职责混乱：规划、决策、执行混在一起")
    print()
    
    print("【认知工作流的优势】")
    print("1. 动态导航：流程图在执行中构建，而非预先固化")
    print("2. 状态满足性检查：基于自然语言先决条件，灵活判断可执行性")
    print("3. 三角色分离：规划者、决策者、执行者各司其职")
    print("4. 自我修复：失败时能动态生成修复任务")
    print("5. 计划修正：决策者可以动态添加、删除、修改任务")
    print()
    
    print("【核心区别】")
    print("传统方式: 用户 → 静态流程图 → 顺序执行")
    print("认知方式: 用户 → 规划者(任务列表) → 决策者(动态选择) → 执行者(纯执行)")
    print()

def demo_key_concepts():
    """演示认知工作流的核心概念"""
    
    print()
    print("🎓 === 认知工作流核心概念演示 ===")
    print()
    
    # 创建示例任务展示先决条件
    print("【先决条件 vs 依赖关系】")
    print()
    
    # 传统方式
    print("传统依赖关系：")
    print("  task1: dependencies: []")
    print("  task2: dependencies: [task1]")
    print("  task3: dependencies: [task2]")
    print("  → 固定的线性执行顺序")
    print()
    
    # 认知工作流方式
    print("认知工作流先决条件：")
    print("  task1: precondition: '用户已提供需求描述'")
    print("  task2: precondition: '基础代码结构已创建'")
    print("  task3: precondition: '代码已通过基本测试'")
    print("  → 基于状态的动态执行")
    print()
    
    print("【三大角色职责】")
    print()
    print("1. 规划者 (CognitivePlanner):")
    print("   - 发散性思考，生成包含所有可能性的任务列表")
    print("   - 为每个任务定义自然语言先决条件")
    print("   - 能生成错误修复任务")
    print()
    
    print("2. 决策者 (CognitiveDecider):")
    print("   - 状态满足性检查：判断哪些任务可执行")
    print("   - 认知导航：从多个可执行任务中智能选择")
    print("   - 动态计划修正：添加、删除、修改任务")
    print()
    
    print("3. 执行者 (CognitiveExecutor):")
    print("   - 纯粹的执行单元，不关心流程控制")
    print("   - 专注于可靠地完成分配的任务")
    print()

def demo_state_satisfiability():
    """演示状态满足性检查机制"""
    
    print()
    print("🔬 === 状态满足性检查演示 ===")
    print()
    
    # 创建全局状态示例
    global_state = GlobalState(current_state="用户已提供计算器开发需求，正在等待需求分析完成")
    global_state.context_variables = {
        "user_requirement": "开发Python计算器",
        "project_status": "初始化",
        "code_files": []
    }
    
    print("当前全局状态:")
    print(f"  主状态: {global_state.current_state}")
    print(f"  上下文变量: {global_state.context_variables}")
    print()
    
    # 示例任务及其先决条件
    example_tasks = [
        ("需求分析", "用户已提供初始需求"),
        ("编写代码", "需求分析已完成，明确了功能规格"),
        ("编写测试", "基础代码已实现"),
        ("代码审查", "代码和测试都已完成"),
        ("部署发布", "所有测试通过，代码质量达标")
    ]
    
    print("任务可执行性分析:")
    for task_name, precondition in example_tasks:
        # 这里简化演示逻辑
        if "用户已提供" in precondition:
            executable = "✅ 可执行"
            confidence = "0.85"
        else:
            executable = "❌ 不可执行"
            confidence = "0.15"
            
        print(f"  {task_name}:")
        print(f"    先决条件: {precondition}")
        print(f"    状态: {executable} (置信度: {confidence})")
        print()

def main():
    """主演示函数"""
    
    print("🧠 认知工作流系统演示")
    print("基于认知工作流核心理念的全新实现")
    print()
    
    try:
        # 1. 核心概念演示
        # demo_key_concepts()
        
        # 2. 状态满足性检查演示
        # demo_state_satisfiability()
        
        # 3. 对比演示
        # demo_comparison_with_traditional()
        
        # 4. 实际工作流演示
        # input("\n按回车键开始实际工作流演示...")
        result = demo_simple_calculator()
        
        if result:
            print()
            print("✅ 认知工作流演示完成！")
            print()
            print("🎉 总结:")
            print("- 成功展示了动态导航能力")
            print("- 验证了三角色协作机制")  
            print("- 演示了状态满足性检查")
            print("- 体现了自适应执行特性")
        else:
            print("❌ 演示过程中遇到问题")
            
    except KeyboardInterrupt:
        print("\n\n用户中断演示")
    except Exception as e:
        logger.error(f"演示失败: {e}")
        
    print("\n感谢使用认知工作流系统演示！")

if __name__ == "__main__":
    main()