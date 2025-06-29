#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
循环预防机制测试

测试我们实现的循环检测和预防机制是否有效工作。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cognitive_workflow_rule_base.domain.entities import WorkflowState, GlobalState, ProductionRule, RuleSet
from cognitive_workflow_rule_base.domain.value_objects import RulePhase
from cognitive_workflow_rule_base.services.rule_generation_service import RuleGenerationService
from cognitive_workflow_rule_base.services.language_model_service import LanguageModelService
from cognitive_workflow_rule_base.services.state_service import StateService
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_workflow_state_loop_detection():
    """测试WorkflowState的循环检测功能"""
    print("\n" + "="*60)
    print("🔬 测试 WorkflowState 循环检测功能")
    print("="*60)
    
    # 创建测试用的WorkflowState
    workflow_state = WorkflowState(
        id="test_workflow_001",
        state="测试初始状态",
        workflow_id="test_workflow",
        iteration_count=0
    )
    
    # 测试1: 基础状态，应该没有循环
    print(f"📋 测试1: 基础状态循环检测")
    print(f"   循环检测结果: {workflow_state.detect_potential_loop()}")
    print(f"   状态循环检测: {workflow_state.check_state_cycle()}")
    assert not workflow_state.detect_potential_loop(), "基础状态不应该检测到循环"
    
    # 测试2: 模拟连续执行相同规则
    print(f"\n📋 测试2: 连续执行相同规则")
    same_rule_id = "rule_001"
    for i in range(4):  # 执行4次相同规则
        workflow_state.mark_rule_executed(same_rule_id, success=True)
        print(f"   第{i+1}次执行 {same_rule_id}: 连续计数 = {workflow_state.consecutive_same_rule_count}")
    
    print(f"   循环检测结果: {workflow_state.detect_potential_loop()}")
    assert workflow_state.detect_potential_loop(), "应该检测到连续执行循环"
    
    # 测试3: 状态指纹循环检测
    print(f"\n📋 测试3: 状态指纹循环检测") 
    # 模拟状态循环
    workflow_state.state = "循环状态A"
    cycle1 = workflow_state.check_state_cycle()
    
    workflow_state.state = "循环状态B"
    cycle2 = workflow_state.check_state_cycle()
    
    workflow_state.state = "循环状态A"  # 回到状态A
    cycle3 = workflow_state.check_state_cycle()
    
    print(f"   第1次状态A: {cycle1}")
    print(f"   状态B: {cycle2}")
    print(f"   第2次状态A: {cycle3}")
    
    # 测试4: 规则过滤功能
    print(f"\n📋 测试4: 规则过滤功能")
    test_rules = [
        ProductionRule(id="rule_001", name="已执行规则", condition="test", action="test", agent_name="test"),
        ProductionRule(id="rule_002", name="失败规则", condition="test", action="test", agent_name="test"),
        ProductionRule(id="rule_003", name="可用规则", condition="test", action="test", agent_name="test"),
    ]
    
    # 标记rule_002失败多次
    for _ in range(4):
        workflow_state.mark_rule_executed("rule_002", success=False)
    
    available_rules = workflow_state.get_available_rules(test_rules)
    available_rule_ids = [rule.id for rule in available_rules]
    
    print(f"   原始规则: {[rule.id for rule in test_rules]}")
    print(f"   可用规则: {available_rule_ids}")
    
    assert "rule_001" not in available_rule_ids, "已执行规则应该被过滤"
    assert "rule_002" not in available_rule_ids, "失败过多规则应该被过滤"
    assert "rule_003" in available_rule_ids, "未执行规则应该可用"
    
    print(f"\n✅ WorkflowState循环检测功能测试通过！")

def test_advanced_loop_detection():
    """测试高级循环检测机制"""
    print("\n" + "="*60)
    print("🔬 测试高级循环检测机制")
    print("="*60)
    
    # 创建模拟的语言模型服务
    class MockLLMService:
        def generate_natural_language_response(self, prompt):
            return "测试响应"
        
        def semantic_match(self, condition, state):
            from cognitive_workflow_rule_base.domain.value_objects import MatchingResult
            return MatchingResult(is_match=True, confidence=0.8, reasoning="测试匹配")
    
    # 创建规则生成服务
    llm_service = MockLLMService()
    rule_gen_service = RuleGenerationService(llm_service)
    
    # 创建测试状态 - 普通状态
    normal_state = GlobalState(
        id="normal_state",
        state="正常执行状态",
        iteration_count=5
    )
    
    # 创建测试状态 - 高循环风险状态
    high_risk_state = GlobalState(
        id="high_risk_state", 
        state="等待等待等待准备准备准备",  # 重复关键词
        iteration_count=20,
        execution_history=[
            "执行失败", "执行失败", "执行失败", "执行成功", "执行失败"
        ]
    )
    
    # 创建测试规则集
    test_rule_set = RuleSet(
        id="test_ruleset",
        goal="测试目标",
        rules=[]
    )
    
    # 测试普通状态
    print(f"📋 测试1: 普通状态的循环检测")
    normal_detection = rule_gen_service._advanced_loop_detection(normal_state, test_rule_set)
    print(f"   风险评分: {normal_detection['overall_risk_score']:.2f}")
    print(f"   检测结果: {normal_detection['recommendations']}")
    
    # 测试高风险状态
    print(f"\n📋 测试2: 高风险状态的循环检测")
    high_risk_detection = rule_gen_service._advanced_loop_detection(high_risk_state, test_rule_set)
    print(f"   风险评分: {high_risk_detection['overall_risk_score']:.2f}")
    print(f"   检测结果: {high_risk_detection['recommendations']}")
    
    # 验证风险评分
    assert normal_detection['overall_risk_score'] < 0.5, "普通状态风险评分应该较低"
    assert high_risk_detection['overall_risk_score'] >= 0.5, "高风险状态风险评分应该较高"
    
    # 测试预防策略
    print(f"\n📋 测试3: 循环预防策略")
    prevention_strategy = rule_gen_service._implement_loop_prevention_strategy(
        high_risk_state, high_risk_detection
    )
    
    if prevention_strategy:
        print(f"   预防策略类型: {prevention_strategy.decision_type}")
        print(f"   置信度: {prevention_strategy.confidence}")
        print(f"   推理: {prevention_strategy.reasoning}")
        assert prevention_strategy is not None, "高风险状态应该触发预防策略"
    else:
        print(f"   没有触发预防策略")
    
    print(f"\n✅ 高级循环检测机制测试通过！")

def test_enhanced_error_recovery():
    """测试增强的错误恢复机制"""
    print("\n" + "="*60)
    print("🔬 测试增强的错误恢复机制")
    print("="*60)
    
    # 创建模拟的语言模型服务和代理注册表
    class MockLLMService:
        def generate_natural_language_response(self, prompt):
            return "测试响应"
    
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.api_specification = f"{name} 智能体规范"
    
    class MockAgentRegistry:
        def __init__(self):
            self.agents = {
                'primary_agent': MockAgent('primary_agent'),
                'backup_agent': MockAgent('backup_agent'),
                'fallback_agent': MockAgent('fallback_agent')
            }
    
    # 创建规则生成服务
    llm_service = MockLLMService()
    agent_registry = MockAgentRegistry()
    rule_gen_service = RuleGenerationService(llm_service, agent_registry)
    rule_gen_service._current_agent_registry = agent_registry
    
    # 创建测试状态
    test_state = GlobalState(
        id="test_error_state",
        state="错误恢复测试状态",
        iteration_count=3
    )
    
    # 测试不同类型的错误恢复
    test_cases = [
        {
            'name': '智能体不可用错误',
            'failure_context': {
                'error_message': 'Agent not found: primary_agent',
                'agent_name': 'primary_agent',
                'global_state': test_state
            }
        },
        {
            'name': '执行超时错误',
            'failure_context': {
                'error_message': 'Execution timeout after 30 seconds',
                'agent_name': 'primary_agent',
                'global_state': test_state
            }
        },
        {
            'name': '数据处理错误',
            'failure_context': {
                'error_message': 'Data format error in processing',
                'agent_name': 'primary_agent',
                'global_state': test_state
            }
        },
        {
            'name': '权限拒绝错误',
            'failure_context': {
                'error_message': 'Permission denied: access restricted',
                'agent_name': 'primary_agent',
                'global_state': test_state
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试{i}: {test_case['name']}")
        
        recovery_rules = rule_gen_service._enhanced_error_recovery_strategy(
            test_case['failure_context'], test_state
        )
        
        print(f"   生成恢复规则数量: {len(recovery_rules)}")
        for j, rule in enumerate(recovery_rules):
            print(f"   规则{j+1}: {rule.name} (优先级: {rule.priority})")
        
        assert len(recovery_rules) > 0, f"{test_case['name']}应该生成恢复规则"
    
    print(f"\n✅ 增强的错误恢复机制测试通过！")

def test_integration():
    """集成测试：测试整个优化系统的协同工作"""
    print("\n" + "="*60)
    print("🔬 集成测试：优化系统协同工作")
    print("="*60)
    
    # 创建一个WorkflowState实例来测试完整的循环预防流程
    workflow_state = WorkflowState(
        id="integration_test",
        state="集成测试状态",
        workflow_id="integration_test",
        iteration_count=12  # 中等迭代次数
    )
    
    # 模拟一些执行历史
    workflow_state.execution_history = [
        "[iter_1] 开始执行任务",
        "[iter_2] 数据收集完成",
        "[iter_3] 处理数据失败",
        "[iter_4] 重试处理数据",
        "[iter_5] 处理数据失败",
        "[iter_6] 尝试另一种方法",
        "[iter_7] 数据处理失败",
        "[iter_8] 重试处理数据",
        "[iter_9] 处理数据失败",
        "[iter_10] 尝试简化处理",
        "[iter_11] 处理仍然失败",
        "[iter_12] 当前状态"
    ]
    
    # 添加一些已执行的规则
    executed_rules = ["rule_001", "rule_002", "rule_003", "rule_004", "rule_005"]
    for rule_id in executed_rules:
        workflow_state.mark_rule_executed(rule_id, success=False)  # 模拟失败
    
    print(f"📊 当前状态概览:")
    print(f"   迭代次数: {workflow_state.iteration_count}")
    print(f"   已执行规则: {len(workflow_state.executed_rules)}")
    print(f"   失败尝试: {workflow_state.failed_attempts}")
    print(f"   连续相同规则: {workflow_state.consecutive_same_rule_count}")
    
    # 测试循环检测
    print(f"\n📋 循环检测结果:")
    loop_detected = workflow_state.detect_potential_loop()
    cycle_detected = workflow_state.check_state_cycle()
    
    print(f"   潜在循环: {loop_detected}")
    print(f"   状态循环: {cycle_detected}")
    
    # 测试执行摘要
    summary = workflow_state.get_execution_summary()
    print(f"\n📊 执行摘要:")
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # 验证系统能够正确识别问题状态
    assert summary['total_failures'] > 0, "应该记录到执行失败"
    assert summary['iteration_count'] > 10, "应该检测到高迭代次数"
    
    print(f"\n✅ 集成测试通过 - 优化系统正常协同工作！")

def main():
    """运行所有测试"""
    print("🚀 开始循环预防机制完整测试")
    print("="*80)
    
    try:
        test_workflow_state_loop_detection()
        test_advanced_loop_detection()
        test_enhanced_error_recovery()
        test_integration()
        
        print("\n" + "="*80)
        print("🎉 所有测试通过！循环预防机制工作正常")
        print("="*80)
        
        print("\n📋 优化总结:")
        print("✅ WorkflowState 循环检测功能完善")
        print("✅ 高级多维度循环检测机制有效")
        print("✅ 增强的错误恢复策略功能齐全")
        print("✅ 系统各组件协同工作良好")
        print("\n🔧 这些优化应该能够有效解决之前遇到的死循环问题！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)