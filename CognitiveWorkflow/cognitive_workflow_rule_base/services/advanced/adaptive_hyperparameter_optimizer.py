# -*- coding: utf-8 -*-
"""
自适应超参数优化器

实现智能的超参数自动调优系统，使用贝叶斯优化、网格搜索、
随机搜索等方法自动发现最优的系统参数配置。

Phase 3: Self-Learning Optimization 核心组件
"""

from typing import Dict, List, Any, Optional, Tuple, Callable, Union
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum
import itertools
import random
from abc import ABC, abstractmethod

from ...domain.value_objects import (
    ReplacementStrategyType, StrategyEffectiveness, SituationScore,
    ExecutionMetrics, AdaptiveReplacementConstants
)

logger = logging.getLogger(__name__)


class OptimizationMethod(Enum):
    """优化方法类型"""
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    SIMULATED_ANNEALING = "simulated_annealing"
    ADAPTIVE_GRID = "adaptive_grid"


class HyperparameterType(Enum):
    """超参数类型"""
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"


@dataclass
class HyperparameterSpace:
    """超参数空间定义"""
    name: str
    param_type: HyperparameterType
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step_size: Optional[float] = None
    categories: Optional[List[Any]] = None
    default_value: Any = None
    
    def sample_random(self) -> Any:
        """随机采样"""
        if self.param_type == HyperparameterType.CONTINUOUS:
            return random.uniform(self.min_value, self.max_value)
        elif self.param_type == HyperparameterType.DISCRETE:
            return random.randint(int(self.min_value), int(self.max_value))
        elif self.param_type == HyperparameterType.CATEGORICAL:
            return random.choice(self.categories)
        elif self.param_type == HyperparameterType.BOOLEAN:
            return random.choice([True, False])
        else:
            return self.default_value
    
    def clip_value(self, value: Any) -> Any:
        """裁剪值到有效范围"""
        if self.param_type == HyperparameterType.CONTINUOUS:
            return max(self.min_value, min(self.max_value, value))
        elif self.param_type == HyperparameterType.DISCRETE:
            return max(int(self.min_value), min(int(self.max_value), int(value)))
        elif self.param_type == HyperparameterType.CATEGORICAL:
            return value if value in self.categories else self.categories[0]
        elif self.param_type == HyperparameterType.BOOLEAN:
            return bool(value)
        else:
            return value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class OptimizationResult:
    """优化结果"""
    parameters: Dict[str, Any]
    objective_value: float
    evaluation_count: int
    optimization_time: float
    convergence_history: List[float]
    best_iteration: int
    confidence_interval: Optional[Tuple[float, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'parameters': self.parameters,
            'objective_value': self.objective_value,
            'evaluation_count': self.evaluation_count,
            'optimization_time': self.optimization_time,
            'convergence_history': self.convergence_history,
            'best_iteration': self.best_iteration,
            'confidence_interval': self.confidence_interval
        }


@dataclass
class EvaluationRecord:
    """评估记录"""
    parameters: Dict[str, Any]
    objective_value: float
    timestamp: datetime
    evaluation_time: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'parameters': self.parameters,
            'objective_value': self.objective_value,
            'timestamp': self.timestamp.isoformat(),
            'evaluation_time': self.evaluation_time,
            'metadata': self.metadata
        }


class ObjectiveFunction:
    """目标函数基类"""
    
    def __init__(self, name: str = "default_objective"):
        self.name = name
        self.evaluation_count = 0
        self.evaluation_history: List[EvaluationRecord] = []
    
    def evaluate(self, parameters: Dict[str, Any]) -> float:
        """评估参数配置"""
        start_time = datetime.now()
        
        try:
            # 调用具体的评估逻辑
            objective_value = self._evaluate_impl(parameters)
            
            # 记录评估
            evaluation_time = (datetime.now() - start_time).total_seconds()
            self.evaluation_count += 1
            
            record = EvaluationRecord(
                parameters=parameters.copy(),
                objective_value=objective_value,
                timestamp=start_time,
                evaluation_time=evaluation_time,
                metadata={'evaluation_id': self.evaluation_count}
            )
            
            self.evaluation_history.append(record)
            
            return objective_value
            
        except Exception as e:
            logger.error(f"目标函数评估失败: {e}")
            return float('-inf')  # 返回最差值
    
    def _evaluate_impl(self, parameters: Dict[str, Any]) -> float:
        """具体的评估实现（子类重写）"""
        # 默认实现：随机返回值
        return random.random()
    
    def get_best_result(self) -> Optional[EvaluationRecord]:
        """获取最佳结果"""
        if not self.evaluation_history:
            return None
        return max(self.evaluation_history, key=lambda x: x.objective_value)
    
    def reset(self):
        """重置评估历史"""
        self.evaluation_count = 0
        self.evaluation_history.clear()


class PerformanceObjectiveFunction(ObjectiveFunction):
    """性能目标函数"""
    
    def __init__(self, effectiveness_tracker, current_context: SituationScore):
        super().__init__("performance_objective")
        self.effectiveness_tracker = effectiveness_tracker
        self.current_context = current_context
    
    def _evaluate_impl(self, parameters: Dict[str, Any]) -> float:
        """基于性能历史评估参数配置"""
        try:
            # 模拟参数配置的性能
            # 实际实现中，这里会应用参数并运行一段时间来评估性能
            
            # 基于历史数据预测性能
            if hasattr(self.effectiveness_tracker, 'get_recent_effectiveness'):
                recent_effectiveness = self.effectiveness_tracker.get_recent_effectiveness(10)
                if recent_effectiveness:
                    base_performance = np.mean([eff.improvement_score for eff in recent_effectiveness])
                else:
                    base_performance = 0.5
            else:
                base_performance = 0.5
            
            # 参数配置的影响评估
            parameter_score = self._assess_parameter_configuration(parameters)
            
            # 上下文适应性评估
            context_fit = self._assess_context_fit(parameters)
            
            # 综合分数
            final_score = (base_performance * 0.4 + 
                          parameter_score * 0.4 + 
                          context_fit * 0.2)
            
            # 添加噪声模拟真实评估的不确定性
            noise = random.gauss(0, 0.05)
            final_score = max(0.0, min(1.0, final_score + noise))
            
            return final_score
            
        except Exception as e:
            logger.error(f"性能目标函数评估失败: {e}")
            return 0.0
    
    def _assess_parameter_configuration(self, parameters: Dict[str, Any]) -> float:
        """评估参数配置质量"""
        score = 0.5  # 基础分数
        
        # 替换率评估
        replacement_ratio = parameters.get('replacement_ratio', 0.3)
        if 0.2 <= replacement_ratio <= 0.5:
            score += 0.1
        elif replacement_ratio > 0.7:
            score -= 0.1
        
        # 相似性阈值评估
        similarity_threshold = parameters.get('similarity_threshold', 0.8)
        if 0.7 <= similarity_threshold <= 0.9:
            score += 0.1
        
        # 性能阈值评估
        performance_threshold = parameters.get('performance_threshold', 0.7)
        if 0.6 <= performance_threshold <= 0.8:
            score += 0.1
        
        # 学习率评估
        learning_rate = parameters.get('learning_rate', 0.01)
        if 0.005 <= learning_rate <= 0.05:
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _assess_context_fit(self, parameters: Dict[str, Any]) -> float:
        """评估参数与当前上下文的匹配度"""
        health = self.current_context.get_overall_health()
        
        # 根据系统健康度调整参数评估
        if health < 0.5:
            # 系统健康度低，需要更保守的参数
            conservative_score = 0.0
            if parameters.get('replacement_ratio', 0.3) < 0.4:
                conservative_score += 0.3
            if parameters.get('performance_threshold', 0.7) > 0.6:
                conservative_score += 0.2
            return conservative_score
        
        elif health > 0.8:
            # 系统健康度高，可以更激进的参数
            aggressive_score = 0.0
            if parameters.get('replacement_ratio', 0.3) > 0.4:
                aggressive_score += 0.3
            if parameters.get('exploration_factor', 0.1) > 0.15:
                aggressive_score += 0.2
            return aggressive_score
        
        else:
            # 中等健康度，平衡参数
            return 0.5


class BayesianOptimizer:
    """贝叶斯优化器（简化实现）"""
    
    def __init__(self, 
                 hyperparameter_space: List[HyperparameterSpace],
                 acquisition_function: str = "expected_improvement"):
        self.hyperparameter_space = {space.name: space for space in hyperparameter_space}
        self.acquisition_function = acquisition_function
        self.observations: List[Tuple[Dict[str, Any], float]] = []
        
    def suggest_next_parameters(self) -> Dict[str, Any]:
        """建议下一个参数配置"""
        if len(self.observations) < 3:
            # 初始随机采样
            return self._random_sample()
        
        # 简化的贝叶斯优化：基于已有观测生成候选
        best_params, best_value = max(self.observations, key=lambda x: x[1])
        
        # 在最佳参数附近生成变异
        candidate = {}
        for param_name, space in self.hyperparameter_space.items():
            if param_name in best_params:
                base_value = best_params[param_name]
                
                if space.param_type == HyperparameterType.CONTINUOUS:
                    # 高斯变异
                    std = (space.max_value - space.min_value) * 0.1
                    new_value = random.gauss(base_value, std)
                    candidate[param_name] = space.clip_value(new_value)
                elif space.param_type == HyperparameterType.DISCRETE:
                    # 随机步长变异
                    step = random.choice([-2, -1, 0, 1, 2])
                    new_value = base_value + step
                    candidate[param_name] = space.clip_value(new_value)
                else:
                    # 分类参数随机选择
                    candidate[param_name] = space.sample_random()
            else:
                candidate[param_name] = space.sample_random()
        
        return candidate
    
    def update_observations(self, parameters: Dict[str, Any], objective_value: float):
        """更新观测数据"""
        self.observations.append((parameters.copy(), objective_value))
        
        # 限制观测数据量
        if len(self.observations) > 100:
            self.observations = self.observations[-100:]
    
    def _random_sample(self) -> Dict[str, Any]:
        """随机采样"""
        sample = {}
        for param_name, space in self.hyperparameter_space.items():
            sample[param_name] = space.sample_random()
        return sample


class GridSearchOptimizer:
    """网格搜索优化器"""
    
    def __init__(self, hyperparameter_space: List[HyperparameterSpace]):
        self.hyperparameter_space = {space.name: space for space in hyperparameter_space}
        self.grid_points = self._generate_grid()
        self.current_index = 0
    
    def _generate_grid(self) -> List[Dict[str, Any]]:
        """生成网格点"""
        param_grids = {}
        
        for param_name, space in self.hyperparameter_space.items():
            if space.param_type == HyperparameterType.CONTINUOUS:
                # 连续参数：生成均匀分布的点
                num_points = 5  # 每个维度5个点
                grid_values = np.linspace(space.min_value, space.max_value, num_points)
                param_grids[param_name] = grid_values.tolist()
            elif space.param_type == HyperparameterType.DISCRETE:
                # 离散参数：所有整数值
                grid_values = list(range(int(space.min_value), int(space.max_value) + 1))
                param_grids[param_name] = grid_values
            elif space.param_type == HyperparameterType.CATEGORICAL:
                # 分类参数：所有类别
                param_grids[param_name] = space.categories
            elif space.param_type == HyperparameterType.BOOLEAN:
                # 布尔参数
                param_grids[param_name] = [True, False]
        
        # 生成笛卡尔积
        param_names = list(param_grids.keys())
        param_values = list(param_grids.values())
        
        grid_points = []
        for combination in itertools.product(*param_values):
            point = dict(zip(param_names, combination))
            grid_points.append(point)
        
        return grid_points
    
    def suggest_next_parameters(self) -> Optional[Dict[str, Any]]:
        """建议下一个参数配置"""
        if self.current_index >= len(self.grid_points):
            return None  # 搜索完成
        
        params = self.grid_points[self.current_index]
        self.current_index += 1
        return params
    
    def get_progress(self) -> float:
        """获取搜索进度"""
        if not self.grid_points:
            return 1.0
        return self.current_index / len(self.grid_points)


class RandomSearchOptimizer:
    """随机搜索优化器"""
    
    def __init__(self, 
                 hyperparameter_space: List[HyperparameterSpace],
                 max_evaluations: int = 100):
        self.hyperparameter_space = {space.name: space for space in hyperparameter_space}
        self.max_evaluations = max_evaluations
        self.evaluation_count = 0
    
    def suggest_next_parameters(self) -> Optional[Dict[str, Any]]:
        """建议下一个参数配置"""
        if self.evaluation_count >= self.max_evaluations:
            return None
        
        sample = {}
        for param_name, space in self.hyperparameter_space.items():
            sample[param_name] = space.sample_random()
        
        self.evaluation_count += 1
        return sample
    
    def get_progress(self) -> float:
        """获取搜索进度"""
        return self.evaluation_count / self.max_evaluations


class GeneticAlgorithmOptimizer:
    """遗传算法优化器"""
    
    def __init__(self, 
                 hyperparameter_space: List[HyperparameterSpace],
                 population_size: int = 20,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8):
        self.hyperparameter_space = {space.name: space for space in hyperparameter_space}
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # 初始化种群
        self.population = self._initialize_population()
        self.fitness_scores = [0.0] * population_size
        self.generation = 0
        self.current_individual = 0
    
    def _initialize_population(self) -> List[Dict[str, Any]]:
        """初始化种群"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param_name, space in self.hyperparameter_space.items():
                individual[param_name] = space.sample_random()
            population.append(individual)
        return population
    
    def suggest_next_parameters(self) -> Optional[Dict[str, Any]]:
        """建议下一个参数配置"""
        if self.current_individual >= self.population_size:
            # 当前代评估完成，进化到下一代
            self._evolve_population()
            self.current_individual = 0
            self.generation += 1
        
        if self.generation >= 10:  # 最大代数
            return None
        
        individual = self.population[self.current_individual]
        return individual
    
    def update_fitness(self, parameters: Dict[str, Any], fitness: float):
        """更新适应度"""
        # 找到对应的个体
        for i, individual in enumerate(self.population):
            if individual == parameters:
                self.fitness_scores[i] = fitness
                break
        
        self.current_individual += 1
    
    def _evolve_population(self):
        """进化种群"""
        # 选择
        parents = self._selection()
        
        # 交叉和变异
        new_population = []
        for i in range(0, len(parents), 2):
            parent1 = parents[i]
            parent2 = parents[i + 1] if i + 1 < len(parents) else parents[0]
            
            # 交叉
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # 变异
            if random.random() < self.mutation_rate:
                child1 = self._mutate(child1)
            if random.random() < self.mutation_rate:
                child2 = self._mutate(child2)
            
            new_population.extend([child1, child2])
        
        # 保留最佳个体（精英主义）
        best_individual = self.population[np.argmax(self.fitness_scores)]
        new_population[0] = best_individual
        
        self.population = new_population[:self.population_size]
        self.fitness_scores = [0.0] * self.population_size
    
    def _selection(self) -> List[Dict[str, Any]]:
        """锦标赛选择"""
        selected = []
        for _ in range(self.population_size):
            tournament_size = 3
            tournament_indices = random.sample(range(self.population_size), tournament_size)
            best_index = max(tournament_indices, key=lambda i: self.fitness_scores[i])
            selected.append(self.population[best_index].copy())
        return selected
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """单点交叉"""
        child1, child2 = parent1.copy(), parent2.copy()
        
        param_names = list(self.hyperparameter_space.keys())
        crossover_point = random.randint(1, len(param_names) - 1)
        
        for i in range(crossover_point, len(param_names)):
            param_name = param_names[i]
            child1[param_name], child2[param_name] = child2[param_name], child1[param_name]
        
        return child1, child2
    
    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """变异操作"""
        mutated = individual.copy()
        
        for param_name, space in self.hyperparameter_space.items():
            if random.random() < 0.1:  # 每个参数10%的变异概率
                mutated[param_name] = space.sample_random()
        
        return mutated


class AdaptiveHyperparameterOptimizer:
    """自适应超参数优化器 - Phase 3核心组件"""
    
    def __init__(self, 
                 optimization_method: OptimizationMethod = OptimizationMethod.BAYESIAN_OPTIMIZATION,
                 max_evaluations: int = 50,
                 convergence_threshold: float = 0.001):
        """
        初始化自适应超参数优化器
        
        Args:
            optimization_method: 优化方法
            max_evaluations: 最大评估次数
            convergence_threshold: 收敛阈值
        """
        self.optimization_method = optimization_method
        self.max_evaluations = max_evaluations
        self.convergence_threshold = convergence_threshold
        
        # 超参数空间定义
        self.hyperparameter_space = self._define_hyperparameter_space()
        
        # 优化器
        self.optimizer = self._create_optimizer()
        
        # 目标函数
        self.objective_function: Optional[ObjectiveFunction] = None
        
        # 优化状态
        self.optimization_history: List[EvaluationRecord] = []
        self.best_result: Optional[OptimizationResult] = None
        self.is_converged = False
        self.start_time: Optional[datetime] = None
        
        # 自适应配置
        self.adaptive_config = {
            'performance_window': 10,  # 性能评估窗口
            'improvement_threshold': 0.05,  # 改进阈值
            'stagnation_limit': 10,  # 停滞限制
            'method_switch_threshold': 20  # 方法切换阈值
        }
        
        logger.info(f"自适应超参数优化器初始化: {optimization_method.value}")
    
    def _define_hyperparameter_space(self) -> List[HyperparameterSpace]:
        """定义超参数空间"""
        return [
            HyperparameterSpace(
                name="replacement_ratio",
                param_type=HyperparameterType.CONTINUOUS,
                min_value=0.1,
                max_value=0.8,
                default_value=0.3
            ),
            HyperparameterSpace(
                name="similarity_threshold",
                param_type=HyperparameterType.CONTINUOUS,
                min_value=0.5,
                max_value=0.95,
                default_value=0.8
            ),
            HyperparameterSpace(
                name="performance_threshold",
                param_type=HyperparameterType.CONTINUOUS,
                min_value=0.3,
                max_value=0.9,
                default_value=0.7
            ),
            HyperparameterSpace(
                name="max_rules_per_phase",
                param_type=HyperparameterType.DISCRETE,
                min_value=2,
                max_value=8,
                default_value=4
            ),
            HyperparameterSpace(
                name="max_rules_per_agent",
                param_type=HyperparameterType.DISCRETE,
                min_value=3,
                max_value=10,
                default_value=5
            ),
            HyperparameterSpace(
                name="learning_rate",
                param_type=HyperparameterType.CONTINUOUS,
                min_value=0.001,
                max_value=0.1,
                default_value=0.01
            ),
            HyperparameterSpace(
                name="exploration_factor",
                param_type=HyperparameterType.CONTINUOUS,
                min_value=0.01,
                max_value=0.3,
                default_value=0.1
            ),
            HyperparameterSpace(
                name="conservative_mode",
                param_type=HyperparameterType.BOOLEAN,
                default_value=False
            ),
            HyperparameterSpace(
                name="optimization_algorithm",
                param_type=HyperparameterType.CATEGORICAL,
                categories=["gradient_descent", "bayesian_optimization", "reinforcement_learning"],
                default_value="adaptive_learning_rate"
            )
        ]
    
    def _create_optimizer(self):
        """创建优化器"""
        if self.optimization_method == OptimizationMethod.BAYESIAN_OPTIMIZATION:
            return BayesianOptimizer(self.hyperparameter_space)
        elif self.optimization_method == OptimizationMethod.GRID_SEARCH:
            return GridSearchOptimizer(self.hyperparameter_space)
        elif self.optimization_method == OptimizationMethod.RANDOM_SEARCH:
            return RandomSearchOptimizer(self.hyperparameter_space, self.max_evaluations)
        elif self.optimization_method == OptimizationMethod.GENETIC_ALGORITHM:
            return GeneticAlgorithmOptimizer(self.hyperparameter_space)
        else:
            # 默认使用贝叶斯优化
            return BayesianOptimizer(self.hyperparameter_space)
    
    def set_objective_function(self, objective_function: ObjectiveFunction):
        """设置目标函数"""
        self.objective_function = objective_function
        logger.info(f"目标函数已设置: {objective_function.name}")
    
    def optimize(self, 
                max_time_minutes: Optional[int] = None) -> OptimizationResult:
        """执行优化"""
        try:
            logger.info("开始超参数优化...")
            self.start_time = datetime.now()
            
            if self.objective_function is None:
                raise ValueError("必须先设置目标函数")
            
            # 优化循环
            evaluation_count = 0
            convergence_history = []
            best_value = float('-inf')
            best_parameters = {}
            stagnation_count = 0
            
            while evaluation_count < self.max_evaluations:
                # 检查时间限制
                if max_time_minutes:
                    elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60
                    if elapsed_minutes > max_time_minutes:
                        logger.info(f"达到时间限制 {max_time_minutes} 分钟，停止优化")
                        break
                
                # 获取下一个参数配置
                next_params = self.optimizer.suggest_next_parameters()
                if next_params is None:
                    logger.info("优化器建议停止搜索")
                    break
                
                # 评估参数配置
                objective_value = self.objective_function.evaluate(next_params)
                evaluation_count += 1
                
                # 记录评估历史
                record = EvaluationRecord(
                    parameters=next_params,
                    objective_value=objective_value,
                    timestamp=datetime.now(),
                    evaluation_time=0.0,  # 由目标函数计算
                    metadata={'evaluation_id': evaluation_count}
                )
                self.optimization_history.append(record)
                
                # 更新优化器
                if hasattr(self.optimizer, 'update_observations'):
                    self.optimizer.update_observations(next_params, objective_value)
                elif hasattr(self.optimizer, 'update_fitness'):
                    self.optimizer.update_fitness(next_params, objective_value)
                
                # 更新最佳结果
                if objective_value > best_value:
                    best_value = objective_value
                    best_parameters = next_params.copy()
                    stagnation_count = 0
                    logger.info(f"发现更优配置: {objective_value:.4f}")
                else:
                    stagnation_count += 1
                
                convergence_history.append(best_value)
                
                # 检查收敛
                if self._check_convergence(convergence_history):
                    logger.info("优化已收敛")
                    self.is_converged = True
                    break
                
                # 自适应策略调整
                if stagnation_count >= self.adaptive_config['stagnation_limit']:
                    self._adaptive_strategy_adjustment()
                    stagnation_count = 0
                
                # 进度报告
                if evaluation_count % 10 == 0:
                    progress = evaluation_count / self.max_evaluations
                    logger.info(f"优化进度: {progress:.1%}, 当前最佳: {best_value:.4f}")
            
            # 创建优化结果
            optimization_time = (datetime.now() - self.start_time).total_seconds()
            
            # 找到最佳迭代
            best_iteration = 0
            for i, value in enumerate(convergence_history):
                if value == best_value:
                    best_iteration = i
                    break
            
            self.best_result = OptimizationResult(
                parameters=best_parameters,
                objective_value=best_value,
                evaluation_count=evaluation_count,
                optimization_time=optimization_time,
                convergence_history=convergence_history,
                best_iteration=best_iteration
            )
            
            logger.info(f"优化完成: 最佳值={best_value:.4f}, 评估次数={evaluation_count}, 用时={optimization_time:.1f}秒")
            return self.best_result
            
        except Exception as e:
            logger.error(f"超参数优化失败: {e}")
            raise
    
    def _check_convergence(self, history: List[float]) -> bool:
        """检查收敛性"""
        if len(history) < self.adaptive_config['performance_window']:
            return False
        
        # 检查最近窗口内的改进
        recent_values = history[-self.adaptive_config['performance_window']:]
        improvement = max(recent_values) - min(recent_values)
        
        return improvement < self.convergence_threshold
    
    def _adaptive_strategy_adjustment(self):
        """自适应策略调整"""
        try:
            logger.info("执行自适应策略调整...")
            
            # 分析当前优化器性能
            recent_evaluations = self.optimization_history[-self.adaptive_config['performance_window']:]
            if not recent_evaluations:
                return
            
            recent_improvements = []
            for i in range(1, len(recent_evaluations)):
                current_best = max(self.optimization_history[:i+1], key=lambda x: x.objective_value).objective_value
                prev_best = max(self.optimization_history[:i], key=lambda x: x.objective_value).objective_value
                improvement = current_best - prev_best
                recent_improvements.append(improvement)
            
            avg_improvement = np.mean(recent_improvements) if recent_improvements else 0.0
            
            # 如果改进很小，考虑切换优化方法
            if avg_improvement < self.adaptive_config['improvement_threshold']:
                self._switch_optimization_method()
            
        except Exception as e:
            logger.error(f"自适应策略调整失败: {e}")
    
    def _switch_optimization_method(self):
        """切换优化方法"""
        try:
            current_method = self.optimization_method
            
            # 选择新的优化方法
            available_methods = [
                OptimizationMethod.BAYESIAN_OPTIMIZATION,
                OptimizationMethod.RANDOM_SEARCH,
                OptimizationMethod.GENETIC_ALGORITHM
            ]
            
            available_methods = [m for m in available_methods if m != current_method]
            if available_methods:
                new_method = random.choice(available_methods)
                
                logger.info(f"切换优化方法: {current_method.value} -> {new_method.value}")
                
                self.optimization_method = new_method
                self.optimizer = self._create_optimizer()
                
                # 如果新优化器支持，传递历史观测数据
                if hasattr(self.optimizer, 'update_observations'):
                    for record in self.optimization_history[-20:]:  # 传递最近20个观测
                        self.optimizer.update_observations(record.parameters, record.objective_value)
            
        except Exception as e:
            logger.error(f"切换优化方法失败: {e}")
    
    def suggest_parameters(self) -> Dict[str, Any]:
        """建议参数配置（单次）"""
        try:
            if hasattr(self.optimizer, 'suggest_next_parameters'):
                suggested = self.optimizer.suggest_next_parameters()
                if suggested:
                    return suggested
            
            # 后备方案：返回默认参数
            default_params = {}
            for space in self.hyperparameter_space:
                default_params[space.name] = space.default_value
            
            return default_params
            
        except Exception as e:
            logger.error(f"建议参数失败: {e}")
            return {}
    
    def evaluate_parameters(self, parameters: Dict[str, Any]) -> float:
        """评估参数配置"""
        if self.objective_function is None:
            raise ValueError("必须先设置目标函数")
        
        return self.objective_function.evaluate(parameters)
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """获取优化状态"""
        try:
            status = {
                'optimization_method': self.optimization_method.value,
                'max_evaluations': self.max_evaluations,
                'current_evaluations': len(self.optimization_history),
                'is_converged': self.is_converged,
                'best_result': self.best_result.to_dict() if self.best_result else None,
                'hyperparameter_space': [space.to_dict() for space in self.hyperparameter_space]
            }
            
            if self.start_time:
                elapsed_time = (datetime.now() - self.start_time).total_seconds()
                status['elapsed_time'] = elapsed_time
                status['progress'] = len(self.optimization_history) / self.max_evaluations
            
            # 添加优化器特定状态
            if hasattr(self.optimizer, 'get_progress'):
                status['optimizer_progress'] = self.optimizer.get_progress()
            
            # 性能趋势
            if len(self.optimization_history) >= 5:
                recent_values = [record.objective_value for record in self.optimization_history[-5:]]
                status['recent_performance_trend'] = self._calculate_trend(recent_values)
            
            return status
            
        except Exception as e:
            logger.error(f"获取优化状态失败: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "insufficient_data"
        
        # 简单的线性趋势
        x = list(range(len(values)))
        correlation = np.corrcoef(x, values)[0, 1] if len(values) > 1 else 0
        
        if correlation > 0.3:
            return "improving"
        elif correlation < -0.3:
            return "declining"
        else:
            return "stable"
    
    def get_parameter_importance(self) -> Dict[str, float]:
        """分析参数重要性"""
        try:
            if len(self.optimization_history) < 10:
                return {}
            
            importance_scores = {}
            
            for space in self.hyperparameter_space:
                param_name = space.name
                
                # 收集该参数的变化和对应的目标值变化
                param_values = []
                objective_values = []
                
                for record in self.optimization_history:
                    if param_name in record.parameters:
                        param_values.append(record.parameters[param_name])
                        objective_values.append(record.objective_value)
                
                # 计算相关性作为重要性度量
                if len(param_values) >= 3 and space.param_type in [HyperparameterType.CONTINUOUS, HyperparameterType.DISCRETE]:
                    try:
                        correlation = abs(np.corrcoef(param_values, objective_values)[0, 1])
                        if not np.isnan(correlation):
                            importance_scores[param_name] = correlation
                        else:
                            importance_scores[param_name] = 0.0
                    except:
                        importance_scores[param_name] = 0.0
                else:
                    # 分类参数：计算方差分析
                    importance_scores[param_name] = 0.5  # 默认中等重要性
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"分析参数重要性失败: {e}")
            return {}
    
    def export_optimization_data(self, format_type: str = 'summary') -> Dict[str, Any]:
        """导出优化数据"""
        try:
            if format_type == 'detailed':
                return {
                    'optimization_config': {
                        'method': self.optimization_method.value,
                        'max_evaluations': self.max_evaluations,
                        'convergence_threshold': self.convergence_threshold,
                        'adaptive_config': self.adaptive_config
                    },
                    'hyperparameter_space': [space.to_dict() for space in self.hyperparameter_space],
                    'optimization_history': [record.to_dict() for record in self.optimization_history],
                    'best_result': self.best_result.to_dict() if self.best_result else None,
                    'parameter_importance': self.get_parameter_importance(),
                    'optimization_status': self.get_optimization_status()
                }
            else:
                return self.get_optimization_status()
                
        except Exception as e:
            logger.error(f"导出优化数据失败: {e}")
            return {'error': str(e)}
    
    def reset_optimization(self):
        """重置优化状态"""
        try:
            self.optimization_history.clear()
            self.best_result = None
            self.is_converged = False
            self.start_time = None
            
            # 重新创建优化器
            self.optimizer = self._create_optimizer()
            
            # 重置目标函数
            if self.objective_function:
                self.objective_function.reset()
            
            logger.info("优化状态已重置")
            
        except Exception as e:
            logger.error(f"重置优化状态失败: {e}")
    
    def create_performance_objective(self, 
                                   effectiveness_tracker,
                                   current_context: SituationScore) -> PerformanceObjectiveFunction:
        """创建性能目标函数"""
        objective = PerformanceObjectiveFunction(effectiveness_tracker, current_context)
        self.set_objective_function(objective)
        return objective