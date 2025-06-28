#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自适应规则替换功能测试

测试自适应替换服务的核心功能，验证不同策略的选择和执行。
"""

import sys
import os
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "CognitiveWorkflow"))

from cognitive_workflow_rule_base.services.adaptive_replacement_service import AdaptiveReplacementService
from cognitive_workflow_rule_base.services.language_model_service import LanguageModelService
from cognitive_workflow_rule_base.domain.entities import ProductionRule, GlobalState
from cognitive_workflow_rule_base.domain.value_objects import RulePhase, ReplacementStrategyType
from pythonTask import llm_deepseek

def create_test_rules():
    """创建测试规则"""
    existing_rules = [
        ProductionRule(
            id="rule_001",
            name="分析需求",
            condition="需要分析用户需求",
            action="仔细分析用户的具体需求",
            agent_name="coder",
            priority=80,
            phase=RulePhase.INFORMATION_GATHERING,
            expected_outcome="明确需求规格"
        ),
        ProductionRule(
            id="rule_002", 
            name="编写代码",
            condition="需要编写代码实现",
            action="根据需求编写高质量代码",
            agent_name="coder",
            priority=70,
            phase=RulePhase.EXECUTION,
            expected_outcome="完成代码实现"
        ),
        ProductionRule(
            id="rule_003",
            name="测试验证",
            condition="需要测试代码功能",
            action="运行测试确保代码正确",
            agent_name="coder",
            priority=60,
            phase=RulePhase.VERIFICATION,
            expected_outcome="测试通过"
        )
    ]
    
    new_rules = [
        ProductionRule(
            id="rule_004",
            name="优化代码",
            condition="需要优化代码性能",
            action="对代码进行性能优化",
            agent_name="coder",
            priority=85,
            phase=RulePhase.EXECUTION,
            expected_outcome="代码性能提升"
        ),
        ProductionRule(
            id="rule_005",
            name="文档编写",
            condition="需要编写技术文档",
            action="编写清晰的技术文档",
            agent_name="coder",
            priority=50,
            phase=RulePhase.VERIFICATION,
            expected_outcome="文档完成"
        )
    ]
    
    return existing_rules, new_rules

def create_test_global_state():
    """创建测试全局状态"""
    return GlobalState(
        id="test_state_001",
        state="系统正在执行测试任务，当前需要优化规则集",
        context_variables={
            'current_phase': 'execution',
            'task_complexity': 'medium'
        },
        execution_history=[
            "规则执行成功: 分析需求",
            "规则执行成功: 编写代码", 
            "规则执行失败: 测试验证 - 发现错误",
            "规则执行成功: 优化代码"
        ],
        workflow_id="test_workflow",
        iteration_count=4,
        goal_achieved=False
    )

def test_situation_assessment():
    """测试情境评估功能"""
    print("🔍 测试情境评估功能...")
    
    llm_service = LanguageModelService(llm_deepseek)
    adaptive_service = AdaptiveReplacementService(llm_service)
    
    existing_rules, new_rules = create_test_rules()
    global_state = create_test_global_state()
    context = {
        'goal': '测试自适应替换功能',
        'iteration_count': 4,
        'max_iterations': 20
    }
    
    # 评估当前情境
    situation_score = adaptive_service._assess_current_situation(
        existing_rules, global_state, context
    )
    
    print(f"📊 情境评估结果:")
    print(f"   规则密度: {situation_score.rule_density:.2f}")
    print(f"   执行效率: {situation_score.execution_efficiency:.2f}")  
    print(f"   目标进度: {situation_score.goal_progress:.2f}")
    print(f"   失败频率: {situation_score.failure_frequency:.2f}")
    print(f"   智能体利用率: {situation_score.agent_utilization:.2f}")
    print(f"   阶段分布: {situation_score.phase_distribution:.2f}")
    print(f"   整体健康度: {situation_score.get_overall_health():.2f}")
    print(f"   关键问题: {situation_score.get_critical_issues()}")
    
    return situation_score

def test_strategy_selection(situation_score):
    """测试策略选择功能"""
    print("\n🎯 测试策略选择功能...")
    
    llm_service = LanguageModelService(llm_deepseek)
    adaptive_service = AdaptiveReplacementService(llm_service)
    
    context = {
        'goal': '测试自适应替换功能',
        'iteration_count': 4,
        'existing_rules': [1, 2, 3]  # 简化表示
    }
    
    # 选择策略
    strategy = adaptive_service._select_optimal_strategy(situation_score, context)
    
    print(f"📋 选择的策略:")
    print(f"   策略类型: {strategy.strategy_type.value}")
    print(f"   策略描述: {strategy.get_strategy_description()}")
    print(f"   替换比例: {strategy.replacement_ratio:.2f}")
    print(f"   相似性阈值: {strategy.similarity_threshold:.2f}")
    print(f"   性能阈值: {strategy.performance_threshold:.2f}")
    print(f"   保守模式: {strategy.conservative_mode}")
    print(f"   激进策略: {strategy.is_aggressive_strategy()}")
    
    return strategy

def test_adaptive_replacement():
    """测试完整的自适应替换流程"""
    print("\n🔄 测试完整的自适应替换流程...")
    
    llm_service = LanguageModelService(llm_deepseek)
    adaptive_service = AdaptiveReplacementService(llm_service)
    
    existing_rules, new_rules = create_test_rules()
    global_state = create_test_global_state()
    context = {
        'goal': '测试自适应替换功能',
        'iteration_count': 4,
        'context_type': 'strategy_adjustment'
    }
    
    print(f"📥 输入规则:")
    print(f"   现有规则: {len(existing_rules)} 个")
    for rule in existing_rules:
        print(f"     - {rule.name} (优先级: {rule.priority}, 阶段: {rule.phase.value})")
    print(f"   新规则: {len(new_rules)} 个") 
    for rule in new_rules:
        print(f"     - {rule.name} (优先级: {rule.priority}, 阶段: {rule.phase.value})")
    
    # 执行自适应替换
    optimized_rules = adaptive_service.execute_adaptive_replacement(
        existing_rules=existing_rules,
        new_rules=new_rules,
        global_state=global_state,
        context=context
    )
    
    print(f"\n📤 输出规则:")
    print(f"   优化后规则: {len(optimized_rules)} 个")
    for rule in optimized_rules:
        print(f"     - {rule.name} (优先级: {rule.priority}, 阶段: {rule.phase.value})")
    
    # 分析替换效果
    print(f"\n📈 替换效果分析:")
    print(f"   规则数量变化: {len(existing_rules)} + {len(new_rules)} -> {len(optimized_rules)}")
    
    # 分析阶段分布
    phase_dist = {}
    for rule in optimized_rules:
        phase = rule.phase.value
        phase_dist[phase] = phase_dist.get(phase, 0) + 1
    print(f"   阶段分布: {phase_dist}")
    
    # 分析优先级分布
    avg_priority = sum(rule.priority for rule in optimized_rules) / len(optimized_rules)
    print(f"   平均优先级: {avg_priority:.1f}")
    
    return optimized_rules

def main():
    """主测试函数"""
    print("🧪 自适应规则替换功能测试")
    print("=" * 50)
    
    try:
        # 1. 测试情境评估
        situation_score = test_situation_assessment()
        
        # 2. 测试策略选择
        strategy = test_strategy_selection(situation_score)
        
        # 3. 测试完整替换流程
        optimized_rules = test_adaptive_replacement()
        
        print("\n✅ 所有测试完成!")
        print(f"🎉 自适应替换功能正常工作")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()