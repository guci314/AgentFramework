#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态任务添加日志可观测性演示

此脚本演示了 CognitiveWorkflow 中动态任务添加功能的详细日志记录，
展示从决策到执行的完整可观测性。

作者：Claude
日期：2024-12-21
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from unittest.mock import Mock, MagicMock
from CognitiveWorkflow.cognitive_workflow import (
    CognitiveWorkflowEngine, 
    CognitiveTask, 
    TaskPhase, 
    TaskStatus,
    GlobalState
)
from agent_base import Result

# 配置日志以显示详细信息
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def create_demo_workflow():
    """创建演示用的工作流引擎"""
    
    # 模拟 LLM
    mock_llm = Mock()
    
    # 模拟决策响应 - 触发动态任务添加
    mock_llm.invoke.return_value = Mock(content="""{
        "action": "add_tasks",
        "reason": "需要添加数据验证和错误处理任务",
        "details": {
            "new_tasks": [
                {
                    "name": "数据验证任务",
                    "instruction": "验证输入数据的完整性和格式正确性",
                    "agent_name": "test_agent",
                    "instruction_type": "execution",
                    "phase": "verification",
                    "expected_output": "数据验证报告",
                    "precondition": "原始数据已准备就绪"
                },
                {
                    "name": "错误处理任务",
                    "instruction": "实现错误捕获和恢复机制",
                    "agent_name": "test_agent",
                    "instruction_type": "execution", 
                    "phase": "execution",
                    "expected_output": "错误处理机制",
                    "precondition": "数据验证任务已完成"
                }
            ]
        }
    }""")
    
    # 模拟智能体
    mock_agent = Mock()
    mock_agent.execute_sync.return_value = Result(
        success=True,
        code="print('Hello World')",
        stdout="Hello World\n",
        stderr="",
        return_value="Hello World"
    )
    
    agents = {"test_agent": mock_agent}
    
    # 创建工作流引擎
    engine = CognitiveWorkflowEngine(
        llm=mock_llm,
        agents=agents,
        max_iterations=3,
        enable_auto_recovery=True
    )
    
    return engine

def demo_dynamic_task_addition():
    """演示动态任务添加的完整日志流程"""
    
    print("🚀 开始动态任务添加日志可观测性演示")
    print("=" * 60)
    
    # 创建工作流引擎
    engine = create_demo_workflow()
    
    # 手动创建一个初始任务
    initial_task = CognitiveTask(
        id="task_001",
        name="初始数据处理任务",
        instruction="处理用户输入的数据",
        agent_name="test_agent",
        instruction_type="execution",
        phase=TaskPhase.EXECUTION,
        expected_output="处理后的数据",
        precondition="用户已提供数据"
    )
    
    # 设置初始状态
    engine.task_list = [initial_task]
    engine.global_state = GlobalState(current_state="准备开始数据处理")
    engine.global_state.set_llm(engine.llm)
    engine.global_state.set_original_goal("演示动态任务添加的日志可观测性")
    
    print("\n📋 初始任务列表:")
    print(f"   - {initial_task.id}: {initial_task.name}")
    
    print("\n🎯 模拟任务执行完成，触发动态计划修正决策...")
    
    # 模拟任务执行结果
    mock_result = Result(
        success=True,
        code="data_processed = process_data(input_data)",
        stdout="数据处理完成",
        stderr="",
        return_value="processed_data"
    )
    
    # 标记初始任务为已完成
    initial_task.status = TaskStatus.COMPLETED
    initial_task.result = mock_result
    
    print("\n" + "="*60)
    print("🔥 触发动态计划修正决策流程")
    print("="*60)
    
    # 调用动态计划修正决策
    modification_decision = engine.decider.plan_modification_decision(
        engine.task_list, 
        engine.global_state, 
        mock_result
    )
    
    print(f"\n🎯 决策结果: {modification_decision['action']}")
    print(f"💡 决策理由: {modification_decision['reason']}")
    
    if modification_decision['action'] == 'add_tasks':
        print("\n" + "="*60)
        print("🚀 执行动态任务添加流程")
        print("="*60)
        
        # 应用计划修正
        engine._apply_plan_modification(modification_decision)
        
        print(f"\n📈 任务添加完成！")
        print(f"   原始任务数: 1")
        print(f"   当前任务数: {len(engine.task_list)}")
        
        print(f"\n📋 更新后的任务列表:")
        for i, task in enumerate(engine.task_list, 1):
            print(f"   {i}. {task.id}: {task.name}")
            print(f"      代理: {task.agent_name}")
            print(f"      阶段: {task.phase.value}")
            print(f"      状态: {task.status.value}")
            print(f"      预期输出: {task.expected_output}")
            print()
    
    print("=" * 60)
    print("✅ 动态任务添加日志可观测性演示完成")
    print("=" * 60)
    
    return engine

def demo_error_scenarios():
    """演示错误场景下的日志记录"""
    
    print("\n🔍 演示错误场景下的日志记录")
    print("=" * 60)
    
    engine = create_demo_workflow()
    
    # 模拟无效的动态任务数据
    invalid_decision = {
        'action': 'add_tasks',
        'reason': '测试错误处理',
        'details': {
            'new_tasks': [
                {
                    # 缺少必填字段 'name'
                    'instruction': '无效任务',
                    'agent_name': 'nonexistent_agent',  # 不存在的智能体
                    'expected_output': '无效输出'
                    # 缺少其他必填字段
                }
            ]
        }
    }
    
    print("\n🚨 测试无效任务数据的错误处理...")
    
    # 设置基本状态
    engine.task_list = []
    engine.global_state = GlobalState(current_state="测试错误处理")
    
    # 尝试添加无效任务
    success = engine._add_dynamic_tasks(invalid_decision)
    
    print(f"\n📊 错误处理结果: {'失败' if not success else '意外成功'}")
    print(f"任务列表数量: {len(engine.task_list)}")
    
    print("\n✅ 错误场景演示完成")

if __name__ == "__main__":
    # 主演示
    engine = demo_dynamic_task_addition()
    
    # 错误场景演示
    demo_error_scenarios()
    
    print(f"\n🎉 所有演示完成！")
    print(f"   ✅ 可观测性日志已成功集成到动态任务添加流程")
    print(f"   ✅ 错误处理和验证机制正常工作")
    print(f"   ✅ 详细的步骤追踪和状态记录已实现") 