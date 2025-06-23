#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一update_state方法演示

展示新的统一状态更新接口的各种使用方式：
1. 简单模式：直接设置状态
2. 智能模式：使用LLM生成状态（需要LLM）
3. 向后兼容：支持旧的调用方式
"""

from cognitive_workflow import GlobalState, CognitiveTask, TaskPhase
from agent_base import Result
from datetime import datetime

def demo_unified_update_state():
    """演示统一的update_state方法"""
    
    print("🔄 统一update_state方法演示")
    print("=" * 50)
    
    # 创建全局状态
    state = GlobalState(current_state="演示初始状态")
    state.set_original_goal("演示统一状态更新接口的功能")
    
    print(f"初始状态: {state.current_state}")
    print()
    
    # 1. 简单模式演示
    print("1️⃣ 简单模式演示（intelligent=False）")
    print("-" * 30)
    
    result1 = state.update_state(
        new_state="这是通过简单模式设置的状态",
        source="demo_simple",
        intelligent=False  # 关闭智能模式
    )
    
    print(f"✅ 返回结果: {result1}")
    print(f"✅ 当前状态: {state.current_state}")
    print()
    
    # 2. 智能模式演示（无LLM，使用fallback）
    print("2️⃣ 智能模式演示（无LLM，使用fallback）")
    print("-" * 40)
    
    result2 = state.update_state(
        new_state="这是智能模式的fallback状态",
        source="demo_intelligent",
        intelligent=True  # 启用智能模式（默认）
    )
    
    print(f"✅ 返回结果: {result2}")
    print(f"✅ 当前状态: {state.current_state}")
    print()
    
    # 3. 带任务和结果的智能模式演示
    print("3️⃣ 带任务和结果的智能模式演示")
    print("-" * 35)
    
    # 创建模拟任务和结果
    demo_task = CognitiveTask(
        id="demo_task_1",
        name="演示任务",
        instruction="执行演示操作",
        agent_name="demo_agent",
        instruction_type="execution",
        phase=TaskPhase.EXECUTION,
        expected_output="演示结果",
        precondition="演示环境已准备"
    )
    
    demo_result = Result(
        success=True,
        code="print('Hello, World!')",
        stdout="Hello, World!",
        stderr="",
        return_value="演示执行成功"
    )
    
    result3 = state.update_state(
        new_state="任务执行完成的fallback状态",
        source="demo_executor",
        task=demo_task,
        result=demo_result,
        intelligent=True
    )
    
    print(f"✅ 返回结果: {result3}")
    print(f"✅ 当前状态: {state.current_state}")
    print()
    
    # 4. 向后兼容演示
    print("4️⃣ 向后兼容演示（旧的调用方式）")
    print("-" * 35)
    
    result4 = state.update_state("向后兼容的状态更新", "demo_legacy")
    
    print(f"✅ 返回结果: {result4}")
    print(f"✅ 当前状态: {state.current_state}")
    print()
    
    # 5. 错误处理演示
    print("5️⃣ 错误处理演示")
    print("-" * 20)
    
    try:
        # 简单模式但没有提供new_state
        state.update_state(intelligent=False, source="error_demo")
    except ValueError as e:
        print(f"✅ 正确捕获错误: {e}")
    
    print()
    
    # 6. 状态历史查看
    print("6️⃣ 状态历史")
    print("-" * 15)
    
    print(f"总状态变更次数: {len(state.state_history)}")
    print("最近的状态历史:")
    for i, history_item in enumerate(state.get_recent_history(3), 1):
        print(f"  {i}. {history_item}")
    
    print()
    
    # 7. 状态摘要
    print("7️⃣ 状态摘要")
    print("-" * 15)
    print(state.get_state_summary())
    
    print("🎉 统一update_state方法演示完成！")
    print("\n💡 使用建议:")
    print("- 默认使用智能模式（intelligent=True）获得更丰富的状态描述")
    print("- 在需要精确控制状态内容时使用简单模式（intelligent=False）")
    print("- 提供task和result参数可获得更详细的上下文信息")
    print("- 方法完全向后兼容，现有代码无需修改")

def demo_api_comparison():
    """对比新旧API的使用方式"""
    
    print("\n📊 API对比演示")
    print("=" * 50)
    
    state = GlobalState(current_state="API对比演示")
    
    print("🔧 新的统一API:")
    print("```python")
    print("# 简单模式")
    print("state.update_state('新状态', intelligent=False)")
    print()
    print("# 智能模式（默认）") 
    print("state.update_state('fallback状态', task=task, result=result)")
    print()
    print("# 向后兼容")
    print("state.update_state('状态', 'source')")
    print("```")
    print()
    
    print("✨ 优势:")
    print("✅ 统一接口，减少方法数量")
    print("✅ 智能模式默认启用")
    print("✅ 完全向后兼容")
    print("✅ 支持灵活的参数组合")
    print("✅ 更清晰的参数语义")

if __name__ == "__main__":
    demo_unified_update_state()
    demo_api_comparison() 