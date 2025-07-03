# -*- coding: utf-8 -*-
"""
预测性优化框架

实现基于预测的智能优化系统，能够预测未来的系统状态和性能，
提前进行优化决策，实现主动式而非被动式的系统优化。

Phase 3: Self-Learning Optimization 核心组件
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ...domain.value_objects import (
    ReplacementStrategyType, StrategyEffectiveness, SituationScore,
    ExecutionMetrics, AdaptiveReplacementConstants
)
from ..advanced.dynamic_parameter_optimizer import DynamicParameterOptimizer, OptimizationAlgorithm
from ..advanced.advanced_pattern_recognition import AdvancedPatternRecognitionEngine, PatternPrediction
from ..adaptive.strategy_effectiveness_tracker import StrategyEffectivenessTracker

logger = logging.getLogger(__name__)


class PredictionHorizon(Enum):
    """预测时间范围"""
    SHORT_TERM = "short_term"      # 短期：1-5分钟
    MEDIUM_TERM = "medium_term"    # 中期：5-30分钟
    LONG_TERM = "long_term"        # 长期：30分钟-2小时


class OptimizationObjective(Enum):
    """优化目标"""
    MAXIMIZE_PERFORMANCE = "maximize_performance"
    MINIMIZE_RISK = "minimize_risk"
    BALANCE_EFFICIENCY = "balance_efficiency"
    ADAPT_TO_CONTEXT = "adapt_to_context"
    EXPLORE_STRATEGIES = "explore_strategies"


@dataclass
class PredictionModel:
    """预测模型"""
    model_id: str
    model_type: str
    horizon: PredictionHorizon
    accuracy: float
    last_updated: datetime
    parameters: Dict[str, Any]
    training_data_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemStatePrediction:
    """系统状态预测"""
    prediction_id: str
    predicted_time: datetime
    predicted_situation: SituationScore
    confidence: float
    contributing_factors: List[str]
    risk_assessment: Dict[str, float]
    recommended_preparations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'prediction_id': self.prediction_id,
            'predicted_time': self.predicted_time.isoformat(),
            'predicted_situation': {
                'rule_density': self.predicted_situation.rule_density,
                'execution_efficiency': self.predicted_situation.execution_efficiency,
                'goal_progress': self.predicted_situation.goal_progress,
                'failure_frequency': self.predicted_situation.failure_frequency,
                'agent_utilization': self.predicted_situation.agent_utilization,
                'phase_distribution': self.predicted_situation.phase_distribution,
                'overall_health': self.predicted_situation.get_overall_health()
            },
            'confidence': self.confidence,
            'contributing_factors': self.contributing_factors,
            'risk_assessment': self.risk_assessment,
            'recommended_preparations': self.recommended_preparations
        }


@dataclass
class OptimizationAction:
    """优化行动"""
    action_id: str
    action_type: str
    target_strategy: ReplacementStrategyType
    parameter_adjustments: Dict[str, float]
    expected_impact: float
    execution_priority: int
    execution_time: datetime
    prerequisites: List[str]
    rollback_plan: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'action_type': self.action_type,
            'target_strategy': self.target_strategy.value,
            'parameter_adjustments': self.parameter_adjustments,
            'expected_impact': self.expected_impact,
            'execution_priority': self.execution_priority,
            'execution_time': self.execution_time.isoformat(),
            'prerequisites': self.prerequisites,
            'rollback_plan': self.rollback_plan
        }


@dataclass
class OptimizationPlan:
    """优化计划"""
    plan_id: str
    objective: OptimizationObjective
    horizon: PredictionHorizon
    actions: List[OptimizationAction]
    expected_outcomes: Dict[str, float]
    confidence: float
    created_time: datetime
    execution_schedule: Dict[str, datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'objective': self.objective.value,
            'horizon': self.horizon.value,
            'actions': [action.to_dict() for action in self.actions],
            'expected_outcomes': self.expected_outcomes,
            'confidence': self.confidence,
            'created_time': self.created_time.isoformat(),
            'execution_schedule': {k: v.isoformat() for k, v in self.execution_schedule.items()}
        }


class TimeSeriesPredictor:
    """时间序列预测器"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.feature_history: deque = deque(maxlen=window_size * 2)
        
    def add_observation(self, timestamp: datetime, features: Dict[str, float]):
        """添加观测数据"""
        self.feature_history.append({
            'timestamp': timestamp,
            'features': features.copy()
        })
    
    def predict_next_state(self, 
                          horizon_minutes: int = 5) -> Tuple[Dict[str, float], float]:
        """预测下一个状态"""
        if len(self.feature_history) < 3:
            return {}, 0.0
        
        try:
            # 提取时间序列数据
            timestamps = [obs['timestamp'] for obs in self.feature_history]
            features = {key: [] for key in self.feature_history[0]['features'].keys()}
            
            for obs in self.feature_history:
                for key, value in obs['features'].items():
                    features[key].append(value)
            
            # 简单的线性外推预测
            predictions = {}
            confidence_scores = []
            
            for feature_name, values in features.items():
                if len(values) >= 3:
                    # 计算趋势
                    recent_trend = self._calculate_trend(values[-3:])
                    current_value = values[-1]
                    
                    # 预测未来值
                    predicted_value = current_value + (recent_trend * horizon_minutes)
                    
                    # 计算置信度
                    variance = np.var(values[-5:]) if len(values) >= 5 else np.var(values)
                    confidence = max(0.1, 1.0 - min(1.0, variance))
                    
                    predictions[feature_name] = max(0.0, min(1.0, predicted_value))
                    confidence_scores.append(confidence)
            
            overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
            return predictions, overall_confidence
            
        except Exception as e:
            logger.error(f"时间序列预测失败: {e}")
            return {}, 0.0
    
    def _calculate_trend(self, values: List[float]) -> float:
        """计算趋势"""
        if len(values) < 2:
            return 0.0
        
        # 简单的线性趋势
        x = list(range(len(values)))
        y = values
        
        n = len(values)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope


class ContextualPredictor:
    """上下文预测器"""
    
    def __init__(self):
        self.context_patterns: Dict[str, List[Tuple[SituationScore, datetime]]] = defaultdict(list)
        self.transition_probabilities: Dict[str, Dict[str, float]] = defaultdict(dict)
        
    def learn_context_patterns(self, history: List[StrategyEffectiveness]):
        """学习上下文模式"""
        try:
            # 清理旧数据
            self.context_patterns.clear()
            self.transition_probabilities.clear()
            
            # 分析上下文转换
            for i in range(len(history) - 1):
                current_context = self._encode_context(history[i].applied_context)
                next_context = self._encode_context(history[i + 1].applied_context)
                
                # 记录转换
                if current_context not in self.transition_probabilities:
                    self.transition_probabilities[current_context] = defaultdict(float)
                self.transition_probabilities[current_context][next_context] += 1.0
                
                # 记录上下文历史
                self.context_patterns[current_context].append(
                    (history[i].applied_context, history[i].application_timestamp)
                )
            
            # 归一化转换概率
            for current_context, transitions in self.transition_probabilities.items():
                total = sum(transitions.values())
                if total > 0:
                    for next_context in transitions:
                        transitions[next_context] /= total
            
            logger.info(f"学习了{len(self.context_patterns)}种上下文模式")
            
        except Exception as e:
            logger.error(f"学习上下文模式失败: {e}")
    
    def predict_context_evolution(self, 
                                current_context: SituationScore,
                                horizon_minutes: int = 10) -> Tuple[SituationScore, float]:
        """预测上下文演化"""
        try:
            current_encoded = self._encode_context(current_context)
            
            # 查找最可能的下一个上下文
            if current_encoded in self.transition_probabilities:
                transitions = self.transition_probabilities[current_encoded]
                if transitions:
                    # 选择概率最高的转换
                    next_encoded = max(transitions.items(), key=lambda x: x[1])
                    next_context_code = next_encoded[0]
                    transition_probability = next_encoded[1]
                    
                    # 解码预测的上下文
                    predicted_context = self._decode_context(next_context_code, current_context)
                    
                    return predicted_context, transition_probability
            
            # 如果没有历史模式，使用趋势预测
            return self._predict_by_trend(current_context), 0.5
            
        except Exception as e:
            logger.error(f"预测上下文演化失败: {e}")
            return current_context, 0.0
    
    def _encode_context(self, context: SituationScore) -> str:
        """编码上下文"""
        health = context.get_overall_health()
        health_level = "high" if health > 0.7 else "medium" if health > 0.4 else "low"
        
        issues = context.get_critical_issues()
        main_issue = issues[0] if issues else "none"
        
        # 离散化关键指标
        density_level = "high" if context.rule_density > 0.7 else "medium" if context.rule_density > 0.4 else "low"
        efficiency_level = "high" if context.execution_efficiency > 0.7 else "medium" if context.execution_efficiency > 0.4 else "low"
        
        return f"{health_level}_{main_issue}_{density_level}_{efficiency_level}"
    
    def _decode_context(self, encoded: str, base_context: SituationScore) -> SituationScore:
        """解码上下文"""
        try:
            parts = encoded.split('_')
            if len(parts) >= 4:
                health_level, main_issue, density_level, efficiency_level = parts[:4]
                
                # 基于编码调整上下文
                new_context = SituationScore(
                    rule_density=base_context.rule_density,
                    execution_efficiency=base_context.execution_efficiency,
                    goal_progress=base_context.goal_progress,
                    failure_frequency=base_context.failure_frequency,
                    agent_utilization=base_context.agent_utilization,
                    phase_distribution=base_context.phase_distribution
                )
                
                # 调整预测值
                if density_level == "high":
                    new_context.rule_density = min(1.0, new_context.rule_density + 0.1)
                elif density_level == "low":
                    new_context.rule_density = max(0.0, new_context.rule_density - 0.1)
                
                if efficiency_level == "high":
                    new_context.execution_efficiency = min(1.0, new_context.execution_efficiency + 0.1)
                elif efficiency_level == "low":
                    new_context.execution_efficiency = max(0.0, new_context.execution_efficiency - 0.1)
                
                return new_context
        
        except Exception as e:
            logger.error(f"解码上下文失败: {e}")
        
        return base_context
    
    def _predict_by_trend(self, current_context: SituationScore) -> SituationScore:
        """基于趋势预测"""
        # 简单的趋势预测：假设轻微改善
        return SituationScore(
            rule_density=max(0.0, min(1.0, current_context.rule_density * 0.95)),
            execution_efficiency=min(1.0, current_context.execution_efficiency * 1.02),
            goal_progress=min(1.0, current_context.goal_progress * 1.05),
            failure_frequency=max(0.0, current_context.failure_frequency * 0.98),
            agent_utilization=current_context.agent_utilization,
            phase_distribution=current_context.phase_distribution
        )


class PerformancePredictor:
    """性能预测器"""
    
    def __init__(self):
        self.performance_models: Dict[ReplacementStrategyType, Dict[str, Any]] = {}
        self.baseline_performance = 0.5
        
    def train_performance_models(self, history: List[StrategyEffectiveness]):
        """训练性能模型"""
        try:
            # 按策略类型分组
            strategy_groups = defaultdict(list)
            for eff in history:
                strategy_groups[eff.strategy_type].append(eff)
            
            # 为每种策略训练模型
            for strategy_type, strategy_history in strategy_groups.items():
                if len(strategy_history) >= 3:
                    model = self._build_strategy_model(strategy_history)
                    self.performance_models[strategy_type] = model
            
            logger.info(f"训练了{len(self.performance_models)}个策略性能模型")
            
        except Exception as e:
            logger.error(f"训练性能模型失败: {e}")
    
    def predict_strategy_performance(self, 
                                   strategy_type: ReplacementStrategyType,
                                   predicted_context: SituationScore,
                                   parameters: Dict[str, float]) -> Tuple[float, float]:
        """预测策略性能"""
        try:
            if strategy_type in self.performance_models:
                model = self.performance_models[strategy_type]
                
                # 计算上下文特征
                context_features = self._extract_context_features(predicted_context)
                
                # 计算参数特征
                param_features = self._extract_parameter_features(parameters)
                
                # 基于模型预测
                predicted_score = self._apply_model(model, context_features, param_features)
                confidence = model.get('confidence', 0.5)
                
                return predicted_score, confidence
            else:
                # 使用基线预测
                baseline_adjustment = predicted_context.get_overall_health() - 0.5
                predicted_score = self.baseline_performance + baseline_adjustment * 0.2
                return max(0.0, min(1.0, predicted_score)), 0.3
                
        except Exception as e:
            logger.error(f"预测策略性能失败: {e}")
            return self.baseline_performance, 0.0
    
    def _build_strategy_model(self, history: List[StrategyEffectiveness]) -> Dict[str, Any]:
        """构建策略模型"""
        try:
            # 提取特征和目标
            context_features = []
            performance_scores = []
            
            for eff in history:
                features = self._extract_context_features(eff.applied_context)
                context_features.append(features)
                performance_scores.append(eff.improvement_score)
            
            # 计算简单的线性关系
            correlations = {}
            for feature_name in context_features[0].keys():
                feature_values = [cf[feature_name] for cf in context_features]
                correlation = np.corrcoef(feature_values, performance_scores)[0, 1]
                if not np.isnan(correlation):
                    correlations[feature_name] = correlation
            
            # 计算模型参数
            avg_performance = np.mean(performance_scores)
            performance_std = np.std(performance_scores)
            
            model = {
                'type': 'linear_correlation',
                'feature_correlations': correlations,
                'baseline_performance': avg_performance,
                'performance_variance': performance_std,
                'confidence': max(0.3, 1.0 - performance_std),
                'sample_size': len(history)
            }
            
            return model
            
        except Exception as e:
            logger.error(f"构建策略模型失败: {e}")
            return {'type': 'default', 'baseline_performance': 0.5, 'confidence': 0.3}
    
    def _extract_context_features(self, context: SituationScore) -> Dict[str, float]:
        """提取上下文特征"""
        return {
            'overall_health': context.get_overall_health(),
            'rule_density': context.rule_density,
            'execution_efficiency': context.execution_efficiency,
            'goal_progress': context.goal_progress,
            'failure_frequency': context.failure_frequency,
            'agent_utilization': context.agent_utilization,
            'phase_distribution': context.phase_distribution,
            'has_critical_issues': 1.0 if context.get_critical_issues() else 0.0
        }
    
    def _extract_parameter_features(self, parameters: Dict[str, float]) -> Dict[str, float]:
        """提取参数特征"""
        # 标准化参数值
        normalized = {}
        for param_name, value in parameters.items():
            if param_name == 'replacement_ratio':
                normalized['replacement_ratio'] = value
            elif param_name == 'similarity_threshold':
                normalized['similarity_threshold'] = value
            elif param_name == 'performance_threshold':
                normalized['performance_threshold'] = value
            else:
                normalized[param_name] = value
        
        return normalized
    
    def _apply_model(self, 
                   model: Dict[str, Any], 
                   context_features: Dict[str, float],
                   param_features: Dict[str, float]) -> float:
        """应用模型进行预测"""
        try:
            if model['type'] == 'linear_correlation':
                # 基于特征相关性预测
                baseline = model['baseline_performance']
                
                feature_contribution = 0.0
                for feature_name, correlation in model['feature_correlations'].items():
                    if feature_name in context_features:
                        feature_value = context_features[feature_name]
                        # 特征贡献 = 相关性 * (特征值 - 0.5) * 影响系数
                        contribution = correlation * (feature_value - 0.5) * 0.3
                        feature_contribution += contribution
                
                predicted_score = baseline + feature_contribution
                return max(0.0, min(1.0, predicted_score))
            else:
                return model.get('baseline_performance', 0.5)
                
        except Exception as e:
            logger.error(f"应用模型失败: {e}")
            return 0.5


class PredictiveOptimizationFramework:
    """预测性优化框架 - Phase 3核心组件"""
    
    def __init__(self, 
                 parameter_optimizer: DynamicParameterOptimizer,
                 pattern_engine: AdvancedPatternRecognitionEngine,
                 effectiveness_tracker: StrategyEffectivenessTracker):
        """
        初始化预测性优化框架
        
        Args:
            parameter_optimizer: 动态参数优化器
            pattern_engine: 高级模式识别引擎
            effectiveness_tracker: 策略效果跟踪器
        """
        self.parameter_optimizer = parameter_optimizer
        self.pattern_engine = pattern_engine
        self.effectiveness_tracker = effectiveness_tracker
        
        # 预测器组件
        self.time_series_predictor = TimeSeriesPredictor()
        self.contextual_predictor = ContextualPredictor()
        self.performance_predictor = PerformancePredictor()
        
        # 预测模型和计划
        self.prediction_models: Dict[str, PredictionModel] = {}
        self.active_predictions: List[SystemStatePrediction] = []
        self.optimization_plans: List[OptimizationPlan] = []
        
        # 配置
        self.prediction_horizons = {
            PredictionHorizon.SHORT_TERM: 5,    # 5分钟
            PredictionHorizon.MEDIUM_TERM: 15,  # 15分钟
            PredictionHorizon.LONG_TERM: 60     # 60分钟
        }
        
        self.optimization_objectives = [
            OptimizationObjective.MAXIMIZE_PERFORMANCE,
            OptimizationObjective.BALANCE_EFFICIENCY,
            OptimizationObjective.ADAPT_TO_CONTEXT
        ]
        
        # 执行器
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        logger.info("预测性优化框架已初始化")
    
    def initialize_predictive_models(self, historical_data: List[StrategyEffectiveness]):
        """初始化预测模型"""
        try:
            logger.info("开始初始化预测模型...")
            
            if len(historical_data) < 5:
                logger.warning("历史数据不足，无法初始化高质量预测模型")
                return
            
            # 训练时间序列预测器
            for i, eff in enumerate(historical_data):
                features = {
                    'improvement_score': eff.improvement_score,
                    'performance_gain': eff.get_performance_gain(),
                    'efficiency_gain': eff.get_efficiency_gain(),
                    'context_health': eff.applied_context.get_overall_health()
                }
                self.time_series_predictor.add_observation(eff.application_timestamp, features)
            
            # 训练上下文预测器
            self.contextual_predictor.learn_context_patterns(historical_data)
            
            # 训练性能预测器
            self.performance_predictor.train_performance_models(historical_data)
            
            # 创建预测模型记录
            self.prediction_models['time_series'] = PredictionModel(
                model_id='time_series_v1',
                model_type='time_series',
                horizon=PredictionHorizon.SHORT_TERM,
                accuracy=0.7,  # 初始估计
                last_updated=datetime.now(),
                parameters={'window_size': self.time_series_predictor.window_size},
                training_data_size=len(historical_data)
            )
            
            self.prediction_models['contextual'] = PredictionModel(
                model_id='contextual_v1',
                model_type='contextual_transition',
                horizon=PredictionHorizon.MEDIUM_TERM,
                accuracy=0.6,
                last_updated=datetime.now(),
                parameters={'pattern_count': len(self.contextual_predictor.context_patterns)},
                training_data_size=len(historical_data)
            )
            
            self.prediction_models['performance'] = PredictionModel(
                model_id='performance_v1',
                model_type='strategy_performance',
                horizon=PredictionHorizon.LONG_TERM,
                accuracy=0.65,
                last_updated=datetime.now(),
                parameters={'strategy_models': len(self.performance_predictor.performance_models)},
                training_data_size=len(historical_data)
            )
            
            logger.info(f"预测模型初始化完成，训练了{len(self.prediction_models)}个模型")
            
        except Exception as e:
            logger.error(f"初始化预测模型失败: {e}")
    
    def generate_system_predictions(self, 
                                  current_context: SituationScore,
                                  current_parameters: Dict[str, float]) -> List[SystemStatePrediction]:
        """生成系统状态预测"""
        predictions = []
        
        try:
            logger.info("生成系统状态预测...")
            
            # 为每个时间范围生成预测
            for horizon, minutes in self.prediction_horizons.items():
                prediction = self._generate_horizon_prediction(
                    current_context, current_parameters, horizon, minutes
                )
                if prediction:
                    predictions.append(prediction)
            
            # 更新活跃预测
            self.active_predictions = predictions
            
            logger.info(f"生成了{len(predictions)}个系统状态预测")
            return predictions
            
        except Exception as e:
            logger.error(f"生成系统预测失败: {e}")
            return []
    
    def _generate_horizon_prediction(self, 
                                   current_context: SituationScore,
                                   current_parameters: Dict[str, float],
                                   horizon: PredictionHorizon,
                                   minutes: int) -> Optional[SystemStatePrediction]:
        """生成特定时间范围的预测"""
        try:
            prediction_time = datetime.now() + timedelta(minutes=minutes)
            
            # 时间序列预测
            ts_prediction, ts_confidence = self.time_series_predictor.predict_next_state(minutes)
            
            # 上下文演化预测
            context_prediction, context_confidence = self.contextual_predictor.predict_context_evolution(
                current_context, minutes
            )
            
            # 综合预测置信度
            overall_confidence = (ts_confidence + context_confidence) / 2.0
            
            # 风险评估
            risk_assessment = self._assess_prediction_risks(
                current_context, context_prediction, minutes
            )
            
            # 生成建议
            recommendations = self._generate_preparation_recommendations(
                current_context, context_prediction, risk_assessment
            )
            
            # 识别贡献因素
            contributing_factors = self._identify_contributing_factors(
                current_context, context_prediction
            )
            
            prediction = SystemStatePrediction(
                prediction_id=f"{horizon.value}_{prediction_time.strftime('%H%M%S')}",
                predicted_time=prediction_time,
                predicted_situation=context_prediction,
                confidence=overall_confidence,
                contributing_factors=contributing_factors,
                risk_assessment=risk_assessment,
                recommended_preparations=recommendations
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"生成{horizon.value}预测失败: {e}")
            return None
    
    def create_optimization_plans(self, 
                                predictions: List[SystemStatePrediction],
                                current_parameters: Dict[str, float]) -> List[OptimizationPlan]:
        """创建优化计划"""
        plans = []
        
        try:
            logger.info("创建优化计划...")
            
            # 为每个优化目标创建计划
            for objective in self.optimization_objectives:
                plan = self._create_objective_plan(objective, predictions, current_parameters)
                if plan:
                    plans.append(plan)
            
            # 排序和筛选计划
            plans = self._prioritize_plans(plans)
            
            # 更新优化计划
            self.optimization_plans = plans
            
            logger.info(f"创建了{len(plans)}个优化计划")
            return plans
            
        except Exception as e:
            logger.error(f"创建优化计划失败: {e}")
            return []
    
    def _create_objective_plan(self, 
                             objective: OptimizationObjective,
                             predictions: List[SystemStatePrediction],
                             current_parameters: Dict[str, float]) -> Optional[OptimizationPlan]:
        """创建特定目标的优化计划"""
        try:
            plan_id = f"{objective.value}_{datetime.now().strftime('%H%M%S')}"
            actions = []
            expected_outcomes = {}
            
            # 根据目标类型生成不同的优化行动
            if objective == OptimizationObjective.MAXIMIZE_PERFORMANCE:
                actions = self._create_performance_actions(predictions, current_parameters)
                expected_outcomes = {'performance_improvement': 0.15, 'efficiency_gain': 0.10}
                
            elif objective == OptimizationObjective.BALANCE_EFFICIENCY:
                actions = self._create_efficiency_actions(predictions, current_parameters)
                expected_outcomes = {'efficiency_improvement': 0.20, 'resource_optimization': 0.15}
                
            elif objective == OptimizationObjective.ADAPT_TO_CONTEXT:
                actions = self._create_adaptive_actions(predictions, current_parameters)
                expected_outcomes = {'context_adaptation': 0.25, 'resilience_improvement': 0.10}
            
            if not actions:
                return None
            
            # 计算整体置信度
            confidence = np.mean([pred.confidence for pred in predictions]) if predictions else 0.5
            
            # 创建执行计划
            execution_schedule = {}
            for i, action in enumerate(actions):
                execution_schedule[action.action_id] = action.execution_time
            
            plan = OptimizationPlan(
                plan_id=plan_id,
                objective=objective,
                horizon=PredictionHorizon.MEDIUM_TERM,  # 默认中期计划
                actions=actions,
                expected_outcomes=expected_outcomes,
                confidence=confidence,
                created_time=datetime.now(),
                execution_schedule=execution_schedule
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"创建{objective.value}计划失败: {e}")
            return None
    
    def _create_performance_actions(self, 
                                  predictions: List[SystemStatePrediction],
                                  current_parameters: Dict[str, float]) -> List[OptimizationAction]:
        """创建性能优化行动"""
        actions = []
        
        try:
            # 分析预测中的性能问题
            for prediction in predictions:
                if prediction.predicted_situation.get_overall_health() < 0.6:
                    # 创建性能提升行动
                    action = OptimizationAction(
                        action_id=f"perf_boost_{prediction.prediction_id}",
                        action_type="parameter_adjustment",
                        target_strategy=ReplacementStrategyType.PERFORMANCE_FOCUSED,
                        parameter_adjustments={
                            'replacement_ratio': min(0.6, current_parameters.get('replacement_ratio', 0.3) + 0.1),
                            'performance_threshold': max(0.6, current_parameters.get('performance_threshold', 0.7) - 0.05)
                        },
                        expected_impact=0.15,
                        execution_priority=1,
                        execution_time=prediction.predicted_time - timedelta(minutes=2),
                        prerequisites=["确认系统状态", "备份当前配置"],
                        rollback_plan={'restore_parameters': current_parameters}
                    )
                    actions.append(action)
            
            return actions[:3]  # 限制行动数量
            
        except Exception as e:
            logger.error(f"创建性能行动失败: {e}")
            return []
    
    def _create_efficiency_actions(self, 
                                 predictions: List[SystemStatePrediction],
                                 current_parameters: Dict[str, float]) -> List[OptimizationAction]:
        """创建效率优化行动"""
        actions = []
        
        try:
            # 寻找效率优化机会
            for prediction in predictions:
                if prediction.predicted_situation.execution_efficiency < 0.7:
                    action = OptimizationAction(
                        action_id=f"eff_opt_{prediction.prediction_id}",
                        action_type="efficiency_optimization",
                        target_strategy=ReplacementStrategyType.INCREMENTAL_IMPROVEMENT,
                        parameter_adjustments={
                            'similarity_threshold': min(0.9, current_parameters.get('similarity_threshold', 0.8) + 0.05),
                            'max_rules_per_phase': max(3, current_parameters.get('max_rules_per_phase', 4) - 1)
                        },
                        expected_impact=0.12,
                        execution_priority=2,
                        execution_time=prediction.predicted_time - timedelta(minutes=3),
                        prerequisites=["分析执行瓶颈", "评估资源使用"],
                        rollback_plan={'restore_parameters': current_parameters}
                    )
                    actions.append(action)
            
            return actions[:2]
            
        except Exception as e:
            logger.error(f"创建效率行动失败: {e}")
            return []
    
    def _create_adaptive_actions(self, 
                               predictions: List[SystemStatePrediction],
                               current_parameters: Dict[str, float]) -> List[OptimizationAction]:
        """创建自适应行动"""
        actions = []
        
        try:
            # 创建上下文适应行动
            for prediction in predictions:
                if len(prediction.contributing_factors) > 0:
                    action = OptimizationAction(
                        action_id=f"adapt_{prediction.prediction_id}",
                        action_type="contextual_adaptation",
                        target_strategy=ReplacementStrategyType.STRATEGIC_PIVOT,
                        parameter_adjustments={
                            'replacement_ratio': 0.5,  # 平衡值
                            'conservative_mode': True if prediction.confidence < 0.7 else False
                        },
                        expected_impact=0.18,
                        execution_priority=1,
                        execution_time=prediction.predicted_time - timedelta(minutes=1),
                        prerequisites=["验证预测条件", "准备应急方案"],
                        rollback_plan={'restore_parameters': current_parameters}
                    )
                    actions.append(action)
            
            return actions[:2]
            
        except Exception as e:
            logger.error(f"创建自适应行动失败: {e}")
            return []
    
    def _assess_prediction_risks(self, 
                               current_context: SituationScore,
                               predicted_context: SituationScore,
                               horizon_minutes: int) -> Dict[str, float]:
        """评估预测风险"""
        risks = {}
        
        try:
            # 健康度下降风险
            health_change = predicted_context.get_overall_health() - current_context.get_overall_health()
            if health_change < -0.1:
                risks['health_degradation'] = min(1.0, abs(health_change) * 2.0)
            
            # 性能下降风险
            efficiency_change = predicted_context.execution_efficiency - current_context.execution_efficiency
            if efficiency_change < -0.1:
                risks['performance_decline'] = min(1.0, abs(efficiency_change) * 1.5)
            
            # 失败率增加风险
            failure_change = predicted_context.failure_frequency - current_context.failure_frequency
            if failure_change > 0.1:
                risks['failure_increase'] = min(1.0, failure_change * 3.0)
            
            # 时间风险（预测距离越远，风险越高）
            time_risk = min(0.5, horizon_minutes / 120.0)  # 最多50%的时间风险
            risks['prediction_uncertainty'] = time_risk
            
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            risks['assessment_error'] = 0.5
        
        return risks
    
    def _generate_preparation_recommendations(self, 
                                            current_context: SituationScore,
                                            predicted_context: SituationScore,
                                            risks: Dict[str, float]) -> List[str]:
        """生成准备建议"""
        recommendations = []
        
        try:
            # 基于风险生成建议
            if 'health_degradation' in risks and risks['health_degradation'] > 0.3:
                recommendations.append("准备系统健康监控和告警")
                recommendations.append("预先准备恢复策略")
            
            if 'performance_decline' in risks and risks['performance_decline'] > 0.3:
                recommendations.append("优化资源分配")
                recommendations.append("准备性能提升措施")
            
            if 'failure_increase' in risks and risks['failure_increase'] > 0.3:
                recommendations.append("增强错误处理机制")
                recommendations.append("准备回滚计划")
            
            # 基于预测上下文生成建议
            if predicted_context.rule_density > 0.8:
                recommendations.append("准备规则集精简")
            
            if predicted_context.agent_utilization < 0.5:
                recommendations.append("平衡智能体负载")
            
            # 通用建议
            recommendations.append("更新系统配置备份")
            
        except Exception as e:
            logger.error(f"生成准备建议失败: {e}")
        
        return recommendations[:5]  # 限制建议数量
    
    def _identify_contributing_factors(self, 
                                     current_context: SituationScore,
                                     predicted_context: SituationScore) -> List[str]:
        """识别贡献因素"""
        factors = []
        
        try:
            # 比较各维度变化
            if abs(predicted_context.rule_density - current_context.rule_density) > 0.1:
                factors.append(f"规则密度变化：{predicted_context.rule_density - current_context.rule_density:+.2f}")
            
            if abs(predicted_context.execution_efficiency - current_context.execution_efficiency) > 0.1:
                factors.append(f"执行效率变化：{predicted_context.execution_efficiency - current_context.execution_efficiency:+.2f}")
            
            if abs(predicted_context.goal_progress - current_context.goal_progress) > 0.1:
                factors.append(f"目标进度变化：{predicted_context.goal_progress - current_context.goal_progress:+.2f}")
            
            if abs(predicted_context.failure_frequency - current_context.failure_frequency) > 0.05:
                factors.append(f"失败频率变化：{predicted_context.failure_frequency - current_context.failure_frequency:+.2f}")
            
            # 如果没有显著变化
            if not factors:
                factors.append("系统状态相对稳定")
            
        except Exception as e:
            logger.error(f"识别贡献因素失败: {e}")
            factors.append("因素分析出错")
        
        return factors
    
    def _prioritize_plans(self, plans: List[OptimizationPlan]) -> List[OptimizationPlan]:
        """优先级排序计划"""
        try:
            # 计算计划优先级分数
            scored_plans = []
            for plan in plans:
                # 综合分数 = 置信度 * 期望收益 * 紧急度
                expected_benefit = sum(plan.expected_outcomes.values())
                urgency = 1.0  # 可以基于风险计算紧急度
                
                priority_score = plan.confidence * expected_benefit * urgency
                scored_plans.append((plan, priority_score))
            
            # 按分数排序
            scored_plans.sort(key=lambda x: x[1], reverse=True)
            
            return [plan for plan, score in scored_plans[:5]]  # 返回前5个计划
            
        except Exception as e:
            logger.error(f"计划优先级排序失败: {e}")
            return plans
    
    def execute_optimization_plan(self, plan: OptimizationPlan) -> Dict[str, Any]:
        """执行优化计划"""
        try:
            logger.info(f"开始执行优化计划: {plan.plan_id}")
            
            execution_results = {}
            successful_actions = 0
            total_actions = len(plan.actions)
            
            # 按优先级执行行动
            sorted_actions = sorted(plan.actions, key=lambda x: x.execution_priority)
            
            for action in sorted_actions:
                try:
                    # 检查先决条件
                    if self._check_prerequisites(action.prerequisites):
                        # 执行行动
                        result = self._execute_action(action)
                        execution_results[action.action_id] = result
                        
                        if result.get('success', False):
                            successful_actions += 1
                        
                        logger.info(f"行动 {action.action_id} 执行完成: {result.get('message', '无消息')}")
                    else:
                        execution_results[action.action_id] = {
                            'success': False,
                            'message': '先决条件未满足',
                            'skipped': True
                        }
                        
                except Exception as e:
                    logger.error(f"执行行动 {action.action_id} 失败: {e}")
                    execution_results[action.action_id] = {
                        'success': False,
                        'message': f'执行错误: {str(e)}',
                        'error': True
                    }
            
            # 计算执行成功率
            success_rate = successful_actions / total_actions if total_actions > 0 else 0.0
            
            overall_result = {
                'plan_id': plan.plan_id,
                'execution_success': success_rate > 0.5,
                'success_rate': success_rate,
                'total_actions': total_actions,
                'successful_actions': successful_actions,
                'action_results': execution_results,
                'execution_time': datetime.now().isoformat(),
                'message': f'计划执行完成，成功率: {success_rate:.2%}'
            }
            
            logger.info(f"优化计划 {plan.plan_id} 执行完成，成功率: {success_rate:.2%}")
            return overall_result
            
        except Exception as e:
            logger.error(f"执行优化计划失败: {e}")
            return {
                'plan_id': plan.plan_id,
                'execution_success': False,
                'message': f'计划执行失败: {str(e)}',
                'error': True
            }
    
    def _check_prerequisites(self, prerequisites: List[str]) -> bool:
        """检查先决条件"""
        # 简化实现：假设所有先决条件都满足
        # 实际实现中应该检查具体条件
        return True
    
    def _execute_action(self, action: OptimizationAction) -> Dict[str, Any]:
        """执行单个优化行动"""
        try:
            if action.action_type == "parameter_adjustment":
                # 模拟参数调整
                logger.info(f"调整参数: {action.parameter_adjustments}")
                return {
                    'success': True,
                    'message': f'参数已调整: {action.parameter_adjustments}',
                    'applied_changes': action.parameter_adjustments
                }
            
            elif action.action_type == "efficiency_optimization":
                # 模拟效率优化
                logger.info(f"执行效率优化: {action.target_strategy.value}")
                return {
                    'success': True,
                    'message': f'效率优化已应用: {action.target_strategy.value}',
                    'optimization_type': 'efficiency'
                }
            
            elif action.action_type == "contextual_adaptation":
                # 模拟上下文适应
                logger.info(f"执行上下文适应: {action.target_strategy.value}")
                return {
                    'success': True,
                    'message': f'上下文适应已应用: {action.target_strategy.value}',
                    'adaptation_type': 'contextual'
                }
            
            else:
                return {
                    'success': False,
                    'message': f'未知的行动类型: {action.action_type}'
                }
                
        except Exception as e:
            logger.error(f"执行行动失败: {e}")
            return {
                'success': False,
                'message': f'行动执行错误: {str(e)}'
            }
    
    def get_framework_status(self) -> Dict[str, Any]:
        """获取框架状态"""
        try:
            return {
                'prediction_models': {
                    model_id: model.to_dict() for model_id, model in self.prediction_models.items()
                },
                'active_predictions': len(self.active_predictions),
                'optimization_plans': len(self.optimization_plans),
                'recent_predictions': [
                    pred.to_dict() for pred in self.active_predictions[-3:]
                ],
                'recent_plans': [
                    plan.to_dict() for plan in self.optimization_plans[-2:]
                ],
                'framework_health': self._calculate_framework_health(),
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取框架状态失败: {e}")
            return {'error': str(e)}
    
    def _calculate_framework_health(self) -> Dict[str, Any]:
        """计算框架健康度"""
        try:
            # 模型健康度
            model_health = np.mean([model.accuracy for model in self.prediction_models.values()]) if self.prediction_models else 0.0
            
            # 预测质量
            prediction_quality = np.mean([pred.confidence for pred in self.active_predictions]) if self.active_predictions else 0.0
            
            # 计划完整性
            plan_completeness = len(self.optimization_plans) / 3.0  # 假设理想状态是3个计划
            plan_completeness = min(1.0, plan_completeness)
            
            # 整体健康度
            overall_health = (model_health + prediction_quality + plan_completeness) / 3.0
            
            return {
                'overall_health': overall_health,
                'model_health': model_health,
                'prediction_quality': prediction_quality,
                'plan_completeness': plan_completeness,
                'status': 'healthy' if overall_health > 0.7 else 'warning' if overall_health > 0.4 else 'critical'
            }
            
        except Exception as e:
            logger.error(f"计算框架健康度失败: {e}")
            return {'overall_health': 0.0, 'status': 'error'}
    
    def export_framework_data(self, format_type: str = 'summary') -> Dict[str, Any]:
        """导出框架数据"""
        try:
            if format_type == 'detailed':
                return {
                    'prediction_models': {
                        model_id: model.to_dict() for model_id, model in self.prediction_models.items()
                    },
                    'active_predictions': [pred.to_dict() for pred in self.active_predictions],
                    'optimization_plans': [plan.to_dict() for plan in self.optimization_plans],
                    'time_series_data': {
                        'window_size': self.time_series_predictor.window_size,
                        'feature_history_length': len(self.time_series_predictor.feature_history)
                    },
                    'contextual_data': {
                        'pattern_count': len(self.contextual_predictor.context_patterns),
                        'transition_count': len(self.contextual_predictor.transition_probabilities)
                    },
                    'performance_data': {
                        'model_count': len(self.performance_predictor.performance_models),
                        'baseline_performance': self.performance_predictor.baseline_performance
                    }
                }
            else:
                return self.get_framework_status()
                
        except Exception as e:
            logger.error(f"导出框架数据失败: {e}")
            return {'error': str(e)}
    
    def reset_framework(self):
        """重置框架状态"""
        try:
            self.prediction_models.clear()
            self.active_predictions.clear()
            self.optimization_plans.clear()
            
            # 重置预测器
            self.time_series_predictor = TimeSeriesPredictor()
            self.contextual_predictor = ContextualPredictor()
            self.performance_predictor = PerformancePredictor()
            
            logger.info("预测性优化框架已重置")
            
        except Exception as e:
            logger.error(f"重置框架失败: {e}")