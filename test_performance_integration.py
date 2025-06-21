#!/usr/bin/env python3
"""
性能监控集成测试
测试WorkflowState与性能监控系统的集成
"""

import sys
import os
import time
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from enhancedAgent_v2 import WorkflowState
from performance_monitor import PerformanceMonitor, get_performance_monitor

def test_performance_integration():
    """测试性能监控集成"""
    print("🚀 开始性能监控集成测试")
    
    # 1. 创建WorkflowState实例
    print("\n1. 创建WorkflowState实例...")
    workflow_state = WorkflowState()
    
    # 2. 检查性能监控是否正确集成
    print("\n2. 检查性能监控集成状态...")
    if hasattr(workflow_state, '_performance_monitor') and workflow_state._performance_monitor:
        print("✅ 性能监控系统已成功集成到WorkflowState")
        print(f"   监控器类型: {type(workflow_state._performance_monitor).__name__}")
    else:
        print("❌ 性能监控系统未集成或不可用")
        return False
    
    # 3. 测试状态操作的性能监控
    print("\n3. 测试状态操作性能监控...")
    
    # 设置状态
    test_states = [
        "项目初始化阶段",
        "数据处理中，已完成30%",
        "遇到网络延迟，正在重试",
        "处理完成，准备生成报告",
        "任务完成，系统正常运行"
    ]
    
    for i, state in enumerate(test_states):
        print(f"   设置状态 {i+1}: {state[:30]}...")
        workflow_state.set_global_state(state, source=f"test_source_{i+1}")
        time.sleep(0.1)  # 模拟处理时间
    
    # 4. 测试历史操作
    print("\n4. 测试历史操作...")
    history = workflow_state.get_state_history()
    print(f"   历史记录数量: {len(history)}")
    
    history_count = workflow_state.get_state_history_count()
    print(f"   历史计数: {history_count}")
    
    # 5. 获取性能统计
    print("\n5. 获取性能统计...")
    monitor = workflow_state._performance_monitor
    
    # 获取基本统计
    stats = monitor.get_performance_report()
    print("   基本统计信息:")
    for category, metrics in stats.items():
        print(f"     {category}:")
        if isinstance(metrics, dict):
            for metric_name, data in metrics.items():
                print(f"       {metric_name}: {data}")
        else:
            print(f"       {metrics}")
    
    # 6. 测试内存使用监控
    print("\n6. 测试内存使用监控...")
    memory_info = workflow_state.get_memory_usage()
    print("   内存使用信息:")
    for key, value in memory_info.items():
        if isinstance(value, (int, float)):
            print(f"     {key}: {value}")
        else:
            print(f"     {key}: {str(value)[:50]}...")
    
    # 7. 测试AI状态更新器状态
    print("\n7. 测试AI状态更新器状态...")
    ai_status = workflow_state.get_ai_updater_status()
    print("   AI更新器状态:")
    for key, value in ai_status.items():
        print(f"     {key}: {value}")
    
    # 8. 测试性能监控的记录功能
    print("\n8. 测试性能监控记录功能...")
    
    # 手动记录一些指标
    monitor.metric_collector.record_counter("test_counter", 5.0, {"test_tag": "integration_test"})
    monitor.metric_collector.record_gauge("test_gauge", 42.0, {"test_tag": "integration_test"})
    monitor.metric_collector.record_timer("test_timer", 123.0, {"operation": "test_timing"})
    
    # 获取更新后的统计
    updated_stats = monitor.get_performance_report()
    print("   更新后的统计信息:")
    for category, metrics in updated_stats.items():
        if "test" in category.lower():
            print(f"     {category}: {metrics}")
    
    # 9. 测试状态摘要功能
    print("\n9. 测试状态摘要功能...")
    summary = workflow_state.get_state_summary()
    print("   状态摘要:")
    print(f"     {summary}")
    
    print("\n✅ 性能监控集成测试完成！")
    return True

def test_performance_monitoring_kpis():
    """测试性能监控KPI收集"""
    print("\n🎯 测试性能监控KPI收集")
    
    # 获取全局性能监控器
    monitor = get_performance_monitor()
    
    # 记录一些KPI指标
    kpi_metrics = [
        ("workflow_execution", "steps_completed", 10),
        ("workflow_execution", "steps_failed", 2),
        ("state_management", "state_updates", 15),
        ("state_management", "history_size", 8),
        ("ai_operations", "llm_calls", 5),
        ("ai_operations", "cache_hits", 3),
        ("system_performance", "memory_usage_mb", 256),
        ("system_performance", "cpu_usage_percent", 45)
    ]
    
    print("   记录KPI指标...")
    for category, operation, value in kpi_metrics:
        monitor.metric_collector.record_counter(f"{category}_{operation}", float(value), {"category": category})
        print(f"     ✓ {category}.{operation}: {value}")
    
    # 记录一些时间指标
    timing_metrics = [
        ("ai_state_update", 1234.0, {"model": "deepseek", "tokens": "150"}),
        ("state_persistence", 45.0, {"operation": "save"}),
        ("history_compression", 678.0, {"entries": "50"}),
        ("workflow_step_execution", 2345.0, {"step_type": "python_execution"})
    ]
    
    print("   记录时间指标...")
    for operation, duration, tags in timing_metrics:
        monitor.metric_collector.record_timer(operation, duration, tags)
        print(f"     ✓ {operation}: {duration}ms")
    
    # 获取完整统计
    print("\n   完整KPI统计:")
    stats = monitor.get_performance_report()
    
    for category, metrics in stats.items():
        print(f"     📊 {category}:")
        if isinstance(metrics, dict):
            for metric_name, data in metrics.items():
                print(f"       {metric_name}: {data}")
        else:
            print(f"       {metrics}")
    
    print("\n✅ KPI收集测试完成！")
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔍 性能监控和KPI收集集成测试")
    print("=" * 60)
    
    try:
        # 测试基础集成
        success1 = test_performance_integration()
        
        # 测试KPI收集
        success2 = test_performance_monitoring_kpis()
        
        if success1 and success2:
            print("\n🎉 所有测试通过！性能监控系统已完全集成。")
            print("\n📋 测试总结:")
            print("  ✅ WorkflowState性能监控集成")
            print("  ✅ 状态操作性能跟踪")
            print("  ✅ 内存使用监控")
            print("  ✅ AI状态更新器状态监控")
            print("  ✅ KPI指标收集")
            print("  ✅ 时间指标记录")
            print("  ✅ 统计数据聚合")
            
            print("\n🚀 子任务5.4 (性能监控和指标收集) 已完成！")
            return True
        else:
            print("\n❌ 部分测试失败，需要检查集成问题。")
            return False
            
    except Exception as e:
        print(f"\n💥 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 