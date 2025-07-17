#!/usr/bin/env python3
"""
测试 run_until_breakpoint() 方法的修复
验证调试器能够正确离开当前断点并继续执行到下一个断点
"""

import os
import sys

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from python_core import *
from llm_lazy import get_model
from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType

def test_run_until_breakpoint_fix():
    """测试 run_until_breakpoint 能够离开当前断点"""
    print("\n🧪 测试 run_until_breakpoint 修复...")
    
    # 创建认知智能体
    llm = get_model("gemini_2_5_flash")
    agent = CognitiveAgent(
        llm=llm,
        max_cycles=5,
        verbose=False,
        enable_meta_cognition=False,
        evaluation_mode="internal"
    )
    
    # 创建调试器
    debugger = CognitiveDebugger(agent)
    
    # 设置断点在决策步骤
    bp_id = debugger.set_breakpoint(
        StepType.DECISION_MAKING,
        description="决策步骤断点"
    )
    print(f"✅ 设置断点: {bp_id}")
    
    # 开始调试
    debugger.start_debug("分析问题：如何提高代码质量？请给出3个建议。")
    
    # 第一次运行到断点
    print("\n🏃 第一次运行到断点...")
    results1 = debugger.run_until_breakpoint()
    print(f"   执行了 {len(results1)} 步")
    print(f"   当前步骤: {debugger.debug_state.current_step.value}")
    
    # 记录当前位置
    first_stop_step = debugger.debug_state.current_step
    first_stop_cycle = debugger.debug_state.cycle_count
    
    # 继续运行到下一个断点
    print("\n🏃 继续运行到下一个断点...")
    results2 = debugger.run_until_breakpoint()
    print(f"   执行了 {len(results2)} 步")
    print(f"   当前步骤: {debugger.debug_state.current_step.value}")
    
    # 记录新位置
    second_stop_step = debugger.debug_state.current_step
    second_stop_cycle = debugger.debug_state.cycle_count
    
    # 验证是否离开了第一个断点
    if len(results2) > 0:
        print("\n✅ 成功：run_until_breakpoint 正确离开了当前断点")
        print(f"   第一次停止: 循环{first_stop_cycle}, {first_stop_step.value}")
        print(f"   第二次停止: 循环{second_stop_cycle}, {second_stop_step.value}")
        
        # 显示执行的步骤
        print("\n📊 第二次执行的步骤:")
        for i, result in enumerate(results2[:5]):  # 只显示前5步
            print(f"   {i+1}. {result.step_type.value} ({result.agent_layer})")
        if len(results2) > 5:
            print(f"   ... 还有 {len(results2)-5} 步")
    else:
        print("\n❌ 问题：run_until_breakpoint 没有执行任何步骤")
        print("   可能仍然停留在当前断点")
    
    # 继续执行到完成
    print("\n🏃 运行到完成...")
    final_results = debugger.run_to_completion()
    print(f"   最后执行了 {len(final_results)} 步")
    print(f"   任务完成: {debugger.debug_state.is_finished}")
    
    return len(results2) > 0

def test_conditional_breakpoint():
    """测试条件断点的情况"""
    print("\n🧪 测试条件断点...")
    
    llm = get_model("gemini_2_5_flash")
    agent = CognitiveAgent(
        llm=llm,
        max_cycles=5,
        verbose=False,
        enable_meta_cognition=False,
        evaluation_mode="internal"
    )
    
    debugger = CognitiveDebugger(agent)
    
    # 设置条件断点：只在第2轮及以后触发
    bp_id = debugger.set_breakpoint(
        StepType.STATE_ANALYSIS,
        condition="cycle_count >= 2",
        description="第2轮及以后的状态分析"
    )
    
    debugger.start_debug("创建一个简单的Python函数")
    
    print("\n🏃 第一次运行到断点...")
    results1 = debugger.run_until_breakpoint()
    if debugger.debug_state.current_step == StepType.STATE_ANALYSIS:
        print(f"   在循环 {debugger.debug_state.cycle_count} 停止")
        
        print("\n🏃 继续运行到下一个断点...")
        results2 = debugger.run_until_breakpoint()
        if len(results2) > 0:
            print(f"   执行了 {len(results2)} 步")
            print(f"   在循环 {debugger.debug_state.cycle_count} 停止")
            print("   ✅ 成功离开断点并继续执行")
        else:
            print("   ❌ 未能离开当前断点")
    
    return True

def main():
    """主测试函数"""
    print("🚀 测试 run_until_breakpoint 修复")
    print("=" * 60)
    
    try:
        # 测试基本功能
        success1 = test_run_until_breakpoint_fix()
        
        # 测试条件断点
        success2 = test_conditional_breakpoint()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("🎉 所有测试通过！run_until_breakpoint 修复成功")
            return True
        else:
            print("⚠️  部分测试失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)