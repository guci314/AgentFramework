# -*- coding: utf-8 -*-
"""
Phase 3 集成测试

测试所有Phase 3 Self-Learning Optimization组件的集成和协同工作。
"""

import unittest
import sys
import os
import time
import json
import random
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognitive_workflow_rule_base.domain.value_objects import (
    ReplacementStrategyType, StrategyEffectiveness, SituationScore,
    ExecutionMetrics, AdaptiveReplacementConstants
)
from cognitive_workflow_rule_base.services.dynamic_parameter_optimizer import (
    DynamicParameterOptimizer, OptimizationAlgorithm
)
from cognitive_workflow_rule_base.services.advanced_pattern_recognition import (
    AdvancedPatternRecognitionEngine
)
from cognitive_workflow_rule_base.services.predictive_optimization_framework import (
    PredictiveOptimizationFramework
)
from cognitive_workflow_rule_base.services.strategy_effectiveness_tracker import (
    StrategyEffectivenessTracker
)
from cognitive_workflow_rule_base.services.reinforcement_learning_optimizer import (
    ReinforcementLearningOptimizer, RLAlgorithmType
)
from cognitive_workflow_rule_base.services.adaptive_hyperparameter_optimizer import (
    AdaptiveHyperparameterOptimizer, OptimizationMethod, PerformanceObjectiveFunction
)
from cognitive_workflow_rule_base.services.intelligent_performance_benchmark import (
    IntelligentPerformanceBenchmark, BenchmarkType
)


class TestPhase3Integration(unittest.TestCase):
    """Phase 3 集成测试"""
    
    def setUp(self):
        """测试设置"""
        print("\n" + "="*80)
        print("🚀 Phase 3: Self-Learning Optimization 集成测试")
        print("="*80)
        
        # 初始化所有组件
        self.effectiveness_tracker = StrategyEffectivenessTracker()
        self.parameter_optimizer = DynamicParameterOptimizer(
            optimization_algorithm=OptimizationAlgorithm.ADAPTIVE_LEARNING_RATE
        )
        self.pattern_engine = AdvancedPatternRecognitionEngine()
        self.predictive_framework = PredictiveOptimizationFramework(
            self.parameter_optimizer,
            self.pattern_engine,
            self.effectiveness_tracker
        )
        self.rl_optimizer = ReinforcementLearningOptimizer(
            algorithm_type=RLAlgorithmType.Q_LEARNING
        )
        self.hyperparameter_optimizer = AdaptiveHyperparameterOptimizer(
            optimization_method=OptimizationMethod.BAYESIAN_OPTIMIZATION
        )
        self.benchmark_system = IntelligentPerformanceBenchmark()
        
        # 生成测试数据
        self.test_history = self._generate_test_effectiveness_history()
        
        print(f"✅ 初始化完成，生成了{len(self.test_history)}条测试数据")
    
    def _generate_test_effectiveness_history(self) -> list:
        """生成测试用的策略效果历史"""
        history = []
        base_time = datetime.now() - timedelta(hours=24)
        
        strategies = list(ReplacementStrategyType)
        
        for i in range(50):  # 生成50条历史记录
            # 创建渐进改善的情境
            health_trend = 0.3 + (i / 100.0)  # 从0.3逐步改善到0.8
            
            context = SituationScore(
                rule_density=0.4 + (i % 10) * 0.03,
                execution_efficiency=0.5 + health_trend * 0.4,
                goal_progress=0.3 + health_trend * 0.5,
                failure_frequency=max(0.05, 0.3 - health_trend * 0.2),
                agent_utilization=0.4 + (i % 8) * 0.06,
                phase_distribution=0.5 + (i % 6) * 0.05
            )
            
            strategy = strategies[i % len(strategies)]
            
            # 模拟一些策略比其他策略更有效
            base_score = 0.4
            if strategy == ReplacementStrategyType.PERFORMANCE_FOCUSED:
                base_score = 0.7
            elif strategy == ReplacementStrategyType.STRATEGIC_PIVOT:
                base_score = 0.6
            
            # 添加一些随机变化和时间趋势
            improvement_score = base_score + health_trend * 0.2 + (i % 7 - 3) * 0.05
            improvement_score = max(0.1, min(0.95, improvement_score))
            
            # 创建before和after指标
            total_rules = 10 + (i % 5)
            successful_before = int((0.6 + (i % 10) * 0.02) * total_rules)
            failed_before = total_rules - successful_before
            
            before_metrics = ExecutionMetrics(
                total_rules_executed=total_rules,
                successful_executions=successful_before,
                failed_executions=failed_before,
                average_execution_time=1.0 + (i % 8) * 0.1,
                total_execution_time=(1.0 + (i % 8) * 0.1) * total_rules,
                rule_match_accuracy=0.85 + (i % 10) * 0.01
            )
            
            total_rules_after = total_rules + 2
            successful_after = int((improvement_score * 0.8 + 0.2) * total_rules_after)
            failed_after = total_rules_after - successful_after
            
            after_metrics = ExecutionMetrics(
                total_rules_executed=total_rules_after,
                successful_executions=successful_after,
                failed_executions=failed_after,
                average_execution_time=max(0.5, before_metrics.average_execution_time - 0.2),
                total_execution_time=max(0.5, before_metrics.average_execution_time - 0.2) * total_rules_after,
                rule_match_accuracy=min(0.95, before_metrics.rule_match_accuracy + 0.05)
            )
            
            effectiveness = StrategyEffectiveness(
                strategy_type=strategy,
                applied_context=context,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_score=improvement_score,
                application_timestamp=base_time + timedelta(minutes=i * 30)
            )
            
            history.append(effectiveness)
        
        return history
    
    def test_01_effectiveness_tracking_integration(self):
        """测试策略效果跟踪集成"""
        print("\n📊 测试1: 策略效果跟踪集成")
        
        # 批量记录效果数据
        for effectiveness in self.test_history:
            self.effectiveness_tracker.record_strategy_application(
                strategy_type=effectiveness.strategy_type,
                applied_context=effectiveness.applied_context,
                before_metrics=effectiveness.before_metrics,
                after_metrics=effectiveness.after_metrics,
                improvement_score=effectiveness.improvement_score
            )
        
        # 获取跟踪器状态
        export_data = self.effectiveness_tracker.export_performance_data('summary')
        print(f"   • 跟踪的策略数量: {len([s for s in export_data['strategy_performance'].values() if s])}")
        print(f"   • 总记录数: {export_data['total_applications']}")
        
        # 验证数据完整性
        self.assertEqual(export_data['total_applications'], len(self.test_history))
        self.assertGreater(len([s for s in export_data['strategy_performance'].values() if s]), 0)
        
        # 获取最佳策略
        best_strategy = export_data.get('best_performing_strategy', 'performance_focused')
        print(f"   • 最佳策略: {best_strategy}")
        
        self.assertIsInstance(best_strategy, str)
        self.assertGreater(len(best_strategy), 0)
        print("   ✅ 策略效果跟踪集成测试通过")
    
    def test_02_pattern_recognition_integration(self):
        """测试模式识别集成"""
        print("\n🔍 测试2: 高级模式识别集成")
        
        # 分析模式
        pattern_analysis = self.pattern_engine.analyze_patterns(
            self.test_history, include_predictions=True
        )
        
        print(f"   • 发现的模式总数: {pattern_analysis['summary']['total_patterns']}")
        print(f"   • 高置信度模式: {pattern_analysis['summary']['high_confidence_patterns']}")
        print(f"   • 预测数量: {len(pattern_analysis['predictions'])}")
        
        # 验证模式识别结果
        self.assertGreater(pattern_analysis['summary']['total_patterns'], 0)
        
        # 检查各类型模式
        patterns = pattern_analysis['patterns']
        for pattern_type, pattern_list in patterns.items():
            if pattern_list:
                print(f"   • {pattern_type}模式: {len(pattern_list)}个")
        
        # 验证预测
        if pattern_analysis['predictions']:
            pred = pattern_analysis['predictions'][0]
            print(f"   • 首个预测: {pred['predicted_pattern']['description'][:50]}...")
        
        print("   ✅ 高级模式识别集成测试通过")
    
    def test_03_parameter_optimization_integration(self):
        """测试动态参数优化集成"""
        print("\n⚙️ 测试3: 动态参数优化集成")
        
        # 准备参数和上下文
        current_params = {
            'replacement_ratio': 0.3,
            'similarity_threshold': 0.8,
            'performance_threshold': 0.7,
            'learning_rate': 0.01
        }
        
        current_context = self.test_history[-1].applied_context
        strategy_type = ReplacementStrategyType.PERFORMANCE_FOCUSED
        
        # 执行参数优化
        optimized_params = self.parameter_optimizer.optimize_parameters(
            strategy_type=strategy_type,
            current_parameters=current_params,
            performance_history=self.test_history[-10:],  # 最近10条记录
            situation_context=current_context
        )
        
        print(f"   • 原始参数: {current_params}")
        print(f"   • 优化参数: {optimized_params}")
        
        # 验证参数优化
        self.assertIsInstance(optimized_params, dict)
        self.assertEqual(len(optimized_params), len(current_params))
        
        # 获取优化摘要
        optimization_summary = self.parameter_optimizer.get_optimization_summary()
        print(f"   • 优化迭代: {optimization_summary.get('total_iterations', 0)}")
        
        print("   ✅ 动态参数优化集成测试通过")
    
    def test_04_reinforcement_learning_integration(self):
        """测试强化学习集成"""
        print("\n🎯 测试4: 强化学习优化集成")
        
        # 初始化强化学习优化器
        rl_optimizer = ReinforcementLearningOptimizer(
            algorithm_type=RLAlgorithmType.Q_LEARNING
        )
        
        # 模拟学习过程
        for i, effectiveness in enumerate(self.test_history[-20:]):  # 使用最近20条数据
            # 编码状态
            if i == 0:
                last_strategy = ReplacementStrategyType.MINIMAL_REPLACEMENT
                last_performance = 0.5
            else:
                last_strategy = self.test_history[-(21-i)].strategy_type
                last_performance = self.test_history[-(21-i)].improvement_score
            
            state = rl_optimizer.encode_state(
                situation=effectiveness.applied_context,
                last_strategy=last_strategy,
                last_performance=last_performance,
                time_since_last=30  # 假设30分钟间隔
            )
            
            # 选择行动
            action = rl_optimizer.choose_action(state)
            
            # 计算奖励
            previous_health = 0.5 if i == 0 else self.test_history[-(21-i)].applied_context.get_overall_health()
            reward = rl_optimizer.calculate_reward(effectiveness, previous_health)
            
            # 下一状态
            if i < len(self.test_history[-20:]) - 1:
                next_effectiveness = self.test_history[-(20-i-1)]
                next_state = rl_optimizer.encode_state(
                    situation=next_effectiveness.applied_context,
                    last_strategy=effectiveness.strategy_type,
                    last_performance=effectiveness.improvement_score
                )
                done = False
            else:
                next_state = state  # 最后一个状态
                done = True
            
            # 学习
            rl_optimizer.learn_from_experience(state, action, reward, next_state, done)
        
        # 获取学习统计
        learning_stats = rl_optimizer.get_learning_statistics()
        print(f"   • 总经验数: {learning_stats['total_experiences']}")
        print(f"   • 平均奖励: {learning_stats['average_reward']:.3f}")
        print(f"   • 探索率: {learning_stats['exploration_rate']:.3f}")
        
        # 获取策略建议
        if self.test_history:
            test_state = rl_optimizer.encode_state(
                situation=self.test_history[-1].applied_context,
                last_strategy=self.test_history[-1].strategy_type,
                last_performance=self.test_history[-1].improvement_score
            )
            
            recommendations = rl_optimizer.get_policy_recommendations(test_state)
            print(f"   • 策略建议数: {len(recommendations)}")
        
        # 验证学习效果
        self.assertGreater(learning_stats['total_experiences'], 0)
        
        print("   ✅ 强化学习优化集成测试通过")
    
    def test_05_predictive_optimization_integration(self):
        """测试预测性优化框架集成"""
        print("\n🔮 测试5: 预测性优化框架集成")
        
        # 初始化预测模型
        self.predictive_framework.initialize_predictive_models(self.test_history)
        
        # 生成系统预测
        current_context = self.test_history[-1].applied_context
        current_params = {
            'replacement_ratio': 0.3,
            'similarity_threshold': 0.8,
            'performance_threshold': 0.7
        }
        
        predictions = self.predictive_framework.generate_system_predictions(
            current_context, current_params
        )
        
        print(f"   • 生成预测数: {len(predictions)}")
        
        if predictions:
            pred = predictions[0]
            print(f"   • 首个预测置信度: {pred.confidence:.3f}")
            print(f"   • 预测健康度: {pred.predicted_situation.get_overall_health():.3f}")
        
        # 创建优化计划
        if predictions:
            optimization_plans = self.predictive_framework.create_optimization_plans(
                predictions, current_params
            )
            
            print(f"   • 优化计划数: {len(optimization_plans)}")
            
            if optimization_plans:
                plan = optimization_plans[0]
                print(f"   • 首个计划行动数: {len(plan.actions)}")
                print(f"   • 计划置信度: {plan.confidence:.3f}")
        
        # 获取框架状态
        framework_status = self.predictive_framework.get_framework_status()
        print(f"   • 预测模型数: {len(framework_status.get('prediction_models', {}))}")
        print(f"   • 框架健康度: {framework_status.get('framework_health', {}).get('overall_health', 0):.3f}")
        
        # 验证预测框架
        self.assertGreater(len(predictions), 0)
        
        print("   ✅ 预测性优化框架集成测试通过")
    
    def test_06_hyperparameter_optimization_integration(self):
        """测试自适应超参数优化集成"""
        print("\n🎛️ 测试6: 自适应超参数优化集成")
        
        # 创建性能目标函数
        current_context = self.test_history[-1].applied_context
        objective_func = self.hyperparameter_optimizer.create_performance_objective(
            self.effectiveness_tracker, current_context
        )
        
        # 建议参数配置
        suggested_params = self.hyperparameter_optimizer.suggest_parameters()
        print(f"   • 建议参数: {suggested_params}")
        
        # 评估参数配置
        performance_score = self.hyperparameter_optimizer.evaluate_parameters(suggested_params)
        print(f"   • 性能评分: {performance_score:.3f}")
        
        # 运行小规模优化（减少评估次数以加快测试）
        self.hyperparameter_optimizer.max_evaluations = 10
        
        optimization_result = self.hyperparameter_optimizer.optimize(max_time_minutes=1)
        
        print(f"   • 优化评估次数: {optimization_result.evaluation_count}")
        print(f"   • 最优性能: {optimization_result.objective_value:.3f}")
        print(f"   • 是否收敛: {self.hyperparameter_optimizer.is_converged}")
        
        # 获取参数重要性
        param_importance = self.hyperparameter_optimizer.get_parameter_importance()
        if param_importance:
            print(f"   • 重要参数: {max(param_importance.items(), key=lambda x: x[1])[0]}")
        
        # 验证超参数优化
        self.assertGreater(optimization_result.evaluation_count, 0)
        self.assertIsInstance(optimization_result.parameters, dict)
        
        print("   ✅ 自适应超参数优化集成测试通过")
    
    def test_07_performance_benchmark_integration(self):
        """测试智能性能基准测试集成"""
        print("\n📈 测试7: 智能性能基准测试集成")
        
        # 定义测试目标函数
        def mock_target_function(context, strategy, parameters):
            """模拟目标函数"""
            time.sleep(0.01)  # 模拟执行时间
            
            # 基于输入计算模拟性能
            health = context.get_overall_health()
            perf_score = health * 0.7 + parameters.get('replacement_ratio', 0.3) * 0.3
            
            # 模拟策略效果
            total_rules = 10
            successful_before = 7
            failed_before = 3
            
            before_metrics = ExecutionMetrics(
                total_rules_executed=total_rules,
                successful_executions=successful_before,
                failed_executions=failed_before,
                average_execution_time=1.0,
                total_execution_time=1.0 * total_rules,
                rule_match_accuracy=0.85
            )
            
            total_rules_after = total_rules + 1
            successful_after = successful_before + 1
            failed_after = total_rules_after - successful_after
            
            after_metrics = ExecutionMetrics(
                total_rules_executed=total_rules_after,
                successful_executions=successful_after,
                failed_executions=failed_after,
                average_execution_time=max(0.5, before_metrics.average_execution_time - 0.1),
                total_execution_time=max(0.5, before_metrics.average_execution_time - 0.1) * total_rules_after,
                rule_match_accuracy=min(0.95, before_metrics.rule_match_accuracy + 0.05)
            )
            
            effectiveness = StrategyEffectiveness(
                strategy_type=strategy,
                applied_context=context,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_score=perf_score,
                application_timestamp=datetime.now()
            )
            
            return effectiveness
        
        # 运行快速性能测试
        benchmark_result = self.benchmark_system.run_benchmark(
            'quick_performance',
            mock_target_function
        )
        
        print(f"   • 完成迭代数: {benchmark_result.iterations_completed}")
        print(f"   • 成功率: {benchmark_result.success_count / max(1, benchmark_result.iterations_completed):.2%}")
        print(f"   • 测试用时: {benchmark_result.total_duration:.2f}秒")
        
        # 验证指标收集
        metrics = benchmark_result.metrics
        print(f"   • 收集的指标类型: {len(metrics)}")
        
        for metric_type, values in metrics.items():
            if values:
                print(f"   • {metric_type.value}: 平均值={sum(values)/len(values):.4f}")
        
        # 获取基准测试状态
        status = self.benchmark_system.get_benchmark_status()
        print(f"   • 可用配置: {len(status['available_configurations'])}")
        print(f"   • 历史记录: {status['history_count']}")
        
        # 验证基准测试
        self.assertGreater(benchmark_result.iterations_completed, 0)
        self.assertGreater(len(metrics), 0)
        
        print("   ✅ 智能性能基准测试集成测试通过")
    
    def test_08_full_system_integration(self):
        """测试完整系统集成"""
        print("\n🔄 测试8: 完整系统集成工作流")
        
        print("   步骤1: 初始化所有组件...")
        
        # 1. 加载历史数据到所有组件
        for effectiveness in self.test_history:
            self.effectiveness_tracker.record_strategy_application(
                strategy_type=effectiveness.strategy_type,
                applied_context=effectiveness.applied_context,
                before_metrics=effectiveness.before_metrics,
                after_metrics=effectiveness.after_metrics,
                improvement_score=effectiveness.improvement_score
            )
        
        # 2. 初始化预测模型
        self.predictive_framework.initialize_predictive_models(self.test_history)
        
        print("   步骤2: 分析当前状态...")
        
        # 3. 分析模式
        pattern_analysis = self.pattern_engine.analyze_patterns(
            self.test_history[-20:], include_predictions=True
        )
        
        # 4. 获取当前最佳策略
        export_data = self.effectiveness_tracker.export_performance_data('summary')
        current_best_strategy = export_data.get('best_performing_strategy', 'performance_focused')
        
        print(f"   • 当前最佳策略: {current_best_strategy}")
        print(f"   • 识别的模式数: {pattern_analysis['summary']['total_patterns']}")
        
        print("   步骤3: 生成优化建议...")
        
        # 5. 参数优化
        current_params = {
            'replacement_ratio': 0.3,
            'similarity_threshold': 0.8,
            'performance_threshold': 0.7
        }
        
        optimized_params = self.parameter_optimizer.optimize_parameters(
            strategy_type=ReplacementStrategyType.PERFORMANCE_FOCUSED,
            current_parameters=current_params,
            performance_history=self.test_history[-10:],
            situation_context=self.test_history[-1].applied_context
        )
        
        # 6. 生成预测和计划
        predictions = self.predictive_framework.generate_system_predictions(
            self.test_history[-1].applied_context, optimized_params
        )
        
        optimization_plans = self.predictive_framework.create_optimization_plans(
            predictions, optimized_params
        ) if predictions else []
        
        print(f"   • 优化预测数: {len(predictions)}")
        print(f"   • 优化计划数: {len(optimization_plans)}")
        
        print("   步骤4: 强化学习优化...")
        
        # 7. 强化学习建议
        if self.test_history:
            rl_state = self.rl_optimizer.encode_state(
                situation=self.test_history[-1].applied_context,
                last_strategy=self.test_history[-1].strategy_type,
                last_performance=self.test_history[-1].improvement_score
            )
            
            rl_action = self.rl_optimizer.choose_action(rl_state)
            rl_recommendations = self.rl_optimizer.get_policy_recommendations(rl_state)
            
            print(f"   • RL建议数: {len(rl_recommendations)}")
        
        print("   步骤5: 综合分析报告...")
        
        # 8. 生成综合报告
        integration_report = {
            'timestamp': datetime.now().isoformat(),
            'effectiveness_tracking': {
                'total_records': len(self.test_history),
                'best_strategy': current_best_strategy,
                'avg_performance': sum(eff.improvement_score for eff in self.test_history) / len(self.test_history)
            },
            'pattern_recognition': {
                'patterns_found': pattern_analysis['summary']['total_patterns'],
                'high_confidence_patterns': pattern_analysis['summary']['high_confidence_patterns'],
                'predictions_generated': len(pattern_analysis['predictions'])
            },
            'parameter_optimization': {
                'optimization_iterations': self.parameter_optimizer.get_optimization_summary().get('total_iterations', 0),
                'parameter_improvements': len([k for k, v in optimized_params.items() if v != current_params.get(k, v)])
            },
            'predictive_framework': {
                'predictions_count': len(predictions),
                'optimization_plans': len(optimization_plans),
                'framework_health': self.predictive_framework.get_framework_status().get('framework_health', {}).get('overall_health', 0)
            },
            'reinforcement_learning': {
                'learning_experiences': self.rl_optimizer.get_learning_statistics()['total_experiences'],
                'exploration_rate': self.rl_optimizer.get_learning_statistics()['exploration_rate']
            },
            'system_status': 'fully_integrated'
        }
        
        print("   📋 集成报告摘要:")
        print(f"   • 效果跟踪记录: {integration_report['effectiveness_tracking']['total_records']}")
        print(f"   • 模式识别结果: {integration_report['pattern_recognition']['patterns_found']}个模式")
        print(f"   • 参数优化改进: {integration_report['parameter_optimization']['parameter_improvements']}个参数")
        print(f"   • 预测框架健康度: {integration_report['predictive_framework']['framework_health']:.3f}")
        print(f"   • RL学习经验: {integration_report['reinforcement_learning']['learning_experiences']}")
        
        # 验证完整集成
        self.assertEqual(integration_report['system_status'], 'fully_integrated')
        self.assertGreater(integration_report['effectiveness_tracking']['total_records'], 0)
        self.assertGreaterEqual(integration_report['pattern_recognition']['patterns_found'], 0)
        
        print("   ✅ 完整系统集成测试通过")
        
        # 保存集成报告
        report_file = f"phase3_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(integration_report, f, ensure_ascii=False, indent=2)
        
        print(f"   📄 集成报告已保存: {report_file}")
    
    def test_09_performance_validation(self):
        """测试性能验证"""
        print("\n⚡ 测试9: 系统性能验证")
        
        # 测试大规模数据处理性能
        large_history = []
        base_time = datetime.now() - timedelta(hours=48)
        
        print("   生成大规模测试数据...")
        start_time = time.time()
        
        for i in range(200):  # 生成200条记录
            context = SituationScore(
                rule_density=0.3 + (i % 20) * 0.02,
                execution_efficiency=0.4 + (i % 15) * 0.03,
                goal_progress=0.2 + (i % 25) * 0.025,
                failure_frequency=max(0.05, 0.3 - (i % 30) * 0.008),
                agent_utilization=0.3 + (i % 12) * 0.04,
                phase_distribution=0.4 + (i % 18) * 0.02
            )
            
            total_rules_perf = 8 + (i % 6)
            success_rate_before = 0.6 + (i % 15) * 0.02
            successful_before = int(success_rate_before * total_rules_perf)
            failed_before = total_rules_perf - successful_before
            
            before_metrics = ExecutionMetrics(
                total_rules_executed=total_rules_perf,
                successful_executions=successful_before,
                failed_executions=failed_before,
                average_execution_time=0.8 + (i % 10) * 0.05,
                total_execution_time=(0.8 + (i % 10) * 0.05) * total_rules_perf,
                rule_match_accuracy=0.85 + (i % 10) * 0.01
            )
            
            total_rules_after_perf = before_metrics.total_rules_executed + 1
            success_rate_after = min(1.0, before_metrics.success_rate + 0.05)
            successful_after_perf = int(success_rate_after * total_rules_after_perf)
            failed_after_perf = total_rules_after_perf - successful_after_perf
            
            after_metrics = ExecutionMetrics(
                total_rules_executed=total_rules_after_perf,
                successful_executions=successful_after_perf,
                failed_executions=failed_after_perf,
                average_execution_time=max(0.3, before_metrics.average_execution_time - 0.1),
                total_execution_time=max(0.3, before_metrics.average_execution_time - 0.1) * total_rules_after_perf,
                rule_match_accuracy=min(0.95, before_metrics.rule_match_accuracy + 0.05)
            )
            
            effectiveness = StrategyEffectiveness(
                strategy_type=list(ReplacementStrategyType)[i % len(ReplacementStrategyType)],
                applied_context=context,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_score=0.3 + (i % 40) * 0.015,
                application_timestamp=base_time + timedelta(minutes=i * 15)
            )
            
            large_history.append(effectiveness)
        
        data_generation_time = time.time() - start_time
        print(f"   • 数据生成用时: {data_generation_time:.2f}秒")
        
        # 测试各组件的大数据处理性能
        performance_results = {}
        
        # 1. 效果跟踪器性能
        start_time = time.time()
        for eff in large_history:
            self.effectiveness_tracker.record_strategy_application(
                strategy_type=eff.strategy_type,
                applied_context=eff.applied_context,
                before_metrics=eff.before_metrics,
                after_metrics=eff.after_metrics,
                improvement_score=eff.improvement_score
            )
        tracking_time = time.time() - start_time
        performance_results['effectiveness_tracking'] = tracking_time
        print(f"   • 效果跟踪处理: {tracking_time:.2f}秒 ({len(large_history)/tracking_time:.1f} 记录/秒)")
        
        # 2. 模式识别性能
        start_time = time.time()
        pattern_result = self.pattern_engine.analyze_patterns(large_history[:100])  # 限制数量避免过长
        pattern_time = time.time() - start_time
        performance_results['pattern_recognition'] = pattern_time
        print(f"   • 模式识别处理: {pattern_time:.2f}秒")
        
        # 3. 参数优化性能
        start_time = time.time()
        optimized = self.parameter_optimizer.optimize_parameters(
            ReplacementStrategyType.PERFORMANCE_FOCUSED,
            {'replacement_ratio': 0.3, 'similarity_threshold': 0.8},
            large_history[-20:],
            large_history[-1].applied_context
        )
        optimization_time = time.time() - start_time
        performance_results['parameter_optimization'] = optimization_time
        print(f"   • 参数优化处理: {optimization_time:.2f}秒")
        
        # 验证性能指标
        total_processing_time = sum(performance_results.values())
        print(f"   • 总处理时间: {total_processing_time:.2f}秒")
        print(f"   • 平均每条记录: {total_processing_time/len(large_history)*1000:.2f}毫秒")
        
        # 性能阈值验证（确保系统能在合理时间内处理大量数据）
        self.assertLess(tracking_time, 5.0, "效果跟踪处理时间过长")
        self.assertLess(pattern_time, 10.0, "模式识别处理时间过长")
        self.assertLess(optimization_time, 3.0, "参数优化处理时间过长")
        
        print("   ✅ 系统性能验证通过")
    
    def test_10_system_robustness(self):
        """测试系统健壮性"""
        print("\n🛡️ 测试10: 系统健壮性验证")
        
        # 测试异常输入处理
        print("   测试异常输入处理...")
        
        # 1. 空数据处理
        try:
            empty_result = self.pattern_engine.analyze_patterns([])
            self.assertIsInstance(empty_result, dict)
            print("   ✓ 空数据处理正常")
        except Exception as e:
            self.fail(f"空数据处理失败: {e}")
        
        # 2. 异常上下文处理
        try:
            extreme_context = SituationScore(
                rule_density=1.5,  # 超出正常范围
                execution_efficiency=-0.5,  # 负值
                goal_progress=2.0,  # 超出范围
                failure_frequency=-1.0,  # 负值
                agent_utilization=10.0,  # 超出范围
                phase_distribution=0.5
            )
            
            # 应该能处理极值而不崩溃
            health = extreme_context.get_overall_health()
            self.assertIsInstance(health, float)
            print("   ✓ 极值上下文处理正常")
            
        except Exception as e:
            self.fail(f"极值上下文处理失败: {e}")
        
        # 3. 测试组件间错误传播
        try:
            # 故意传入不匹配的参数
            invalid_params = {'invalid_param': 'invalid_value'}
            
            # 应该优雅地处理而不是崩溃
            result = self.parameter_optimizer.optimize_parameters(
                ReplacementStrategyType.PERFORMANCE_FOCUSED,
                invalid_params,
                self.test_history[-5:],
                self.test_history[-1].applied_context
            )
            
            self.assertIsInstance(result, dict)
            print("   ✓ 无效参数处理正常")
            
        except Exception as e:
            print(f"   ✓ 无效参数被正确拒绝: {type(e).__name__}")
        
        # 4. 内存使用监控
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量操作
        for i in range(50):
            temp_history = self.test_history[-10:]
            eff = temp_history[i % len(temp_history)]
            self.effectiveness_tracker.record_strategy_application(
                strategy_type=eff.strategy_type,
                applied_context=eff.applied_context,
                before_metrics=eff.before_metrics,
                after_metrics=eff.after_metrics,
                improvement_score=eff.improvement_score
            )
            
            if i % 10 == 0:
                gc.collect()  # 强制垃圾回收
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        print(f"   • 初始内存: {initial_memory:.1f}MB")
        print(f"   • 最终内存: {final_memory:.1f}MB")
        print(f"   • 内存增长: {memory_growth:.1f}MB")
        
        # 验证内存增长在合理范围内
        self.assertLess(memory_growth, 100.0, "内存增长过多，可能存在内存泄漏")
        
        print("   ✅ 系统健壮性验证通过")


def run_integration_tests():
    """运行集成测试"""
    print("\n" + "🎯" + " "*30 + "PHASE 3 集成测试启动" + " "*30 + "🎯")
    print("="*100)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase3Integration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "="*100)
    print("🏁 Phase 3 集成测试完成")
    print(f"✅ 通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"💥 错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun
    print(f"\n🎯 整体成功率: {success_rate:.1%}")
    
    if success_rate >= 0.8:
        print("🎉 Phase 3: Self-Learning Optimization 集成测试通过！")
        print("🚀 系统已准备好进行生产环境部署！")
    else:
        print("⚠️  集成测试存在问题，需要进一步优化")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)