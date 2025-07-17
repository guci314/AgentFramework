#!/usr/bin/env python3
"""
自然语言状态管理演示
==================

演示新的自然语言全局状态管理功能，包括：
1. 智能状态更新
2. 自然语言条件评估
3. 状态历史追踪
4. 混合模式兼容性
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from static_workflow.workflow_definitions import (
    WorkflowDefinition, WorkflowMetadata, WorkflowStep, StepExecution,
    StepExecutionStatus, WorkflowExecutionContext
)
from static_workflow.global_state_updater import GlobalStateUpdater
from static_workflow.control_flow_evaluator import ControlFlowEvaluator
from static_workflow.workflow_definitions import WorkflowLoader


def create_mock_llm():
    """创建模拟LLM，提供智能的响应"""
    
    mock_llm = Mock()
    
    # 状态更新响应
    state_responses = [
        "项目需求分析已完成。明确了计算器的核心功能需求：支持四则运算、错误处理、用户界面友好。技术栈确定为Python，采用模块化设计。下一步将进行架构设计。",
        
        "架构设计已完成。采用分层架构：UI层负责用户交互，逻辑层处理计算，工具层提供辅助功能。定义了清晰的模块接口和数据流。准备开始核心功能实现。",
        
        "核心计算功能实现完成。已创建Calculator类，包含add、subtract、multiply、divide四个核心方法。代码结构清晰，包含完整的错误处理机制。准备编写测试用例。",
        
        "测试用例编写完成。创建了全面的测试套件，覆盖正常情况、边界条件和异常情况。测试用例包括单元测试和集成测试，确保代码质量。准备运行测试验证。",
        
        "测试验证已完成。所有26个测试用例全部通过，代码覆盖率达到98%。功能正确性得到充分验证，没有发现任何缺陷。准备进行代码质量检查。",
        
        "代码质量检查完成。代码符合PEP8规范，注释完整，函数命名清晰。使用pylint检查得分9.8/10。代码质量优秀，满足生产环境要求。准备生成项目文档。",
        
        "项目文档生成完成。创建了完整的README文件、API文档和使用示例。文档结构清晰，内容详实，便于用户理解和使用。智能计算器项目开发圆满完成！"
    ]
    
    # 条件评估响应
    condition_responses = {
        "所有测试都通过，没有失败的用例": "true",
        "代码质量良好，符合所有编程规范": "true",
        "需求分析是否完成": "true",
        "架构设计是否满足要求": "true"
    }
    
    def mock_invoke(messages):
        content = messages[1]["content"] if len(messages) > 1 else messages[0]["content"]
        
        # 判断是状态更新还是条件评估
        if "工作流状态更新任务" in content:
            # 状态更新请求
            response = Mock()
            if hasattr(mock_invoke, 'call_count'):
                mock_invoke.call_count += 1
            else:
                mock_invoke.call_count = 0
            
            if mock_invoke.call_count < len(state_responses):
                response.content = state_responses[mock_invoke.call_count]
            else:
                response.content = "工作流继续进行中..."
            return response
        else:
            # 条件评估请求
            response = Mock()
            for condition, result in condition_responses.items():
                if condition in content:
                    response.content = result
                    return response
            response.content = "false"  # 默认返回false
            return response
    
    mock_llm.invoke = mock_invoke
    return mock_llm


def demo_state_updates():
    """演示状态更新功能"""
    print("🎯 演示1: 智能状态更新功能")
    print("="*50)
    
    # 创建模拟LLM
    mock_llm = create_mock_llm()
    
    # 创建状态更新器
    updater = GlobalStateUpdater(llm=mock_llm, enable_updates=True)
    
    # 创建执行上下文
    context = WorkflowExecutionContext("demo-workflow-001")
    
    # 模拟步骤执行和状态更新
    steps = [
        ("需求分析", "analyst", "分析计算器功能需求"),
        ("架构设计", "architect", "设计软件架构"), 
        ("核心实现", "coder", "实现核心计算功能"),
        ("编写测试", "tester", "编写测试用例"),
        ("运行测试", "tester", "验证功能正确性"),
        ("质量检查", "reviewer", "检查代码质量"),
        ("生成文档", "documenter", "生成项目文档")
    ]
    
    current_state = "智能计算器项目开始，目标是创建功能完整的计算器应用。"
    context.update_global_state(current_state)
    
    print(f"📋 初始状态:")
    print(f"   {current_state}\n")
    
    for i, (name, agent, instruction) in enumerate(steps, 1):
        print(f"🚀 步骤 {i}: {name}")
        
        # 创建步骤执行实例
        step = WorkflowStep(
            id=f"step{i}",
            name=name,
            agent_name=agent,
            instruction=instruction,
            expected_output=f"{name}的输出结果"
        )
        
        execution = StepExecution(f"exec-{i}", f"step{i}", 1)
        execution.status = StepExecutionStatus.COMPLETED
        
        # 更新状态
        new_state = updater.update_state(
            current_state=context.current_global_state,
            step=step,
            execution=execution,
            workflow_context=f"智能计算器开发 | 步骤 {i}/{len(steps)}"
        )
        
        context.update_global_state(new_state)
        
        print(f"   📝 更新后状态: {new_state[:150]}...")
        print()
    
    print(f"📊 最终状态摘要:")
    print(context.get_state_summary())


def demo_natural_language_conditions():
    """演示自然语言条件评估"""
    print("\n🎯 演示2: 自然语言条件评估")
    print("="*50)
    
    # 创建模拟LLM
    mock_llm = create_mock_llm()
    
    # 创建控制流评估器
    evaluator = ControlFlowEvaluator(llm=mock_llm)
    
    # 设置工作流状态上下文
    global_state = """智能计算器项目已完成所有开发阶段：
- 需求分析：✅ 已完成，明确了功能要求
- 架构设计：✅ 已完成，采用分层架构  
- 核心实现：✅ 已完成，包含四则运算功能
- 测试验证：✅ 已完成，26个测试用例全部通过
- 质量检查：✅ 已完成，代码质量评分9.8/10
- 文档生成：✅ 已完成，包含完整的用户文档

项目状态：开发完成，质量优秀，准备发布。"""
    
    # 创建模拟的步骤结果
    mock_result = Mock()
    mock_result.success = True
    mock_result.stdout = "All 26 tests passed successfully"
    mock_result.return_value = "Test suite completed with 100% pass rate"
    
    evaluator.set_context(global_state=global_state, step_result=mock_result)
    
    # 测试各种自然语言条件
    test_conditions = [
        "所有测试都通过，没有失败的用例",
        "代码质量良好，符合所有编程规范", 
        "需求分析是否完成",
        "是否还有未完成的开发任务",
        "项目是否准备好发布"
    ]
    
    print("📋 测试条件评估:")
    for condition in test_conditions:
        result = evaluator.evaluate_natural_language_condition(condition)
        status = "✅ 满足" if result else "❌ 不满足"
        print(f"   {condition}")
        print(f"   → {status}\n")


def demo_backward_compatibility():
    """演示向后兼容性"""
    print("\n🎯 演示3: 向后兼容性")
    print("="*50)
    
    # 加载示例工作流
    try:
        loader = WorkflowLoader()
        workflow_path = "static_workflow/workflow_examples/natural_language_state_demo.json"
        workflow = loader.load_from_file(workflow_path)
        
        print("📋 工作流配置:")
        print(f"   名称: {workflow.workflow_metadata.name}")
        print(f"   描述: {workflow.workflow_metadata.description}")
        print(f"   步骤数量: {len(workflow.steps)}")
        
        print(f"\n📝 初始全局状态:")
        print(f"   {workflow.global_state}")
        
        print(f"\n🔧 全局变量(向后兼容):")
        for key, value in workflow.global_variables.items():
            print(f"   {key}: {value}")
        
        print("\n✅ 成功加载包含自然语言状态的工作流配置")
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")


def demo_mixed_mode():
    """演示混合模式：传统变量 + 自然语言状态"""
    print("\n🎯 演示4: 混合模式")
    print("="*50)
    
    # 创建混合模式的工作流定义
    workflow = WorkflowDefinition(
        workflow_metadata=WorkflowMetadata(
            name="混合模式演示",
            version="1.0", 
            description="同时使用传统变量和自然语言状态"
        ),
        steps=[],
        global_variables={
            "project_name": "智能计算器",
            "version": "1.0.0",
            "test_count": 0,
            "success_rate": 0.0
        },
        global_state="项目开始：将开发智能计算器，目标是创建高质量的计算应用。"
    )
    
    print("📋 混合模式配置:")
    print(f"   传统变量: {workflow.global_variables}")
    print(f"   自然语言状态: {workflow.global_state}")
    
    # 创建状态更新器用于数据提取
    updater = GlobalStateUpdater(llm=None)
    
    # 模拟状态更新
    updated_state = """项目进展顺利！

已完成工作：
- 核心功能开发：100%完成
- 测试用例编写：26个测试用例
- 质量检查：代码评分9.8/10

统计数据：
- 总测试数：26
- 通过率：100%
- 代码覆盖率：98%

当前状态：开发完成，准备发布。"""
    
    # 从自然语言中提取结构化数据
    extracted_data = updater.extract_structured_data(updated_state)
    
    print(f"\n📊 从自然语言状态提取的结构化数据:")
    for key, value in extracted_data.items():
        print(f"   {key}: {value}")
    
    # 可以将提取的数据更新到传统变量中
    if 'completed_steps' in extracted_data:
        workflow.global_variables['test_count'] = extracted_data.get('completed_steps', 0)
    
    print(f"\n🔄 更新后的传统变量:")
    for key, value in workflow.global_variables.items():
        print(f"   {key}: {value}")
    
    print("\n✅ 混合模式演示完成：传统变量和自然语言状态可以和谐共存")


def main():
    """主演示函数"""
    print("🌟 自然语言状态管理系统演示")
    print("="*60)
    print("本演示展示了静态工作流系统的新功能：")
    print("• 智能的自然语言状态更新")
    print("• 基于上下文的条件评估")  
    print("• 完整的状态历史追踪")
    print("• 向后兼容的混合模式")
    print("="*60)
    
    try:
        # 演示1：状态更新
        demo_state_updates()
        
        # 演示2：自然语言条件
        demo_natural_language_conditions()
        
        # 演示3：向后兼容性
        demo_backward_compatibility()
        
        # 演示4：混合模式
        demo_mixed_mode()
        
        print("\n🎉 所有演示完成!")
        print("\n💡 总结:")
        print("1. ✅ 自然语言状态管理功能完全正常")
        print("2. ✅ LLM智能更新提供了丰富的上下文信息")
        print("3. ✅ 自然语言条件评估支持复杂的业务逻辑")
        print("4. ✅ 保持了与现有系统的完全兼容性")
        print("5. ✅ 混合模式支持灵活的使用场景")
        
        print("\n🚀 新的自然语言状态管理系统已经准备就绪！")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()