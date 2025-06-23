#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三阶段规划模式测试

验证修改后的规划者是否能按照"收集→执行→验证"三阶段模式生成任务
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognitive_workflow import CognitivePlanner, TaskPhase
from pythonTask import Agent, llm_deepseek
import json

def test_three_phase_planning():
    """测试三阶段规划模式"""
    
    print("🧪 三阶段规划模式测试")
    print("=" * 50)
    
    # 使用与演示文件相同的LLM配置
    llm = llm_deepseek
    
    # 创建测试用的智能体
    test_agents = {
        'analyst': Agent(llm=llm),
        'coder': Agent(llm=llm), 
        'tester': Agent(llm=llm)
    }
    
    # 设置API规格说明
    test_agents['analyst'].api_specification = "需求分析师，擅长分析用户需求和技术调研"
    test_agents['coder'].api_specification = "程序员，擅长编写和调试代码"
    test_agents['tester'].api_specification = "测试工程师，擅长编写测试用例和验证功能"
    
    # 初始化规划者
    planner = CognitivePlanner(llm, test_agents, interactive_mode=False)
    
    # 测试用例1：简单目标
    print("\n📝 测试用例1：简单目标 - Hello World程序")
    print("-" * 30)
    
    goal1 = "开发一个简单的Python Hello World程序"
    tasks1 = planner.generate_task_list(goal1)
    
    print(f"生成任务数量: {len(tasks1)}")
    
    # 统计各阶段任务数量
    phase_counts = {}
    for task in tasks1:
        phase = task.phase.value
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
    print("各阶段任务分布:")
    for phase_name in ['information', 'execution', 'verification']:
        count = phase_counts.get(phase_name, 0)
        print(f"  {phase_name}: {count} 个任务")
        
    print("\n任务详情:")
    for i, task in enumerate(tasks1, 1):
        print(f"  {i}. [{task.phase.value}] {task.id} - {task.name}")
        print(f"     先决条件: {task.precondition}")
        print()
    
    # 测试用例2：复杂目标
    print("\n📝 测试用例2：复杂目标 - 数据分析工具")
    print("-" * 30)
    
    goal2 = "开发一个数据分析工具，能够读取CSV文件并生成统计图表"
    tasks2 = planner.generate_task_list(goal2)
    
    print(f"生成任务数量: {len(tasks2)}")
    
    # 统计各阶段任务数量
    phase_counts2 = {}
    for task in tasks2:
        phase = task.phase.value
        phase_counts2[phase] = phase_counts2.get(phase, 0) + 1
        
    print("各阶段任务分布:")
    for phase_name in ['information', 'execution', 'verification']:
        count = phase_counts2.get(phase_name, 0)
        print(f"  {phase_name}: {count} 个任务")
        
    print("\n任务详情:")
    for i, task in enumerate(tasks2, 1):
        print(f"  {i}. [{task.phase.value}] {task.id} - {task.name}")
        print(f"     先决条件: {task.precondition}")
        print()
    
    # 验证三阶段逻辑
    print("\n🔍 三阶段逻辑验证")
    print("-" * 30)
    
    def verify_three_phase_logic(tasks, goal_name):
        """验证三阶段逻辑是否正确"""
        print(f"\n验证 '{goal_name}' 的三阶段逻辑:")
        
        # 按阶段分组
        phase_tasks = {
            'information': [],
            'execution': [],
            'verification': []
        }
        
        for task in tasks:
            phase_tasks[task.phase.value].append(task)
            
        # 检查是否有执行和验证阶段（必须）
        has_execution = len(phase_tasks['execution']) > 0
        has_verification = len(phase_tasks['verification']) > 0
        
        print(f"  ✅ 有执行阶段: {has_execution}")
        print(f"  ✅ 有验证阶段: {has_verification}")
        
        # 检查ID命名是否符合规范
        id_pattern_correct = True
        for task in tasks:
            phase_prefix = {
                'information': 'collect_',
                'execution': 'exec_',
                'verification': 'verify_'
            }
            expected_prefix = phase_prefix.get(task.phase.value, '')
            if expected_prefix and not task.id.startswith(expected_prefix):
                id_pattern_correct = False
                print(f"  ⚠️ 任务ID不符合规范: {task.id} (应以 {expected_prefix} 开头)")
                
        if id_pattern_correct:
            print(f"  ✅ 任务ID命名规范正确")
            
        # 检查先决条件是否体现阶段关系
        precondition_logic = True
        for task in phase_tasks['execution']:
            if phase_tasks['information'] and not any(
                keyword in task.precondition.lower() 
                for keyword in ['收集', '分析', '明确', '完成', '获取']
            ):
                precondition_logic = False
                print(f"  ⚠️ 执行阶段任务先决条件未体现信息收集: {task.precondition}")
                
        for task in phase_tasks['verification']:
            if not any(
                keyword in task.precondition.lower()
                for keyword in ['实现', '完成', '编写', '开发', '生成']
            ):
                precondition_logic = False
                print(f"  ⚠️ 验证阶段任务先决条件未体现执行完成: {task.precondition}")
                
        if precondition_logic:
            print(f"  ✅ 先决条件逻辑正确")
            
        return has_execution and has_verification and id_pattern_correct and precondition_logic
    
    # 验证两个测试用例
    result1 = verify_three_phase_logic(tasks1, "Hello World程序")
    result2 = verify_three_phase_logic(tasks2, "数据分析工具")
    
    print(f"\n🎯 测试结果总结")
    print("-" * 30)
    print(f"测试用例1 (简单目标): {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"测试用例2 (复杂目标): {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("\n🎉 三阶段规划模式测试全部通过！")
        print("✅ 规划者能够正确按照 '收集→执行→验证' 三阶段模式生成任务")
        print("✅ 任务ID命名符合阶段前缀规范")
        print("✅ 先决条件体现了阶段间的逻辑关系")
    else:
        print("\n❌ 部分测试未通过，需要进一步优化")
        
    return result1 and result2

if __name__ == "__main__":
    test_three_phase_planning() 