"""
认知调试智能体演示程序

展示认知调试智能体的调试、监控功能和Gemini Flash集成。
包含认知断点、异步监控、单步跟踪等高级调试功能。
"""

import sys
import os
import time
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pythonTask import Agent, llm_deepseek

# 导入本地模块
try:
    # 首先尝试包导入
    from embodied_cognitive_workflow import (
        CognitiveAgent, 
        create_cognitive_agent,
        CognitiveDebugAgent,
        CognitiveDebugger,
        DebugLevel,
        GeminiFlashClient,
        create_gemini_client,
        CognitiveDebugVisualizer
    )
except ImportError:
    # 直接从当前目录导入
    from embodied_cognitive_workflow import (
        CognitiveAgent, 
        create_cognitive_agent,
        EmbodiedCognitiveWorkflow,
        create_embodied_cognitive_workflow, 
        execute_embodied_cognitive_task
    )
    from cognitive_debug_agent import CognitiveDebugAgent, CognitiveDebugger, DebugLevel
    from gemini_flash_integration import GeminiFlashClient, create_gemini_client
    from cognitive_debug_visualizer import CognitiveDebugVisualizer


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demo_basic_cognitive_debug():
    """演示基础认知调试功能"""
    print("=" * 60)
    print("🔍 基础认知调试智能体演示")
    print("=" * 60)
    
    # 创建基础智能体
    print("1. 创建基础智能体...")
    base_agent = Agent(llm=llm_deepseek)
    
    # 创建认知智能体
    print("2. 创建认知智能体...")
    cognitive_agent = create_cognitive_agent(
        llm=llm_deepseek,
        ego_config={},
        id_config={},
        body_config={}
    )
    
    # 创建认知调试智能体
    print("3. 创建认知调试智能体...")
    debug_agent = CognitiveDebugAgent(
        cognitive_agent=cognitive_agent,
        llm=llm_deepseek,
        enable_debugging=True,
        enable_step_tracking=True
    )
    
    # 执行任务
    print("4. 执行调试监控任务...")
    instruction = "计算1+1的结果并解释原理"
    result = debug_agent.execute_with_debugging(instruction, DebugLevel.DETAILED)
    
    print(f"执行结果: {result.return_value}")
    
    # 获取调试摘要
    print("5. 获取调试摘要...")
    summary = debug_agent.get_debug_summary()
    print(f"调试摘要: {summary}")
    
    return debug_agent


def demo_debugging_features(debug_agent):
    """演示调试功能"""
    print("\n" + "=" * 60)
    print("🔍 高级调试功能演示")
    print("=" * 60)
    
    debugger = debug_agent.debugger
    if not debugger:
        print("调试器未启用")
        return
    
    # 设置断点
    print("1. 设置认知断点...")
    bp1 = debugger.set_cognitive_breakpoint("自我", "如果执行失败")
    bp2 = debugger.set_cognitive_breakpoint("本我", "如果包含错误")
    bp3 = debugger.set_cognitive_breakpoint("身体", "如果执行时间超过5秒")
    
    print(f"设置了3个断点: {bp1}, {bp2}, {bp3}")
    
    # 启动调试模式
    print("2. 启动调试模式...")
    debugger.is_debugging = True
    
    # 执行一些任务来触发断点
    print("3. 执行测试任务...")
    test_instructions = [
        "计算2+2",
        "写一个hello world程序",
        "解释什么是AI"
    ]
    
    for instruction in test_instructions:
        print(f"   执行: {instruction}")
        result = debug_agent.execute_with_debugging(instruction, DebugLevel.FULL)
        print(f"   结果: {'成功' if result.success else '失败'}")
        time.sleep(1)
    
    # 显示调试摘要
    print("4. 调试摘要...")
    debug_summary = debugger.get_debug_summary()
    print(f"调试摘要: {debug_summary}")
    
    # 显示认知轨迹
    print("5. 认知轨迹...")
    trace = debug_agent.get_cognitive_trace()
    print(f"记录了 {len(trace)} 个认知步骤")
    
    if trace:
        print("最新的5个步骤:")
        for step in trace[-5:]:
            print(f"   {step.step_id}: {step.layer} - {step.action} ({'成功' if step.success else '失败'})")


def demo_gemini_integration():
    """演示Gemini Flash集成"""
    print("\n" + "=" * 60)
    print("🚀 Gemini Flash集成演示")
    print("=" * 60)
    
    # 检查网络环境提示
    print("📍 注意：在中国大陆地区，Google Gemini服务通常无法直接访问")
    print("   如需使用Gemini功能，请确保：")
    print("   1. 设置了有效的代理服务器")
    print("   2. 配置了 GEMINI_API_KEY 环境变量")
    print("   3. 代理服务器能够稳定访问Google API")
    print()
    
    # 尝试创建Gemini客户端
    print("1. 尝试创建Gemini Flash客户端...")
    
    try:
        gemini_client = create_gemini_client()
        
        if not gemini_client:
            print("⚠️  Gemini Flash客户端创建失败")
            print("   可能的原因：")
            print("   - 未设置 GEMINI_API_KEY 环境变量")
            print("   - 网络无法访问Google API服务")
            print("   - 代理服务器配置问题")
            print("\n🔄 跳过Gemini集成演示，使用基础调试功能...")
            return None
        
        print("✅ Gemini Flash客户端创建成功")
        
        # 健康检查
        print("2. 执行网络连接健康检查...")
        if gemini_client.health_check():
            print("✅ Gemini Flash服务连接正常")
        else:
            print("❌ Gemini Flash服务连接失败")
            print("   可能的原因：")
            print("   - 网络连接不稳定")
            print("   - Google API服务被阻断")
            print("   - 代理配置有问题")
            print("\n🔄 跳过Gemini集成演示...")
            return None
            
    except Exception as e:
        print(f"❌ Gemini客户端初始化异常: {e}")
        print("   这通常表示网络访问受限")
        print("🔄 跳过Gemini集成演示...")
        return None
    
    # 测试断点条件评估
    print("3. 测试智能断点条件评估...")
    test_context = {
        "layer": "自我",
        "action": "执行Python代码",
        "success": False,
        "error_message": "NameError: name 'undefined_var' is not defined",
        "execution_time": 0.5
    }
    
    test_conditions = [
        "如果执行失败",
        "如果包含NameError错误",
        "如果执行时间超过1秒",
        "如果是成功的执行"
    ]
    
    for condition in test_conditions:
        result = gemini_client.evaluate_breakpoint_condition(condition, test_context)
        print(f"   条件: '{condition}' -> {result}")
    
    # 测试Bug分析
    print("4. 测试智能Bug分析...")
    bug_step_data = {
        "step_id": "test_step_001",
        "layer": "身体",
        "action": "执行代码",
        "success": False,
        "error_message": "IndentationError: unexpected indent",
        "execution_time": 0.1,
        "input_data": "print('hello world')\n  print('bad indent')",
        "output_data": None
    }
    
    bug_analysis = gemini_client.analyze_bug_potential(bug_step_data)
    print(f"   Bug分析结果:")
    print(f"     有Bug: {bug_analysis.get('has_bug', False)}")
    print(f"     严重程度: {bug_analysis.get('severity', 'unknown')}")
    print(f"     描述: {bug_analysis.get('description', 'N/A')}")
    print(f"     修复建议: {bug_analysis.get('fix_suggestion', 'N/A')}")
    
    return gemini_client


def demo_cognitive_debug_without_gemini():
    """演示不依赖Gemini的认知调试功能"""
    print("\n" + "=" * 60)
    print("🔍 基础认知调试功能演示（无需Gemini）")
    print("=" * 60)
    
    # 创建基础组件
    print("1. 创建认知调试智能体...")
    base_agent = Agent(llm=llm_deepseek)
    cognitive_agent = create_cognitive_agent(
        llm=llm_deepseek,
        ego_config={},
        id_config={},
        body_config={}
    )
    
    # 创建不依赖Gemini的认知调试智能体
    debug_agent = CognitiveDebugAgent(
        cognitive_agent=cognitive_agent,
        llm=llm_deepseek,
        gemini_flash_client=None,  # 不使用Gemini
        enable_debugging=True,
        enable_step_tracking=True
    )
    
    print("✅ 基础认知调试智能体创建成功")
    
    # 设置传统断点
    print("2. 设置基础调试断点...")
    debug_agent.set_debug_breakpoint("自我", "执行失败")
    debug_agent.set_debug_breakpoint("身体", "执行时间过长")
    debug_agent.set_debug_breakpoint("本我", "包含错误")
    
    # 执行测试任务
    print("3. 执行测试任务...")
    tasks = [
        "计算1+1并解释数学原理",
        "写一个简单的Python函数",
        "解释什么是认知工作流",
        "创建一个包含错误的代码示例"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n   任务 {i}: {task}")
        start_time = time.time()
        
        result = debug_agent.execute_with_debugging(task, DebugLevel.DETAILED)
        
        execution_time = time.time() - start_time
        print(f"   结果: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"   执行时间: {execution_time:.2f}秒")
        
        if not result.success:
            print(f"   错误信息: {result.error_message}")
        
        # 模拟短暂等待
        time.sleep(0.5)
    
    # 显示调试统计
    print("\n4. 调试统计信息...")
    summary = debug_agent.get_debug_summary()
    print(f"   总任务数: {summary['performance_metrics']['total_tasks']}")
    print(f"   成功任务: {summary['performance_metrics']['successful_tasks']}")
    print(f"   失败任务: {summary['performance_metrics']['failed_tasks']}")
    print(f"   平均执行时间: {summary['performance_metrics']['average_execution_time']:.2f}秒")
    
    # 显示认知轨迹
    print("5. 认知轨迹分析...")
    trace = debug_agent.get_cognitive_trace()
    print(f"   记录了 {len(trace)} 个认知步骤")
    
    if trace:
        print("   最新的认知步骤:")
        for step in trace[-3:]:  # 显示最近3个步骤
            status = "✅ 成功" if step.success else "❌ 失败"
            print(f"   - {step.step_id}: {step.layer} -> {step.action} ({status})")
    
    # 显示调试器状态
    print("6. 调试器状态...")
    if debug_agent.debugger:
        breakpoints = debug_agent.debugger.get_all_breakpoints()
        print(f"   活动断点数: {len(breakpoints)}")
        for bp in breakpoints[:3]:  # 显示前3个断点
            print(f"   - {bp.breakpoint_id}: {bp.layer} -> {bp.condition}")
    
    print("\n✅ 基础认知调试功能演示完成")
    print("💡 提示：这些功能不需要网络连接，完全本地运行")
    
    return debug_agent


def demo_cognitive_debug_with_gemini():
    """演示带Gemini集成的认知调试"""
    print("\n" + "=" * 60)
    print("🌟 认知调试 + Gemini Flash 完整演示")
    print("=" * 60)
    
    # 创建Gemini客户端
    print("🔍 尝试启用Gemini Flash智能分析...")
    gemini_client = create_gemini_client()
    if not gemini_client:
        print("⚠️  Gemini Flash不可用，使用基础调试功能演示")
        print("   （在中国大陆，这是正常情况）")
        return demo_cognitive_debug_without_gemini()
    
    # 创建基础组件
    base_agent = Agent(llm=llm_deepseek)
    cognitive_agent = create_cognitive_agent(
        llm=llm_deepseek,
        ego_config={},
        id_config={},
        body_config={}
    )
    
    # 创建带Gemini的认知调试智能体
    debug_agent = CognitiveDebugAgent(
        cognitive_agent=cognitive_agent,
        llm=llm_deepseek,
        gemini_flash_client=gemini_client,
        enable_debugging=True,
        enable_step_tracking=True
    )
    
    print("✅ 认知调试智能体（带Gemini Flash）创建成功")
    
    # 设置智能断点
    print("1. 设置智能断点...")
    debug_agent.set_debug_breakpoint("自我", "如果执行失败或包含语法错误")
    debug_agent.set_debug_breakpoint("身体", "如果执行时间超过3秒")
    
    # 执行复杂任务
    print("2. 执行复杂任务...")
    tasks = [
        "写一个冒泡排序算法",
        "计算斐波那契数列的第10项",
        "故意制造一个语法错误的代码",  # 这应该触发断点
        "解释机器学习的基本概念"
    ]
    
    for task in tasks:
        print(f"\n   任务: {task}")
        start_time = time.time()
        
        result = debug_agent.execute_with_debugging(task, DebugLevel.FULL)
        
        execution_time = time.time() - start_time
        print(f"   结果: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"   执行时间: {execution_time:.2f}秒")
        
        # 检查是否有新的Bug报告
        bugs = debug_agent.get_bug_reports()
        if bugs:
            latest_bug = bugs[-1]
            print(f"   🐛 发现Bug: {latest_bug.description}")
    
    # 显示最终统计
    print("\n3. 最终统计...")
    summary = debug_agent.get_debug_summary()
    print(f"   总任务数: {summary['performance_metrics']['total_tasks']}")
    print(f"   成功任务: {summary['performance_metrics']['successful_tasks']}")
    print(f"   失败任务: {summary['performance_metrics']['failed_tasks']}")
    print(f"   平均执行时间: {summary['performance_metrics']['average_execution_time']:.2f}秒")
    
    bugs = debug_agent.get_bug_reports()
    print(f"   Bug报告数: {len(bugs)}")
    
    trace = debug_agent.get_cognitive_trace()
    print(f"   认知步骤数: {len(trace)}")
    
    return debug_agent


def demo_visualizer(debug_agent):
    """演示可视化界面"""
    print("\n" + "=" * 60)
    print("📊 可视化调试界面演示")
    print("=" * 60)
    
    try:
        print("启动可视化调试器...")
        print("注意：这将打开一个GUI窗口")
        print("关闭窗口可返回主程序")
        
        visualizer = CognitiveDebugVisualizer(debug_agent)
        visualizer.run()
        
    except Exception as e:
        print(f"可视化界面启动失败: {e}")
        print("可能需要安装GUI相关依赖（tkinter, matplotlib）")


def main():
    """主演示函数"""
    setup_logging()
    
    print("🔍 认知调试智能体完整演示")
    print("包含智能调试、监控分析等功能")
    print("=" * 60)
    print("📍 演示说明：")
    print("   - 基础认知调试功能：完全本地运行，无需网络")
    print("   - Gemini Flash集成：需要Google API访问权限")
    print("   - 在中国大陆地区，Gemini功能通常无法使用")
    print("   - 演示程序会自动适配可用功能")
    
    try:
        # 基础功能演示
        print("\n" + "=" * 60)
        print("🚀 第一阶段：基础认知调试功能")
        print("=" * 60)
        debug_agent = demo_basic_cognitive_debug()
        
        # 调试功能演示
        print("\n" + "=" * 60)
        print("🔧 第二阶段：高级调试功能")
        print("=" * 60)
        demo_debugging_features(debug_agent)
        
        # Gemini集成演示
        print("\n" + "=" * 60)
        print("🌐 第三阶段：网络服务集成")
        print("=" * 60)
        gemini_client = demo_gemini_integration()
        
        # 完整集成演示
        print("\n" + "=" * 60)
        print("🌟 第四阶段：综合功能演示")
        print("=" * 60)
        if gemini_client:
            print("✅ 启用Gemini智能分析功能")
            enhanced_debug_agent = demo_cognitive_debug_with_gemini()
        else:
            print("🔄 使用基础调试功能（推荐中国大陆用户）")
            enhanced_debug_agent = demo_cognitive_debug_without_gemini()
        
        # 询问是否启动可视化界面
        print("\n" + "=" * 60)
        print("📊 可视化界面（可选）")
        print("=" * 60)
        print("💡 提示：可视化界面需要GUI环境支持")
        user_input = input("是否启动可视化调试界面？(y/N): ")
        
        if user_input.lower() in ['y', 'yes']:
            demo_visualizer(enhanced_debug_agent)
        else:
            print("✅ 跳过可视化界面演示")
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        print("📋 演示总结：")
        print("   ✅ 认知智能体：三层架构（自我、本我、身体）")
        print("   ✅ 调试功能：断点、轨迹跟踪、性能监控")
        print("   ✅ 本地运行：无需网络连接")
        if gemini_client:
            print("   ✅ 智能分析：Gemini Flash集成")
        else:
            print("   ⚠️  智能分析：网络受限，使用基础功能")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n感谢使用认知调试智能体演示程序！")
        print("💡 更多功能和文档，请查看项目文档")
        print("🌐 项目地址：https://github.com/your-repo/embodied-cognitive-workflow")


if __name__ == "__main__":
    main()