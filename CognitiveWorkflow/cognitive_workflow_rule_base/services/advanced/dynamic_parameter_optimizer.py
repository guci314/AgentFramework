# -*- coding: utf-8 -*-
"""
动态参数优化器

实现智能的参数自动调优系统，基于历史性能数据动态调整策略参数。
支持梯度下降、贝叶斯优化、强化学习等多种优化算法。

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

from ...domain.value_objects import (
    ReplacementStrategyType, StrategyEffectiveness, SituationScore,
    AdaptiveReplacementConstants
)

logger = logging.getLogger(__name__)


class OptimizationAlgorithm(Enum):
    """优化算法类型"""
    GRADIENT_DESCENT = "gradient_descent"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    GENETIC_ALGORITHM = "genetic_algorithm"
    SIMULATED_ANNEALING = "simulated_annealing"
    ADAPTIVE_LEARNING_RATE = "adaptive_learning_rate"


@dataclass
class ParameterRange:
    """参数范围定义"""
    min_value: float
    max_value: float
    default_value: float
    step_size: float = 0.01
    parameter_type: str = "continuous"  # continuous, discrete, categorical
    
    def clip(self, value: float) -> float:
        """将值限制在有效范围内"""
        return max(self.min_value, min(self.max_value, value))
    
    def normalize(self, value: float) -> float:
        """将值归一化到[0,1]范围"""
        if self.max_value == self.min_value:
            return 0.0
        return (value - self.min_value) / (self.max_value - self.min_value)
    
    def denormalize(self, normalized_value: float) -> float:
        """将归一化值还原到原始范围"""
        return self.min_value + normalized_value * (self.max_value - self.min_value)


@dataclass
class OptimizationState:
    """优化状态记录"""
    iteration: int
    parameters: Dict[str, float]
    performance_score: float
    improvement_rate: float
    convergence_metric: float
    timestamp: datetime
    algorithm_used: OptimizationAlgorithm
    metadata: Dict[str, Any]


@dataclass
class LearningCurve:
    """学习曲线数据"""
    iterations: List[int]
    performance_scores: List[float]
    parameter_values: List[Dict[str, float]]
    convergence_metrics: List[float]
    best_score: float
    best_parameters: Dict[str, float]
    
    def add_point(self, iteration: int, score: float, parameters: Dict[str, float], convergence: float):
        """添加学习曲线数据点"""
        self.iterations.append(iteration)
        self.performance_scores.append(score)
        self.parameter_values.append(parameters.copy())
        self.convergence_metrics.append(convergence)
        
        if score > self.best_score:
            self.best_score = score
            self.best_parameters = parameters.copy()


class DynamicParameterOptimizer:
    """动态参数优化器 - Phase 3核心组件"""
    
    def __init__(self, 
                 optimization_algorithm: OptimizationAlgorithm = OptimizationAlgorithm.ADAPTIVE_LEARNING_RATE,
                 max_iterations: int = 100,
                 convergence_threshold: float = 0.001,
                 learning_rate: float = 0.01):
        """
        初始化动态参数优化器
        
        Args:
            optimization_algorithm: 使用的优化算法
            max_iterations: 最大优化迭代次数
            convergence_threshold: 收敛阈值
            learning_rate: 学习率
        """
        self.algorithm = optimization_algorithm
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.learning_rate = learning_rate
        
        # 定义可优化的参数范围
        self.parameter_ranges = self._define_parameter_ranges()
        
        # 优化状态追踪
        self.optimization_history: List[OptimizationState] = []
        self.learning_curves: Dict[ReplacementStrategyType, LearningCurve] = {}
        self.current_iteration = 0
        
        # 算法特定状态
        self.gradient_estimates: Dict[str, float] = {}
        self.momentum_terms: Dict[str, float] = {}
        self.adaptive_rates: Dict[str, float] = {}
        
        # 贝叶斯优化状态
        self.gaussian_process_data: List[Tuple[Dict[str, float], float]] = []
        
        # 强化学习状态
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.exploration_rate = 0.1
        self.discount_factor = 0.95
        
        # 性能追踪
        self.performance_baseline = 0.5  # 基线性能
        self.improvement_threshold = 0.05  # 最小改进阈值
        
        logger.info(f"动态参数优化器已初始化: {optimization_algorithm.value}")
    
    def _define_parameter_ranges(self) -> Dict[str, ParameterRange]:
        """定义可优化参数的范围"""
        return {
            'replacement_ratio': ParameterRange(
                min_value=0.1, max_value=0.8, default_value=0.3, step_size=0.05
            ),
            'similarity_threshold': ParameterRange(
                min_value=0.5, max_value=0.95, default_value=0.8, step_size=0.05
            ),
            'performance_threshold': ParameterRange(
                min_value=0.3, max_value=0.9, default_value=0.7, step_size=0.05
            ),
            'max_rules_per_phase': ParameterRange(
                min_value=2, max_value=8, default_value=4, step_size=1, parameter_type="discrete"
            ),
            'max_rules_per_agent': ParameterRange(
                min_value=3, max_value=10, default_value=5, step_size=1, parameter_type="discrete"
            ),
            'learning_rate_adaptation': ParameterRange(
                min_value=0.001, max_value=0.1, default_value=0.01, step_size=0.001
            ),
            'exploration_factor': ParameterRange(
                min_value=0.01, max_value=0.3, default_value=0.1, step_size=0.01
            ),
            'convergence_patience': ParameterRange(
                min_value=5, max_value=20, default_value=10, step_size=1, parameter_type="discrete"
            )
        }
    
    def optimize_parameters(self, 
                          strategy_type: ReplacementStrategyType,
                          current_parameters: Dict[str, float],
                          performance_history: List[StrategyEffectiveness],
                          situation_context: SituationScore) -> Dict[str, float]:
        """
        优化策略参数
        
        Args:
            strategy_type: 策略类型
            current_parameters: 当前参数值
            performance_history: 性能历史数据
            situation_context: 当前情境上下文
            
        Returns:
            Dict[str, float]: 优化后的参数
        """
        try:
            logger.info(f"开始优化策略参数: {strategy_type.value}")
            
            # 计算当前性能分数
            current_score = self._calculate_performance_score(performance_history)
            
            # 根据选择的算法进行优化
            if self.algorithm == OptimizationAlgorithm.GRADIENT_DESCENT:
                optimized_params = self._gradient_descent_optimization(
                    strategy_type, current_parameters, performance_history, situation_context
                )
            elif self.algorithm == OptimizationAlgorithm.BAYESIAN_OPTIMIZATION:
                optimized_params = self._bayesian_optimization(
                    strategy_type, current_parameters, performance_history, situation_context
                )
            elif self.algorithm == OptimizationAlgorithm.REINFORCEMENT_LEARNING:
                optimized_params = self._reinforcement_learning_optimization(
                    strategy_type, current_parameters, performance_history, situation_context
                )
            elif self.algorithm == OptimizationAlgorithm.ADAPTIVE_LEARNING_RATE:
                optimized_params = self._adaptive_learning_rate_optimization(
                    strategy_type, current_parameters, performance_history, situation_context
                )
            else:
                # 默认使用自适应学习率
                optimized_params = self._adaptive_learning_rate_optimization(
                    strategy_type, current_parameters, performance_history, situation_context
                )
            
            # 验证参数范围
            optimized_params = self._validate_and_clip_parameters(optimized_params)
            
            # 记录优化状态
            optimized_score = current_score  # 实际应用后才能得到真实分数
            self._record_optimization_state(
                strategy_type, optimized_params, optimized_score, situation_context
            )
            
            logger.info(f"参数优化完成: {strategy_type.value}, 当前分数: {current_score:.3f}")
            return optimized_params
            
        except Exception as e:
            logger.error(f"参数优化失败: {e}")
            return current_parameters  # 返回原始参数作为后备
    
    def _gradient_descent_optimization(self, 
                                     strategy_type: ReplacementStrategyType,
                                     current_params: Dict[str, float],
                                     history: List[StrategyEffectiveness],
                                     context: SituationScore) -> Dict[str, float]:
        """梯度下降优化"""
        try:
            if len(history) < 2:
                return current_params
            
            # 估计梯度
            gradients = self._estimate_gradients(current_params, history)
            
            # 更新参数
            optimized_params = {}
            for param_name, current_value in current_params.items():
                if param_name in self.parameter_ranges:
                    gradient = gradients.get(param_name, 0.0)
                    
                    # 应用动量
                    momentum_key = f"{strategy_type.value}_{param_name}"
                    if momentum_key not in self.momentum_terms:
                        self.momentum_terms[momentum_key] = 0.0
                    
                    self.momentum_terms[momentum_key] = (
                        0.9 * self.momentum_terms[momentum_key] + 
                        0.1 * gradient
                    )
                    
                    # 参数更新
                    new_value = current_value + self.learning_rate * self.momentum_terms[momentum_key]
                    optimized_params[param_name] = new_value
                else:
                    optimized_params[param_name] = current_value
            
            return optimized_params
            
        except Exception as e:
            logger.error(f"梯度下降优化失败: {e}")
            return current_params
    
    def _bayesian_optimization(self, 
                             strategy_type: ReplacementStrategyType,
                             current_params: Dict[str, float],
                             history: List[StrategyEffectiveness],
                             context: SituationScore) -> Dict[str, float]:
        """贝叶斯优化"""
        try:
            # 简化的贝叶斯优化实现
            # 实际项目中可以使用scikit-optimize或GPyOpt等库
            
            # 更新高斯过程数据
            current_score = self._calculate_performance_score(history)
            self.gaussian_process_data.append((current_params.copy(), current_score))
            
            # 限制数据点数量
            if len(self.gaussian_process_data) > 50:
                self.gaussian_process_data = self.gaussian_process_data[-50:]
            
            # 使用简单的期望改进来选择下一个参数
            best_score = max([score for _, score in self.gaussian_process_data])
            
            # 生成候选参数
            candidates = self._generate_parameter_candidates(current_params, num_candidates=10)
            
            # 选择最佳候选
            best_candidate = current_params
            best_expected_improvement = 0.0
            
            for candidate in candidates:
                expected_improvement = self._calculate_expected_improvement(
                    candidate, best_score
                )
                if expected_improvement > best_expected_improvement:
                    best_expected_improvement = expected_improvement
                    best_candidate = candidate
            
            return best_candidate
            
        except Exception as e:
            logger.error(f"贝叶斯优化失败: {e}")
            return current_params
    
    def _reinforcement_learning_optimization(self, 
                                          strategy_type: ReplacementStrategyType,
                                          current_params: Dict[str, float],
                                          history: List[StrategyEffectiveness],
                                          context: SituationScore) -> Dict[str, float]:
        """强化学习优化"""
        try:
            # 将当前状态编码为字符串
            state_key = self._encode_state(context, current_params)
            
            # 获取可能的动作（参数调整）
            possible_actions = self._get_possible_actions(current_params)
            
            # 选择动作（epsilon-greedy策略）
            if np.random.random() < self.exploration_rate:
                # 探索：随机选择动作
                action = np.random.choice(list(possible_actions.keys()))
            else:
                # 利用：选择Q值最高的动作
                q_values = self.q_table[state_key]
                if q_values:
                    action = max(q_values.items(), key=lambda x: x[1])[0]
                else:
                    action = np.random.choice(list(possible_actions.keys()))
            
            # 应用动作获得新参数
            new_params = possible_actions[action]
            
            # 更新Q表（如果有历史数据）
            if len(history) > 0:
                reward = self._calculate_reward(history[-1])
                old_q = self.q_table[state_key].get(action, 0.0)
                
                # Q-learning更新
                # Q(s,a) = Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
                max_future_q = max(self.q_table[state_key].values()) if self.q_table[state_key] else 0.0
                new_q = old_q + self.learning_rate * (reward + self.discount_factor * max_future_q - old_q)
                self.q_table[state_key][action] = new_q
            
            # 逐渐减少探索率
            self.exploration_rate = max(0.01, self.exploration_rate * 0.995)
            
            return new_params
            
        except Exception as e:
            logger.error(f"强化学习优化失败: {e}")
            return current_params
    
    def _adaptive_learning_rate_optimization(self, 
                                           strategy_type: ReplacementStrategyType,
                                           current_params: Dict[str, float],
                                           history: List[StrategyEffectiveness],
                                           context: SituationScore) -> Dict[str, float]:
        """自适应学习率优化"""
        try:
            if len(history) < 2:
                return current_params
            
            # 计算性能趋势
            recent_scores = [eff.improvement_score for eff in history[-5:]]
            performance_trend = self._calculate_trend(recent_scores)
            
            # 根据趋势调整学习率
            if performance_trend > 0.01:  # 性能提升
                adaptive_lr = min(0.05, self.learning_rate * 1.1)
            elif performance_trend < -0.01:  # 性能下降
                adaptive_lr = max(0.001, self.learning_rate * 0.9)
            else:  # 性能平稳
                adaptive_lr = self.learning_rate
            
            # 基于情境健康度调整参数
            health = context.get_overall_health()
            
            optimized_params = {}
            for param_name, current_value in current_params.items():
                if param_name in self.parameter_ranges:
                    param_range = self.parameter_ranges[param_name]
                    
                    # 计算调整方向和幅度
                    if param_name == 'replacement_ratio':
                        # 健康度低时增加替换率，健康度高时降低替换率
                        adjustment = adaptive_lr * (0.5 - health)
                    elif param_name == 'similarity_threshold':
                        # 健康度低时降低相似性阈值（更宽松），健康度高时提高阈值
                        adjustment = adaptive_lr * (health - 0.5)
                    elif param_name == 'performance_threshold':
                        # 健康度低时降低性能阈值，健康度高时提高阈值
                        adjustment = adaptive_lr * (health - 0.5)
                    else:
                        # 其他参数根据性能趋势调整
                        adjustment = adaptive_lr * performance_trend
                    
                    new_value = param_range.clip(current_value + adjustment)
                    optimized_params[param_name] = new_value
                else:
                    optimized_params[param_name] = current_value
            
            return optimized_params
            
        except Exception as e:
            logger.error(f"自适应学习率优化失败: {e}")
            return current_params
    
    def _estimate_gradients(self, 
                          params: Dict[str, float], 
                          history: List[StrategyEffectiveness]) -> Dict[str, float]:
        """估计参数梯度"""
        gradients = {}
        
        if len(history) < 2:
            return gradients
        
        # 使用有限差分法估计梯度
        recent_performance = [eff.improvement_score for eff in history[-3:]]
        performance_change = recent_performance[-1] - recent_performance[0] if len(recent_performance) >= 2 else 0
        
        for param_name in params:
            if param_name in self.parameter_ranges:
                # 简单的梯度估计：性能变化与参数变化的关系
                if param_name == 'replacement_ratio':
                    # 假设替换率与性能呈倒U型关系
                    current_ratio = params[param_name]
                    optimal_ratio = 0.4  # 假设最优值
                    gradients[param_name] = -2 * (current_ratio - optimal_ratio) * performance_change
                elif param_name == 'similarity_threshold':
                    # 相似性阈值通常越高越好，但有上限
                    gradients[param_name] = performance_change * 0.1
                else:
                    # 默认梯度估计
                    gradients[param_name] = performance_change * 0.05
        
        return gradients
    
    def _calculate_performance_score(self, history: List[StrategyEffectiveness]) -> float:
        """计算整体性能分数"""
        if not history:
            return self.performance_baseline
        
        # 使用加权平均，最近的记录权重更高
        weights = [0.5 ** i for i in range(len(history))][::-1]  # 倒序，最新的权重最高
        weighted_scores = [eff.improvement_score * weight for eff, weight in zip(history, weights)]
        
        return sum(weighted_scores) / sum(weights) if weights else self.performance_baseline
    
    def _calculate_trend(self, scores: List[float]) -> float:
        """计算性能趋势"""
        if len(scores) < 2:
            return 0.0
        
        # 简单的线性趋势计算
        n = len(scores)
        x = list(range(n))
        y = scores
        
        # 计算斜率
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def _generate_parameter_candidates(self, 
                                     current_params: Dict[str, float], 
                                     num_candidates: int = 10) -> List[Dict[str, float]]:
        """生成参数候选"""
        candidates = []
        
        for _ in range(num_candidates):
            candidate = {}
            for param_name, current_value in current_params.items():
                if param_name in self.parameter_ranges:
                    param_range = self.parameter_ranges[param_name]
                    # 在当前值附近生成随机变化
                    noise = np.random.normal(0, 0.1) * (param_range.max_value - param_range.min_value)
                    new_value = param_range.clip(current_value + noise)
                    candidate[param_name] = new_value
                else:
                    candidate[param_name] = current_value
            candidates.append(candidate)
        
        return candidates
    
    def _calculate_expected_improvement(self, 
                                      candidate_params: Dict[str, float], 
                                      best_score: float) -> float:
        """计算期望改进"""
        # 简化的期望改进计算
        # 实际实现中应该基于高斯过程的不确定性
        
        # 基于参数与历史最佳参数的距离来估计改进潜力
        if not self.gaussian_process_data:
            return 0.1  # 默认小的改进期望
        
        best_params = None
        for params, score in self.gaussian_process_data:
            if score == best_score:
                best_params = params
                break
        
        if best_params is None:
            return 0.1
        
        # 计算参数距离
        distance = 0.0
        for param_name in candidate_params:
            if param_name in best_params and param_name in self.parameter_ranges:
                param_range = self.parameter_ranges[param_name]
                normalized_current = param_range.normalize(candidate_params[param_name])
                normalized_best = param_range.normalize(best_params[param_name])
                distance += (normalized_current - normalized_best) ** 2
        
        distance = math.sqrt(distance)
        
        # 期望改进与距离成反比（但要考虑探索）
        exploration_bonus = 0.01 * distance  # 鼓励探索
        return exploration_bonus
    
    def _encode_state(self, context: SituationScore, params: Dict[str, float]) -> str:
        """编码状态为字符串"""
        # 离散化连续值以创建状态表示
        health_level = "high" if context.get_overall_health() > 0.7 else "medium" if context.get_overall_health() > 0.4 else "low"
        
        param_signature = []
        for param_name in sorted(params.keys()):
            if param_name in self.parameter_ranges:
                param_range = self.parameter_ranges[param_name]
                normalized_value = param_range.normalize(params[param_name])
                discretized_value = int(normalized_value * 10)  # 离散化为0-10
                param_signature.append(f"{param_name}:{discretized_value}")
        
        return f"{health_level}_" + "_".join(param_signature)
    
    def _get_possible_actions(self, current_params: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """获取可能的动作"""
        actions = {}
        
        # 为每个参数生成小幅调整的动作
        for param_name, current_value in current_params.items():
            if param_name in self.parameter_ranges:
                param_range = self.parameter_ranges[param_name]
                step = param_range.step_size
                
                # 增加动作
                new_params_up = current_params.copy()
                new_params_up[param_name] = param_range.clip(current_value + step)
                actions[f"increase_{param_name}"] = new_params_up
                
                # 减少动作
                new_params_down = current_params.copy()
                new_params_down[param_name] = param_range.clip(current_value - step)
                actions[f"decrease_{param_name}"] = new_params_down
        
        # 保持不变动作
        actions["no_change"] = current_params.copy()
        
        return actions
    
    def _calculate_reward(self, effectiveness: StrategyEffectiveness) -> float:
        """计算强化学习奖励"""
        # 基于改进分数和成功率计算奖励
        base_reward = effectiveness.improvement_score
        
        # 额外奖励
        if effectiveness.is_successful_application():
            base_reward += 0.1
        
        # 性能奖励
        if effectiveness.get_performance_gain() > 0:
            base_reward += 0.05
        
        return base_reward
    
    def _validate_and_clip_parameters(self, params: Dict[str, float]) -> Dict[str, float]:
        """验证并裁剪参数到有效范围"""
        validated_params = {}
        
        for param_name, value in params.items():
            if param_name in self.parameter_ranges:
                param_range = self.parameter_ranges[param_name]
                validated_params[param_name] = param_range.clip(value)
            else:
                validated_params[param_name] = value
        
        return validated_params
    
    def _record_optimization_state(self, 
                                 strategy_type: ReplacementStrategyType,
                                 parameters: Dict[str, float],
                                 performance_score: float,
                                 context: SituationScore):
        """记录优化状态"""
        improvement_rate = 0.0
        if self.optimization_history:
            last_score = self.optimization_history[-1].performance_score
            improvement_rate = (performance_score - last_score) / max(abs(last_score), 0.001)
        
        convergence_metric = abs(improvement_rate) if improvement_rate != 0 else 0.0
        
        state = OptimizationState(
            iteration=self.current_iteration,
            parameters=parameters.copy(),
            performance_score=performance_score,
            improvement_rate=improvement_rate,
            convergence_metric=convergence_metric,
            timestamp=datetime.now(),
            algorithm_used=self.algorithm,
            metadata={
                'strategy_type': strategy_type.value,
                'context_health': context.get_overall_health(),
                'critical_issues': context.get_critical_issues()
            }
        )
        
        self.optimization_history.append(state)
        
        # 更新学习曲线
        if strategy_type not in self.learning_curves:
            self.learning_curves[strategy_type] = LearningCurve(
                iterations=[], performance_scores=[], parameter_values=[],
                convergence_metrics=[], best_score=0.0, best_parameters={}
            )
        
        self.learning_curves[strategy_type].add_point(
            self.current_iteration, performance_score, parameters, convergence_metric
        )
        
        self.current_iteration += 1
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要"""
        if not self.optimization_history:
            return {'message': '暂无优化历史'}
        
        recent_states = self.optimization_history[-10:]
        
        return {
            'total_iterations': len(self.optimization_history),
            'current_algorithm': self.algorithm.value,
            'recent_performance': [s.performance_score for s in recent_states],
            'best_performance': max(s.performance_score for s in self.optimization_history),
            'convergence_status': self._check_convergence(),
            'parameter_stability': self._analyze_parameter_stability(),
            'learning_progress': {
                strategy.value: {
                    'best_score': curve.best_score,
                    'best_parameters': curve.best_parameters,
                    'total_iterations': len(curve.iterations)
                }
                for strategy, curve in self.learning_curves.items()
            }
        }
    
    def _check_convergence(self) -> Dict[str, Any]:
        """检查收敛状态"""
        if len(self.optimization_history) < 10:
            return {'converged': False, 'reason': '数据不足'}
        
        recent_convergence = [s.convergence_metric for s in self.optimization_history[-10:]]
        avg_convergence = sum(recent_convergence) / len(recent_convergence)
        
        converged = avg_convergence < self.convergence_threshold
        
        return {
            'converged': converged,
            'average_convergence_metric': avg_convergence,
            'threshold': self.convergence_threshold,
            'reason': '已收敛' if converged else '仍在优化中'
        }
    
    def _analyze_parameter_stability(self) -> Dict[str, float]:
        """分析参数稳定性"""
        if len(self.optimization_history) < 5:
            return {}
        
        recent_states = self.optimization_history[-5:]
        stability_metrics = {}
        
        # 计算每个参数的变异系数
        for param_name in self.parameter_ranges:
            values = []
            for state in recent_states:
                if param_name in state.parameters:
                    values.append(state.parameters[param_name])
            
            if values and len(values) > 1:
                mean_val = sum(values) / len(values)
                if mean_val != 0:
                    std_val = math.sqrt(sum((v - mean_val) ** 2 for v in values) / len(values))
                    stability_metrics[param_name] = 1.0 - (std_val / abs(mean_val))  # 稳定性分数
                else:
                    stability_metrics[param_name] = 1.0
        
        return stability_metrics
    
    def export_learning_data(self, format_type: str = 'summary') -> Dict[str, Any]:
        """导出学习数据"""
        if format_type == 'detailed':
            return {
                'optimization_history': [asdict(state) for state in self.optimization_history],
                'learning_curves': {
                    strategy.value: {
                        'iterations': curve.iterations,
                        'performance_scores': curve.performance_scores,
                        'parameter_values': curve.parameter_values,
                        'convergence_metrics': curve.convergence_metrics,
                        'best_score': curve.best_score,
                        'best_parameters': curve.best_parameters
                    }
                    for strategy, curve in self.learning_curves.items()
                },
                'parameter_ranges': {
                    name: asdict(range_def) for name, range_def in self.parameter_ranges.items()
                },
                'algorithm_state': {
                    'current_algorithm': self.algorithm.value,
                    'learning_rate': self.learning_rate,
                    'exploration_rate': getattr(self, 'exploration_rate', None),
                    'gradient_estimates': self.gradient_estimates,
                    'momentum_terms': self.momentum_terms
                }
            }
        else:
            return self.get_optimization_summary()
    
    def reset_optimization_state(self):
        """重置优化状态"""
        self.optimization_history.clear()
        self.learning_curves.clear()
        self.current_iteration = 0
        self.gradient_estimates.clear()
        self.momentum_terms.clear()
        self.adaptive_rates.clear()
        self.gaussian_process_data.clear()
        self.q_table.clear()
        
        logger.info("优化状态已重置")