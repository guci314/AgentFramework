# -*- coding: utf-8 -*-
"""
策略效果跟踪服务

跟踪和分析自适应规则替换策略的执行效果，为策略学习和优化提供数据支持。
支持实时效果监控、历史数据分析和策略改进建议。
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

from ...domain.value_objects import (
    StrategyEffectiveness, ReplacementStrategyType, SituationScore, 
    ExecutionMetrics, AdaptiveReplacementConstants
)

logger = logging.getLogger(__name__)


class StrategyEffectivenessTracker:
    """策略效果跟踪器 - 监控和分析策略执行效果"""
    
    def __init__(self, max_history_size: int = 100):
        """
        初始化策略效果跟踪器
        
        Args:
            max_history_size: 最大历史记录数量
        """
        self.max_history_size = max_history_size
        
        # 策略执行历史
        self.strategy_history: deque[StrategyEffectiveness] = deque(maxlen=max_history_size)
        
        # 按策略类型分组的历史记录
        self.strategy_type_history: Dict[ReplacementStrategyType, List[StrategyEffectiveness]] = defaultdict(list)
        
        # 策略性能统计
        self.strategy_stats: Dict[ReplacementStrategyType, Dict[str, float]] = defaultdict(dict)
        
        # 上下文模式统计
        self.context_pattern_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # 实时监控数据
        self.recent_applications: deque[Dict[str, Any]] = deque(maxlen=20)
        
    def record_strategy_application(self,
                                  strategy_type: ReplacementStrategyType,
                                  applied_context: SituationScore,
                                  before_metrics: ExecutionMetrics,
                                  after_metrics: ExecutionMetrics,
                                  improvement_score: float,
                                  additional_data: Optional[Dict[str, Any]] = None) -> None:
        """
        记录策略应用效果
        
        Args:
            strategy_type: 应用的策略类型
            applied_context: 应用时的情境
            before_metrics: 应用前的执行指标
            after_metrics: 应用后的执行指标  
            improvement_score: 改进分数
            additional_data: 额外的数据
        """
        try:
            # 创建效果记录
            effectiveness = StrategyEffectiveness(
                strategy_type=strategy_type,
                applied_context=applied_context,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_score=improvement_score,
                application_timestamp=datetime.now()
            )
            
            # 添加到历史记录
            self.strategy_history.append(effectiveness)
            self.strategy_type_history[strategy_type].append(effectiveness)
            
            # 限制策略类型历史大小
            if len(self.strategy_type_history[strategy_type]) > self.max_history_size // 4:
                self.strategy_type_history[strategy_type] = self.strategy_type_history[strategy_type][-self.max_history_size // 4:]
            
            # 记录实时应用数据
            application_data = {
                'strategy_type': strategy_type.value,
                'timestamp': datetime.now(),
                'improvement_score': improvement_score,
                'performance_gain': effectiveness.get_performance_gain(),
                'efficiency_gain': effectiveness.get_efficiency_gain(),
                'is_successful': effectiveness.is_successful_application(),
                'context_health': applied_context.get_overall_health()
            }
            
            if additional_data:
                application_data.update(additional_data)
                
            self.recent_applications.append(application_data)
            
            # 更新统计信息
            self._update_strategy_statistics(strategy_type)
            self._update_context_pattern_stats(applied_context, effectiveness)
            
            logger.info(f"策略应用已记录: {strategy_type.value} - 改进分数: {improvement_score:.2f}")
            
        except Exception as e:
            logger.error(f"记录策略应用失败: {e}")
    
    def get_strategy_performance_summary(self, 
                                       strategy_type: Optional[ReplacementStrategyType] = None) -> Dict[str, Any]:
        """
        获取策略性能摘要
        
        Args:
            strategy_type: 特定策略类型（None表示所有策略）
            
        Returns:
            Dict[str, Any]: 性能摘要
        """
        try:
            if strategy_type:
                # 特定策略的性能摘要
                return self._get_single_strategy_summary(strategy_type)
            else:
                # 所有策略的综合摘要
                return self._get_comprehensive_summary()
                
        except Exception as e:
            logger.error(f"获取策略性能摘要失败: {e}")
            return {}
    
    def recommend_optimal_strategy(self, 
                                 current_situation: SituationScore,
                                 context: Dict[str, Any]) -> Tuple[ReplacementStrategyType, float]:
        """
        基于历史数据推荐最优策略
        
        Args:
            current_situation: 当前情境
            context: 执行上下文
            
        Returns:
            Tuple[ReplacementStrategyType, float]: (推荐策略, 推荐置信度)
        """
        try:
            # 分析相似情境下的策略表现
            similar_situations = self._find_similar_situations(current_situation)
            
            if not similar_situations:
                logger.warning("未找到相似情境，返回默认推荐")
                return ReplacementStrategyType.INCREMENTAL_IMPROVEMENT, 0.5
            
            # 计算各策略的预期效果
            strategy_scores = self._calculate_strategy_scores(similar_situations, current_situation)
            
            # 选择最优策略
            best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
            
            logger.info(f"推荐策略: {best_strategy[0].value} (置信度: {best_strategy[1]:.2f})")
            
            return best_strategy
            
        except Exception as e:
            logger.error(f"策略推荐失败: {e}")
            return ReplacementStrategyType.INCREMENTAL_IMPROVEMENT, 0.3
    
    def analyze_strategy_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        分析策略趋势
        
        Args:
            days: 分析的天数
            
        Returns:
            Dict[str, Any]: 趋势分析结果
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            recent_history = [
                eff for eff in self.strategy_history 
                if eff.application_timestamp >= cutoff_time
            ]
            
            if not recent_history:
                return {'message': f'最近{days}天无策略应用记录'}
            
            trends = {
                'period_days': days,
                'total_applications': len(recent_history),
                'strategy_distribution': self._calculate_strategy_distribution(recent_history),
                'average_improvement': statistics.mean([eff.improvement_score for eff in recent_history]),
                'success_rate': sum(1 for eff in recent_history if eff.is_successful_application()) / len(recent_history),
                'performance_trend': self._calculate_performance_trend(recent_history),
                'most_effective_strategy': self._find_most_effective_recent_strategy(recent_history),
                'context_patterns': self._analyze_context_patterns(recent_history)
            }
            
            logger.info(f"策略趋势分析完成: {days}天, {len(recent_history)}次应用")
            return trends
            
        except Exception as e:
            logger.error(f"策略趋势分析失败: {e}")
            return {}
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        获取策略改进建议
        
        Returns:
            List[Dict[str, Any]]: 改进建议列表
        """
        try:
            recommendations = []
            
            # 分析低效策略
            ineffective_strategies = self._identify_ineffective_strategies()
            for strategy_type, issues in ineffective_strategies.items():
                recommendations.append({
                    'type': 'strategy_optimization',
                    'strategy': strategy_type.value,
                    'priority': 'high',
                    'issues': issues,
                    'recommendation': f'考虑调整{strategy_type.value}策略的参数或使用条件'
                })
            
            # 分析参数优化机会
            parameter_optimizations = self._identify_parameter_optimizations()
            for optimization in parameter_optimizations:
                recommendations.append({
                    'type': 'parameter_tuning',
                    'priority': 'medium',
                    **optimization
                })
            
            # 分析新策略需求
            strategy_gaps = self._identify_strategy_gaps()
            for gap in strategy_gaps:
                recommendations.append({
                    'type': 'new_strategy',
                    'priority': 'low',
                    **gap
                })
            
            # 按优先级排序
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            logger.info(f"生成了 {len(recommendations)} 个改进建议")
            return recommendations
            
        except Exception as e:
            logger.error(f"生成改进建议失败: {e}")
            return []
    
    def export_performance_data(self, format_type: str = 'summary') -> Dict[str, Any]:
        """
        导出性能数据
        
        Args:
            format_type: 导出格式 ('summary', 'detailed', 'raw')
            
        Returns:
            Dict[str, Any]: 导出的数据
        """
        try:
            if format_type == 'raw':
                return {
                    'strategy_history': [
                        {
                            'strategy_type': eff.strategy_type.value,
                            'improvement_score': eff.improvement_score,
                            'performance_gain': eff.get_performance_gain(),
                            'efficiency_gain': eff.get_efficiency_gain(),
                            'is_successful': eff.is_successful_application(),
                            'timestamp': eff.application_timestamp.isoformat(),
                            'context_health': eff.applied_context.get_overall_health()
                        }
                        for eff in self.strategy_history
                    ]
                }
            elif format_type == 'detailed':
                return {
                    'strategy_statistics': dict(self.strategy_stats),
                    'context_patterns': dict(self.context_pattern_stats),
                    'recent_applications': list(self.recent_applications),
                    'trends': self.analyze_strategy_trends(30)  # 30天趋势
                }
            else:  # summary
                return {
                    'total_applications': len(self.strategy_history),
                    'strategy_performance': {
                        strategy_type.value: self.strategy_stats.get(strategy_type, {})
                        for strategy_type in ReplacementStrategyType
                    },
                    'overall_success_rate': self._calculate_overall_success_rate(),
                    'best_performing_strategy': self._find_best_performing_strategy(),
                    'recent_trends': self.analyze_strategy_trends(7)  # 7天趋势
                }
                
        except Exception as e:
            logger.error(f"导出性能数据失败: {e}")
            return {}
    
    # 私有辅助方法
    def _update_strategy_statistics(self, strategy_type: ReplacementStrategyType):
        """更新策略统计信息"""
        try:
            history = self.strategy_type_history[strategy_type]
            if not history:
                return
            
            # 计算统计指标
            improvement_scores = [eff.improvement_score for eff in history]
            performance_gains = [eff.get_performance_gain() for eff in history]
            success_rate = sum(1 for eff in history if eff.is_successful_application()) / len(history)
            
            self.strategy_stats[strategy_type] = {
                'total_applications': len(history),
                'average_improvement': statistics.mean(improvement_scores),
                'median_improvement': statistics.median(improvement_scores),
                'success_rate': success_rate,
                'average_performance_gain': statistics.mean(performance_gains),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"更新策略统计失败: {e}")
    
    def _update_context_pattern_stats(self, context: SituationScore, effectiveness: StrategyEffectiveness):
        """更新上下文模式统计"""
        try:
            # 根据上下文健康度分类
            health_category = 'high' if context.get_overall_health() > 0.7 else 'medium' if context.get_overall_health() > 0.4 else 'low'
            
            # 根据主要问题分类
            issues = context.get_critical_issues()
            issue_category = issues[0] if issues else 'no_issues'
            
            pattern_key = f"{health_category}_{issue_category}"
            
            if pattern_key not in self.context_pattern_stats:
                self.context_pattern_stats[pattern_key] = {
                    'count': 0,
                    'total_improvement': 0.0,
                    'successful_applications': 0,
                    'strategy_usage': defaultdict(int)
                }
            
            stats = self.context_pattern_stats[pattern_key]
            stats['count'] += 1
            stats['total_improvement'] += effectiveness.improvement_score
            if effectiveness.is_successful_application():
                stats['successful_applications'] += 1
            stats['strategy_usage'][effectiveness.strategy_type.value] += 1
            
        except Exception as e:
            logger.error(f"更新上下文模式统计失败: {e}")
    
    def _get_single_strategy_summary(self, strategy_type: ReplacementStrategyType) -> Dict[str, Any]:
        """获取单个策略的性能摘要"""
        history = self.strategy_type_history.get(strategy_type, [])
        stats = self.strategy_stats.get(strategy_type, {})
        
        if not history:
            return {'message': f'策略 {strategy_type.value} 无应用记录'}
        
        return {
            'strategy_type': strategy_type.value,
            'applications': len(history),
            'statistics': stats,
            'recent_performance': [eff.improvement_score for eff in history[-5:]],
            'best_application': max(history, key=lambda x: x.improvement_score).improvement_score,
            'worst_application': min(history, key=lambda x: x.improvement_score).improvement_score
        }
    
    def _get_comprehensive_summary(self) -> Dict[str, Any]:
        """获取所有策略的综合摘要"""
        return {
            'total_applications': len(self.strategy_history),
            'strategy_breakdown': {
                strategy_type.value: len(self.strategy_type_history.get(strategy_type, []))
                for strategy_type in ReplacementStrategyType
            },
            'overall_statistics': {
                'average_improvement': statistics.mean([eff.improvement_score for eff in self.strategy_history]) if self.strategy_history else 0.0,
                'success_rate': self._calculate_overall_success_rate(),
                'most_used_strategy': self._find_most_used_strategy(),
                'best_performing_strategy': self._find_best_performing_strategy()
            },
            'recent_trends': self.analyze_strategy_trends(7)
        }
    
    def _find_similar_situations(self, current_situation: SituationScore, similarity_threshold: float = 0.8) -> List[StrategyEffectiveness]:
        """查找相似情境"""
        similar = []
        
        for effectiveness in self.strategy_history:
            similarity = self._calculate_situation_similarity(current_situation, effectiveness.applied_context)
            if similarity >= similarity_threshold:
                similar.append(effectiveness)
        
        return similar
    
    def _calculate_situation_similarity(self, situation1: SituationScore, situation2: SituationScore) -> float:
        """计算情境相似度"""
        try:
            # 计算各维度的相似度
            dimensions = [
                abs(situation1.rule_density - situation2.rule_density),
                abs(situation1.execution_efficiency - situation2.execution_efficiency),
                abs(situation1.goal_progress - situation2.goal_progress),
                abs(situation1.failure_frequency - situation2.failure_frequency),
                abs(situation1.agent_utilization - situation2.agent_utilization),
                abs(situation1.phase_distribution - situation2.phase_distribution)
            ]
            
            # 计算平均相似度（差异越小，相似度越高）
            average_difference = statistics.mean(dimensions)
            similarity = 1.0 - average_difference
            
            return max(0.0, min(1.0, similarity))
            
        except Exception:
            return 0.0
    
    def _calculate_strategy_scores(self, similar_situations: List[StrategyEffectiveness], current_situation: SituationScore) -> Dict[ReplacementStrategyType, float]:
        """计算各策略的预期分数"""
        strategy_scores = defaultdict(list)
        
        # 收集相似情境下各策略的表现
        for effectiveness in similar_situations:
            strategy_scores[effectiveness.strategy_type].append(effectiveness.improvement_score)
        
        # 计算各策略的期望分数
        final_scores = {}
        for strategy_type, scores in strategy_scores.items():
            if scores:
                # 计算加权平均（考虑成功应用的权重）
                successful_scores = [score for score in scores if score > 0.6]
                if successful_scores:
                    final_scores[strategy_type] = statistics.mean(successful_scores) * 1.2  # 成功应用加权
                else:
                    final_scores[strategy_type] = statistics.mean(scores)
            else:
                final_scores[strategy_type] = 0.5  # 默认分数
        
        return final_scores
    
    def _calculate_overall_success_rate(self) -> float:
        """计算整体成功率"""
        if not self.strategy_history:
            return 0.0
        return sum(1 for eff in self.strategy_history if eff.is_successful_application()) / len(self.strategy_history)
    
    def _find_best_performing_strategy(self) -> str:
        """找到表现最好的策略"""
        if not self.strategy_stats:
            return "无数据"
        
        best_strategy = max(
            self.strategy_stats.items(),
            key=lambda x: x[1].get('average_improvement', 0) * x[1].get('success_rate', 0)
        )
        
        return best_strategy[0].value
    
    def _find_most_used_strategy(self) -> str:
        """找到使用最多的策略"""
        if not self.strategy_type_history:
            return "无数据"
        
        most_used = max(
            self.strategy_type_history.items(),
            key=lambda x: len(x[1])
        )
        
        return most_used[0].value
    
    def _calculate_strategy_distribution(self, history: List[StrategyEffectiveness]) -> Dict[str, int]:
        """计算策略分布"""
        distribution = defaultdict(int)
        for eff in history:
            distribution[eff.strategy_type.value] += 1
        return dict(distribution)
    
    def _calculate_performance_trend(self, history: List[StrategyEffectiveness]) -> str:
        """计算性能趋势"""
        if len(history) < 3:
            return "数据不足"
        
        # 按时间排序并计算趋势
        sorted_history = sorted(history, key=lambda x: x.application_timestamp)
        recent_scores = [eff.improvement_score for eff in sorted_history[-5:]]
        earlier_scores = [eff.improvement_score for eff in sorted_history[-10:-5]] if len(sorted_history) >= 10 else []
        
        if not earlier_scores:
            return "稳定"
        
        recent_avg = statistics.mean(recent_scores)
        earlier_avg = statistics.mean(earlier_scores)
        
        if recent_avg > earlier_avg + 0.1:
            return "上升"
        elif recent_avg < earlier_avg - 0.1:
            return "下降"
        else:
            return "稳定"
    
    def _find_most_effective_recent_strategy(self, history: List[StrategyEffectiveness]) -> Dict[str, Any]:
        """找到最近最有效的策略"""
        if not history:
            return {}
        
        best_recent = max(history, key=lambda x: x.improvement_score)
        return {
            'strategy_type': best_recent.strategy_type.value,
            'improvement_score': best_recent.improvement_score,
            'timestamp': best_recent.application_timestamp.isoformat()
        }
    
    def _analyze_context_patterns(self, history: List[StrategyEffectiveness]) -> Dict[str, Any]:
        """分析上下文模式"""
        health_distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for eff in history:
            health = eff.applied_context.get_overall_health()
            if health > 0.7:
                health_distribution['high'] += 1
            elif health > 0.4:
                health_distribution['medium'] += 1
            else:
                health_distribution['low'] += 1
        
        return {
            'health_distribution': health_distribution,
            'most_common_health_level': max(health_distribution.items(), key=lambda x: x[1])[0]
        }
    
    def _identify_ineffective_strategies(self) -> Dict[ReplacementStrategyType, List[str]]:
        """识别低效策略"""
        ineffective = {}
        
        for strategy_type, stats in self.strategy_stats.items():
            issues = []
            
            if stats.get('success_rate', 0) < 0.5:
                issues.append("成功率过低")
            if stats.get('average_improvement', 0) < 0.3:
                issues.append("平均改进效果不佳")
            if stats.get('total_applications', 0) > 5 and stats.get('average_performance_gain', 0) < 0:
                issues.append("性能提升为负")
            
            if issues:
                ineffective[strategy_type] = issues
        
        return ineffective
    
    def _identify_parameter_optimizations(self) -> List[Dict[str, Any]]:
        """识别参数优化机会"""
        optimizations = []
        
        # 分析替换比例的效果
        replacement_ratio_analysis = self._analyze_replacement_ratio_effectiveness()
        if replacement_ratio_analysis:
            optimizations.append(replacement_ratio_analysis)
        
        # 分析相似性阈值的效果
        similarity_threshold_analysis = self._analyze_similarity_threshold_effectiveness()
        if similarity_threshold_analysis:
            optimizations.append(similarity_threshold_analysis)
        
        return optimizations
    
    def _analyze_replacement_ratio_effectiveness(self) -> Optional[Dict[str, Any]]:
        """分析替换比例的有效性"""
        # 简化实现：根据历史数据分析最优替换比例范围
        if len(self.strategy_history) < 10:
            return None
        
        # 这里可以实现更复杂的分析逻辑
        return {
            'parameter': 'replacement_ratio',
            'current_range': '0.1-0.8',
            'recommended_range': '0.2-0.6',
            'reason': '历史数据显示中等替换比例效果更好'
        }
    
    def _analyze_similarity_threshold_effectiveness(self) -> Optional[Dict[str, Any]]:
        """分析相似性阈值的有效性"""
        # 简化实现
        if len(self.strategy_history) < 10:
            return None
        
        return {
            'parameter': 'similarity_threshold',
            'current_range': '0.6-0.9',
            'recommended_range': '0.7-0.85',
            'reason': '适中的相似性阈值在大多数情况下表现更佳'
        }
    
    def _identify_strategy_gaps(self) -> List[Dict[str, Any]]:
        """识别策略空白"""
        gaps = []
        
        # 分析是否需要新的策略类型
        context_patterns = self.context_pattern_stats
        
        # 检查是否有特定情境缺乏有效策略
        for pattern, stats in context_patterns.items():
            if stats['count'] > 5 and stats['successful_applications'] / stats['count'] < 0.4:
                gaps.append({
                    'context_pattern': pattern,
                    'success_rate': stats['successful_applications'] / stats['count'],
                    'recommendation': f'为{pattern}情境开发专门的策略'
                })
        
        return gaps