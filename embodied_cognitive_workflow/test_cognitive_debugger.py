#!/usr/bin/env python3
"""
测试 CognitiveDebugger 功能
验证调试器的基本功能是否正常工作
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

try:
    import pythonTask
    from embodied_cognitive_workflow.embodied_cognitive_workflow import CognitiveAgent, WorkflowContext, DecisionType
    from cognitive_debugger import CognitiveDebugger, StepType
    from agent_base import Result
    
    # 使用Gemini模型
    llm_gemini = pythonTask.llm_gemini_2_5_flash_google
    
    print("✅ 所有模块导入成功！")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

def test_debugger_initialization():
    """测试调试器初始化"""
    print("\n🧪 测试调试器初始化...")
    
    # 创建认知智能体
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=3,
        verbose=False,
        enable_super_ego=False,
        evaluation_mode="internal"
    )
    
    # 创建调试器
    debugger = CognitiveDebugger(agent)
    
    print(f"   ✅ 调试器创建成功")
    print(f"   📊 包装的智能体: {type(debugger.wrapped_agent).__name__}")
    print(f"   🔧 步骤执行器: {type(debugger.step_executor).__name__}")
    print(f"   🛑 断点管理器: {type(debugger.breakpoint_manager).__name__}")
    
    return debugger

def test_debug_session_start():
    """测试调试会话开始"""
    print("\n🧪 测试调试会话开始...")
    
    agent = CognitiveAgent(llm=llm_gemini, max_cycles=3, verbose=False)
    debugger = CognitiveDebugger(agent)
    
    instruction = "计算 2 + 3 的结果"
    debugger.start_debug(instruction)
    
    print(f"   ✅ 调试会话已开始")
    print(f"   📝 指令: {debugger._instruction}")
    print(f"   🕐 开始时间: {debugger.debug_state.execution_start_time}")
    print(f"   📍 当前步骤: {debugger.debug_state.current_step}")
    
    return debugger

def test_single_step_execution():
    """测试单步执行"""
    print("\n🧪 测试单步执行...")
    
    agent = CognitiveAgent(llm=llm_gemini, max_cycles=3, verbose=False)
    debugger = CognitiveDebugger(agent)
    
    debugger.start_debug("计算 1 + 1")
    
    # 执行几个步骤
    steps_to_test = 3
    for i in range(steps_to_test):
        if debugger.debug_state.is_finished:
            print(f"   ⏹️  执行在第 {i+1} 步完成")
            break
        
        print(f"   📍 执行第 {i+1} 步...")
        step_result = debugger.run_one_step()
        
        if step_result:
            print(f"      ✅ 步骤成功: {step_result.step_type.value}")
            print(f"      ⏱️  耗时: {step_result.execution_time:.3f}s")
            print(f"      🎯 输出: {str(step_result.output_data)[:50]}...")
        else:
            print(f"      ❌ 步骤失败或暂停")
            break
    
    return debugger

def test_breakpoint_functionality():
    """测试断点功能"""
    print("\n🧪 测试断点功能...")
    
    agent = CognitiveAgent(llm=llm_gemini, max_cycles=3, verbose=False)
    debugger = CognitiveDebugger(agent)
    
    # 设置断点
    breakpoint_id = debugger.set_breakpoint(
        step_type=StepType.STATE_ANALYSIS,
        description="测试断点"
    )
    
    print(f"   ✅ 断点设置成功: {breakpoint_id}")
    
    # 列出断点
    breakpoints = debugger.list_breakpoints()
    print(f"   📋 当前断点数量: {len(breakpoints)}")
    
    # 移除断点
    success = debugger.remove_breakpoint(breakpoint_id)
    print(f"   🗑️  断点移除: {'成功' if success else '失败'}")
    
    return debugger

def test_state_inspection():
    """测试状态检查"""
    print("\n🧪 测试状态检查...")
    
    agent = CognitiveAgent(llm=llm_gemini, max_cycles=3, verbose=False)
    debugger = CognitiveDebugger(agent)
    
    debugger.start_debug("简单测试任务")
    
    # 执行一步
    debugger.run_one_step()
    
    # 检查状态
    snapshot = debugger.inspect_state()
    
    if snapshot:
        print(f"   ✅ 状态快照获取成功")
        print(f"   📊 当前步骤: {snapshot.current_step.value}")
        print(f"   🔢 总步骤数: {snapshot.total_steps}")
        print(f"   ⏱️  执行时间: {snapshot.execution_time:.2f}s")
    else:
        print(f"   ❌ 状态快照获取失败")
    
    return debugger

def test_execution_trace():
    """测试执行轨迹"""
    print("\n🧪 测试执行轨迹...")
    
    agent = CognitiveAgent(llm=llm_gemini, max_cycles=2, verbose=False)
    debugger = CognitiveDebugger(agent)
    
    debugger.start_debug("测试执行轨迹")
    
    # 执行几步
    debugger.run_steps(3)
    
    # 获取执行轨迹
    trace = debugger.get_execution_trace()
    
    print(f"   ✅ 执行轨迹获取成功")
    print(f"   📈 步骤数量: {len(trace)}")
    
    for i, step in enumerate(trace):
        print(f"      {i+1}. {step.step_type.value} ({step.agent_layer})")
    
    return debugger

def test_multi_step_execution():
    """测试多步执行"""
    print("\n🧪 测试多步执行...")
    
    agent = CognitiveAgent(llm=llm_gemini, max_cycles=2, verbose=False)
    debugger = CognitiveDebugger(agent)
    
    debugger.start_debug("多步执行测试")
    
    # 执行多步
    results = debugger.run_steps(5)
    
    print(f"   ✅ 多步执行完成")
    print(f"   📊 执行步骤数: {len(results)}")
    print(f"   🏁 是否完成: {debugger.debug_state.is_finished}")
    
    return debugger

def main():
    """主测试函数"""
    print("🚀 开始测试 CognitiveDebugger")
    print("=" * 60)
    
    test_functions = [
        test_debugger_initialization,
        test_debug_session_start,
        test_single_step_execution,
        test_breakpoint_functionality,
        test_state_inspection,
        test_execution_trace,
        test_multi_step_execution
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
            print("   ✅ 测试通过\n")
        except Exception as e:
            print(f"   ❌ 测试失败: {e}\n")
    
    print("=" * 60)
    print(f"📊 测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！CognitiveDebugger 基本功能正常")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)