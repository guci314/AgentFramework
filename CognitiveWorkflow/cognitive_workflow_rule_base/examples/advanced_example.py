# -*- coding: utf-8 -*-
"""
高级使用示例

展示产生式规则认知工作流系统的高级功能，包括：
- 自定义规则生成
- 复杂工作流控制
- 状态监控和分析
- 错误恢复机制
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base import (
    create_production_rule_system,
    ProductionRule, AgentCapability, AgentRegistry,
    RulePhase, ExecutionStatus
)


def create_specialized_agents():
    """创建专业化的智能体"""
    
    # Python专家
    python_expert = Agent(llm=llm_deepseek)
    python_expert.api_specification = '''
    Python编程专家，精通：
    - Python语法和最佳实践
    - 面向对象编程和设计模式
    - 代码优化和性能调优
    - 第三方库集成
    '''
    
    # 测试工程师
    test_engineer = Agent(llm=llm_deepseek)
    test_engineer.api_specification = '''
    测试工程师，专长：
    - 单元测试和集成测试设计
    - 测试驱动开发(TDD)
    - 代码覆盖率分析
    - 性能测试和压力测试
    '''
    
    # 架构师
    architect = Agent(llm=llm_deepseek)
    architect.api_specification = '''
    软件架构师，擅长：
    - 系统架构设计
    - 技术方案评估
    - 代码审查和质量把控
    - 技术文档编写
    '''
    
    # DevOps工程师
    devops_engineer = Agent(llm=llm_deepseek)
    devops_engineer.api_specification = '''
    DevOps工程师，专业：
    - CI/CD流水线设计
    - 容器化和部署
    - 监控和日志分析
    - 自动化运维
    '''
    
    # 产品经理
    product_manager = Agent(llm=llm_deepseek)
    product_manager.api_specification = '''
    产品经理，负责：
    - 需求分析和产品规划
    - 用户体验设计
    - 项目协调和管理
    - 质量验收和发布决策
    '''
    
    return {
        "python_expert": python_expert,
        "test_engineer": test_engineer,
        "architect": architect,
        "devops_engineer": devops_engineer,
        "product_manager": product_manager
    }


def create_custom_agent_registry():
    """创建自定义智能体注册表"""
    
    registry = AgentRegistry()
    
    # 注册Python专家能力
    python_capability = AgentCapability(
        id="python_expert",
        name="Python编程专家",
        description="精通Python编程和最佳实践",
        supported_actions=["编写代码", "代码优化", "调试程序", "性能分析"],
        api_specification="Python编程专家，提供高质量的Python代码开发服务"
    )
    registry.register_capability(python_capability)
    
    # 注册测试工程师能力
    test_capability = AgentCapability(
        id="test_engineer",
        name="测试工程师",
        description="专业的软件测试和质量保证",
        supported_actions=["编写测试", "执行测试", "质量分析", "测试报告"],
        api_specification="测试工程师，提供全面的软件测试服务"
    )
    registry.register_capability(test_capability)
    
    # 注册架构师能力
    architect_capability = AgentCapability(
        id="architect",
        name="软件架构师",
        description="系统架构设计和技术方案制定",
        supported_actions=["架构设计", "技术评估", "代码审查", "文档编写"],
        api_specification="软件架构师，提供技术架构和方案设计服务"
    )
    registry.register_capability(architect_capability)
    
    return registry


def create_custom_rules():
    """创建自定义规则"""
    
    custom_rules = []
    
    # 需求分析规则
    requirement_rule = ProductionRule(
        id="req_analysis_001",
        name="需求分析和技术方案制定",
        condition="接收到新的开发需求且需要技术方案",
        action="分析需求的技术可行性，制定详细的技术实现方案，包括架构设计、技术选型和开发计划",
        agent_capability_id="architect",
        priority=95,
        phase=RulePhase.INFORMATION_GATHERING,
        expected_outcome="完整的技术方案文档，包括架构图、开发计划和风险评估"
    )
    custom_rules.append(requirement_rule)
    
    # 代码开发规则
    development_rule = ProductionRule(
        id="dev_impl_001",
        name="核心功能开发实现",
        condition="技术方案已确定且可以开始编码实现",
        action="根据技术方案实现核心功能代码，遵循最佳实践，确保代码质量和可维护性",
        agent_capability_id="python_expert",
        priority=85,
        phase=RulePhase.PROBLEM_SOLVING,
        expected_outcome="完整的功能实现代码，包括必要的注释和文档"
    )
    custom_rules.append(development_rule)
    
    # 测试开发规则
    testing_rule = ProductionRule(
        id="test_dev_001",
        name="测试用例开发和执行",
        condition="核心功能代码已完成且需要测试验证",
        action="编写全面的单元测试和集成测试，执行测试并生成测试报告",
        agent_capability_id="test_engineer",
        priority=80,
        phase=RulePhase.VERIFICATION,
        expected_outcome="完整的测试套件和测试报告，确保代码质量"
    )
    custom_rules.append(testing_rule)
    
    # 代码审查规则
    review_rule = ProductionRule(
        id="code_review_001", 
        name="代码质量审查",
        condition="代码和测试都已完成且需要质量审查",
        action="对代码进行全面审查，检查代码质量、安全性、性能和最佳实践符合性",
        agent_capability_id="architect",
        priority=75,
        phase=RulePhase.VERIFICATION,
        expected_outcome="代码审查报告和改进建议"
    )
    custom_rules.append(review_rule)
    
    return custom_rules


def advanced_workflow_control_demo():
    """高级工作流控制演示"""
    
    print("🎯 高级工作流控制演示")
    print("="*40)
    
    # 创建智能体和注册表
    agents = create_specialized_agents()
    agent_registry = create_custom_agent_registry()
    
    # 创建工作流系统
    workflow_engine = create_production_rule_system(
        llm=llm_deepseek,
        agents=agents,
        enable_auto_recovery=True
    )
    
    # 复杂的开发目标
    goal = """
    开发一个Web API服务，要求：
    1. 实现用户认证和授权
    2. 提供RESTful API接口
    3. 集成数据库操作
    4. 编写完整的测试套件
    5. 部署文档和运维指南
    6. 性能优化和安全加固
    """
    
    print(f"目标: {goal}")
    print("\n开始异步执行工作流...")
    
    # 启动异步执行
    success = workflow_engine.execute_goal_async(goal, agent_registry)
    
    if not success:
        print("❌ 异步执行启动失败")
        return
    
    print("✅ 异步执行已启动")
    
    # 监控执行过程
    try:
        monitor_execution_progress(workflow_engine)
    except KeyboardInterrupt:
        print("\n\n⏸️  用户请求停止执行")
        workflow_engine.stop_execution()
        
    # 获取最终结果
    result = workflow_engine.get_execution_result()
    if result:
        print(f"\n📊 最终结果:")
        print(f"   成功: {'是' if result.is_successful else '否'}")
        print(f"   迭代次数: {result.total_iterations}")
        print(f"   最终状态: {result.final_state[:150]}...")


def monitor_execution_progress(workflow_engine):
    """监控执行进度"""
    
    print("\n📈 实时监控执行进度 (按Ctrl+C停止):")
    print("-"*50)
    
    last_iteration = 0
    
    while workflow_engine.is_running():
        # 获取当前指标
        metrics = workflow_engine.get_execution_metrics()
        current_state = metrics.get('current_state', {})
        
        iteration_count = current_state.get('iteration_count', 0)
        
        # 只在迭代次数变化时显示
        if iteration_count != last_iteration:
            timestamp = time.strftime("%H:%M:%S")
            status = metrics.get('execution_status', 'unknown')
            description = current_state.get('description', 'unknown')[:80]
            
            print(f"[{timestamp}] 迭代 {iteration_count} | 状态: {status}")
            print(f"         当前状态: {description}...")
            
            if workflow_engine.is_paused():
                print("         ⏸️  工作流已暂停")
            
            last_iteration = iteration_count
        
        time.sleep(1)  # 每秒检查一次
    
    print(f"\n🏁 执行完成，最终状态: {workflow_engine.get_execution_status().value}")


def demonstrate_error_recovery():
    """演示错误恢复机制"""
    
    print("\n🔧 错误恢复机制演示")
    print("="*35)
    
    agents = create_specialized_agents()
    
    # 创建有意引发错误的工作流
    workflow_engine = create_production_rule_system(
        llm=llm_deepseek,
        agents=agents,
        enable_auto_recovery=True
    )
    
    # 容易出错的复杂目标
    error_prone_goal = """
    执行高风险任务：
    1. 连接到不存在的数据库
    2. 调用未定义的API接口
    3. 处理损坏的配置文件
    4. 在出错时自动恢复并完成任务
    """
    
    print(f"目标 (模拟错误场景): {error_prone_goal}")
    print("\n开始执行，观察自动恢复...")
    
    try:
        result = workflow_engine.execute_goal(error_prone_goal)
        
        print(f"\n结果:")
        print(f"  成功: {'是' if result.is_successful else '否'}")
        print(f"  迭代次数: {result.total_iterations}")
        
        if result.execution_metrics:
            metrics = result.execution_metrics
            print(f"  总执行次数: {metrics.total_rules_executed}")
            print(f"  失败次数: {metrics.failed_executions}")
            print(f"  恢复成功率: {metrics.success_rate:.2%}")
        
        # 显示恢复过程
        history = workflow_engine.get_workflow_history()
        if history:
            print(f"\n🔄 恢复过程 (显示最近5步):")
            for i, entry in enumerate(history[-5:], 1):
                print(f"   {i}. {entry['description'][:100]}...")
    
    except Exception as e:
        print(f"演示执行失败: {e}")


def analyze_workflow_performance():
    """工作流性能分析"""
    
    print("\n📊 工作流性能分析")
    print("="*30)
    
    agents = create_specialized_agents()
    workflow_engine = create_production_rule_system(
        llm=llm_deepseek,
        agents=agents
    )
    
    # 执行多个小任务进行性能分析
    test_goals = [
        "创建一个简单的Hello World程序",
        "编写一个基础的计算器函数",
        "实现一个简单的文件读写操作",
        "创建一个基础的数据处理脚本"
    ]
    
    performance_data = []
    
    for i, goal in enumerate(test_goals, 1):
        print(f"\n执行任务 {i}: {goal}")
        
        start_time = time.time()
        result = workflow_engine.execute_goal(goal)
        end_time = time.time()
        
        duration = end_time - start_time
        
        performance_data.append({
            'goal': goal,
            'success': result.is_successful,
            'duration': duration,
            'iterations': result.total_iterations,
            'execution_metrics': result.execution_metrics
        })
        
        print(f"   完成时间: {duration:.2f}秒")
        print(f"   迭代次数: {result.total_iterations}")
        print(f"   结果: {'成功' if result.is_successful else '失败'}")
    
    # 性能总结
    print(f"\n📈 性能总结:")
    total_time = sum(data['duration'] for data in performance_data)
    avg_time = total_time / len(performance_data)
    success_rate = sum(1 for data in performance_data if data['success']) / len(performance_data)
    avg_iterations = sum(data['iterations'] for data in performance_data) / len(performance_data)
    
    print(f"   总执行时间: {total_time:.2f}秒")
    print(f"   平均执行时间: {avg_time:.2f}秒")
    print(f"   成功率: {success_rate:.2%}")
    print(f"   平均迭代次数: {avg_iterations:.1f}")


def main():
    """主函数"""
    
    print("🚀 产生式规则认知工作流高级功能演示")
    print("基于自然语言IF-THEN规则的智能工作流系统")
    print("="*70)
    
    try:
        # 高级工作流控制
        print("\n【演示1: 高级工作流控制】")
        advanced_workflow_control_demo()
        
        # 错误恢复机制
        print("\n\n【演示2: 自动错误恢复】")
        demonstrate_error_recovery()
        
        # 性能分析
        print("\n\n【演示3: 性能分析】")
        analyze_workflow_performance()
        
        print("\n\n🎉 高级功能演示完成!")
        print("\n🔥 核心高级特性:")
        print("✓ 异步工作流执行和控制")
        print("✓ 实时进度监控和状态跟踪")
        print("✓ 智能错误恢复和自修复")
        print("✓ 自定义规则和智能体管理")
        print("✓ 性能分析和优化建议")
        print("✓ 复杂工作流的动态调整")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n\n演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()