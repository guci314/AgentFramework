# -*- coding: utf-8 -*-
"""
测试并行规则匹配性能

比较顺序执行vs并行执行的性能差异
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent))

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base import (
    create_production_rule_system,
    ProductionRule, RuleSet, GlobalState, RulePhase, AgentRegistry, AgentCapability
)
from cognitive_workflow_rule_base.services.language_model_service import LanguageModelService
from cognitive_workflow_rule_base.services.rule_matching_service import RuleMatchingService


def create_test_rules(count: int = 10) -> List[ProductionRule]:
    """创建测试规则"""
    
    rules = []
    
    rule_templates = [
        {
            "name_template": "分析_{}_需求",
            "condition_template": "IF 需要分析{}相关的任务需求",
            "action_template": "THEN 详细分析{}的功能需求和技术实现方案",
            "phase": RulePhase.INFORMATION_GATHERING,
            "priority": 85
        },
        {
            "name_template": "开发_{}_功能",
            "condition_template": "IF {}的需求分析已完成且可以开始编码",
            "action_template": "THEN 实现{}的核心功能代码",
            "phase": RulePhase.PROBLEM_SOLVING,
            "priority": 80
        },
        {
            "name_template": "测试_{}_模块",
            "condition_template": "IF {}的功能代码已开发完成",
            "action_template": "THEN 编写和执行{}的单元测试",
            "phase": RulePhase.VERIFICATION,
            "priority": 75
        },
        {
            "name_template": "优化_{}_性能",
            "condition_template": "IF {}的基本功能已实现且需要性能优化",
            "action_template": "THEN 分析和优化{}的性能瓶颈",
            "phase": RulePhase.PROBLEM_SOLVING,
            "priority": 70
        },
        {
            "name_template": "文档化_{}_接口",
            "condition_template": "IF {}的开发和测试已完成",
            "action_template": "THEN 编写{}的API文档和使用说明",
            "phase": RulePhase.VERIFICATION,
            "priority": 65
        }
    ]
    
    domains = [
        "用户认证", "数据存储", "网络通信", "文件处理", "缓存管理",
        "日志记录", "配置管理", "安全加密", "性能监控", "错误处理",
        "用户界面", "数据分析", "消息队列", "定时任务", "版本控制"
    ]
    
    for i in range(count):
        template = rule_templates[i % len(rule_templates)]
        domain = domains[i % len(domains)]
        
        rule = ProductionRule(
            id=f"test_rule_{i+1:03d}",
            name=template["name_template"].format(domain),
            condition=template["condition_template"].format(domain),
            action=template["action_template"].format(domain),
            agent_capability_id="test_agent",
            priority=template["priority"] + (i % 10),  # 添加一些变化
            phase=template["phase"],
            expected_outcome=f"{domain}相关任务的预期结果",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        rules.append(rule)
    
    return rules


def create_test_global_state() -> GlobalState:
    """创建测试全局状态"""
    
    return GlobalState(
        id="test_state_001",
        description="""
        系统当前状态：正在开发一个复合型Web应用系统。
        
        当前进展：
        - 用户认证模块需求分析已完成
        - 数据存储方案设计进行中
        - 网络通信协议待确定
        - 需要开始编写核心功能代码
        - 文件处理功能需要优化
        - 缓存管理策略需要实现
        
        技术栈：Python Flask, SQLAlchemy, Redis, Nginx
        开发阶段：功能开发和测试
        优先级：高性能、高可用性
        """,
        context_variables={
            "current_phase": "problem_solving",
            "project_type": "web_application", 
            "technology_stack": ["python", "flask", "redis", "nginx"],
            "development_stage": "implementation",
            "priority_focus": "performance"
        },
        workflow_id="test_workflow_001",
        iteration_count=5,
        goal_achieved=False,
        execution_history=[
            "用户认证需求分析完成",
            "数据库设计方案初稿完成",
            "开始核心API开发",
            "遇到性能瓶颈需要优化",
            "开始并行开发多个模块"
        ],
        timestamp=datetime.now()
    )


def test_sequential_vs_parallel_performance():
    """测试顺序执行vs并行执行的性能"""
    
    print("🧪 规则匹配并行执行性能测试")
    print("="*50)
    
    # 创建测试数据
    rule_counts = [5, 10, 20, 30]  # 不同规则数量
    max_workers_options = [1, 2, 4, 8]  # 不同线程数
    
    # 创建LLM服务
    llm_service = LanguageModelService(llm_deepseek)
    
    print("📊 性能测试结果:")
    print("-" * 80)
    print(f"{'规则数量':<8} {'线程数':<6} {'耗时(秒)':<10} {'相对性能':<10} {'状态':<10}")
    print("-" * 80)
    
    results = []
    
    for rule_count in rule_counts:
        print(f"\n🔍 测试 {rule_count} 个规则:")
        
        # 创建测试数据
        test_rules = create_test_rules(rule_count)
        rule_set = RuleSet(
            id=f"test_set_{rule_count}",
            goal=f"测试{rule_count}个规则的匹配性能",
            rules=test_rules
        )
        global_state = create_test_global_state()
        
        baseline_time = None
        
        for max_workers in max_workers_options:
            try:
                # 创建规则匹配服务
                rule_matching = RuleMatchingService(llm_service, max_workers)
                
                # 执行性能测试
                start_time = time.time()
                
                applicable_rules = rule_matching.find_applicable_rules(global_state, rule_set)
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                # 计算相对性能
                if baseline_time is None:
                    baseline_time = execution_time
                    relative_performance = "100%"
                else:
                    improvement = ((baseline_time - execution_time) / baseline_time) * 100
                    relative_performance = f"{improvement:+.1f}%"
                
                status = "✅ 成功" if len(applicable_rules) > 0 else "⚠️ 无匹配"
                
                print(f"{rule_count:<8} {max_workers:<6} {execution_time:<10.3f} {relative_performance:<10} {status:<10}")
                
                results.append({
                    'rule_count': rule_count,
                    'max_workers': max_workers,
                    'execution_time': execution_time,
                    'relative_performance': relative_performance,
                    'applicable_rules_count': len(applicable_rules)
                })
                
                # 短暂休息避免API频率限制
                time.sleep(0.5)
                
            except Exception as e:
                print(f"{rule_count:<8} {max_workers:<6} {'ERROR':<10} {'N/A':<10} ❌ 失败")
                print(f"   错误: {str(e)[:60]}...")
    
    # 分析结果
    print("\n📈 性能分析:")
    print("-" * 40)
    
    # 找出最佳配置
    best_configs = {}
    for rule_count in rule_counts:
        rule_results = [r for r in results if r['rule_count'] == rule_count]
        if rule_results:
            best_config = min(rule_results, key=lambda x: x['execution_time'])
            best_configs[rule_count] = best_config
            
            print(f"规则数量 {rule_count}: 最佳配置 {best_config['max_workers']} 线程")
            print(f"   耗时: {best_config['execution_time']:.3f}秒")
            print(f"   匹配规则: {best_config['applicable_rules_count']}个")
    
    return results


def test_parallel_correctness():
    """测试并行执行的正确性"""
    
    print("\n🔍 并行执行正确性验证")
    print("="*35)
    
    # 创建测试数据
    test_rules = create_test_rules(15)
    rule_set = RuleSet(
        id="correctness_test",
        goal="验证并行执行的正确性",
        rules=test_rules
    )
    global_state = create_test_global_state()
    
    # 创建LLM服务
    llm_service = LanguageModelService(llm_deepseek)
    
    # 测试不同线程数的结果一致性
    results_by_workers = {}
    
    for max_workers in [1, 2, 4]:
        try:
            print(f"测试 {max_workers} 线程配置...")
            
            rule_matching = RuleMatchingService(llm_service, max_workers)
            applicable_rules = rule_matching.find_applicable_rules(global_state, rule_set)
            
            # 记录结果（规则ID列表，排序后）
            rule_ids = sorted([rule.id for rule in applicable_rules])
            results_by_workers[max_workers] = rule_ids
            
            print(f"   找到 {len(applicable_rules)} 个适用规则")
            
            time.sleep(0.5)  # 避免API频率限制
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            results_by_workers[max_workers] = None
    
    # 验证结果一致性
    print("\n📋 结果一致性检查:")
    
    valid_results = {k: v for k, v in results_by_workers.items() if v is not None}
    
    if len(valid_results) < 2:
        print("⚠️  有效结果不足，无法进行一致性比较")
        return False
    
    # 比较所有结果
    reference_result = list(valid_results.values())[0]
    
    all_consistent = True
    for workers, result in valid_results.items():
        if result == reference_result:
            print(f"   ✅ {workers} 线程: 结果一致 ({len(result)} 个规则)")
        else:
            print(f"   ❌ {workers} 线程: 结果不一致")
            print(f"      期望: {len(reference_result)} 个规则")
            print(f"      实际: {len(result)} 个规则")
            all_consistent = False
    
    if all_consistent:
        print("\n🎉 所有并行配置的结果完全一致！")
    else:
        print("\n⚠️  并行执行结果存在不一致，需要检查线程安全问题")
    
    return all_consistent


def main():
    """主函数"""
    
    print("🚀 RuleMatchingService 并行执行优化测试")
    print("验证并行规则匹配的性能改进和正确性")
    print("="*70)
    
    try:
        # 性能测试
        performance_results = test_sequential_vs_parallel_performance()
        
        # 正确性测试  
        correctness_passed = test_parallel_correctness()
        
        # 总结
        print("\n📊 测试总结:")
        print("="*30)
        
        if performance_results:
            print("✅ 性能测试: 完成")
            
            # 计算平均性能改进
            improvements = []
            for result in performance_results:
                if result['max_workers'] > 1 and result['relative_performance'] != "100%":
                    try:
                        improvement = float(result['relative_performance'].replace('%', '').replace('+', ''))
                        improvements.append(improvement)
                    except:
                        pass
            
            if improvements:
                avg_improvement = sum(improvements) / len(improvements)
                print(f"   平均性能改进: {avg_improvement:.1f}%")
            
        print(f"✅ 正确性测试: {'通过' if correctness_passed else '失败'}")
        
        print(f"\n🎯 并行优化要点:")
        print("   ✓ ThreadPoolExecutor进行并行评估")
        print("   ✓ 线程安全的LLM服务调用")
        print("   ✓ 智能回退到顺序执行")
        print("   ✓ 超时保护和异常处理")
        print("   ✓ 可配置的并行线程数")
        
        if correctness_passed and performance_results:
            print("\n🎉 并行规则匹配优化成功！")
        else:
            print("\n⚠️  需要进一步调试和优化")
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试执行异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()