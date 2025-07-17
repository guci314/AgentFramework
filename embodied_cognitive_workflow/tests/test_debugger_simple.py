#!/usr/bin/env python3
"""
简单的CognitiveDebugger测试
直接导入模块避免包导入问题
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
    # 直接导入
    from embodied_cognitive_workflow.embodied_cognitive_workflow import CognitiveAgent, WorkflowContext, DecisionType
    from embodied_cognitive_workflow.cognitive_debugger import CognitiveDebugger, StepType, DebugUtils
    from agent_base import Result
    from python_core import *
from llm_lazy import get_model
    
    print("✅ 所有模块导入成功！")
    
    # 测试数据结构
    print("\n🧪 测试数据结构...")
    
    # 测试StepType枚举
    print(f"StepType.INIT: {StepType.INIT.value}")
    print(f"StepType.COMPLEXITY_EVAL: {StepType.COMPLEXITY_EVAL.value}")
    print(f"StepType.COMPLETED: {StepType.COMPLETED.value}")
    
    # 测试调试器创建
    print("\n🧪 测试调试器创建...")
    
    # 创建模拟的智能体
    from unittest.mock import Mock
    mock_agent = Mock()
    mock_agent.max_cycles = 3
    mock_agent.enable_meta_cognition= False
    mock_agent.evaluation_mode = "internal"
    
    # 创建调试器
    debugger = CognitiveDebugger(mock_agent)
    print(f"✅ 调试器创建成功")
    print(f"   当前步骤: {debugger.debug_state.current_step}")
    print(f"   循环计数: {debugger.debug_state.cycle_count}")
    print(f"   是否完成: {debugger.debug_state.is_finished}")
    
    # 测试断点功能
    print("\n🧪 测试断点功能...")
    
    bp_id = debugger.set_breakpoint(
        StepType.STATE_ANALYSIS,
        description="测试断点"
    )
    print(f"✅ 断点设置成功: {bp_id}")
    
    breakpoints = debugger.list_breakpoints()
    print(f"✅ 断点列表获取成功，共 {len(breakpoints)} 个断点")
    
    success = debugger.remove_breakpoint(bp_id)
    print(f"✅ 断点移除: {'成功' if success else '失败'}")
    
    # 测试性能分析
    print("\n🧪 测试性能分析...")
    
    # 创建测试步骤结果
    from datetime import datetime
    test_steps = []
    for i in range(3):
        step_result = Mock()
        step_result.step_type = StepType.INIT
        step_result.execution_time = 0.1 + i * 0.1
        step_result.agent_layer = "System"
        step_result.error = None
        step_result.debug_info = {}
        test_steps.append(step_result)
    
    # 测试性能分析
    report = DebugUtils.analyze_performance(test_steps)
    print(f"✅ 性能分析成功")
    print(f"   总时间: {report.total_time:.3f}s")
    print(f"   平均时间: {report.avg_step_time:.3f}s")
    
    # 测试可视化
    flow_chart = DebugUtils.visualize_execution_flow(test_steps)
    print(f"✅ 流程可视化成功")
    print(f"   输出长度: {len(flow_chart)} 字符")
    
    # 测试导出/导入
    print("\n🧪 测试会话导出/导入...")
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        # 创建测试调试状态
        from embodied_cognitive_workflow.cognitive_debugger import DebugState
        debug_state = DebugState()
        debug_state.current_step = StepType.STATE_ANALYSIS
        debug_state.cycle_count = 2
        
        # 测试导出
        success = DebugUtils.export_debug_session(debug_state, temp_file)
        print(f"✅ 会话导出: {'成功' if success else '失败'}")
        
        # 测试导入
        imported_data = DebugUtils.import_debug_session(temp_file)
        success = imported_data is not None
        print(f"✅ 会话导入: {'成功' if success else '失败'}")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    print("\n🎉 所有基础测试通过！CognitiveDebugger 核心功能正常")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)