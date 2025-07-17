#!/usr/bin/env python3
"""
CognitiveDebugger 功能演示
展示如何使用认知调试器进行单步调试
"""

import os
import sys

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from embodied_cognitive_workflow.embodied_cognitive_workflow import CognitiveAgent
    from embodied_cognitive_workflow.cognitive_debugger import CognitiveDebugger, StepType
    from python_core import *
from llm_lazy import get_model
    
    print("✅ 模块导入成功！")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

def demo_basic_debugging():
    """演示基本调试功能"""
    print("\n" + "="*60)
    print("🎬 演示1: 基本调试功能")
    print("="*60)
    
    # 创建认知智能体
    agent = CognitiveAgent(
        llm=\1("gemini_2_5_flash"),
        max_cycles=3,
        verbose=False,
        enable_meta_cognition=False,
        evaluation_mode="internal"
    )
    
    # 创建调试器
    debugger = CognitiveDebugger(agent)
    
    # 开始调试会话
    task = "计算 15 + 23 的结果"
    print(f"📝 任务: {task}")
    debugger.start_debug(task)
    
    # 单步执行演示
    print("\n🔄 开始单步执行演示...")
    step_count = 0
    max_steps = 8  # 限制步数防止无限循环
    
    while not debugger.debug_state.is_finished and step_count < max_steps:
        step_result = debugger.run_one_step()
        
        if step_result is None:
            print("⏸️  遇到断点，执行暂停")
            break
        
        step_count += 1
        print(f"\n📍 步骤 {step_count}: {step_result.step_type.value}")
        print(f"   🎯 执行层: {step_result.agent_layer}")
        print(f"   ⏱️  耗时: {step_result.execution_time:.3f}s")
        
        # 显示输出数据（截断长输出）
        output_str = str(step_result.output_data)
        if len(output_str) > 100:
            output_str = output_str[:100] + "..."
        print(f"   📊 输出: {output_str}")
        
        # 显示调试信息
        if step_result.debug_info:
            print(f"   🔍 调试信息: {list(step_result.debug_info.keys())}")
    
    print(f"\n✅ 演示完成，共执行 {step_count} 步")
    return debugger

def demo_breakpoint_debugging():
    """演示断点调试功能"""
    print("\n" + "="*60)
    print("🎬 演示2: 断点调试功能")
    print("="*60)
    
    # 创建智能体和调试器
    agent = CognitiveAgent(
        llm=\1("gemini_2_5_flash"),
        max_cycles=5,
        verbose=False
    )
    debugger = CognitiveDebugger(agent)
    
    # 设置断点
    print("🛑 设置断点...")
    bp_id1 = debugger.set_breakpoint(
        StepType.DECISION_MAKING,
        description="决策步骤断点"
    )
    
    bp_id2 = debugger.set_breakpoint(
        StepType.BODY_EXECUTION,
        description="执行步骤断点"
    )
    
    # 列出当前断点
    breakpoints = debugger.list_breakpoints()
    print(f"📋 已设置 {len(breakpoints)} 个断点")
    
    # 开始调试
    task = "写一个Python函数计算阶乘"
    print(f"\n📝 任务: {task}")
    debugger.start_debug(task)
    
    # 执行到断点
    print("\n🏃 执行到第一个断点...")
    results1 = debugger.run_until_breakpoint()
    print(f"⏸️  在断点停止，已执行 {len(results1)} 步")
    
    if results1:
        last_step = results1[-1]
        print(f"   停止在: {last_step.step_type.value}")
    
    # 继续执行到下一个断点
    print("\n🏃 继续执行到下一个断点...")
    results2 = debugger.run_until_breakpoint()
    print(f"⏸️  在断点停止，又执行了 {len(results2)} 步")
    
    # 移除断点并完成执行
    debugger.remove_breakpoint(bp_id1)
    debugger.remove_breakpoint(bp_id2)
    print("\n🗑️  移除所有断点，继续执行...")
    
    remaining_results = debugger.run_to_completion()
    print(f"✅ 执行完成，又执行了 {len(remaining_results)} 步")
    
    return debugger

def demo_performance_analysis():
    """演示性能分析功能"""
    print("\n" + "="*60)
    print("🎬 演示3: 性能分析功能")
    print("="*60)
    
    # 创建智能体和调试器
    agent = CognitiveAgent(
        llm=\1("gemini_2_5_flash"),
        max_cycles=4,
        verbose=False
    )
    debugger = CognitiveDebugger(agent)
    
    # 执行一个稍复杂的任务
    task = "创建一个简单的数据分析程序，读取CSV文件并计算平均值"
    print(f"📝 任务: {task}")
    debugger.start_debug(task)
    
    # 执行到完成
    print("\n🏃 执行任务...")
    results = debugger.run_to_completion()
    print(f"✅ 任务完成，共执行 {len(results)} 步")
    
    # 获取性能报告
    print("\n📊 性能分析报告:")
    report = debugger.get_performance_report()
    
    print(f"   ⏱️  总执行时间: {report.total_time:.3f}s")
    print(f"   📊 平均步骤耗时: {report.avg_step_time:.3f}s")
    print(f"   🐌 最慢步骤: {report.slowest_step}")
    print(f"   🚀 最快步骤: {report.fastest_step}")
    
    print(f"\n📈 步骤耗时分解:")
    for step_type, time_spent in report.step_time_breakdown.items():
        percentage = (time_spent / report.total_time) * 100 if report.total_time > 0 else 0
        print(f"   {step_type}: {time_spent:.3f}s ({percentage:.1f}%)")
    
    # 显示执行流程可视化
    print(f"\n🔄 执行流程可视化:")
    flow_chart = debugger.visualize_execution_flow()
    print(flow_chart)
    
    return debugger

def demo_state_inspection():
    """演示状态检查功能"""
    print("\n" + "="*60)
    print("🎬 演示4: 状态检查功能")
    print("="*60)
    
    # 创建智能体和调试器
    agent = CognitiveAgent(
        llm=\1("gemini_2_5_flash"),
        max_cycles=3,
        verbose=False
    )
    debugger = CognitiveDebugger(agent)
    
    task = "分析文本'Hello World'的字符统计"
    print(f"📝 任务: {task}")
    debugger.start_debug(task)
    
    # 执行几步并检查状态
    print("\n🔄 执行过程中的状态检查:")
    
    for i in range(3):
        # 执行一步
        step_result = debugger.run_one_step()
        if step_result is None or debugger.debug_state.is_finished:
            break
        
        print(f"\n--- 第 {i+1} 步后的状态 ---")
        
        # 检查状态
        snapshot = debugger.capture_debug_snapshot()
        if snapshot:
            print(f"📊 执行进度:")
            print(f"   当前步骤: {snapshot.current_step.value}")
            print(f"   循环轮数: {snapshot.cycle_count}")
            print(f"   已执行步骤: {snapshot.total_steps}")
            print(f"   执行时间: {snapshot.execution_time:.2f}s")
            print(f"   目标达成: {'✅' if snapshot.goal_achieved else '❌'}")
            
            print(f"\n🧠 认知状态:")
            if snapshot.current_state_analysis:
                print(f"   状态分析: {snapshot.current_state_analysis[:100]}...")
            if snapshot.id_evaluation:
                print(f"   本我评估: {snapshot.id_evaluation[:100]}...")
            
            print(f"\n💾 内存状态:")
            print(f"   消息数量: {snapshot.memory_length}")
            print(f"   Token使用: {snapshot.memory_tokens}")
    
    # 完成执行
    remaining_results = debugger.run_to_completion()
    print(f"\n✅ 任务完成，又执行了 {len(remaining_results)} 步")
    
    return debugger

def demo_session_export_import():
    """演示会话导出导入功能"""
    print("\n" + "="*60)
    print("🎬 演示5: 会话导出导入功能")
    print("="*60)
    
    # 创建智能体和调试器
    agent = CognitiveAgent(
        llm=\1("gemini_2_5_flash"),
        max_cycles=3,
        verbose=False
    )
    debugger = CognitiveDebugger(agent)
    
    # 执行一个任务
    task = "计算1到10的平方和"
    print(f"📝 任务: {task}")
    debugger.start_debug(task)
    
    results = debugger.run_to_completion()
    print(f"✅ 任务完成，共执行 {len(results)} 步")
    
    # 导出会话
    session_file = "demo_debug_session.json"
    print(f"\n💾 导出调试会话到: {session_file}")
    success = debugger.export_session(session_file)
    
    if success:
        print("✅ 会话导出成功")
        
        # 检查文件大小
        file_size = os.path.getsize(session_file)
        print(f"   文件大小: {file_size} 字节")
        
        # 导入会话（演示）
        print(f"\n📥 导入调试会话...")
        import_success = debugger.import_session(session_file)
        
        if import_success:
            print("✅ 会话导入成功（仅用于查看数据）")
        
        # 清理文件
        os.remove(session_file)
        print(f"🗑️  清理临时文件: {session_file}")
    
    return debugger

def main():
    """主演示函数"""
    print("🚀 CognitiveDebugger 功能演示")
    print("展示认知调试器的各种调试功能")
    print("=" * 80)
    
    try:
        # 运行各种演示
        demos = [
            demo_basic_debugging,
            demo_breakpoint_debugging,
            demo_performance_analysis,
            demo_state_inspection,
            demo_session_export_import
        ]
        
        for i, demo_func in enumerate(demos, 1):
            print(f"\n🎯 运行演示 {i}/{len(demos)}: {demo_func.__name__}")
            try:
                demo_func()
                print(f"✅ 演示 {i} 完成")
            except Exception as e:
                print(f"❌ 演示 {i} 失败: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*80)
        print("🎉 所有演示完成！")
        print("\n📚 更多功能请参考:")
        print("   - API文档: ai_docs/cognitive_debugger_api.md")
        print("   - 快速入门: ai_docs/cognitive_debugger_quickstart.md")
        print("   - 设计文档: ai_docs/cognitive_debugger_design.md")
        
    except KeyboardInterrupt:
        print("\n⚠️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()