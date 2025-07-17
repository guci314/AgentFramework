#!/usr/bin/env python3
"""
测试 inspect_workflow_state 方法
演示如何方便地获取工作流状态
"""

import os
import sys

# 设置代理
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from embodied_cognitive_workflow import CognitiveAgent
from embodied_cognitive_workflow.cognitive_debugger import CognitiveDebugger, StepType
from llm_lazy import get_model

def test_inspect_workflow_state():
    """测试 inspect_workflow_state 方法"""
    print("🧪 测试 inspect_workflow_state 方法")
    print("=" * 60)
    
    # 创建认知智能体
    agent = CognitiveAgent(
        llm=get_model("gemini_2_5_flash"),
        max_cycles=3,
        verbose=False,
        enable_meta_cognition=False
    )
    
    # 创建调试器
    debugger = CognitiveDebugger(agent)
    
    # 测试1：调试未开始时
    print("\n1️⃣ 调试未开始时调用:")
    workflow_context = debugger.inspect_workflow_state()
    print(f"   返回值: {workflow_context}")
    
    # 开始调试
    task = "计算 10 + 20 的结果"
    print(f"\n2️⃣ 开始调试任务: {task}")
    debugger.start_debug(task)
    
    # 测试2：调试开始后立即获取状态
    print("\n3️⃣ 调试开始后获取初始状态:")
    workflow_context = debugger.inspect_workflow_state()
    if workflow_context:
        print(f"   ✅ 成功获取 WorkflowContext")
        print(f"   - 指令: {workflow_context.instruction}")
        print(f"   - 当前状态: '{workflow_context.current_state}' (初始为空)")
        print(f"   - 本我评估: '{workflow_context.id_evaluation}' (初始为空)")
        print(f"   - 目标达成: {workflow_context.goal_achieved}")
        print(f"   - 循环轮数: {workflow_context.current_cycle}")
    
    # 执行几步
    print("\n4️⃣ 执行几个步骤...")
    for i in range(5):
        step_result = debugger.run_one_step()
        if step_result:
            print(f"   步骤 {i+1}: {step_result.step_type.value}")
            
            # 在状态分析步骤后检查
            if step_result.step_type == StepType.STATE_ANALYSIS:
                print("\n   📊 状态分析完成，检查工作流状态:")
                workflow_context = debugger.inspect_workflow_state()
                if workflow_context and workflow_context.current_state:
                    print(f"   - 当前状态分析: {workflow_context.current_state[:100]}...")
            
            # 在本我评估步骤后检查
            elif step_result.step_type == StepType.ID_EVALUATION:
                print("\n   🎯 本我评估完成，检查工作流状态:")
                workflow_context = debugger.inspect_workflow_state()
                if workflow_context:
                    print(f"   - 本我评估: {workflow_context.id_evaluation[:100]}...")
                    print(f"   - 目标达成: {workflow_context.goal_achieved}")
    
    # 完成执行
    print("\n5️⃣ 完成剩余执行...")
    remaining_results = debugger.run_to_completion()
    print(f"   又执行了 {len(remaining_results)} 步")
    
    # 最终状态检查
    print("\n6️⃣ 获取最终工作流状态:")
    workflow_context = debugger.inspect_workflow_state()
    if workflow_context:
        print(f"   - 指令: {workflow_context.instruction}")
        print(f"   - 最终状态: {workflow_context.current_state[:100]}...")
        print(f"   - 目标达成: {workflow_context.goal_achieved}")
        print(f"   - 总循环数: {workflow_context.current_cycle}")
        print(f"   - 历史记录: {len(workflow_context.history)} 条")
        
        # 显示完整上下文
        print("\n7️⃣ 获取格式化的完整上下文:")
        full_context = workflow_context.get_current_context()
        print(f"{full_context[:300]}...")
    
    print("\n✅ 测试完成！")
    print("\n📝 使用总结:")
    print("   - debugger.inspect_workflow_state() 直接返回 WorkflowContext 对象")
    print("   - 可以方便地访问所有工作流状态属性")
    print("   - 比通过 debugger.debug_state.workflow_context 访问更直观")
    print("   - 自动处理调试未开始的情况")

def compare_methods():
    """比较不同的状态获取方法"""
    print("\n\n🔄 比较不同的状态获取方法")
    print("=" * 60)
    
    agent = CognitiveAgent(
        llm=get_model("deepseek_chat"),
        max_cycles=2,
        verbose=False
    )
    debugger = CognitiveDebugger(agent)
    debugger.start_debug("简单测试")
    
    # 执行一些步骤
    for _ in range(3):
        debugger.run_one_step()
    
    print("\n方法1：直接访问（原始方式）")
    print("workflow_context = debugger.debug_state.workflow_context")
    workflow_context = debugger.debug_state.workflow_context
    print(f"结果: {workflow_context}")
    
    print("\n方法2：使用新的 inspect_workflow_state 方法")
    print("workflow_context = debugger.inspect_workflow_state()")
    workflow_context = debugger.inspect_workflow_state()
    print(f"结果: {workflow_context}")
    
    print("\n方法3：使用 inspect_state 获取快照")
    print("snapshot = debugger.capture_debug_snapshot()")
    snapshot = debugger.capture_debug_snapshot()
    if snapshot:
        print(f"结果: StateSnapshot 对象")
        print(f"  - instruction: {snapshot.instruction}")
        print(f"  - current_state_analysis: {snapshot.current_state_analysis[:50]}...")
    
    print("\n✅ 三种方法的对比:")
    print("   1. 直接访问：需要了解内部结构")
    print("   2. inspect_workflow_state()：简洁直观，返回原始对象")
    print("   3. inspect_state()：返回快照，包含更多统计信息")

if __name__ == "__main__":
    try:
        test_inspect_workflow_state()
        compare_methods()
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()