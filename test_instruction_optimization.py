#!/usr/bin/env python3
"""
测试状态感知指令优化系统

本测试验证：
1. 指令优化器初始化
2. 不同类型的指令优化
3. 状态感知的优化策略
4. 优化效果评估
5. 优化统计和监控
"""

import sys
import traceback
from datetime import datetime as dt
from enhancedAgent_v2 import (
    MultiStepAgent_v2, RegisteredAgent, WorkflowState,
    StateAwareInstructionOptimizer, InstructionOptimizationType,
    OptimizationStrategy, InstructionOptimizationResult
)
from pythonTask import Agent, llm_deepseek

def create_test_agent():
    """创建测试用的MultiStepAgent_v2实例"""
    # 创建一个简单的注册代理
    test_registered_agent = RegisteredAgent(
        name="test_agent",
        instance=Agent(llm=llm_deepseek, stateful=True),
        description="测试代理"
    )
    
    # 创建MultiStepAgent_v2实例
    agent = MultiStepAgent_v2(
        llm=llm_deepseek,
        registered_agents=[test_registered_agent],
        max_retries=3
    )
    
    return agent

def setup_test_state(agent):
    """设置测试状态"""
    # 设置有意义的全局状态
    state_content = """
    [项目初始化] 项目已启动，Python环境配置完成
    [配置管理] 数据库连接已建立，API密钥已配置
    [错误记录] 之前在文件操作中遇到权限错误，已解决
    [进度跟踪] 前端组件开发完成60%，后端API开发完成40%
    [依赖关系] Redis缓存服务正常运行，日志系统已激活
    """
    
    agent.workflow_state.set_global_state(state_content, "test_setup")
    
    # 添加一些状态历史
    agent.workflow_state.set_global_state(
        state_content + "\n[测试更新] 添加了新的错误处理逻辑", 
        "test_update_1"
    )
    
    return agent.workflow_state

def test_basic_optimization():
    """测试基本指令优化功能"""
    print("=" * 60)
    print("测试 1: 基本指令优化功能")
    print("=" * 60)
    
    try:
        # 创建测试代理
        agent = create_test_agent()
        
        # 验证优化器初始化
        assert hasattr(agent, 'instruction_optimizer'), "指令优化器未正确初始化"
        assert agent.optimization_enabled, "指令优化未默认启用"
        
        print("✅ 指令优化器初始化成功")
        
        # 设置测试状态
        global_state = setup_test_state(agent)
        
        # 创建测试步骤
        test_step = {
            'id': 'test_step_1',
            'name': 'API开发',
            'type': 'development',
            'description': '创建用户认证API端点',
            'expected_output': 'JWT认证端点',
            'dependencies': ['config_step', 'db_step']
        }
        
        # 测试简单指令优化
        simple_instruction = "创建API"
        optimization_context = {
            'previous_results': ['配置完成', '数据库连接成功'],
            'workflow_state': global_state,
            'agent_instance': agent
        }
        
        # 检查是否可以优化
        can_optimize = agent.instruction_optimizer.can_optimize(
            simple_instruction, test_step, global_state, optimization_context
        )
        
        print(f"✅ 指令优化可用性检查: {can_optimize}")
        
        if can_optimize:
            # 执行优化
            optimization_result = agent.instruction_optimizer.optimize_instruction(
                simple_instruction, test_step, global_state, optimization_context
            )
            
            print(f"✅ 指令优化执行成功")
            print(f"   原始指令长度: {len(optimization_result.original_instruction)}")
            print(f"   优化后指令长度: {len(optimization_result.optimized_instruction)}")
            print(f"   置信度: {optimization_result.confidence_score:.2f}")
            print(f"   预期改进: {optimization_result.predicted_improvement:.2f}")
            print(f"   应用的优化: {', '.join(optimization_result.applied_enhancements)}")
            print(f"   优化理由: {optimization_result.optimization_reasoning}")
            
            # 验证优化类型
            expected_types = [
                InstructionOptimizationType.CONTEXT_ENHANCEMENT,
                InstructionOptimizationType.CLARITY_OPTIMIZATION
            ]
            
            found_types = [opt_type for opt_type in expected_types 
                          if opt_type in optimization_result.optimization_types]
            
            print(f"✅ 发现预期的优化类型: {[t.value for t in found_types]}")
            
        return True
        
    except Exception as e:
        print(f"❌ 基本优化测试失败: {e}")
        traceback.print_exc()
        return False

def test_optimization_statistics():
    """测试优化统计功能"""
    print("\n" + "=" * 60)
    print("测试 2: 优化统计功能")
    print("=" * 60)
    
    try:
        agent = create_test_agent()
        global_state = setup_test_state(agent)
        
        # 重置统计
        agent.reset_optimization_statistics()
        
        # 执行多次优化
        instructions = [
            "创建API",
            "配置数据库",
            "部署应用",
            "运行测试",
            "更新文档"
        ]
        
        test_step = {
            'id': 'stats_test',
            'name': '统计测试',
            'type': 'development'
        }
        
        optimization_context = {
            'workflow_state': global_state,
            'agent_instance': agent
        }
        
        for i, instruction in enumerate(instructions):
            test_step['id'] = f'stats_test_{i+1}'
            
            if agent.instruction_optimizer.can_optimize(instruction, test_step, global_state, optimization_context):
                agent.instruction_optimizer.optimize_instruction(
                    instruction, test_step, global_state, optimization_context
                )
        
        # 获取统计信息
        stats = agent.get_optimization_statistics()
        
        print(f"✅ 优化统计结果:")
        print(f"   总优化次数: {stats['total_optimizations']}")
        print(f"   成功优化次数: {stats['successful_optimizations']}")
        print(f"   成功率: {stats['success_rate']:.2f}")
        print(f"   平均置信度: {stats['average_confidence']:.2f}")
        print(f"   平均改进度: {stats['average_improvement']:.2f}")
        print(f"   优化类型使用情况: {stats['optimization_types_used']}")
        
        # 验证统计数据
        assert stats['total_optimizations'] > 0, "总优化次数应大于0"
        assert stats['success_rate'] >= 0.0 and stats['success_rate'] <= 1.0, "成功率应在0-1之间"
        
        print("✅ 统计数据验证通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 统计测试失败: {e}")
        traceback.print_exc()
        return False

def test_integrated_state_aware_instruction():
    """测试集成的状态感知指令生成"""
    print("\n" + "=" * 60)
    print("测试 3: 集成的状态感知指令生成")
    print("=" * 60)
    
    try:
        agent = create_test_agent()
        global_state = setup_test_state(agent)
        
        # 创建测试步骤
        test_step = {
            'id': 'integrated_test',
            'name': 'API集成测试',
            'type': 'testing',
            'description': '执行完整的API集成测试',
            'expected_output': '测试报告',
            'dependencies': ['api_dev', 'db_setup']
        }
        
        original_instruction = "运行测试"
        previous_results = [
            "API开发完成",
            "数据库配置成功",
            "单元测试通过"
        ]
        
        # 生成状态感知指令（包含优化）
        enhanced_instruction = agent._generate_state_aware_instruction(
            test_step, original_instruction, previous_results, global_state
        )
        
        print(f"✅ 状态感知指令生成成功")
        print(f"   原始指令: '{original_instruction}'")
        print(f"   增强指令长度: {len(enhanced_instruction)} 字符")
        
        # 验证指令包含预期内容
        expected_sections = [
            "## 任务指令",
            "## 🎯 相关状态上下文",
            "## 💡 智能执行提示"
        ]
        
        for section in expected_sections:
            if section in enhanced_instruction:
                print(f"   ✅ 包含部分: {section}")
            else:
                print(f"   ⚠️ 缺少部分: {section}")
        
        # 检查是否包含优化信息
        if "## 🔧 指令优化信息" in enhanced_instruction:
            print(f"   ✅ 包含指令优化信息")
        else:
            print(f"   ℹ️ 未应用指令优化（可能不满足优化条件）")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始测试状态感知指令优化系统")
    print("=" * 80)
    
    tests = [
        ("基本指令优化功能", test_basic_optimization),
        ("优化统计功能", test_optimization_statistics),
        ("集成的状态感知指令生成", test_integrated_state_aware_instruction)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 出现异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "=" * 80)
    print("🎯 测试结果总结")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！状态感知指令优化系统工作正常。")
        return True
    else:
        print(f"⚠️ 有 {total - passed} 个测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 