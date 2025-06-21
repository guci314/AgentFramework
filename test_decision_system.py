#!/usr/bin/env python3
"""
测试状态感知决策系统

本测试验证：
1. 决策节点创建和配置
2. 状态条件评估
3. 决策路径选择
4. 决策统计和监控
5. 与MultiStepAgent_v2的集成
"""

import sys
import traceback
from datetime import datetime as dt
from enhancedAgent_v2 import (
    MultiStepAgent_v2, RegisteredAgent, WorkflowState,
    StateCondition, DecisionNode, StateAwareDecisionManager,
    DecisionNodeType, ConditionOperator, DecisionResult
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

def test_basic_decision_functionality():
    """测试基本决策功能"""
    print("🔍 测试1: 基本决策功能")
    
    try:
        agent = create_test_agent()
        
        # 设置初始状态
        agent.workflow_state.set_global_state("任务状态: 初始化\\n测试完成: false\\n错误计数: 0")
        
        # 创建条件：检查测试是否完成
        test_completed_condition = StateCondition(
            state_path="测试完成",
            operator=ConditionOperator.EQUALS,
            expected_value=True,
            description="检查测试是否完成"
        )
        
        # 创建条件决策节点
        decision_node = agent.add_conditional_decision(
            node_id="test_completion_check",
            condition=test_completed_condition,
            true_step="finish_workflow",
            false_step="continue_testing",
            description="测试完成检查决策节点"
        )
        
        print(f"   ✅ 创建决策节点: {decision_node.node_id}")
        
        # 评估决策（应该返回false分支）
        result = agent.evaluate_workflow_decision("test_completion_check")
        print(f"   ✅ 决策结果: {result.next_step_id} (置信度: {result.confidence:.2f})")
        print(f"   📋 决策原因: {result.decision_reason}")
        
        assert result.next_step_id == "continue_testing", f"期望 continue_testing，实际 {result.next_step_id}"
        assert result.decision_made == True, "决策应该成功"
        
        # 更新状态并重新评估
        agent.workflow_state.set_global_state("任务状态: 执行中\\n测试完成: true\\n错误计数: 0")
        
        result2 = agent.evaluate_workflow_decision("test_completion_check")
        print(f"   ✅ 更新状态后决策结果: {result2.next_step_id} (置信度: {result2.confidence:.2f})")
        
        assert result2.next_step_id == "finish_workflow", f"期望 finish_workflow，实际 {result2.next_step_id}"
        
        print("   🎉 基本决策功能测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 基本决策功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_validation_decision():
    """测试验证决策功能"""
    print("\\n🔍 测试2: 验证决策功能")
    
    try:
        agent = create_test_agent()
        
        # 设置包含错误计数的状态
        agent.workflow_state.set_global_state("项目状态: 构建中\\n错误计数: 3\\n成功率: 85%")
        
        # 创建验证条件：错误计数应该小于等于5
        error_threshold_condition = StateCondition(
            state_path="错误计数",
            operator=ConditionOperator.LESS_EQUAL,
            expected_value=5,
            description="检查错误计数是否在可接受范围内"
        )
        
        # 创建验证决策节点
        validation_node = agent.add_validation_decision(
            node_id="error_validation",
            condition=error_threshold_condition,
            valid_step="proceed_with_deployment",
            invalid_step="fix_errors_first",
            description="错误计数验证节点"
        )
        
        print(f"   ✅ 创建验证节点: {validation_node.node_id}")
        
        # 评估验证决策（3 <= 5应该为true，通过验证）
        result = agent.evaluate_workflow_decision("error_validation")
        print(f"   ✅ 验证结果: {result.next_step_id} (置信度: {result.confidence:.2f})")
        print(f"   📋 验证原因: {result.decision_reason}")
        
        assert result.next_step_id == "proceed_with_deployment", f"期望 proceed_with_deployment，实际 {result.next_step_id}"
        assert result.decision_made == True, "验证决策应该成功"
        
        # 更新状态到错误计数过高的情况
        agent.workflow_state.set_global_state("项目状态: 构建中\\n错误计数: 8\\n成功率: 65%")
        
        result2 = agent.evaluate_workflow_decision("error_validation")
        print(f"   ✅ 错误过多时验证结果: {result2.next_step_id} (置信度: {result2.confidence:.2f})")
        
        assert result2.next_step_id == "fix_errors_first", f"期望 fix_errors_first，实际 {result2.next_step_id}"
        
        print("   🎉 验证决策功能测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 验证决策功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_complex_state_conditions():
    """测试复杂状态条件"""
    print("\\n🔍 测试3: 复杂状态条件")
    
    try:
        agent = create_test_agent()
        
        # 设置复杂状态
        complex_state = '''
        {
            "deployment": {
                "status": "ready",
                "environment": "production",
                "health_score": 95
            },
            "approval": {
                "status": "pending",
                "required_approvers": ["manager", "security"],
                "received_approvals": ["manager"]
            }
        }
        '''
        agent.workflow_state.set_global_state(complex_state)
        
        # 创建包含文本匹配的条件
        approval_condition = StateCondition(
            state_path="approval",
            operator=ConditionOperator.CONTAINS,
            expected_value="pending",
            description="检查是否有待审批项目"
        )
        
        # 创建决策节点
        approval_node = agent.create_decision_node(
            node_id="approval_check",
            node_type=DecisionNodeType.CONDITIONAL,
            description="审批状态检查"
        )
        approval_node.add_condition(approval_condition)
        approval_node.add_decision_path("true", "wait_for_approval")
        approval_node.add_decision_path("false", "proceed_deployment")
        approval_node.set_default_path("manual_review")
        
        print(f"   ✅ 创建复杂条件节点: {approval_node.node_id}")
        
        # 评估决策
        result = agent.evaluate_workflow_decision("approval_check")
        print(f"   ✅ 复杂条件决策结果: {result.next_step_id} (置信度: {result.confidence:.2f})")
        print(f"   📋 评估的条件数量: {len(result.evaluated_conditions)}")
        print(f"   📋 使用的状态变量: {result.state_variables_used}")
        
        # 验证结果
        assert result.next_step_id == "wait_for_approval", f"期望 wait_for_approval，实际 {result.next_step_id}"
        assert len(result.evaluated_conditions) == 1, "应该评估1个条件"
        assert "approval" in result.state_variables_used, "应该使用approval变量"
        
        print("   🎉 复杂状态条件测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 复杂状态条件测试失败: {e}")
        traceback.print_exc()
        return False

def test_decision_statistics():
    """测试决策统计功能"""
    print("\\n🔍 测试4: 决策统计功能")
    
    try:
        agent = create_test_agent()
        
        # 重置统计
        agent.reset_decision_statistics()
        
        # 创建多个决策节点并执行决策
        for i in range(3):
            agent.workflow_state.set_global_state(f"iteration: {i}\\nstatus: running")
            
            condition = StateCondition(
                state_path="iteration",
                operator=ConditionOperator.EQUALS,
                expected_value=str(i),
                description=f"检查迭代{i}"
            )
            
            node = agent.add_conditional_decision(
                node_id=f"iter_check_{i}",
                condition=condition,
                true_step=f"process_{i}",
                false_step=f"skip_{i}",
                description=f"迭代{i}检查"
            )
            
            # 执行决策
            result = agent.evaluate_workflow_decision(f"iter_check_{i}")
            print(f"   ✅ 迭代 {i} 决策结果: {result.next_step_id}")
        
        # 获取统计信息
        stats = agent.get_decision_statistics()
        print(f"   📊 决策统计:")
        print(f"      总决策数: {stats['total_decisions']}")
        print(f"      成功决策数: {stats['successful_decisions']}")
        print(f"      平均置信度: {stats['average_confidence']:.2f}")
        print(f"      使用的决策类型: {stats['decision_types_used']}")
        print(f"      最常用变量: {stats['most_used_variables']}")
        
        # 验证统计数据
        assert stats['total_decisions'] == 3, f"期望3次决策，实际{stats['total_decisions']}"
        assert stats['successful_decisions'] == 3, f"期望3次成功，实际{stats['successful_decisions']}"
        assert stats['average_confidence'] > 0.0, "平均置信度应该大于0"
        
        # 列出所有决策节点
        nodes = agent.list_decision_nodes()
        print(f"   📋 注册的决策节点数量: {len(nodes)}")
        for node in nodes:
            print(f"      - {node['node_id']}: {node['node_type']} ({node['condition_count']}个条件)")
        
        assert len(nodes) >= 3, f"应该至少有3个决策节点，实际{len(nodes)}"
        
        print("   🎉 决策统计功能测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 决策统计功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_edge_cases():
    """测试边缘情况"""
    print("\\n🔍 测试5: 边缘情况处理")
    
    try:
        agent = create_test_agent()
        
        # 测试空状态
        agent.workflow_state.set_global_state("")
        
        empty_condition = StateCondition(
            state_path="nonexistent_key",
            operator=ConditionOperator.IS_EMPTY,
            expected_value=None,
            description="检查不存在的键"
        )
        
        empty_node = agent.add_conditional_decision(
            node_id="empty_check",
            condition=empty_condition,
            true_step="handle_empty",
            false_step="has_value",
            description="空值检查"
        )
        
        result = agent.evaluate_workflow_decision("empty_check")
        print(f"   ✅ 空状态决策结果: {result.next_step_id}")
        
        # 测试不存在的决策节点
        try:
            invalid_result = agent.evaluate_workflow_decision("nonexistent_node")
            assert not invalid_result.decision_made, "不存在的节点应该返回失败"
            print(f"   ✅ 不存在节点处理: {invalid_result.decision_reason}")
        except Exception:
            print("   ✅ 不存在节点处理正常抛出异常")
        
        # 测试正则表达式匹配
        agent.workflow_state.set_global_state("version: v1.2.3\\nbuild: 20240101")
        
        version_condition = StateCondition(
            state_path="version",
            operator=ConditionOperator.REGEX_MATCH,
            expected_value=r"v\\d+\\.\\d+\\.\\d+",
            description="检查版本号格式"
        )
        
        version_node = agent.add_conditional_decision(
            node_id="version_check",
            condition=version_condition,
            true_step="valid_version",
            false_step="invalid_version",
            description="版本号格式检查"
        )
        
        version_result = agent.evaluate_workflow_decision("version_check")
        print(f"   ✅ 版本号检查结果: {version_result.next_step_id}")
        assert version_result.next_step_id == "valid_version", "版本号格式应该有效"
        
        print("   🎉 边缘情况处理测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 边缘情况处理测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("🧪 开始状态感知决策系统测试")
    print("=" * 60)
    
    tests = [
        test_basic_decision_functionality,
        test_validation_decision,
        test_complex_state_conditions,
        test_decision_statistics,
        test_edge_cases
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\\n" + "=" * 60)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！状态感知决策系统工作正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 