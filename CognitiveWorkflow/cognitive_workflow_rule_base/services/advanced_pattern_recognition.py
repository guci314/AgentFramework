# -*- coding: utf-8 -*-
"""
高级模式识别引擎

实现复杂的模式识别和预测分析功能，能够识别策略执行模式、
上下文模式、性能模式等，为智能决策提供深度洞察。

Phase 3: Self-Learning Optimization 核心组件
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import math
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from ..domain.value_objects import (
    ReplacementStrategyType, StrategyEffectiveness, SituationScore,
    RulePhase, ExecutionMetrics
)

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """模式类型"""
    TEMPORAL = "temporal"                    # 时间模式
    CONTEXTUAL = "contextual"               # 上下文模式
    PERFORMANCE = "performance"             # 性能模式
    STRATEGY_SEQUENCE = "strategy_sequence" # 策略序列模式
    CYCLICAL = "cyclical"                   # 周期性模式
    ANOMALY = "anomaly"                     # 异常模式
    CORRELATION = "correlation"             # 关联模式
    TREND = "trend"                         # 趋势模式


@dataclass
class Pattern:
    """模式定义"""
    pattern_id: str
    pattern_type: PatternType
    description: str
    confidence: float
    frequency: int
    last_occurrence: datetime
    parameters: Dict[str, Any]
    predictive_power: float
    impact_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type.value,
            'description': self.description,
            'confidence': self.confidence,
            'frequency': self.frequency,
            'last_occurrence': self.last_occurrence.isoformat(),
            'parameters': self.parameters,
            'predictive_power': self.predictive_power,
            'impact_score': self.impact_score
        }


@dataclass
class PatternPrediction:
    """模式预测"""
    predicted_pattern: Pattern
    probability: float
    expected_timing: datetime
    confidence_interval: Tuple[float, float]
    conditions: List[str]
    recommended_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'predicted_pattern': self.predicted_pattern.to_dict(),
            'probability': self.probability,
            'expected_timing': self.expected_timing.isoformat(),
            'confidence_interval': self.confidence_interval,
            'conditions': self.conditions,
            'recommended_actions': self.recommended_actions
        }


class PatternDetector(ABC):
    """模式检测器基类"""
    
    @abstractmethod
    def detect_patterns(self, data: List[Any]) -> List[Pattern]:
        """检测模式"""
        pass
    
    @abstractmethod
    def get_pattern_type(self) -> PatternType:
        """获取模式类型"""
        pass


class TemporalPatternDetector(PatternDetector):
    """时间模式检测器"""
    
    def get_pattern_type(self) -> PatternType:
        return PatternType.TEMPORAL
    
    def detect_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测时间模式"""
        patterns = []
        
        if len(data) < 5:
            return patterns
        
        try:
            # 检测时间间隔模式
            intervals = self._calculate_time_intervals(data)
            interval_pattern = self._detect_interval_pattern(intervals)
            if interval_pattern:
                patterns.append(interval_pattern)
            
            # 检测周期性模式
            cyclical_patterns = self._detect_cyclical_patterns(data)
            patterns.extend(cyclical_patterns)
            
            # 检测时间趋势
            trend_pattern = self._detect_time_trend(data)
            if trend_pattern:
                patterns.append(trend_pattern)
            
        except Exception as e:
            logger.error(f"时间模式检测失败: {e}")
        
        return patterns
    
    def _calculate_time_intervals(self, data: List[StrategyEffectiveness]) -> List[float]:
        """计算时间间隔"""
        intervals = []
        for i in range(1, len(data)):
            interval = (data[i].application_timestamp - data[i-1].application_timestamp).total_seconds()
            intervals.append(interval)
        return intervals
    
    def _detect_interval_pattern(self, intervals: List[float]) -> Optional[Pattern]:
        """检测间隔模式"""
        if len(intervals) < 3:
            return None
        
        # 计算间隔的统计特性
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        cv = std_interval / mean_interval if mean_interval > 0 else 0
        
        # 如果变异系数小，说明有规律性
        if cv < 0.3:  # 变异系数阈值
            confidence = 1.0 - cv
            return Pattern(
                pattern_id=f"temporal_interval_{int(mean_interval)}",
                pattern_type=PatternType.TEMPORAL,
                description=f"策略执行间隔相对稳定，平均间隔{mean_interval:.1f}秒",
                confidence=confidence,
                frequency=len(intervals),
                last_occurrence=datetime.now(),
                parameters={
                    'mean_interval': mean_interval,
                    'std_interval': std_interval,
                    'coefficient_variation': cv
                },
                predictive_power=confidence * 0.7,
                impact_score=0.6
            )
        return None
    
    def _detect_cyclical_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测周期性模式"""
        patterns = []
        
        if len(data) < 10:
            return patterns
        
        # 按小时分组检测日周期
        hourly_performance = defaultdict(list)
        for eff in data:
            hour = eff.application_timestamp.hour
            hourly_performance[hour].append(eff.improvement_score)
        
        # 检测是否有明显的时间偏好
        if len(hourly_performance) >= 3:
            hour_scores = {}
            for hour, scores in hourly_performance.items():
                hour_scores[hour] = np.mean(scores)
            
            # 找到最佳和最差时间
            best_hour = max(hour_scores.items(), key=lambda x: x[1])
            worst_hour = min(hour_scores.items(), key=lambda x: x[1])
            
            if best_hour[1] - worst_hour[1] > 0.2:  # 显著差异
                patterns.append(Pattern(
                    pattern_id=f"cyclical_hourly_{best_hour[0]}",
                    pattern_type=PatternType.CYCLICAL,
                    description=f"策略在{best_hour[0]}时表现最佳，{worst_hour[0]}时表现最差",
                    confidence=0.8,
                    frequency=len(data),
                    last_occurrence=datetime.now(),
                    parameters={
                        'best_hour': best_hour[0],
                        'best_score': best_hour[1],
                        'worst_hour': worst_hour[0],
                        'worst_score': worst_hour[1],
                        'hour_scores': hour_scores
                    },
                    predictive_power=0.6,
                    impact_score=0.7
                ))
        
        return patterns
    
    def _detect_time_trend(self, data: List[StrategyEffectiveness]) -> Optional[Pattern]:
        """检测时间趋势"""
        if len(data) < 5:
            return None
        
        # 计算时间序列趋势
        timestamps = [(eff.application_timestamp - data[0].application_timestamp).total_seconds() 
                     for eff in data]
        scores = [eff.improvement_score for eff in data]
        
        # 计算线性回归
        correlation = np.corrcoef(timestamps, scores)[0, 1] if len(timestamps) > 1 else 0
        
        if abs(correlation) > 0.5:  # 显著相关
            trend_direction = "上升" if correlation > 0 else "下降"
            confidence = abs(correlation)
            
            return Pattern(
                pattern_id=f"trend_{trend_direction}_{abs(correlation):.2f}",
                pattern_type=PatternType.TREND,
                description=f"策略性能呈{trend_direction}趋势，相关系数{correlation:.3f}",
                confidence=confidence,
                frequency=len(data),
                last_occurrence=datetime.now(),
                parameters={
                    'correlation': correlation,
                    'trend_direction': trend_direction,
                    'data_points': len(data)
                },
                predictive_power=confidence * 0.8,
                impact_score=confidence * 0.9
            )
        
        return None


class ContextualPatternDetector(PatternDetector):
    """上下文模式检测器"""
    
    def get_pattern_type(self) -> PatternType:
        return PatternType.CONTEXTUAL
    
    def detect_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测上下文模式"""
        patterns = []
        
        if len(data) < 3:
            return patterns
        
        try:
            # 检测健康度模式
            health_patterns = self._detect_health_patterns(data)
            patterns.extend(health_patterns)
            
            # 检测关键问题模式
            issue_patterns = self._detect_issue_patterns(data)
            patterns.extend(issue_patterns)
            
            # 检测上下文聚类
            cluster_patterns = self._detect_context_clusters(data)
            patterns.extend(cluster_patterns)
            
        except Exception as e:
            logger.error(f"上下文模式检测失败: {e}")
        
        return patterns
    
    def _detect_health_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测健康度模式"""
        patterns = []
        
        # 按健康度分组
        health_groups = {'high': [], 'medium': [], 'low': []}
        
        for eff in data:
            health = eff.applied_context.get_overall_health()
            if health > 0.7:
                health_groups['high'].append(eff)
            elif health > 0.4:
                health_groups['medium'].append(eff)
            else:
                health_groups['low'].append(eff)
        
        # 分析每组的性能
        for group_name, group_data in health_groups.items():
            if len(group_data) >= 2:
                avg_performance = np.mean([eff.improvement_score for eff in group_data])
                
                patterns.append(Pattern(
                    pattern_id=f"health_{group_name}_performance",
                    pattern_type=PatternType.CONTEXTUAL,
                    description=f"{group_name}健康度情境下平均性能{avg_performance:.3f}",
                    confidence=0.8,
                    frequency=len(group_data),
                    last_occurrence=max(eff.application_timestamp for eff in group_data),
                    parameters={
                        'health_level': group_name,
                        'average_performance': avg_performance,
                        'sample_size': len(group_data)
                    },
                    predictive_power=0.7,
                    impact_score=0.8
                ))
        
        return patterns
    
    def _detect_issue_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测关键问题模式"""
        patterns = []
        
        # 收集所有关键问题
        issue_performance = defaultdict(list)
        
        for eff in data:
            issues = eff.applied_context.get_critical_issues()
            if issues:
                for issue in issues:
                    issue_performance[issue].append(eff.improvement_score)
            else:
                issue_performance['no_issues'].append(eff.improvement_score)
        
        # 分析每种问题的影响
        for issue, scores in issue_performance.items():
            if len(scores) >= 2:
                avg_score = np.mean(scores)
                
                patterns.append(Pattern(
                    pattern_id=f"issue_{issue}_impact",
                    pattern_type=PatternType.CONTEXTUAL,
                    description=f"问题'{issue}'情境下平均性能{avg_score:.3f}",
                    confidence=0.75,
                    frequency=len(scores),
                    last_occurrence=datetime.now(),
                    parameters={
                        'issue_type': issue,
                        'average_performance': avg_score,
                        'sample_size': len(scores)
                    },
                    predictive_power=0.6,
                    impact_score=0.7
                ))
        
        return patterns
    
    def _detect_context_clusters(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测上下文聚类"""
        patterns = []
        
        # 简化的聚类：基于健康度和主要问题
        context_signatures = {}
        
        for eff in data:
            context = eff.applied_context
            health_level = "high" if context.get_overall_health() > 0.7 else "medium" if context.get_overall_health() > 0.4 else "low"
            issues = context.get_critical_issues()
            main_issue = issues[0] if issues else "none"
            
            signature = f"{health_level}_{main_issue}"
            
            if signature not in context_signatures:
                context_signatures[signature] = []
            context_signatures[signature].append(eff)
        
        # 分析每个聚类
        for signature, cluster_data in context_signatures.items():
            if len(cluster_data) >= 3:
                avg_performance = np.mean([eff.improvement_score for eff in cluster_data])
                performance_std = np.std([eff.improvement_score for eff in cluster_data])
                
                patterns.append(Pattern(
                    pattern_id=f"cluster_{signature}",
                    pattern_type=PatternType.CONTEXTUAL,
                    description=f"上下文聚类'{signature}'平均性能{avg_performance:.3f}±{performance_std:.3f}",
                    confidence=0.7,
                    frequency=len(cluster_data),
                    last_occurrence=max(eff.application_timestamp for eff in cluster_data),
                    parameters={
                        'context_signature': signature,
                        'average_performance': avg_performance,
                        'performance_std': performance_std,
                        'cluster_size': len(cluster_data)
                    },
                    predictive_power=0.65,
                    impact_score=0.75
                ))
        
        return patterns


class PerformancePatternDetector(PatternDetector):
    """性能模式检测器"""
    
    def get_pattern_type(self) -> PatternType:
        return PatternType.PERFORMANCE
    
    def detect_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测性能模式"""
        patterns = []
        
        if len(data) < 5:
            return patterns
        
        try:
            # 检测性能峰值模式
            peak_patterns = self._detect_peak_patterns(data)
            patterns.extend(peak_patterns)
            
            # 检测性能下降模式
            decline_patterns = self._detect_decline_patterns(data)
            patterns.extend(decline_patterns)
            
            # 检测性能稳定区间
            stability_patterns = self._detect_stability_patterns(data)
            patterns.extend(stability_patterns)
            
            # 检测异常性能
            anomaly_patterns = self._detect_performance_anomalies(data)
            patterns.extend(anomaly_patterns)
            
        except Exception as e:
            logger.error(f"性能模式检测失败: {e}")
        
        return patterns
    
    def _detect_peak_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测性能峰值模式"""
        patterns = []
        
        scores = [eff.improvement_score for eff in data]
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # 找到显著高于平均值的点
        peak_threshold = mean_score + 1.5 * std_score
        peaks = [i for i, score in enumerate(scores) if score > peak_threshold]
        
        if len(peaks) >= 2:
            # 分析峰值出现的条件
            peak_contexts = [data[i].applied_context for i in peaks]
            
            # 找到共同特征
            common_features = self._find_common_context_features(peak_contexts)
            
            if common_features:
                patterns.append(Pattern(
                    pattern_id=f"performance_peaks_{len(peaks)}",
                    pattern_type=PatternType.PERFORMANCE,
                    description=f"发现{len(peaks)}个性能峰值，平均分数{np.mean([scores[i] for i in peaks]):.3f}",
                    confidence=0.8,
                    frequency=len(peaks),
                    last_occurrence=data[peaks[-1]].application_timestamp,
                    parameters={
                        'peak_indices': peaks,
                        'peak_scores': [scores[i] for i in peaks],
                        'peak_threshold': peak_threshold,
                        'common_features': common_features
                    },
                    predictive_power=0.75,
                    impact_score=0.9
                ))
        
        return patterns
    
    def _detect_decline_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测性能下降模式"""
        patterns = []
        
        # 检测连续下降
        scores = [eff.improvement_score for eff in data]
        decline_sequences = []
        current_decline = []
        
        for i in range(1, len(scores)):
            if scores[i] < scores[i-1]:
                if not current_decline:
                    current_decline = [i-1, i]
                else:
                    current_decline.append(i)
            else:
                if len(current_decline) >= 3:  # 至少3个连续下降点
                    decline_sequences.append(current_decline)
                current_decline = []
        
        # 处理结尾的下降序列
        if len(current_decline) >= 3:
            decline_sequences.append(current_decline)
        
        for decline_seq in decline_sequences:
            decline_start = scores[decline_seq[0]]
            decline_end = scores[decline_seq[-1]]
            decline_magnitude = decline_start - decline_end
            
            if decline_magnitude > 0.1:  # 显著下降
                patterns.append(Pattern(
                    pattern_id=f"performance_decline_{decline_seq[0]}_{decline_seq[-1]}",
                    pattern_type=PatternType.PERFORMANCE,
                    description=f"性能连续下降，从{decline_start:.3f}降至{decline_end:.3f}",
                    confidence=0.85,
                    frequency=len(decline_seq),
                    last_occurrence=data[decline_seq[-1]].application_timestamp,
                    parameters={
                        'decline_sequence': decline_seq,
                        'decline_start': decline_start,
                        'decline_end': decline_end,
                        'decline_magnitude': decline_magnitude
                    },
                    predictive_power=0.7,
                    impact_score=0.8
                ))
        
        return patterns
    
    def _detect_stability_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测性能稳定区间"""
        patterns = []
        
        scores = [eff.improvement_score for eff in data]
        
        # 使用滑动窗口检测稳定区间
        window_size = min(5, len(scores))
        stable_regions = []
        
        for i in range(len(scores) - window_size + 1):
            window_scores = scores[i:i+window_size]
            window_std = np.std(window_scores)
            
            if window_std < 0.05:  # 低变异性
                stable_regions.append((i, i+window_size-1, np.mean(window_scores), window_std))
        
        # 合并重叠的稳定区间
        merged_regions = self._merge_overlapping_regions(stable_regions)
        
        for start, end, avg_score, stability in merged_regions:
            if end - start >= 3:  # 至少4个数据点
                patterns.append(Pattern(
                    pattern_id=f"stability_{start}_{end}",
                    pattern_type=PatternType.PERFORMANCE,
                    description=f"性能稳定区间，平均分数{avg_score:.3f}，稳定性{1-stability:.3f}",
                    confidence=0.8,
                    frequency=end - start + 1,
                    last_occurrence=data[end].application_timestamp,
                    parameters={
                        'start_index': start,
                        'end_index': end,
                        'average_score': avg_score,
                        'stability_metric': 1 - stability,
                        'duration': end - start + 1
                    },
                    predictive_power=0.6,
                    impact_score=0.7
                ))
        
        return patterns
    
    def _detect_performance_anomalies(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测性能异常"""
        patterns = []
        
        scores = [eff.improvement_score for eff in data]
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # 检测异常值（超过2个标准差）
        anomaly_threshold_high = mean_score + 2 * std_score
        anomaly_threshold_low = mean_score - 2 * std_score
        
        anomalies = []
        for i, score in enumerate(scores):
            if score > anomaly_threshold_high or score < anomaly_threshold_low:
                anomaly_type = "positive" if score > anomaly_threshold_high else "negative"
                anomalies.append((i, score, anomaly_type))
        
        if anomalies:
            patterns.append(Pattern(
                pattern_id=f"performance_anomalies_{len(anomalies)}",
                pattern_type=PatternType.ANOMALY,
                description=f"发现{len(anomalies)}个性能异常值",
                confidence=0.9,
                frequency=len(anomalies),
                last_occurrence=data[anomalies[-1][0]].application_timestamp,
                parameters={
                    'anomalies': anomalies,
                    'high_threshold': anomaly_threshold_high,
                    'low_threshold': anomaly_threshold_low,
                    'baseline_mean': mean_score,
                    'baseline_std': std_score
                },
                predictive_power=0.5,
                impact_score=0.8
            ))
        
        return patterns
    
    def _find_common_context_features(self, contexts: List[SituationScore]) -> Dict[str, Any]:
        """找到上下文的共同特征"""
        if not contexts:
            return {}
        
        # 计算各维度的平均值和一致性
        features = {}
        
        # 健康度特征
        health_scores = [ctx.get_overall_health() for ctx in contexts]
        if len(set([h > 0.7 for h in health_scores])) == 1:  # 都在同一健康等级
            features['consistent_health_level'] = "high" if health_scores[0] > 0.7 else "medium" if health_scores[0] > 0.4 else "low"
        
        # 关键问题特征
        all_issues = []
        for ctx in contexts:
            all_issues.extend(ctx.get_critical_issues())
        
        if all_issues:
            issue_counts = Counter(all_issues)
            common_issues = [issue for issue, count in issue_counts.items() if count >= len(contexts) * 0.7]
            if common_issues:
                features['common_issues'] = common_issues
        
        return features
    
    def _merge_overlapping_regions(self, regions: List[Tuple]) -> List[Tuple]:
        """合并重叠的区间"""
        if not regions:
            return []
        
        # 按开始位置排序
        sorted_regions = sorted(regions, key=lambda x: x[0])
        merged = [sorted_regions[0]]
        
        for current in sorted_regions[1:]:
            last = merged[-1]
            
            # 如果重叠，合并
            if current[0] <= last[1] + 1:
                new_end = max(last[1], current[1])
                new_avg = (last[2] * (last[1] - last[0] + 1) + current[2] * (current[1] - current[0] + 1)) / (new_end - last[0] + 1)
                new_std = min(last[3], current[3])  # 取更稳定的
                merged[-1] = (last[0], new_end, new_avg, new_std)
            else:
                merged.append(current)
        
        return merged


class StrategySequencePatternDetector(PatternDetector):
    """策略序列模式检测器"""
    
    def get_pattern_type(self) -> PatternType:
        return PatternType.STRATEGY_SEQUENCE
    
    def detect_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测策略序列模式"""
        patterns = []
        
        if len(data) < 4:
            return patterns
        
        try:
            # 检测策略转换模式
            transition_patterns = self._detect_transition_patterns(data)
            patterns.extend(transition_patterns)
            
            # 检测策略组合模式
            combination_patterns = self._detect_combination_patterns(data)
            patterns.extend(combination_patterns)
            
            # 检测成功序列模式
            success_patterns = self._detect_success_sequences(data)
            patterns.extend(success_patterns)
            
        except Exception as e:
            logger.error(f"策略序列模式检测失败: {e}")
        
        return patterns
    
    def _detect_transition_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测策略转换模式"""
        patterns = []
        
        # 构建策略转换序列
        strategy_sequence = [eff.strategy_type for eff in data]
        transitions = [(strategy_sequence[i], strategy_sequence[i+1]) for i in range(len(strategy_sequence)-1)]
        
        # 统计转换频率
        transition_counts = Counter(transitions)
        
        # 找到频繁转换
        total_transitions = len(transitions)
        frequent_transitions = [(trans, count) for trans, count in transition_counts.items() 
                              if count >= max(2, total_transitions * 0.2)]
        
        for (from_strategy, to_strategy), count in frequent_transitions:
            # 计算转换后的性能变化
            performance_changes = []
            for i in range(len(data)-1):
                if (data[i].strategy_type, data[i+1].strategy_type) == (from_strategy, to_strategy):
                    performance_changes.append(data[i+1].improvement_score - data[i].improvement_score)
            
            if performance_changes:
                avg_change = np.mean(performance_changes)
                
                patterns.append(Pattern(
                    pattern_id=f"transition_{from_strategy.value}_to_{to_strategy.value}",
                    pattern_type=PatternType.STRATEGY_SEQUENCE,
                    description=f"策略转换：{from_strategy.value} → {to_strategy.value}，平均性能变化{avg_change:.3f}",
                    confidence=0.8,
                    frequency=count,
                    last_occurrence=datetime.now(),
                    parameters={
                        'from_strategy': from_strategy.value,
                        'to_strategy': to_strategy.value,
                        'frequency': count,
                        'average_performance_change': avg_change,
                        'performance_changes': performance_changes
                    },
                    predictive_power=0.7,
                    impact_score=abs(avg_change)
                ))
        
        return patterns
    
    def _detect_combination_patterns(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测策略组合模式"""
        patterns = []
        
        # 使用滑动窗口检测策略组合
        window_size = 3
        for i in range(len(data) - window_size + 1):
            window_data = data[i:i+window_size]
            strategy_combo = tuple(eff.strategy_type for eff in window_data)
            combo_performance = np.mean([eff.improvement_score for eff in window_data])
            
            # 这里可以添加更复杂的组合分析逻辑
            # 简化实现：记录高性能组合
            if combo_performance > 0.8:
                patterns.append(Pattern(
                    pattern_id=f"combo_{'_'.join([s.value[:4] for s in strategy_combo])}",
                    pattern_type=PatternType.STRATEGY_SEQUENCE,
                    description=f"高性能策略组合：{' → '.join([s.value for s in strategy_combo])}",
                    confidence=0.75,
                    frequency=1,  # 在完整实现中应该统计频率
                    last_occurrence=window_data[-1].application_timestamp,
                    parameters={
                        'strategy_combination': [s.value for s in strategy_combo],
                        'average_performance': combo_performance,
                        'window_size': window_size
                    },
                    predictive_power=0.65,
                    impact_score=0.8
                ))
        
        return patterns
    
    def _detect_success_sequences(self, data: List[StrategyEffectiveness]) -> List[Pattern]:
        """检测成功序列模式"""
        patterns = []
        
        # 找到连续成功的序列
        success_sequences = []
        current_sequence = []
        
        for eff in data:
            if eff.is_successful_application():
                current_sequence.append(eff)
            else:
                if len(current_sequence) >= 3:  # 至少3个连续成功
                    success_sequences.append(current_sequence)
                current_sequence = []
        
        # 处理结尾的成功序列
        if len(current_sequence) >= 3:
            success_sequences.append(current_sequence)
        
        for seq in success_sequences:
            strategy_types = [eff.strategy_type for eff in seq]
            avg_performance = np.mean([eff.improvement_score for eff in seq])
            
            patterns.append(Pattern(
                pattern_id=f"success_sequence_{len(seq)}_{seq[0].application_timestamp.strftime('%H%M')}",
                pattern_type=PatternType.STRATEGY_SEQUENCE,
                description=f"连续{len(seq)}个成功策略执行，平均性能{avg_performance:.3f}",
                confidence=0.85,
                frequency=len(seq),
                last_occurrence=seq[-1].application_timestamp,
                parameters={
                    'sequence_length': len(seq),
                    'strategy_sequence': [s.value for s in strategy_types],
                    'average_performance': avg_performance,
                    'start_time': seq[0].application_timestamp.isoformat(),
                    'end_time': seq[-1].application_timestamp.isoformat()
                },
                predictive_power=0.8,
                impact_score=0.9
            ))
        
        return patterns


class AdvancedPatternRecognitionEngine:
    """高级模式识别引擎 - Phase 3核心组件"""
    
    def __init__(self):
        """初始化模式识别引擎"""
        # 注册各种模式检测器
        self.detectors: Dict[PatternType, PatternDetector] = {
            PatternType.TEMPORAL: TemporalPatternDetector(),
            PatternType.CONTEXTUAL: ContextualPatternDetector(),
            PatternType.PERFORMANCE: PerformancePatternDetector(),
            PatternType.STRATEGY_SEQUENCE: StrategySequencePatternDetector()
        }
        
        # 模式存储
        self.discovered_patterns: Dict[str, Pattern] = {}
        self.pattern_predictions: List[PatternPrediction] = []
        
        # 配置
        self.min_data_points = 3
        self.confidence_threshold = 0.6
        self.max_patterns_per_type = 10
        
        logger.info("高级模式识别引擎已初始化")
    
    def analyze_patterns(self, 
                        effectiveness_history: List[StrategyEffectiveness],
                        include_predictions: bool = True) -> Dict[str, Any]:
        """
        分析模式
        
        Args:
            effectiveness_history: 策略效果历史数据
            include_predictions: 是否包含预测
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            logger.info(f"开始模式分析，历史数据{len(effectiveness_history)}条")
            
            if len(effectiveness_history) < self.min_data_points:
                return {
                    'patterns': {},
                    'predictions': [],
                    'summary': {
                        'total_patterns': 0,
                        'high_confidence_patterns': 0,
                        'message': f'数据不足，需要至少{self.min_data_points}条记录'
                    }
                }
            
            # 运行所有检测器
            all_patterns = {}
            pattern_counts = {}
            
            for pattern_type, detector in self.detectors.items():
                try:
                    patterns = detector.detect_patterns(effectiveness_history)
                    
                    # 过滤低置信度模式
                    high_confidence_patterns = [p for p in patterns if p.confidence >= self.confidence_threshold]
                    
                    # 限制每种类型的模式数量
                    if len(high_confidence_patterns) > self.max_patterns_per_type:
                        high_confidence_patterns = sorted(high_confidence_patterns, 
                                                        key=lambda x: x.confidence, reverse=True)[:self.max_patterns_per_type]
                    
                    all_patterns[pattern_type.value] = [p.to_dict() for p in high_confidence_patterns]
                    pattern_counts[pattern_type.value] = len(high_confidence_patterns)
                    
                    # 更新发现的模式
                    for pattern in high_confidence_patterns:
                        self.discovered_patterns[pattern.pattern_id] = pattern
                    
                    logger.info(f"{pattern_type.value}模式检测完成：发现{len(high_confidence_patterns)}个高置信度模式")
                    
                except Exception as e:
                    logger.error(f"{pattern_type.value}模式检测失败: {e}")
                    all_patterns[pattern_type.value] = []
                    pattern_counts[pattern_type.value] = 0
            
            # 生成预测
            predictions = []
            if include_predictions:
                predictions = self._generate_predictions(effectiveness_history)
            
            # 计算摘要统计
            total_patterns = sum(pattern_counts.values())
            high_confidence_patterns = sum(1 for patterns in all_patterns.values() 
                                         for pattern in patterns 
                                         if pattern['confidence'] >= 0.8)
            
            # 识别最重要的模式
            important_patterns = self._identify_important_patterns(all_patterns)
            
            # 生成洞察和建议
            insights = self._generate_insights(all_patterns, effectiveness_history)
            
            result = {
                'patterns': all_patterns,
                'predictions': [p.to_dict() for p in predictions],
                'important_patterns': important_patterns,
                'insights': insights,
                'summary': {
                    'total_patterns': total_patterns,
                    'high_confidence_patterns': high_confidence_patterns,
                    'pattern_counts_by_type': pattern_counts,
                    'data_points_analyzed': len(effectiveness_history),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info(f"模式分析完成：发现{total_patterns}个模式，{high_confidence_patterns}个高置信度模式")
            return result
            
        except Exception as e:
            logger.error(f"模式分析失败: {e}")
            return {
                'patterns': {},
                'predictions': [],
                'summary': {
                    'total_patterns': 0,
                    'high_confidence_patterns': 0,
                    'error': str(e)
                }
            }
    
    def _generate_predictions(self, history: List[StrategyEffectiveness]) -> List[PatternPrediction]:
        """生成模式预测"""
        predictions = []
        
        try:
            # 基于发现的模式生成预测
            for pattern in self.discovered_patterns.values():
                if pattern.predictive_power > 0.6:
                    prediction = self._create_pattern_prediction(pattern, history)
                    if prediction:
                        predictions.append(prediction)
            
            # 按概率排序
            predictions.sort(key=lambda x: x.probability, reverse=True)
            
            # 限制预测数量
            return predictions[:5]
            
        except Exception as e:
            logger.error(f"生成预测失败: {e}")
            return []
    
    def _create_pattern_prediction(self, 
                                 pattern: Pattern, 
                                 history: List[StrategyEffectiveness]) -> Optional[PatternPrediction]:
        """创建模式预测"""
        try:
            # 基于模式类型生成不同的预测
            if pattern.pattern_type == PatternType.CYCLICAL:
                return self._predict_cyclical_pattern(pattern, history)
            elif pattern.pattern_type == PatternType.TREND:
                return self._predict_trend_pattern(pattern, history)
            elif pattern.pattern_type == PatternType.PERFORMANCE:
                return self._predict_performance_pattern(pattern, history)
            elif pattern.pattern_type == PatternType.STRATEGY_SEQUENCE:
                return self._predict_sequence_pattern(pattern, history)
            else:
                return self._predict_generic_pattern(pattern, history)
                
        except Exception as e:
            logger.error(f"创建模式预测失败: {e}")
            return None
    
    def _predict_cyclical_pattern(self, 
                                pattern: Pattern, 
                                history: List[StrategyEffectiveness]) -> Optional[PatternPrediction]:
        """预测周期性模式"""
        if 'best_hour' in pattern.parameters:
            best_hour = pattern.parameters['best_hour']
            now = datetime.now()
            
            # 计算下一个最佳时间
            next_best_time = now.replace(hour=best_hour, minute=0, second=0, microsecond=0)
            if next_best_time <= now:
                next_best_time += timedelta(days=1)
            
            return PatternPrediction(
                predicted_pattern=pattern,
                probability=pattern.confidence * 0.8,
                expected_timing=next_best_time,
                confidence_interval=(pattern.confidence - 0.1, pattern.confidence + 0.1),
                conditions=[f"在{best_hour}时执行策略"],
                recommended_actions=[f"调度策略执行到{best_hour}:00附近", "准备高优先级任务"]
            )
        
        return None
    
    def _predict_trend_pattern(self, 
                             pattern: Pattern, 
                             history: List[StrategyEffectiveness]) -> Optional[PatternPrediction]:
        """预测趋势模式"""
        correlation = pattern.parameters.get('correlation', 0)
        trend_direction = pattern.parameters.get('trend_direction', '')
        
        # 预测趋势继续
        next_execution_time = datetime.now() + timedelta(hours=1)  # 假设下次执行时间
        
        conditions = [f"趋势{trend_direction}继续"]
        actions = []
        
        if trend_direction == "上升":
            actions = ["继续当前策略方向", "可以适度增加风险"]
            probability = pattern.confidence * 0.9
        else:
            actions = ["考虑调整策略", "增强监控和干预"]
            probability = pattern.confidence * 0.7
        
        return PatternPrediction(
            predicted_pattern=pattern,
            probability=probability,
            expected_timing=next_execution_time,
            confidence_interval=(probability - 0.1, probability + 0.1),
            conditions=conditions,
            recommended_actions=actions
        )
    
    def _predict_performance_pattern(self, 
                                   pattern: Pattern, 
                                   history: List[StrategyEffectiveness]) -> Optional[PatternPrediction]:
        """预测性能模式"""
        if pattern.pattern_id.startswith('performance_peaks'):
            # 预测下一个性能峰值
            common_features = pattern.parameters.get('common_features', {})
            
            conditions = []
            if 'consistent_health_level' in common_features:
                conditions.append(f"系统健康度保持{common_features['consistent_health_level']}水平")
            if 'common_issues' in common_features:
                conditions.append(f"避免问题：{', '.join(common_features['common_issues'])}")
            
            return PatternPrediction(
                predicted_pattern=pattern,
                probability=pattern.confidence * 0.6,
                expected_timing=datetime.now() + timedelta(hours=2),
                confidence_interval=(0.4, 0.8),
                conditions=conditions,
                recommended_actions=["创造峰值条件", "准备资源投入", "监控关键指标"]
            )
        
        return None
    
    def _predict_sequence_pattern(self, 
                                pattern: Pattern, 
                                history: List[StrategyEffectiveness]) -> Optional[PatternPrediction]:
        """预测序列模式"""
        if pattern.pattern_id.startswith('transition_'):
            from_strategy = pattern.parameters.get('from_strategy')
            to_strategy = pattern.parameters.get('to_strategy')
            
            # 检查当前是否处于转换前状态
            if history and history[-1].strategy_type.value == from_strategy:
                return PatternPrediction(
                    predicted_pattern=pattern,
                    probability=pattern.confidence * 0.8,
                    expected_timing=datetime.now() + timedelta(minutes=30),
                    confidence_interval=(0.6, 0.9),
                    conditions=[f"当前策略为{from_strategy}"],
                    recommended_actions=[f"准备转换到{to_strategy}策略", "评估转换条件"]
                )
        
        return None
    
    def _predict_generic_pattern(self, 
                               pattern: Pattern, 
                               history: List[StrategyEffectiveness]) -> Optional[PatternPrediction]:
        """预测通用模式"""
        return PatternPrediction(
            predicted_pattern=pattern,
            probability=pattern.predictive_power,
            expected_timing=datetime.now() + timedelta(hours=1),
            confidence_interval=(pattern.confidence - 0.2, pattern.confidence + 0.1),
            conditions=["基于历史模式"],
            recommended_actions=["监控模式指标", "准备相应措施"]
        )
    
    def _identify_important_patterns(self, all_patterns: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """识别重要模式"""
        important = []
        
        for pattern_type, patterns in all_patterns.items():
            for pattern in patterns:
                # 计算重要性分数
                importance_score = (
                    pattern['confidence'] * 0.4 +
                    pattern['predictive_power'] * 0.3 +
                    pattern['impact_score'] * 0.3
                )
                
                if importance_score > 0.7:
                    important.append({
                        'pattern': pattern,
                        'importance_score': importance_score,
                        'reasons': self._explain_importance(pattern, importance_score)
                    })
        
        # 按重要性排序
        important.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return important[:5]  # 返回前5个最重要的模式
    
    def _explain_importance(self, pattern: Dict[str, Any], score: float) -> List[str]:
        """解释模式重要性"""
        reasons = []
        
        if pattern['confidence'] > 0.8:
            reasons.append("高置信度模式")
        
        if pattern['predictive_power'] > 0.7:
            reasons.append("强预测能力")
        
        if pattern['impact_score'] > 0.8:
            reasons.append("高影响力")
        
        if pattern['frequency'] > 5:
            reasons.append("高频出现")
        
        if score > 0.9:
            reasons.append("综合评分优秀")
        
        return reasons
    
    def _generate_insights(self, 
                         all_patterns: Dict[str, List[Dict]], 
                         history: List[StrategyEffectiveness]) -> List[Dict[str, Any]]:
        """生成洞察和建议"""
        insights = []
        
        try:
            # 分析整体趋势
            if history:
                recent_performance = [eff.improvement_score for eff in history[-5:]]
                if len(recent_performance) >= 3:
                    trend = "improving" if recent_performance[-1] > recent_performance[0] else "declining"
                    insights.append({
                        'type': 'trend_analysis',
                        'insight': f"最近性能呈{trend}趋势",
                        'confidence': 0.8,
                        'recommendation': "继续监控趋势变化" if trend == "improving" else "需要干预措施"
                    })
            
            # 分析模式密度
            total_patterns = sum(len(patterns) for patterns in all_patterns.values())
            if total_patterns > 10:
                insights.append({
                    'type': 'pattern_density',
                    'insight': f"发现{total_patterns}个模式，系统行为高度可预测",
                    'confidence': 0.9,
                    'recommendation': "可以实施更积极的优化策略"
                })
            elif total_patterns < 3:
                insights.append({
                    'type': 'pattern_density',
                    'insight': "模式较少，系统行为随机性较高",
                    'confidence': 0.8,
                    'recommendation': "需要收集更多数据或增加策略多样性"
                })
            
            # 分析策略效果
            if 'performance' in all_patterns and all_patterns['performance']:
                peak_patterns = [p for p in all_patterns['performance'] if 'peaks' in p['pattern_id']]
                if peak_patterns:
                    insights.append({
                        'type': 'performance_optimization',
                        'insight': f"发现{len(peak_patterns)}个性能峰值模式",
                        'confidence': 0.85,
                        'recommendation': "重点研究峰值条件，复制成功经验"
                    })
            
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
        
        return insights
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """获取模式摘要"""
        if not self.discovered_patterns:
            return {'message': '暂无发现的模式'}
        
        # 按类型分组
        patterns_by_type = defaultdict(list)
        for pattern in self.discovered_patterns.values():
            patterns_by_type[pattern.pattern_type.value].append(pattern)
        
        # 计算统计信息
        total_patterns = len(self.discovered_patterns)
        avg_confidence = np.mean([p.confidence for p in self.discovered_patterns.values()])
        high_impact_patterns = sum(1 for p in self.discovered_patterns.values() if p.impact_score > 0.8)
        
        return {
            'total_patterns': total_patterns,
            'patterns_by_type': {ptype: len(patterns) for ptype, patterns in patterns_by_type.items()},
            'average_confidence': avg_confidence,
            'high_impact_patterns': high_impact_patterns,
            'most_recent_pattern': max(self.discovered_patterns.values(), 
                                     key=lambda x: x.last_occurrence).pattern_id,
            'prediction_count': len(self.pattern_predictions)
        }
    
    def export_patterns(self, format_type: str = 'summary') -> Dict[str, Any]:
        """导出模式数据"""
        if format_type == 'detailed':
            return {
                'discovered_patterns': {pid: pattern.to_dict() for pid, pattern in self.discovered_patterns.items()},
                'predictions': [pred.to_dict() for pred in self.pattern_predictions],
                'detector_configs': {
                    'min_data_points': self.min_data_points,
                    'confidence_threshold': self.confidence_threshold,
                    'max_patterns_per_type': self.max_patterns_per_type
                }
            }
        else:
            return self.get_pattern_summary()
    
    def clear_patterns(self):
        """清除所有模式"""
        self.discovered_patterns.clear()
        self.pattern_predictions.clear()
        logger.info("所有模式已清除")