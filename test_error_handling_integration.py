#!/usr/bin/env python3
"""
测试状态驱动错误处理机制的完整集成

本测试验证：
1. 错误处理机制初始化
2. 不同类型错误的分类和处理
3. 状态感知的错误恢复
4. 错误统计和监控
5. 恢复动作的应用
"""

import sys
import traceback
from datetime import datetime as dt
from enhancedAgent_v2 import (
    MultiStepAgent_v2, RegisteredAgent, WorkflowState,
    WorkflowErrorType, WorkflowErrorContext, GenericErrorHandler,
    WorkflowErrorDispatcher
)
from python_core import Agent, get_model("deepseek_chat")

def create_test_agent():
    """创建测试用的MultiStepAgent_v2实例"""
    # 创建一个简单的注册代理
    test_registered_agent = RegisteredAgent(
        name="test_agent",
        instance=Agent(llm=get_model("deepseek_chat"), stateful=True),
        description="测试代理"
    )
    
    # 创建MultiStepAgent_v2实例
    agent = MultiStepAgent_v2(
        llm=get_model("deepseek_chat"),
        registered_agents=[test_registered_agent],
        max_retries=3
    )
    
    return agent

def test_error_handler_initialization():
    """测试错误处理机制初始化"""
    print("=== 测试1: 错误处理机制初始化 ===")
    
    try:
        agent = create_test_agent()
        
        # 验证错误分发器存在
        assert hasattr(agent, 'error_dispatcher'), "错误分发器未初始化"
        assert isinstance(agent.error_dispatcher, WorkflowErrorDispatcher), "错误分发器类型不正确"
        
        # 验证错误统计存在
        assert hasattr(agent, 'error_statistics'), "错误统计未初始化"
        stats = agent.get_error_statistics()
        assert stats['total_errors'] == 0, "初始错误数量应为0"
        assert stats['handled_errors'] == 0, "初始处理错误数量应为0"
        
        print("✅ 错误处理机制初始化测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误处理机制初始化测试失败: {e}")
        traceback.print_exc()
        return False

def test_error_classification():
    """测试错误分类功能"""
    print("\n=== 测试2: 错误分类功能 ===")
    
    test_cases = [
        (FileNotFoundError("文件未找到"), WorkflowErrorType.FILE_ERROR),
        (PermissionError("权限不足"), WorkflowErrorType.PERMISSION_ERROR),
        (TimeoutError("操作超时"), WorkflowErrorType.TIMEOUT_ERROR),
        (ConnectionError("网络连接失败"), WorkflowErrorType.NETWORK_ERROR),
        (ValueError("值错误"), WorkflowErrorType.VALIDATION_ERROR),
        (Exception("未知错误"), WorkflowErrorType.UNKNOWN_ERROR),
    ]
    
    try:
        agent = create_test_agent()
        dispatcher = agent.error_dispatcher
        
        for error, expected_type in test_cases:
            classified_type = dispatcher.classify_error(error)
            assert classified_type == expected_type, \
                f"错误分类失败: {type(error).__name__} -> {classified_type}, 期望: {expected_type}"
            print(f"✅ {type(error).__name__} -> {classified_type.value}")
        
        print("✅ 错误分类测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误分类测试失败: {e}")
        traceback.print_exc()
        return False

def test_error_handling_workflow():
    """测试错误处理工作流"""
    print("\n=== 测试3: 错误处理工作流 ===")
    
    try:
        agent = create_test_agent()
        
        # 模拟工作流上下文
        context = {
            'plan': [{'id': 'test1', 'name': '测试步骤'}],
            'completed_steps': 0,
            'failed_steps': 0,
            'summary': '测试摘要',
            'start_time': dt.now(),
            'current_step': {
                'id': 'test1',
                'name': '测试步骤',
                'instruction': '执行测试',
                'agent_name': 'test_agent'
            }
        }
        
        # 模拟不同类型的错误
        test_errors = [
            FileNotFoundError("测试文件未找到"),
            PermissionError("测试权限错误"),
            TimeoutError("测试超时错误")
        ]
        
        for error in test_errors:
            print(f"\n处理错误: {type(error).__name__}")
            initial_stats = agent.get_error_statistics()
            
            # 调用错误处理
            agent._handle_workflow_error(context, error)
            
            # 验证统计更新
            updated_stats = agent.get_error_statistics()
            assert updated_stats['total_errors'] > initial_stats['total_errors'], \
                "总错误数量应该增加"
            
            print(f"✅ {type(error).__name__} 处理完成")
        
        # 验证最终统计
        final_stats = agent.get_error_statistics()
        print(f"\n最终统计:")
        print(f"  总错误: {final_stats['total_errors']}")
        print(f"  已处理: {final_stats['handled_errors']}")
        print(f"  未处理: {final_stats['unhandled_errors']}")
        print(f"  成功率: {final_stats['recovery_success_rate']:.2%}")
        
        assert final_stats['total_errors'] == len(test_errors), "总错误数量不正确"
        
        print("✅ 错误处理工作流测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误处理工作流测试失败: {e}")
        traceback.print_exc()
        return False

def test_recovery_actions():
    """测试恢复动作应用"""
    print("\n=== 测试4: 恢复动作应用 ===")
    
    try:
        agent = create_test_agent()
        context = {}
        
        # 测试不同的恢复动作
        recovery_actions = [
            "retry_step",
            "skip_step", 
            "pause_workflow",
            "continue_workflow",
            "delay_10",
            "generate_fix_task"
        ]
        
        for action in recovery_actions:
            print(f"应用恢复动作: {action}")
            agent._apply_recovery_action(action, context)
            
            if action == "retry_step":
                assert context.get('should_retry') is True, "重试标记未设置"
            elif action == "skip_step":
                assert context.get('should_skip') is True, "跳过标记未设置"
            elif action.startswith("delay_"):
                expected_delay = int(action.split("_")[1])
                assert context.get('delay_seconds') == expected_delay, "延迟时间设置不正确"
            
            print(f"✅ {action} 应用成功")
        
        print("✅ 恢复动作应用测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 恢复动作应用测试失败: {e}")
        traceback.print_exc()
        return False

def test_state_aware_error_handling():
    """测试状态感知的错误处理"""
    print("\n=== 测试5: 状态感知的错误处理 ===")
    
    try:
        agent = create_test_agent()
        
        # 设置全局状态
        agent.workflow_state.set_global_state("测试工作流正在执行文件操作")
        
        # 创建带有状态上下文的错误处理场景
        context = {
            'current_step': {
                'id': 'file_op',
                'name': '文件操作',
                'instruction': '读取配置文件',
                'agent_name': 'test_agent'
            },
            'plan': [{'id': 'file_op', 'name': '文件操作'}],
            'completed_steps': 0,
            'summary': '正在执行文件操作任务'
        }
        
        # 模拟文件操作错误
        file_error = FileNotFoundError("config.json 文件未找到")
        
        print("处理状态感知的文件错误...")
        agent._handle_workflow_error(context, file_error)
        
        # 验证状态更新
        updated_state = agent.workflow_state.get_global_state()
        print(f"更新后的状态: {updated_state}")
        
        # 验证状态历史
        state_history = agent.workflow_state.get_state_history()
        assert len(state_history) > 0, "状态历史应该有记录"
        
        # 验证错误统计
        stats = agent.get_error_statistics()
        assert 'file_error' in stats['error_types'], "文件错误类型统计应该存在"
        
        print("✅ 状态感知的错误处理测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 状态感知的错误处理测试失败: {e}")
        traceback.print_exc()
        return False

def test_error_statistics():
    """测试错误统计功能"""
    print("\n=== 测试6: 错误统计功能 ===")
    
    try:
        agent = create_test_agent()
        
        # 模拟多种错误
        context = {
            'current_step': {'id': 'test', 'name': '测试', 'instruction': '测试', 'agent_name': 'test'},
            'plan': [],
            'summary': ''
        }
        
        errors_to_test = [
            FileNotFoundError("文件1未找到"),
            FileNotFoundError("文件2未找到"),  # 重复类型
            PermissionError("权限错误"),
            TimeoutError("超时错误"),
        ]
        
        for error in errors_to_test:
            agent._handle_workflow_error(context, error)
        
        # 获取统计信息
        stats = agent.get_error_statistics()
        
        print("错误统计信息:")
        print(f"  总错误: {stats['total_errors']}")
        print(f"  已处理: {stats['handled_errors']}")  
        print(f"  未处理: {stats['unhandled_errors']}")
        print(f"  成功率: {stats['recovery_success_rate']:.2%}")
        print("  错误类型分布:")
        for error_type, count in stats['error_types'].items():
            print(f"    {error_type}: {count}")
        
        # 验证统计准确性
        assert stats['total_errors'] == len(errors_to_test), "总错误数量不正确"
        assert stats['error_types']['file_error'] == 2, "文件错误统计不正确"
        assert stats['error_types']['permission_error'] == 1, "权限错误统计不正确"
        assert stats['error_types']['timeout_error'] == 1, "超时错误统计不正确"
        
        # 测试统计重置
        agent.reset_error_statistics()
        reset_stats = agent.get_error_statistics()
        assert reset_stats['total_errors'] == 0, "统计重置后总错误数应为0"
        assert len(reset_stats['error_types']) == 0, "统计重置后错误类型应为空"
        
        print("✅ 错误统计功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误统计功能测试失败: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("开始运行状态驱动错误处理机制集成测试")
    print("=" * 50)
    
    tests = [
        test_error_handler_initialization,
        test_error_classification,
        test_error_handling_workflow,
        test_recovery_actions,
        test_state_aware_error_handling,
        test_error_statistics
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 发生异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！状态驱动错误处理机制集成成功！")
        print("\n主要功能验证:")
        print("✅ 错误处理机制初始化")
        print("✅ 错误分类和路由")
        print("✅ 状态感知的错误处理")
        print("✅ 恢复动作应用")
        print("✅ 错误统计和监控")
        print("✅ 完整的错误处理工作流")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 